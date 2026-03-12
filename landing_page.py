from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QStackedWidget,
                               QSizePolicy, QMessageBox, QDialog, QFormLayout,
                               QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from api_client import api_client
from doctor_view import DoctorView
from radiologist_view import RadiologistView
from datetime import datetime

class LandingPage(QMainWindow):
    def __init__(self, user_email, user_type='unknown', user_name=None):
        super().__init__()
        self.user_email = user_email
        self.user_type = user_type  # 'doctor' or 'radiologist'
        self.user_name = user_name or user_email
        
        # Initialize view based on user type
        if self.user_type == 'doctor':
            self.view = DoctorView(self)
        elif self.user_type == 'radiologist':
            self.view = RadiologistView(self)
        else:
            self.view = None
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('DeepNeuro - Brain Disease Diagnosis')
        self.showMaximized()
        
        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f5f7fa, stop:1 #e8ecf2);
        """)
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # Stacked layout for landing and viewer
        self.stacked = QStackedWidget()
        self.landing_widget = self.create_landing_page()
        self.viewer_widget = self.create_viewer_page()
        self.stacked.addWidget(self.landing_widget)
        self.stacked.addWidget(self.viewer_widget)
        main_layout.addWidget(self.stacked)
        
        # No animations

    def create_landing_page(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        header = self.create_header()
        layout.addWidget(header)
        
        # Add user type info
        user_type_label = QLabel(f"Role: {self.user_type.capitalize()}")
        user_type_label.setFont(QFont("Segoe UI", 9))
        user_type_label.setStyleSheet("color: #666; margin-left: 8px;")
        layout.addWidget(user_type_label)

        # Get buttons container from the appropriate view
        if self.view:
            buttons_container = self.view.create_buttons_container()
            layout.addWidget(buttons_container)
            
            # Add inbox view for doctors, requests view for radiologists
            if self.user_type == 'doctor':
                self.inbox_container = self.view.create_inbox_view()
                layout.addWidget(self.inbox_container, 1)
            elif self.user_type == 'radiologist':
                self.requests_container = self.view.create_radiologist_requests_view()
                layout.addWidget(self.requests_container, 1)
        else:
            layout.addStretch()
        
        return container

    def create_viewer_page(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        back_btn = QPushButton("← Back to Landing")
        back_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #edf2f7;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
            QPushButton:pressed {
                background: #cbd5e0;
            }
        """)
        back_btn.clicked.connect(self.show_landing_page)

        title = QLabel("🧠 3D Brain Visualization")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
    
        header_layout.addWidget(back_btn)
        header_layout.addSpacing(8)
        header_layout.addWidget(title)
        header_layout.addStretch()


        viewer_container = QFrame()
        viewer_container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid #e2e8f0;
            }
        """)
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(12, 12, 12, 12)
        viewer_layout.setSpacing(8)

        self.viewer_host = QWidget()
        self.viewer_host_layout = QVBoxLayout(self.viewer_host)
        self.viewer_host_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer_host_layout.setSpacing(0)
        self.viewer_host_layout.addWidget(self.create_viewer_placeholder())

        viewer_layout.addWidget(self.viewer_host)

        layout.addWidget(header)
        layout.addWidget(viewer_container)
        return container

    def create_viewer_placeholder(self):
        placeholder = QFrame()
        placeholder.setStyleSheet("""
            QFrame {
                border: 2px dashed #cbd5e0;
                border-radius: 8px;
                background: #f8fafc;
            }
        """)
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("No visualization loaded yet")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #2d3748;")

        subtitle = QLabel("Click 'Visualize Medical Records' to open the viewer")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #718096;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return placeholder
    
    def get_dialog_style(self):
        """Return stylesheet for dialog boxes"""
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
    
    def show_message_box(self, title, message, msg_type="information"):
        """Show styled message box"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(self.get_dialog_style())
        
        if msg_type == "question":
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            return msg_box.exec()
        elif msg_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif msg_type == "critical":
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.Information)
        
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
        
    def create_header(self):
        """Create header with welcome message"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f172a, stop:0.55 #1e293b, stop:1 #334155);
                border-radius: 8px;
                padding: 12px 16px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(10)
        
        # Welcome icon and message
        welcome_container = QWidget()
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setSpacing(2)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        
        welcome = QLabel(f"Welcome to DeepNeuro")
        welcome.setFont(QFont("Segoe UI", 14, QFont.Bold))
        welcome.setStyleSheet("color: white;")
        
        user_label = QLabel(f"👤 Dr {self.user_name}")
        user_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        user_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        welcome_layout.addWidget(welcome)
        welcome_layout.addWidget(user_label)
        
        # Profile button
        profile_btn = QPushButton("👤 Profile")
        profile_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        profile_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        profile_btn.setCursor(Qt.PointingHandCursor)
        profile_btn.clicked.connect(self.handle_profile)
        profile_btn.setFixedHeight(35)

        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        settings_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.clicked.connect(self.handle_settings)
        settings_btn.setFixedHeight(35)

        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.handle_logout)
        logout_btn.setFixedHeight(35)
        
        layout.addWidget(welcome_container)
        layout.addStretch()
        layout.addWidget(profile_btn)
        layout.addWidget(settings_btn)
        layout.addWidget(logout_btn)
        
        return header
    
    def create_info_cards(self):
        """Create info cards with key features"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        layout.setStretch(2, 1)
        
        # Card 1: AI Powered
        card1 = self.create_info_card("🤖", "AI-Powered", "Advanced deep learning models")
        
        # Card 2: Fast Results
        card2 = self.create_info_card("⚡", "Fast Results", "Diagnosis in seconds")
        
        # Card 3: High Accuracy
        card3 = self.create_info_card("🎯", "Accurate", "Clinical-grade precision")
        
        layout.addWidget(card1)
        layout.addWidget(card2)
        layout.addWidget(card3)
        
        return container

    def create_hero_section(self):
        hero = QFrame()
        hero.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f172a, stop:0.55 #1e293b, stop:1 #334155);
                border-radius: 10px;
                padding: 12px;
            }
        """)
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        headline = QLabel("Precision neuro-imaging, unified workflow")
        headline.setFont(QFont("Segoe UI", 13, QFont.Bold))
        headline.setStyleSheet("color: white;")

        copy = QLabel(
            "Upload MRI data, run AI segmentation, and explore results in 3D\n"
            "without leaving this workspace. Designed for speed and clarity."
        )
        copy.setFont(QFont("Segoe UI", 8))
        copy.setStyleSheet("color: rgba(255, 255, 255, 0.85);")

        left_layout.addWidget(headline)
        left_layout.addWidget(copy)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        metric1 = self.create_metric_card("99.1%", "Model accuracy", "Latest validation")
        metric2 = self.create_metric_card("< 12s", "Avg. processing", "GPU optimized")

        right_layout.addWidget(metric1)
        right_layout.addWidget(metric2)

        layout.addWidget(left, 2)
        layout.addWidget(right, 1)
        return hero

    def create_metric_card(self, value, title, subtitle):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        value_label.setStyleSheet("color: white;")

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Segoe UI", 7))
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        layout.addWidget(value_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return card

    def create_steps_section(self):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 8px;
            }
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        step1 = self.create_step_card("1", "Upload MRI", "Drop a .nii.gz file")
        step2 = self.create_step_card("2", "Run AI", "Segmentation in seconds")
        step3 = self.create_step_card("3", "Explore 3D", "Rotate and inspect")

        layout.addWidget(step1)
        layout.addWidget(step2)
        layout.addWidget(step3)
        return container

    def create_step_card(self, number, title, subtitle):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #f7fafc;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        number_label = QLabel(number)
        number_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        number_label.setStyleSheet("color: #667eea;")

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        title_label.setStyleSheet("color: #2d3748;")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Segoe UI", 7))
        subtitle_label.setStyleSheet("color: #718096;")

        layout.addWidget(number_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return card
    
    def create_info_card(self, icon, title, description):
        """Create a small info card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 6px;
                padding: 8px;
                border: 1px solid #edf2f7;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 18))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(30, 30)
        
        # Text container
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        title_label.setStyleSheet("color: #2d3748;")
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 7))
        desc_label.setStyleSheet("color: #718096;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_container)
        layout.addStretch()
        
        return card
    
    def create_title_section(self):
        """Create title and subtitle section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 6, 0, 6)
        
        title = QLabel("Select Diagnosis Module")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Choose the neural imaging analysis you need")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #718096;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return container

    def create_diagnosis_button(self, title, color):
        """Create a simple diagnosis button"""
        button = QPushButton(title)
        button.setFixedHeight(70)
        button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        button.setCursor(Qt.PointingHandCursor)
        
        # Define hover colors based on the base color
        hover_colors = {
            "#6366f1": "#818cf8",  # Lighter indigo
            "#ef4444": "#f87171",  # Lighter red
            "#10b981": "#34d399",  # Lighter green
            "#f59e0b": "#fbbf24",  # Lighter amber
            "#8b5cf6": "#a78bfa"   # Lighter purple
        }
        hover_color = hover_colors.get(color, color)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {hover_color};
                padding: 20px;
            }}
            QPushButton:pressed {{
                background: {color};
                padding: 22px 20px 18px 20px;
            }}
        """)
        
        button.clicked.connect(lambda: self.handle_diagnosis_click(title))
        
        return button

    def handle_logout(self):
        """Handle logout button click"""
        reply = self.show_message_box(
            "Logout",
            "Are you sure you want to logout?",
            "question"
        )
        
        if reply == QMessageBox.Yes:
            # Import here to avoid circular dependency
            from auth_window import AuthWindow
            self.auth_window = AuthWindow()
            self.auth_window.show()
            self.close()

    def handle_profile(self):
        """Handle profile button click"""
        self.show_message_box(
            "Profile",
            "Profile details will be available here soon.",
            "information"
        )

    def handle_settings(self):
        """Handle settings button click"""
        self.show_message_box(
            "Settings",
            "Settings will be available here soon.",
            "information"
        )

    def handle_diagnosis_click(self, diagnosis_type):
        """Handle diagnosis button click"""
        if diagnosis_type == "Visualize Medical Records":
            self.open_visualization_selector()
        elif diagnosis_type == "Add Patient":
            self.view.open_add_patient_form()
        elif diagnosis_type == "Send to Radiologist":
            self.view.open_send_case_form()
        elif diagnosis_type == "Upload Test":
            self.show_message_box(
                "Upload Test",
                "Upload test functionality will be implemented soon.\n\n"
                "This will allow you to:\n"
                "• Upload MRI/CT scan files\n"
                "• View test history\n"
                "• Manage test results",
                "information"
            )
        else:
            # Coming soon for other diagnosis types
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Coming Soon")
            msg_box.setText(
                f"{diagnosis_type} diagnosis module will be implemented here.\n\n"
                "This will include:\n"
                "• Medical image upload\n"
                "• AI-powered analysis\n"
                "• Detailed diagnosis report\n"
                "• Treatment recommendations"
            )
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStyleSheet(self.get_dialog_style())
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

    def open_visualization_selector(self):
        """Collect disease type and visualization mode before opening viewer."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Visualize Medical Records")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QLabel {
                color: #1f2937;
            }
            QLabel#DialogSubtitle {
                color: #6b7280;
            }
            QFrame#OptionsCard {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QLabel#FieldLabel {
                color: #374151;
                font-weight: 600;
                min-width: 120px;
            }
            QComboBox {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 34px 8px 10px;
                color: #111827;
                min-height: 24px;
                font-weight: 600;
            }
            QComboBox:hover {
                border: 1px solid #94a3b8;
            }
            QComboBox:focus {
                border: 1px solid #6366f1;
                background: #eef2ff;
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
            QComboBox QAbstractItemView {
                background: white;
                color: #111827;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                selection-background-color: #e0e7ff;
                selection-color: #1e293b;
                padding: 4px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 14px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Select visualization options")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))

        subtitle = QLabel("Choose disease type and view mode")
        subtitle.setObjectName("DialogSubtitle")
        subtitle.setFont(QFont("Segoe UI", 9))

        options_card = QFrame()
        options_card.setObjectName("OptionsCard")
        card_layout = QVBoxLayout(options_card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        disease_combo = QComboBox()
        disease_combo.setObjectName("DiseaseCombo")
        disease_combo.addItems([
            "Glioma Tumor",
            "Hemorrhagic Stroke",
            "Ischemic Stroke"
        ])

        mode_combo = QComboBox()
        mode_combo.setObjectName("ModeCombo")
        mode_combo.addItems(["2D", "3D"])

        disease_label = QLabel("Disease Type")
        disease_label.setObjectName("FieldLabel")
        mode_label = QLabel("Visualization")
        mode_label.setObjectName("FieldLabel")

        form.addRow(disease_label, disease_combo)
        form.addRow(mode_label, mode_combo)
        card_layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #111827;
                border: none;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #818cf8;
            }
        """)

        def handle_open():
            selected_disease = disease_combo.currentText()
            selected_mode = mode_combo.currentText()
            dialog.accept()
            self.launch_visualization(selected_disease, selected_mode)

        open_btn.clicked.connect(handle_open)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(open_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(options_card)
        layout.addLayout(buttons)

        dialog.exec()

    def launch_visualization(self, disease_type, mode):
        """Route visualization request to supported/placeholder flows."""
        if disease_type == "Glioma Tumor" and mode == "3D":
            self.show_segmentation_viewer()
            return

        self.show_message_box(
            "Coming Soon",
            f"{mode} visualization for {disease_type} is not available yet.\n\n"
            "Currently available: Glioma Tumor (3D).",
            "information"
        )

    def show_segmentation_viewer(self):
        if hasattr(self, "seg_viewer") and self.seg_viewer is not None:
            self.stacked.setCurrentIndex(1)
            return

        try:
            from segmentation_viewer import SegmentationViewer
            self.seg_viewer = SegmentationViewer()
            self.seg_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            for i in reversed(range(self.viewer_host_layout.count())):
                widget = self.viewer_host_layout.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)

            self.viewer_host_layout.addWidget(self.seg_viewer)
            self.stacked.setCurrentIndex(1)
        except ImportError as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Missing Dependencies")
            msg_box.setText(
                f"Required libraries are not installed:\n\n{str(e)}\n\n"
                "Please install: nibabel, scikit-image, pyvista, pyvistaqt"
            )
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setStyleSheet(self.get_dialog_style())
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"Failed to open segmentation viewer:\n\n{str(e)}")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setStyleSheet(self.get_dialog_style())
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

    def show_landing_page(self):
        self.stacked.setCurrentIndex(0)
