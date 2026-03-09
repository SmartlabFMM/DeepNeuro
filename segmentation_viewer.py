import nibabel as nib
import numpy as np
from skimage import measure
import pyvista as pv
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QFileDialog, QMessageBox, QSizePolicy
from pyvistaqt import QtInteractor
import os

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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        from PySide6.QtWidgets import QLabel
        from PySide6.QtGui import QFont
        from PySide6.QtCore import Qt
        
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
        checkbox_layout.setSpacing(10)
        
        for label, name in class_labels.items():
            cb = QCheckBox(name)
            cb.setChecked(True)
            rgb = [int(255 * c) for c in colors[label]]
            cb.setStyleSheet(f"""
                QCheckBox {{ 
                    color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); 
                    font-weight: 600; 
                    font-size: 10px;
                }}
            """)
            cb.stateChanged.connect(self.update_mesh_visibility)
            self.checkboxes[label] = cb
            checkbox_layout.addWidget(cb)
        
        layout.addWidget(checkbox_container)

        # Import button
        import_btn = QPushButton("Import Segmentation")
        import_btn.setStyleSheet("""
            QPushButton {
                background: #2d3748;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1f2937;
            }
            QPushButton:pressed {
                background: #111827;
            }
        """)
        import_btn.clicked.connect(self.import_seg_file)
        from PySide6.QtCore import Qt
        import_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(import_btn)

        # PyVista widget
        self.pv_widget = QtInteractor(self)
        self.pv_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pv_widget.setStyleSheet("""
            QtInteractor {
                background: #111827;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.pv_widget)
        
        # Instructions
        instructions = QLabel("Select a segmentation file (.nii.gz) to visualize the 3D model")
        instructions.setFont(QFont("Segoe UI", 8))
        instructions.setStyleSheet("color: #718096; padding: 2px;")
        instructions.setAlignment(Qt.AlignLeft)
        layout.addWidget(instructions)

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
        self.seg_volume = nib.load(seg_file).get_fdata()
        self.t1_volume = nib.load(t1_path).get_fdata()
        self.t1_volume = (self.t1_volume - np.min(self.t1_volume)) / (np.max(self.t1_volume) - np.min(self.t1_volume))
        
        for cb in self.checkboxes.values():
            cb.setChecked(True)
        
        self.init_3d()

    def init_3d(self):
        self.pv_widget.clear()
        
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
        for label, cb in self.checkboxes.items():
            actor = self.meshes.get(label)
            if actor:
                actor.SetVisibility(cb.isChecked())
        self.pv_widget.render()
