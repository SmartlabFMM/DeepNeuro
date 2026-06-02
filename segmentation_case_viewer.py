"""3D Segmentation Viewer with Case Info and Mask Navigation."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from segmentation_viewer import SegmentationPane
from shared_request_ui import clean_value, format_request_datetime


class SegmentationViewerWrapper(QWidget):
    """Wrapper that keeps the left pane alive and swaps a persistent right placeholder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.left_pane = SegmentationPane()
        self.right_pane = None
        self.right_placeholder = QFrame()
        self.splitter = QSplitter(Qt.Horizontal)
        self._case_segmentation_items = []
        self._case_current_index = 0
        self._case_selection_callback = None
        self._setup_splitter()

    def configure_case_segmentation_selector(self, segmentations, current_index, on_display):
        """Use case-bound segmentation selector (instead of import button) for all panes."""
        self._case_segmentation_items = list(segmentations or [])
        self._case_current_index = int(current_index or 0)
        self._case_selection_callback = on_display
        self._apply_case_selector(self.left_pane)
        if self.right_pane is not None:
            self._apply_case_selector(self.right_pane)

    def _apply_case_selector(self, pane):
        if pane is None:
            return
        pane.configure_case_segmentation_selector(
            self._case_segmentation_items,
            self._case_current_index,
            self._case_selection_callback,
        )

    def _setup_splitter(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)

        self.left_pane.set_peer_viewer(self)
        self.right_placeholder.setMinimumWidth(0)
        self.right_placeholder.setStyleSheet("background: transparent; border: none;")

        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.right_placeholder)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([600, 0])

        main_layout.addWidget(self.splitter)

    def ensure_split_view(self):
        if self.right_pane is not None:
            return self.right_pane

        self.right_pane = SegmentationPane()
        self._apply_case_selector(self.right_pane)
        self.right_pane.set_peer_viewer(self)
        self.left_pane.set_peer_viewer(self)

        try:
            self.left_pane.close_btn.setVisible(True)
            self.right_pane.close_btn.setVisible(True)
        except Exception:
            pass

        placeholder_index = self.splitter.indexOf(self.right_placeholder)
        if placeholder_index == -1:
            if self.right_placeholder.parent() is not None:
                self.right_placeholder.setParent(None)
            if self.splitter.count() < 2:
                self.splitter.addWidget(self.right_placeholder)
            else:
                self.splitter.insertWidget(1, self.right_placeholder)
            placeholder_index = self.splitter.indexOf(self.right_placeholder)

        if placeholder_index == -1:
            self.right_pane = None
            return None

        old_widget = self.splitter.replaceWidget(placeholder_index, self.right_pane)
        if old_widget is not None and old_widget is not self.right_placeholder:
            old_widget.setParent(None)
            old_widget.deleteLater()

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([300, 300])
        return self.right_pane

    def remove_pane(self, pane_widget):
        if pane_widget is self.right_pane:
            try:
                self.left_pane.close_btn.setVisible(False)
            except Exception:
                pass
            try:
                self.right_pane.close_btn.setVisible(False)
            except Exception:
                pass

            try:
                self.right_pane.peer_viewer = None
            except Exception:
                pass
            try:
                self.left_pane.peer_viewer = self
            except Exception:
                pass

            placeholder_index = self.splitter.indexOf(self.right_pane)
            if placeholder_index == -1:
                placeholder_index = self.splitter.indexOf(self.right_placeholder)
            if placeholder_index == -1:
                self.splitter.addWidget(self.right_placeholder)
            else:
                self.splitter.replaceWidget(placeholder_index, self.right_placeholder)

            self.right_pane = None
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 0)
            self.splitter.setSizes([600, 0])
            return

        if pane_widget is self.left_pane:
            if self.right_pane is None:
                self.hide()
                return

            new_left = self.right_pane
            left_index = self.splitter.indexOf(self.left_pane)
            if left_index == -1:
                return

            old_left = self.splitter.replaceWidget(left_index, new_left)
            if old_left is not None:
                old_left.setParent(None)
                old_left.deleteLater()

            right_index = self.splitter.indexOf(self.right_placeholder)
            if right_index == -1:
                if self.right_placeholder.parent() is not None:
                    self.right_placeholder.setParent(None)
                self.splitter.insertWidget(left_index + 1, self.right_placeholder)
            elif right_index != left_index + 1:
                self.splitter.replaceWidget(right_index, self.right_placeholder)

            self.left_pane = new_left
            self.left_pane.set_peer_viewer(self)
            self.right_pane = None

            try:
                self.left_pane.close_btn.setVisible(False)
            except Exception:
                pass

            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 0)
            self.splitter.setSizes([600, 0])
            return


class Segmentation3DCaseViewerDialog(QDialog):
    """Dialog showing 3D segmentation viewer with case info and mask navigation."""

    def __init__(self, parent, case_info=None, segmentation_file_id=None, all_patient_segmentations=None, on_segmentation_selected=None):
        super().__init__(parent)
        self.setWindowTitle("3D Segmentation Viewer")
        self.setMinimumSize(1400, 850)
        self.case_info = case_info or {}
        self.segmentation_file_id = segmentation_file_id
        self.all_patient_segmentations = all_patient_segmentations or []
        self.on_segmentation_selected = on_segmentation_selected
        self.current_seg_index = 0

        if segmentation_file_id and self.all_patient_segmentations:
            for idx, seg in enumerate(self.all_patient_segmentations):
                if str(seg.get("id", "")) == str(segmentation_file_id):
                    self.current_seg_index = idx
                    break

        self.setStyleSheet(
            """
            QDialog {
                background: #f8fafc;
            }
            QLabel {
                color: #1f2937;
            }
            QFrame#SidebarCard {
                background: rgba(15, 23, 42, 0.06);
                border: 1px solid rgba(148, 163, 184, 0.35);
                border-radius: 10px;
            }
            QFrame#SidebarDarkCard {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel#CardTitle {
                color: #0f172a;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#DarkCardTitle {
                color: #e2e8f0;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#InfoRow {
                color: #0f172a;
                font-size: 11px;
                background: #ffffff;
                border: 1px solid #dbe5f3;
                border-radius: 8px;
                padding: 6px 8px;
            }
            QLabel#FilesHint {
                color: #cbd5e1;
                font-size: 10px;
            }
            QComboBox {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px 8px;
                font-weight: 600;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #e2e8f0;
                background: #f8fafc;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #475569;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                selection-background-color: #e0f2fe;
                selection-color: #0c4a6e;
            }
            """
        )
        self._setup_ui()
        self.setWindowState(self.windowState() | Qt.WindowMaximized)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        title = QLabel("3D Segmentation Viewer")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #111827;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)

        viewer_container = QFrame()
        viewer_container.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }
            """
        )
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)

        try:
            self.seg_viewer_wrapper = SegmentationViewerWrapper()
            self.seg_viewer_wrapper.configure_case_segmentation_selector(
                self.all_patient_segmentations,
                self.current_seg_index,
                self._on_segmentation_clicked,
            )
            viewer_layout.addWidget(self.seg_viewer_wrapper)
        except Exception as exc:
            error_label = QLabel(f"Failed to load 3D viewer: {exc}")
            error_label.setStyleSheet("color: #dc2626; padding: 20px;")
            viewer_layout.addWidget(error_label)
            self.seg_viewer_wrapper = None

        splitter.addWidget(viewer_container)
        splitter.setCollapsible(0, False)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        case_scroll = QScrollArea()
        case_scroll.setWidgetResizable(True)
        case_scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #f3f4f6;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 4px;
                min-height: 20px;
            }
            """
        )

        case_content = QWidget()
        case_layout = QVBoxLayout(case_content)
        case_layout.setContentsMargins(0, 0, 0, 0)
        case_layout.setSpacing(8)
        case_layout.addWidget(self._build_case_info_card())
        case_layout.addStretch()
        case_scroll.setWidget(case_content)
        right_layout.addWidget(case_scroll, 1)
        right_panel.setMaximumWidth(340)

        splitter.addWidget(right_panel)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: #e5e7eb;
                color: #111827;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
            """
        )
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)

    def _build_case_info_card(self):
        card = QFrame()
        card.setObjectName("SidebarCard")
        card.setMinimumHeight(300)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

        title = QLabel("Case Information")
        title.setObjectName("CardTitle")
        card_layout.addWidget(title)

        rows = [
            ("Patient", clean_value(self.case_info.get("patient_name"))),
            ("Patient ID", clean_value(self.case_info.get("patient_id"))),
            ("Request Date", format_request_datetime(self.case_info.get("created_at", ""))),
            ("Completed At", format_request_datetime(self.case_info.get("completed_at"))),
            ("Diagnosis", clean_value(self.case_info.get("diagnosis_type", "Pending"))),
            ("Status", clean_value(self.case_info.get("status", "Unknown"))),
        ]

        for label_text, value in rows:
            row = QLabel(f"{label_text}: {value}")
            row.setObjectName("InfoRow")
            row.setWordWrap(True)
            card_layout.addWidget(row)

        card_layout.addStretch(1)
        return card

    def _build_segmentation_nav(self):
        nav_frame = QFrame()
        nav_frame.setObjectName("SidebarDarkCard")
        nav_frame.setMinimumHeight(210)
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(6)

        nav_title = QLabel(f"Segmentation Files ({len(self.all_patient_segmentations)})")
        nav_title.setObjectName("DarkCardTitle")
        nav_layout.addWidget(nav_title)

        nav_hint = QLabel("Choose a saved segmentation and click Display")
        nav_hint.setObjectName("FilesHint")
        nav_hint.setWordWrap(True)
        nav_layout.addWidget(nav_hint)

        if not self.all_patient_segmentations:
            empty = QLabel("No segmentations found for this patient")
            empty.setStyleSheet("color: #cbd5e1; padding: 6px 0;")
            nav_layout.addWidget(empty)
        else:
            self.seg_selector = QComboBox()
            self.seg_selector.setMaxVisibleItems(12)
            for idx, seg_info in enumerate(self.all_patient_segmentations):
                seg_name = seg_info.get("name", f"Segmentation {idx + 1}")
                created_date = format_request_datetime(seg_info.get("created_at", ""))
                self.seg_selector.addItem(f"{seg_name}  |  {created_date}", idx)

            if 0 <= self.current_seg_index < self.seg_selector.count():
                self.seg_selector.setCurrentIndex(self.current_seg_index)
            self.seg_selector.currentIndexChanged.connect(self._on_segmentation_option_changed)
            nav_layout.addWidget(self.seg_selector)

            self.seg_selected_meta = QLabel()
            self.seg_selected_meta.setObjectName("FilesHint")
            self.seg_selected_meta.setWordWrap(True)
            nav_layout.addWidget(self.seg_selected_meta)

            display_btn = QPushButton("Display Selected")
            display_btn.setCursor(Qt.PointingHandCursor)
            display_btn.setStyleSheet(
                """
                QPushButton {
                    background: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: #1d4ed8;
                }
                """
            )
            display_btn.clicked.connect(self._load_selected_segmentation)
            nav_layout.addWidget(display_btn)

            self._on_segmentation_option_changed(self.seg_selector.currentIndex())

        nav_layout.addStretch()
        return nav_frame

    def _on_segmentation_option_changed(self, index):
        if index < 0 or index >= len(self.all_patient_segmentations):
            return
        seg_info = self.all_patient_segmentations[index]
        seg_name = seg_info.get("name", f"Segmentation {index + 1}")
        created_date = format_request_datetime(seg_info.get("created_at", ""))
        req_id = clean_value(seg_info.get("request_id"))
        if hasattr(self, "seg_selected_meta"):
            self.seg_selected_meta.setText(
                f"Selected: {seg_name}\nCreated: {created_date}\nRequest ID: {req_id}"
            )

    def _load_selected_segmentation(self):
        if not hasattr(self, "seg_selector"):
            return
        selected_index = self.seg_selector.currentIndex()
        if selected_index < 0 or selected_index >= len(self.all_patient_segmentations):
            return
        seg_info = self.all_patient_segmentations[selected_index]
        self._on_segmentation_clicked(selected_index, seg_info)

    def _on_segmentation_clicked(self, index, seg_info_or_id):
        self.current_seg_index = index
        # Accept either a dict (new) or the legacy seg id string
        if isinstance(seg_info_or_id, dict):
            seg_id = seg_info_or_id.get('id') or seg_info_or_id.get('request_id') or ''
            self.segmentation_file_id = seg_id
            if callable(self.on_segmentation_selected):
                try:
                    self.on_segmentation_selected(seg_info_or_id)
                except TypeError:
                    self.on_segmentation_selected(seg_id)
        else:
            self.segmentation_file_id = seg_info_or_id
            if callable(self.on_segmentation_selected):
                self.on_segmentation_selected(seg_info_or_id)
