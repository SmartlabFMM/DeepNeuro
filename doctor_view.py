"""Doctor-specific landing page view"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QSizePolicy, QMessageBox, QDialog, QFormLayout,
                               QLineEdit, QComboBox, QSpinBox, QScrollArea, QPlainTextEdit,
                               QDateEdit, QCompleter)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from api_client import api_client
from datetime import datetime
import random


class DoctorView:
    """Handles all doctor-specific UI components and logic"""
    
    def __init__(self, parent):
        self.parent = parent
        self.user_email = parent.user_email
        self.user_name = parent.user_name
        self.requests_list_widget = None
        self.requests_list_layout = None
        self.all_radiologists = []
        
    def create_buttons_container(self):
        """Create container with diagnosis buttons for doctors"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Doctor main actions
        self.btn_visualize = self.parent.create_diagnosis_button("Visualize Medical Records", "#6366f1")
        self.btn_add_patient = self.parent.create_diagnosis_button("Add Patient", "#10b981")
        self.btn_send_case = self.parent.create_diagnosis_button("Send to Radiologist", "#f59e0b")
        
        layout.addWidget(self.btn_visualize)
        layout.addWidget(self.btn_add_patient)
        layout.addWidget(self.btn_send_case)
        
        return container
    
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
        """Refresh the inbox with latest requests"""
        # Clear existing items
        while self.requests_list_layout.count():
            child = self.requests_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get requests from API
        response, status_code = api_client.get_doctor_requests(self.user_email)
        requests = response.get('requests', []) if response.get('success') else []
        
        if not requests:
            # Show empty state
            empty_label = QLabel("No requests sent yet. Use 'Send to Radiologist' to create one.")
            empty_label.setFont(QFont("Segoe UI", 9))
            empty_label.setStyleSheet("color: #9ca3af; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.requests_list_layout.addWidget(empty_label)
        else:
            # Group requests by case_id
            from collections import defaultdict
            grouped_requests = defaultdict(list)
            for request in requests:
                grouped_requests[request['case_id']].append(request)
            
            # Display each group
            for case_id, case_requests in grouped_requests.items():
                group_card = self.create_grouped_request_card(case_id, case_requests)
                self.requests_list_layout.addWidget(group_card)
        
        self.requests_list_layout.addStretch()
    
    def create_grouped_request_card(self, case_id, requests):
        """Create a grouped card for multiple requests with the same case ID"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)
        
        # Count unread requests in this group
        unread_count = sum(1 for r in requests if not r.get('is_read', 0))
        is_any_unread = unread_count > 0
        
        # Header card with case ID and count
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
        
        # Case ID
        case_label = QLabel(f"🗂️ {case_id}")
        case_font = QFont("Segoe UI", 11, QFont.Bold)
        case_label.setFont(case_font)
        case_label.setStyleSheet("color: #111827;")
        case_label.setMinimumWidth(150)
        
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
        
        content_widget.setVisible(False)  # Start collapsed
        container_layout.addWidget(content_widget)
        
        # Toggle expand/collapse
        def toggle_expand():
            is_visible = content_widget.isVisible()
            content_widget.setVisible(not is_visible)
            expand_btn.setText("▲ Collapse" if not is_visible else "▼ Expand")
        
        expand_btn.clicked.connect(toggle_expand)
        
        return container
    
    def create_request_card(self, request):
        """Create a simplified card for displaying a single request"""
        is_unread = not request.get('is_read', 0)
        
        card = QFrame()
        if is_unread:
            card.setStyleSheet("""
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
            """)
        else:
            card.setStyleSheet("""
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
            """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)
        
        # Case ID
        case_label = QLabel(f"🗂️ {request['case_id']}")
        case_font = QFont("Segoe UI", 11, QFont.Bold)
        case_label.setFont(case_font)
        case_label.setStyleSheet("color: #111827;")
        case_label.setMinimumWidth(150)
        
        # Sender info
        sender_label = QLabel(f"To: {request['radiologist_email']}")
        sender_font = QFont("Segoe UI", 9)
        if is_unread:
            sender_font.setBold(True)
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
        priority_text = f"🔴 Urgent" if priority == "Urgent" else f"🟢 Routine"
        priority_label = QLabel(priority_text)
        priority_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        priority_label.setStyleSheet("color: #374151;")
        priority_label.setFixedWidth(120)
        
        # Date sent
        try:
            date_str = request['created_at']
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str)
                formatted_date = date_obj.strftime("%b %d, %Y %I:%M %p")
            else:
                formatted_date = date_str
        except:
            formatted_date = request.get('created_at', 'N/A')
        
        date_label = QLabel(f"📅 {formatted_date}")
        date_label.setFont(QFont("Segoe UI", 8))
        date_label.setStyleSheet("color: #6b7280;")
        date_label.setMinimumWidth(150)
        
        layout.addWidget(case_label)
        layout.addWidget(sender_label)
        layout.addWidget(status_label)
        layout.addWidget(priority_label)
        layout.addWidget(date_label)
        layout.addStretch()
        
        # Make card clickable
        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda e: self.show_request_details(request)
        
        return card
    
    def show_request_details(self, request):
        """Show detailed view of a request in a dialog"""
        # Mark as read immediately when dialog opens
        if request['id']:
            api_client.mark_read_doctor(request['id'])
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Case Details - {request['case_id']}")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        dialog.setStyleSheet("""
            QDialog {
                background: #f3f4f6;
            }
            QLabel {
                color: #374151;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with case ID
        title = QLabel(f"Case: {request['case_id']}")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1f2937;")
        layout.addWidget(title)
        
        # Create scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        
        # Details in sections
        details = [
            ("Patient Information", [
                (f"Patient Name", request.get('patient_name', 'N/A')),
                (f"Patient ID", request.get('patient_id', 'N/A')),
            ]),
            ("Medical Information", [
                (f"Diagnosis Type", request.get('diagnosis_type', 'N/A')),
                (f"Age", request.get('patient_age', 'N/A')),
                (f"Gender", request.get('patient_gender', 'N/A')),
            ]),
            ("Case Information", [
                (f"Case ID", request['case_id']),
                (f"Sent To", request.get('radiologist_email', 'N/A')),
                (f"Priority", request['priority']),
                (f"Status", request['status']),
                (f"Scan Date", request.get('scan_date', 'N/A')),
            ]),
        ]
        
        for section_title, section_items in details:
            # Section header
            section_label = QLabel(section_title)
            section_font = QFont("Segoe UI", 11, QFont.Bold)
            section_label.setFont(section_font)
            section_label.setStyleSheet("color: #1f2937; margin-top: 10px;")
            content_layout.addWidget(section_label)
            
            # Section items
            for label_text, value_text in section_items:
                item_layout = QHBoxLayout()
                label = QLabel(label_text)
                label_font = QFont("Segoe UI", 9)
                label.setFont(label_font)
                label.setStyleSheet("color: #6b7280; font-weight: bold;")
                label.setMinimumWidth(120)
                
                value = QLabel(str(value_text))
                value_font = QFont("Segoe UI", 9)
                value.setFont(value_font)
                value.setStyleSheet("color: #111827;")
                
                item_layout.addWidget(label)
                item_layout.addWidget(value)
                item_layout.addStretch()
                
                content_layout.addLayout(item_layout)
        
        # Description section
        if request.get('description'):
            desc_label = QLabel("Description")
            desc_font = QFont("Segoe UI", 11, QFont.Bold)
            desc_label.setFont(desc_font)
            desc_label.setStyleSheet("color: #1f2937; margin-top: 10px;")
            content_layout.addWidget(desc_label)
            
            desc_text = QPlainTextEdit()
            desc_text.setPlainText(request['description'])
            desc_text.setReadOnly(True)
            desc_text.setMinimumHeight(100)
            desc_text.setStyleSheet("""
                QPlainTextEdit {
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 8px;
                    color: #111827;
                }
            """)
            content_layout.addWidget(desc_text)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #111827;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
        
        # Refresh inbox after dialog closes to update card styling
        self.refresh_inbox()

    def open_add_patient_form(self):
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

        patient_age = QSpinBox()
        patient_age.setRange(0, 120)
        patient_age.setSpecialValueText("")
        patient_age.setValue(0)

        patient_sex = QComboBox()
        patient_sex.addItems(["Female", "Male", "Other"])

        patient_id = QLineEdit()
        patient_id.setPlaceholderText("Hospital or national ID")

        patient_email = QLineEdit()
        patient_email.setPlaceholderText("Patient email")

        phone_number = QLineEdit()
        phone_number.setPlaceholderText("Phone number")

        has_conditions = QComboBox()
        has_conditions.addItems(["No", "Yes"])

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
            if patient_age.value() <= 0:
                self.parent.show_message_box("Missing Information", "Please enter a valid age.", "warning")
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
                patient_age=patient_age.value(),
                patient_sex=patient_sex.currentText(),
                patient_id=patient_id.text().strip(),
                patient_email=patient_email.text().strip(),
                phone_number=phone_number.text().strip(),
                has_conditions=(has_conditions.currentText() == "Yes"),
                conditions_notes=conditions_notes.toPlainText().strip()
            )

            if response.get('success'):
                dialog.accept()
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
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QPlainTextEdit {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 10px;
                color: #111827;
                selection-background-color: #fde68a;
            }
            QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover, QPlainTextEdit:hover {
                border: 1px solid #94a3b8;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QPlainTextEdit:focus {
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
            QComboBox::down-arrow, QDateEdit::down-arrow {
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

        # Load previous cases for autocomplete
        response, status_code = api_client.get_previous_cases(self.user_email)
        previous_cases = response.get('cases', []) if response.get('success') else []
        self.cases_dict = {case['case_id']: case for case in previous_cases}
        
        case_id = QLineEdit()
        case_id.setPlaceholderText("Type to search previous cases or enter new case ID")
        
        # Add autocomplete for case IDs
        case_id_list = [case['case_id'] for case in previous_cases]
        case_id_completer = QCompleter(case_id_list)
        case_id_completer.setCaseSensitivity(Qt.CaseInsensitive)
        case_id_completer.setFilterMode(Qt.MatchContains)
        case_id.setCompleter(case_id_completer)

        patient_name = QLineEdit()
        patient_name.setPlaceholderText("Full name")

        patient_id = QLineEdit()
        patient_id.setPlaceholderText("Hospital or national ID")

        patient_age = QSpinBox()
        patient_age.setRange(0, 120)
        patient_age.setSpecialValueText("")
        patient_age.setValue(0)

        patient_gender = QComboBox()
        patient_gender.addItems(["Female", "Male", "Other"])
        
        # Auto-fill patient fields when case ID is selected
        def on_case_id_selected(selected_case_id):
            if selected_case_id in self.cases_dict:
                case_data = self.cases_dict[selected_case_id]
                patient_name.setText(case_data['patient_name'])
                patient_id.setText(case_data['patient_id'])
                patient_age.setValue(case_data['patient_age'] if case_data['patient_age'] else 0)
                
                # Set gender
                gender_index = patient_gender.findText(case_data['patient_gender'])
                if gender_index >= 0:
                    patient_gender.setCurrentIndex(gender_index)
        
        # Trigger auto-fill when user selects from completer dropdown
        case_id_completer.activated.connect(on_case_id_selected)

        diagnosis_type = QComboBox()
        diagnosis_type.addItems([
            "Glioma Tumor",
            "Hemorrhagic Stroke",
            "Ischemic Stroke"
        ])

        scan_date = QDateEdit()
        scan_date.setCalendarPopup(True)
        scan_date.setDate(QDate.currentDate())

        priority = QComboBox()
        priority.addItems(["Routine", "Urgent"])

        # Radiologist field with autocomplete
        radiologist_email = QLineEdit()
        radiologist_email.setPlaceholderText("Search radiologist by name or email...")
        
        # Load radiologists from database
        response, status_code = api_client.get_all_radiologists()
        radiologists = response.get('radiologists', []) if response.get('success') else []
        self.all_radiologists = radiologists
        
        # Create autocomplete list
        radiologist_list = [f"{rad['name']} ({rad['email']})" for rad in radiologists]
        completer = QCompleter(radiologist_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        radiologist_email.setCompleter(completer)

        description = QPlainTextEdit()
        description.setPlaceholderText("Add clinical notes, symptoms, or special instructions")
        description.setMinimumHeight(90)

        case_id_label = QLabel("Case ID")
        case_id_label.setObjectName("FieldLabel")
        patient_name_label = QLabel("Patient Name")
        patient_name_label.setObjectName("FieldLabel")
        patient_id_label = QLabel("Patient ID")
        patient_id_label.setObjectName("FieldLabel")
        age_label = QLabel("Age")
        age_label.setObjectName("FieldLabel")
        gender_label = QLabel("Gender")
        gender_label.setObjectName("FieldLabel")
        diagnosis_label = QLabel("Diagnosis Type")
        diagnosis_label.setObjectName("FieldLabel")
        scan_date_label = QLabel("Scan Date")
        scan_date_label.setObjectName("FieldLabel")
        priority_label = QLabel("Priority")
        priority_label.setObjectName("FieldLabel")
        radiologist_label = QLabel("Radiologist")
        radiologist_label.setObjectName("FieldLabel")
        description_label = QLabel("Description")
        description_label.setObjectName("FieldLabel")

        form.addRow(case_id_label, case_id)
        form.addRow(patient_name_label, patient_name)
        form.addRow(patient_id_label, patient_id)
        form.addRow(age_label, patient_age)
        form.addRow(gender_label, patient_gender)
        form.addRow(diagnosis_label, diagnosis_type)
        form.addRow(scan_date_label, scan_date)
        form.addRow(priority_label, priority)
        form.addRow(radiologist_label, radiologist_email)
        form.addRow(description_label, description)

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
            if not radiologist_email.text().strip():
                self.parent.show_message_box("Missing Information", "Radiologist field is required.", "warning")
                return
            if not description.toPlainText().strip():
                self.parent.show_message_box("Missing Information", "Please add a description.", "warning")
                return
            
            # Extract email from radiologist field (format: "Name (email)")
            radiologist_text = radiologist_email.text().strip()
            if '(' in radiologist_text and ')' in radiologist_text:
                radiologist_email_value = radiologist_text[radiologist_text.rfind('(')+1:radiologist_text.rfind(')')].strip()
            else:
                self.parent.show_message_box("Missing Information", "Please select a valid radiologist.", "warning")
                return
            
            # Submit via API
            response, status_code = api_client.submit_diagnosis_request(
                case_id=case_id.text().strip() or f"{datetime.now().strftime('%Y')}{random.randint(1000, 9999)}",
                doctor_email=self.user_email,
                doctor_name=self.user_name,
                patient_name=patient_name.text().strip(),
                patient_id=patient_id.text().strip(),
                patient_age=patient_age.value(),
                patient_gender=patient_gender.currentText(),
                diagnosis_type=diagnosis_type.currentText(),
                scan_date=scan_date.date().toString("yyyy-MM-dd"),
                priority=priority.currentText(),
                radiologist_email=radiologist_email_value,
                description=description.toPlainText().strip()
            )
            
            dialog.accept()
            
            if response.get('success'):
                self.refresh_inbox()
                self.parent.show_message_box(
                    "Case Sent",
                    "The case has been sent to the selected radiologist.",
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

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(form_card)
        layout.addLayout(actions)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(container)

        dialog.exec()
