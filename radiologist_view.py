"""Radiologist-specific landing page view"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QSizePolicy, QMessageBox, QDialog,
                               QApplication, QScrollArea, QPlainTextEdit, QLineEdit,
                               QFileDialog, QComboBox, QStackedWidget)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QPainter, QColor
from api_client import api_client
from datetime import datetime
import math
import os
import time


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


class RadiologistRequestsDataLoader(QThread):
    """Load radiologist requests without blocking the UI thread."""
    loaded = Signal(object, str)

    def __init__(self, radiologist_email):
        super().__init__()
        self.radiologist_email = radiologist_email

    def run(self):
        try:
            response, _ = api_client.get_radiologist_requests(self.radiologist_email)
            if response.get('success'):
                self.loaded.emit(response.get('requests', []), "")
            else:
                self.loaded.emit([], response.get('message', 'Unable to load requests right now.'))
        except Exception:
            self.loaded.emit([], 'Unable to load requests right now.')


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
        self.radiologist_loading_spinner = None
        self.radiologist_requests_loader = None
        self.radiologist_refresh_token = 0
        self.radiologist_click_guard_until = 0.0
        self.expanded_patient_groups = set()

    def _update_completed_request_in_cache(self, request_id, diagnosis_type, test_file, segmentation_file):
        """Update local request cache after radiologist completes a case."""
        for request in self.all_received_requests:
            if request.get('id') == request_id:
                request['diagnosis_type'] = diagnosis_type
                request['uploaded_test_file'] = test_file
                request['segmentation_file'] = segmentation_file
                request['status'] = 'Completed'
                request['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

    def _split_uploaded_test_files(self, test_file_value):
        """Decode a stored test-file string into a list of file paths."""
        if not test_file_value:
            return []
        if isinstance(test_file_value, list):
            return [str(path).strip() for path in test_file_value if str(path).strip()]
        return [path.strip() for path in str(test_file_value).split('|') if path.strip()]

    def _upload_case_file(self, file_path):
        """Upload a local case file to backend storage and return the stored file ID."""
        response, _ = api_client.upload_file(file_path, self.user_email)
        if response.get('success'):
            file_record = response.get('file') or {}
            return str(file_record.get('id', '')).strip()
        return ""

    def _store_case_attachments(self, test_files, segmentation_file):
        """Upload case attachments and return backend file IDs."""
        uploaded_test_ids = []
        for file_path in test_files:
            file_id = self._upload_case_file(file_path)
            if not file_id:
                return [], ""
            uploaded_test_ids.append(file_id)

        segmentation_file_id = ""
        if segmentation_file:
            segmentation_file_id = self._upload_case_file(segmentation_file)
            if not segmentation_file_id:
                return [], ""

        return uploaded_test_ids, segmentation_file_id

    def _download_attached_file(self, request_id, file_type, file_index=0):
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
            file_index=file_index,
            user_email=self.user_email,
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

    def _open_attached_file(self, request_id, file_type, file_index=0):
        """Open an attached file by downloading it to a temp location first."""
        import tempfile
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        temp_dir = os.path.join(tempfile.gettempdir(), 'DeepNeuro', 'case-files')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{request_id}_{file_type}_{file_index}")

        response, status_code = api_client.download_attached_file(
            request_id=request_id,
            file_type=file_type,
            file_index=file_index,
            user_email=self.user_email,
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


    def _create_file_chip(self, file_path, request_id=None, file_type=None):
        """Create a simple file-logo style chip for uploaded files with optional download button."""
        chip = QFrame()
        chip.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        row = QHBoxLayout(chip)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(8)

        icon_label = QLabel("📄")
        icon_label.setFont(QFont("Segoe UI", 11))
        name_label = QLabel(os.path.basename(file_path) or file_path)
        name_label.setStyleSheet("color: #0f172a; font-weight: 600;")
        name_label.setToolTip(file_path)

        row.addWidget(icon_label)
        row.addWidget(name_label)
        row.addStretch()
        
        # Add download button if request_id and file_type provided
        if request_id and file_type:
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
                lambda checked, req_id=request_id, f_type=file_type: 
                self._download_attached_file(req_id, f_type)
            )
            row.addWidget(download_btn)
        
        return chip
        
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
        if self.radiologist_requests_layout is None:
            return

        self.radiologist_refresh_token += 1
        refresh_token = self.radiologist_refresh_token
        refresh_started = datetime.now()

        self._show_radiologist_loading()
        QApplication.processEvents()

        if self.radiologist_requests_loader is not None:
            try:
                if self.radiologist_requests_loader.isRunning():
                    return
            except RuntimeError:
                self.radiologist_requests_loader = None

        self.radiologist_requests_loader = RadiologistRequestsDataLoader(self.user_email)

        def finish_refresh(requests, error_message):
            if refresh_token != self.radiologist_refresh_token:
                return
            if self.radiologist_requests_layout is None:
                return
            self.all_received_requests = requests
            self.apply_radiologist_filter()
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
            loader = self.radiologist_requests_loader
            self.radiologist_requests_loader = None
            if loader is not None:
                try:
                    loader.deleteLater()
                except RuntimeError:
                    pass

        self.radiologist_requests_loader.loaded.connect(on_loaded)
        self.radiologist_requests_loader.finished.connect(on_loader_finished)
        self.radiologist_requests_loader.start()

    def _clear_radiologist_requests_layout(self):
        """Remove all current widgets from received requests layout."""
        self.radiologist_loading_spinner = None
        while self.radiologist_requests_layout.count():
            child = self.radiologist_requests_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _show_radiologist_loading(self):
        """Show a centered loading state while refreshing received requests."""
        self._clear_radiologist_requests_layout()

        loading_container = QWidget()
        loading_container.setAttribute(Qt.WA_TranslucentBackground, True)
        loading_container.setStyleSheet("background: transparent; border: none;")
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 16, 0, 16)
        loading_layout.setSpacing(8)
        loading_layout.setAlignment(Qt.AlignCenter)

        self.radiologist_loading_spinner = DotSpinner()
        self.radiologist_loading_spinner.start()

        loading_label = QLabel("Loading requests...")
        loading_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        loading_label.setStyleSheet("color: #6b7280; background: transparent;")
        loading_label.setAlignment(Qt.AlignCenter)

        loading_layout.addWidget(self.radiologist_loading_spinner, alignment=Qt.AlignCenter)
        loading_layout.addWidget(loading_label, alignment=Qt.AlignCenter)

        self.radiologist_requests_layout.addStretch()
        self.radiologist_requests_layout.addWidget(loading_container, alignment=Qt.AlignCenter)
        self.radiologist_requests_layout.addStretch()

    def apply_radiologist_filter(self):
        """Filter cached received requests by patient ID or patient name."""
        # Prevent accidental card click right after typing/clear-button interactions.
        self.radiologist_click_guard_until = time.monotonic() + 0.30

        # Clear existing items
        self._clear_radiologist_requests_layout()

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

    def _mark_request_read_in_cache(self, request_id):
        """Keep local cache in sync after marking a request as read."""
        for cached_request in self.all_received_requests:
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
            request_card = self.create_radiologist_request_card(request)
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
    
    def create_radiologist_request_card(self, request):
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
        
        # Sender info (doctor name)
        sender_label = QLabel(f"From: {request['doctor_name']}")
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
        
        # Date received
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
        card.mouseReleaseEvent = lambda e, req=request, req_card=card: self._on_radiologist_request_card_clicked(e, req, req_card)
        
        return card

    def _on_radiologist_request_card_clicked(self, event, request, card_widget):
        """Open request details only for an explicit left-click release."""
        if event.button() != Qt.LeftButton:
            event.ignore()
            return
        if time.monotonic() < self.radiologist_click_guard_until:
            event.ignore()
            return
        event.accept()
        self.show_radiologist_request_details(request, card_widget)
    
    def show_radiologist_request_details(self, request, card_widget=None):
        """Show detailed view of a request received by radiologist"""
        # Mark as read immediately when dialog opens
        if request['id']:
            api_client.mark_read_radiologist(request['id'])
            request['is_read'] = 1
            self._mark_request_read_in_cache(request['id'])
            if self.radiologist_requests_layout is not None:
                self.apply_radiologist_filter()
            if card_widget is not None:
                card_widget.setStyleSheet(self._request_card_style(False))
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Request Details - {request['patient_id']}")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(560)
        dialog.setStyleSheet("""
            QDialog {
                background: #f3f4f6;
            }
            QLabel {
                color: #374151;
            }
        """)
        
        root_layout = QVBoxLayout(dialog)
        root_layout.setSpacing(12)
        root_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"Patient ID: {request['patient_id']}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1f2937;")
        root_layout.addWidget(title)

        content_stack = QStackedWidget()
        root_layout.addWidget(content_stack)

        # Details page
        details_page = QWidget()
        details_layout = QVBoxLayout(details_page)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)

        details = [
            ("Patient Information", [
                ("Patient Name", request.get('patient_name', 'N/A')),
                ("Patient ID", request.get('patient_id', 'N/A')),
                ("Email", request.get('patient_email', 'N/A')),
                ("Phone", request.get('phone_number', 'N/A')),
            ]),
            ("Medical Information", [
                ("Diagnosis Type", request.get('diagnosis_type', 'N/A')),
            ]),
            ("Case Information", [
                ("Patient ID", request['patient_id']),
                ("From Doctor", request.get('doctor_name', 'N/A')),
                ("Priority", request['priority']),
                ("Status", request['status']),
                ("Scan Date", request.get('scan_date', 'N/A')),
                ("Received", request.get('created_at', 'N/A')),
            ]),
        ]

        for section_title, section_items in details:
            section_label = QLabel(section_title)
            section_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            section_label.setStyleSheet("color: #1f2937; margin-top: 10px;")
            content_layout.addWidget(section_label)

            for label_text, value_text in section_items:
                item_layout = QHBoxLayout()
                label = QLabel(label_text)
                label.setFont(QFont("Segoe UI", 9))
                label.setStyleSheet("color: #6b7280; font-weight: bold;")
                label.setMinimumWidth(120)

                value = QLabel(str(value_text))
                value.setFont(QFont("Segoe UI", 9))
                value.setStyleSheet("color: #111827;")

                item_layout.addWidget(label)
                item_layout.addWidget(value)
                item_layout.addStretch()
                content_layout.addLayout(item_layout)

        if request.get('description'):
            desc_label = QLabel("Description")
            desc_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
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

        existing_tests = self._split_uploaded_test_files(request.get('uploaded_test_file'))
        if existing_tests or request.get('segmentation_file'):
            files_label = QLabel("Attached Files")
            files_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            files_label.setStyleSheet("color: #1f2937; margin-top: 10px;")
            content_layout.addWidget(files_label)

            if existing_tests:
                tests_title = QLabel("Uploaded Test Files")
                tests_title.setStyleSheet("color: #6b7280; font-weight: 700;")
                content_layout.addWidget(tests_title)
                for file_path in existing_tests:
                    content_layout.addWidget(self._create_file_chip(file_path, request.get('id'), 'test'))

            if request.get('segmentation_file'):
                seg_title = QLabel("Segmentation File")
                seg_title.setStyleSheet("color: #6b7280; font-weight: 700; margin-top: 8px;")
                content_layout.addWidget(seg_title)
                content_layout.addWidget(self._create_file_chip(str(request.get('segmentation_file')), request.get('id'), 'segmentation'))

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        details_layout.addWidget(scroll)
        content_stack.addWidget(details_page)

        # Model usage page (same window)
        model_page = QWidget()
        model_layout = QVBoxLayout(model_page)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(10)

        header = QLabel("Model Usage")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setStyleSheet("color: #1f2937;")

        helper = QLabel("Upload test files, generate/select a segmentation file, then send all files in this same request.")
        helper.setStyleSheet("color: #6b7280;")
        helper.setWordWrap(True)

        diagnosis_type = QComboBox()
        diagnosis_type.addItems(["Glioma Tumor", "Hemorrhagic Stroke", "Ischemic Stroke"])
        diagnosis_type.setCurrentIndex(-1)
        diagnosis_type.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 7px 10px;
            }
        """)

        selected_test_files = []

        files_section = QFrame()
        files_section.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        files_section_layout = QVBoxLayout(files_section)
        files_section_layout.setContentsMargins(10, 10, 10, 10)
        files_section_layout.setSpacing(8)

        files_section_title = QLabel("Uploaded Test Files")
        files_section_title.setStyleSheet("color: #374151; font-weight: 700;")

        files_list_widget = QWidget()
        files_list_layout = QVBoxLayout(files_list_widget)
        files_list_layout.setContentsMargins(0, 0, 0, 0)
        files_list_layout.setSpacing(6)

        empty_files_label = QLabel("No test files uploaded yet")
        empty_files_label.setStyleSheet("color: #9ca3af; font-style: italic;")

        def refresh_uploaded_files_view():
            while files_list_layout.count():
                item = files_list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not selected_test_files:
                files_list_layout.addWidget(empty_files_label)
                return

            for file_path in selected_test_files:
                files_list_layout.addWidget(self._create_file_chip(file_path))

        upload_tests_btn = QPushButton("Upload Test Files")
        upload_tests_btn.setCursor(Qt.PointingHandCursor)
        upload_tests_btn.setStyleSheet("""
            QPushButton {
                background: #dbeafe;
                color: #1e40af;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #bfdbfe;
            }
        """)

        segmentation_file_input = QLineEdit()
        segmentation_file_input.setReadOnly(True)
        segmentation_file_input.setPlaceholderText("Segmentation file generated by model")

        generate_seg_btn = QPushButton("Generate / Select Segmentation File")
        generate_seg_btn.setCursor(Qt.PointingHandCursor)
        generate_seg_btn.setStyleSheet("""
            QPushButton {
                background: #ede9fe;
                color: #5b21b6;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #ddd6fe;
            }
        """)

        def pick_test_files():
            file_paths, _ = QFileDialog.getOpenFileNames(
                dialog,
                "Upload Test Files",
                "",
                "All files (*.*)"
            )
            if file_paths:
                selected_test_files.clear()
                selected_test_files.extend(file_paths)
                refresh_uploaded_files_view()

        def pick_generated_segmentation_file():
            file_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Select Generated Segmentation File",
                "",
                "All files (*.*)"
            )
            if file_path:
                segmentation_file_input.setText(file_path)

        upload_tests_btn.clicked.connect(pick_test_files)
        generate_seg_btn.clicked.connect(pick_generated_segmentation_file)

        refresh_uploaded_files_view()

        files_section_layout.addWidget(files_section_title)
        files_section_layout.addWidget(files_list_widget)

        model_layout.addWidget(header)
        model_layout.addWidget(helper)
        model_layout.addWidget(QLabel("Diagnosis Type"))
        model_layout.addWidget(diagnosis_type)
        model_layout.addWidget(upload_tests_btn)
        model_layout.addWidget(files_section)
        model_layout.addWidget(QLabel("Segmentation Output"))
        model_layout.addWidget(segmentation_file_input)
        model_layout.addWidget(generate_seg_btn)
        model_layout.addStretch()

        content_stack.addWidget(model_page)
        content_stack.setCurrentWidget(details_page)

        action_layout = QHBoxLayout()

        back_btn = QPushButton("Back to Details")
        back_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #e0e7ff;
                color: #3730a3;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background: #c7d2fe;
            }
        """)
        back_btn.setVisible(False)

        diagnose_btn = QPushButton("Diagnose & Upload Tests")
        diagnose_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        diagnose_btn.setCursor(Qt.PointingHandCursor)
        diagnose_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)

        complete_btn = QPushButton("Complete & Send to Doctor")
        complete_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        complete_btn.setCursor(Qt.PointingHandCursor)
        complete_btn.setStyleSheet("""
            QPushButton {
                background: #0ea5e9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #0284c7;
            }
        """)
        complete_btn.setVisible(False)

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

        def open_model_usage_page():
            content_stack.setCurrentWidget(model_page)
            diagnose_btn.setVisible(False)
            back_btn.setVisible(True)
            complete_btn.setVisible(True)

        def open_details_page():
            content_stack.setCurrentWidget(details_page)
            diagnose_btn.setVisible(True)
            back_btn.setVisible(False)
            complete_btn.setVisible(False)

        def complete_and_send():
            if diagnosis_type.currentIndex() < 0:
                self.parent.show_message_box("Missing Information", "Please choose diagnosis type.", "warning")
                return
            if not selected_test_files:
                self.parent.show_message_box("Missing Information", "Please upload test files first.", "warning")
                return

            segmentation_file = segmentation_file_input.text().strip()

            test_file_ids, segmentation_file_id = self._store_case_attachments(selected_test_files, segmentation_file)
            if not test_file_ids:
                self.parent.show_message_box("Upload Failed", "One or more files could not be uploaded to the backend.", "warning")
                return

            test_files_value = ' | '.join(test_file_ids)
            response, _ = api_client.complete_case_request(
                request_id=request.get('id'),
                radiologist_email=self.user_email,
                diagnosis_type=diagnosis_type.currentText(),
                uploaded_test_file=test_files_value,
                segmentation_file=segmentation_file_id,
            )

            if response.get('success'):
                self._update_completed_request_in_cache(
                    request_id=request.get('id'),
                    diagnosis_type=diagnosis_type.currentText(),
                    test_file=test_files_value,
                    segmentation_file=segmentation_file_id,
                )
                request['diagnosis_type'] = diagnosis_type.currentText()
                request['uploaded_test_file'] = test_files_value
                request['segmentation_file'] = segmentation_file_id
                request['status'] = 'Completed'
                self.apply_radiologist_filter()
                self.parent.show_message_box("Success", response.get('message', 'Case completed successfully.'), "information")
                dialog.accept()
                return

            self.parent.show_message_box("Error", response.get('message', 'Failed to complete request.'), "warning")

        diagnose_btn.clicked.connect(open_model_usage_page)
        back_btn.clicked.connect(open_details_page)
        complete_btn.clicked.connect(complete_and_send)

        action_layout.addWidget(back_btn)
        action_layout.addStretch()
        action_layout.addWidget(diagnose_btn)
        action_layout.addWidget(complete_btn)
        action_layout.addWidget(close_btn)
        root_layout.addLayout(action_layout)
        
        dialog.exec()
