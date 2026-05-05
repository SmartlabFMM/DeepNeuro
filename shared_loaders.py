"""Shared UI components and utilities for loaders and background threads."""

import math
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class DotSpinner(QWidget):
    """Small circular loading spinner inspired by Windows startup dots."""

    def __init__(self, parent=None, dot_count=8, color="#3b82f6"):
        super().__init__(parent)
        self.dot_count = dot_count
        self.active_index = 0
        self.base_color = QColor(color)
        self.timer = QTimer(self)
        self.timer.setInterval(90)
        self.timer.timeout.connect(self._advance)
        self.setFixedSize(56, 56)

    def start(self):
        if not self.timer.isActive():
            self.timer.start()

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()
        self.active_index = 0
        self.update()

    def _advance(self):
        self.active_index = (self.active_index + 1) % self.dot_count
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        center_x = self.width() / 2
        center_y = self.height() / 2
        orbit_radius = min(self.width(), self.height()) * 0.32
        dot_radius = max(2.6, min(self.width(), self.height()) * 0.07)

        for i in range(self.dot_count):
            distance = (i - self.active_index) % self.dot_count
            alpha = max(35, 255 - distance * 28)
            color = QColor(self.base_color)
            color.setAlpha(alpha)
            painter.setBrush(color)

            angle = (360 / self.dot_count) * i
            radians = math.radians(angle)
            x = center_x + orbit_radius * math.cos(radians)
            y = center_y + orbit_radius * math.sin(radians)
            painter.drawEllipse(int(x - dot_radius), int(y - dot_radius), int(dot_radius * 2), int(dot_radius * 2))
