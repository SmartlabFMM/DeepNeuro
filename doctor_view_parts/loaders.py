"""Background loaders for the doctor view."""

import math

from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from api_client import api_client


class SendCaseDataLoader(QThread):
    """Load send-case autocomplete data without blocking the UI thread."""

    loaded = Signal(object, object, str)

    def __init__(self, doctor_email):
        super().__init__()
        self.doctor_email = doctor_email

    def run(self):
        try:
            patients_response, _ = api_client.get_doctor_patients(self.doctor_email)
            previous_cases_response, _ = api_client.get_previous_cases(self.doctor_email)
            radiologists_response, _ = api_client.get_all_radiologists()

            cases_dict = {}
            if patients_response.get('success'):
                for patient in patients_response.get('patients', []):
                    patient_id = str(patient.get('patient_id', '')).strip()
                    if patient_id:
                        cases_dict[patient_id] = {
                            'patient_name': patient.get('patient_name', ''),
                            'patient_age': patient.get('patient_age', ''),
                            'patient_gender': patient.get('patient_sex', ''),
                            'patient_email': patient.get('patient_email', ''),
                            'phone_number': patient.get('phone_number', ''),
                        }

            if previous_cases_response.get('success'):
                for case in previous_cases_response.get('cases', []):
                    patient_id = str(case.get('patient_id', '')).strip()
                    if patient_id:
                        cases_dict[patient_id] = {
                            'patient_name': case.get('patient_name', ''),
                            'patient_age': case.get('patient_age', ''),
                            'patient_gender': case.get('patient_gender', ''),
                            'patient_email': '',
                            'phone_number': '',
                        }

            radiologists = []
            if radiologists_response.get('success'):
                radiologists = radiologists_response.get('radiologists', [])

            self.loaded.emit(cases_dict, radiologists, "")
        except Exception:
            self.loaded.emit({}, [], 'Unable to load case suggestions right now.')


class PatientsDataLoader(QThread):
    """Load doctor patients without blocking the UI thread."""

    loaded = Signal(object, str)

    def __init__(self, doctor_email):
        super().__init__()
        self.doctor_email = doctor_email

    def run(self):
        try:
            response, _ = api_client.get_doctor_patients(self.doctor_email)
            if response.get('success'):
                self.loaded.emit(response.get('patients', []), "")
            else:
                self.loaded.emit([], response.get('message', 'Unable to load patients right now.'))
        except Exception:
            self.loaded.emit([], 'Unable to load patients right now.')


class DoctorRequestsDataLoader(QThread):
    """Load sent requests without blocking the UI thread."""

    loaded = Signal(object, str)

    def __init__(self, doctor_email):
        super().__init__()
        self.doctor_email = doctor_email

    def run(self):
        try:
            response, _ = api_client.get_doctor_requests(self.doctor_email)
            if response.get('success'):
                self.loaded.emit(response.get('requests', []), "")
            else:
                self.loaded.emit([], response.get('message', 'Unable to load requests right now.'))
        except Exception:
            self.loaded.emit([], 'Unable to load requests right now.')


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
