"""Profile and Settings windows for DeepNeuro users

Rewritten to provide an in-window stacked flow for Edit Profile and Change Password
using the same horizontal slide animation as the auth screens.
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QLineEdit, QCheckBox, QMessageBox, QTabWidget,
                               QStackedWidget, QWidget, QFormLayout, QSpinBox, QComboBox)
from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QFont
from api_client import api_client
from session_cache import get_cached_profile, get_cached_settings, prime_user_session


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
"""


class ProfileWindow(QDialog):
    """User profile information window with in-window edit/password flows."""

    def __init__(self, parent, user_email, user_name, user_type):
        super().__init__(parent)
        self.user_email = user_email
        self.user_name = user_name
        self.user_type = user_type
        self.parent = parent
        self.cached_profile_data = get_cached_profile(user_email)

        self.setWindowTitle("User Profile")
        self.setMinimumWidth(550)
        self.setMinimumHeight(470)
        self.resize(550, 470)
        self.setStyleSheet(PROFILE_SETTINGS_STYLESHEET)

        self.init_ui()
        self.load_profile()

    def get_header_button_style(self):
        # Use a light-background-friendly button style for dialogs
        return (
            "QPushButton {"
            "background: #e5e7eb; color: #111827;"
            "border: 1px solid #d1d5db; border-radius:6px; padding:6px 12px;}"
            "QPushButton:hover { background: #d1d5db;}"
        )

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Profile")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #1f2937;")
        layout.addWidget(header)

        # Stacked pages: view, edit, password
        self.stacked = QStackedWidget()
        self.profile_page = self.build_profile_page()
        self.edit_page = self.build_edit_page()
        self.password_page = self.build_password_page()

        self.stacked.addWidget(self.profile_page)
        self.stacked.addWidget(self.edit_page)
        self.stacked.addWidget(self.password_page)

        layout.addWidget(self.stacked, 1)

    def build_profile_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("ProfileCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True)
        form_layout.addRow(QLabel("Full Name"), self.name_input)

        self.email_input = QLineEdit()
        self.email_input.setReadOnly(True)
        form_layout.addRow(QLabel("Email Address"), self.email_input)

        self.type_input = QLineEdit()
        self.type_input.setReadOnly(True)
        form_layout.addRow(QLabel("Account Type"), self.type_input)

        self.medical_id_input = QLineEdit()
        self.medical_id_input.setReadOnly(True)
        form_layout.addRow(QLabel("Medical ID"), self.medical_id_input)

        self.reg_date_input = QLineEdit()
        self.reg_date_input.setReadOnly(True)
        form_layout.addRow(QLabel("Registration Date"), self.reg_date_input)

        self.last_login_input = QLineEdit()
        self.last_login_input.setReadOnly(True)
        form_layout.addRow(QLabel("Last Login"), self.last_login_input)

        card_layout.addLayout(form_layout)
        page_layout.addWidget(card, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        edit_btn = QPushButton("Edit Profile")
        edit_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        edit_btn.setStyleSheet(self.get_header_button_style())
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self.handle_edit_profile)

        change_password_btn = QPushButton("Change Password")
        change_password_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        change_password_btn.setStyleSheet(self.get_header_button_style())
        change_password_btn.setCursor(Qt.PointingHandCursor)
        change_password_btn.clicked.connect(self.handle_change_password)

        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        close_btn.setStyleSheet(self.get_header_button_style())
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(change_password_btn)
        button_layout.addWidget(close_btn)
        page_layout.addLayout(button_layout)

        return page

    def build_edit_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("Edit Profile")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        description = QLabel("Update your display name. Your email address cannot be changed here.")
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        form.setSpacing(10)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.edit_name_input = QLineEdit()
        self.edit_email_input = QLineEdit()
        self.edit_email_input.setReadOnly(True)

        form.addRow(QLabel("Full Name"), self.edit_name_input)
        form.addRow(QLabel("Email Address"), self.edit_email_input)
        layout.addLayout(form)

        button_row = QHBoxLayout()
        form.setSpacing(6)

        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        back_btn.setStyleSheet(self.get_header_button_style())
        back_btn.clicked.connect(lambda: self.switch_page(0))

        save_btn = QPushButton("Save Changes")
        save_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        save_btn.setStyleSheet(self.get_header_button_style())
        save_btn.clicked.connect(self.save_profile_changes)

        button_row.addWidget(back_btn)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)
        return page

    def build_password_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Change Password")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        self.password_info = QLabel("")
        self.password_info.setWordWrap(True)
        layout.addWidget(self.password_info)

        form = QFormLayout()
        form.setSpacing(6)

        # Verification code (step 1)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter verification code")

        # New password fields (step 2) hidden until verification
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setVisible(False)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setVisible(False)

        form.addRow(QLabel("Verification Code"), self.code_input)
        layout.addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch()

        resend_btn = QPushButton("Resend Code")
        resend_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        resend_btn.setStyleSheet(self.get_header_button_style())
        resend_btn.clicked.connect(self.resend_password_code)

        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        back_btn.setStyleSheet(self.get_header_button_style())
        back_btn.clicked.connect(lambda: self.switch_page(0))

        verify_btn = QPushButton("Verify Code")
        verify_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        verify_btn.setStyleSheet(self.get_header_button_style())
        verify_btn.clicked.connect(self.verify_password_code)

        save_btn = QPushButton("Update Password")
        save_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        save_btn.setStyleSheet(self.get_header_button_style())
        save_btn.clicked.connect(self.update_password_with_code)
        save_btn.setVisible(False)

        # store refs for toggling
        self._verify_btn = verify_btn
        self._save_btn = save_btn

        button_row.addWidget(resend_btn)
        button_row.addWidget(back_btn)
        button_row.addWidget(verify_btn)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)
        return page

    def load_profile(self):
        # Populate fields from cached data if available
        data = self.cached_profile_data or {}
        self.name_input.setText(data.get('name', self.user_name or ''))
        self.email_input.setText(data.get('email', self.user_email or ''))
        self.type_input.setText(data.get('type', (self.user_type or '').capitalize()))
        self.medical_id_input.setText(data.get('medical_id', ''))
        self.reg_date_input.setText(data.get('registered_at', ''))
        self.last_login_input.setText(data.get('last_login', ''))

        # Edit page defaults
        self.edit_name_input.setText(self.name_input.text())
        self.edit_email_input.setText(self.email_input.text())

    def switch_page(self, target_index: int):
        current_index = self.stacked.currentIndex()
        if target_index == current_index:
            return

        current_widget = self.stacked.currentWidget()
        next_widget = self.stacked.widget(target_index)
        if current_widget is None or next_widget is None:
            self.stacked.setCurrentIndex(target_index)
            return

        width = self.stacked.width() or 1

        # Prepare widgets for animation
        current_widget.move(0, 0)
        next_widget.setGeometry(0, 0, self.stacked.width(), self.stacked.height())

        # Decide direction: forward -> slide right, backward -> slide left
        forward = target_index > current_index
        start_x_next = width if forward else -width
        end_x_current = -width if forward else width

        next_widget.move(start_x_next, 0)
        next_widget.show()
        next_widget.raise_()

        outgoing_anim = QPropertyAnimation(current_widget, b"pos", self)
        outgoing_anim.setDuration(330)
        outgoing_anim.setStartValue(QPoint(0, 0))
        outgoing_anim.setEndValue(QPoint(end_x_current, 0))
        outgoing_anim.setEasingCurve(QEasingCurve.OutCubic)

        incoming_anim = QPropertyAnimation(next_widget, b"pos", self)
        incoming_anim.setDuration(330)
        incoming_anim.setStartValue(QPoint(start_x_next, 0))
        incoming_anim.setEndValue(QPoint(0, 0))
        incoming_anim.setEasingCurve(QEasingCurve.OutCubic)

        transition_group = QParallelAnimationGroup(self)
        transition_group.addAnimation(outgoing_anim)
        transition_group.addAnimation(incoming_anim)

        def finish_transition():
            self.stacked.setCurrentIndex(target_index)
            current_widget.move(0, 0)
            next_widget.move(0, 0)

        transition_group.finished.connect(finish_transition)
        self._page_transition_group = transition_group
        transition_group.start()

    def handle_edit_profile(self):
        self.edit_name_input.setText(self.name_input.text())
        self.switch_page(1)

    def handle_change_password(self):
        # Request verification code then switch to password page
        request_response, _ = api_client.request_password_reset(self.user_email)
        if not request_response.get('success'):
            self.parent.show_message_box(
                "Verification Failed",
                request_response.get('message', 'Failed to send verification code.'),
                "warning",
            )
            return

        self.password_info.setText(
            f"A verification code was sent to {self.user_email}. Enter it below with your new password."
        )
        self.code_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        # Ensure step 2 remains hidden until code verification succeeds
        self.new_password_input.setVisible(False)
        self.confirm_password_input.setVisible(False)
        if hasattr(self, '_verify_btn'):
            self._verify_btn.setVisible(True)
        if hasattr(self, '_save_btn'):
            self._save_btn.setVisible(False)
        self.switch_page(2)

    def verify_password_code(self):
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Missing Code", "Please enter the verification code sent to your email.")
            return

        verify_response, _ = api_client.verify_reset_code(self.user_email, code)
        if not verify_response.get('success'):
            QMessageBox.warning(self, "Verification Failed", verify_response.get('message', 'Invalid verification code'))
            return

        # Code valid: swipe to the new-password view in the same window
        self._show_new_password_page(code)

    def _show_new_password_page(self, verification_code):
        self.pending_password_code = verification_code

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Set New Password")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        info = QLabel("Enter and confirm your new password.")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(8)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("Enter new password")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")

        form.addRow(QLabel("New Password"), self.new_password_input)
        form.addRow(QLabel("Confirm Password"), self.confirm_password_input)
        layout.addLayout(form)

        row = QHBoxLayout()
        row.addStretch()

        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        back_btn.setStyleSheet(self.get_header_button_style())
        back_btn.clicked.connect(lambda: self.switch_page(2))

        save_btn = QPushButton("Update Password")
        save_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        save_btn.setStyleSheet(self.get_header_button_style())
        save_btn.clicked.connect(self.update_password_with_code)

        row.addWidget(back_btn)
        row.addWidget(save_btn)
        layout.addLayout(row)

        if self.stacked.count() == 3:
            self.stacked.insertWidget(3, page)
        elif self.stacked.count() > 3:
            old = self.stacked.widget(3)
            self.stacked.removeWidget(old)
            old.deleteLater()
            self.stacked.insertWidget(3, page)
        else:
            self.stacked.addWidget(page)

        self.password_new_page = page
        self.switch_page(3)
        self.new_password_input.setFocus()

    def save_profile_changes(self):
        new_name = self.edit_name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Missing Information", "Full name is required.")
            return

        response, _ = api_client.update_user_profile(self.user_email, new_name)
        if not response.get('success'):
            QMessageBox.warning(self, "Update Failed", response.get('message', 'Failed to update profile'))
            return

        updated_user = response.get('user', {})
        self.user_name = updated_user.get('name', new_name)
        self.name_input.setText(self.user_name)
        self.edit_name_input.setText(self.user_name)
        self.cached_profile_data = updated_user
        prime_user_session(self.user_email, profile=updated_user)

        if hasattr(self.parent, 'refresh_user_identity'):
            self.parent.refresh_user_identity(self.user_name)

        self.parent.show_message_box(
            "Profile Updated",
            "Your profile changes were saved successfully.",
            "information",
        )
        self.switch_page(0)

    def resend_password_code(self):
        resend_response, _ = api_client.request_password_reset(self.user_email)
        if resend_response.get('success'):
            self.parent.show_message_box(
                "Code Sent",
                f"A new verification code was sent to {self.user_email}.",
                "information",
            )
            self.password_info.setText(
                f"A verification code was sent to {self.user_email}. Enter it below with your new password."
            )
        else:
            self.parent.show_message_box(
                "Resend Failed",
                resend_response.get('message', 'Failed to resend verification code.'),
                "warning",
            )

    def update_password_with_code(self):
        verification_code = getattr(self, 'pending_password_code', self.code_input.text().strip())
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not verification_code or not new_password or not confirm_password:
            QMessageBox.warning(self, "Missing Information", "Please fill in all password fields.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "The new passwords do not match.")
            return

        reset_response, _ = api_client.reset_password(self.user_email, verification_code, new_password)
        if not reset_response.get('success'):
            QMessageBox.warning(self, "Update Failed", reset_response.get('message', 'Failed to update password'))
            return

        self.parent.show_message_box(
            "Password Updated",
            "Your password has been changed successfully.",
            "information",
        )
        self.switch_page(0)


class SettingsWindow(QDialog):
    """User settings window"""

    def __init__(self, parent, user_email, user_name, user_type):
        super().__init__(parent)
        self.user_email = user_email
        self.user_name = user_name
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
        self.two_fa_check.setChecked(False)
        layout.addWidget(self.two_fa_check)

        layout.addStretch()
        return widget

    def load_settings(self):
        # Populate settings defaults from cached data if any
        data = self.cached_settings_data or {}
        self.case_request_notify.setChecked(data.get('case_requests', True))
        self.case_completed_notify.setChecked(data.get('case_completed', True))
        self.patient_update_notify.setChecked(data.get('patient_updates', True))
        self.system_notify.setChecked(data.get('system_alerts', True))
        self.frequency_combo.setCurrentText(data.get('email_frequency', 'Immediately'))
        self.theme_combo.setCurrentText(data.get('theme', 'Light'))
        self.font_size_spin.setValue(data.get('font_size', 10))
        self.autosave_check.setChecked(data.get('autosave', True))
        self.timeout_spin.setValue(data.get('session_timeout', 120))

    def handle_save_settings(self):
        # Placeholder: persist settings via api_client if needed
        self.parent.show_message_box("Settings Saved", "Settings have been saved.", "information")

    def handle_reset_settings(self):
        # Reset to defaults in UI
        self.frequency_combo.setCurrentText('Immediately')
        self.theme_combo.setCurrentText('Light')
        self.font_size_spin.setValue(10)
        self.autosave_check.setChecked(True)
        self.case_request_notify.setChecked(True)
        self.case_completed_notify.setChecked(True)
        self.patient_update_notify.setChecked(True)
        self.system_notify.setChecked(True)
        self.timeout_spin.setValue(120)
        self.parent.show_message_box("Reset", "Settings have been reset to defaults.", "information")
