import os
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal, QSequentialAnimationGroup, QPauseAnimation
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGraphicsOpacityEffect,
)


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self, logo_path=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # Ensure the window is opaque (no translucent background) so edges are solid
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        # Use the same gradient as the branding sidebar so the splash matches it
        self.setStyleSheet(
            "background: qlineargradient(x1:1, y1:0, x2:1, y2:1,"
            " stop:0 #000006, stop:0.25 #050319, stop:0.5 #0f0630,"
            " stop:0.75 #160646, stop:1 #1d053f);"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")

        if logo_path and os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            if not pix.isNull():
                pix = pix.scaledToWidth(300, Qt.SmoothTransformation)
                self.logo_label.setPixmap(pix)

        layout.addWidget(self.logo_label)

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._anim_in = None
        self._anim_out = None
        self._group = None

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(50, self.start_animation)

    def start_animation(self):
        self._anim_in = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim_in.setDuration(600)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)

        self._anim_out = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim_out.setDuration(600)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)

        pause = QPauseAnimation(900, self)

        self._group = QSequentialAnimationGroup(self)
        self._group.addAnimation(self._anim_in)
        self._group.addAnimation(pause)
        self._group.addAnimation(self._anim_out)
        self._group.finished.connect(self._on_finished)
        self._group.start()


    def _on_finished(self):
        self.finished.emit()
        self.close()
