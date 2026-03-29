import os
from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

class_labels = {
    0: "Brain Surface",
    1: "Necrotic/Non-enhancing Tumor",
    2: "Edema",
    3: "Enhancing Tumor",
    4: "Resection Cavity"
}
colors = {
    0: [0.5, 0.5, 0.5],
    1: [0.0, 0.0, 0.0],
    2: [0.5, 1.0, 0.5],
    3: [1.0, 0.2, 0.2],
    4: [0.2, 0.4, 1.0]
}

class SegmentationViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Segmentation Viewer - DeepNeuro")
        self.setMinimumSize(620, 420)
        self.meshes = {}
        self.seg_volume = None
        self.t1_volume = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title and option section
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(12)
        
        title = QLabel("Segmentation Control Panel")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #2d3748;")
        header_layout.addWidget(title)
        
        # Checkboxes container
        self.checkboxes = {}
        checkbox_container = QWidget()
        checkbox_container.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setSpacing(12)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        
        for label, name in class_labels.items():
            cb = QCheckBox(name)
            cb.setChecked(True)
            rgb = [int(255 * c) for c in colors[label]]
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: #2d3748;
                    font-weight: 500;
                    font-size: 10px;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 2px solid #cbd5e0;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]});
                    border-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]});
                }}
            """)
            cb.stateChanged.connect(self.update_mesh_visibility)
            self.checkboxes[label] = cb
            checkbox_layout.addWidget(cb)
        
        checkbox_layout.addStretch()
        header_layout.addWidget(checkbox_container)
        layout.addWidget(header_frame)
        
        # Main content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background: white;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        # Import button
        import_btn = QPushButton("Import Segmentation File")
        import_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        import_btn.setMinimumHeight(40)
        import_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6941a5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bc4, stop:1 #5d3a94);
            }
        """)
        import_btn.clicked.connect(self.import_seg_file)
        import_btn.setCursor(Qt.PointingHandCursor)
        content_layout.addWidget(import_btn)

        # Plot area (lazy 3D widget creation avoids lag when opening viewer)
        self.pv_widget = None
        self.plot_container = QFrame()
        self.plot_container.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setSpacing(0)

        self.plot_hint = QLabel("Select a segmentation file to visualize the 3D brain model")
        self.plot_hint.setFont(QFont("Segoe UI", 11))
        self.plot_hint.setStyleSheet("color: #718096;")
        self.plot_hint.setAlignment(Qt.AlignCenter)
        self.plot_layout.addWidget(self.plot_hint)

        content_layout.addWidget(self.plot_container, 1)
        layout.addWidget(content_frame, 1)
        
        # Footer instructions
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border-top: 1px solid #e2e8f0;
            }
        """)
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 12, 20, 12)
        footer_layout.setSpacing(0)
        
        instructions = QLabel("💡 Select a .nii.gz segmentation file to load. The corresponding -t1n.nii.gz file must be in the same folder.")
        instructions.setFont(QFont("Segoe UI", 9))
        instructions.setStyleSheet("color: #718096;")
        instructions.setWordWrap(True)
        footer_layout.addWidget(instructions)
        layout.addWidget(footer_frame)

    def ensure_plotter(self):
        if self.pv_widget is not None:
            return

        from pyvistaqt import QtInteractor

        self.pv_widget = QtInteractor(self)
        self.pv_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pv_widget.setStyleSheet("""
            QtInteractor {
                background: #1f2937;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

        for i in reversed(range(self.plot_layout.count())):
            item = self.plot_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        self.plot_layout.addWidget(self.pv_widget)

    def import_seg_file(self):
        seg_file, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Segmentation File", 
            "", 
            "NIfTI files (*.nii.gz);;All files (*.*)"
        )
        if not seg_file:
            return
        
        folder = os.path.dirname(seg_file)
        t1n_file = next((os.path.join(folder, f) for f in os.listdir(folder) if f.endswith("-t1n.nii.gz")), None)
        
        if t1n_file is None:
            QMessageBox.critical(
                self, 
                "Error", 
                "Could not find corresponding t1n.nii.gz file in the same folder.\n\n"
                "Please ensure both files are in the same directory."
            )
            return
        
        try:
            self.load_volumes(seg_file, t1n_file)
            QMessageBox.information(
                self,
                "Success",
                "Segmentation file loaded successfully!\n\n"
                "Use the checkboxes to toggle visibility of different regions."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load segmentation file:\n\n{str(e)}"
            )

    def load_volumes(self, seg_file, t1_path):
        import nibabel as nib
        import numpy as np

        self.seg_volume = nib.load(seg_file).get_fdata()
        self.t1_volume = nib.load(t1_path).get_fdata()
        t1_min = np.min(self.t1_volume)
        t1_max = np.max(self.t1_volume)
        denom = t1_max - t1_min
        if denom > 0:
            self.t1_volume = (self.t1_volume - t1_min) / denom
        else:
            self.t1_volume = np.zeros_like(self.t1_volume)
        
        for cb in self.checkboxes.values():
            cb.setChecked(True)
        
        self.init_3d()

    def init_3d(self):
        import numpy as np
        import pyvista as pv
        from skimage import measure

        self.ensure_plotter()
        self.pv_widget.clear()
        self.meshes.clear()
        
        # Brain surface
        verts, faces, _, _ = measure.marching_cubes(self.t1_volume, level=0.1)
        faces = np.hstack([[3, *face] for face in faces])
        brain_mesh = pv.PolyData(verts, faces)
        self.meshes[0] = self.pv_widget.add_mesh(
            brain_mesh, 
            color=colors[0], 
            opacity=0.1, 
            name="Brain Surface"
        )

        # Segmentation regions
        for label in [1, 2, 3, 4]:
            mask = (self.seg_volume == label)
            if np.sum(mask) == 0:
                continue
            
            verts, faces, _, _ = measure.marching_cubes(mask, level=0)
            faces = np.hstack([[3, *face] for face in faces])
            mesh = pv.PolyData(verts, faces)
            self.meshes[label] = self.pv_widget.add_mesh(
                mesh, 
                color=colors[label], 
                opacity=0.95, 
                name=class_labels[label]
            )
        
        self.pv_widget.show()

    def update_mesh_visibility(self):
        if self.pv_widget is None:
            return

        for label, cb in self.checkboxes.items():
            actor = self.meshes.get(label)
            if actor:
                actor.SetVisibility(cb.isChecked())
        self.pv_widget.render()
