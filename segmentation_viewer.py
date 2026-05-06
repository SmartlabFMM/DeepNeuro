import os
import sys

# Set OpenGL to software mode BEFORE any Qt imports to prevent VTK blocking
# Advanced VTK/PyOpenGL overrides are platform-specific; only apply them on Linux
os.environ["QT_OPENGL"] = "software"
if sys.platform.startswith("linux"):
    os.environ["QT_XCB_GL_INTEGRATION"] = "xcb_glx"
    os.environ["PYOPENGL_PLATFORM"] = "osmesa"  # Force off-screen Mesa rendering for VTK on Linux

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


class SegmentationViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SegmentationViewerRoot")
        self.setWindowTitle("3D Segmentation Viewer - DeepNeuro")
        self.setMinimumSize(1260, 720)
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
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)

        # Sidebar header
        sidebar_eyebrow = QLabel("SEGMENTATION VIEWER")
        sidebar_eyebrow.setObjectName("SidebarEyebrow")
        sidebar_title = QLabel("3D Visualization")
        sidebar_title.setObjectName("SidebarTitle")
        sidebar_subtitle = QLabel("Import segmentation file and adjust visualization parameters")
        sidebar_subtitle.setObjectName("SidebarSubtitle")
        sidebar_subtitle.setWordWrap(True)

        sidebar_layout.addWidget(sidebar_eyebrow)
        sidebar_layout.addWidget(sidebar_title)
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

        import_btn = QPushButton("Import Segmentation File")
        import_btn.setObjectName("ImportButton")
        import_btn.clicked.connect(self.import_seg_file)
        info_layout.addWidget(import_btn)

        sidebar_layout.addWidget(info_card)

        # Display settings card
        settings_card = QFrame()
        settings_card.setObjectName("SidebarCard")
        settings_card.setMinimumHeight(96)
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(4)

        settings_title = QLabel("Display Settings")
        settings_title.setObjectName("CardTitle")
        settings_layout.addWidget(settings_title)

        # Background
        bg_label = QLabel("Background")
        bg_label.setStyleSheet("color: #cbd5e1; font-size: 9px; font-weight: 700; background: transparent; border: none;")
        self.bg_combo = QComboBox()
        self.bg_combo.addItem("White")
        self.bg_combo.setCurrentIndex(0)
        self.bg_combo.setEnabled(False)
        settings_layout.addWidget(bg_label)
        settings_layout.addWidget(self.bg_combo)

        sidebar_layout.addWidget(settings_card)

        # Layers card
        layers_card = QFrame()
        layers_card.setObjectName("SidebarDarkCard")
        layers_layout = QVBoxLayout(layers_card)
        layers_layout.setContentsMargins(8, 8, 8, 8)
        layers_layout.setSpacing(6)

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
                    border-radius: 7px;
                    border-left: 4px solid {color_hex[label_id]};
                }}
            """)
            layer_layout = QVBoxLayout(layer_widget)
            layer_layout.setContentsMargins(7, 5, 7, 5)
            layer_layout.setSpacing(3)

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

            # remove placeholder and add widget
            if getattr(self, "_renderer_placeholder", None) is not None:
                self._renderer_placeholder.setParent(None)
                self._renderer_placeholder = None

            self.viewer_container.layout().addWidget(self.pv_widget)
            self._picker = pv._vtk.vtkCellPicker()
            self._picker.SetTolerance(0.005)
            self.pv_widget.setMouseTracking(True)
            self.pv_widget.installEventFilter(self)
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
        seg_file, _ = QFileDialog.getOpenFileName(self, "Select Segmentation File", "", "*.nii.gz;;*.nii")
        if not seg_file:
            return

        folder = os.path.dirname(seg_file)
        t1_file = next((os.path.join(folder, f) for f in os.listdir(folder) if "t1" in f.lower()), None)

        if not t1_file:
            QMessageBox.critical(self, "Error", "T1 file not found in the same directory")
            return

        try:
            self.current_file = os.path.basename(seg_file)
            self.file_label.setText(f"<b>Loaded:</b> {self.current_file}")
            self.load_volumes(seg_file, t1_file)
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
            self.tumor_volume_voxels = int(np.count_nonzero(np.isin(self.seg_volume, [1, 2, 3, 4])))

            for label in [1, 2, 3, 4]:
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
                    show_edges=False
                )
                self.actor_lookup[self._actor_key(self.meshes[0])] = 0

            # Process segmentation labels
            for label in [1, 2, 3, 4]:
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
                        color=colors[label], 
                        opacity=self.layer_opacities[label],
                        edge_color=None,
                        show_edges=False
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
            
            self.pv_widget.render()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to render 3D visualization: {str(e)}")

    def apply_display_settings(self):
        """Apply display settings like background color."""
        if not self.pv_widget:
            return

        self.pv_widget.set_background("#ffffff")
        self.pv_widget.render()

    def eventFilter(self, obj, event):
        if obj is getattr(self, "pv_widget", None) and getattr(self, "_picker", None):
            if event.type() == QEvent.MouseMove:
                self._show_hover_info(event)
            elif event.type() == QEvent.Leave:
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