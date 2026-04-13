"""Shared UI helpers for doctor/radiologist request detail dialogs."""

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
