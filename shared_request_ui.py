"""Shared UI helpers for doctor/radiologist request detail dialogs."""

from datetime import datetime
from PySide6.QtCore import Qt, QDate, QLocale
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QAbstractSpinBox, QDateEdit, QFrame, QGridLayout, QLabel, QVBoxLayout


REQUEST_DETAILS_DIALOG_STYLESHEET = """
    QDialog {
        background: #f8fafc;
    }
    QLabel {
        color: #1f2937;
    }
    QFrame#HeaderCard, QFrame#SectionCard {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
    }
    QLabel#SectionTitle {
        color: #111827;
        font-weight: 700;
    }
    QLabel#MutedText {
        color: #6b7280;
    }
    QLabel#Badge {
        border-radius: 999px;
        padding: 4px 10px;
        font-weight: 700;
    }
"""


DATE_FILTER_DATEEDIT_STYLESHEET = """
    QDateEdit {
        background: #ffffff;
        border: 1px solid #c7d2fe;
        border-radius: 8px;
        padding: 7px 10px;
        padding-right: 22px;
        color: #111827;
        font-weight: 600;
    }
    QDateEdit:read-only {
        background: #ffffff;
        color: #111827;
    }
    QDateEdit:hover {
        border: 1px solid #a5b4fc;
        background: #f8faff;
    }
    QDateEdit:focus {
        border: 1px solid #4f46e5;
        background: #eef2ff;
    }
    QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #c7d2fe;
        background: #eef2ff;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }
    QDateEdit::down-arrow {
        image: none;
        width: 0px;
        height: 0px;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #3730a3;
        margin-top: 2px;
    }
    QCalendarWidget QWidget {
        background: white;
        color: #111827;
    }
    QCalendarWidget QToolButton {
        color: #111827;
        background: #f3f4f6;
        border: none;
        border-radius: 4px;
    }
    QCalendarWidget QToolButton::menu-indicator {
        image: none;
        width: 0px;
        height: 0px;
    }
    QCalendarWidget QAbstractItemView {
        background: white;
        color: #111827;
        selection-background-color: #6366f1;
        selection-color: white;
    }
"""


DATE_FILTER_LABEL_STYLESHEET = """
    color: #3730a3;
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    border-radius: 6px;
    padding: 3px 8px;
"""


DATE_FILTER_CLEAR_BUTTON_STYLESHEET = """
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
"""


def create_standard_date_filter_edit():
    """Create a date edit configured for calendar-only filtering."""
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("dd/MM/yyyy")
    date_edit.setDate(QDate.currentDate())
    date_edit.setReadOnly(False)
    date_edit.lineEdit().setReadOnly(True)
    date_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)
    date_edit.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
    date_edit.setFixedWidth(128)
    date_edit.setStyleSheet(DATE_FILTER_DATEEDIT_STYLESHEET)
    date_edit.wheelEvent = lambda event: event.ignore()
    return date_edit


def create_date_filter_label(text):
    """Create a styled label for date-filter controls."""
    label = QLabel(text)
    label.setFont(QFont("Segoe UI", 8, QFont.Bold))
    label.setStyleSheet(DATE_FILTER_LABEL_STYLESHEET)
    return label


def clean_value(value):
    """Return a human-readable placeholder for empty values."""
    if value is None:
        return "N/A"
    text = str(value).strip()
    return text if text else "N/A"


def make_badge(text, background, foreground, border_color=None):
    """Create a pill-style status/metadata badge label."""
    badge = QLabel(clean_value(text))
    badge.setObjectName("Badge")
    badge.setStyleSheet(
        f"background: {background}; color: {foreground}; border: 1px solid {border_color or background};"
    )
    return badge


def make_section_card(section_title, rows):
    """Create a standard section card with two-column rows."""
    card = QFrame()
    card.setObjectName("SectionCard")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 14, 16, 14)
    card_layout.setSpacing(10)

    section_label = QLabel(section_title)
    section_label.setObjectName("SectionTitle")
    section_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
    card_layout.addWidget(section_label)

    grid = QGridLayout()
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(10)
    grid.setContentsMargins(0, 0, 0, 0)

    for row_index, (label_text, value_widget) in enumerate(rows):
        label = QLabel(label_text)
        label.setObjectName("MutedText")
        label.setFont(QFont("Segoe UI", 9))
        label.setMinimumWidth(130)
        label.setWordWrap(True)

        grid.addWidget(label, row_index, 0, alignment=Qt.AlignTop)
        grid.addWidget(value_widget, row_index, 1)

    card_layout.addLayout(grid)
    return card


def format_request_datetime(date_value):
    """Format date as DD-MM-YYYY HH:MM.
    
    Handles ISO format, fallback string parsing, and missing values.
    """
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


def create_grouped_request_card(patient_id, requests, card_creator_callback, expanded_groups_set):
    """Factory function to create grouped request cards for both doctor and radiologist views.
    
    Parameters:
    - patient_id: The patient ID for grouping
    - requests: List of request dicts to display
    - card_creator_callback: Function to create individual request card (takes request dict, returns QWidget)
    - expanded_groups_set: Set tracking which groups are currently expanded
    
    Returns: QWidget container with grouped and collapsible requests
    """
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame)
    
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
    latest_date = format_request_datetime(latest_request.get('created_at', 'N/A'))

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
        request_card = card_creator_callback(request)
        content_layout.addWidget(request_card)
    
    patient_group_key = str(patient_id)
    is_expanded = patient_group_key in expanded_groups_set
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
            expanded_groups_set.add(patient_group_key)
        else:
            expanded_groups_set.discard(patient_group_key)
    
    expand_btn.clicked.connect(toggle_expand)
    
    return container


