"""
build_all.py - 1-Click Complete System Builder.
Run this once to generate all software modules and immediately start the app.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILES = {
    # ------------------- 1. TRANSLATIONS -------------------
    "translations.py": '''"""
translations.py - Complete Bilingual Dictionary (Gujarati & English).
"""

TRANSLATIONS = {
    "gu": {
        "app_title": "જ્વેલરી બિલિંગ અને ખાતાવહી",
        "tagline": "સોના-ચાંદીના દાગીનાનું બિલિંગ સોફ્ટવેર",
        "btn_switch_lang": "English માં જુઓ",
        
        "nav_new_bill": "૧. નવું બિલ બનાવો (New Bill)",
        "nav_customers": "૨. ગ્રાહકોની યાદી (Customers)",
        "nav_ledger": "૩. જમા / ઉધાર ખાતાવહી (Ledger)",
        "nav_backup": "૪. પેન ડ્રાઈવમાં બેકઅપ લો (Backup)",
        
        "lbl_cust_name": "ગ્રાહકનું નામ (શેઠશ્રી):",
        "lbl_cust_mobile": "મોબાઇલ નંબર:",
        "lbl_cust_address": "સરનામું:",
        "lbl_cust_gstin": "હસ્તે / GSTIN:",
        "lbl_search": "શોધો (મોબાઇલ અથવા નામ):",
        "btn_add_customer": "+ નવો ગ્રાહક ઉમેરો",
        "btn_save": "સેવ કરો (Save)",
        "btn_cancel": "રદ કરો (Cancel)",
        
        "lbl_bill_no": "બીલ નં.:",
        "lbl_book_no": "બુક નં.:",
        "lbl_bill_date": "તારીખ:",
        "lbl_item_desc": "વિગત (વસ્તુ + HUID):",
        "lbl_hsn": "H.S.N.:",
        "lbl_weight": "વજન (ગ્રામ):",
        "lbl_rate": "ભાવ (Rate):",
        "lbl_amount": "રકમ (Amount):",
        "btn_add_item": "+ વસ્તુ ઉમેરો",
        "btn_delete_item": "કાઢી નાખો",
        "lbl_subtotal": "કુલ રકમ (Subtotal):",
        "lbl_cgst": "C-GST (૧.૫%):",
        "lbl_sgst": "S-GST (૧.૫%):",
        "lbl_grand_total": "કુલ બીલ રકમ (Grand Total):",
        "lbl_paid_now": "રોકડા જમા આપ્યા (Paid):",
        "lbl_balance_due": "બાકી ઉધાર રકમ (Udhar Balance):",
        "btn_save_print": "બિલ સેવ અને પ્રિન્ટ કરો (Save & Print)",
        
        "lbl_total_udhar": "કુલ બાકી ઉધાર:",
        "lbl_jama": "જમા (Credit)",
        "lbl_udhar": "ઉધાર (Debit)",
        "btn_add_payment": "+ જમા રકમ નોંધો (Record Payment)",
        
        "msg_saved": "સફળતાપૂર્વક સેવ થઈ ગયું!",
        "msg_backup_ok": "પેન ડ્રાઈવમાં બેકઅપ સફળતાપૂર્વક લેવાઈ ગયું છે!",
    },
    
    "en": {
        "app_title": "Jewelry Billing & Ledger",
        "tagline": "Jewelry Shop Billing & Account Software",
        "btn_switch_lang": "ગુજરાતી માં જુઓ",
        
        "nav_new_bill": "1. Create New Bill",
        "nav_customers": "2. Customer Directory",
        "nav_ledger": "3. Credit / Debit Ledger",
        "nav_backup": "4. Backup to Pen Drive",
        
        "lbl_cust_name": "Customer Name:",
        "lbl_cust_mobile": "Mobile Number:",
        "lbl_cust_address": "Address:",
        "lbl_cust_gstin": "Through / GSTIN:",
        "lbl_search": "Search (Mobile or Name):",
        "btn_add_customer": "+ Add Customer",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        
        "lbl_bill_no": "Bill No.:",
        "lbl_book_no": "Book No.:",
        "lbl_bill_date": "Date:",
        "lbl_item_desc": "Description (Item + HUID):",
        "lbl_hsn": "H.S.N.:",
        "lbl_weight": "Weight (Grams):",
        "lbl_rate": "Rate:",
        "lbl_amount": "Amount:",
        "btn_add_item": "+ Add Item",
        "btn_delete_item": "Remove",
        "lbl_subtotal": "Subtotal:",
        "lbl_cgst": "C-GST (1.5%):",
        "lbl_sgst": "S-GST (1.5%):",
        "lbl_grand_total": "Grand Total:",
        "lbl_paid_now": "Paid Now:",
        "lbl_balance_due": "Balance Due (Udhar):",
        "btn_save_print": "Save & Print Bill",
        
        "lbl_total_udhar": "Total Outstanding Balance:",
        "lbl_jama": "Credit (Jama)",
        "lbl_udhar": "Debit (Udhar)",
        "btn_add_payment": "+ Record Payment",
        
        "msg_saved": "Saved successfully!",
        "msg_backup_ok": "Backup completed successfully!",
    }
}

active_lang = "gu"

def t(key: str) -> str:
    return TRANSLATIONS.get(active_lang, {}).get(key, key)

def toggle_language() -> str:
    global active_lang
    active_lang = "en" if active_lang == "gu" else "gu"
    return active_lang
''',

    # ------------------- 2. DATABASE -------------------
    "database.py": '''"""
database.py - SQLite Database Engine.
Calculates balances dynamically. Stored in integer paise.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jewelry_shop.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_gu TEXT NOT NULL,
            name_en TEXT DEFAULT '',
            mobile TEXT NOT NULL,
            address TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no INTEGER NOT NULL,
            book_no INTEGER DEFAULT 1,
            bill_date TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            subtotal_paise INTEGER NOT NULL,
            cgst_paise INTEGER NOT NULL,
            sgst_paise INTEGER NOT NULL,
            grand_total_paise INTEGER NOT NULL,
            paid_paise INTEGER NOT NULL,
            balance_paise INTEGER NOT NULL,
            payment_mode TEXT DEFAULT 'CASH',
            status TEXT DEFAULT 'ACTIVE',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            hsn_code TEXT DEFAULT '7113',
            weight_mg INTEGER NOT NULL,
            rate_paise INTEGER NOT NULL,
            amount_paise INTEGER NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            entry_type TEXT NOT NULL CHECK(entry_type IN ('UDHAR', 'JAMA')),
            amount_paise INTEGER NOT NULL,
            bill_id INTEGER,
            payment_mode TEXT DEFAULT 'CASH',
            remark TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        );
    """)

    conn.commit()
    conn.close()

def add_customer(name_gu: str, mobile: str, address: str = "", name_en: str = "", gstin: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO customers (name_gu, name_en, mobile, address, gstin)
        VALUES (?, ?, ?, ?, ?);
    """, (name_gu.strip(), name_en.strip(), mobile.strip(), address.strip(), gstin.strip()))
    cust_id = c.lastrowid
    conn.commit()
    conn.close()
    return cust_id

def search_customers(keyword: str) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    q = f"%{keyword.strip()}%"
    c.execute("""
        SELECT * FROM customers 
        WHERE mobile LIKE ? OR name_gu LIKE ? OR name_en LIKE ?
        ORDER BY id DESC LIMIT 50;
    """, (q, q, q))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_customer_balance(customer_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(amount_paise), 0) FROM ledger WHERE customer_id = ? AND entry_type = 'UDHAR';", (customer_id,))
    udhar = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount_paise), 0) FROM ledger WHERE customer_id = ? AND entry_type = 'JAMA';", (customer_id,))
    jama = c.fetchone()[0]
    conn.close()
    return udhar - jama

def add_payment(customer_id: int, amount_paise: int, payment_mode: str = "CASH", remark: str = "", date_str: str = None) -> int:
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, payment_mode, remark)
        VALUES (?, ?, 'JAMA', ?, ?, ?);
    """, (customer_id, date_str, amount_paise, payment_mode, remark))
    lid = c.lastrowid
    conn.commit()
    conn.close()
    return lid

def get_customer_ledger(customer_id: int) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT l.*, b.bill_no 
        FROM ledger l
        LEFT JOIN bills b ON l.bill_id = b.id
        WHERE l.customer_id = ?
        ORDER BY l.entry_date ASC, l.id ASC;
    """, (customer_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_next_bill_number() -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COALESCE(MAX(bill_no), 0) + 1 FROM bills;")
    next_no = c.fetchone()[0]
    conn.close()
    return next_no

def create_bill(customer_id: int, bill_date: str, items: List[Dict], paid_paise: int, payment_mode: str = "CASH") -> int:
    conn = get_connection()
    c = conn.cursor()
    
    subtotal_paise = sum(item["amount_paise"] for item in items)
    cgst_paise = round(subtotal_paise * 0.015)
    sgst_paise = round(subtotal_paise * 0.015)
    grand_total_paise = subtotal_paise + cgst_paise + sgst_paise
    balance_paise = max(0, grand_total_paise - paid_paise)
    bill_no = get_next_bill_number()

    c.execute("""
        INSERT INTO bills (
            bill_no, bill_date, customer_id, subtotal_paise,
            cgst_paise, sgst_paise, grand_total_paise, paid_paise,
            balance_paise, payment_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (bill_no, bill_date, customer_id, subtotal_paise, cgst_paise, sgst_paise, grand_total_paise, paid_paise, balance_paise, payment_mode))
    
    bill_id = c.lastrowid

    for item in items:
        c.execute("""
            INSERT INTO bill_items (bill_id, description, hsn_code, weight_mg, rate_paise, amount_paise)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (bill_id, item["description"], item.get("hsn_code", "7113"), item["weight_mg"], item["rate_paise"], item["amount_paise"]))

    if paid_paise > 0:
        c.execute("""
            INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark)
            VALUES (?, ?, 'JAMA', ?, ?, ?, ?);
        """, (customer_id, bill_date, paid_paise, bill_id, payment_mode, f"બિલ નં. {bill_no} પેમેન્ટ"))

    if balance_paise > 0:
        c.execute("""
            INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark)
            VALUES (?, ?, 'UDHAR', ?, ?, 'CREDIT', ?);
        """, (customer_id, bill_date, balance_paise, bill_id, f"બિલ નં. {bill_no} બાકી ઉધાર"))

    conn.commit()
    conn.close()
    return bill_id

def backup_database(destination_folder: str) -> str:
    os.makedirs(destination_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(destination_folder, f"jewelry_shop_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_file)
    return backup_file
''',

    # ------------------- 3. THEME -------------------
    "theme.py": '''"""
theme.py - Professional Jewelry Theme.
"""

COLOR_PRIMARY   = "#092E23"   # Royal Forest Deep Emerald
COLOR_GOLD      = "#C5A880"   # Champagne Gold
COLOR_BG        = "#F9F8F5"   # Warm Pearl Ivory
COLOR_CARD      = "#FFFFFF"
COLOR_BORDER    = "#E3DDD3"
COLOR_TEXT      = "#1A2621"

GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    color: {COLOR_TEXT};
    background-color: {COLOR_BG};
}}

QFrame#HeaderBar {{
    background-color: {COLOR_PRIMARY};
    border-bottom: 2px solid {COLOR_GOLD};
}}

QLabel#HeaderBrandTitle {{
    color: #FFFFFF;
    font-size: 22px;
    font-weight: bold;
    background: transparent;
}}

QLabel#HeaderTagline {{
    color: {COLOR_GOLD};
    font-size: 13px;
    background: transparent;
}}

QPushButton.BigHomeButton {{
    background-color: {COLOR_CARD};
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 22px;
    font-size: 18px;
    font-weight: bold;
    color: {COLOR_PRIMARY};
    text-align: left;
}}

QPushButton.BigHomeButton:hover {{
    background-color: #F3EFE7;
    border-color: {COLOR_GOLD};
}}

QPushButton#PrimaryBtn {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: 1px solid {COLOR_GOLD};
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 15px;
    font-weight: bold;
}}

QPushButton#PrimaryBtn:hover {{
    background-color: #134B3B;
}}

QPushButton#SecondaryBtn {{
    background-color: #EDE8E1;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
}}

QPushButton#SecondaryBtn:hover {{
    background-color: #DFD8CD;
}}

QLineEdit, QComboBox, QDateEdit {{
    background-color: #FFFFFF;
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 2px solid {COLOR_GOLD};
}}

QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #F0ECE6;
    font-size: 14px;
}}

QHeaderView::section {{
    background-color: #F3EFEA;
    color: {COLOR_PRIMARY};
    padding: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
}}
"""
''',

    # ------------------- 4. CUSTOMERS VIEW -------------------
    "customers_view.py": '''"""
customers_view.py - Customer Directory & Add Dialog.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from translations import t
from database import search_customers, add_customer, get_customer_balance

class AddCustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("btn_add_customer"))
        self.resize(480, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        form = QFormLayout()

        self.txt_name_gu = QLineEdit()
        self.txt_name_gu.setPlaceholderText("દા.ત. નટવરલાલ સોની")
        form.addRow(t("lbl_cust_name"), self.txt_name_gu)

        self.txt_mobile = QLineEdit()
        self.txt_mobile.setPlaceholderText("૧૦ આંકડાનો મોબાઇલ નંબર")
        form.addRow(t("lbl_cust_mobile"), self.txt_mobile)

        self.txt_address = QLineEdit()
        self.txt_address.setPlaceholderText("ગામ / સરનામું")
        form.addRow(t("lbl_cust_address"), self.txt_address)

        self.txt_name_en = QLineEdit()
        self.txt_name_en.setPlaceholderText("e.g. Natwarlal Soni")
        form.addRow("Name in English (વૈકલ્પિક):", self.txt_name_en)

        self.txt_gstin = QLineEdit()
        self.txt_gstin.setPlaceholderText("GSTIN (જો હોય તો)")
        form.addRow(t("lbl_cust_gstin"), self.txt_gstin)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton(t("btn_cancel"))
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton(t("btn_save"))
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self.save)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def save(self):
        name = self.txt_name_gu.text().strip()
        mobile = self.txt_mobile.text().strip()
        if not name:
            QMessageBox.warning(self, "ધ્યાન આપો", "કૃપા કરીને ગ્રાહકનું નામ દાખલ કરો.")
            return
        if not mobile or len(mobile) < 10:
            QMessageBox.warning(self, "ધ્યાન આપો", "કૃપા કરીને સાચો ૧૦ આંકડાનો મોબાઇલ નંબર દાખલ કરો.")
            return

        add_customer(
            name_gu=name,
            mobile=mobile,
            address=self.txt_address.text().strip(),
            name_en=self.txt_name_en.text().strip(),
            gstin=self.txt_gstin.text().strip()
        )
        self.accept()

class CustomersView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        top = QHBoxLayout()
        btn_back = QPushButton("⬅ પાછા જાઓ (Back)")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(self.on_back_callback)
        top.addWidget(btn_back)

        top.addSpacing(16)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search"))
        self.txt_search.textChanged.connect(self.load_customers)
        top.addWidget(self.txt_search, stretch=2)

        top.addSpacing(16)
        self.btn_add = QPushButton(t("btn_add_customer"))
        self.btn_add.setObjectName("PrimaryBtn")
        self.btn_add.clicked.connect(self.open_add_dialog)
        top.addWidget(self.btn_add)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "ગ્રાહકનું નામ (Name)", "મોબાઇલ (Mobile)", "સરનામું (Address)", "બાકી ઉધાર (Udhar)"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)

    def load_customers(self, query=""):
        self.table.setRowCount(0)
        for row_idx, c in enumerate(search_customers(query)):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(c["id"])))
            
            name = c["name_gu"]
            if c["name_en"]:
                name += f" ({c['name_en']})"
            self.table.setItem(row_idx, 1, QTableWidgetItem(name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(c["mobile"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(c["address"] or "-"))

            bal_paise = get_customer_balance(c["id"])
            bal_rs = bal_paise / 100.0
            bal_text = f"₹ {bal_rs:,.2f} ઉધાર" if bal_paise > 0 else ("₹ 0.00" if bal_paise == 0 else f"₹ {abs(bal_rs):,.2f} જમા")
            
            item = QTableWidgetItem(bal_text)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(Qt.red if bal_paise > 0 else Qt.darkGreen)
            self.table.setItem(row_idx, 4, item)

    def open_add_dialog(self):
        if AddCustomerDialog(self).exec():
            self.load_customers(self.txt_search.text())
''',

    # ------------------- 5. LEDGER VIEW -------------------
    "ledger_view.py": '''"""
ledger_view.py - Complete Jama/Udhar ledger screen for any customer.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from translations import t
from database import search_customers, get_customer_ledger, get_customer_balance, add_payment

class AddPaymentDialog(QDialog):
    def __init__(self, customer_id, customer_name, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setWindowTitle(f"જમા રકમ નોંધો - {customer_name}")
        self.resize(400, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        form = QFormLayout()

        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("દા.ત. 5000")
        form.addRow("જમા રકમ (Amount in Rs):", self.txt_amount)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["CASH (રોકડ)", "UPI (GPay / PhonePe)", "CHEQUE (ચેક)", "BANK TRANSFER"])
        form.addRow("ચૂકવણીનો પ્રકાર (Mode):", self.cmb_mode)

        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText("દા.ત. પેમેન્ટ મળ્યું")
        form.addRow("નોંધ (Remark):", self.txt_remark)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton(t("btn_cancel"))
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton(t("btn_save"))
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self.save)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def save(self):
        try:
            amt = float(self.txt_amount.text().strip())
            if amt <= 0:
                raise ValueError
        except:
            QMessageBox.warning(self, "ધ્યાન આપો", "કૃપા કરીને સાચી રકમ દાખલ કરો.")
            return

        paise = int(round(amt * 100))
        mode = self.cmb_mode.currentText().split()[0]
        add_payment(self.customer_id, paise, payment_mode=mode, remark=self.txt_remark.text().strip())
        self.accept()

class LedgerView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.current_customer = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        top = QHBoxLayout()
        btn_back = QPushButton("⬅ પાછા જાઓ (Back)")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(self.on_back_callback)
        top.addWidget(btn_back)

        top.addSpacing(16)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 ગ્રાહક શોધો (મોબાઇલ અથવા નામ)...")
        self.txt_search.textChanged.connect(self.on_search)
        top.addWidget(self.txt_search, stretch=2)

        self.btn_pay = QPushButton(t("btn_add_payment"))
        self.btn_pay.setObjectName("PrimaryBtn")
        self.btn_pay.setEnabled(False)
        self.btn_pay.clicked.connect(self.open_payment_dialog)
        top.addWidget(self.btn_pay)
        layout.addLayout(top)

        # Customer Header details & Balance Banner
        self.lbl_cust_info = QLabel("કૃપા કરીને ઉપરથી ગ્રાહક પસંદ કરો.")
        self.lbl_cust_info.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px;")
        layout.addWidget(self.lbl_cust_info)

        # Ledger History Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "તારીખ (Date)", "પ્રકાર (Type)", "વિગત / બિલ નં.", "ઉધાર (Debit)", "જમા (Credit)", "ચૂકવણી મોડ"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

    def on_search(self, text):
        results = search_customers(text)
        if results:
            self.load_customer_ledger(results[0])

    def load_customer_ledger(self, customer):
        self.current_customer = customer
        self.btn_pay.setEnabled(True)

        bal_paise = get_customer_balance(customer["id"])
        bal_rs = bal_paise / 100.0
        color = "red" if bal_paise > 0 else "green"
        status = f"₹ {bal_rs:,.2f} બાકી ઉધાર" if bal_paise > 0 else "₹ 0.00 (બધો હિસાબ ક્લીયર)"

        self.lbl_cust_info.setText(
            f"ગ્રાહક: {customer['name_gu']} ({customer['mobile']})   |   "
            f"<span style='color:{color}; font-size:18px;'>કુલ બાકી: {status}</span>"
        )

        entries = get_customer_ledger(customer["id"])
        self.table.setRowCount(0)
        for row_idx, e in enumerate(entries):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(e["entry_date"]))
            
            # Type
            t_item = QTableWidgetItem(e["entry_type"])
            t_item.setForeground(Qt.red if e["entry_type"] == "UDHAR" else Qt.darkGreen)
            self.table.setItem(row_idx, 1, t_item)

            desc = e["remark"]
            if e.get("bill_no"):
                desc = f"બિલ નં. {e['bill_no']} - " + desc
            self.table.setItem(row_idx, 2, QTableWidgetItem(desc))

            rs = e["amount_paise"] / 100.0
            if e["entry_type"] == "UDHAR":
                self.table.setItem(row_idx, 3, QTableWidgetItem(f"₹ {rs:,.2f}"))
                self.table.setItem(row_idx, 4, QTableWidgetItem("-"))
            else:
                self.table.setItem(row_idx, 3, QTableWidgetItem("-"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(f"₹ {rs:,.2f}"))

            self.table.setItem(row_idx, 5, QTableWidgetItem(e["payment_mode"]))

    def open_payment_dialog(self):
        if self.current_customer:
            dlg = AddPaymentDialog(self.current_customer["id"], self.current_customer["name_gu"], self)
            if dlg.exec():
                self.load_customer_ledger(self.current_customer)
''',

    # ------------------- 6. BILLING VIEW -------------------
    "billing_view.py": '''"""
billing_view.py - New Bill Creation Screen.
Matches your exact photo: Customer mobile, HSN 7113, Weight, Rate, 1.5% CGST + 1.5% SGST.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

from translations import t
from database import search_customers, add_customer, create_bill, get_next_bill_number

class BillingView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.selected_customer = None
        self.init_ui()
        self.reset_form()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # 1. Top Bar
        top = QHBoxLayout()
        btn_back = QPushButton("⬅ પાછા જાઓ (Back)")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(self.on_back_callback)
        top.addWidget(btn_back)

        top.addStretch()
        self.lbl_bill_info = QLabel("બીલ નં: 1")
        self.lbl_bill_info.setStyleSheet("font-size: 18px; font-weight: bold;")
        top.addWidget(self.lbl_bill_info)
        layout.addLayout(top)

        # 2. Customer Section Frame
        cust_frame = QFrame()
        cust_frame.setObjectName("CardFrame")
        cust_layout = QHBoxLayout(cust_frame)
        cust_layout.setContentsMargins(16, 12, 16, 12)

        self.txt_cust_search = QLineEdit()
        self.txt_cust_search.setPlaceholderText("🔍 ગ્રાહક શોધો (મોબાઇલ અથવા નામ)...")
        self.txt_cust_search.textChanged.connect(self.on_customer_search)
        cust_layout.addWidget(self.txt_cust_search, stretch=2)

        self.txt_cust_phone = QLineEdit()
        self.txt_cust_phone.setPlaceholderText("મોબાઇલ નંબર (Mobile No.)")
        cust_layout.addWidget(self.txt_cust_phone, stretch=1)

        self.txt_cust_address = QLineEdit()
        self.txt_cust_address.setPlaceholderText("સરનામું (Address)")
        cust_layout.addWidget(self.txt_cust_address, stretch=2)

        layout.addWidget(cust_frame)

        # 3. Item Entry Row (Fast Typing with Enter)
        item_bar = QHBoxLayout()
        self.txt_item_desc = QLineEdit()
        self.txt_item_desc.setPlaceholderText("વિગત (દા.ત. લકી HUID સાથે)")
        item_bar.addWidget(self.txt_item_desc, stretch=3)

        self.txt_hsn = QLineEdit("7113")
        self.txt_hsn.setPlaceholderText("HSN")
        self.txt_hsn.setMaximumWidth(80)
        item_bar.addWidget(self.txt_hsn)

        self.txt_weight = QLineEdit()
        self.txt_weight.setPlaceholderText("વજન (ગ્રા. દા.ત. 3.040)")
        self.txt_weight.textChanged.connect(self.calculate_row_amount)
        item_bar.addWidget(self.txt_weight, stretch=1)

        self.txt_rate = QLineEdit()
        self.txt_rate.setPlaceholderText("ભાવ (દા.ત. 67250)")
        self.txt_rate.textChanged.connect(self.calculate_row_amount)
        item_bar.addWidget(self.txt_rate, stretch=1)

        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("રકમ (Amount)")
        self.txt_amount.setReadOnly(True)
        item_bar.addWidget(self.txt_amount, stretch=1)

        btn_add_item = QPushButton("+ ઉમેરો (Add)")
        btn_add_item.setObjectName("PrimaryBtn")
        btn_add_item.clicked.connect(self.add_item_to_table)
        item_bar.addWidget(btn_add_item)

        layout.addLayout(item_bar)

        # 4. Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "વિગત (Description)", "H.S.N.", "વજન (Weight)", "ભાવ (Rate)", "રકમ (Amount)", "ક્રિયા"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # 5. Calculation Summary & Action Bar
        summary_frame = QFrame()
        summary_frame.setObjectName("CardFrame")
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(16, 12, 16, 12)

        self.lbl_totals = QLabel("Subtotal: ₹0.00 | CGST 1.5%: ₹0.00 | SGST 1.5%: ₹0.00 | Grand Total: ₹0.00")
        self.lbl_totals.setStyleSheet("font-size: 15px; font-weight: bold;")
        summary_layout.addWidget(self.lbl_totals, stretch=2)

        self.txt_paid = QLineEdit()
        self.txt_paid.setPlaceholderText("રોકડા ચૂકવ્યા (Paid Now)")
        self.txt_paid.textChanged.connect(self.update_totals_display)
        summary_layout.addWidget(self.txt_paid, stretch=1)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["CASH (રોકડ)", "CREDIT (ઉધાર)", "UPI (ઓનલાઇન)"])
        summary_layout.addWidget(self.cmb_mode)

        btn_save = QPushButton("💾 બિલ સેવ કરો (Save Bill)")
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self.save_bill)
        summary_layout.addWidget(btn_save)

        layout.addWidget(summary_frame)

    def reset_form(self):
        self.selected_customer = None
        self.txt_cust_search.clear()
        self.txt_cust_phone.clear()
        self.txt_cust_address.clear()
        self.txt_item_desc.clear()
        self.txt_weight.clear()
        self.txt_rate.clear()
        self.txt_amount.clear()
        self.txt_paid.clear()
        self.table.setRowCount(0)
        self.items_data = []
        self.lbl_bill_info.setText(f"બીલ નં: {get_next_bill_number()}")
        self.update_totals_display()

    def on_customer_search(self, text):
        results = search_customers(text)
        if results:
            c = results[0]
            self.selected_customer = c
            self.txt_cust_phone.setText(c["mobile"])
            self.txt_cust_address.setText(c["address"])

    def calculate_row_amount(self):
        try:
            wt = float(self.txt_weight.text() or 0)
            rate = float(self.txt_rate.text() or 0)
            # Jewelry rate is per 10g or per 1g
            amt = round(wt * (rate / 10.0), 2) if rate > 10000 else round(wt * rate, 2)
            self.txt_amount.setText(str(amt))
        except:
            self.txt_amount.clear()

    def add_item_to_table(self):
        desc = self.txt_item_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "ધ્યાન આપો", "કૃપા કરીને વસ્તુની વિગત દાખલ કરો.")
            return

        try:
            wt = float(self.txt_weight.text())
            rate = float(self.txt_rate.text())
            amt = float(self.txt_amount.text())
        except:
            QMessageBox.warning(self, "ધ્યાન આપો", "કૃપા કરીને સાચું વજન અને ભાવ દાખલ કરો.")
            return

        item_dict = {
            "description": desc,
            "hsn_code": self.txt_hsn.text().strip() or "7113",
            "weight_mg": int(round(wt * 1000)),
            "rate_paise": int(round(rate * 100)),
            "amount_paise": int(round(amt * 100))
        }
        self.items_data.append(item_dict)

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(desc))
        self.table.setItem(row, 1, QTableWidgetItem(item_dict["hsn_code"]))
        self.table.setItem(row, 2, QTableWidgetItem(f"{wt:.3f} g"))
        self.table.setItem(row, 3, QTableWidgetItem(f"₹ {rate:,.2f}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"₹ {amt:,.2f}"))

        btn_del = QPushButton("❌")
        btn_del.setMaximumWidth(40)
        btn_del.clicked.connect(lambda _, r=row: self.remove_item(r))
        self.table.setCellWidget(row, 5, btn_del)

        self.txt_item_desc.clear()
        self.txt_weight.clear()
        self.txt_amount.clear()
        self.txt_item_desc.setFocus()
        self.update_totals_display()

    def remove_item(self, row):
        if row < len(self.items_data):
            self.items_data.pop(row)
            self.table.removeRow(row)
            self.update_totals_display()

    def update_totals_display(self):
        subtotal = sum(i["amount_paise"] for i in self.items_data) / 100.0
        cgst = round(subtotal * 0.015, 2)
        sgst = round(subtotal * 0.015, 2)
        grand = round(subtotal + cgst + sgst)
        
        try:
            paid = float(self.txt_paid.text() or 0)
        except:
            paid = 0.0

        due = max(0.0, grand - paid)
        self.lbl_totals.setText(
            f"કુલ રકમ: ₹{subtotal:,.2f}  |  "
            f"CGST(1.5%): ₹{cgst:,.2f}  |  "
            f"SGST(1.5%): ₹{sgst:,.2f}  |  "
            f"<span style='color:green;'>ગ્રાન્ડ ટોટલ: ₹{grand:,.2f}</span>  |  "
            f"<span style='color:red;'>બાકી ઉધાર: ₹{due:,.2f}</span>"
        )

    def save_bill(self):
        if not self.items_data:
            QMessageBox.warning(self, "ધ્યાન આપો", "બિલમાં ઓછામાં ઓછી ૧ વસ્તુ ઉમેરો.")
            return

        cust_name = self.txt_cust_search.text().strip()
        cust_phone = self.txt_cust_phone.text().strip()

        if not cust_phone or len(cust_phone) < 10:
            QMessageBox.warning(self, "ધ્યાન આપો", "કૃપા કરીને ગ્રાહકનો ૧૦ આંકડાનો મોબાઇલ નંબર દાખલ કરો.")
            return

        if not self.selected_customer:
            cust_id = add_customer(name_gu=cust_name or "ગ્રાહક", mobile=cust_phone, address=self.txt_cust_address.text().strip())
        else:
            cust_id = self.selected_customer["id"]

        try:
            paid_rs = float(self.txt_paid.text() or 0)
        except:
            paid_rs = 0.0

        paid_paise = int(round(paid_rs * 100))
        mode = self.cmb_mode.currentText().split()[0]
        today = datetime.now().strftime("%Y-%m-%d")

        bill_id = create_bill(
            customer_id=cust_id,
            bill_date=today,
            items=self.items_data,
            paid_paise=paid_paise,
            payment_mode=mode
        )

        QMessageBox.information(self, "સફળતા", f"બિલ સફળતાપૂર્વક બની ગયું! (બિલ ID: {bill_id})")
        self.reset_form()
''',

    # ------------------- 7. MAIN WINDOW -------------------
    "main.py": '''"""
main.py - Main Window with Multi-Screen Flow.
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QFrame, QFileDialog, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt

from translations import t, toggle_language
from database import init_db, backup_database
from theme import GLOBAL_STYLESHEET
from customers_view import CustomersView
from ledger_view import LedgerView
from billing_view import BillingView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jewelry Billing & Ledger - બિલિંગ અને ખાતાવહી")
        self.resize(1120, 740)
        self.setMinimumSize(950, 680)
        
        init_db()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Header
        header = QFrame()
        header.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)

        title_box = QVBoxLayout()
        self.lbl_title = QLabel(t("app_title"))
        self.lbl_title.setObjectName("HeaderBrandTitle")
        self.lbl_tagline = QLabel(t("tagline"))
        self.lbl_tagline.setObjectName("HeaderTagline")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_tagline)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.btn_lang = QPushButton(t("btn_switch_lang"))
        self.btn_lang.setObjectName("SecondaryBtn")
        self.btn_lang.setCursor(Qt.PointingHandCursor)
        self.btn_lang.clicked.connect(self.on_switch_language)
        header_layout.addWidget(self.btn_lang)

        main_layout.addWidget(header)

        # 2. Multi-Screen Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Screen 0: Home Screen (4 Big Buttons)
        self.home_widget = QWidget()
        home_layout = QVBoxLayout(self.home_widget)
        home_layout.setContentsMargins(40, 30, 40, 40)
        home_layout.setSpacing(18)

        self.btn_new_bill = QPushButton(t("nav_new_bill"))
        self.btn_new_bill.setProperty("class", "BigHomeButton")
        self.btn_new_bill.setCursor(Qt.PointingHandCursor)
        self.btn_new_bill.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        self.btn_customers = QPushButton(t("nav_customers"))
        self.btn_customers.setProperty("class", "BigHomeButton")
        self.btn_customers.setCursor(Qt.PointingHandCursor)
        self.btn_customers.clicked.connect(self.open_customers)

        self.btn_ledger = QPushButton(t("nav_ledger"))
        self.btn_ledger.setProperty("class", "BigHomeButton")
        self.btn_ledger.setCursor(Qt.PointingHandCursor)
        self.btn_ledger.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        self.btn_backup = QPushButton(t("nav_backup"))
        self.btn_backup.setProperty("class", "BigHomeButton")
        self.btn_backup.setCursor(Qt.PointingHandCursor)
        self.btn_backup.clicked.connect(self.on_backup_clicked)

        home_layout.addWidget(self.btn_new_bill)
        home_layout.addWidget(self.btn_customers)
        home_layout.addWidget(self.btn_ledger)
        home_layout.addWidget(self.btn_backup)
        home_layout.addStretch()

        self.stack.addWidget(self.home_widget)

        # Screen 1: Customers View
        self.customers_view = CustomersView(on_back_callback=lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.customers_view)

        # Screen 2: Ledger View
        self.ledger_view = LedgerView(on_back_callback=lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.ledger_view)

        # Screen 3: Billing View
        self.billing_view = BillingView(on_back_callback=lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.billing_view)

    def open_customers(self):
        self.customers_view.load_customers()
        self.stack.setCurrentIndex(1)

    def on_switch_language(self):
        toggle_language()
        self.lbl_title.setText(t("app_title"))
        self.lbl_tagline.setText(t("tagline"))
        self.btn_lang.setText(t("btn_switch_lang"))
        self.btn_new_bill.setText(t("nav_new_bill"))
        self.btn_customers.setText(t("nav_customers"))
        self.btn_ledger.setText(t("nav_ledger"))
        self.btn_backup.setText(t("nav_backup"))

    def on_backup_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "પેન ડ્રાઈવ અથવા ફોલ્ડર પસંદ કરો")
        if folder:
            backup_file = backup_database(folder)
            QMessageBox.information(self, "Backup Success", f"{t('msg_backup_ok')}\\n\\n{backup_file}")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''
}

def build_all():
    print("=" * 60)
    print("   JEWELRY BILLING & LEDGER SOFTWARE - AUTO-BUILDER")
    print("=" * 60)
    
    for filename, content in FILES.items():
        file_path = os.path.join(BASE_DIR, filename)
        print(f"Creating: {filename}...")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\\n")
            
    print("\\n[OK] All modules created successfully!")
    print("Launching the software now...\\n")
    
    # Launch main.py
    import subprocess
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "main.py")])

if __name__ == "__main__":
    build_all()