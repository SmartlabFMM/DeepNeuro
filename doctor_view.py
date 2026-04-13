"""Doctor-specific landing page view"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QSizePolicy, QMessageBox, QDialog, QFormLayout,
                               QLineEdit, QComboBox, QSpinBox, QScrollArea, QPlainTextEdit,
                               QApplication, QCompleter, QTableWidget, QTableWidgetItem, QHeaderView,
                               QStackedWidget, QFileDialog, QDateEdit, QGridLayout)
from PySide6.QtCore import Qt, QThread, Signal, QStringListModel, QTimer, QDate
from PySide6.QtGui import QFont, QIntValidator, QPainter, QColor, QDesktopServices
from PySide6.QtCore import QUrl
from api_client import api_client
from shared_request_ui import (
    REQUEST_DETAILS_DIALOG_STYLESHEET,
    DATE_FILTER_CLEAR_BUTTON_STYLESHEET,
    clean_value,
    create_date_filter_label,
    create_standard_date_filter_edit,
    make_badge,
    make_section_card,
)
from datetime import datetime
import os
import math
import time


class SendCaseDataLoader(QThread):
    """Load send-case autocomplete data without blocking the UI thread."""
    loaded = Signal(object, object, str)

    def __init__(self, doctor_email):
        super().__init__()
        self.doctor_email = doctor_email

    def run(self):
        try:
            warning_parts = []

            # Load saved patients for this doctor.
            patients_response, _ = api_client.get_doctor_patients(self.doctor_email)
            if patients_response.get('success'):
                patients = patients_response.get('patients', [])
                patients_dict = {
                    str(patient.get('patient_id', '')): {
                        'patient_name': patient.get('patient_name', ''),
                        'patient_age': patient.get('patient_age', ''),
                        'patient_gender': patient.get('patient_sex', ''),
                        'patient_email': patient.get('patient_email', ''),
                        'phone_number': patient.get('phone_number', ''),
                    }
                    for patient in patients
                    if str(patient.get('patient_id', '')).strip()
                }
            else:
                patients_dict = {}
                warning_parts.append("saved patients")

            previous_cases_response, _ = api_client.get_previous_cases(self.doctor_email)
            if previous_cases_response.get('success'):
                previous_cases = previous_cases_response.get('cases', [])
                previous_cases_dict = {
                    str(case.get('patient_id', '')): {
                        'patient_name': case.get('patient_name', ''),
                        'patient_age': case.get('patient_age', ''),
                        'patient_gender': case.get('patient_gender', ''),
                        'patient_email': '',
                        'phone_number': '',
                    }
                    for case in previous_cases
                    if str(case.get('patient_id', '')).strip()
                }
            else:
                previous_cases_dict = {}
                warning_parts.append("case history")

            # Merge both sources so doctors can fetch from patients + previous requests.
            # Previous requests override saved patient profile values for the same ID.
            cases_dict = {**patients_dict, **previous_cases_dict}

            radiologists_response, _ = api_client.get_all_radiologists()
            if radiologists_response.get('success'):
                radiologists = radiologists_response.get('radiologists', [])
            else:
                radiologists = []
                warning_parts.append("radiologists")

            warning_message = ""
            if warning_parts:
                warning_message = f"Unable to load {', '.join(warning_parts)} right now."

            self.loaded.emit(cases_dict, radiologists, warning_message)
        except Exception:
            self.loaded.emit({}, [], "Unable to load suggestions right now.")


class PatientsDataLoader(QThread):
    """Load patient table data without blocking the UI thread."""
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
    """Load doctor inbox requests without blocking the UI thread."""
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


class DoctorView:
    """Handles all doctor-specific UI components and logic"""
    
    def __init__(self, parent):
        self.parent = parent
        self.user_email = parent.user_email
        self.user_name = parent.user_name
        self.requests_list_widget = None
        self.requests_list_layout = None
        self.inbox_search_input = None
        self.inbox_date_from = None
        self.inbox_date_to = None
        self.inbox_date_filter_active = False
        self.inbox_all_requests = []
        self.inbox_loading_spinner = None
        self.inbox_loader = None
        self.inbox_refresh_token = 0
        self.inbox_click_guard_until = 0.0
        self.expanded_patient_groups = set()
        self.all_radiologists = []
        self.cases_dict = {}
        self.send_case_loader = None
        self.patients_loader = None
        
    def create_buttons_container(self):
        """Create container with diagnosis buttons for doctors"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Doctor main actions
        self.btn_visualize = self.parent.create_diagnosis_button("Visualize Medical Records", "#6366f1")
        self.btn_manage_patients = self.parent.create_diagnosis_button("Manage Patients", "#10b981")
        self.btn_send_case = self.parent.create_diagnosis_button("Send to Radiologist", "#f59e0b")
        
        layout.addWidget(self.btn_visualize)
        layout.addWidget(self.btn_manage_patients)
        layout.addWidget(self.btn_send_case)
        
        return container

    def open_manage_patients_view(self):
        """Open a dialog with the doctor's patient table and quick actions."""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Manage Patients")
        dialog.setMinimumWidth(1180)
        dialog.setMinimumHeight(680)
        dialog.resize(1180, 680)
        dialog.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QFrame#PatientsCard {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }
            QLabel {
                color: #1f2937;
            }
            QTableWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                gridline-color: #e5e7eb;
                selection-background-color: #dcfce7;
                selection-color: #14532d;
                color: #111827;
            }
            QHeaderView::section {
                background: #f3f4f6;
                color: #1f2937;
                border: none;
                border-right: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                padding: 8px;
                font-weight: 600;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 14px;
                border: none;
                font-weight: 600;
            }
        """)

        root_layout = QVBoxLayout(dialog)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(10)

        title = QLabel("Patient Management")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        subtitle = QLabel("View all your patients and add new records")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #6b7280;")

        card = QFrame()
        card.setObjectName("PatientsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        table_title = QLabel("My Patients")
        table_title.setFont(QFont("Segoe UI", 11, QFont.Bold))

        table_subtitle = QLabel("All profiles linked to your account")
        table_subtitle.setFont(QFont("Segoe UI", 9))
        table_subtitle.setStyleSheet("color: #6b7280;")

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.setSpacing(2)
        title_block.addWidget(table_title)
        title_block.addWidget(table_subtitle)

        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Search by patient ID or patient name")
        filter_input.setClearButtonEnabled(True)
        filter_input.setFixedWidth(280)
        filter_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                color: #111827;
            }
            QLineEdit:focus {
                border: 1px solid #10b981;
            }
        """)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #111827;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)

        add_patient_btn = QPushButton("Add Patient")
        add_patient_btn.setCursor(Qt.PointingHandCursor)
        add_patient_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
            }
            QPushButton:hover {
                background: #34d399;
            }
        """)

        actions.addLayout(title_block)
        actions.addStretch()
        actions.addWidget(filter_input)
        actions.addWidget(refresh_btn)
        actions.addWidget(add_patient_btn)

        patients_table = QTableWidget()
        patients_table.setColumnCount(10)
        patients_table.setHorizontalHeaderLabels([
            "Patient ID",
            "Name",
            "Age",
            "Sex",
            "Email",
            "Phone",
            "Has Conditions",
            "Conditions Notes",
            "Created",
            "Action"
        ])
        patients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        patients_table.setSelectionBehavior(QTableWidget.SelectRows)
        patients_table.setSelectionMode(QTableWidget.SingleSelection)
        patients_table.setAlternatingRowColors(True)
        patients_table.verticalHeader().setVisible(False)
        patients_table.horizontalHeader().setStretchLastSection(False)
        patients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        patients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        patients_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        patients_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        patients_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        patients_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        patients_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        patients_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        patients_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        patients_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)

        content_stack = QStackedWidget()

        loading_page = QWidget()
        loading_layout = QVBoxLayout(loading_page)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setSpacing(10)
        loading_layout.addStretch()

        spinner_container = QWidget()
        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        spinner_layout.setSpacing(8)
        spinner_layout.setAlignment(Qt.AlignCenter)

        loading_spinner = DotSpinner()
        loading_spinner.start()

        loading_label = QLabel("Loading patients...")
        loading_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        loading_label.setStyleSheet("color: #6b7280;")
        loading_label.setAlignment(Qt.AlignCenter)

        spinner_layout.addWidget(loading_spinner, alignment=Qt.AlignCenter)
        spinner_layout.addWidget(loading_label, alignment=Qt.AlignCenter)

        loading_layout.addWidget(spinner_container, alignment=Qt.AlignCenter)
        loading_layout.addStretch()

        table_page = QWidget()
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        table_layout.addWidget(patients_table)

        content_stack.addWidget(loading_page)
        content_stack.addWidget(table_page)

        all_patients = []
        dialog_is_alive = {'value': True}

        def on_delete_patient_click(patient_id):
            if not patient_id:
                return

            confirmation = self.parent.show_message_box(
                "Delete Patient",
                f"Are you sure you want to delete patient ID: {patient_id}?",
                "question"
            )
            if confirmation != QMessageBox.Yes:
                return

            response, _ = api_client.delete_patient(self.user_email, patient_id)
            if response.get('success'):
                self.parent.show_message_box("Success", response.get('message', 'Patient deleted successfully'), "information")
                load_patients_async(show_error=False)
                return

            self.parent.show_message_box(
                "Error",
                response.get('message', 'Unable to delete patient right now.'),
                "warning"
            )

        def is_dialog_alive():
            return dialog_is_alive['value']

        def set_loading_state(is_loading):
            if not is_dialog_alive():
                return
            try:
                content_stack.setCurrentIndex(0 if is_loading else 1)
                refresh_btn.setEnabled(not is_loading)
                add_patient_btn.setEnabled(not is_loading)
                filter_input.setEnabled(not is_loading)
                if is_loading:
                    loading_spinner.start()
                else:
                    loading_spinner.stop()
            except RuntimeError:
                # Dialog widgets were already destroyed.
                dialog_is_alive['value'] = False

        def populate_patients_table(patients):
            patients_table.setRowCount(0)

            for row_index, patient in enumerate(patients):
                patients_table.insertRow(row_index)

                values = [
                    str(patient.get('patient_id', '')),
                    str(patient.get('patient_name', '')),
                    str(patient.get('patient_age', '')),
                    str(patient.get('patient_sex', '')),
                    str(patient.get('patient_email', '')),
                    str(patient.get('phone_number', '')),
                    "Yes" if patient.get('has_conditions') else "No",
                    str(patient.get('conditions_notes') or '-'),
                    self._format_request_datetime(patient.get('created_at', '')),
                ]

                for col_index, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    patients_table.setItem(row_index, col_index, item)

                patient_id = str(patient.get('patient_id', '')).strip()
                delete_btn = QPushButton("Delete")
                delete_btn.setCursor(Qt.PointingHandCursor)
                delete_btn.setFixedSize(64, 24)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background: #ef4444;
                        color: white;
                        border-radius: 5px;
                        border: none;
                        padding: 2px 8px;
                        font-size: 10px;
                        font-weight: 700;
                    }
                    QPushButton:hover {
                        background: #dc2626;
                    }
                """)
                delete_btn.clicked.connect(lambda _checked=False, pid=patient_id: on_delete_patient_click(pid))
                patients_table.setCellWidget(row_index, 9, delete_btn)

        def apply_patients_filter():
            query = filter_input.text().strip().lower()
            if not query:
                populate_patients_table(all_patients)
                return

            filtered_patients = [
                patient for patient in all_patients
                if self._matches_patient_search(patient, query)
            ]
            populate_patients_table(filtered_patients)

        def load_patients_async(show_error=True):
            if self.patients_loader is not None:
                try:
                    if self.patients_loader.isRunning():
                        return
                except RuntimeError:
                    # Qt already deleted the underlying C++ object.
                    self.patients_loader = None

            set_loading_state(True)

            self.patients_loader = PatientsDataLoader(self.user_email)

            def on_loaded(patients, error_message):
                if not is_dialog_alive():
                    return
                set_loading_state(False)
                all_patients.clear()
                all_patients.extend(patients)
                apply_patients_filter()
                if error_message and show_error:
                    self.parent.show_message_box("Error", error_message, "warning")

            def on_loader_finished():
                loader = self.patients_loader
                self.patients_loader = None
                if loader is not None:
                    try:
                        loader.deleteLater()
                    except RuntimeError:
                        pass

            self.patients_loader.loaded.connect(on_loaded)
            self.patients_loader.finished.connect(on_loader_finished)
            self.patients_loader.start()

        def on_dialog_finished(_result):
            dialog_is_alive['value'] = False
            loader = self.patients_loader
            if loader is None:
                return
            try:
                loader.loaded.disconnect()
            except (RuntimeError, TypeError):
                pass

        def on_add_patient_click():
            self.open_add_patient_form(on_success=lambda: load_patients_async(show_error=False))

        refresh_btn.clicked.connect(lambda: load_patients_async(show_error=True))
        add_patient_btn.clicked.connect(on_add_patient_click)
        filter_input.textChanged.connect(lambda _: apply_patients_filter())

        card_layout.addLayout(actions)
        card_layout.addWidget(content_stack)

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #111827;
                min-width: 96px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        close_btn.clicked.connect(dialog.accept)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(card, 1)
        root_layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dialog.finished.connect(on_dialog_finished)

        set_loading_state(True)
        load_patients_async(show_error=True)
        dialog.exec()
    
    def create_inbox_view(self):
        """Create inbox view to display sent requests"""
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setMinimumHeight(300)
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📨 Sent Requests")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1f2937;")
        
        subtitle = QLabel("Track your submitted cases")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #6b7280;")

        self.inbox_search_input = QLineEdit()
        self.inbox_search_input.setPlaceholderText("Search by patient ID or patient name")
        self.inbox_search_input.setClearButtonEnabled(True)
        self.inbox_search_input.setFixedWidth(280)
        self.inbox_search_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                color: #111827;
            }
            QLineEdit:focus {
                border: 1px solid #6366f1;
            }
        """)
        self.inbox_search_input.textChanged.connect(self.apply_inbox_filter)

        self.inbox_date_from = create_standard_date_filter_edit()
        self.inbox_date_to = create_standard_date_filter_edit()

        self.inbox_date_from.dateChanged.connect(self._activate_inbox_date_filter)
        self.inbox_date_to.dateChanged.connect(self._activate_inbox_date_filter)

        clear_date_btn = QPushButton("Clear")
        clear_date_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
        clear_date_btn.setCursor(Qt.PointingHandCursor)
        clear_date_btn.setStyleSheet(DATE_FILTER_CLEAR_BUTTON_STYLESHEET)
        clear_date_btn.clicked.connect(self.clear_inbox_date_filter)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_inbox)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        header_layout.addWidget(self.inbox_search_input)

        from_label = create_date_filter_label("From")
        to_label = create_date_filter_label("To")

        header_layout.addWidget(from_label)
        header_layout.addWidget(self.inbox_date_from)
        header_layout.addWidget(to_label)
        header_layout.addWidget(self.inbox_date_to)
        header_layout.addWidget(clear_date_btn)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Scrollable area for requests list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.requests_list_widget = QWidget()
        self.requests_list_layout = QVBoxLayout(self.requests_list_widget)
        self.requests_list_layout.setContentsMargins(0, 0, 0, 0)
        self.requests_list_layout.setSpacing(8)
        
        scroll.setWidget(self.requests_list_widget)
        layout.addWidget(scroll)
        
        # Load initial requests
        self.refresh_inbox()
        
        return frame
    
    def refresh_inbox(self):
        """Fetch latest requests from API, then apply local filter."""
        if self.requests_list_layout is None:
            return

        self.inbox_refresh_token += 1
        refresh_token = self.inbox_refresh_token
        refresh_started = datetime.now()

        self._show_inbox_loading()
        QApplication.processEvents()

        if self.inbox_loader is not None:
            try:
                if self.inbox_loader.isRunning():
                    return
            except RuntimeError:
                self.inbox_loader = None

        self.inbox_loader = DoctorRequestsDataLoader(self.user_email)

        def finish_refresh(requests, error_message):
            if refresh_token != self.inbox_refresh_token:
                return
            if self.requests_list_layout is None:
                return
            self.inbox_all_requests = requests
            self.apply_inbox_filter()
            if error_message:
                self.parent.show_message_box("Error", error_message, "warning")

        def on_loaded(requests, error_message):
            elapsed_ms = int((datetime.now() - refresh_started).total_seconds() * 1000)
            delay_ms = max(0, 1000 - elapsed_ms)
            if delay_ms > 0:
                QTimer.singleShot(delay_ms, lambda: finish_refresh(requests, error_message))
            else:
                finish_refresh(requests, error_message)

        def on_loader_finished():
            loader = self.inbox_loader
            self.inbox_loader = None
            if loader is not None:
                try:
                    loader.deleteLater()
                except RuntimeError:
                    pass

        self.inbox_loader.loaded.connect(on_loaded)
        self.inbox_loader.finished.connect(on_loader_finished)
        self.inbox_loader.start()

    def _clear_inbox_layout(self):
        """Remove all current widgets from inbox list layout."""
        self.inbox_loading_spinner = None
        while self.requests_list_layout.count():
            child = self.requests_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _show_inbox_loading(self):
        """Show a centered loading state while refreshing inbox requests."""
        self._clear_inbox_layout()

        loading_container = QWidget()
        loading_container.setAttribute(Qt.WA_TranslucentBackground, True)
        loading_container.setStyleSheet("background: transparent; border: none;")
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 16, 0, 16)
        loading_layout.setSpacing(8)
        loading_layout.setAlignment(Qt.AlignCenter)

        self.inbox_loading_spinner = DotSpinner()
        self.inbox_loading_spinner.start()

        loading_label = QLabel("Loading requests...")
        loading_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        loading_label.setStyleSheet("color: #6b7280; background: transparent;")
        loading_label.setAlignment(Qt.AlignCenter)

        loading_layout.addWidget(self.inbox_loading_spinner, alignment=Qt.AlignCenter)
        loading_layout.addWidget(loading_label, alignment=Qt.AlignCenter)

        self.requests_list_layout.addStretch()
        self.requests_list_layout.addWidget(loading_container, alignment=Qt.AlignCenter)
        self.requests_list_layout.addStretch()

    def apply_inbox_filter(self):
        """Filter cached inbox requests by patient ID, patient name, or created date."""
        # Prevent accidental card click right after typing/clear-button interactions.
        self.inbox_click_guard_until = time.monotonic() + 0.30

        # Clear existing items
        self._clear_inbox_layout()

        requests = list(self.inbox_all_requests)

        search_query = ""
        if self.inbox_search_input is not None:
            search_query = self.inbox_search_input.text().strip().lower()

        if search_query:
            requests = [
                request for request in requests
                if self._matches_request_search(request, search_query)
            ]

        selected_from, selected_to = self._get_inbox_filter_range()
        if selected_from is not None or selected_to is not None:
            requests = [
                request for request in requests
                if self._matches_request_date_range(request, selected_from, selected_to)
            ]
        
        if not requests:
            # Show empty state
            if self.inbox_all_requests:
                empty_text = "No matching requests found."
            else:
                empty_text = "No requests sent yet. Use 'Send to Radiologist' to create one."
            empty_label = QLabel(empty_text)
            empty_label.setFont(QFont("Segoe UI", 9))
            empty_label.setStyleSheet("color: #9ca3af; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.requests_list_layout.addWidget(empty_label)
        else:
            # Group requests by patient_id
            from collections import defaultdict
            grouped_requests = defaultdict(list)
            for request in requests:
                grouped_requests[request['patient_id']].append(request)
            
            # Display each group
            for patient_id, case_requests in grouped_requests.items():
                group_card = self.create_grouped_request_card(patient_id, case_requests)
                self.requests_list_layout.addWidget(group_card)
        
        self.requests_list_layout.addStretch()

    def _matches_patient_search(self, patient, search_query):
        """Return True when query matches patient ID or patient name."""
        patient_id = str(patient.get('patient_id', '')).lower()
        patient_name = str(patient.get('patient_name', patient.get('name', ''))).lower()
        return search_query in patient_id or search_query in patient_name

    def _matches_request_search(self, request, search_query):
        """Return True when query matches patient ID or patient name."""
        patient_id = str(request.get('patient_id', '')).lower()
        patient_name = str(request.get('patient_name', '')).lower()
        return search_query in patient_id or search_query in patient_name

    def _activate_inbox_date_filter(self):
        """Enable the inbox date filter after the user selects a date."""
        self.inbox_date_filter_active = True
        self.apply_inbox_filter()

    def clear_inbox_date_filter(self):
        """Show inbox requests from all dates."""
        self.inbox_date_filter_active = False
        if self.inbox_date_from is not None and self.inbox_date_to is not None:
            today = QDate.currentDate()
            self.inbox_date_from.blockSignals(True)
            self.inbox_date_to.blockSignals(True)
            self.inbox_date_from.setDate(today)
            self.inbox_date_to.setDate(today)
            self.inbox_date_from.blockSignals(False)
            self.inbox_date_to.blockSignals(False)
        self.apply_inbox_filter()

    def _get_inbox_filter_range(self):
        if not self.inbox_date_filter_active or self.inbox_date_from is None or self.inbox_date_to is None:
            return None, None

        from_qdate = self.inbox_date_from.date()
        to_qdate = self.inbox_date_to.date()
        from_date = datetime(from_qdate.year(), from_qdate.month(), from_qdate.day()).date()
        to_date = datetime(to_qdate.year(), to_qdate.month(), to_qdate.day()).date()

        if from_date <= to_date:
            return from_date, to_date
        return to_date, from_date

    def _request_created_date(self, request):
        """Return the request created date when it can be parsed."""
        created_at = request.get('created_at', '')
        if not created_at:
            return None

        created_at_str = str(created_at).strip()
        try:
            normalized = created_at_str.replace('Z', '+00:00')
            return datetime.fromisoformat(normalized).date()
        except Exception:
            pass

        if len(created_at_str) >= 10 and created_at_str[4] == '-' and created_at_str[7] == '-':
            try:
                return datetime.strptime(created_at_str[:10], '%Y-%m-%d').date()
            except Exception:
                return None

        return None

    def _matches_request_date_range(self, request, selected_from, selected_to):
        """Return True when request created date falls within from/to date range."""
        request_date = self._request_created_date(request)
        if request_date is None:
            return False
        if selected_from is not None and request_date < selected_from:
            return False
        if selected_to is not None and request_date > selected_to:
            return False
        return True

    def _mark_request_read_in_cache(self, request_id):
        """Keep local cache in sync after marking a request as read."""
        for cached_request in self.inbox_all_requests:
            if cached_request.get('id') == request_id:
                cached_request['is_read'] = 1
                break

    def _request_card_style(self, is_unread):
        if is_unread:
            return """
                QFrame {
                    background: #eff6ff;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame:hover {
                    background: #dbeafe;
                    border-color: #1e40af;
                    cursor: pointer;
                }
            """
        return """
            QFrame {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
                cursor: pointer;
            }
        """

    def _format_request_datetime(self, date_value):
        """Format date as DD-MM-YYYY HH:MM."""
        if not date_value:
            return 'N/A'

        date_str = str(date_value).strip()
        try:
            normalized = date_str.replace('Z', '+00:00')
            date_obj = datetime.fromisoformat(normalized)
            return date_obj.strftime("%d-%m-%Y %H:%M")
        except Exception:
            pass

        if len(date_str) >= 16 and date_str[4] == '-' and date_str[7] == '-':
            return f"{date_str[8:10]}-{date_str[5:7]}-{date_str[0:4]} {date_str[11:16]}"

        if len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
            return f"{date_str[8:10]}-{date_str[5:7]}-{date_str[0:4]} 00:00"

        return date_str
    
    def create_grouped_request_card(self, patient_id, requests):
        """Create a grouped card for multiple requests with the same patient ID"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)
        
        # Count unread requests in this group
        unread_count = sum(1 for r in requests if not r.get('is_read', 0))
        is_any_unread = unread_count > 0
        
        # Header card with patient ID and count
        header_card = QFrame()
        if is_any_unread:
            header_card.setStyleSheet("""
                QFrame {
                    background: #eff6ff;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame:hover {
                    background: #dbeafe;
                    border-color: #1e40af;
                }
            """)
        else:
            header_card.setStyleSheet("""
                QFrame {
                    background: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame:hover {
                    background: #f3f4f6;
                    border-color: #d1d5db;
                }
            """)
        
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(16)
        
        # Patient ID + name
        sample_request = requests[0] if requests else {}
        patient_name = str(sample_request.get('patient_name', '')).strip()
        case_display = f"🆔 {patient_id} - {patient_name}" if patient_name else f"🆔 {patient_id}"
        case_label = QLabel(case_display)
        case_font = QFont("Segoe UI", 11, QFont.Bold)
        case_label.setFont(case_font)
        case_label.setStyleSheet("color: #111827;")
        case_label.setMinimumWidth(260)
        
        # Count badge
        count_text = f"{len(requests)} request{'s' if len(requests) > 1 else ''}"
        if unread_count > 0:
            count_text += f" ({unread_count} unread)"
        count_label = QLabel(count_text)
        count_font = QFont("Segoe UI", 9, QFont.Bold)
        count_label.setFont(count_font)
        count_label.setStyleSheet("""
            background: #fef3c7;
            color: #92400e;
            border-radius: 4px;
            padding: 4px 12px;
        """)

        latest_request = max(requests, key=lambda r: str(r.get('created_at', '')))
        latest_date = self._format_request_datetime(latest_request.get('created_at', 'N/A'))

        latest_date_label = QLabel(f"📅 {latest_date}")
        latest_date_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        latest_date_label.setStyleSheet("color: #4b5563;")
        latest_date_label.setMinimumWidth(180)
        
        # Expand/collapse button
        expand_btn = QPushButton("▼ Expand")
        expand_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #374151;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        expand_btn.setFixedWidth(100)

        header_layout.addWidget(latest_date_label)
        header_layout.addWidget(case_label)
        header_layout.addWidget(count_label)
        header_layout.addStretch()
        header_layout.addWidget(expand_btn)
        
        container_layout.addWidget(header_card)
        
        # Collapsible content area for individual requests
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 8, 0, 0)
        content_layout.setSpacing(8)
        
        for request in requests:
            request_card = self.create_request_card(request)
            content_layout.addWidget(request_card)
        
        patient_group_key = str(patient_id)
        is_expanded = patient_group_key in self.expanded_patient_groups
        content_widget.setVisible(is_expanded)
        expand_btn.setText("▲ Collapse" if is_expanded else "▼ Expand")
        container_layout.addWidget(content_widget)
        
        # Toggle expand/collapse
        def toggle_expand():
            is_visible = content_widget.isVisible()
            new_is_visible = not is_visible
            content_widget.setVisible(new_is_visible)
            expand_btn.setText("▲ Collapse" if new_is_visible else "▼ Expand")
            if new_is_visible:
                self.expanded_patient_groups.add(patient_group_key)
            else:
                self.expanded_patient_groups.discard(patient_group_key)
        
        expand_btn.clicked.connect(toggle_expand)
        
        return container
    
    def create_request_card(self, request):
        """Create a simplified card for displaying a single request"""
        is_unread = not request.get('is_read', 0)
        
        card = QFrame()
        card.setStyleSheet(self._request_card_style(is_unread))
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)
        
        # Patient ID + name
        patient_name = str(request.get('patient_name', '')).strip()
        case_display = f"🆔 {request['patient_id']} - {patient_name}" if patient_name else f"🆔 {request['patient_id']}"
        case_label = QLabel(case_display)
        case_font = QFont("Segoe UI", 11, QFont.Bold)
        case_label.setFont(case_font)
        case_label.setStyleSheet("color: #111827;")
        case_label.setMinimumWidth(260)
        
        # Sender info
        sender_label = QLabel(f"To: {request['radiologist_email']}")
        sender_font = QFont("Segoe UI", 9, QFont.Bold)
        sender_label.setFont(sender_font)
        sender_label.setStyleSheet("color: #6b7280;")
        sender_label.setMinimumWidth(200)
        
        # Status badge
        status = request['status']
        status_colors = {
            'Pending': '#fef3c7',
            'In Progress': '#dbeafe',
            'Completed': '#d1fae5'
        }
        status_text_colors = {
            'Pending': '#92400e',
            'In Progress': '#1e40af',
            'Completed': '#065f46'
        }
        
        status_label = QLabel(status)
        status_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        status_label.setStyleSheet(f"""
            background: {status_colors.get(status, '#f3f4f6')};
            color: {status_text_colors.get(status, '#374151')};
            border-radius: 4px;
            padding: 4px 12px;
        """)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setFixedWidth(100)
        
        # Priority badge
        priority = request['priority']
        priority_text = f" 🔴  Urgent" if priority == "Urgent" else f" 🟢  Routine"
        priority_label = QLabel(priority_text)
        priority_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        priority_label.setStyleSheet("color: #374151;")
        priority_label.setFixedWidth(120)
        
        # Date sent
        formatted_date = self._format_request_datetime(request.get('created_at', 'N/A'))
        
        date_label = QLabel(f"📅 {formatted_date}")
        date_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        date_label.setStyleSheet("color: #6b7280;")
        date_label.setMinimumWidth(150)
        
        layout.addWidget(date_label)
        layout.addWidget(case_label)
        layout.addWidget(sender_label)
        layout.addWidget(status_label)
        layout.addWidget(priority_label)
        layout.addStretch()
        
        # Make card clickable
        card.setCursor(Qt.PointingHandCursor)
        card.mouseReleaseEvent = lambda e, req=request, req_card=card: self._on_request_card_clicked(e, req, req_card)
        
        return card

    def _on_request_card_clicked(self, event, request, card_widget):
        """Open request details only for an explicit left-click release."""
        if event.button() != Qt.LeftButton:
            event.ignore()
            return
        if time.monotonic() < self.inbox_click_guard_until:
            event.ignore()
            return
        event.accept()
        QTimer.singleShot(0, lambda req=request, req_card=card_widget: self.show_request_details(req, req_card))
    
    def _download_attached_file(self, request_id, file_type, file_index):
        """Download an attached file from a request."""
        save_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            f"Save {file_type} File",
            "",
            "All files (*.*)"
        )
        
        if not save_path:
            return
        
        response, status_code = api_client.download_attached_file(
            request_id=request_id,
            file_type=file_type,
            user_email=self.user_email,
            file_index=file_index,
            save_path=save_path
        )
        
        if response.get('success'):
            self.parent.show_message_box(
                "Download Complete",
                f"File saved successfully to:\n{save_path}",
                "information"
            )
        else:
            self.parent.show_message_box(
                "Download Failed",
                response.get('message', 'Failed to download file'),
                "warning"
            )

    def _open_attached_file(self, request_id, file_type, file_index):
        """Open an attached file through a temporary local download."""
        import tempfile

        temp_dir = os.path.join(tempfile.gettempdir(), 'DeepNeuro', 'doctor-files')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{request_id}_{file_type}_{file_index}")

        response, status_code = api_client.download_attached_file(
            request_id=request_id,
            file_type=file_type,
            user_email=self.user_email,
            file_index=file_index,
            save_path=temp_path
        )

        if response.get('success'):
            QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))
        else:
            self.parent.show_message_box(
                "Open Failed",
                response.get('message', 'Failed to open file'),
                "warning"
            )
    
    def show_request_details(self, request, card_widget=None):
        """Show detailed view of a request in a dialog"""
        # Mark as read immediately when dialog opens
        if request['id']:
            api_client.mark_read_doctor(request['id'])
            request['is_read'] = 1
            self._mark_request_read_in_cache(request['id'])
            if self.requests_list_layout is not None:
                self.apply_inbox_filter()
            if card_widget is not None:
                card_widget.setStyleSheet(self._request_card_style(False))
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Request Details - {request['patient_id']}")
        dialog.setMinimumWidth(530)
        dialog.setMinimumHeight(600)
        dialog.resize(530, 600)
        dialog.setStyleSheet(REQUEST_DETAILS_DIALOG_STYLESHEET)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(10)

        title = QLabel(f"Case Information • {clean_value(request.get('patient_id'))}")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #111827;")
        header_layout.addWidget(title)

        subtitle = QLabel(f"{clean_value(request.get('patient_name'))}  •  {clean_value(request.get('diagnosis_type'))}")
        subtitle.setObjectName("MutedText")
        subtitle.setFont(QFont("Segoe UI", 10))
        header_layout.addWidget(subtitle)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        badge_row.addWidget(make_badge(f"Status: {request.get('status', 'N/A')}", "#ecfeff", "#155e75", "#a5f3fc"))
        badge_row.addWidget(make_badge(f"Priority: {request.get('priority', 'N/A')}", "#fff7ed", "#9a3412", "#fed7aa"))
        badge_row.addWidget(make_badge(f"Scan Date: {request.get('scan_date', 'N/A')}", "#eef2ff", "#3730a3", "#c7d2fe"))
        badge_row.addStretch()
        header_layout.addLayout(badge_row)

        layout.addWidget(header_card)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(2, 2, 2, 2)

        patient_rows = [
            ("Patient Name", QLabel(clean_value(request.get('patient_name')))),
            ("Patient ID", QLabel(clean_value(request.get('patient_id')))),
            ("Email", QLabel(clean_value(request.get('patient_email')))),
            ("Phone", QLabel(clean_value(request.get('phone_number')))),
        ]
        medical_rows = [
            ("Diagnosis Type", QLabel(clean_value(request.get('diagnosis_type')))),
            ("Age", QLabel(clean_value(request.get('patient_age')))),
            ("Gender", QLabel(clean_value(request.get('patient_gender')))),
            ("Sent To", QLabel(clean_value(request.get('radiologist_email')))),
        ]

        priority_label = make_badge(request.get('priority', 'N/A'), "#fff7ed", "#9a3412", "#fed7aa")
        status_label = make_badge(request.get('status', 'N/A'), "#ecfeff", "#155e75", "#a5f3fc")
        scan_date_label = QLabel(clean_value(request.get('scan_date')))
        scan_date_label.setStyleSheet("color: #111827; padding-top: 4px;")

        case_rows = [
            ("Priority", priority_label),
            ("Status", status_label),
            ("Scan Date", scan_date_label),
        ]

        content_layout.addWidget(make_section_card("Patient Information", patient_rows))
        content_layout.addWidget(make_section_card("Medical Information", medical_rows))
        content_layout.addWidget(make_section_card("Case Information", case_rows))

        if request.get('description'):
            desc_card = QFrame()
            desc_card.setObjectName("SectionCard")
            desc_layout = QVBoxLayout(desc_card)
            desc_layout.setContentsMargins(16, 14, 16, 14)
            desc_layout.setSpacing(10)

            desc_label = QLabel("Description")
            desc_label.setObjectName("SectionTitle")
            desc_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            desc_layout.addWidget(desc_label)

            desc_text = QPlainTextEdit()
            desc_text.setPlainText(request['description'])
            desc_text.setReadOnly(True)
            desc_text.setMinimumHeight(120)
            desc_text.setStyleSheet("""
                QPlainTextEdit {
                    background: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 10px;
                    padding: 10px;
                    color: #111827;
                }
            """)
            desc_layout.addWidget(desc_text)
            content_layout.addWidget(desc_card)

        if request.get('uploaded_test_file') or request.get('segmentation_file'):
            files_card = QFrame()
            files_card.setObjectName("SectionCard")
            files_layout = QVBoxLayout(files_card)
            files_layout.setContentsMargins(16, 14, 16, 14)
            files_layout.setSpacing(10)

            files_label = QLabel("Attached Files")
            files_label.setObjectName("SectionTitle")
            files_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            files_layout.addWidget(files_label)

            uploaded_tests = [item.strip() for item in str(request.get('uploaded_test_file', '')).split('|') if item.strip()]

            if uploaded_tests:
                tests_title = QLabel("Uploaded Test Files")
                tests_title.setObjectName("MutedText")
                tests_title.setStyleSheet("color: #6b7280; font-weight: 700;")
                files_layout.addWidget(tests_title)

                stored_test_names = request.get('uploaded_test_file_names') or []
                tests_grid = QGridLayout()
                tests_grid.setContentsMargins(0, 0, 0, 0)
                tests_grid.setHorizontalSpacing(8)
                tests_grid.setVerticalSpacing(8)
                tests_grid.setColumnStretch(0, 1)
                tests_grid.setColumnStretch(1, 1)

                for idx, file_path in enumerate(uploaded_tests):
                    display_name = ""
                    if idx < len(stored_test_names):
                        display_name = str(stored_test_names[idx]).strip()
                    if not display_name:
                        display_name = os.path.basename(file_path) or file_path

                    file_chip = QFrame()
                    file_chip.setStyleSheet("""
                        QFrame {
                            background: #f8fafc;
                            border: 1px solid #e2e8f0;
                            border-radius: 8px;
                        }
                    """)
                    file_row = QHBoxLayout(file_chip)
                    file_row.setContentsMargins(10, 7, 10, 7)
                    file_row.setSpacing(8)

                    file_label = QLabel(f"📄 {display_name}")
                    file_label.setStyleSheet("color: #111827;")
                    file_label.setWordWrap(True)
                    file_label.setToolTip(display_name)
                    file_row.addWidget(file_label)
                    file_row.addStretch()

                    if request.get('id'):
                        open_btn = QPushButton("Open")
                        open_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
                        open_btn.setCursor(Qt.PointingHandCursor)
                        open_btn.setStyleSheet("""
                            QPushButton {
                                background: #dcfce7;
                                color: #166534;
                                border: none;
                                border-radius: 4px;
                                padding: 4px 8px;
                            }
                            QPushButton:hover {
                                background: #bbf7d0;
                            }
                        """)
                        open_btn.setFixedWidth(70)
                        open_btn.clicked.connect(
                            lambda checked, req_id=request.get('id'), f_type='test', f_idx=idx:
                            self._open_attached_file(req_id, f_type, f_idx)
                        )

                        download_btn = QPushButton("Download")
                        download_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
                        download_btn.setCursor(Qt.PointingHandCursor)
                        download_btn.setStyleSheet("""
                            QPushButton {
                                background: #e0f2fe;
                                color: #0369a1;
                                border: none;
                                border-radius: 4px;
                                padding: 4px 8px;
                            }
                            QPushButton:hover {
                                background: #bae6fd;
                            }
                        """)
                        download_btn.setFixedWidth(80)
                        download_btn.clicked.connect(
                            lambda checked, req_id=request.get('id'), f_type='test', f_idx=idx:
                            self._download_attached_file(req_id, f_type, f_idx)
                        )
                        file_row.addWidget(open_btn)
                        file_row.addWidget(download_btn)

                    tests_grid.addWidget(file_chip, idx // 2, idx % 2)

                files_layout.addLayout(tests_grid)

            if request.get('segmentation_file'):
                seg_title = QLabel("Segmentation File")
                seg_title.setStyleSheet("color: #6b7280; font-weight: 700; margin-top: 8px;")
                files_layout.addWidget(seg_title)

                seg_row = QHBoxLayout()
                seg_value = str(request.get('segmentation_file', 'N/A'))
                seg_name = str(request.get('segmentation_file_name', '')).strip()
                if not seg_name:
                    seg_name = os.path.basename(seg_value) or seg_value
                seg_label = QLabel(f"📄 {seg_name}")
                seg_label.setStyleSheet("color: #111827;")
                seg_label.setWordWrap(True)
                seg_row.addWidget(seg_label)

                if request.get('id'):
                    open_btn = QPushButton("Open")
                    open_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    open_btn.setCursor(Qt.PointingHandCursor)
                    open_btn.setStyleSheet("""
                        QPushButton {
                            background: #dcfce7;
                            color: #166534;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background: #bbf7d0;
                        }
                    """)
                    open_btn.setFixedWidth(70)
                    open_btn.clicked.connect(
                        lambda checked, req_id=request.get('id'):
                        self._open_attached_file(req_id, 'segmentation', 0)
                    )

                    download_btn = QPushButton("Download")
                    download_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    download_btn.setCursor(Qt.PointingHandCursor)
                    download_btn.setStyleSheet("""
                        QPushButton {
                            background: #f0e7fe;
                            color: #6b21a8;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background: #e9d5ff;
                        }
                    """)
                    download_btn.setFixedWidth(80)
                    download_btn.clicked.connect(
                        lambda checked, req_id=request.get('id'):
                        self._download_attached_file(req_id, 'segmentation', 0)
                    )
                    seg_row.addWidget(open_btn)
                    seg_row.addWidget(download_btn)

                seg_row.addStretch()
                files_layout.addLayout(seg_row)

            content_layout.addWidget(files_card)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background: #111827;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #374151;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def open_add_patient_form(self, on_success=None):
        """Open the add patient dialog for doctors"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Add Patient")
        dialog.setMinimumWidth(620)
        dialog.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QLabel {
                color: #374151;
            }
            QLabel#DialogSubtitle {
                color: #6b7280;
            }
            QLabel#FieldLabel {
                color: #334155;
                font-weight: 600;
                min-width: 120px;
            }
            QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 10px;
                color: #111827;
                selection-background-color: #86efac;
            }
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QPlainTextEdit:hover {
                border: 1px solid #94a3b8;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {
                border: 1px solid #10b981;
                background: #f0fdf4;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #e2e8f0;
                background: #f8fafc;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 8px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
                border: none;
                background: #f8fafc;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #e2e8f0;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #111827;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                selection-background-color: #f0fdf4;
                selection-color: #1f2937;
                padding: 4px;
            }
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Add New Patient")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1f2937;")

        subtitle = QLabel("Enter patient information to save the profile")
        subtitle.setObjectName("DialogSubtitle")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #6b7280;")

        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }
        """)
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.setContentsMargins(14, 12, 14, 12)
        form_card_layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        patient_name = QLineEdit()
        patient_name.setPlaceholderText("Full name")

        patient_age = QLineEdit()
        patient_age.setPlaceholderText("Age")
        patient_age.setValidator(QIntValidator(1, 120, self.parent))

        patient_sex = QComboBox()
        patient_sex.addItems(["Female", "Male"])
        patient_sex.setCurrentIndex(-1)

        patient_id = QLineEdit()
        patient_id.setPlaceholderText("Hospital or national ID")

        patient_email = QLineEdit()
        patient_email.setPlaceholderText("Patient email")

        phone_number = QLineEdit()
        phone_number.setPlaceholderText("Phone number")

        has_conditions = QComboBox()
        has_conditions.addItems(["No", "Yes"])
        has_conditions.setCurrentIndex(-1)

        conditions_notes = QPlainTextEdit()
        conditions_notes.setPlaceholderText("If yes, add chronic conditions, medications, allergies, etc.")
        conditions_notes.setMinimumHeight(90)

        def on_conditions_change(text):
            conditions_notes.setEnabled(text == "Yes")
            if text != "Yes":
                conditions_notes.clear()

        has_conditions.currentTextChanged.connect(on_conditions_change)
        on_conditions_change(has_conditions.currentText())

        patient_name_label = QLabel("Patient Name")
        patient_name_label.setObjectName("FieldLabel")
        age_label = QLabel("Age")
        age_label.setObjectName("FieldLabel")
        sex_label = QLabel("Sex")
        sex_label.setObjectName("FieldLabel")
        patient_id_label = QLabel("Patient ID")
        patient_id_label.setObjectName("FieldLabel")
        email_label = QLabel("Email")
        email_label.setObjectName("FieldLabel")
        phone_label = QLabel("Phone Number")
        phone_label.setObjectName("FieldLabel")
        has_conditions_label = QLabel("Has Conditions")
        has_conditions_label.setObjectName("FieldLabel")
        conditions_label = QLabel("Condition Details")
        conditions_label.setObjectName("FieldLabel")

        form.addRow(patient_name_label, patient_name)
        form.addRow(age_label, patient_age)
        form.addRow(sex_label, patient_sex)
        form.addRow(patient_id_label, patient_id)
        form.addRow(email_label, patient_email)
        form.addRow(phone_label, phone_number)
        form.addRow(has_conditions_label, has_conditions)
        form.addRow(conditions_label, conditions_notes)

        actions = QHBoxLayout()
        actions.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #111827;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)

        add_btn = QPushButton("Add Patient")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #34d399;
            }
        """)

        def handle_submit():
            if not patient_name.text().strip():
                self.parent.show_message_box("Missing Information", "Patient name is required.", "warning")
                return
            if not patient_age.text().strip().isdigit():
                self.parent.show_message_box("Missing Information", "Age must be a number.", "warning")
                return
            age_value = int(patient_age.text().strip())
            if age_value < 1 or age_value > 120:
                self.parent.show_message_box("Missing Information", "Age must be between 1 and 120.", "warning")
                return
            if not patient_id.text().strip():
                self.parent.show_message_box("Missing Information", "Patient ID is required.", "warning")
                return
            if not patient_email.text().strip():
                self.parent.show_message_box("Missing Information", "Patient email is required.", "warning")
                return
            if not phone_number.text().strip():
                self.parent.show_message_box("Missing Information", "Phone number is required.", "warning")
                return

            if has_conditions.currentText() == "Yes" and not conditions_notes.toPlainText().strip():
                self.parent.show_message_box("Missing Information", "Please add condition details.", "warning")
                return

            response, status_code = api_client.add_patient(
                doctor_email=self.user_email,
                patient_name=patient_name.text().strip(),
                patient_age=age_value,
                patient_sex=patient_sex.currentText(),
                patient_id=patient_id.text().strip(),
                patient_email=patient_email.text().strip(),
                phone_number=phone_number.text().strip(),
                has_conditions=(has_conditions.currentText() == "Yes"),
                conditions_notes=conditions_notes.toPlainText().strip()
            )

            if response.get('success'):
                dialog.accept()
                if callable(on_success):
                    on_success()
                self.parent.show_message_box(
                    "Patient Added",
                    "Patient information has been saved successfully.",
                    "information"
                )
            else:
                self.parent.show_message_box(
                    "Error",
                    response.get('message', 'Failed to add patient. Please try again.'),
                    "critical"
                )

        add_btn.clicked.connect(handle_submit)

        actions.addWidget(cancel_btn)
        actions.addWidget(add_btn)

        form_card_layout.addLayout(form)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(form_card)
        layout.addLayout(actions)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(container)

        dialog.exec()

    def open_send_case_form(self):
        """Open the send case dialog for doctors"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Send Case to Radiologist")
        dialog.setMinimumWidth(620)
        dialog.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QLabel {
                color: #374151;
            }
            QLabel#DialogSubtitle {
                color: #6b7280;
            }
            QLabel#FieldLabel {
                color: #334155;
                font-weight: 600;
                min-width: 120px;
            }
            QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 10px;
                color: #111827;
                selection-background-color: #fde68a;
            }
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QPlainTextEdit:hover {
                border: 1px solid #94a3b8;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {
                border: 1px solid #f59e0b;
                background: #fffbeb;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #e2e8f0;
                background: #f8fafc;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 8px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
                border: none;
                background: #f8fafc;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #e2e8f0;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #111827;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                selection-background-color: #fffbeb;
                selection-color: #1f2937;
                padding: 4px;
            }
            QListView {
                background: white;
                color: #111827;
                selection-background-color: #fffbeb;
                selection-color: #1f2937;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Send Patient Case")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1f2937;")

        subtitle = QLabel("Fill in the case details and select the radiologist")
        subtitle.setObjectName("DialogSubtitle")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #6b7280;")

        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }
        """)
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.setContentsMargins(14, 12, 14, 12)
        form_card_layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        content_stack = QStackedWidget()

        loading_page = QWidget()
        loading_layout = QVBoxLayout(loading_page)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setSpacing(10)
        loading_layout.addStretch()

        spinner_container = QWidget()
        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        spinner_layout.setSpacing(8)
        spinner_layout.setAlignment(Qt.AlignCenter)

        loading_spinner = DotSpinner()
        loading_spinner.start()

        loading_label = QLabel("Loading case suggestions...")
        loading_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        loading_label.setStyleSheet("color: #6b7280;")
        loading_label.setAlignment(Qt.AlignCenter)

        spinner_layout.addWidget(loading_spinner, alignment=Qt.AlignCenter)
        spinner_layout.addWidget(loading_label, alignment=Qt.AlignCenter)

        loading_layout.addWidget(spinner_container, alignment=Qt.AlignCenter)
        loading_layout.addStretch()

        form_page = QWidget()
        form_page_layout = QVBoxLayout(form_page)
        form_page_layout.setContentsMargins(0, 0, 0, 0)
        form_page_layout.setSpacing(12)

        self.cases_dict = {}

        patient_id = QLineEdit()
        patient_id.setPlaceholderText("ID")

        # Add autocomplete for patient IDs (loaded in background)
        patient_id_model = QStringListModel([])
        patient_id_completer = QCompleter(patient_id_model)
        patient_id_completer.setCaseSensitivity(Qt.CaseInsensitive)
        patient_id_completer.setFilterMode(Qt.MatchContains)
        patient_id.setCompleter(patient_id_completer)

        patient_name = QLineEdit()
        patient_name.setPlaceholderText("Full name")

        patient_age = QLineEdit()
        patient_age.setPlaceholderText("Age")
        patient_age.setValidator(QIntValidator(1, 120, self.parent))
        patient_age.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        patient_gender = QComboBox()
        patient_gender.setEditable(True)
        patient_gender.setInsertPolicy(QComboBox.NoInsert)
        patient_gender.lineEdit().setReadOnly(True)
        patient_gender.lineEdit().setPlaceholderText("Gender")
        patient_gender.addItems(["Female", "Male"])
        patient_gender.setCurrentIndex(-1)
        patient_gender.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        patient_email = QLineEdit()
        patient_email.setPlaceholderText("Email")

        phone_number = QLineEdit()
        phone_number.setPlaceholderText("Phone number")
        phone_number.setMinimumWidth(180)
        # Auto-fill patient fields when case ID is selected
        def on_patient_id_selected(selected_patient_id):
            if selected_patient_id in self.cases_dict:
                case_data = self.cases_dict[selected_patient_id]
                patient_name.setText(case_data['patient_name'])
                patient_age.setText(str(case_data['patient_age']) if case_data['patient_age'] else "")
                patient_email.setText(str(case_data.get('patient_email', '') or ''))
                phone_number.setText(str(case_data.get('phone_number', '') or ''))
                
                # Set gender
                gender_index = patient_gender.findText(case_data['patient_gender'])
                if gender_index >= 0:
                    patient_gender.setCurrentIndex(gender_index)
        
        # Trigger auto-fill when user selects from completer dropdown
        patient_id_completer.activated.connect(on_patient_id_selected)

        diagnosis_type = QComboBox()
        diagnosis_type.setEditable(True)
        diagnosis_type.setInsertPolicy(QComboBox.NoInsert)
        diagnosis_type.lineEdit().setReadOnly(True)
        diagnosis_type.lineEdit().setPlaceholderText("Diagnosis Type")
        diagnosis_type.addItems([
            "Glioma Tumor",
            "Hemorrhagic Stroke",
            "Ischemic Stroke"
        ])
        diagnosis_type.setCurrentIndex(-1)

        priority = QComboBox()
        priority.setEditable(True)
        priority.setInsertPolicy(QComboBox.NoInsert)
        priority.lineEdit().setReadOnly(True)
        priority.lineEdit().setPlaceholderText("Priority")
        priority.addItems(["Routine", "Urgent"])
        priority.setCurrentIndex(-1)

        # Radiologist field with searchable combo box
        radiologist_combo = QComboBox()
        radiologist_combo.setEditable(True)
        radiologist_combo.setInsertPolicy(QComboBox.NoInsert)
        radiologist_combo.lineEdit().setPlaceholderText("Search radiologist by name or email...")
        radiologist_combo.setCurrentIndex(-1)

        # Create autocomplete list (loaded in background)
        radiologist_model = QStringListModel([])
        completer = QCompleter(radiologist_model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        radiologist_combo.setCompleter(completer)

        description = QPlainTextEdit()
        description.setPlaceholderText("Add clinical notes, symptoms, or special instructions")
        description.setMinimumHeight(90)

        patient_section_label = QLabel("Patient Informations")
        patient_section_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        patient_section_label.setStyleSheet("color: #1f2937; margin-top: 6px; margin-bottom: 1px;")
        patient_section_label.setMaximumWidth(180)
        patient_section_label.setMinimumHeight(40)

        case_section_label = QLabel("Case Request")
        case_section_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        case_section_label.setStyleSheet("color: #1f2937; margin-top: 6px; margin-bottom: 1px;")
        case_section_label.setMaximumWidth(120)
        case_section_label.setMinimumHeight(40)


        patient_info_row = QWidget()
        patient_info_layout = QHBoxLayout(patient_info_row)
        patient_info_layout.setContentsMargins(0, 0, 0, 0)
        patient_info_layout.setSpacing(8)
        patient_id.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        patient_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        patient_info_layout.addWidget(patient_id, 1)
        patient_info_layout.addWidget(patient_name, 1)

        personal_row = QWidget()
        personal_layout = QHBoxLayout(personal_row)
        personal_layout.setContentsMargins(0, 0, 0, 0)
        personal_layout.setSpacing(8)
        personal_layout.addWidget(patient_age, 1)
        personal_layout.addWidget(patient_gender, 1)

        contact_row = QWidget()
        contact_layout = QHBoxLayout(contact_row)
        contact_layout.setContentsMargins(0, 0, 0, 0)
        contact_layout.setSpacing(8)
        contact_layout.addWidget(patient_email)
        contact_layout.addWidget(phone_number)

        case_main_row = QWidget()
        case_main_layout = QHBoxLayout(case_main_row)
        case_main_layout.setContentsMargins(0, 0, 0, 0)
        case_main_layout.setSpacing(8)
        case_main_layout.addWidget(diagnosis_type)
        case_main_layout.addWidget(priority)

        form.addRow(patient_section_label)
        form.addRow(patient_info_row)
        form.addRow(personal_row)
        form.addRow(contact_row)
        form.addRow(case_section_label)
        form.addRow(case_main_row)
        form.addRow(radiologist_combo)
        form.addRow(description)

        actions = QHBoxLayout()
        actions.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #111827;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)

        send_btn = QPushButton("Send Case")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #fbbf24;
            }
        """)

        def handle_submit():
            if not patient_name.text().strip():
                self.parent.show_message_box("Missing Information", "Patient name is required.", "warning")
                return
            if not patient_id.text().strip():
                self.parent.show_message_box("Missing Information", "Patient ID is required.", "warning")
                return
            if not patient_age.text().strip().isdigit():
                self.parent.show_message_box("Missing Information", "Age must be a number.", "warning")
                return
            age_value = int(patient_age.text().strip())
            if age_value < 1 or age_value > 120:
                self.parent.show_message_box("Missing Information", "Age must be between 1 and 120.", "warning")
                return

            missing_optional_fields = []
            if not patient_email.text().strip():
                missing_optional_fields.append("Email")
            if not phone_number.text().strip():
                missing_optional_fields.append("Phone Number")

            if missing_optional_fields:
                missing_text = ", ".join(missing_optional_fields)
                continue_reply = self.parent.show_message_box(
                    "Optional Fields Empty",
                    f"Some optional fields are empty: {missing_text}.\n\nDo you want to continue sending?",
                    "question"
                )
                if continue_reply != QMessageBox.Yes:
                    return

            if not radiologist_combo.currentText().strip():
                self.parent.show_message_box("Missing Information", "Radiologist field is required.", "warning")
                return
            if not description.toPlainText().strip():
                self.parent.show_message_box("Missing Information", "Please add a description.", "warning")
                return
            
            # Extract email from radiologist field (format: "Name (email)")
            radiologist_text = radiologist_combo.currentText().strip()
            if '(' in radiologist_text and ')' in radiologist_text:
                radiologist_email_value = radiologist_text[radiologist_text.rfind('(')+1:radiologist_text.rfind(')')].strip()
            elif '@' in radiologist_text and '.' in radiologist_text:
                radiologist_email_value = radiologist_text
            else:
                self.parent.show_message_box("Missing Information", "Please select a valid radiologist.", "warning")
                return
            
            # Submit via API
            response, status_code = api_client.submit_diagnosis_request(
                doctor_email=self.user_email,
                doctor_name=self.user_name,
                patient_name=patient_name.text().strip(),
                patient_id=patient_id.text().strip(),
                patient_age=age_value,
                patient_gender=patient_gender.currentText(),
                patient_email=patient_email.text().strip(),
                phone_number=phone_number.text().strip(),
                diagnosis_type=diagnosis_type.currentText(),
                scan_date=datetime.now().strftime("%d-%m-%Y"),
                priority=priority.currentText(),
                radiologist_email=radiologist_email_value,
                description=description.toPlainText().strip()
            )
            
            dialog.accept()
            
            if response.get('success'):
                self.refresh_inbox()
                self.parent.show_message_box(
                    "Case Sent",
                    response.get('message', 'The case has been sent to the selected radiologist.'),
                    "information"
                )
            else:
                self.parent.show_message_box(
                    "Error",
                    response.get('message', 'Failed to save the case. Please try again.'),
                    "critical"
                )

        send_btn.clicked.connect(handle_submit)

        actions.addWidget(cancel_btn)
        actions.addWidget(send_btn)

        form_card_layout.addLayout(form)

        form_page_layout.addWidget(form_card)
        form_page_layout.addLayout(actions)

        content_stack.addWidget(loading_page)
        content_stack.addWidget(form_page)

        dialog_is_alive = {'value': True}

        def is_dialog_alive():
            return dialog_is_alive['value']

        def set_send_case_loading_state(is_loading):
            if not is_dialog_alive():
                return
            try:
                content_stack.setCurrentIndex(0 if is_loading else 1)
                send_btn.setEnabled(not is_loading)
                if is_loading:
                    loading_spinner.start()
                else:
                    loading_spinner.stop()
            except RuntimeError:
                dialog_is_alive['value'] = False

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(content_stack)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(container)

        # Load autocomplete data after dialog is created so the form appears instantly.
        def on_loader_finished(cases_dict, radiologists, warning_message):
            if not is_dialog_alive():
                return

            self.cases_dict = cases_dict
            self.all_radiologists = radiologists

            patient_id_model.setStringList(list(cases_dict.keys()))
            radiologist_options = [f"{rad['name']} ({rad['email']})" for rad in radiologists]
            radiologist_model.setStringList(radiologist_options)

            # Populate combo dropdown so users can scroll/select entries.
            current_text = radiologist_combo.currentText()
            radiologist_combo.clear()
            radiologist_combo.addItems(radiologist_options)
            if current_text:
                radiologist_combo.setEditText(current_text)
            else:
                radiologist_combo.setCurrentIndex(-1)

            set_send_case_loading_state(False)

            if warning_message:
                self.parent.show_message_box("Warning", warning_message, "warning")

        def on_loader_thread_finished():
            loader = getattr(dialog, '_send_case_loader', None)
            if loader is None:
                return
            try:
                loader.deleteLater()
            except RuntimeError:
                pass
            if self.send_case_loader is loader:
                self.send_case_loader = None
            dialog._send_case_loader = None

        def on_dialog_finished(_result):
            dialog_is_alive['value'] = False
            loader = getattr(dialog, '_send_case_loader', None)
            if loader is None:
                return
            try:
                loader.loaded.disconnect(on_loader_finished)
            except (RuntimeError, TypeError):
                pass

        set_send_case_loading_state(True)

        dialog._send_case_loader = SendCaseDataLoader(self.user_email)
        self.send_case_loader = dialog._send_case_loader
        dialog._send_case_loader.loaded.connect(on_loader_finished)
        dialog._send_case_loader.finished.connect(on_loader_thread_finished)
        dialog.finished.connect(on_dialog_finished)
        dialog._send_case_loader.start()

        dialog.exec()
