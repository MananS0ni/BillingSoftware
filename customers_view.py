"""
customers_view.py - Customer Directory & Add Dialog.
Full 100% dynamic bilingual translation support.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from translations import t
from database import search_customers, add_customer, get_customer_balance, get_customer_bills
from bill_details_dialog import BillDetailsDialog
from format_utils import format_inr

class AddCustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("btn_add_customer"))
        self.resize(500, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        form = QFormLayout()

        self.lbl_f_name = QLabel(t("lbl_cust_name"))
        self.txt_name_gu = QLineEdit()
        self.txt_name_gu.setPlaceholderText(t("ph_cust_name"))
        form.addRow(self.lbl_f_name, self.txt_name_gu)

        self.lbl_f_mob = QLabel(t("lbl_cust_mobile"))
        self.txt_mobile = QLineEdit()
        self.txt_mobile.setMaxLength(10)
        self.txt_mobile.setPlaceholderText(t("ph_cust_mobile"))
        form.addRow(self.lbl_f_mob, self.txt_mobile)

        self.lbl_f_addr = QLabel(t("lbl_cust_address"))
        self.txt_address = QLineEdit()
        self.txt_address.setPlaceholderText(t("ph_cust_address"))
        form.addRow(self.lbl_f_addr, self.txt_address)

        self.lbl_f_en = QLabel(t("lbl_cust_name_en"))
        self.txt_name_en = QLineEdit()
        self.txt_name_en.setPlaceholderText("e.g. Natwarlal Soni")
        form.addRow(self.lbl_f_en, self.txt_name_en)

        self.lbl_f_gst = QLabel(t("lbl_cust_gstin"))
        self.txt_gstin = QLineEdit()
        self.txt_gstin.setPlaceholderText("GSTIN")
        form.addRow(self.lbl_f_gst, self.txt_gstin)

        self.lbl_f_pan = QLabel(t("lbl_cust_pan"))
        self.txt_pan = QLineEdit()
        self.txt_pan.setMaxLength(10)
        self.txt_pan.setPlaceholderText(t("ph_cust_pan"))
        form.addRow(self.lbl_f_pan, self.txt_pan)

        self.lbl_f_aadhaar = QLabel(t("lbl_cust_aadhaar"))
        self.txt_aadhaar = QLineEdit()
        self.txt_aadhaar.setMaxLength(14)
        self.txt_aadhaar.setPlaceholderText(t("ph_cust_aadhaar"))
        form.addRow(self.lbl_f_aadhaar, self.txt_aadhaar)

        # Seamless Enter-key navigation
        self.txt_name_gu.returnPressed.connect(lambda: self.txt_mobile.setFocus())
        self.txt_mobile.returnPressed.connect(lambda: self.txt_address.setFocus())
        self.txt_address.returnPressed.connect(lambda: self.txt_name_en.setFocus())
        self.txt_name_en.returnPressed.connect(lambda: self.txt_gstin.setFocus())
        self.txt_gstin.returnPressed.connect(lambda: self.txt_pan.setFocus())
        self.txt_pan.returnPressed.connect(lambda: self.txt_aadhaar.setFocus())
        self.txt_aadhaar.returnPressed.connect(self.save)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.btn_cancel = QPushButton(t("btn_cancel"))
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton(t("btn_save"))
        self.btn_save.setObjectName("PrimaryBtn")
        self.btn_save.clicked.connect(self.save)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

    def save(self):
        name = self.txt_name_gu.text().strip()
        mobile = self.txt_mobile.text().strip()
        if not name:
            QMessageBox.warning(self, "Attention", "Please enter customer name.")
            return

        if len(mobile) != 10 or not mobile.isdigit():
            if len(mobile) < 10:
                QMessageBox.warning(
                    self, "Invalid Mobile Number (અમાન્ય મોબાઇલ નંબર)", 
                    f"મોબાઇલ નંબરમાં માત્ર {len(mobile)} આંકડા છે.\nકૃપા કરીને બરાબર ૧૦ આંકડાનો નંબર દાખલ કરો.\n(Mobile number has only {len(mobile)} digits. Please enter exactly 10 digits)."
                )
            else:
                QMessageBox.warning(
                    self, "Invalid Mobile Number (અમાન્ય મોબાઇલ નંબર)", 
                    "કૃપા કરીને બરાબર ૧૦ આંકડાનો સાચો મોબાઇલ નંબર દાખલ કરો.\n(Please enter exactly 10 digits)."
                )
            self.txt_mobile.setFocus()
            return

        add_customer(
            name_gu=name,
            mobile=mobile,
            address=self.txt_address.text().strip(),
            name_en=self.txt_name_en.text().strip(),
            gstin=self.txt_gstin.text().strip(),
            pan_no=self.txt_pan.text().strip().upper(),
            aadhaar_no=self.txt_aadhaar.text().strip()
        )
        self.accept()

class CustomerBillsDialog(QDialog):
    """Lists all past bills of a customer with 1-click view and reprint."""
    def __init__(self, customer, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle(f"Past Bills - {customer['name_gu']} ({customer['mobile']})")
        self.resize(650, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        lbl = QLabel(f"📜 Past Invoices: {self.customer['name_gu']} ({self.customer['mobile']})")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0B1E19;")
        layout.addWidget(lbl)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Bill No", "Date", "Grand Total", "Paid", "Balance (Udhar)", "Action"
        ])
        h = table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        bills = get_customer_bills(self.customer["id"])
        for r_idx, b in enumerate(bills):
            table.insertRow(r_idx)
            table.setItem(r_idx, 0, QTableWidgetItem(f"#{b['bill_no']}"))
            table.setItem(r_idx, 1, QTableWidgetItem(b["bill_date"]))
            
            gt = b["grand_total_paise"] / 100.0
            table.setItem(r_idx, 2, QTableWidgetItem(format_inr(gt)))

            pd = b["paid_paise"] / 100.0
            table.setItem(r_idx, 3, QTableWidgetItem(format_inr(pd)))

            bal = b["balance_paise"] / 100.0
            bal_item = QTableWidgetItem(format_inr(bal))
            bal_item.setForeground(Qt.red if bal > 0 else Qt.darkGreen)
            table.setItem(r_idx, 4, bal_item)

            btn = QPushButton("👁️ View Bill Details")
            btn.setObjectName("SecondaryBtn")
            btn.clicked.connect(lambda _, b_id=b["id"]: BillDetailsDialog(b_id, self).exec())
            table.setCellWidget(r_idx, 5, btn)

        layout.addWidget(table)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("SecondaryBtn")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

class CustomersView(QWidget):
    def __init__(self, on_back_callback, on_open_ledger_callback=None):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.on_open_ledger_callback = on_open_ledger_callback
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        top = QHBoxLayout()
        self.btn_back = QPushButton(t("btn_back"))
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.on_back_callback)
        top.addWidget(self.btn_back)

        self.lbl_page_title = QLabel(t("cust_title"))
        self.lbl_page_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-left: 10px;")
        top.addWidget(self.lbl_page_title)

        top.addSpacing(20)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_cust"))
        self.txt_search.textChanged.connect(self.load_customers)
        top.addWidget(self.txt_search, stretch=2)

        top.addSpacing(16)
        self.btn_add = QPushButton(t("btn_add_customer"))
        self.btn_add.setObjectName("GoldActionBtn")
        self.btn_add.clicked.connect(self.open_add_dialog)
        top.addWidget(self.btn_add)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.setup_table_headers()

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)

    def setup_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            t("th_cust_id"),
            t("th_cust_name"),
            t("th_cust_mobile"),
            t("th_cust_address"),
            t("th_cust_balance"),
            "જૂના બિલ (Past Bills)"
        ])

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
            
            if bal_paise > 0:
                bal_text = f"{format_inr(bal_rs)} {t('status_udhar')}"
            elif bal_paise == 0:
                bal_text = t("status_settled")
            else:
                bal_text = f"{format_inr(abs(bal_rs))} {t('status_jama')}"
            
            item = QTableWidgetItem(bal_text)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(Qt.red if bal_paise > 0 else Qt.darkGreen)
            self.table.setItem(row_idx, 4, item)

            # Action buttons container (Ledger & Past Bills)
            action_box = QWidget()
            ab_layout = QHBoxLayout(action_box)
            ab_layout.setContentsMargins(4, 2, 4, 2)
            ab_layout.setSpacing(6)

            if self.on_open_ledger_callback:
                btn_ledger = QPushButton("📖 ખાતાવહી")
                btn_ledger.setStyleSheet("""
                    QPushButton {
                        background-color: #12382C;
                        color: #FFFFFF;
                        border: 1px solid #D4AF37;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #1E4D3D; }
                """)
                btn_ledger.setCursor(Qt.PointingHandCursor)
                btn_ledger.clicked.connect(lambda _, cust=c: self.on_open_ledger_callback(cust))
                ab_layout.addWidget(btn_ledger)

            btn_past = QPushButton("📜 જૂના બિલ")
            btn_past.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #E2E8F0; }
            """)
            btn_past.setCursor(Qt.PointingHandCursor)
            btn_past.clicked.connect(lambda _, cust=c: self.open_past_bills(cust))
            ab_layout.addWidget(btn_past)

            self.table.setCellWidget(row_idx, 5, action_box)

    def open_past_bills(self, customer):
        bills = get_customer_bills(customer["id"])
        if not bills:
            QMessageBox.information(self, "Past Bills", f"{customer['name_gu']} નું કોઈ જૂનું બિલ સિસ્ટમમાં નથી.\n(No past bills found for this customer).")
            return
        CustomerBillsDialog(customer, self).exec()

    def open_add_dialog(self):
        if AddCustomerDialog(self).exec():
            self.load_customers(self.txt_search.text())

    def retranslate_ui(self):
        self.btn_back.setText(t("btn_back"))
        self.lbl_page_title.setText(t("cust_title"))
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_cust"))
        self.btn_add.setText(t("btn_add_customer"))
        self.setup_table_headers()
        self.load_customers(self.txt_search.text())
