"""Case sequence viewer extracted from the doctor view."""

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QImage, QPainter, QPixmap, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QListWidgetItem,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from shared_request_ui import clean_value
from doctor_view_parts.widgets import DraggableSequenceList, SequenceDropPanel


class CaseSequenceViewerDialog(QDialog):
    """Visualize multiple 3D test sequences with synchronized scrolling."""

    def __init__(
        self,
        parent,
        sequence_entries,
        case_info=None,
        scan_date_options=None,
        current_scan_option_id=None,
        on_scan_date_selected=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Case Sequence Viewer")
        self.setMinimumSize(1250, 780)
        self.setSizeGripEnabled(True)
        self.case_info = case_info or {}
        self.scan_date_options = list(scan_date_options or [])
        self.current_scan_option_id = str(current_scan_option_id or "")
        self.on_scan_date_selected = on_scan_date_selected
        self._scan_change_in_progress = False
        self.scan_date_combo = None
        self.case_info_rows = {}

        self.sequence_by_key = {}
        self.current_sequence_keys = []
        self.panel_assignments = [self._empty_panel_assignment() for _ in range(4)]
        self.panels = []
        self.max_depth = 1
        self._set_sequence_entries(sequence_entries, keep_assignments=False)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setChildrenCollapsible(False)

        sidebar = QFrame()
        sidebar.setObjectName("ViewerSidebar")
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("""
            QFrame#ViewerSidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #081223, stop:1 #0f172a);
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
            QFrame#SidebarCard {
                background: rgba(248, 250, 252, 0.98);
                border: 1px solid #dbe2ea;
                border-radius: 12px;
            }
            QFrame#SidebarDarkCard {
                background: rgba(15, 23, 42, 0.78);
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel#SidebarEyebrow {
                color: #93c5fd;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            QLabel#SidebarTitle {
                color: #f8fafc;
                font-size: 18px;
                font-weight: 800;
            }
            QLabel#SidebarSubtitle {
                color: #cbd5e1;
                font-size: 12px;
            }
            QLabel#CardTitle {
                color: #0f172a;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel#DarkCardTitle {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel#InfoRow {
                color: #334155;
                font-size: 12px;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px 7px;
            }
            QLabel#FilesHint {
                color: #94a3b8;
                font-size: 11px;
            }
            QListWidget {
                background: rgba(255, 255, 255, 0.98);
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 4px;
                color: #0f172a;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 6px;
                margin: 0px;
                color: #0f172a;
            }
            QListWidget::item:hover {
                background: #e0f2fe;
            }
            QListWidget::item:selected {
                background: #bae6fd;
                color: #0c4a6e;
                font-weight: 700;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 3px 0 3px 0;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                min-height: 24px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)

        sidebar_header = QFrame()
        sidebar_header.setStyleSheet("background: transparent; border: none;")
        sidebar_header_layout = QVBoxLayout(sidebar_header)
        sidebar_header_layout.setContentsMargins(4, 4, 4, 4)
        sidebar_header_layout.setSpacing(3)

        sidebar_eyebrow = QLabel("VISUALIZATION")
        sidebar_eyebrow.setObjectName("SidebarEyebrow")
        sidebar_title = QLabel("Case Navigator")
        sidebar_title.setObjectName("SidebarTitle")
        sidebar_subtitle = QLabel("Review metadata and drag test files from the selected scan date into any panel")
        sidebar_subtitle.setObjectName("SidebarSubtitle")
        sidebar_subtitle.setWordWrap(True)

        sidebar_header_layout.addWidget(sidebar_eyebrow)
        sidebar_header_layout.addWidget(sidebar_title)
        sidebar_header_layout.addWidget(sidebar_subtitle)

        case_card = QFrame()
        case_card.setObjectName("SidebarCard")
        case_card.setMinimumHeight(360)
        case_layout = QVBoxLayout(case_card)
        case_layout.setContentsMargins(8, 8, 8, 8)
        case_layout.setSpacing(6)

        case_title = QLabel("Case Information")
        case_title.setObjectName("CardTitle")
        case_layout.addWidget(case_title)

        scan_date_title = QLabel("Scan Date")
        scan_date_title.setStyleSheet("color: #334155; font-size: 11px; font-weight: 700;")
        case_layout.addWidget(scan_date_title)

        self.scan_date_combo = QComboBox()
        self.scan_date_combo.setStyleSheet("""
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
        """)
        case_layout.addWidget(self.scan_date_combo)
        self._populate_scan_date_options()

        case_rows = [
            ("Patient", clean_value(self.case_info.get("patient_name"))),
            ("Patient ID", clean_value(self.case_info.get("patient_id"))),
            ("Diagnosis", clean_value(self.case_info.get("diagnosis_type"))),
            ("Priority", clean_value(self.case_info.get("priority"))),
            ("Status", clean_value(self.case_info.get("status"))),
        ]

        for label_text, value_text in case_rows:
            row = self._make_case_info_row(label_text, value_text)
            row.setObjectName("InfoRow")
            row.setWordWrap(True)
            case_layout.addWidget(row)
            self.case_info_rows[label_text] = row

        files_info_card = QFrame()
        files_info_card.setObjectName("SidebarDarkCard")
        files_info_card.setMinimumHeight(170)
        files_info_layout = QVBoxLayout(files_info_card)
        files_info_layout.setContentsMargins(8, 8, 8, 8)
        files_info_layout.setSpacing(5)

        files_title = QLabel(f"Test Files ({len(self.sequence_by_key)})")
        files_title.setObjectName("DarkCardTitle")
        files_help = QLabel("Drag any file from this scan date onto one of the 4 panels")
        files_help.setWordWrap(True)
        files_help.setObjectName("FilesHint")
        files_help.setMinimumHeight(16)

        files_info_layout.addWidget(files_title)

        self.file_list = DraggableSequenceList()
        self.file_list.setMinimumHeight(110)
        self.file_list.setSpacing(1)
        self.file_list.setUniformItemSizes(True)

        files_info_layout.addWidget(self.file_list, 1)
        files_info_layout.addWidget(files_help)

        for key, entry in self.sequence_by_key.items():
            item = QListWidgetItem(f"📄 {entry['name']}")
            item.setData(Qt.UserRole, key)
            item.setToolTip(entry['name'])
            self.file_list.addItem(item)

        sidebar_layout.addWidget(sidebar_header)
        sidebar_layout.addWidget(case_card, 5)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(files_info_card, 2)
        sidebar_layout.addStretch(1)

        viewer_container = QFrame()
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(8, 4, 8, 4)
        viewer_layout.setSpacing(12)

        def create_panel(panel_index):
            panel = SequenceDropPanel(
                panel_index,
                self.assign_sequence_to_panel,
                self.on_panel_colormap_changed,
                self.adjust_slice,
                self.swap_panel_layers,
                self.clear_panel_layer,
            )
            panel.setMinimumSize(300, 260)
            self.panels.append(panel)
            return panel

        top_row_splitter = QSplitter(Qt.Horizontal)
        top_row_splitter.setHandleWidth(10)
        top_row_splitter.setChildrenCollapsible(False)
        top_row_splitter.addWidget(create_panel(0))
        top_row_splitter.addWidget(create_panel(1))
        top_row_splitter.setStretchFactor(0, 1)
        top_row_splitter.setStretchFactor(1, 1)

        bottom_row_splitter = QSplitter(Qt.Horizontal)
        bottom_row_splitter.setHandleWidth(10)
        bottom_row_splitter.setChildrenCollapsible(False)
        bottom_row_splitter.addWidget(create_panel(2))
        bottom_row_splitter.addWidget(create_panel(3))
        bottom_row_splitter.setStretchFactor(0, 1)
        bottom_row_splitter.setStretchFactor(1, 1)

        panel_splitter = QSplitter(Qt.Vertical)
        panel_splitter.setHandleWidth(10)
        panel_splitter.setChildrenCollapsible(False)
        panel_splitter.addWidget(top_row_splitter)
        panel_splitter.addWidget(bottom_row_splitter)
        panel_splitter.setStretchFactor(0, 1)
        panel_splitter.setStretchFactor(1, 1)
        panel_splitter.setSizes([1, 1])

        controls = QHBoxLayout()
        controls.setContentsMargins(4, 4, 4, 2)
        controls.setSpacing(12)

        slice_text_label = QLabel("Slice")
        slice_text_label.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        controls.addWidget(slice_text_label)
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(max(0, self.max_depth - 1))
        self.slice_slider.setValue(self.slice_slider.maximum() // 2)
        self.slice_slider.valueChanged.connect(self.render_all_panels)
        controls.addWidget(self.slice_slider, 1)

        self.slice_value_label = QLabel("")
        self.slice_value_label.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        controls.addWidget(self.slice_value_label)

        viewer_layout.addWidget(panel_splitter, 1)
        viewer_layout.addLayout(controls)

        splitter.addWidget(sidebar)
        splitter.addWidget(viewer_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 940])

        root.addWidget(splitter, 1)

        self.render_all_panels()

    def _make_case_info_row(self, label_text, value_text):
        return QLabel(
            f"<span style='color:#64748b; font-weight:700;'>{clean_value(label_text)}</span><br>"
            f"<span style='color:#0f172a; font-weight:700;'>{clean_value(value_text)}</span>"
        )

    def _set_case_info(self, case_info):
        self.case_info = dict(case_info or {})
        mapping = {
            "Patient": self.case_info.get("patient_name", ""),
            "Patient ID": self.case_info.get("patient_id", ""),
            "Diagnosis": self.case_info.get("diagnosis_type", ""),
            "Priority": self.case_info.get("priority", ""),
            "Status": self.case_info.get("status", ""),
        }
        for label_text, value_text in mapping.items():
            row = self.case_info_rows.get(label_text)
            if row is not None:
                row.setText(
                    f"<span style='color:#64748b; font-weight:700;'>{clean_value(label_text)}</span><br>"
                    f"<span style='color:#0f172a; font-weight:700;'>{clean_value(value_text)}</span>"
                )

    def _populate_scan_date_options(self):
        if self.scan_date_combo is None:
            return

        self.scan_date_combo.blockSignals(True)
        self.scan_date_combo.clear()

        if self.scan_date_options:
            for option in self.scan_date_options:
                option_id = str(option.get("id", ""))
                option_label = self._format_scan_date_with_time(option.get("request") or {})
                self.scan_date_combo.addItem(option_label, option_id)

            target_index = -1
            if self.current_scan_option_id:
                for i in range(self.scan_date_combo.count()):
                    if str(self.scan_date_combo.itemData(i) or "") == self.current_scan_option_id:
                        target_index = i
                        break
            if target_index < 0:
                target_index = 0
            self.scan_date_combo.setCurrentIndex(target_index)
        else:
            scan_date_value = self._format_scan_date_with_time(self.case_info)
            self.scan_date_combo.addItem(scan_date_value, "")
            self.scan_date_combo.setCurrentIndex(0)

        self.scan_date_combo.setEnabled(self.scan_date_combo.count() > 1)
        self.scan_date_combo.blockSignals(False)
        self.scan_date_combo.currentIndexChanged.connect(self._on_scan_date_changed)

    def _set_sequence_entries(self, sequence_entries, keep_assignments=True):
        current_entries = {
            str(entry["key"]): {
                "name": str(entry["name"]),
                "volume": entry["volume"],
            }
            for entry in sequence_entries
        }
        self.current_sequence_keys = list(current_entries.keys())
        self.sequence_by_key.update(current_entries)

        max_depth = 1
        for entry in self.sequence_by_key.values():
            depth = int(entry["volume"].shape[2]) if entry["volume"].ndim >= 3 else 1
            max_depth = max(max_depth, depth)
        self.max_depth = max_depth

        if not keep_assignments:
            self.panel_assignments = [self._empty_panel_assignment() for _ in range(4)]
        else:
            next_assignments = []
            for assignment in self.panel_assignments:
                base_key = assignment.get("base") if isinstance(assignment, dict) else None
                overlay_key = assignment.get("overlay") if isinstance(assignment, dict) else None
                next_assignments.append({
                    "base": base_key if base_key in self.sequence_by_key else None,
                    "overlay": overlay_key if overlay_key in self.sequence_by_key else None,
                })
            self.panel_assignments = next_assignments

        if hasattr(self, "slice_slider") and self.slice_slider is not None:
            self.slice_slider.setMaximum(max(0, self.max_depth - 1))
            self.slice_slider.setValue(min(self.slice_slider.value(), self.slice_slider.maximum()))

        if hasattr(self, "file_list") and self.file_list is not None:
            self.file_list.clear()
            for key in self.current_sequence_keys:
                entry = self.sequence_by_key.get(key)
                if entry is None:
                    continue
                item = QListWidgetItem(f"📄 {entry['name']}")
                item.setData(Qt.UserRole, key)
                item.setToolTip(entry['name'])
                self.file_list.addItem(item)

    def _on_scan_date_changed(self, index):
        if self._scan_change_in_progress:
            return
        if index < 0 or self.on_scan_date_selected is None:
            return

        option_id = str(self.scan_date_combo.itemData(index) or "") if self.scan_date_combo is not None else ""
        if not option_id:
            return

        self._scan_change_in_progress = True
        try:
            payload = self.on_scan_date_selected(option_id)
            if not payload:
                return

            case_info = payload.get("case_info", {})
            self.current_scan_option_id = option_id
            if case_info:
                self._set_case_info(case_info)

            sequence_entries = payload.get("sequence_entries", [])
            self._set_sequence_entries(sequence_entries, keep_assignments=True)
            self.render_all_panels()
        finally:
            self._scan_change_in_progress = False

    def _format_scan_date_with_time(self, request):
        """Format scan date with time from created_at timestamp."""
        scan_date = clean_value(request.get("scan_date"))
        created_at = str(request.get("created_at", "") or "").strip()

        if created_at and scan_date != "N/A":
            try:
                normalized = created_at.replace("Z", "+00:00")
                date_obj = datetime.fromisoformat(normalized)
                return f"{scan_date} {date_obj.strftime('%H:%M')}"
            except Exception:
                pass

        return scan_date

    def _empty_panel_assignment(self):
        return {"base": None, "overlay": None}

    def clear_panel_layer(self, panel_index, layer_role):
        assignment = self.panel_assignments[panel_index]
        if layer_role == "top":
            assignment["base"] = assignment.get("overlay")
            assignment["overlay"] = None
        elif layer_role == "bottom":
            assignment["overlay"] = None
        self.render_all_panels()

    def _blend_overlay(self, base_rgb, overlay_rgb, overlay_alpha=0.45):
        import numpy as np

        base = base_rgb.astype(np.float32) / 255.0
        overlay = overlay_rgb.astype(np.float32) / 255.0
        blended = base * (1.0 - overlay_alpha) + overlay * overlay_alpha
        return (np.clip(blended, 0.0, 1.0) * 255.0).astype(np.uint8)

    def adjust_slice(self, delta):
        new_value = self.slice_slider.value() + delta
        new_value = max(self.slice_slider.minimum(), min(self.slice_slider.maximum(), new_value))
        self.slice_slider.setValue(new_value)

    def assign_sequence_to_panel(self, panel_index, seq_key):
        if seq_key not in self.sequence_by_key:
            return
        assignment = self.panel_assignments[panel_index]
        base_key = assignment.get("base")
        overlay_key = assignment.get("overlay")

        if base_key is None:
            assignment["base"] = seq_key
        elif seq_key == base_key:
            return
        elif overlay_key is None:
            assignment["overlay"] = seq_key
        elif seq_key == overlay_key:
            return
        else:
            assignment["overlay"] = seq_key

        self.render_all_panels()

    def swap_panel_layers(self, panel_index):
        assignment = self.panel_assignments[panel_index]
        base_key = assignment.get("base")
        overlay_key = assignment.get("overlay")
        if base_key is None or overlay_key is None:
            return
        assignment["base"], assignment["overlay"] = overlay_key, base_key
        self.render_all_panels()

    def on_panel_colormap_changed(self, _panel_index):
        self.render_all_panels()

    def _normalize_slice(self, slice_2d):
        import numpy as np

        arr = np.nan_to_num(slice_2d.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
        min_v = float(arr.min())
        max_v = float(arr.max())
        if max_v > min_v:
            return (arr - min_v) / (max_v - min_v)
        return np.zeros_like(arr, dtype=np.float32)

    def _orient_slice_landscape(self, slice_2d):
        """Preserve the source slice orientation so portrait layout stays intact."""
        import numpy as np

        return np.asarray(slice_2d)

    def _apply_colormap(self, normalized, cmap_name):
        import numpy as np

        x = normalized
        if cmap_name == "Grayscale":
            rgb = np.stack([x, x, x], axis=-1)
        elif cmap_name == "Hot":
            r = np.clip(3.0 * x, 0, 1)
            g = np.clip(3.0 * x - 1.0, 0, 1)
            b = np.clip(3.0 * x - 2.0, 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        elif cmap_name == "Jet":
            r = np.clip(1.5 - np.abs(4.0 * x - 3.0), 0, 1)
            g = np.clip(1.5 - np.abs(4.0 * x - 2.0), 0, 1)
            b = np.clip(1.5 - np.abs(4.0 * x - 1.0), 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        elif cmap_name == "Inferno":
            r = np.clip(x ** 0.45, 0, 1)
            g = np.clip(x ** 1.15, 0, 1)
            b = np.clip(x ** 3.0, 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        elif cmap_name == "Viridis":
            r = np.clip(0.23 + 0.75 * x, 0, 1)
            g = np.clip(0.15 + 0.85 * (x ** 1.1), 0, 1)
            b = np.clip(0.35 + 0.45 * (1.0 - x), 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        elif cmap_name == "Plasma":
            r = np.clip(0.35 + 0.85 * x, 0, 1)
            g = np.clip(0.05 + 0.55 * np.sqrt(x), 0, 1)
            b = np.clip(0.55 + 0.45 * (1.0 - x), 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        elif cmap_name == "Magma":
            r = np.clip(0.1 + 1.2 * (x ** 1.15), 0, 1)
            g = np.clip(0.02 + 0.75 * (x ** 1.7), 0, 1)
            b = np.clip(0.18 + 0.55 * (1.0 - x) ** 1.3, 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        elif cmap_name == "Bone":
            r = np.clip(0.15 + 0.85 * x, 0, 1)
            g = np.clip(0.2 + 0.8 * x, 0, 1)
            b = np.clip(0.25 + 0.75 * x, 0, 1)
            rgb = np.stack([r, g, b], axis=-1)
        return (rgb * 255.0).astype(np.uint8)

    def _is_dark_image(self, rgb_image):
        """Estimate perceived brightness to decide text color."""
        import numpy as np

        if rgb_image.size == 0:
            return False

        r = rgb_image[..., 0].astype(np.float32)
        g = rgb_image[..., 1].astype(np.float32)
        b = rgb_image[..., 2].astype(np.float32)
        luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b).mean()
        return luminance < 120.0

    def _to_pixmap(self, rgb_image, target_size):
        import numpy as np

        rgb_image = np.ascontiguousarray(rgb_image)
        height, width, _ = rgb_image.shape
        qimg = QImage(rgb_image.data, width, height, 3 * width, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        return pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _compose_side_by_side(self, left_rgb, right_rgb, target_size, background_color="#ffffff"):
        width = max(1, int(target_size.width()))
        height = max(1, int(target_size.height()))
        gap = max(8, width // 40)
        half_width = max(1, (width - gap) // 2)

        canvas = QPixmap(width, height)
        canvas.fill(QColor(background_color))

        left_pixmap = self._to_pixmap(left_rgb, target_size).scaled(
            half_width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        right_pixmap = self._to_pixmap(right_rgb, target_size).scaled(
            half_width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        left_x = max(0, (half_width - left_pixmap.width()) // 2)
        left_y = max(0, (height - left_pixmap.height()) // 2)
        right_slot_x = half_width + gap
        right_x = right_slot_x + max(0, (half_width - right_pixmap.width()) // 2)
        right_y = max(0, (height - right_pixmap.height()) // 2)

        separator_x = half_width
        painter.fillRect(separator_x, 0, gap, height, QColor("white"))

        painter.drawPixmap(left_x, left_y, left_pixmap)
        painter.drawPixmap(right_x, right_y, right_pixmap)
        painter.end()
        return canvas

    def render_all_panels(self):
        import numpy as np

        global_slice = self.slice_slider.value()
        self.slice_value_label.setText(f"{global_slice + 1} / {self.max_depth}")

        for panel_index, panel in enumerate(self.panels):
            assignment = self.panel_assignments[panel_index]
            base_key = assignment.get("base")
            overlay_key = assignment.get("overlay")

            if (not base_key or base_key not in self.sequence_by_key) and (not overlay_key or overlay_key not in self.sequence_by_key):
                panel.set_has_sequence(False)
                panel.title_label.setText(f"Panel {panel_index + 1}")
                panel.image_label.setText("Drop a sequence file here")
                panel.image_label.setPixmap(QPixmap())
                panel.slice_info_label.setText("No file assigned")
                panel.set_layer_info("", "", False)
                panel.apply_contrast_theme(dark_background=False)
                continue

            base_entry = self.sequence_by_key.get(base_key) if base_key in self.sequence_by_key else None
            overlay_entry = self.sequence_by_key.get(overlay_key) if overlay_key in self.sequence_by_key else None

            if base_entry is None and overlay_entry is not None:
                base_entry = overlay_entry
                overlay_entry = None
                assignment["base"] = overlay_key
                assignment["overlay"] = None

            if base_entry is None:
                panel.set_has_sequence(False)
                panel.title_label.setText(f"Panel {panel_index + 1}")
                panel.image_label.setText("Drop a sequence file here")
                panel.image_label.setPixmap(QPixmap())
                panel.slice_info_label.setText("No file assigned")
                panel.set_layer_info("", "", False)
                panel.apply_contrast_theme(dark_background=False)
                continue

            base_volume = base_entry["volume"]
            base_name = base_entry["name"]

            if base_volume.ndim < 3:
                panel.image_label.setText("Unsupported volume shape")
                panel.slice_info_label.setText("Expected 3D volume")
                panel.set_layer_info("", "", False)
                continue

            base_depth = int(base_volume.shape[2])
            slice_index = min(max(0, global_slice), max(0, base_depth - 1))
            base_slice = np.asarray(base_volume[:, :, slice_index])
            base_slice = self._orient_slice_landscape(base_slice)
            base_normalized = self._normalize_slice(base_slice)

            if overlay_entry is not None and overlay_entry.get("volume") is not None:
                overlay_volume = overlay_entry["volume"]
                overlay_name = overlay_entry["name"]
                if overlay_volume.ndim >= 3:
                    overlay_depth = int(overlay_volume.shape[2])
                    overlay_slice_index = min(max(0, global_slice), max(0, overlay_depth - 1))
                    overlay_slice = np.asarray(overlay_volume[:, :, overlay_slice_index])
                    overlay_slice = self._orient_slice_landscape(overlay_slice)
                    overlay_normalized = self._normalize_slice(overlay_slice)

                    left_rgb = self._apply_colormap(base_normalized, panel.cmap_combo.currentText())
                    right_rgb = self._apply_colormap(overlay_normalized, panel.cmap_combo.currentText())
                    pair_is_dark = self._is_dark_image(left_rgb) and self._is_dark_image(right_rgb)
                    panel_bg = "#0f172a" if pair_is_dark else "#ffffff"
                    rgb = self._compose_side_by_side(
                        left_rgb,
                        right_rgb,
                        panel.image_label.size(),
                        background_color=panel_bg,
                    )
                    panel.apply_contrast_theme(dark_background=pair_is_dark)
                    panel.set_has_sequence(True)
                    panel.title_label.setText(
                        f"Panel {panel_index + 1} • {base_name} | {overlay_name}"
                    )
                    panel.image_label.setText("")
                    panel.image_label.setPixmap(rgb)
                    panel.set_layer_info(
                        (
                            f"Left: {base_name}  •  Slice {slice_index + 1}/{base_depth}"
                            f"  •  Shape {base_volume.shape[0]}x{base_volume.shape[1]}x{base_volume.shape[2]}"
                        ),
                        (
                            f"Right: {overlay_name}  •  Slice {overlay_slice_index + 1}/{overlay_depth}"
                            f"  •  Shape {overlay_volume.shape[0]}x{overlay_volume.shape[1]}x{overlay_volume.shape[2]}"
                        ),
                        True,
                    )
                    continue

            rgb = self._apply_colormap(base_normalized, panel.cmap_combo.currentText())
            panel.apply_contrast_theme(dark_background=self._is_dark_image(rgb))
            panel.set_has_sequence(True)

            panel.title_label.setText(f"Panel {panel_index + 1} • {base_name}")
            panel.image_label.setText("")
            panel.image_label.setPixmap(self._to_pixmap(rgb, panel.image_label.size()))
            panel.set_layer_info(
                (
                    f"Left: {base_name}  •  Slice {slice_index + 1}/{base_depth}"
                    f"  •  Shape {base_volume.shape[0]}x{base_volume.shape[1]}x{base_volume.shape[2]}"
                ),
                "",
                True,
            )
            panel.slice_info_label.setText(
                f"Slice {slice_index + 1}/{base_depth}  •  Shape {base_volume.shape[0]}x{base_volume.shape[1]}x{base_volume.shape[2]}"
            )
