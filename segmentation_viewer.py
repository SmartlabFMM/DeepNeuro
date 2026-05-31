import os
import sys
import logging

# Set OpenGL to software mode BEFORE any Qt imports to prevent VTK blocking
# Advanced VTK/PyOpenGL overrides are platform-specific; only apply them on Linux
os.environ["QT_OPENGL"] = "software"
if sys.platform.startswith("linux"):
    os.environ["QT_XCB_GL_INTEGRATION"] = "xcb_glx"
    os.environ["PYOPENGL_PLATFORM"] = "osmesa"  # Force off-screen Mesa rendering for VTK on Linux

# Suppress VTK warnings
os.environ["VTK_LOG_VERBOSITY"] = "OFF"

# Suppress VTK logging at Python level
logging.getLogger("vtkWin32OpenGLRenderWindow").setLevel(logging.CRITICAL)
logging.getLogger("vtkOpenGLRenderWindow").setLevel(logging.CRITICAL)
logging.getLogger("vtkRenderWindow").setLevel(logging.CRITICAL)
# Suppress all root-level warnings from VTK
logging.captureWarnings(False)
for handler in logging.root.handlers[:]:
    handler.addFilter(lambda record: "vtkWin32OpenGLRenderWindow" not in record.getMessage())

import traceback
from datetime import datetime
import nibabel as nib
import numpy as np
from skimage import measure

# Delay importing pyvista
pv = None
QtInteractor = None

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QEvent
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QSizePolicy, QVBoxLayout, QWidget, QComboBox,
    QFrame, QSplitter, QSlider, QSpinBox, QToolTip
)

class_labels = {
    0: "Brain Surface",
    1: "Necrotic/Non-enhancing Tumor",
    2: "Edema",
    3: "Enhancing Tumor",
    4: "Resection Cavity"
}

colors = {
    0: [0.7, 0.7, 0.7],
    1: [0.2, 0.2, 0.2],
    2: [0.4, 0.9, 0.4],
    3: [1.0, 0.1, 0.1],
    4: [0.1, 0.5, 1.0]
}

color_hex = {
    0: "#B0B0B0",
    1: "#333333",
    2: "#66E666",
    3: "#FF1A1A",
    4: "#1A80FF"
}


class SegmentationPane(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SegmentationViewerRoot")
        self.setWindowTitle("3D Segmentation Viewer - DeepNeuro")
        self.setMinimumSize(620, 720)
        self.setStyleSheet("""
            QWidget#SegmentationViewerRoot {
                background: #081223;
                color: #f8fafc;
            }
            QWidget#SegmentationViewerRoot QLabel {
                background: transparent;
                border: none;
            }
            QWidget#SegmentationViewerRoot QCheckBox {
                background: transparent;
                border: none;
            }
            QWidget#SegmentationViewerRoot QPushButton {
                background: transparent;
            }
        """)

        self.meshes = {}
        self.actor_lookup = {}
        self.region_stats = {}
        self.seg_volume = None
        self.t1_volume = None
        self.voxel_volume_mm3 = 1.0
        self.brain_volume_voxels = 0
        self.tumor_volume_voxels = 0
        self.current_file = None
        self.layer_opacities = {0: 0.15, 1: 0.85, 2: 0.8, 3: 0.9, 4: 0.85}
        self.sidebar_stat_labels = {}
        self.peer_viewer = None
        self._case_segmentation_items = []
        self._case_segmentation_selector = None
        self._case_segmentation_display_btn = None
        self._case_segmentation_callback = None

        # Main layout with splitter
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setChildrenCollapsible(False)

        # ============ SIDEBAR ============
        sidebar = QFrame()
        sidebar.setObjectName("ViewerSidebar")
        sidebar.setFixedWidth(270)
        sidebar.setStyleSheet("""
            QFrame#ViewerSidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #081223, stop:1 #0f172a);
                border: 1px solid #1e293b;
                border-radius: 0px;
            }
            QFrame#SidebarCard {
                background: rgba(15, 23, 42, 0.30);
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 10px;
            }
            QFrame#SidebarDarkCard {
                background: rgba(15, 23, 42, 0.78);
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 10px;
            }
            QLabel#SidebarEyebrow {
                color: #93c5fd;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 0.8px;
                background: transparent;
                border: none;
            }
            QLabel#SidebarTitle {
                color: #f8fafc;
                font-size: 16px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            QLabel#SidebarSubtitle {
                color: #cbd5e1;
                font-size: 10px;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
            QLabel#CardTitle {
                color: #e2e8f0;
                font-size: 12px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            QLabel#DarkCardTitle {
                color: #f8fafc;
                font-size: 12px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            QLabel#InfoRow {
                color: #e2e8f0;
                font-size: 10px;
                background: transparent;
                border: none;
                padding: 0px;
                min-height: 0px;
            }
            QComboBox, QSpinBox, QSlider {
                background: rgba(255, 255, 255, 0.08);
                color: #f8fafc;
                border: 1px solid rgba(203, 213, 225, 0.28);
                border-radius: 6px;
                padding: 3px 5px;
                font-size: 10px;
            }
            QComboBox::drop-down {
                background: rgba(255, 255, 255, 0.08);
                border-left: 1px solid rgba(203, 213, 225, 0.22);
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QPushButton {
                background: linear-gradient(to bottom, #6366f1, #4f46e5);
                color: white;
                border: none;
                border-radius: 7px;
                padding: 7px 10px;
                font-weight: 600;
                font-size: 10px;
            }
            QPushButton:hover {
                background: linear-gradient(to bottom, #818cf8, #6366f1);
            }
            QPushButton:pressed {
                background: linear-gradient(to bottom, #4f46e5, #4338ca);
            }
            QPushButton#ImportButton {
                background: rgba(255, 255, 255, 0.04);
                color: #dbeafe;
                border: 1px dashed rgba(147, 197, 253, 0.45);
                border-radius: 8px;
                padding: 7px 10px;
                font-weight: 600;
            }
            QPushButton#ImportButton:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(191, 219, 254, 0.8);
            }
            QPushButton#ImportButton:pressed {
                background: rgba(255, 255, 255, 0.12);
            }
            QPushButton#HomeButton {
                background: #f8fafc;
                color: black;
                border: 2px solid #0f172a;
                border-radius: 16px;
                min-width: 34px;
                min-height: 34px;
                max-width: 34px;
                max-height: 34px;
                font-size: 18px;
                font-weight: 950;
                padding: 0px;
            }
            QPushButton#HomeButton:hover {
                background: #e2e8f0;
                border-color: #1e293b;
            }
            QPushButton#HomeButton:pressed {
                background: #cbd5e1;
            }
            QPushButton#PlusButton {
                background: #f8fafc;
                color: black;
                border: 2px solid #0f172a;
                border-radius: 16px;
                min-width: 34px;
                min-height: 34px;
                max-width: 34px;
                max-height: 34px;
                font-size: 20px;
                font-weight: 900;
                padding: 0px;
            }
            QPushButton#PlusButton:hover {
                background: #e2e8f0;
                border-color: #1e293b;
            }
            QPushButton#PlusButton:pressed {
                background: #cbd5e1;
            }
            QFrame#StatsCard QLabel#StatValue {
                color: #f8fafc;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            QFrame#StatsCard QLabel#StatHint {
                color: #cbd5e1;
                font-size: 9px;
                background: transparent;
                border: none;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)

        # Sidebar header
        sidebar_title = QLabel("3D Visualization")
        sidebar_title.setObjectName("SidebarTitle")
        sidebar_subtitle = QLabel("Import segmentation file and adjust visualization parameters")
        sidebar_subtitle.setObjectName("SidebarSubtitle")
        sidebar_subtitle.setWordWrap(True)

        sidebar_title_row = QHBoxLayout()
        sidebar_title_row.setContentsMargins(0, 0, 0, 0)
        sidebar_title_row.setSpacing(6)
        sidebar_title_row.addWidget(sidebar_title)
        sidebar_title_row.addStretch()

        split_btn = QPushButton("+")
        split_btn.setObjectName("PlusButton")
        split_btn.setToolTip("Create split view")
        split_btn.clicked.connect(self.request_split_view)
        sidebar_title_row.addWidget(split_btn)

        home_btn = QPushButton("⌂")
        home_btn.setObjectName("HomeButton")
        home_btn.setToolTip("Return to landing page")
        home_btn.clicked.connect(self.go_back_to_landing_page)
        sidebar_title_row.addWidget(home_btn)

        # Close button (visible only when this pane is in split view)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setToolTip("Close this pane")
        close_btn.setStyleSheet("""
            QPushButton#CloseButton {
                background: #f8fafc;
                color: #0f172a;
                border: 2px solid #0f172a;
                border-radius: 16px;
                min-width: 34px;
                min-height: 34px;
                max-width: 34px;
                max-height: 34px;
                font-size: 16px;
                font-weight: 900;
                padding: 0px;
            }
            QPushButton#CloseButton:hover {
                background: #e2e8f0;
                border-color: #1e293b;
            }
            QPushButton#CloseButton:pressed {
                background: #cbd5e1;
            }
        """)
        close_btn.clicked.connect(self.close_pane)
        close_btn.setVisible(False)  # Hidden by default, shown only in split view
        self.close_btn = close_btn
        sidebar_title_row.addWidget(close_btn)

        sidebar_layout.addLayout(sidebar_title_row)
        sidebar_layout.addWidget(sidebar_subtitle)

        # File info card
        info_card = QFrame()
        info_card.setObjectName("SidebarCard")
        info_card.setMinimumHeight(82)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(5)

        info_title = QLabel("File Information")
        info_title.setObjectName("CardTitle")
        info_layout.addWidget(info_title)

        self.file_label = QLabel("No file loaded")
        self.file_label.setObjectName("InfoRow")
        self.file_label.setWordWrap(True)
        info_layout.addWidget(self.file_label)

        self.import_btn = QPushButton("Import Segmentation File")
        self.import_btn.setObjectName("ImportButton")
        self.import_btn.clicked.connect(self.import_seg_file)
        info_layout.addWidget(self.import_btn)

        # Segmentation mode selector (Auto / Tumor / Ischemia)
        self.segmentation_mode_selector = QComboBox()
        self.segmentation_mode_selector.addItem("Auto-Detect", "auto")
        self.segmentation_mode_selector.addItem("Tumor (0-4)", "tumor")
        self.segmentation_mode_selector.addItem("Ischemia (0-1)", "ischemia")
        self.segmentation_mode_selector.setCurrentIndex(0)
        self.segmentation_mode_selector.currentIndexChanged.connect(self.on_segmentation_mode_changed)
        info_layout.addWidget(self.segmentation_mode_selector)

        # Internal mode state: 'auto', 'tumor', or 'ischemia'
        self.segmentation_mode = 'auto'

        self.info_layout = info_layout

        sidebar_layout.addWidget(info_card)

        # Layers card
        layers_card = QFrame()
        layers_card.setObjectName("SidebarDarkCard")
        layers_card.setMaximumHeight(305)
        layers_layout = QVBoxLayout(layers_card)
        layers_layout.setContentsMargins(8, 6, 8, 6)
        layers_layout.setSpacing(4)

        layers_title = QLabel("Segmentation Layers")
        layers_title.setObjectName("DarkCardTitle")
        layers_layout.addWidget(layers_title)

        self.layer_controls = {}
        for label_id in [0, 1, 2, 3, 4]:
            layer_widget = QFrame()
            layer_widget.setStyleSheet(f"""
                QFrame {{
                    background: rgba(30, 41, 59, 0.6);
                    border: 1px solid #475569;
                    border-radius: 6px;
                    border-left: 4px solid {color_hex[label_id]};
                }}
            """)
            layer_layout = QVBoxLayout(layer_widget)
            layer_layout.setContentsMargins(6, 4, 6, 4)
            layer_layout.setSpacing(2)

            # Label with checkbox
            label_row = QHBoxLayout()
            cb = QCheckBox(class_labels[label_id])
            cb.setChecked(True)
            cb.setStyleSheet("color: #f8fafc; font-weight: 600; font-size: 10px; background: transparent; border: none;")
            cb.stateChanged.connect(self.update_mesh_visibility)
            label_row.addWidget(cb)
            label_row.addStretch()
            layer_layout.addLayout(label_row)

            # Opacity slider
            opacity_layout = QHBoxLayout()
            opacity_label = QLabel("Opacity:")
            opacity_label.setStyleSheet("color: #cbd5e1; font-size: 9px; background: transparent; border: none;")
            opacity_slider = QSlider(Qt.Horizontal)
            opacity_slider.setMinimum(0)
            opacity_slider.setMaximum(100)
            opacity_slider.setValue(int(self.layer_opacities[label_id] * 100))
            opacity_slider.valueChanged.connect(
                lambda val, lid=label_id: self.set_layer_opacity(lid, val / 100.0)
            )
            opacity_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #334155;
                    height: 5px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #93c5fd;
                    width: 12px;
                    margin: -4px 0;
                    border-radius: 6px;
                }
            """)
            opacity_value = QLabel(f"{int(self.layer_opacities[label_id] * 100)}%")
            opacity_value.setStyleSheet("color: #cbd5e1; font-size: 9px; min-width: 30px;")
            opacity_layout.addWidget(opacity_label)
            opacity_layout.addWidget(opacity_slider, 1)
            opacity_layout.addWidget(opacity_value)
            layer_layout.addLayout(opacity_layout)

            self.layer_controls[label_id] = {
                "checkbox": cb,
                "slider": opacity_slider,
                "value_label": opacity_value
            }
            layers_layout.addWidget(layer_widget)

        sidebar_layout.addWidget(layers_card, 1)
        sidebar_layout.addStretch()

        # ============ MAIN VIEWER ============
        self.viewer_container = QFrame()
        viewer_layout = QVBoxLayout(self.viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)

        stats_row = QHBoxLayout()
        stats_row.setContentsMargins(10, 6, 10, 0)
        stats_row.setSpacing(0)
        stats_row.addStretch()

        stats_card = QFrame()
        stats_card.setObjectName("StatsCard")
        stats_card.setMaximumWidth(240)
        stats_card.setStyleSheet("""
            QFrame#StatsCard {
                background: rgba(15, 23, 42, 0.60);
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 10px;
            }
        """)
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        stats_layout.setSpacing(4)

        stats_title = QLabel("Quick Statistics")
        stats_title.setObjectName("CardTitle")
        stats_layout.addWidget(stats_title)

        stats_hint = QLabel("Load a segmentation file to refresh these values")
        stats_hint.setObjectName("StatHint")
        stats_hint.setWordWrap(True)
        stats_layout.addWidget(stats_hint)

        stats_rows = [
            ("File", "No file loaded"),
            ("Brain voxels", "0"),
            ("Tumor voxels", "0"),
            ("Tumor volume", "0.0 mm³"),
        ]
        for label_text, value_text in stats_rows:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            label = QLabel(label_text)
            label.setStyleSheet("color: #93c5fd; font-size: 9px; font-weight: 700; background: transparent; border: none;")
            value = QLabel(value_text)
            value.setObjectName("StatValue")
            value.setWordWrap(True)
            row.addWidget(label)
            row.addWidget(value, 1)
            stats_layout.addLayout(row)
            self.sidebar_stat_labels[label_text] = value

        stats_row.addWidget(stats_card)
        viewer_layout.addLayout(stats_row)

        # Placeholder shown while renderer initializes
        self.pv_widget = None
        self._renderer_placeholder = QLabel("Initializing 3D renderer...")
        self._renderer_placeholder.setStyleSheet("color: #94a3b8; padding: 24px;")
        viewer_layout.addWidget(self._renderer_placeholder)

        # Start background thread to import heavy renderer modules
        class RendererImportThread(QThread):
            finished = Signal(object, object)
            error = Signal(str)

            def run(self):
                try:
                    import pyvista as _pv
                    from pyvistaqt import QtInteractor as _QtInteractor
                    self.finished.emit(_pv, _QtInteractor)
                except Exception as e:
                    self.error.emit(str(e))

        self._renderer_thread = RendererImportThread()
        self._renderer_thread.finished.connect(self._on_renderer_ready)
        self._renderer_thread.error.connect(self._on_renderer_error)
        self._renderer_thread.start()

        splitter.addWidget(sidebar)
        splitter.addWidget(self.viewer_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([270, 1090])

        main_layout.addWidget(splitter)

    def _on_renderer_ready(self, _pv, _QtInteractor):
        """Called when renderer modules are imported in background thread."""
        global pv, QtInteractor
        pv = _pv
        QtInteractor = _QtInteractor

        try:
            self.pv_widget = QtInteractor(self.viewer_container)
            self.pv_widget.set_background("#ffffff")

            # Improve lighting to reduce shadows
            # Disable shadows for clearer visibility from all angles
            self.pv_widget.disable_shadows()
            
            # Add headlight for even illumination (reduces dark areas from all angles)
            self.pv_widget.add_light(pv.Light(intensity=0.8, light_type='headlight'))
            self.pv_widget.add_light(pv.Light(intensity=0.35, light_type='scenelight'))

            # remove placeholder and add widget
            if getattr(self, "_renderer_placeholder", None) is not None:
                self._renderer_placeholder.setParent(None)
                self._renderer_placeholder = None

            self.viewer_container.layout().addWidget(self.pv_widget)
            
            # Add XYZ axes widget
            self.pv_widget.show_axes()
            
            self._picker = pv._vtk.vtkCellPicker()
            self._picker.SetTolerance(0.005)
            self.pv_widget.setMouseTracking(True)
            self.pv_widget.installEventFilter(self)

            if self.seg_volume is not None and self.t1_volume is not None:
                self.init_3d()

            self.pv_widget.render()
        except Exception as e:
            err = QLabel(f"3D Viewer init failed: {str(e)}")
            err.setStyleSheet("color: #dc2626; font-weight: 600; padding: 20px;")
            if getattr(self, "_renderer_placeholder", None) is not None:
                self._renderer_placeholder.setParent(None)
                self._renderer_placeholder = None
            self.viewer_container.layout().addWidget(err)

    def _on_renderer_error(self, msg):
        self.pv_widget = None
        err = QLabel(f"3D Viewer failed: {msg}")
        err.setStyleSheet("color: #dc2626; font-weight: 600; padding: 20px;")
        if getattr(self, "_renderer_placeholder", None) is not None:
            self._renderer_placeholder.setParent(None)
            self._renderer_placeholder = None
        self.viewer_container.layout().addWidget(err)

    def import_seg_file(self):
        self._import_seg_file_into(self)

    def configure_case_segmentation_selector(self, segmentations, current_index, on_display):
        """Replace the import action with a segmentation selector for case-bound viewers."""
        self.clear_case_segmentation_selector()

        if not segmentations:
            self.import_btn.setVisible(False)
            self.file_label.setText("No segmentation files available")
            return

        self._case_segmentation_items = list(segmentations)
        self._case_segmentation_callback = on_display
        self.import_btn.setVisible(False)

        selector = QComboBox()
        selector.setMaxVisibleItems(12)
        for idx, seg_info in enumerate(self._case_segmentation_items):
            seg_name = seg_info.get("name", f"Segmentation {idx + 1}")
            selector.addItem(seg_name, idx)

        if 0 <= current_index < selector.count():
            selector.setCurrentIndex(current_index)
        selector.currentIndexChanged.connect(self._on_case_segmentation_changed)

        display_btn = QPushButton("Display Selected")
        display_btn.setObjectName("ImportButton")
        display_btn.clicked.connect(self._display_selected_case_segmentation)

        self._case_segmentation_selector = selector
        self._case_segmentation_display_btn = display_btn
        self.info_layout.addWidget(selector)
        self.info_layout.addWidget(display_btn)

        self._on_case_segmentation_changed(selector.currentIndex())

    def clear_case_segmentation_selector(self):
        if self._case_segmentation_selector is not None:
            self._case_segmentation_selector.deleteLater()
            self._case_segmentation_selector = None
        if self._case_segmentation_display_btn is not None:
            self._case_segmentation_display_btn.deleteLater()
            self._case_segmentation_display_btn = None
        self._case_segmentation_items = []
        self._case_segmentation_callback = None
        if hasattr(self, "import_btn"):
            self.import_btn.setVisible(True)

    def _on_case_segmentation_changed(self, index):
        if index < 0 or index >= len(self._case_segmentation_items):
            return
        seg_info = self._case_segmentation_items[index]
        seg_name = seg_info.get("name", f"Segmentation {index + 1}")
        self.file_label.setText(f"Selected: {seg_name}")

    def _display_selected_case_segmentation(self):
        if self._case_segmentation_selector is None:
            return
        idx = self._case_segmentation_selector.currentIndex()
        if idx < 0 or idx >= len(self._case_segmentation_items):
            return
        if callable(self._case_segmentation_callback):
            self._case_segmentation_callback(idx, self._case_segmentation_items[idx])

    def request_split_view(self):
        if self.peer_viewer is not None and hasattr(self.peer_viewer, "ensure_split_view"):
            self.peer_viewer.ensure_split_view()

    def go_back_to_landing_page(self):
        viewer = self.peer_viewer
        if viewer is not None and hasattr(viewer, "go_to_landing_page"):
            viewer.go_to_landing_page()
            return

        widget = self
        while widget is not None:
            if hasattr(widget, "show_landing_page"):
                widget.show_landing_page()
                return
            widget = widget.parentWidget()

    def close_pane(self):
        """Close/hide this pane if it's the right pane in a split view."""
        if self.peer_viewer is not None and hasattr(self.peer_viewer, "remove_pane"):
            self.peer_viewer.remove_pane(self)

    def import_seg_file_to_peer(self):
        seg_file, t1_file = self._pick_segmentation_pair()
        if not seg_file or not t1_file:
            return

        viewer = self.peer_viewer
        if viewer is not None and hasattr(viewer, "ensure_split_view"):
            target_viewer = viewer.ensure_split_view()
        else:
            target_viewer = viewer or self

        try:
            target_viewer.current_file = os.path.basename(seg_file)
            target_viewer.file_label.setText(f"<b>Loaded:</b> {target_viewer.current_file}")
            target_viewer.load_volumes(seg_file, t1_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load files: {str(e)}")

    def set_peer_viewer(self, peer_viewer):
        self.peer_viewer = peer_viewer

    def _pick_segmentation_pair(self):
        seg_file, _ = QFileDialog.getOpenFileName(self, "Select Segmentation File", "", "*.nii.gz;;*.nii")
        if not seg_file:
            return None, None

        folder = os.path.dirname(seg_file)
        t1_file = next((os.path.join(folder, f) for f in os.listdir(folder) if "t1" in f.lower()), None)

        if not t1_file:
            QMessageBox.critical(self, "Error", "T1 file not found in the same directory")
            return None, None

        return seg_file, t1_file

    def _import_seg_file_into(self, target_viewer):
        seg_file, t1_file = self._pick_segmentation_pair()
        if not seg_file or not t1_file:
            return

        try:
            target_viewer.current_file = os.path.basename(seg_file)
            target_viewer.file_label.setText(f"<b>Loaded:</b> {target_viewer.current_file}")
            target_viewer.load_volumes(seg_file, t1_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load files: {str(e)}")

    def load_volumes(self, seg, t1):
        try:
            seg_img = nib.load(seg)
            t1_img = nib.load(t1)
            self.seg_volume = seg_img.get_fdata()
            self.t1_volume = t1_img.get_fdata()
            self.voxel_volume_mm3 = float(np.prod(t1_img.header.get_zooms()[:3]))
            self.init_3d()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load volume data: {str(e)}")

    def on_segmentation_mode_changed(self, index):
        mode = self.segmentation_mode_selector.currentData()
        self.segmentation_mode = mode
        # If volumes are loaded, re-render using the selected interpretation
        if self.seg_volume is not None and self.t1_volume is not None:
            try:
                self.init_3d()
            except Exception:
                pass

    def init_3d(self):
        """Initialize 3D visualization with enhanced meshes."""
        if self.pv_widget is None:
            return

        try:
            self.pv_widget.clear()
            self.meshes.clear()
            self.actor_lookup.clear()
            self.region_stats.clear()

            # Process T1 volume - brain surface with smoothing
            t1_normalized = (self.t1_volume - self.t1_volume.min()) / (self.t1_volume.max() - self.t1_volume.min() + 1e-5)
            threshold = np.percentile(t1_normalized, 15)
            brain_mask = t1_normalized >= threshold
            self.brain_volume_voxels = int(np.count_nonzero(brain_mask))

            # Determine which labels represent lesion regions for this segmentation.
            present_labels = sorted(list(np.unique(self.seg_volume).astype(int)))

            if self.segmentation_mode == 'ischemia':
                # Force interpret as ischemia (label 1 == lesion)
                class_labels[1] = "Ischemic Lesion"
                colors[1] = [1.0, 0.1, 0.1]
                color_hex[1] = "#FF1A1A"
                lesion_labels = [1]
            elif self.segmentation_mode == 'tumor':
                lesion_labels = [l for l in [1, 2, 3, 4] if l in present_labels]
            else:
                # Auto mode: if only {0,1} present, treat as ischemia; otherwise tumor labels
                if set(present_labels).issubset({0, 1}):
                    class_labels[1] = "Ischemic Lesion"
                    colors[1] = [1.0, 0.1, 0.1]
                    color_hex[1] = "#FF1A1A"
                    lesion_labels = [1]
                else:
                    lesion_labels = [l for l in [1, 2, 3, 4] if l in present_labels]

            self.tumor_volume_voxels = int(np.count_nonzero(np.isin(self.seg_volume, lesion_labels)))

            for label in lesion_labels:
                voxels = int(np.count_nonzero(self.seg_volume == label))
                self.region_stats[label] = {
                    "voxels": voxels,
                    "volume_mm3": voxels * self.voxel_volume_mm3,
                    "brain_pct": (voxels / self.brain_volume_voxels * 100.0) if self.brain_volume_voxels else 0.0,
                    "tumor_pct": (voxels / self.tumor_volume_voxels * 100.0) if self.tumor_volume_voxels else 0.0,
                }

            brain_voxels = int(np.count_nonzero(brain_mask))
            self.region_stats[0] = {
                "voxels": brain_voxels,
                "volume_mm3": brain_voxels * self.voxel_volume_mm3,
                "brain_pct": 100.0,
                "tumor_pct": 0.0,
            }
            
            verts, faces, _, _ = measure.marching_cubes(t1_normalized, threshold)
            
            # Scale vertices if needed
            if len(verts) > 0:
                faces = np.hstack([[3, *f] for f in faces])
                mesh = pv.PolyData(verts, faces)
                
                # Smooth the brain surface mesh (reduced iterations for speed)
                mesh = mesh.smooth(n_iter=80, relaxation_factor=0.1)
                
                self.meshes[0] = self.pv_widget.add_mesh(
                    mesh, 
                    color=colors[0], 
                    opacity=self.layer_opacities[0],
                    edge_color=None,
                    show_edges=False,
                    smooth_shading=True,
                    ambient=0.75,
                    diffuse=0.55,
                    specular=0.05,
                    specular_power=10
                )
                self.actor_lookup[self._actor_key(self.meshes[0])] = 0

            # Process segmentation labels (use the lesion_labels determined earlier)
            for label in lesion_labels:
                mask = (self.seg_volume == label)
                if np.sum(mask) < 100:  # Skip very small regions
                    continue

                verts, faces, _, _ = measure.marching_cubes(mask.astype(float), 0.5)

                if len(verts) > 0:
                    faces = np.hstack([[3, *f] for f in faces])
                    mesh = pv.PolyData(verts, faces)
                    
                    # Smooth segmentation meshes for better visualization (reduced iterations)
                    mesh = mesh.smooth(n_iter=50, relaxation_factor=0.15)
                    
                    self.meshes[label] = self.pv_widget.add_mesh(
                        mesh, 
                        color=colors.get(label, [1.0, 0.1, 0.1]), 
                        opacity=self.layer_opacities.get(label, 0.85),
                        edge_color=None,
                        show_edges=False,
                        smooth_shading=True,
                        ambient=0.75,
                        diffuse=0.55,
                        specular=0.05,
                        specular_power=10
                    )
                    self.actor_lookup[self._actor_key(self.meshes[label])] = label

            # Configure viewer appearance
            self.pv_widget.set_background("#ffffff")
            self.pv_widget.renderer.ResetCamera()
            
            # Set up better lighting
            self.pv_widget.renderer.RemoveAllLights()
            light = pv.Light()
            light.SetPosition(1, 1, 1)
            light.SetFocalPoint(0, 0, 0)
            light.SetIntensity(1.0)
            self.pv_widget.renderer.AddLight(light)
            
            light2 = pv.Light()
            light2.SetPosition(-1, -1, 0.5)
            light2.SetFocalPoint(0, 0, 0)
            light2.SetIntensity(0.4)
            self.pv_widget.renderer.AddLight(light2)
            
            self._refresh_sidebar_stats()
            self.pv_widget.render()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to render 3D visualization: {str(e)}")

    def _refresh_sidebar_stats(self):
        """Update the compact sidebar statistics after a volume loads."""
        file_label = self.sidebar_stat_labels.get("File")
        if file_label is not None:
            file_label.setText(self.current_file or "No file loaded")

        brain_label = self.sidebar_stat_labels.get("Brain voxels")
        if brain_label is not None:
            brain_label.setText(f"{self.brain_volume_voxels:,}")

        tumor_label = self.sidebar_stat_labels.get("Tumor voxels")
        if tumor_label is not None:
            tumor_label.setText(f"{self.tumor_volume_voxels:,}")

        tumor_volume_label = self.sidebar_stat_labels.get("Tumor volume")
        if tumor_volume_label is not None:
            tumor_volume_mm3 = self.tumor_volume_voxels * self.voxel_volume_mm3
            tumor_volume_label.setText(f"{tumor_volume_mm3:,.1f} mm³")

    def apply_display_settings(self):
        """Apply display settings like background color."""
        if not self.pv_widget:
            return

        self.pv_widget.set_background("#ffffff")
        self.pv_widget.render()

    def eventFilter(self, obj, event):
        if obj is getattr(self, "pv_widget", None) and getattr(self, "_picker", None):
            if event.type() == QEvent.Leave:
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def _actor_key(self, actor):
        try:
            return actor.GetAddressAsString("")
        except Exception:
            return str(id(actor))

    def _show_hover_info(self, event):
        if not self.pv_widget or not self.region_stats:
            return

        pos = event.position().toPoint()
        if not self._picker.Pick(pos.x(), pos.y(), 0, self.pv_widget.renderer):
            QToolTip.hideText()
            return

        picked_actor = self._picker.GetActor()
        if picked_actor is None:
            QToolTip.hideText()
            return

        label_id = self.actor_lookup.get(self._actor_key(picked_actor))
        if label_id is None:
            QToolTip.hideText()
            return

        tooltip_text = self._format_hover_text(label_id)
        QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self.pv_widget)

    def _format_hover_text(self, label_id):
        name = class_labels.get(label_id, "Unknown Region")
        stats = self.region_stats.get(label_id, {})
        volume_mm3 = stats.get("volume_mm3", 0.0)
        brain_pct = stats.get("brain_pct", 0.0)
        tumor_pct = stats.get("tumor_pct", 0.0)

        if label_id == 0:
            return (
                f"{name}\n"
                f"Estimated volume: {volume_mm3:,.1f} mm³\n"
                f"Brain reference: 100%"
            )

        return (
            f"{name}\n"
            f"Volume: {volume_mm3:,.1f} mm³\n"
            f"Share of brain: {brain_pct:.2f}%\n"
            f"Share of tumor: {tumor_pct:.2f}%"
        )

    def set_layer_opacity(self, label_id, opacity):
        """Update opacity for a specific segmentation layer."""
        self.layer_opacities[label_id] = opacity
        
        if label_id in self.meshes and self.pv_widget:
            actor = self.meshes[label_id]
            actor.GetProperty().SetOpacity(opacity)
            self.pv_widget.render()
        
        # Update label display
        if label_id in self.layer_controls:
            self.layer_controls[label_id]["value_label"].setText(f"{int(opacity * 100)}%")

    def update_mesh_visibility(self):
        """Toggle visibility of segmentation layers."""
        if not self.pv_widget:
            return

        for label_id, controls in self.layer_controls.items():
            actor = self.meshes.get(label_id)
            if actor:
                actor.SetVisibility(controls["checkbox"].isChecked())

        self.pv_widget.render()


class SegmentationViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Segmentation Viewer - DeepNeuro")
        self.setMinimumSize(1260, 720)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.left_pane = SegmentationPane()
        self.right_pane = None
        self.left_pane.set_peer_viewer(self)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)

        self.right_placeholder = QFrame()
        self.right_placeholder.setMinimumWidth(0)
        self.right_placeholder.setStyleSheet("background: transparent; border: none;")

        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.right_placeholder)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([1260, 0])

        root.addWidget(self.splitter)

    def ensure_split_view(self):
        if self.right_pane is not None:
            return self.right_pane

        self.right_pane = SegmentationPane()
        self.right_pane.set_peer_viewer(self)
        self.left_pane.set_peer_viewer(self)

        # Show close buttons now that we're in split view
        self.left_pane.close_btn.setVisible(True)
        self.right_pane.close_btn.setVisible(True)

        # Use persistent placeholder and widget lookup instead of fixed index
        placeholder_index = self.splitter.indexOf(self.right_placeholder)
        if placeholder_index == -1:
            # If placeholder lost parent, reattach it
            if self.right_placeholder.parent() is not None:
                self.right_placeholder.setParent(None)
            if self.splitter.count() < 2:
                self.splitter.addWidget(self.right_placeholder)
            else:
                self.splitter.insertWidget(1, self.right_placeholder)
            placeholder_index = self.splitter.indexOf(self.right_placeholder)

        if placeholder_index == -1:
            # can't find slot to place right pane
            self.right_pane = None
            return None

        old_placeholder = self.splitter.replaceWidget(placeholder_index, self.right_pane)
        if old_placeholder is not None and old_placeholder is not self.right_placeholder:
            old_placeholder.setParent(None)
            old_placeholder.deleteLater()

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([630, 630])
        return self.right_pane

    def remove_pane(self, pane_widget):
        """Remove the given pane (left or right). Keep remaining pane if present.

        If removing the left pane and a right pane exists, shift the right pane
        into the left position and clear the right side. If removing the right
        pane, replace it with a placeholder.
        """
        # If request is to remove right pane
        if pane_widget is self.right_pane:
            # Hide close buttons
            try:
                self.left_pane.close_btn.setVisible(False)
            except Exception:
                pass
            try:
                self.right_pane.close_btn.setVisible(False)
            except Exception:
                pass

            # Clear peer references in right pane (it's being deleted)
            try:
                self.right_pane.peer_viewer = None
            except Exception:
                pass

            # Clear the left pane's peer_viewer to allow fresh split next time
            try:
                self.left_pane.peer_viewer = None
            except Exception:
                pass

            # Replace right pane with persistent placeholder
            placeholder_index = self.splitter.indexOf(self.right_pane)
            if placeholder_index == -1:
                placeholder_index = self.splitter.indexOf(self.right_placeholder)
            if placeholder_index == -1:
                # ensure placeholder exists
                self.splitter.addWidget(self.right_placeholder)
                placeholder_index = self.splitter.indexOf(self.right_placeholder)
            else:
                self.splitter.replaceWidget(placeholder_index, self.right_placeholder)
            self.right_pane = None
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 0)
            self.splitter.setSizes([1260, 0])
            
            # Re-establish peer_viewer for left pane pointing to self (SegmentationViewer)
            try:
                self.left_pane.peer_viewer = self
            except Exception:
                pass
            return

        # If request is to remove left pane
        if pane_widget is self.left_pane:
            if self.right_pane is not None:
                # Move right pane into left slot
                new_left = self.right_pane
                # Replace left widget with new_left using index lookup
                left_index = self.splitter.indexOf(self.left_pane)
                if left_index != -1:
                    old_left = self.splitter.replaceWidget(left_index, new_left)
                    if old_left is not None:
                        old_left.setParent(None)
                        old_left.deleteLater()
                else:
                    # left pane not found; abort
                    return

                # Ensure persistent placeholder occupies the right slot
                right_index = self.splitter.indexOf(self.right_placeholder)
                if right_index == -1:
                    # insert placeholder after new left
                    self.splitter.insertWidget(left_index + 1, self.right_placeholder)
                elif right_index != left_index + 1:
                    self.splitter.replaceWidget(right_index, self.right_placeholder)

                # Update references
                self.left_pane = new_left
                self.left_pane.set_peer_viewer(self)
                self.right_pane = None

                # Hide close buttons
                try:
                    self.left_pane.close_btn.setVisible(False)
                except Exception:
                    pass

                self.splitter.setStretchFactor(0, 1)
                self.splitter.setStretchFactor(1, 0)
                self.splitter.setSizes([1260, 0])
                return

            # No right pane to keep; hide the whole viewer
            try:
                self.hide()
            except Exception:
                pass
            return

    def remove_right_pane(self):
        """Remove/hide the right pane and return to single-pane view."""
        if self.right_pane is None:
            return

        # Hide close buttons
        self.left_pane.close_btn.setVisible(False)
        self.right_pane.close_btn.setVisible(False)

        # Ensure persistent placeholder exists for right side
        if not hasattr(self, "right_placeholder") or self.right_placeholder is None:
            self.right_placeholder = QFrame()
            self.right_placeholder.setMinimumWidth(0)
            self.right_placeholder.setStyleSheet("background: transparent; border: none;")

        # Replace right pane using index lookup
        right_index = self.splitter.indexOf(self.right_pane)
        if right_index == -1:
            right_index = self.splitter.indexOf(self.right_placeholder)
        if right_index == -1:
            # attach placeholder at end
            self.splitter.addWidget(self.right_placeholder)
            right_index = self.splitter.indexOf(self.right_placeholder)

        old_pane = self.splitter.replaceWidget(right_index, self.right_placeholder)
        if old_pane is not None and old_pane is not self.right_placeholder:
            old_pane.setParent(None)
            old_pane.deleteLater()

        # Reset split factors
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([1260, 0])

        self.right_pane = None

    def open_secondary_view(self):
        self.ensure_split_view()

    def go_to_landing_page(self):
        widget = self.parentWidget()
        while widget is not None:
            if hasattr(widget, "show_landing_page"):
                widget.show_landing_page()
                return
            widget = widget.parentWidget()

    def closeEvent(self, event):
        self.hide()
        event.ignore()


if __name__ == "__main__":
    # Optional: helps avoid GPU/OpenGL issues on some Windows setups
    os.environ["QT_OPENGL"] = "software"

    app = QApplication(sys.argv)

    # Optional: better global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = SegmentationViewer()
    window.show()

    sys.exit(app.exec())