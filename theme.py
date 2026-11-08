"""
theme.py - Executive Luxury Theme for Jewelry Billing & Ledger.
Modern, sleek, and father-friendly with large high-contrast elements.
"""

COLOR_PRIMARY_DARK  = "#0B1E19"   # Deep Luxury Dark Emerald
COLOR_PRIMARY_MED   = "#12382C"   # Sidebar & Header Accent
COLOR_GOLD          = "#D4AF37"   # Pure Luxury Gold
COLOR_GOLD_LIGHT    = "#F3EBD8"   # Gold Tint
COLOR_GOLD_HOVER    = "#C59B27"   # Deep Gold
COLOR_BG            = "#F8F7F4"   # Soft warm luxury ivory background
COLOR_CARD          = "#FFFFFF"   # Crisp White Card
COLOR_BORDER        = "#E8E4DC"   # Soft border
COLOR_TEXT          = "#1A2521"   # Deep Charcoal
COLOR_TEXT_MUTED    = "#6E7A75"   # Subtitle grey
COLOR_SUCCESS       = "#16A34A"   # Vibrant Green for Paid/Jama
COLOR_DANGER        = "#DC2626"   # Vibrant Ruby Red for Udhar

GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    color: {COLOR_TEXT};
    background-color: {COLOR_BG};
}}

QLabel {{
    background-color: transparent;
}}

/* Top Header Bar */
QFrame#TopHeaderBar {{
    background-color: {COLOR_PRIMARY_DARK};
    border-bottom: 2px solid {COLOR_GOLD};
}}

QLabel#AppBrandTitle {{
    color: #FFFFFF;
    font-size: 21px;
    font-weight: bold;
    letter-spacing: 0.5px;
    background: transparent;
}}

QLabel#AppBrandTagline {{
    color: {COLOR_GOLD};
    font-size: 12px;
    font-weight: 500;
    background: transparent;
}}

/* Left Sidebar Navigation */
QFrame#LeftSidebar {{
    background-color: {COLOR_PRIMARY_MED};
    border-right: 1px solid #0E2920;
}}

QPushButton.NavButton {{
    background-color: transparent;
    color: #E2E8F0;
    border: none;
    border-left: 4px solid transparent;
    padding: 14px 18px;
    font-size: 15px;
    font-weight: 600;
    text-align: left;
    border-radius: 0px;
}}

QPushButton.NavButton:hover {{
    background-color: #194C3C;
    color: #FFFFFF;
}}

QPushButton.NavButton[active="true"] {{
    background-color: #1E5C49;
    color: {COLOR_GOLD};
    border-left: 4px solid {COLOR_GOLD};
    font-weight: bold;
}}

/* Executive Stat Cards (Dashboard) */
QFrame#StatCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 16px;
}}

QLabel#StatTitle {{
    font-size: 13px;
    color: {COLOR_TEXT_MUTED};
    font-weight: 600;
    background: transparent;
}}

QLabel#StatValue {{
    font-size: 26px;
    font-weight: bold;
    color: {COLOR_PRIMARY_DARK};
    background: transparent;
    margin-top: 4px;
}}

/* Clean Standard Card Frame */
QFrame#CardFrame {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
}}

QLabel#CardHeaderTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_PRIMARY_DARK};
    padding-bottom: 6px;
    border-bottom: 1.5px solid {COLOR_BORDER};
}}

/* Form Input Fields with Labels */
QLabel.FormLabel {{
    font-size: 13px;
    font-weight: 600;
    color: {COLOR_TEXT};
}}

QLineEdit, QComboBox, QDateEdit {{
    background-color: #FFFFFF;
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 14px;
    color: {COLOR_TEXT};
}}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 2px solid {COLOR_GOLD};
    background-color: #FFFDF9;
}}

/* Action Buttons */
QPushButton#PrimaryBtn {{
    background-color: {COLOR_PRIMARY_MED};
    color: #FFFFFF;
    border: 1px solid {COLOR_GOLD};
    border-radius: 8px;
    padding: 11px 22px;
    font-size: 15px;
    font-weight: bold;
}}

QPushButton#PrimaryBtn:hover {{
    background-color: {COLOR_PRIMARY_DARK};
    border-color: #FFFFFF;
}}

QPushButton#GoldActionBtn {{
    background-color: {COLOR_GOLD};
    color: {COLOR_PRIMARY_DARK};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: bold;
}}

QPushButton#GoldActionBtn:hover {{
    background-color: {COLOR_GOLD_HOVER};
    color: #FFFFFF;
}}

QPushButton#SecondaryBtn {{
    background-color: #EFECE6;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 500;
}}

QPushButton#SecondaryBtn:hover {{
    background-color: #E2DDD5;
}}

/* Language Toggle Pill */
QPushButton#LangPillBtn {{
    background-color: transparent;
    color: {COLOR_GOLD};
    border: 1.5px solid {COLOR_GOLD};
    border-radius: 20px;
    padding: 6px 18px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton#LangPillBtn:hover {{
    background-color: {COLOR_GOLD};
    color: {COLOR_PRIMARY_DARK};
}}

/* Modern Tables */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    gridline-color: #F1ECE4;
    font-size: 14px;
    selection-background-color: {COLOR_GOLD_LIGHT};
    selection-color: {COLOR_PRIMARY_DARK};
}}

QHeaderView::section {{
    background-color: #F6F3EC;
    color: {COLOR_PRIMARY_DARK};
    padding: 10px 12px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
}}

/* Live Digital Invoice Receipt Box (Right Side in Billing) */
QFrame#InvoiceSlipCard {{
    background-color: #FFFFFF;
    border: 2px solid {COLOR_GOLD};
    border-radius: 14px;
    padding: 18px;
}}

QFrame#GrandTotalPill {{
    background-color: {COLOR_PRIMARY_DARK};
    border: 1.5px solid {COLOR_GOLD};
    border-radius: 10px;
    padding: 12px;
}}

QFrame#GrandTotalPill QLabel {{
    background-color: transparent;
}}

/* Calendar & Date Picker Styling */
QCalendarWidget QWidget {{
    background-color: #FFFFFF;
    color: {COLOR_TEXT};
}}

QCalendarWidget QAbstractItemView:enabled {{
    background-color: #FFFFFF;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_GOLD};
    selection-color: {COLOR_PRIMARY_DARK};
}}

QLabel#GrandTotalNumber {{
    color: {COLOR_GOLD};
    font-size: 28px;
    font-weight: bold;
    background: transparent;
}}
"""
