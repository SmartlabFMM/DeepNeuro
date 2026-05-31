"""Profile and Settings windows for DeepNeuro users"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QLineEdit, QCheckBox, QMessageBox, QTabWidget,
                               QWidget, QFormLayout, QSpinBox, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from api_client import api_client
from session_cache import get_cached_profile, get_cached_settings


PROFILE_SETTINGS_STYLESHEET = """
    QDialog {
        background: #f8fafc;
    }
    QLabel {
        color: #1f2937;
    }
    QFrame#ProfileCard {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 20px;
    }
    QLineEdit {
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 8px 12px;
        color: #111827;
    }
    QLineEdit:focus {
        border: 1px solid #6366f1;
        background: white;
    }
    QLineEdit:read-only {
        background: #f9fafb;
        color: #6b7280;
    }
    QPushButton {
        border-radius: 6px;
        padding: 8px 16px;
        border: none;
        font-weight: 600;
    }
    QPushButton#PrimaryBtn {
        background: #6366f1;
        color: white;
    }
    QPushButton#PrimaryBtn:hover {
        background: #4f46e5;
    }
    QPushButton#SecondaryBtn {
        background: #e5e7eb;
        color: #111827;
    }
    QPushButton#SecondaryBtn:hover {
        background: #d1d5db;
    }
    QCheckBox {
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }
    QCheckBox::indicator:checked {
        background: #6366f1;
        border: 1px solid #6366f1;
    }
    QTabWidget::pane {
        border: 1px solid #e5e7eb;
    }
    QTabBar::tab {
        background: #f3f4f6;
        color: #374151;
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
    }
    QTabBar::tab:selected {
        background: white;
        border-bottom: 2px solid #6366f1;
        color: #6366f1;
    }
"""


class ProfileWindow(QDialog):
    """User profile information window"""
    
    def __init__(self, parent, user_email, user_name, user_type):
        super().__init__(parent)
        self.user_email = user_email
        self.user_name = user_name
        self.user_type = user_type
        self.parent = parent
        self.cached_profile_data = get_cached_profile(user_email)
        
        self.setWindowTitle("User Profile")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.resize(550, 450)
        self.setStyleSheet(PROFILE_SETTINGS_STYLESHEET)
        
        self.init_ui()
        self.load_user_details()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Profile Information")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #1f2937;")
        layout.addWidget(header)
        
        # Profile card
        card = QFrame()
        card.setObjectName("ProfileCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        
        # Form layout for user info
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Name field
        name_label = QLabel("Full Name")
        name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.name_input = QLineEdit()
        self.name_input.setText(self.user_name)
        self.name_input.setReadOnly(True)
        form_layout.addRow(name_label, self.name_input)
        
        # Email field
        email_label = QLabel("Email Address")
        email_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.email_input = QLineEdit()
        self.email_input.setText(self.user_email)
        self.email_input.setReadOnly(True)
        form_layout.addRow(email_label, self.email_input)
        
        # User Type field
        type_label = QLabel("Account Type")
        type_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.type_input = QLineEdit()
        self.type_input.setText(self.user_type.capitalize())
        self.type_input.setReadOnly(True)
        form_layout.addRow(type_label, self.type_input)
        
        # Medical ID field
        medical_id_label = QLabel("Medical ID")
        medical_id_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.medical_id_input = QLineEdit()
        self.medical_id_input.setReadOnly(True)
        form_layout.addRow(medical_id_label, self.medical_id_input)
        
        # Registration date field
        reg_date_label = QLabel("Registration Date")
        reg_date_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.reg_date_input = QLineEdit()
        self.reg_date_input.setReadOnly(True)
        form_layout.addRow(reg_date_label, self.reg_date_input)
        
        # Last login field
        last_login_label = QLabel("Last Login")
        last_login_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.last_login_input = QLineEdit()
        self.last_login_input.setReadOnly(True)
        form_layout.addRow(last_login_label, self.last_login_input)
        
        card_layout.addLayout(form_layout)
        layout.addWidget(card, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        edit_btn = QPushButton("Edit Profile")
        edit_btn.setObjectName("SecondaryBtn")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self.handle_edit_profile)
        
        change_password_btn = QPushButton("Change Password")
        change_password_btn.setObjectName("SecondaryBtn")
        change_password_btn.setCursor(Qt.PointingHandCursor)
        change_password_btn.clicked.connect(self.handle_change_password)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("SecondaryBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(change_password_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_user_details(self):
        """Load user details from API"""
        user_data = self.cached_profile_data
        if user_data is None:
            response, _ = api_client.get_user_profile(self.user_email)

            if response.get('success'):
                user_data = response.get('user', {})
            else:
                self.parent.show_message_box(
                    "Error",
                    response.get('message', 'Failed to load profile details'),
                    "warning"
                )
                return

        self.medical_id_input.setText(user_data.get('medical_id', 'N/A'))
        self.reg_date_input.setText(user_data.get('created_at', 'N/A'))
        self.last_login_input.setText(user_data.get('last_login', 'Never'))
    
    def handle_edit_profile(self):
        """Handle edit profile button"""
        self.parent.show_message_box(
            "Edit Profile",
            "Profile editing will be available in a future update.",
            "information"
        )
    
    def handle_change_password(self):
        """Handle change password button"""
        self.parent.show_message_box(
            "Change Password",
            "Password change feature will be available in a future update.",
            "information"
        )


class SettingsWindow(QDialog):
    """User settings window"""
    
    def __init__(self, parent, user_email, user_name, user_type):
        super().__init__(parent)
        self.user_email = user_email
        self.user_name = user_name
        self.user_type = user_type
        self.parent = parent
        self.cached_settings_data = get_cached_settings(user_email)
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.resize(550, 450)
        self.setStyleSheet(PROFILE_SETTINGS_STYLESHEET)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Settings")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #1f2937;")
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_notification_tab(), "Notifications")
        tabs.addTab(self.create_display_tab(), "Display")
        tabs.addTab(self.create_privacy_tab(), "Privacy & Security")
        
        layout.addWidget(tabs, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.handle_save_settings)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("SecondaryBtn")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.handle_reset_settings)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("SecondaryBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_notification_tab(self):
        """Create notification settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Section header
        header = QLabel("Email Notifications")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Notification options
        self.case_request_notify = QCheckBox("Case Requests")
        self.case_request_notify.setFont(QFont("Segoe UI", 10))
        self.case_request_notify.setChecked(True)
        layout.addWidget(self.case_request_notify)
        
        self.case_completed_notify = QCheckBox("Case Completions")
        self.case_completed_notify.setFont(QFont("Segoe UI", 10))
        self.case_completed_notify.setChecked(True)
        layout.addWidget(self.case_completed_notify)
        
        self.patient_update_notify = QCheckBox("Patient Updates")
        self.patient_update_notify.setFont(QFont("Segoe UI", 10))
        self.patient_update_notify.setChecked(True)
        layout.addWidget(self.patient_update_notify)
        
        self.system_notify = QCheckBox("System Alerts")
        self.system_notify.setFont(QFont("Segoe UI", 10))
        self.system_notify.setChecked(True)
        layout.addWidget(self.system_notify)
        
        # Frequency
        freq_header = QLabel("Email Frequency")
        freq_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(freq_header)
        
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Send notifications:")
        freq_label.setFont(QFont("Segoe UI", 10))
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Immediately", "Daily Digest", "Weekly Digest"])
        self.frequency_combo.setMaximumWidth(200)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.frequency_combo)
        freq_layout.addStretch()
        layout.addLayout(freq_layout)
        
        layout.addStretch()
        return widget
    
    def create_display_tab(self):
        """Create display settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Theme
        header = QLabel("Appearance")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(header)
        
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setFont(QFont("Segoe UI", 10))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System Default"])
        self.theme_combo.setMaximumWidth(200)
        self.theme_combo.setCurrentText("Light")
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Font size
        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        font_label.setFont(QFont("Segoe UI", 10))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(20)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setMaximumWidth(100)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        # Auto-save
        self.autosave_check = QCheckBox("Auto-save drafts")
        self.autosave_check.setFont(QFont("Segoe UI", 10))
        self.autosave_check.setChecked(True)
        layout.addWidget(self.autosave_check)
        
        layout.addStretch()
        return widget
    
    def create_privacy_tab(self):
        """Create privacy and security settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Security
        header = QLabel("Security")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Session timeout
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Session Timeout (minutes):")
        timeout_label.setFont(QFont("Segoe UI", 10))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimum(5)
        self.timeout_spin.setMaximum(1440)
        self.timeout_spin.setValue(120)
        self.timeout_spin.setMaximumWidth(100)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)
        
        # Two-factor auth
        self.two_fa_check = QCheckBox("Enable Two-Factor Authentication (Coming Soon)")
        self.two_fa_check.setFont(QFont("Segoe UI", 10))
        self.two_fa_check.setEnabled(False)
        layout.addWidget(self.two_fa_check)
        
        # Privacy
        privacy_header = QLabel("Privacy")
        privacy_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(privacy_header)
        
        self.analytics_check = QCheckBox("Allow usage analytics")
        self.analytics_check.setFont(QFont("Segoe UI", 10))
        self.analytics_check.setChecked(True)
        layout.addWidget(self.analytics_check)
        
        self.data_sharing_check = QCheckBox("Allow data sharing for research")
        self.data_sharing_check.setFont(QFont("Segoe UI", 10))
        self.data_sharing_check.setChecked(False)
        layout.addWidget(self.data_sharing_check)
        
        # Data export
        export_btn = QPushButton("Export My Data")
        export_btn.setObjectName("SecondaryBtn")
        export_btn.setMaximumWidth(200)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self.handle_export_data)
        layout.addWidget(export_btn)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """Load user settings from API"""
        settings = self.cached_settings_data
        if settings is None:
            response, _ = api_client.get_user_settings(self.user_email)

            if response.get('success'):
                settings = response.get('settings', {})
            else:
                return

        # Notification settings
        self.case_request_notify.setChecked(settings.get('case_request_notify', True))
        self.case_completed_notify.setChecked(settings.get('case_completed_notify', True))
        self.patient_update_notify.setChecked(settings.get('patient_update_notify', True))
        self.system_notify.setChecked(settings.get('system_notify', True))
        self.frequency_combo.setCurrentText(settings.get('notification_frequency', 'Immediately'))

        # Display settings
        self.theme_combo.setCurrentText(settings.get('theme', 'Light'))
        self.font_size_spin.setValue(int(settings.get('font_size', 10)))
        self.autosave_check.setChecked(settings.get('autosave', True))

        # Privacy settings
        self.timeout_spin.setValue(int(settings.get('session_timeout', 120)))
        self.analytics_check.setChecked(settings.get('allow_analytics', True))
        self.data_sharing_check.setChecked(settings.get('allow_data_sharing', False))
    
    def handle_save_settings(self):
        """Save settings to API"""
        settings_data = {
            'user_email': self.user_email,
            'case_request_notify': self.case_request_notify.isChecked(),
            'case_completed_notify': self.case_completed_notify.isChecked(),
            'patient_update_notify': self.patient_update_notify.isChecked(),
            'system_notify': self.system_notify.isChecked(),
            'notification_frequency': self.frequency_combo.currentText(),
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'autosave': self.autosave_check.isChecked(),
            'session_timeout': self.timeout_spin.value(),
            'allow_analytics': self.analytics_check.isChecked(),
            'allow_data_sharing': self.data_sharing_check.isChecked(),
        }
        
        response, _ = api_client.save_user_settings(settings_data)
        
        if response.get('success'):
            self.parent.show_message_box(
                "Success",
                "Settings saved successfully!",
                "information"
            )
            self.accept()
        else:
            self.parent.show_message_box(
                "Error",
                response.get('message', 'Failed to save settings'),
                "warning"
            )
    
    def handle_reset_settings(self):
        """Reset settings to defaults"""
        reply = self.parent.show_message_box(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            "question"
        )
        
        if reply == QMessageBox.Yes:
            self.load_settings()
            self.parent.show_message_box(
                "Reset Complete",
                "Settings have been reset to defaults.",
                "information"
            )
    
    def handle_export_data(self):
        """Handle data export"""
        self.parent.show_message_box(
            "Export Data",
            "Data export feature will be available in a future update.",
            "information"
        )
