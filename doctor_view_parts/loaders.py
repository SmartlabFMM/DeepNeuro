"""Background loaders for the doctor view."""

import logging
from PySide6.QtCore import QThread, Signal

from api_client import api_client
from shared_loaders import DotSpinner

# Configure logger for this module
logger = logging.getLogger(__name__)


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
        except Exception as e:
            logger.exception(f"Failed to load send-case data for {self.doctor_email}")
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
        except Exception as e:
            logger.exception(f"Failed to load patients for {self.doctor_email}")
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
        except Exception as e:
            logger.exception(f"Failed to load requests for {self.doctor_email}")
            self.loaded.emit([], 'Unable to load requests right now.')
