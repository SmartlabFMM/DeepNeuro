"""Radiologist-specific landing page view"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QSizePolicy, QMessageBox, QDialog,
                               QScrollArea, QPlainTextEdit, QLineEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from api_client import api_client
from datetime import datetime


class RadiologistView:
    """Handles all radiologist-specific UI components and logic"""
    
    def __init__(self, parent):
        self.parent = parent
        self.user_email = parent.user_email
        self.user_name = parent.user_name
        self.radiologist_requests_widget = None
        self.radiologist_requests_layout = None
        self.requests_search_input = None
        self.all_received_requests = []
        
    def create_buttons_container(self):
        """Create container with diagnosis buttons for radiologists"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Radiologist sees imaging analysis options
        self.btn_upload = self.parent.create_diagnosis_button("Upload Test", "#10b981")
        self.btn_imaging = self.parent.create_diagnosis_button("Image Analysis", "#8b5cf6")
        self.btn_report = self.parent.create_diagnosis_button("Generate Report", "#f59e0b")
        
        layout.addWidget(self.btn_upload)
        layout.addWidget(self.btn_imaging)
        layout.addWidget(self.btn_report)
        
        return container
    
    def create_radiologist_requests_view(self):
        """Create requests view for radiologists to display sent requests from doctors"""
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
        title = QLabel("📥 Received Requests")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #1f2937;")
        
        subtitle = QLabel("Cases sent to you by doctors")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #6b7280;")

        self.requests_search_input = QLineEdit()
        self.requests_search_input.setPlaceholderText("Search by patient ID or patient name")
        self.requests_search_input.setClearButtonEnabled(True)
        self.requests_search_input.setFixedWidth(280)
        self.requests_search_input.setStyleSheet("""
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
        self.requests_search_input.textChanged.connect(self.apply_radiologist_filter)
        
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
        refresh_btn.clicked.connect(self.refresh_radiologist_requests)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        header_layout.addWidget(self.requests_search_input)
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
        
        self.radiologist_requests_widget = QWidget()
        self.radiologist_requests_layout = QVBoxLayout(self.radiologist_requests_widget)
        self.radiologist_requests_layout.setContentsMargins(0, 0, 0, 0)
        self.radiologist_requests_layout.setSpacing(8)
        
        scroll.setWidget(self.radiologist_requests_widget)
        layout.addWidget(scroll)
        
        # Load initial requests
        self.refresh_radiologist_requests()
        
        return frame
    
    def refresh_radiologist_requests(self):
        """Fetch latest requests from API, then apply local filter."""
        response, status_code = api_client.get_radiologist_requests(self.user_email)
        self.all_received_requests = response.get('requests', []) if response.get('success') else []
        self.apply_radiologist_filter()

    def apply_radiologist_filter(self):
        """Filter cached received requests by patient ID or patient name."""
        # Clear existing items
        while self.radiologist_requests_layout.count():
            child = self.radiologist_requests_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        requests = list(self.all_received_requests)

        search_query = ""
        if self.requests_search_input is not None:
            search_query = self.requests_search_input.text().strip().lower()

        if search_query:
            requests = [
                request for request in requests
                if self._matches_request_search(request, search_query)
            ]
        
        if not requests:
            # Show empty state
            empty_text = "No matching requests found." if self.all_received_requests else "No requests received yet."
            empty_label = QLabel(empty_text)
            empty_label.setFont(QFont("Segoe UI", 9))
            empty_label.setStyleSheet("color: #9ca3af; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.radiologist_requests_layout.addWidget(empty_label)
        else:
            # Group requests by patient_id
            from collections import defaultdict
            grouped_requests = defaultdict(list)
            for request in requests:
                grouped_requests[request['patient_id']].append(request)
            
            # Display each group
            for patient_id, case_requests in grouped_requests.items():
                group_card = self.create_grouped_radiologist_request_card(patient_id, case_requests)
                self.radiologist_requests_layout.addWidget(group_card)
        
        self.radiologist_requests_layout.addStretch()

    def _matches_request_search(self, request, search_query):
        """Return True when query matches patient ID or patient name."""
        patient_id = str(request.get('patient_id', '')).lower()
        patient_name = str(request.get('patient_name', '')).lower()
        return search_query in patient_id or search_query in patient_name
    
    def create_grouped_radiologist_request_card(self, patient_id, requests):
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
        
        # Patient ID
        case_label = QLabel(f"🆔 {patient_id}")
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
            request_card = self.create_radiologist_request_card(request)
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
    
    def create_radiologist_request_card(self, request):
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
        
        # Patient ID
        case_label = QLabel(f"🆔 {request['patient_id']}")
        case_font = QFont("Segoe UI", 11, QFont.Bold)
        case_label.setFont(case_font)
        case_label.setStyleSheet("color: #111827;")
        case_label.setMinimumWidth(150)
        
        # Sender info (doctor name)
        sender_label = QLabel(f"From: {request['doctor_name']}")
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
        
        # Date received
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
        card.mousePressEvent = lambda e: self.show_radiologist_request_details(request)
        
        return card
    
    def show_radiologist_request_details(self, request):
        """Show detailed view of a request received by radiologist"""
        # Mark as read immediately when dialog opens
        if request['id']:
            api_client.mark_read_radiologist(request['id'])
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Request Details - {request['patient_id']}")
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
        
        # Title with patient ID
        title = QLabel(f"Patient ID: {request['patient_id']}")
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
            ]),
            ("Case Information", [
                (f"Patient ID", request['patient_id']),
                (f"From Doctor", request.get('doctor_name', 'N/A')),
                (f"Priority", request['priority']),
                (f"Status", request['status']),
                (f"Scan Date", request.get('scan_date', 'N/A')),
                (f"Received", request.get('created_at', 'N/A')),
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
        
        # Refresh radiologist requests after dialog closes
        self.refresh_radiologist_requests()
