from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from api_client import api_client
from auth_screens import (
    EmailVerificationForm,
    ForgotPasswordForm,
    NewPasswordForm,
    ResetCodeForm,
    SignInForm,
    SignUpForm,
    create_branding_panel,
)
from landing_page import LandingPage


class AuthWindow(QMainWindow):
    PAGE_SIGN_IN = 0
    PAGE_SIGN_UP = 1
    PAGE_VERIFY_EMAIL = 2
    PAGE_FORGOT_PASSWORD = 3
    PAGE_RESET_CODE = 4
    PAGE_NEW_PASSWORD = 5

    def __init__(self):
        super().__init__()
        self.current_verification_email = None
        self.verification_attempts = 0
        self.verification_time_remaining = 0

        self.current_reset_email = None
        self.current_reset_code = None
        self.reset_attempts = 0
        self.reset_time_remaining = 0

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("DeepNeuro - Brain Disease Diagnosis")
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(create_branding_panel(), 0)
        main_layout.addWidget(self.create_right_panel(), 1)

    def create_right_panel(self):
        panel = QWidget()
        panel.setObjectName("rightPanel")
        panel.setStyleSheet("#rightPanel { background: white; }")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(35, 25, 35, 25)

        self.stacked_widget = QStackedWidget()

        input_style = self.get_input_style()
        button_style = self.get_button_style()

        self.signin_form = SignInForm(input_style, button_style)
        self.signup_form = SignUpForm(input_style, button_style)
        self.verify_form = EmailVerificationForm(button_style)
        self.forgot_form = ForgotPasswordForm(input_style, button_style)
        self.reset_code_form = ResetCodeForm(button_style)
        self.new_password_form = NewPasswordForm(input_style, button_style)

        self.stacked_widget.addWidget(self.signin_form)
        self.stacked_widget.addWidget(self.signup_form)
        self.stacked_widget.addWidget(self.verify_form)
        self.stacked_widget.addWidget(self.forgot_form)
        self.stacked_widget.addWidget(self.reset_code_form)
        self.stacked_widget.addWidget(self.new_password_form)

        self.bind_events()
        layout.addWidget(self.stacked_widget)
        return panel

    def bind_events(self):
        self.signin_form.email_input.textChanged.connect(self.validate_login_form)
        self.signin_form.password_input.textChanged.connect(self.validate_login_form)
        self.signin_form.sign_in_btn.clicked.connect(self.handle_login)
        self.signin_form.switch_to_signup_btn.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_UP)
        )
        self.signin_form.forgot_btn.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(self.PAGE_FORGOT_PASSWORD)
        )

        self.signup_form.name_input.textChanged.connect(self.validate_signup_form)
        self.signup_form.medical_id_input.textChanged.connect(self.validate_signup_form)
        self.signup_form.email_input.textChanged.connect(self.validate_signup_form)
        self.signup_form.password_input.textChanged.connect(self.validate_signup_form)
        self.signup_form.confirm_password_input.textChanged.connect(self.validate_signup_form)
        self.signup_form.accept_terms_checkbox.stateChanged.connect(self.validate_signup_form)
        self.signup_form.password_input.textChanged.connect(self.update_password_strength)
        self.signup_form.password_input.focus_in_callback = self.on_password_focus_in
        self.signup_form.password_input.focus_out_callback = self.on_password_focus_out
        self.signup_form.sign_up_btn.clicked.connect(self.handle_signup)
        self.signup_form.switch_to_signin_btn.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_IN)
        )
        self.signup_form.terms_link.linkActivated.connect(self.show_terms_dialog)

        self.verify_form.code_input.textChanged.connect(self.validate_code_input)
        self.verify_form.code_input.textChanged.connect(self.validate_verification_form)
        self.verify_form.verify_btn.clicked.connect(self.handle_verification)
        self.verify_form.resend_btn.clicked.connect(self.resend_verification_code)
        self.verify_form.back_to_signup_btn.clicked.connect(self.go_back_to_signup)

        self.forgot_form.email_input.textChanged.connect(self.validate_forgot_form)
        self.forgot_form.send_reset_code_btn.clicked.connect(self.handle_forgot_password)
        self.forgot_form.back_to_signin_btn.clicked.connect(self.go_back_to_login)

        self.reset_code_form.code_input.textChanged.connect(self.validate_reset_code_input)
        self.reset_code_form.code_input.textChanged.connect(self.validate_reset_code_form)
        self.reset_code_form.verify_btn.clicked.connect(self.handle_reset_code_verification)
        self.reset_code_form.resend_btn.clicked.connect(self.resend_reset_code)
        self.reset_code_form.back_to_signin_btn.clicked.connect(self.go_back_to_login)

        self.new_password_form.new_password_input.textChanged.connect(self.validate_new_password_form)
        self.new_password_form.confirm_password_input.textChanged.connect(self.validate_new_password_form)
        self.new_password_form.new_password_input.textChanged.connect(self.update_reset_password_strength)
        self.new_password_form.new_password_input.focus_in_callback = self.on_reset_password_focus_in
        self.new_password_form.new_password_input.focus_out_callback = self.on_reset_password_focus_out
        self.new_password_form.update_password_btn.clicked.connect(self.handle_password_reset)
        self.new_password_form.back_to_signin_btn.clicked.connect(self.go_back_to_login)

    def get_input_style(self):
        return """
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background: #fafafa;
            }
        """

    def get_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6941a5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bc4, stop:1 #5d3a94);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #888888;
            }
        """

    def get_dialog_style(self):
        return """
            QMessageBox {
                background: white;
            }
            QMessageBox QLabel {
                color: #333;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 60px;
                font-weight: 600;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6941a5);
            }
            QMessageBox QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bc4, stop:1 #5d3a94);
            }
        """

    def show_message_box(self, title, message, msg_type="warning"):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(self.get_dialog_style())

        if msg_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif msg_type == "critical":
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.Information)

        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def validate_login_form(self):
        email_filled = bool(self.signin_form.email_input.text().strip())
        password_filled = bool(self.signin_form.password_input.text())
        self.signin_form.sign_in_btn.setEnabled(email_filled and password_filled)

    def validate_signup_form(self):
        name_filled = bool(self.signup_form.name_input.text().strip())
        email_filled = bool(self.signup_form.email_input.text().strip())
        password_filled = bool(self.signup_form.password_input.text())
        confirm_filled = bool(self.signup_form.confirm_password_input.text())
        medical_id_filled = bool(self.signup_form.medical_id_input.text().strip())
        terms_accepted = self.signup_form.accept_terms_checkbox.isChecked()
        self.signup_form.sign_up_btn.setEnabled(
            name_filled and email_filled and password_filled and confirm_filled and medical_id_filled and terms_accepted
        )

    def on_password_focus_in(self):
        self.signup_form.password_strength_bar.show()
        self.signup_form.password_strength_label.show()
        if self.signup_form.password_input.text():
            self.update_password_strength()

    def on_password_focus_out(self):
        self.signup_form.password_strength_bar.hide()
        self.signup_form.password_strength_label.hide()

    def animate_progress_bar(self, end_value):
        if hasattr(self, "progress_animation") and self.progress_animation.state() == QPropertyAnimation.Running:
            self.progress_animation.stop()

        self.progress_animation = QPropertyAnimation(self.signup_form.password_strength_bar, b"value")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_animation.setStartValue(self.signup_form.password_strength_bar.value())
        self.progress_animation.setEndValue(min(end_value, 100))
        self.progress_animation.start()

    def update_password_strength(self):
        password = self.signup_form.password_input.text()
        strength = 0
        strength_text = "Password Strength: Weak"
        strength_color = "#ff4444"

        if password:
            if len(password) >= 8:
                strength += 20
            if len(password) >= 12:
                strength += 10
            if len(password) >= 16:
                strength += 10
            if any(c.islower() for c in password):
                strength += 15
            if any(c.isupper() for c in password):
                strength += 15
            if any(c.isdigit() for c in password):
                strength += 15
            if any(not c.isalnum() for c in password):
                strength += 15

            if strength < 30:
                strength_text, strength_color = "Password Strength: Weak", "#ff4444"
            elif strength < 50:
                strength_text, strength_color = "Password Strength: Fair", "#ffaa00"
            elif strength < 75:
                strength_text, strength_color = "Password Strength: Good", "#88cc00"
            else:
                strength_text, strength_color = "Password Strength: Strong", "#44cc44"

        self.signup_form.password_strength_label.setText(strength_text)
        self.signup_form.password_strength_label.setStyleSheet(f"color: {strength_color};")
        self.signup_form.password_strength_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: #e0e0e0;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: {strength_color};
            }}
            """
        )
        self.animate_progress_bar(strength)

    def on_reset_password_focus_in(self):
        self.new_password_form.password_strength_bar.show()
        self.new_password_form.password_strength_label.show()
        if self.new_password_form.new_password_input.text():
            self.update_reset_password_strength()

    def on_reset_password_focus_out(self):
        self.new_password_form.password_strength_bar.hide()
        self.new_password_form.password_strength_label.hide()

    def animate_reset_progress_bar(self, end_value):
        if hasattr(self, "reset_progress_animation") and self.reset_progress_animation.state() == QPropertyAnimation.Running:
            self.reset_progress_animation.stop()

        self.reset_progress_animation = QPropertyAnimation(self.new_password_form.password_strength_bar, b"value")
        self.reset_progress_animation.setDuration(300)
        self.reset_progress_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.reset_progress_animation.setStartValue(self.new_password_form.password_strength_bar.value())
        self.reset_progress_animation.setEndValue(min(end_value, 100))
        self.reset_progress_animation.start()

    def update_reset_password_strength(self):
        password = self.new_password_form.new_password_input.text()
        strength = 0
        strength_text = "Password Strength: Weak"
        strength_color = "#ff4444"

        if password:
            if len(password) >= 8:
                strength += 20
            if len(password) >= 12:
                strength += 10
            if len(password) >= 16:
                strength += 10
            if any(c.islower() for c in password):
                strength += 15
            if any(c.isupper() for c in password):
                strength += 15
            if any(c.isdigit() for c in password):
                strength += 15
            if any(not c.isalnum() for c in password):
                strength += 15

            if strength < 30:
                strength_text, strength_color = "Password Strength: Weak", "#ff4444"
            elif strength < 50:
                strength_text, strength_color = "Password Strength: Fair", "#ffaa00"
            elif strength < 75:
                strength_text, strength_color = "Password Strength: Good", "#88cc00"
            else:
                strength_text, strength_color = "Password Strength: Strong", "#44cc44"

        self.new_password_form.password_strength_label.setText(strength_text)
        self.new_password_form.password_strength_label.setStyleSheet(f"color: {strength_color};")
        self.new_password_form.password_strength_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: #e0e0e0;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: {strength_color};
            }}
            """
        )
        self.animate_reset_progress_bar(strength)

    def show_terms_dialog(self):
        terms_text = """
        <h2>Terms of Service and Privacy Policy</h2>

        <h3>Terms of Service</h3>
        <p><b>1. Acceptance of Terms</b><br>
        By accessing and using DeepNeuro Brain Disease Diagnosis System, you accept and agree to be bound by the terms and provision of this agreement.</p>

        <p><b>2. Use License</b><br>
        Permission is granted to use this application for medical diagnosis purposes. This is the grant of a license, not a transfer of title.</p>

        <p><b>3. Medical Disclaimer</b><br>
        This AI-powered system is designed to assist medical professionals. All diagnoses should be verified by qualified healthcare providers. DeepNeuro is not a substitute for professional medical advice.</p>

        <p><b>4. User Responsibilities</b><br>
        - Provide accurate patient information<br>
        - Maintain confidentiality of account credentials<br>
        - Use the system in accordance with medical ethics<br>
        - Report any system errors or inconsistencies</p>

        <p><b>5. Limitation of Liability</b><br>
        DeepNeuro and its developers shall not be liable for any damages arising from the use or inability to use this application.</p>

        <h3>Privacy Policy</h3>
        <p><b>1. Information Collection</b><br>
        We collect user account information (name, email) and medical imaging data for diagnosis purposes.</p>

        <p><b>2. Data Usage</b><br>
        Your data is used solely for:<br>
        - Providing diagnosis services<br>
        - Improving AI model accuracy<br>
        - System analytics and performance monitoring</p>

        <p><b>3. Data Security</b><br>
        We implement industry-standard security measures including:<br>
        - Encrypted password storage<br>
        - Secure data transmission<br>
        - Regular security audits</p>

        <p><b>4. Data Sharing</b><br>
        We do not share, sell, or distribute your personal or medical data to third parties without explicit consent.</p>

        <p><b>5. Your Rights</b><br>
        You have the right to:<br>
        - Access your stored data<br>
        - Request data deletion<br>
        - Update your information<br>
        - Withdraw consent at any time</p>

        <p><b>6. Changes to Policy</b><br>
        We reserve the right to update this policy. Users will be notified of significant changes.</p>

        <p style="margin-top: 20px;"><i>Last updated: February 18, 2026</i></p>
        """

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Terms of Service and Privacy Policy")
        dialog.setTextFormat(Qt.RichText)
        dialog.setText(terms_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setIcon(QMessageBox.Information)
        dialog.setStyleSheet(self.get_dialog_style())
        dialog.exec()

    def handle_login(self):
        email = self.signin_form.email_input.text().strip()
        password = self.signin_form.password_input.text()

        if not email or not password:
            self.show_message_box("Error", "Please fill in all fields.", "warning")
            return

        response, status_code = api_client.login(email, password)
        if response.get("success") and status_code == 200:
            user = response.get("user", {})
            user_type = user.get("user_type", "unknown")
            user_name = user.get("name", email)
            self.landing_page = LandingPage(email, user_type, user_name)
            self.landing_page.show()
            self.close()
            return

        self.show_message_box(
            "Login Failed",
            response.get("message", "Invalid email or password.\nPlease try again."),
            "critical",
        )

    def handle_signup(self):
        name = self.signup_form.name_input.text().strip()
        email = self.signup_form.email_input.text().strip()
        password = self.signup_form.password_input.text()
        confirm = self.signup_form.confirm_password_input.text()
        medical_id = self.signup_form.medical_id_input.text().strip()

        if not all([name, email, password, confirm, medical_id]):
            self.show_message_box("Error", "Please fill in all fields.", "warning")
            return

        if not self.signup_form.accept_terms_checkbox.isChecked():
            self.show_message_box("Error", "Please accept the Terms of Service and Privacy Policy.", "warning")
            return

        if len(password) < 8:
            self.show_message_box("Error", "Password must be at least 8 characters long.", "warning")
            return

        if password != confirm:
            self.show_message_box("Error", "Passwords do not match.", "warning")
            return

        if "@" not in email or "." not in email:
            self.show_message_box("Error", "Please enter a valid email address.", "warning")
            return

        if not (medical_id.startswith("01") or medical_id.startswith("02")):
            self.show_message_box(
                "Error",
                "Medical ID must start with 01 (Doctor) or 02 (Radiologist).",
                "warning",
            )
            return

        response, status_code = api_client.register(name, email, password, medical_id)
        if response.get("success") and status_code == 201:
            self.show_verification_form(email)
            return

        self.show_message_box(
            "Registration Error",
            response.get("message", "Failed to register. Please try again."),
            "critical",
        )

    def show_verification_form(self, email):
        self.current_verification_email = email
        self.verification_attempts = 0
        self.verify_form.email_label.setText(f"Verification code sent to {email}")
        self.verify_form.code_input.clear()
        self.verify_form.code_input.setEnabled(True)
        self.verify_form.verify_btn.setEnabled(False)
        self.verify_form.resend_btn.setEnabled(True)

        self.verification_time_remaining = 900
        self.start_verification_timer()
        self.stacked_widget.setCurrentIndex(self.PAGE_VERIFY_EMAIL)

    def start_verification_timer(self):
        if hasattr(self, "verification_timer") and self.verification_timer.isActive():
            self.verification_timer.stop()
        self.verification_timer = QTimer()
        self.verification_timer.timeout.connect(self.update_verification_timer)
        self.verification_timer.start(1000)

    def update_verification_timer(self):
        self.verification_time_remaining -= 1
        minutes = self.verification_time_remaining // 60
        seconds = self.verification_time_remaining % 60
        self.verify_form.timer_label.setText(f"Code expires in {minutes:02d}:{seconds:02d}")

        if self.verification_time_remaining <= 0:
            self.verification_timer.stop()
            self.verify_form.timer_label.setText("Verification code has expired")
            self.verify_form.timer_label.setStyleSheet("color: #ff4444;")
            self.verify_form.verify_btn.setEnabled(False)
            self.verify_form.code_input.setEnabled(False)

    def validate_code_input(self):
        text = self.verify_form.code_input.text()
        filtered_text = "".join(c for c in text if c.isdigit())
        if filtered_text != text:
            self.verify_form.code_input.setText(filtered_text)

    def validate_verification_form(self):
        code = self.verify_form.code_input.text()
        self.verify_form.verify_btn.setEnabled(len(code) == 6 and self.verification_time_remaining > 0)

    def validate_forgot_form(self):
        email_filled = bool(self.forgot_form.email_input.text().strip())
        self.forgot_form.send_reset_code_btn.setEnabled(email_filled)

    def handle_forgot_password(self):
        email = self.forgot_form.email_input.text().strip()

        if not email:
            self.show_message_box("Error", "Please enter your email address.", "warning")
            return

        if "@" not in email or "." not in email:
            self.show_message_box("Error", "Please enter a valid email address.", "warning")
            return

        response, _ = api_client.request_password_reset(email)
        if response.get("success"):
            self.show_reset_code_form(email)
            return

        self.show_message_box("Error", response.get("message", "Failed to request password reset."), "warning")

    def show_reset_code_form(self, email):
        self.current_reset_email = email
        self.reset_attempts = 0
        self.reset_code_form.email_label.setText(f"Reset code sent to {email}")
        self.reset_code_form.code_input.clear()
        self.reset_code_form.code_input.setEnabled(True)
        self.reset_code_form.timer_label.setStyleSheet("color: #ff6b6b;")
        self.reset_code_form.verify_btn.setEnabled(False)
        self.reset_code_form.resend_btn.setEnabled(True)

        self.reset_time_remaining = 900
        self.start_reset_timer()
        self.stacked_widget.setCurrentIndex(self.PAGE_RESET_CODE)

    def start_reset_timer(self):
        if hasattr(self, "reset_timer") and self.reset_timer.isActive():
            self.reset_timer.stop()
        self.reset_timer = QTimer()
        self.reset_timer.timeout.connect(self.update_reset_timer)
        self.reset_timer.start(1000)

    def update_reset_timer(self):
        self.reset_time_remaining -= 1
        minutes = self.reset_time_remaining // 60
        seconds = self.reset_time_remaining % 60
        self.reset_code_form.timer_label.setText(f"Code expires in {minutes:02d}:{seconds:02d}")

        if self.reset_time_remaining <= 0:
            self.reset_timer.stop()
            self.reset_code_form.timer_label.setText("Reset code has expired")
            self.reset_code_form.timer_label.setStyleSheet("color: #ff4444;")
            self.reset_code_form.verify_btn.setEnabled(False)
            self.reset_code_form.code_input.setEnabled(False)

    def validate_reset_code_input(self):
        text = self.reset_code_form.code_input.text()
        filtered_text = "".join(c for c in text if c.isdigit())
        if filtered_text != text:
            self.reset_code_form.code_input.setText(filtered_text)

    def validate_reset_code_form(self):
        code = self.reset_code_form.code_input.text()
        self.reset_code_form.verify_btn.setEnabled(len(code) == 6 and self.reset_time_remaining > 0)

    def handle_reset_code_verification(self):
        email = self.current_reset_email
        code = self.reset_code_form.code_input.text()

        if not code:
            self.show_message_box("Error", "Please enter the reset code.", "warning")
            return

        self.reset_attempts += 1
        if self.reset_attempts > 5:
            self.show_message_box("Error", "Too many incorrect attempts. Please request a new code.", "warning")
            if hasattr(self, "reset_timer"):
                self.reset_timer.stop()
            self.go_back_to_login()
            return

        response, _ = api_client.verify_reset_code(email, code)
        if response.get("success"):
            self.current_reset_code = code
            if hasattr(self, "reset_timer"):
                self.reset_timer.stop()
            self.new_password_form.new_password_input.clear()
            self.new_password_form.confirm_password_input.clear()
            self.new_password_form.update_password_btn.setEnabled(False)
            self.stacked_widget.setCurrentIndex(self.PAGE_NEW_PASSWORD)
            return

        remaining_attempts = 5 - self.reset_attempts
        self.show_message_box(
            "Verification Failed",
            f"{response.get('message', 'Invalid reset code')}\n\nRemaining attempts: {remaining_attempts}",
            "warning",
        )

    def resend_reset_code(self):
        email = self.current_reset_email
        response, _ = api_client.request_password_reset(email)
        if not response.get("success"):
            self.show_message_box("Error", response.get("message", "Failed to resend reset code."), "warning")
            return

        self.reset_code_form.code_input.clear()
        self.reset_time_remaining = 900
        self.reset_attempts = 0
        self.start_reset_timer()
        self.show_message_box("Success", "New reset code has been sent to your email.", "information")

    def validate_new_password_form(self):
        password_filled = bool(self.new_password_form.new_password_input.text())
        confirm_filled = bool(self.new_password_form.confirm_password_input.text())
        self.new_password_form.update_password_btn.setEnabled(password_filled and confirm_filled)

    def handle_password_reset(self):
        email = self.current_reset_email
        password = self.new_password_form.new_password_input.text()
        confirm = self.new_password_form.confirm_password_input.text()

        if not password or not confirm:
            self.show_message_box("Error", "Please fill in all fields.", "warning")
            return

        if len(password) < 8:
            self.show_message_box("Error", "Password must be at least 8 characters long.", "warning")
            return

        if password != confirm:
            self.show_message_box("Error", "Passwords do not match.", "warning")
            return

        if not self.current_reset_code:
            self.show_message_box("Error", "Reset session expired. Please request a new code.", "warning")
            self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_IN)
            return

        response, _ = api_client.reset_password(email, self.current_reset_code, password)
        if response.get("success"):
            self.show_message_box("Success", "Your password has been updated. You can now sign in.", "information")
            self.clear_reset_forms()
            self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_IN)
            return

        self.show_message_box(
            "Error",
            response.get("message", "Failed to update password. Please try again."),
            "critical",
        )

    def go_back_to_login(self):
        if hasattr(self, "reset_timer") and self.reset_timer.isActive():
            self.reset_timer.stop()
        self.clear_reset_forms()
        self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_IN)

    def clear_reset_forms(self):
        self.forgot_form.email_input.clear()
        self.reset_code_form.code_input.clear()
        self.new_password_form.new_password_input.clear()
        self.new_password_form.confirm_password_input.clear()
        self.current_reset_email = None
        self.current_reset_code = None
        self.new_password_form.password_strength_bar.hide()
        self.new_password_form.password_strength_label.hide()

    def handle_verification(self):
        email = self.current_verification_email
        code = self.verify_form.code_input.text()

        if not code:
            self.show_message_box("Error", "Please enter the verification code.", "warning")
            return

        self.verification_attempts += 1
        if self.verification_attempts > 5:
            self.show_message_box(
                "Error",
                "Too many incorrect attempts.\nPlease request a new verification code.",
                "warning",
            )
            if hasattr(self, "verification_timer"):
                self.verification_timer.stop()
            self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_UP)
            self.clear_signup_form()
            return

        response, status_code = api_client.verify_email(email, code)
        if response.get("success") and status_code == 200:
            if hasattr(self, "verification_timer") and self.verification_timer.isActive():
                self.verification_timer.stop()
            self.show_message_box(
                "Success",
                "Email verified successfully!\n\nYour account has been created.\nYou can now sign in with your credentials.",
                "information",
            )
            self.clear_signup_form()
            self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_IN)
            return

        remaining_attempts = 5 - self.verification_attempts
        self.show_message_box(
            "Verification Failed",
            f"{response.get('message', 'Invalid verification code')}\n\nRemaining attempts: {remaining_attempts}",
            "warning",
        )

    def resend_verification_code(self):
        if not self.current_verification_email:
            self.show_message_box("Error", "Verification session not found.", "warning")
            return

        response, _ = api_client.resend_email_verification(self.current_verification_email)
        if not response.get("success"):
            self.show_message_box(
                "Error",
                response.get("message", "Failed to resend verification email."),
                "warning",
            )
            return

        self.verify_form.code_input.clear()
        self.verify_form.code_input.setEnabled(True)
        self.verification_attempts = 0
        self.verification_time_remaining = 900
        self.start_verification_timer()
        self.show_message_box("Success", "New verification code has been sent to your email.", "information")

    def go_back_to_signup(self):
        if hasattr(self, "verification_timer") and self.verification_timer.isActive():
            self.verification_timer.stop()
        self.stacked_widget.setCurrentIndex(self.PAGE_SIGN_UP)

    def clear_signup_form(self):
        self.signup_form.name_input.clear()
        self.signup_form.email_input.clear()
        self.signup_form.password_input.clear()
        self.signup_form.confirm_password_input.clear()
        self.signup_form.medical_id_input.clear()
        self.signup_form.accept_terms_checkbox.setChecked(False)
