"""Case viewer dialog that embeds the standard segmentation viewer."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFrame, QLabel, QHBoxLayout

from shared_request_ui import clean_value, format_request_datetime

from segmentation_viewer import SegmentationViewer


class Segmentation3DCaseViewerDialog(QDialog):
    """Dialog showing the same viewer layout as the main segmentation viewer."""

    def __init__(self, parent, case_info=None, segmentation_file_id=None, all_patient_segmentations=None, on_segmentation_selected=None):
        super().__init__(parent)
        self.setWindowTitle("3D Segmentation Viewer")
        self.setMinimumSize(1260, 720)
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

        self.setStyleSheet("QDialog { background: #081223; }")
        self._setup_ui()
        self.setWindowState(self.windowState() | Qt.WindowMaximized)

    def _setup_ui(self):
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.viewer = SegmentationViewer()

        self.viewer.left_pane.configure_case_segmentation_selector(
            self.all_patient_segmentations,
            self.current_seg_index,
            self._on_segmentation_clicked,
        )

        self._enable_case_mode_for_split_view()

        # Create case info bar
        case_bar = self._build_case_info_bar()

        # Insert it directly next to the stats card
        try:
            self.viewer.left_pane.case_info_layout.addWidget(case_bar)
            self.viewer.left_pane.case_info_container.setVisible(True)
        except Exception as e:
            print("Failed to insert case info bar:", e)

        layout.addWidget(self.viewer)

    def _on_segmentation_clicked(self, index, seg_info_or_id):
        self.current_seg_index = index
        if isinstance(seg_info_or_id, dict):
            self.segmentation_file_id = seg_info_or_id.get("id") or seg_info_or_id.get("request_id") or ""
            if callable(self.on_segmentation_selected):
                try:
                    self.on_segmentation_selected(seg_info_or_id)
                except TypeError:
                    self.on_segmentation_selected(self.segmentation_file_id)
        else:
            self.segmentation_file_id = seg_info_or_id
            if callable(self.on_segmentation_selected):
                self.on_segmentation_selected(seg_info_or_id)

    def _enable_case_mode_for_split_view(self):
        """Force any new split pane to use patient-history segmentation selector."""
        original_ensure_split = self.viewer.ensure_split_view

        def ensure_split_with_case_selector():
            pane = original_ensure_split()
            if pane is not None:
                pane.configure_case_segmentation_selector(
                    self.all_patient_segmentations,
                    self.current_seg_index,
                    self._on_segmentation_clicked,
                )
            return pane

        self.viewer.ensure_split_view = ensure_split_with_case_selector

    def _build_case_info_bar(self):
        card = QFrame()
        card.setObjectName("CaseInfoBar")
        card.setFixedHeight(88)
        card.setMinimumWidth(680)
        card.setMaximumWidth(760)
        card.setStyleSheet(
            """
            QFrame#CaseInfoBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #081223, stop:1 #0f172a);
                border: 1px solid rgba(255,255,255,0.06);
            }
            QLabel#CaseInfoTitle {
                color: #93c5fd;
                font-weight: 800;
            }
            QLabel#CaseInfoValue {
                color: #f8fafc;
            }
            """
        )

        row = QHBoxLayout(card)
        row.setContentsMargins(10, 10, 14, 10)
        row.setSpacing(14)

        # Center container
        center = QFrame()
        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(14)

        # Build labels from case_info
        fields = [
            ("Patient", clean_value(self.case_info.get("patient_name"))),
            ("Patient ID", clean_value(self.case_info.get("patient_id"))),
            ("Request Date", format_request_datetime(self.case_info.get("created_at", ""))),
            ("Diagnosis", clean_value(self.case_info.get("diagnosis_type", ""))),
            ("Priority", clean_value(self.case_info.get("priority"))),
            ("Completed At", format_request_datetime(self.case_info.get("completed_at", ""))),
        ]

        for title, val in fields:
            container = QFrame()
            container.setMinimumWidth(92)
            v = QVBoxLayout(container)
            v.setContentsMargins(0, 0, 0, 0)
            t = QLabel(title)
            t.setObjectName("CaseInfoTitle")
            value = QLabel(str(val))
            value.setObjectName("CaseInfoValue")
            value.setMinimumWidth(92)
            v.addWidget(t)
            v.addWidget(value)
            center_layout.addWidget(container)

        row.addWidget(center, 0, Qt.AlignLeft | Qt.AlignVCenter)
        row.addStretch(1)

        return card

    def show_landing_page(self):
        """Close this modal viewer and delegate landing-page navigation upward."""
        self.accept()

        widget = self.parentWidget()
        while widget is not None:
            if hasattr(widget, "show_landing_page"):
                widget.show_landing_page()
                return
            widget = widget.parentWidget()
