"""Shared widgets for the extracted doctor case viewer."""

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class DraggableSequenceList(QListWidget):
    """List widget that drags a custom file-key payload."""

    MIME_TYPE = "application/x-deepneuro-seq-key"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDefaultDropAction(Qt.CopyAction)

    def mimeTypes(self):
        return [self.MIME_TYPE]

    def mimeData(self, items):
        mime_data = QMimeData()
        if not items:
            return mime_data

        item = items[0]
        key = str(item.data(Qt.UserRole) or "")
        mime_data.setData(self.MIME_TYPE, key.encode("utf-8"))
        mime_data.setText(item.text())
        return mime_data


class DraggableLayerInfoLabel(QLabel):
    """Simple label used inside the draggable layer info box."""

    MIME_TYPE = "application/x-deepneuro-layer-role"

    def __init__(self, panel_index, layer_role, on_swap_requested, parent=None):
        super().__init__(parent)
        self.panel_index = panel_index
        self.layer_role = layer_role
        self.on_swap_requested = on_swap_requested
        self._drag_start_pos = None
        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(self.MIME_TYPE, self.layer_role.encode("utf-8"))
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)
        self._drag_start_pos = None
        self.setCursor(Qt.OpenHandCursor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return

        source_role = bytes(event.mimeData().data(self.MIME_TYPE)).decode("utf-8")
        if source_role and source_role != self.layer_role and callable(self.on_swap_requested):
            self.on_swap_requested(self.panel_index)
            event.acceptProposedAction()
            return
        event.ignore()

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)


class DraggableLayerInfoBox(QFrame):
    """Draggable info box used to reorder and remove displayed files inside a panel."""

    MIME_TYPE = DraggableLayerInfoLabel.MIME_TYPE

    def __init__(self, panel_index, layer_role, on_swap_requested, on_close_requested=None, parent=None):
        super().__init__(parent)
        self.panel_index = panel_index
        self.layer_role = layer_role
        self.on_swap_requested = on_swap_requested
        self.on_close_requested = on_close_requested
        self._drag_start_pos = None
        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.info_label = DraggableLayerInfoLabel(panel_index, layer_role, on_swap_requested, self)
        self.info_label.setWordWrap(False)
        self.info_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.info_label.setMinimumWidth(0)

        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(18, 18)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setFlat(True)
        self.close_button.clicked.connect(self._handle_close_clicked)

        row.addWidget(self.info_label, 1)
        row.addWidget(self.close_button, 0, Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(row)

    def set_text(self, info_text):
        self.info_label.setText(info_text)

    def set_close_visible(self, visible):
        self.close_button.setVisible(bool(visible))

    def _handle_close_clicked(self):
        if callable(self.on_close_requested):
            self.on_close_requested(self.panel_index, self.layer_role)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(self.MIME_TYPE, self.layer_role.encode("utf-8"))
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)
        self._drag_start_pos = None
        self.setCursor(Qt.OpenHandCursor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return

        source_role = bytes(event.mimeData().data(self.MIME_TYPE)).decode("utf-8")
        if source_role and source_role != self.layer_role and callable(self.on_swap_requested):
            self.on_swap_requested(self.panel_index)
            event.acceptProposedAction()
            return
        event.ignore()

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)


class SequenceDropPanel(QFrame):
    """Drop target panel that displays one sequence slice with colormap."""

    def __init__(self, panel_index, on_drop_file, on_colormap_changed, on_scroll_slice, on_swap_layers, on_close_layer, parent=None):
        super().__init__(parent)
        self.panel_index = panel_index
        self.on_drop_file = on_drop_file
        self.on_colormap_changed = on_colormap_changed
        self.on_scroll_slice = on_scroll_slice
        self.on_swap_layers = on_swap_layers
        self.on_close_layer = on_close_layer
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.title_label = QLabel(f"Panel {panel_index + 1}")
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(["Grayscale", "Hot", "Jet", "Inferno", "Viridis", "Plasma", "Magma", "Bone"])
        self.cmap_combo.setCurrentText("Grayscale")
        self.cmap_combo.setFixedWidth(120)
        self.cmap_combo.currentTextChanged.connect(lambda _text: self.on_colormap_changed(self.panel_index))
        self.cmap_combo.setVisible(False)

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.cmap_combo)

        self.image_label = QLabel("Drop a sequence file here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(190)
        self.image_label.setMaximumHeight(520)

        self.slice_info_label = QLabel("No file assigned")
        self.slice_info_label.setAlignment(Qt.AlignRight)
        self.slice_info_label.setWordWrap(False)

        self.layer_info_container = QWidget()
        self.layer_info_container.setVisible(False)
        layer_info_layout = QVBoxLayout(self.layer_info_container)
        layer_info_layout.setContentsMargins(0, 0, 0, 0)
        layer_info_layout.setSpacing(4)

        self.top_info_box = DraggableLayerInfoBox(panel_index, "top", self._toggle_layer_order, self._close_layer)
        self.bottom_info_box = DraggableLayerInfoBox(panel_index, "bottom", self._toggle_layer_order, self._close_layer)
        layer_info_layout.addWidget(self.top_info_box)
        layer_info_layout.addWidget(self.bottom_info_box)

        root.addLayout(header)
        root.addWidget(self.image_label, 1)
        root.addWidget(self.layer_info_container)
        root.addWidget(self.slice_info_label)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)
        self.apply_contrast_theme(dark_background=False)

    def set_has_sequence(self, has_sequence):
        self.cmap_combo.setVisible(bool(has_sequence))

    def show_layer_boxes(self, show_boxes):
        self.layer_info_container.setVisible(bool(show_boxes))
        self.slice_info_label.setVisible(not bool(show_boxes))

    def set_layer_info(self, top_info, bottom_info, show_boxes):
        self.top_info_box.set_text(top_info)
        self.top_info_box.set_close_visible(bool(top_info))
        self.bottom_info_box.set_text(bottom_info)
        self.bottom_info_box.set_close_visible(bool(bottom_info))
        self.bottom_info_box.setVisible(bool(bottom_info))
        self.show_layer_boxes(show_boxes)

    def _toggle_layer_order(self, panel_index):
        if callable(self.on_swap_layers):
            self.on_swap_layers(panel_index)

    def _close_layer(self, panel_index, layer_role):
        if callable(self.on_close_layer):
            self.on_close_layer(panel_index, layer_role)

    def apply_contrast_theme(self, dark_background):
        if dark_background:
            title_color = "#e2e8f0"
            info_color = "#cbd5e1"
            border_color = "#475569"
            panel_bg = "#111827"
            image_bg = "#0f172a"
            placeholder_color = "#cbd5e1"
            combo_bg = "#0f172a"
            combo_text = "#e2e8f0"
            combo_border = "#475569"
        else:
            title_color = "#334155"
            info_color = "#64748b"
            border_color = "#cbd5e1"
            panel_bg = "#f8fafc"
            image_bg = "#ffffff"
            placeholder_color = "#64748b"
            combo_bg = "#ffffff"
            combo_text = "#0f172a"
            combo_border = "#cbd5e1"

        self.setStyleSheet(f"QFrame {{ background: {panel_bg}; border: 1px solid #dbe2ea; border-radius: 8px; }}")
        self.title_label.setStyleSheet(f"color: {title_color}; font-weight: 700;")
        self.slice_info_label.setStyleSheet(f"color: {info_color}; font-size: 11px;")
        self.top_info_box.info_label.setStyleSheet(f"color: {info_color}; font-size: 11px; font-weight: 700;")
        self.bottom_info_box.info_label.setStyleSheet(f"color: {info_color}; font-size: 11px; font-weight: 700;")
        self.image_label.setStyleSheet(f"QLabel {{ color: {placeholder_color}; border: 1px dashed {border_color}; border-radius: 6px; background: {image_bg}; }}")
        self.cmap_combo.setStyleSheet(f"QComboBox {{ background: {combo_bg}; color: {combo_text}; border: 1px solid {combo_border}; border-radius: 6px; padding: 4px 8px; }}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(DraggableSequenceList.MIME_TYPE):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(DraggableSequenceList.MIME_TYPE):
            event.ignore()
            return

        seq_key = bytes(event.mimeData().data(DraggableSequenceList.MIME_TYPE)).decode("utf-8")
        if seq_key:
            self.on_drop_file(self.panel_index, seq_key)
            event.acceptProposedAction()
            return
        event.ignore()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            self.on_scroll_slice(1 if delta > 0 else -1)
            event.accept()
            return
        event.ignore()
