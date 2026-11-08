"""
ledger_view.py - Complete Jama/Udhar ledger screen for any customer.
Includes quick customer selector dropdown and always-enabled payment recording.
Full 100% dynamic bilingual translation support.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QMessageBox, QComboBox, QFrame
)
from PySide6.QtCore import Qt
from translations import t
from database import search_customers, get_customer_ledger, get_customer_balance, add_payment
from bill_details_dialog import BillDetailsDialog
from format_utils import format_inr

class AddPaymentDialog(QDialog):
    def __init__(self, customer_id=None, customer_name=None, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        title = t("btn_record_payment")
        if customer_name:
            title += f" - {customer_name}"
        self.setWindowTitle(title)
        self.resize(480, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        form = QFormLayout()

        # If no customer was pre-selected, show customer dropdown
        self.all_customers = search_customers("")
        if not self.customer_id:
            self.lbl_f_cust = QLabel(t("lbl_cust_name"))
            self.cmb_customer = QComboBox()
            for c in self.all_customers:
                self.cmb_customer.addItem(f"{c['name_gu']} ({c['mobile']})", c["id"])
            form.addRow(self.lbl_f_cust, self.cmb_customer)

        self.lbl_f_amt = QLabel(t("lbl_pay_amount"))
        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("e.g. 5000")
        form.addRow(self.lbl_f_amt, self.txt_amount)

        self.lbl_f_mode = QLabel(t("lbl_pay_mode_modal"))
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["CASH", "UPI (GPay / PhonePe)", "CHEQUE", "BANK TRANSFER"])
        form.addRow(self.lbl_f_mode, self.cmb_mode)

        self.lbl_f_ref = QLabel(t("lbl_payment_ref"))
        self.txt_ref = QLineEdit()
        self.txt_ref.setPlaceholderText(t("ph_upi_ref"))
        form.addRow(self.lbl_f_ref, self.txt_ref)

        self.cmb_mode.currentTextChanged.connect(self.on_mode_changed)
        self.on_mode_changed(self.cmb_mode.currentText())

        self.lbl_f_rem = QLabel(t("lbl_pay_remark"))
        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText("e.g. Payment received")
        form.addRow(self.lbl_f_rem, self.txt_remark)

        # Seamless Enter-key navigation
        self.txt_amount.returnPressed.connect(lambda: self.txt_ref.setFocus() if self.txt_ref.isEnabled() else self.btn_save.setFocus())
        self.txt_ref.returnPressed.connect(lambda: self.txt_remark.setFocus())
        self.txt_remark.returnPressed.connect(self.save)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_cancel = QPushButton(t("btn_cancel"))
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton(t("btn_save"))
        self.btn_save.setObjectName("PrimaryBtn")
        self.btn_save.clicked.connect(self.save)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addLayout(btns)

    def on_mode_changed(self, text):
        mode = text.upper()
        if "UPI" in mode:
            self.lbl_f_ref.setVisible(True)
            self.txt_ref.setVisible(True)
            self.txt_ref.setPlaceholderText(t("ph_upi_ref"))
        elif "CHEQUE" in mode or "BANK" in mode:
            self.lbl_f_ref.setVisible(True)
            self.txt_ref.setVisible(True)
            self.txt_ref.setPlaceholderText(t("ph_cheque_ref"))
        else:
            self.lbl_f_ref.setVisible(False)
            self.txt_ref.setVisible(False)
            self.txt_ref.clear()

    def save(self):
        # Determine customer_id
        target_id = self.customer_id
        if not target_id:
            if hasattr(self, 'cmb_customer') and self.cmb_customer.currentIndex() >= 0:
                target_id = self.cmb_customer.currentData()
            else:
                QMessageBox.warning(self, "Attention", "Please select a customer.")
                return

        try:
            amt = float(self.txt_amount.text().strip())
            if amt <= 0:
                raise ValueError
        except:
            QMessageBox.warning(self, "Attention", "Please enter a valid amount.")
            return

        paise = int(round(amt * 100))
        mode = self.cmb_mode.currentText().split()[0]
        ref = self.txt_ref.text().strip()
        add_payment(target_id, paise, payment_mode=mode, remark=self.txt_remark.text().strip(), payment_ref=ref)
        self.accept()

class LedgerView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.current_customer = None
        self.init_ui()
        self.refresh_customer_dropdown()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        top = QHBoxLayout()
        self.btn_back = QPushButton(t("btn_back"))
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.on_back_callback)
        top.addWidget(self.btn_back)

        self.lbl_page_title = QLabel(t("ledger_title"))
        self.lbl_page_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-left: 10px;")
        top.addWidget(self.lbl_page_title)

        top.addSpacing(16)

        # Quick Customer Dropdown Selector
        self.cmb_select_cust = QComboBox()
        self.cmb_select_cust.setMinimumWidth(260)
        self.cmb_select_cust.currentIndexChanged.connect(self.on_customer_dropdown_changed)
        top.addWidget(self.cmb_select_cust)

        # Search Bar
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_cust"))
        self.txt_search.textChanged.connect(self.on_search)
        top.addWidget(self.txt_search, stretch=2)

        # Always-Enabled Record Payment Button
        self.btn_pay = QPushButton(t("btn_record_payment"))
        self.btn_pay.setObjectName("GoldActionBtn")
        self.btn_pay.setCursor(Qt.PointingHandCursor)
        self.btn_pay.clicked.connect(self.open_payment_dialog)
        top.addWidget(self.btn_pay)
        layout.addLayout(top)

        # Customer Header details & Balance Banner Card
        self.card_info = QFrame()
        self.card_info.setObjectName("CardFrame")
        c_layout = QHBoxLayout(self.card_info)
        c_layout.setContentsMargins(16, 12, 16, 12)
        
        self.lbl_cust_info = QLabel(t("lbl_select_cust_prompt"))
        self.lbl_cust_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        c_layout.addWidget(self.lbl_cust_info)
        layout.addWidget(self.card_info)

        # Ledger History Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.setup_table_headers()
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

    def refresh_customer_dropdown(self):
        self.cmb_select_cust.blockSignals(True)
        self.cmb_select_cust.clear()
        self.cmb_select_cust.addItem("-- Select Customer (ગ્રાહક પસંદ કરો) --", None)
        customers = search_customers("")
        for c in customers:
            self.cmb_select_cust.addItem(f"{c['name_gu']} ({c['mobile']})", c)
        self.cmb_select_cust.blockSignals(False)

    def on_customer_dropdown_changed(self, idx):
        c = self.cmb_select_cust.currentData()
        if c:
            self.load_customer_ledger(c)

    def setup_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            t("th_date"),
            t("th_entry_type"),
            t("th_remark"),
            t("th_debit"),
            t("th_credit"),
            t("th_mode"),
            t("th_action")
        ])

    def on_search(self, text):
        results = search_customers(text)
        if results:
            self.load_customer_ledger(results[0])

    def load_customer_ledger(self, customer):
        self.current_customer = customer

        bal_paise = get_customer_balance(customer["id"])
        bal_rs = bal_paise / 100.0
        color = "#DC2626" if bal_paise > 0 else "#16A34A"
        
        if bal_paise > 0:
            status = f"{format_inr(bal_rs)} {t('status_udhar')}"
        elif bal_paise == 0:
            status = t("status_settled")
        else:
            status = f"{format_inr(abs(bal_rs))} {t('status_jama')}"

        self.lbl_cust_info.setText(
            f"👤 {customer['name_gu']} ({customer['mobile']})   |   "
            f"<span style='color:{color}; font-size:18px; font-weight:bold;'>{t('lbl_balance_due')} {status}</span>"
        )

        entries = get_customer_ledger(customer["id"])
        self.table.setRowCount(0)
        for row_idx, e in enumerate(entries):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(e["entry_date"]))
            
            t_item = QTableWidgetItem(e["entry_type"])
            t_item.setForeground(Qt.red if e["entry_type"] == "UDHAR" else Qt.darkGreen)
            self.table.setItem(row_idx, 1, t_item)

            desc = e["remark"]
            if e.get("bill_no"):
                desc = f"#{e['bill_no']} - " + desc
            self.table.setItem(row_idx, 2, QTableWidgetItem(desc))

            rs = e["amount_paise"] / 100.0
            if e["entry_type"] == "UDHAR":
                self.table.setItem(row_idx, 3, QTableWidgetItem(format_inr(rs)))
                self.table.setItem(row_idx, 4, QTableWidgetItem("-"))
            else:
                self.table.setItem(row_idx, 3, QTableWidgetItem("-"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(format_inr(rs)))

            mode_display = e["payment_mode"] or ""
            if e.get("payment_ref"):
                mode_display += f" ({e['payment_ref']})"
            self.table.setItem(row_idx, 5, QTableWidgetItem(mode_display))

            if e.get("bill_id"):
                btn_view = QPushButton("🧾 " + t("btn_print"))
                btn_view.setObjectName("SecondaryBtn")
                btn_view.clicked.connect(lambda _, b_id=e["bill_id"]: BillDetailsDialog(b_id, self).exec())
                self.table.setCellWidget(row_idx, 6, btn_view)
            else:
                self.table.setItem(row_idx, 6, QTableWidgetItem("-"))

    def open_payment_dialog(self):
        cust_id = self.current_customer["id"] if self.current_customer else None
        cust_name = self.current_customer["name_gu"] if self.current_customer else None
        dlg = AddPaymentDialog(cust_id, cust_name, self)
        if dlg.exec():
            if self.current_customer:
                self.load_customer_ledger(self.current_customer)
            self.refresh_customer_dropdown()

    def retranslate_ui(self):
        self.btn_back.setText(t("btn_back"))
        self.lbl_page_title.setText(t("ledger_title"))
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_cust"))
        self.btn_pay.setText(t("btn_record_payment"))
        self.setup_table_headers()
        self.refresh_customer_dropdown()
        if self.current_customer:
            self.load_customer_ledger(self.current_customer)
        else:
            self.lbl_cust_info.setText(t("lbl_select_cust_prompt"))
