from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PasswordLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.focus_in_callback = None
        self.focus_out_callback = None

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.focus_in_callback:
            self.focus_in_callback()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.focus_out_callback:
            self.focus_out_callback()


class SignInForm(QWidget):
    def __init__(self, input_style, button_style):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Welcome Back")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        subtitle = QLabel("Sign in to access your account")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")

        email_label = QLabel("Email Address")
        email_label.setFont(QFont("Segoe UI", 10))
        email_label.setStyleSheet("color: #333;")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setFont(QFont("Segoe UI", 10))
        self.email_input.setMinimumHeight(35)
        self.email_input.setStyleSheet(input_style)

        password_label = QLabel("Password")
        password_label.setFont(QFont("Segoe UI", 10))
        password_label.setStyleSheet("color: #333;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Segoe UI", 10))
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet(input_style)

        self.remember_me_checkbox = QCheckBox("Remember me")
        self.remember_me_checkbox.setFont(QFont("Segoe UI", 10))
        self.remember_me_checkbox.setStyleSheet("color: #666;")

        forgot_layout = QHBoxLayout()
        forgot_layout.addStretch()
        self.forgot_btn = self._create_link_button("Forgot password?")
        forgot_layout.addWidget(self.forgot_btn)

        self.sign_in_btn = QPushButton("Sign In")
        self.sign_in_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.sign_in_btn.setMinimumHeight(40)
        self.sign_in_btn.setCursor(Qt.PointingHandCursor)
        self.sign_in_btn.setStyleSheet(button_style)
        self.sign_in_btn.setEnabled(False)

        switch_layout = QHBoxLayout()
        switch_label = QLabel("Don't have an account?")
        switch_label.setFont(QFont("Segoe UI", 10))
        switch_label.setStyleSheet("color: #666;")
        self.switch_to_signup_btn = self._create_link_button("Sign Up", bold=True)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_to_signup_btn)
        switch_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(15)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.remember_me_checkbox)
        layout.addLayout(forgot_layout)
        layout.addSpacing(8)
        layout.addWidget(self.sign_in_btn)
        layout.addSpacing(12)
        layout.addLayout(switch_layout)
        layout.addStretch()
        
        # Enable Enter key to submit form
        self.password_input.returnPressed.connect(self.sign_in_btn.click)

    def _create_link_button(self, text, bold=True):
        button = QPushButton(text)
        button.setFont(QFont("Segoe UI", 9 if not bold else 10, QFont.Bold if bold else QFont.Normal))
        button.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        button.setCursor(Qt.PointingHandCursor)
        return button


class SignUpForm(QWidget):
    def __init__(self, input_style, button_style):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Create Account")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        subtitle = QLabel("Join us to start your diagnosis journey")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")

        name_label = QLabel("Full Name")
        name_label.setFont(QFont("Segoe UI", 10))
        name_label.setStyleSheet("color: #333;")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. John Doe")
        self.name_input.setFont(QFont("Segoe UI", 10))
        self.name_input.setMinimumHeight(35)
        self.name_input.setStyleSheet(input_style)

        medical_id_label = QLabel("Medical ID")
        medical_id_label.setFont(QFont("Segoe UI", 10))
        medical_id_label.setStyleSheet("color: #333;")

        self.medical_id_input = QLineEdit()
        self.medical_id_input.setPlaceholderText("e.g. 01-MED-123456")
        self.medical_id_input.setFont(QFont("Segoe UI", 10))
        self.medical_id_input.setMinimumHeight(35)
        self.medical_id_input.setStyleSheet(input_style)

        email_label = QLabel("Email Address")
        email_label.setFont(QFont("Segoe UI", 10))
        email_label.setStyleSheet("color: #333;")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g. your.email@example.com")
        self.email_input.setFont(QFont("Segoe UI", 10))
        self.email_input.setMinimumHeight(35)
        self.email_input.setStyleSheet(input_style)

        password_label = QLabel("Password")
        password_label.setFont(QFont("Segoe UI", 10))
        password_label.setStyleSheet("color: #333;")

        self.password_input = PasswordLineEdit()
        self.password_input.setPlaceholderText("Create a password (min. 8 characters)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Segoe UI", 10))
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet(input_style)

        self.password_strength_bar = QProgressBar()
        self.password_strength_bar.setMinimum(0)
        self.password_strength_bar.setMaximum(100)
        self.password_strength_bar.setValue(0)
        self.password_strength_bar.setTextVisible(False)
        self.password_strength_bar.setMinimumHeight(8)
        self.password_strength_bar.hide()
        self.password_strength_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 4px;
                background: #e0e0e0;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: #ff4444;
            }
            """
        )

        self.password_strength_label = QLabel("Password Strength: Weak")
        self.password_strength_label.setFont(QFont("Segoe UI", 9))
        self.password_strength_label.setStyleSheet("color: #ff4444;")
        self.password_strength_label.hide()

        confirm_label = QLabel("Confirm Password")
        confirm_label.setFont(QFont("Segoe UI", 10))
        confirm_label.setStyleSheet("color: #333;")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Re-enter your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFont(QFont("Segoe UI", 10))
        self.confirm_password_input.setMinimumHeight(35)
        self.confirm_password_input.setStyleSheet(input_style)

        terms_layout = QHBoxLayout()
        terms_layout.setSpacing(5)
        self.accept_terms_checkbox = QCheckBox()
        self.accept_terms_checkbox.setStyleSheet("QCheckBox { color: #666; }")

        terms_text = QLabel("I accept the ")
        terms_text.setFont(QFont("Segoe UI", 9))
        terms_text.setStyleSheet("color: #666;")

        self.terms_link = QLabel('<a href="#" style="color: #667eea; text-decoration: none;">Terms of Service and Privacy Policy</a>')
        self.terms_link.setFont(QFont("Segoe UI", 9))
        self.terms_link.setOpenExternalLinks(False)
        self.terms_link.setCursor(Qt.PointingHandCursor)

        terms_layout.addWidget(self.accept_terms_checkbox)
        terms_layout.addWidget(terms_text)
        terms_layout.addWidget(self.terms_link)
        terms_layout.addStretch()

        self.sign_up_btn = QPushButton("Create Account")
        self.sign_up_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.sign_up_btn.setMinimumHeight(40)
        self.sign_up_btn.setCursor(Qt.PointingHandCursor)
        self.sign_up_btn.setStyleSheet(button_style)
        self.sign_up_btn.setEnabled(False)

        switch_layout = QHBoxLayout()
        switch_label = QLabel("Already have an account?")
        switch_label.setFont(QFont("Segoe UI", 10))
        switch_label.setStyleSheet("color: #666;")
        self.switch_to_signin_btn = QPushButton("Sign In")
        self.switch_to_signin_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.switch_to_signin_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.switch_to_signin_btn.setCursor(Qt.PointingHandCursor)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_to_signin_btn)
        switch_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(medical_id_label)
        layout.addWidget(self.medical_id_input)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.password_strength_bar)
        layout.addWidget(self.password_strength_label)
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_password_input)
        layout.addLayout(terms_layout)
        layout.addSpacing(8)
        layout.addWidget(self.sign_up_btn)
        layout.addSpacing(10)
        layout.addLayout(switch_layout)
        layout.addStretch()
        
        # Enable Enter key to submit form
        self.confirm_password_input.returnPressed.connect(self.sign_up_btn.click)


class EmailVerificationForm(QWidget):
    def __init__(self, button_style):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Verify Your Email")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        self.email_label = QLabel("Verification code sent to your email")
        self.email_label.setFont(QFont("Segoe UI", 9))
        self.email_label.setStyleSheet("color: #666; margin-bottom: 15px;")

        info_msg = QLabel(
            "We've sent a 6-digit verification code to your email.\n"
            "Please enter it below to complete your registration."
        )
        info_msg.setFont(QFont("Segoe UI", 10))
        info_msg.setStyleSheet("color: #666; margin-bottom: 20px; line-height: 1.4;")
        info_msg.setWordWrap(True)

        code_label = QLabel("Verification Code")
        code_label.setFont(QFont("Segoe UI", 10))
        code_label.setStyleSheet("color: #333;")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit code")
        self.code_input.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.code_input.setMinimumHeight(45)
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.setMaxLength(6)
        self.code_input.setStyleSheet(
            """
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                color: #333;
                letter-spacing: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background: #fafafa;
            }
            """
        )

        self.timer_label = QLabel()
        self.timer_label.setFont(QFont("Segoe UI", 9))
        self.timer_label.setStyleSheet("color: #ff6b6b;")
        self.timer_label.setAlignment(Qt.AlignCenter)

        self.verify_btn = QPushButton("Verify Email")
        self.verify_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.verify_btn.setMinimumHeight(40)
        self.verify_btn.setCursor(Qt.PointingHandCursor)
        self.verify_btn.setStyleSheet(button_style)
        self.verify_btn.setEnabled(False)

        resend_layout = QHBoxLayout()
        resend_text = QLabel("Didn't receive the code?")
        resend_text.setFont(QFont("Segoe UI", 9))
        resend_text.setStyleSheet("color: #666;")

        self.resend_btn = QPushButton("Resend")
        self.resend_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.resend_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.resend_btn.setCursor(Qt.PointingHandCursor)

        resend_layout.addWidget(resend_text)
        resend_layout.addWidget(self.resend_btn)
        resend_layout.addStretch()

        back_layout = QHBoxLayout()
        back_text = QLabel("Changed your mind?")
        back_text.setFont(QFont("Segoe UI", 9))
        back_text.setStyleSheet("color: #666;")

        self.back_to_signup_btn = QPushButton("Back to Sign Up")
        self.back_to_signup_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.back_to_signup_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.back_to_signup_btn.setCursor(Qt.PointingHandCursor)

        back_layout.addWidget(back_text)
        back_layout.addWidget(self.back_to_signup_btn)
        back_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(self.email_label)
        layout.addWidget(info_msg)
        layout.addSpacing(15)
        layout.addWidget(code_label)
        layout.addWidget(self.code_input)
        layout.addWidget(self.timer_label)
        layout.addSpacing(8)
        layout.addWidget(self.verify_btn)
        layout.addSpacing(10)
        layout.addLayout(resend_layout)
        layout.addSpacing(5)
        layout.addLayout(back_layout)
        layout.addStretch()


class ForgotPasswordForm(QWidget):
    def __init__(self, input_style, button_style):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Reset Password")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        subtitle = QLabel("Enter your email to receive a reset code")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")

        email_label = QLabel("Email Address")
        email_label.setFont(QFont("Segoe UI", 10))
        email_label.setStyleSheet("color: #333;")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setFont(QFont("Segoe UI", 10))
        self.email_input.setMinimumHeight(35)
        self.email_input.setStyleSheet(input_style)

        self.send_reset_code_btn = QPushButton("Send Reset Code")
        self.send_reset_code_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.send_reset_code_btn.setMinimumHeight(40)
        self.send_reset_code_btn.setCursor(Qt.PointingHandCursor)
        self.send_reset_code_btn.setStyleSheet(button_style)
        self.send_reset_code_btn.setEnabled(False)

        back_layout = QHBoxLayout()
        back_text = QLabel("Remembered your password?")
        back_text.setFont(QFont("Segoe UI", 9))
        back_text.setStyleSheet("color: #666;")

        self.back_to_signin_btn = QPushButton("Back to Sign In")
        self.back_to_signin_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.back_to_signin_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.back_to_signin_btn.setCursor(Qt.PointingHandCursor)

        back_layout.addWidget(back_text)
        back_layout.addWidget(self.back_to_signin_btn)
        back_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addSpacing(10)
        layout.addWidget(self.send_reset_code_btn)
        layout.addSpacing(10)
        layout.addLayout(back_layout)
        layout.addStretch()
        
        # Enable Enter key to submit form
        self.email_input.returnPressed.connect(self.send_reset_code_btn.click)
        
        # Enable Enter key to submit form
        self.email_input.returnPressed.connect(self.send_reset_code_btn.click)


class ResetCodeForm(QWidget):
    def __init__(self, button_style):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Verify Reset Code")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        self.email_label = QLabel("Reset code sent to your email")
        self.email_label.setFont(QFont("Segoe UI", 9))
        self.email_label.setStyleSheet("color: #666; margin-bottom: 15px;")

        info_msg = QLabel(
            "We have sent a 6-digit reset code to your email.\n"
            "Please enter it below to continue."
        )
        info_msg.setFont(QFont("Segoe UI", 10))
        info_msg.setStyleSheet("color: #666; margin-bottom: 20px; line-height: 1.4;")
        info_msg.setWordWrap(True)

        code_label = QLabel("Reset Code")
        code_label.setFont(QFont("Segoe UI", 10))
        code_label.setStyleSheet("color: #333;")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit code")
        self.code_input.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.code_input.setMinimumHeight(45)
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.setMaxLength(6)
        self.code_input.setStyleSheet(
            """
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                color: #333;
                letter-spacing: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background: #fafafa;
            }
            """
        )

        self.timer_label = QLabel()
        self.timer_label.setFont(QFont("Segoe UI", 9))
        self.timer_label.setStyleSheet("color: #ff6b6b;")
        self.timer_label.setAlignment(Qt.AlignCenter)

        self.verify_btn = QPushButton("Verify Code")
        self.verify_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.verify_btn.setMinimumHeight(40)
        self.verify_btn.setCursor(Qt.PointingHandCursor)
        self.verify_btn.setStyleSheet(button_style)
        self.verify_btn.setEnabled(False)

        resend_layout = QHBoxLayout()
        resend_text = QLabel("Didn't receive the code?")
        resend_text.setFont(QFont("Segoe UI", 9))
        resend_text.setStyleSheet("color: #666;")

        self.resend_btn = QPushButton("Resend")
        self.resend_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.resend_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.resend_btn.setCursor(Qt.PointingHandCursor)

        resend_layout.addWidget(resend_text)
        resend_layout.addWidget(self.resend_btn)
        resend_layout.addStretch()

        back_layout = QHBoxLayout()
        back_text = QLabel("Changed your mind?")
        back_text.setFont(QFont("Segoe UI", 9))
        back_text.setStyleSheet("color: #666;")

        self.back_to_signin_btn = QPushButton("Back to Sign In")
        self.back_to_signin_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.back_to_signin_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.back_to_signin_btn.setCursor(Qt.PointingHandCursor)

        back_layout.addWidget(back_text)
        back_layout.addWidget(self.back_to_signin_btn)
        back_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(self.email_label)
        layout.addWidget(info_msg)
        layout.addSpacing(15)
        layout.addWidget(code_label)
        layout.addWidget(self.code_input)
        layout.addWidget(self.timer_label)
        layout.addSpacing(8)
        layout.addWidget(self.verify_btn)
        layout.addSpacing(10)
        layout.addLayout(resend_layout)
        layout.addSpacing(5)
        layout.addLayout(back_layout)
        layout.addStretch()
        
        # Enable Enter key to submit form
        self.code_input.returnPressed.connect(self.verify_btn.click)


class NewPasswordForm(QWidget):
    def __init__(self, input_style, button_style):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Create New Password")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")

        subtitle = QLabel("Choose a strong new password")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")

        password_label = QLabel("New Password")
        password_label.setFont(QFont("Segoe UI", 10))
        password_label.setStyleSheet("color: #333;")

        self.new_password_input = PasswordLineEdit()
        self.new_password_input.setPlaceholderText("Enter a new password")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setFont(QFont("Segoe UI", 10))
        self.new_password_input.setMinimumHeight(35)
        self.new_password_input.setStyleSheet(input_style)

        self.password_strength_bar = QProgressBar()
        self.password_strength_bar.setMinimum(0)
        self.password_strength_bar.setMaximum(100)
        self.password_strength_bar.setValue(0)
        self.password_strength_bar.setTextVisible(False)
        self.password_strength_bar.setMinimumHeight(8)
        self.password_strength_bar.hide()
        self.password_strength_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 4px;
                background: #e0e0e0;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: #ff4444;
            }
            """
        )

        self.password_strength_label = QLabel("Password Strength: Weak")
        self.password_strength_label.setFont(QFont("Segoe UI", 9))
        self.password_strength_label.setStyleSheet("color: #ff4444;")
        self.password_strength_label.hide()

        confirm_label = QLabel("Confirm Password")
        confirm_label.setFont(QFont("Segoe UI", 10))
        confirm_label.setStyleSheet("color: #333;")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Re-enter your new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFont(QFont("Segoe UI", 10))
        self.confirm_password_input.setMinimumHeight(35)
        self.confirm_password_input.setStyleSheet(input_style)

        self.update_password_btn = QPushButton("Update Password")
        self.update_password_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.update_password_btn.setMinimumHeight(40)
        self.update_password_btn.setCursor(Qt.PointingHandCursor)
        self.update_password_btn.setStyleSheet(button_style)
        self.update_password_btn.setEnabled(False)

        back_layout = QHBoxLayout()
        back_text = QLabel("Need to start over?")
        back_text.setFont(QFont("Segoe UI", 9))
        back_text.setStyleSheet("color: #666;")

        self.back_to_signin_btn = QPushButton("Back to Sign In")
        self.back_to_signin_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.back_to_signin_btn.setStyleSheet(
            """
            QPushButton {
                color: #667eea;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #764ba2;
            }
            """
        )
        self.back_to_signin_btn.setCursor(Qt.PointingHandCursor)

        back_layout.addWidget(back_text)
        back_layout.addWidget(self.back_to_signin_btn)
        back_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(password_label)
        layout.addWidget(self.new_password_input)
        layout.addWidget(self.password_strength_bar)
        layout.addWidget(self.password_strength_label)
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_password_input)
        layout.addSpacing(10)
        layout.addWidget(self.update_password_btn)
        layout.addSpacing(10)
        layout.addLayout(back_layout)
        layout.addStretch()
        
        # Enable Enter key to submit form
        self.confirm_password_input.returnPressed.connect(self.update_password_btn.click)


def create_branding_panel():
    panel = QFrame()
    panel.setObjectName("leftPanel")
    panel.setStyleSheet(
        """
        #leftPanel {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #667eea, stop:1 #764ba2);
        }
        """
    )

    layout = QVBoxLayout(panel)
    layout.setAlignment(Qt.AlignCenter)
    layout.setContentsMargins(25, 25, 25, 25)

    title = QLabel("DeepNeuro")
    title.setFont(QFont("Segoe UI", 20, QFont.Bold))
    title.setStyleSheet("color: white;")
    title.setAlignment(Qt.AlignCenter)

    subtitle = QLabel("Brain Disease Diagnosis System")
    subtitle.setFont(QFont("Segoe UI", 11))
    subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin-top: 10px;")
    subtitle.setAlignment(Qt.AlignCenter)

    description = QLabel(
        "Advanced AI-powered diagnosis for:\n\n"
        "- Glioma Tumor Detection\n"
        "- Hemorrhagic Stroke Analysis\n"
        "- Ischemic Stroke Detection\n\n"
        "Accurate, Fast, and Reliable\n"
        "Medical Imaging Analysis"
    )
    description.setFont(QFont("Segoe UI", 10))
    description.setStyleSheet(
        """
        color: rgba(255, 255, 255, 0.85);
        margin-top: 25px;
        line-height: 1.5;
        """
    )
    description.setAlignment(Qt.AlignLeft)

    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addWidget(description)
    layout.addStretch()

    return panel
