"""
billing_view.py - Executive Split-Screen POS Billing Interface.
Features a high-end data entry panel on the left and a live Digital Invoice Slip on the right.
Full 100% dynamic bilingual translation support.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QFrame, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QEvent
from datetime import datetime
import os
import re

from translations import t
from database import search_customers, add_customer, create_bill, get_next_bill_number
from print_manager import print_or_pdf_bill, export_bill_to_pdf
from format_utils import format_inr
from whatsapp_manager import send_bill_async, get_whatsapp_status
from settings_manager import get_owner_phone, is_owner_copy_enabled

HSN_PRESETS = [
    ("7113 - Gold & Silver Jewellery (સોના-ચાંદીના દાગીના)", "7113"),
    ("7108 - Gold Ingot / Bullion / Lagdi / Biscuit (સોનાની લગડી/બિસ્કિટ)", "7108"),
    ("7106 - Silver Ingot / Bullion / Lagdi / Chorsa (ચાંદીની લગડી/ચોરસા)", "7106"),
    ("7114 - Silver Articles & Utensils (ચાંદીના વાસણ/પૂજા સામગ્રી)", "7114"),
    ("7118 - Gold & Silver Coins (સોના-ચાંદીના સિક્કા)", "7118"),
    ("7117 - Imitation / Fashion Jewellery (આર્ટિફિશિયલ દાગીના)", "7117"),
    ("7418 - Copper Utensils & Articles (તાંબાના વાસણ/પૂજા પાત્ર)", "7418"),
    ("7403 - Refined Copper / Alloys (શુદ્ધ તાંબુ/મિશ્ર ધાતુ)", "7403"),
    ("Other / Custom (પોતાનો કોડ લખો)", "OTHER"),
]

class BillingView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.selected_customer = None
        self.items_data = []
        self.init_ui()
        self.reset_form()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # 1. Top Header Row
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(t("btn_back"))
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.on_back_callback)
        top_bar.addWidget(self.btn_back)

        self.lbl_screen_title = QLabel(t("billing_title"))
        self.lbl_screen_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-left: 10px;")
        top_bar.addWidget(self.lbl_screen_title)

        top_bar.addStretch()

        self.lbl_bill_badge = QLabel("બિલ નં: 1")
        self.lbl_bill_badge.setStyleSheet("font-size: 16px; font-weight: bold; background: #0B1E19; color: #D4AF37; padding: 6px 16px; border-radius: 8px;")
        top_bar.addWidget(self.lbl_bill_badge)
        main_layout.addLayout(top_bar)

        # 2. Main Two-Column Split Layout
        split_layout = QHBoxLayout()
        split_layout.setSpacing(16)

        # ================= LEFT COLUMN: Data Entry =================
        left_column = QVBoxLayout()
        left_column.setSpacing(14)

        # --- Card A: Customer Information ---
        self.card_cust = QFrame()
        self.card_cust.setObjectName("CardFrame")
        cust_layout = QVBoxLayout(self.card_cust)
        cust_layout.setContentsMargins(16, 14, 16, 14)
        cust_layout.setSpacing(10)

        self.lbl_card_cust_title = QLabel(t("card_customer_info"))
        self.lbl_card_cust_title.setObjectName("CardHeaderTitle")
        cust_layout.addWidget(self.lbl_card_cust_title)

        cust_grid = QGridLayout()
        cust_grid.setSpacing(10)

        # Mobile Search
        self.lbl_cust_phone = QLabel(t("lbl_cust_mobile"))
        self.lbl_cust_phone.setProperty("class", "FormLabel")
        self.txt_cust_phone = QLineEdit()
        self.txt_cust_phone.setMaxLength(10)
        self.txt_cust_phone.setPlaceholderText(t("ph_cust_phone"))
        self.txt_cust_phone.textChanged.connect(self.on_phone_changed)
        cust_grid.addWidget(self.lbl_cust_phone, 0, 0)
        cust_grid.addWidget(self.txt_cust_phone, 1, 0)

        # Name
        self.lbl_cust_name = QLabel(t("lbl_cust_name"))
        self.lbl_cust_name.setProperty("class", "FormLabel")
        self.txt_cust_name = QLineEdit()
        self.txt_cust_name.setPlaceholderText(t("ph_cust_name"))
        cust_grid.addWidget(self.lbl_cust_name, 0, 1)
        cust_grid.addWidget(self.txt_cust_name, 1, 1)

        # Address
        self.lbl_cust_addr = QLabel(t("lbl_cust_address"))
        self.lbl_cust_addr.setProperty("class", "FormLabel")
        self.txt_cust_address = QLineEdit()
        self.txt_cust_address.setPlaceholderText(t("ph_cust_addr"))
        cust_grid.addWidget(self.lbl_cust_addr, 0, 2)
        cust_grid.addWidget(self.txt_cust_address, 1, 2)

        # PAN Card (Safety / IT Compliance)
        self.lbl_cust_pan = QLabel(t("lbl_cust_pan"))
        self.lbl_cust_pan.setProperty("class", "FormLabel")
        self.txt_cust_pan = QLineEdit()
        self.txt_cust_pan.setMaxLength(10)
        self.txt_cust_pan.setPlaceholderText(t("ph_cust_pan"))
        cust_grid.addWidget(self.lbl_cust_pan, 2, 0)
        cust_grid.addWidget(self.txt_cust_pan, 3, 0)

        # Aadhaar Card (Safety / Proof)
        self.lbl_cust_aadhaar = QLabel(t("lbl_cust_aadhaar"))
        self.lbl_cust_aadhaar.setProperty("class", "FormLabel")
        self.txt_cust_aadhaar = QLineEdit()
        self.txt_cust_aadhaar.setMaxLength(14)
        self.txt_cust_aadhaar.setPlaceholderText(t("ph_cust_aadhaar"))
        cust_grid.addWidget(self.lbl_cust_aadhaar, 2, 1)
        cust_grid.addWidget(self.txt_cust_aadhaar, 3, 1)

        cust_layout.addLayout(cust_grid)
        left_column.addWidget(self.card_cust)

        # --- Card B: Jewelry Item Entry ---
        self.card_item = QFrame()
        self.card_item.setObjectName("CardFrame")
        item_card_layout = QVBoxLayout(self.card_item)
        item_card_layout.setContentsMargins(16, 14, 16, 14)
        item_card_layout.setSpacing(10)

        self.lbl_card_item_title = QLabel(t("card_item_entry"))
        self.lbl_card_item_title.setObjectName("CardHeaderTitle")
        item_card_layout.addWidget(self.lbl_card_item_title)

        item_grid = QGridLayout()
        item_grid.setSpacing(10)

        # Row 0 & 1: Description + HSN Dropdown
        self.lbl_form_desc = QLabel(t("lbl_item_desc"))
        self.lbl_form_desc.setProperty("class", "FormLabel")
        self.txt_item_desc = QLineEdit()
        self.txt_item_desc.setPlaceholderText(t("ph_item_desc"))
        item_grid.addWidget(self.lbl_form_desc, 0, 0, 1, 2)
        item_grid.addWidget(self.txt_item_desc, 1, 0, 1, 2)

        self.lbl_form_hsn = QLabel(t("lbl_hsn"))
        self.lbl_form_hsn.setProperty("class", "FormLabel")
        self.cmb_hsn = QComboBox()
        self.cmb_hsn.setEditable(True)
        for label, code in HSN_PRESETS:
            self.cmb_hsn.addItem(label, code)
        self.cmb_hsn.setCurrentIndex(0)  # Default: 7113 Gold & Silver Jewellery
        self.cmb_hsn.setMinimumWidth(300)
        self.cmb_hsn.installEventFilter(self)
        if self.cmb_hsn.lineEdit():
            self.cmb_hsn.lineEdit().installEventFilter(self)
        item_grid.addWidget(self.lbl_form_hsn, 0, 2, 1, 3)
        item_grid.addWidget(self.cmb_hsn, 1, 2, 1, 3)

        # Row 2 & 3: Weight (g) | Rate/g (Rs) | Making (Rs) | Total Amount | + Add Button
        self.lbl_form_wt = QLabel(t("lbl_weight"))
        self.lbl_form_wt.setProperty("class", "FormLabel")
        self.txt_weight = QLineEdit()
        self.txt_weight.setPlaceholderText("e.g. 50.000")
        self.txt_weight.textChanged.connect(self.calculate_row_amount)
        item_grid.addWidget(self.lbl_form_wt, 2, 0)
        item_grid.addWidget(self.txt_weight, 3, 0)

        self.lbl_form_rate = QLabel(t("lbl_rate"))
        self.lbl_form_rate.setProperty("class", "FormLabel")
        self.txt_rate = QLineEdit()
        self.txt_rate.setPlaceholderText("e.g. 7300")
        self.txt_rate.textChanged.connect(self.calculate_row_amount)
        item_grid.addWidget(self.lbl_form_rate, 2, 1)
        item_grid.addWidget(self.txt_rate, 3, 1)

        self.lbl_form_making = QLabel(t("lbl_making"))
        self.lbl_form_making.setProperty("class", "FormLabel")
        self.txt_making = QLineEdit()
        self.txt_making.setPlaceholderText("e.g. 2000")
        self.txt_making.textChanged.connect(self.calculate_row_amount)
        item_grid.addWidget(self.lbl_form_making, 2, 2)
        item_grid.addWidget(self.txt_making, 3, 2)

        self.lbl_form_amt = QLabel(t("lbl_amount"))
        self.lbl_form_amt.setProperty("class", "FormLabel")
        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("0.00")
        self.txt_amount.setStyleSheet("background-color: #FFFDF9; font-weight: bold; font-size: 15px; color: #0B1E19; border: 2px solid #D4AF37;")
        item_grid.addWidget(self.lbl_form_amt, 2, 3)
        item_grid.addWidget(self.txt_amount, 3, 3)

        self.btn_add_item = QPushButton(t("btn_add_item_to_table"))
        self.btn_add_item.setObjectName("PrimaryBtn")
        self.btn_add_item.setCursor(Qt.PointingHandCursor)
        self.btn_add_item.clicked.connect(self.add_item_to_table)
        item_grid.addWidget(self.btn_add_item, 3, 4)

        item_card_layout.addLayout(item_grid)
        left_column.addWidget(self.card_item)

        # --- Items Table ---
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(7)
        self.setup_table_headers()
        
        th = self.table_items.horizontalHeader()
        th.setSectionResizeMode(0, QHeaderView.Stretch)
        th.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_items.verticalHeader().setDefaultSectionSize(36)

        left_column.addWidget(self.table_items, stretch=1)
        split_layout.addLayout(left_column, stretch=6)

        # ================= RIGHT COLUMN: Live Digital Invoice Slip =================
        self.card_invoice = QFrame()
        self.card_invoice.setObjectName("InvoiceSlipCard")
        self.card_invoice.setMinimumWidth(340)
        self.card_invoice.setMaximumWidth(400)
        
        inv_layout = QVBoxLayout(self.card_invoice)
        inv_layout.setContentsMargins(18, 16, 18, 16)
        inv_layout.setSpacing(12)

        self.lbl_inv_title = QLabel(t("card_invoice_summary"))
        self.lbl_inv_title.setObjectName("CardHeaderTitle")
        inv_layout.addWidget(self.lbl_inv_title)

        # GST Toggle Checkbox
        self.chk_apply_gst = QCheckBox(t("lbl_apply_gst"))
        self.chk_apply_gst.setChecked(True)
        self.chk_apply_gst.setStyleSheet("font-weight: bold; margin-bottom: 6px;")
        self.chk_apply_gst.stateChanged.connect(self.update_totals_display)
        inv_layout.addWidget(self.chk_apply_gst)

        # Summary Rows (Subtotal, CGST, SGST)
        summary_grid = QGridLayout()
        summary_grid.setSpacing(8)

        self.lbl_subtotal_tag = QLabel(t("lbl_subtotal"))
        self.lbl_subtotal_val = QLabel("₹ 0.00")
        self.lbl_subtotal_val.setAlignment(Qt.AlignRight)
        self.lbl_subtotal_val.setStyleSheet("font-weight: bold;")
        summary_grid.addWidget(self.lbl_subtotal_tag, 0, 0)
        summary_grid.addWidget(self.lbl_subtotal_val, 0, 1)

        self.lbl_cgst_tag = QLabel(t("lbl_cgst"))
        self.lbl_cgst_val = QLabel("₹ 0.00")
        self.lbl_cgst_val.setAlignment(Qt.AlignRight)
        summary_grid.addWidget(self.lbl_cgst_tag, 1, 0)
        summary_grid.addWidget(self.lbl_cgst_val, 1, 1)

        self.lbl_sgst_tag = QLabel(t("lbl_sgst"))
        self.lbl_sgst_val = QLabel("₹ 0.00")
        self.lbl_sgst_val.setAlignment(Qt.AlignRight)
        summary_grid.addWidget(self.lbl_sgst_tag, 2, 0)
        summary_grid.addWidget(self.lbl_sgst_val, 2, 1)

        inv_layout.addLayout(summary_grid)

        # Luxury Grand Total Box
        total_pill = QFrame()
        total_pill.setObjectName("GrandTotalPill")
        pill_layout = QVBoxLayout(total_pill)
        pill_layout.setContentsMargins(12, 10, 12, 10)
        
        self.lbl_grand_tag = QLabel(t("lbl_grand_total"))
        self.lbl_grand_tag.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        self.lbl_grand_val = QLabel("₹ 0.00")
        self.lbl_grand_val.setObjectName("GrandTotalNumber")
        pill_layout.addWidget(self.lbl_grand_tag)
        pill_layout.addWidget(self.lbl_grand_val)
        inv_layout.addWidget(total_pill)

        # Paid Now & Balance Due
        pay_grid = QGridLayout()
        pay_grid.setSpacing(8)

        self.lbl_paid_tag = QLabel(t("lbl_paid_now"))
        self.lbl_paid_tag.setProperty("class", "FormLabel")
        self.txt_paid = QLineEdit()
        self.txt_paid.setPlaceholderText(t("ph_paid_now"))
        self.txt_paid.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_paid_tag, 0, 0)
        pay_grid.addWidget(self.txt_paid, 0, 1)

        self.lbl_due_tag = QLabel(t("lbl_balance_due"))
        self.lbl_due_tag.setProperty("class", "FormLabel")
        self.lbl_due_val = QLabel("₹ 0.00")
        self.lbl_due_val.setStyleSheet("color: #DC2626; font-size: 16px; font-weight: bold;")
        pay_grid.addWidget(self.lbl_due_tag, 1, 0)
        pay_grid.addWidget(self.lbl_due_val, 1, 1)

        self.lbl_mode_tag = QLabel(t("lbl_pay_mode"))
        self.lbl_mode_tag.setProperty("class", "FormLabel")
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["CASH", "CREDIT / UDHAR", "UPI", "CHEQUE"])
        pay_grid.addWidget(self.lbl_mode_tag, 2, 0)
        pay_grid.addWidget(self.cmb_mode, 2, 1)

        # Dynamic Reference (UPI UTR / Cheque No.)
        self.lbl_ref_tag = QLabel(t("lbl_payment_ref"))
        self.lbl_ref_tag.setProperty("class", "FormLabel")
        self.txt_payment_ref = QLineEdit()
        self.txt_payment_ref.setPlaceholderText(t("ph_upi_ref"))
        pay_grid.addWidget(self.lbl_ref_tag, 3, 0)
        pay_grid.addWidget(self.txt_payment_ref, 3, 1)

        self.cmb_mode.currentTextChanged.connect(self.on_payment_mode_changed)
        self.on_payment_mode_changed(self.cmb_mode.currentText())

        inv_layout.addLayout(pay_grid)
        inv_layout.addStretch()

        # Action Buttons: Save With Print & Save Without Print
        btn_box = QVBoxLayout()
        btn_box.setSpacing(10)

        # 1. Primary Gold Button: Save & Print Invoice
        self.btn_save_print = QPushButton(t("btn_save_with_print"))
        self.btn_save_print.setObjectName("GoldActionBtn")
        self.btn_save_print.setCursor(Qt.PointingHandCursor)
        self.btn_save_print.clicked.connect(lambda: self.save_bill(with_print=True))
        btn_box.addWidget(self.btn_save_print)

        # 2. Emerald / Primary Button: Save Without Print
        self.btn_save_only = QPushButton(t("btn_save_only"))
        self.btn_save_only.setObjectName("PrimaryBtn")
        self.btn_save_only.setCursor(Qt.PointingHandCursor)
        self.btn_save_only.clicked.connect(lambda: self.save_bill(with_print=False))
        btn_box.addWidget(self.btn_save_only)

        inv_layout.addLayout(btn_box)

        # Wire Enter-key navigation across the entire billing workflow
        self.txt_cust_phone.returnPressed.connect(self.on_cust_phone_enter)
        self.txt_cust_name.returnPressed.connect(lambda: (self.txt_cust_address.setFocus(), self.txt_cust_address.selectAll()))
        self.txt_cust_address.returnPressed.connect(lambda: (self.txt_item_desc.setFocus(), self.txt_item_desc.selectAll()))
        self.txt_cust_pan.returnPressed.connect(lambda: (self.txt_cust_aadhaar.setFocus(), self.txt_cust_aadhaar.selectAll()))
        self.txt_cust_aadhaar.returnPressed.connect(lambda: (self.txt_item_desc.setFocus(), self.txt_item_desc.selectAll()))

        self.txt_item_desc.returnPressed.connect(self.on_item_desc_enter)
        self.txt_weight.returnPressed.connect(lambda: (self.txt_rate.setFocus(), self.txt_rate.selectAll()))
        self.txt_rate.returnPressed.connect(lambda: (self.txt_making.setFocus(), self.txt_making.selectAll()))
        self.txt_making.returnPressed.connect(self.add_item_to_table)

        self.txt_paid.returnPressed.connect(self.on_paid_enter)
        self.txt_payment_ref.returnPressed.connect(lambda: self.btn_save_print.setFocus())

        split_layout.addWidget(self.card_invoice, stretch=3)
        main_layout.addLayout(split_layout)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if hasattr(self, 'cmb_hsn') and (obj is self.cmb_hsn or (self.cmb_hsn.lineEdit() and obj is self.cmb_hsn.lineEdit())):
                self.on_hsn_enter()
                return True
        return super().eventFilter(obj, event)

    def on_hsn_enter(self):
        self.txt_weight.setFocus()
        self.txt_weight.selectAll()

    def on_item_desc_enter(self):
        desc = self.txt_item_desc.text().strip()
        if desc:
            self.cmb_hsn.setFocus()
            if self.cmb_hsn.lineEdit():
                self.cmb_hsn.lineEdit().selectAll()
        else:
            # If item description is empty, user is done adding items -> jump to Payment!
            self.txt_paid.setFocus()
            self.txt_paid.selectAll()

    def on_cust_phone_enter(self):
        if self.txt_cust_name.text().strip():
            # Customer already identified from phone search -> jump directly to first item!
            self.txt_item_desc.setFocus()
            self.txt_item_desc.selectAll()
        else:
            # New customer -> jump to name input
            self.txt_cust_name.setFocus()
            self.txt_cust_name.selectAll()

    def on_paid_enter(self):
        mode = self.cmb_mode.currentText()
        if mode in ("UPI", "CHEQUE"):
            self.txt_payment_ref.setFocus()
            self.txt_payment_ref.selectAll()
        else:
            self.btn_save_print.setFocus()

    def get_selected_hsn(self) -> str:
        txt = self.cmb_hsn.currentText().strip()
        # 1. Extract leading digits if present (e.g. "7113 - Gold..." or "7108" or "71131910")
        match = re.match(r"^(\d{4,8})", txt)
        if match:
            return match.group(1)
        # 2. Check currentData if available
        data = self.cmb_hsn.currentData()
        if data and data != "OTHER":
            return str(data)
        # 3. Return user's custom typed text if valid
        if txt and "Other" not in txt and "પોતાનો" not in txt:
            return txt
        return "7113"

    def setup_table_headers(self):
        self.table_items.setHorizontalHeaderLabels([
            t("th_desc"), t("th_hsn"), t("th_weight"), t("th_rate"), t("th_making"), t("th_amount"), t("th_action")
        ])

    def reset_form(self):
        self.selected_customer = None
        self.txt_cust_phone.clear()
        self.txt_cust_name.clear()
        self.txt_cust_address.clear()
        self.txt_cust_pan.clear()
        self.txt_cust_aadhaar.clear()
        self.txt_payment_ref.clear()
        self.txt_item_desc.clear()
        self.cmb_hsn.setCurrentIndex(0)
        self.txt_weight.clear()
        self.txt_rate.clear()
        self.txt_making.clear()
        self.txt_amount.clear()
        self.txt_paid.clear()
        self.table_items.setRowCount(0)
        self.items_data = []
        self.lbl_bill_badge.setText(f"{t('bill_no_label')} #{get_next_bill_number()}")
        self.update_totals_display()

    def on_phone_changed(self, text):
        if len(text.strip()) >= 4:
            results = search_customers(text)
            if results:
                c = results[0]
                self.selected_customer = c
                self.txt_cust_name.setText(c["name_gu"])
                self.txt_cust_address.setText(c["address"] or "")
                self.txt_cust_pan.setText(c.get("pan_no", "") or "")
                self.txt_cust_aadhaar.setText(c.get("aadhaar_no", "") or "")

    def on_payment_mode_changed(self, mode_text):
        mode = mode_text.upper()
        if "UPI" in mode:
            self.lbl_ref_tag.setVisible(True)
            self.txt_payment_ref.setVisible(True)
            self.txt_payment_ref.setPlaceholderText(t("ph_upi_ref"))
        elif "CHEQUE" in mode or "CHECK" in mode:
            self.lbl_ref_tag.setVisible(True)
            self.txt_payment_ref.setVisible(True)
            self.txt_payment_ref.setPlaceholderText(t("ph_cheque_ref"))
        else:
            self.lbl_ref_tag.setVisible(False)
            self.txt_payment_ref.setVisible(False)
            self.txt_payment_ref.clear()

    def calculate_row_amount(self):
        try:
            wt = float(self.txt_weight.text() or 0)
            rate = float(self.txt_rate.text() or 0)
            making = float(self.txt_making.text() or 0)
            # Direct transparent math: (Weight in grams * Rate per gram) + Making Charges
            amt = round((wt * rate) + making, 2)
            self.txt_amount.setText(str(amt))
        except:
            pass

    def add_item_to_table(self):
        desc = self.txt_item_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Attention", t("msg_add_item_first"))
            return

        try:
            wt = float(self.txt_weight.text() or 0)
            rate = float(self.txt_rate.text() or 0)
            making = float(self.txt_making.text() or 0)
            amt = float(self.txt_amount.text())
        except:
            QMessageBox.warning(self, "Attention", "Please enter valid numbers.")
            return

        hsn_code = self.get_selected_hsn()
        item_dict = {
            "description": desc,
            "hsn_code": hsn_code,
            "weight_mg": int(round(wt * 1000)),
            "rate_paise": int(round(rate * 100)),
            "making_paise": int(round(making * 100)),
            "amount_paise": int(round(amt * 100))
        }
        self.items_data.append(item_dict)

        row = self.table_items.rowCount()
        self.table_items.insertRow(row)
        self.table_items.setItem(row, 0, QTableWidgetItem(desc))
        self.table_items.setItem(row, 1, QTableWidgetItem(item_dict["hsn_code"] or "-"))
        self.table_items.setItem(row, 2, QTableWidgetItem(f"{wt:.3f} g"))
        self.table_items.setItem(row, 3, QTableWidgetItem(format_inr(rate)))
        self.table_items.setItem(row, 4, QTableWidgetItem(format_inr(making)))
        self.table_items.setItem(row, 5, QTableWidgetItem(format_inr(amt)))

        btn_del = QPushButton("❌")
        btn_del.setMaximumWidth(40)
        btn_del.clicked.connect(lambda _, r=row: self.remove_item(r))
        self.table_items.setCellWidget(row, 6, btn_del)

        self.txt_item_desc.clear()
        self.txt_weight.clear()
        self.txt_making.clear()
        self.txt_amount.clear()
        self.cmb_hsn.setCurrentIndex(0)  # Reset to default 7113
        self.txt_item_desc.setFocus()
        self.update_totals_display()

    def remove_item(self, row):
        if row < len(self.items_data):
            self.items_data.pop(row)
            self.table_items.removeRow(row)
            self.update_totals_display()

    def update_totals_display(self):
        subtotal = sum(i["amount_paise"] for i in self.items_data) / 100.0
        if self.chk_apply_gst.isChecked():
            cgst = round(subtotal * 0.015, 2)
            sgst = round(subtotal * 0.015, 2)
        else:
            cgst = 0.0
            sgst = 0.0
        grand = round(subtotal + cgst + sgst)
        
        try:
            paid = float(self.txt_paid.text() or 0)
        except:
            paid = 0.0

        due = max(0.0, grand - paid)
        self.lbl_subtotal_val.setText(format_inr(subtotal))
        self.lbl_cgst_val.setText(format_inr(cgst))
        self.lbl_sgst_val.setText(format_inr(sgst))
        self.lbl_grand_val.setText(format_inr(grand))

        self.lbl_due_val.setText(format_inr(due))
        if due > 0:
            self.lbl_due_val.setStyleSheet("color: #DC2626; font-size: 16px; font-weight: bold;")
        else:
            self.lbl_due_val.setStyleSheet("color: #16A34A; font-size: 16px; font-weight: bold;")

    def save_bill(self, with_print=True):
        if not self.items_data:
            QMessageBox.warning(self, "Attention", t("msg_add_item_first"))
            return

        cust_phone = self.txt_cust_phone.text().strip()
        cust_name = self.txt_cust_name.text().strip() or "Customer"

        # Input Validation: Must be exactly 10 digits
        if len(cust_phone) != 10 or not cust_phone.isdigit():
            if len(cust_phone) < 10:
                QMessageBox.warning(
                    self, "Invalid Mobile Number (અમાન્ય મોબાઇલ નંબર)", 
                    f"મોબાઇલ નંબરમાં માત્ર {len(cust_phone)} આંકડા છે.\nકૃપા કરીને બરાબર ૧૦ આંકડાનો નંબર દાખલ કરો.\n(Mobile number has only {len(cust_phone)} digits. Please enter exactly 10 digits)."
                )
            else:
                QMessageBox.warning(
                    self, "Invalid Mobile Number (અમાન્ય મોબાઇલ નંબર)", 
                    "કૃપા કરીને બરાબર ૧૦ આંકડાનો સાચો મોબાઇલ નંબર દાખલ કરો.\n(Please enter exactly 10 digits)."
                )
            self.txt_cust_phone.setFocus()
            return

        pan_val = self.txt_cust_pan.text().strip().upper()
        aadhaar_val = self.txt_cust_aadhaar.text().strip()
        ref_val = self.txt_payment_ref.text().strip()

        if not self.selected_customer:
            cust_id = add_customer(
                name_gu=cust_name, mobile=cust_phone,
                address=self.txt_cust_address.text().strip(),
                pan_no=pan_val, aadhaar_no=aadhaar_val
            )
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
            payment_mode=mode,
            payment_ref=ref_val
        )

        subtotal = sum(i["amount_paise"] for i in self.items_data)
        if self.chk_apply_gst.isChecked():
            cgst = round(subtotal * 0.015)
            sgst = round(subtotal * 0.015)
        else:
            cgst = 0
            sgst = 0
        grand = subtotal + cgst + sgst
        due = max(0, grand - paid_paise)

        bill_data = {
            "bill_no": get_next_bill_number() - 1,
            "book_no": 1,
            "bill_date": today,
            "customer_name": cust_name,
            "customer_mobile": cust_phone,
            "customer_address": self.txt_cust_address.text().strip(),
            "pan_no": pan_val,
            "aadhaar_no": aadhaar_val,
            "items": self.items_data,
            "subtotal_paise": subtotal,
            "cgst_paise": cgst,
            "sgst_paise": sgst,
            "grand_total_paise": grand,
            "paid_paise": paid_paise,
            "balance_paise": due,
            "payment_mode": mode,
            "payment_ref": ref_val
        }

        # 1. Automatically export PDF to dedicated invoices folder
        invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
        os.makedirs(invoices_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_\u0A80-\u0AFF]', '_', cust_name)
        pdf_filename = f"Invoice_Bill_{bill_data['bill_no']}_{safe_name}.pdf"
        pdf_path = os.path.join(invoices_dir, pdf_filename)
        export_bill_to_pdf(bill_data, pdf_path)

        # 2. Automated Silent WhatsApp Dispatch to Customer & Father
        grand_fmt = format_inr(grand, is_paise=True)
        paid_fmt = format_inr(paid_paise, is_paise=True)
        due_fmt = format_inr(due, is_paise=True)

        wa_msg = (
            f"નમસ્તે {cust_name} શેઠ,\n\n"
            f"આપનું સોની નટવરલાલ હિંમતલાલ (Soni Natvarlal Himmatlal) નું ટેક્સ ઇન્વોઇસ નં. #{bill_data['bill_no']} સામેલ છે.\n\n"
            f"🧾 બિલ નં.: #{bill_data['bill_no']}\n"
            f"📅 તારીખ: {today}\n"
            f"💎 કુલ રકમ: {grand_fmt}\n"
            f"💵 જમા આપ્યા: {paid_fmt}\n"
            f"⚖️ બાકી ઉધાર: {due_fmt}\n\n"
            f"આપનું ડિજિટલ ઇનવોઇસ PDF આ સાથે સામેલ છે.\n"
            f"આપની મુલાકાત બદલ ખૂબ ખૂબ આભાર! 🙏\n\n"
            f"સોની નટવરલાલ હિંમતલાલ\n"
            f"Soni Natvarlal Himmatlal"
        )

        wa_status = get_whatsapp_status()
        wa_notice = ""
        if wa_status.get("status") == "connected":
            send_bill_async(cust_phone, message=wa_msg, pdf_path=pdf_path)
            wa_notice = f"\n\n📲 {t('msg_wa_sent')} (+91 {cust_phone})"

            # Send copy to Father's phone if enabled
            owner_phone = get_owner_phone()
            if is_owner_copy_enabled() and owner_phone:
                ref_tag = f" ({ref_val})" if ref_val else ""
                owner_msg = (
                    f"👑 [સોની નટવરલાલ હિંમતલાલ - બિલ એલર્ટ #{bill_data['bill_no']}]\n\n"
                    f"🧾 બિલ નં.: #{bill_data['bill_no']}\n"
                    f"📅 તારીખ: {today}\n"
                    f"👤 ગ્રાહક: {cust_name} ({cust_phone})\n"
                    f"💎 કુલ રકમ: {grand_fmt}\n"
                    f"💵 જમા લીધા: {paid_fmt} [{mode}{ref_tag}]\n"
                    f"⚖️ બાકી ઉધાર: {due_fmt}\n\n"
                    f"📄 ગ્રાહકનું પાકું PDF ઇનવોઇસ આ સાથે સામેલ છે."
                )
                send_bill_async(owner_phone, message=owner_msg, pdf_path=pdf_path)
                wa_notice += f"\n👑 પિતાશ્રીના WhatsApp પર કોપી મોકલાઈ ગઈ (+91 {owner_phone})"
        else:
            wa_notice = f"\n\n⚠️ {t('msg_wa_not_linked')}"

        # 3. Print or Save Only
        if with_print:
            print_or_pdf_bill(bill_data, self)
        else:
            QMessageBox.information(
                self, t("msg_saved_success"),
                f"{t('msg_bill_saved_success')}\n\nબિલ નં. / Bill #{bill_data['bill_no']}\nકુલ રકમ / Total: {grand_fmt}{wa_notice}"
            )

        self.reset_form()

    def retranslate_ui(self):
        """Translates 100% of labels, placeholders, headers, and buttons."""
        self.btn_back.setText(t("btn_back"))
        self.lbl_screen_title.setText(t("billing_title"))
        self.lbl_card_cust_title.setText(t("card_customer_info"))
        self.lbl_cust_phone.setText(t("lbl_cust_mobile"))
        self.txt_cust_phone.setPlaceholderText(t("ph_cust_phone"))
        self.lbl_cust_name.setText(t("lbl_cust_name"))
        self.txt_cust_name.setPlaceholderText(t("ph_cust_name"))
        self.lbl_cust_addr.setText(t("lbl_cust_address"))
        self.txt_cust_address.setPlaceholderText(t("ph_cust_addr"))
        self.lbl_cust_pan.setText(t("lbl_cust_pan"))
        self.txt_cust_pan.setPlaceholderText(t("ph_cust_pan"))
        self.lbl_cust_aadhaar.setText(t("lbl_cust_aadhaar"))
        self.txt_cust_aadhaar.setPlaceholderText(t("ph_cust_aadhaar"))

        self.lbl_card_item_title.setText(t("card_item_entry"))
        self.lbl_form_desc.setText(t("lbl_item_desc"))
        self.txt_item_desc.setPlaceholderText(t("ph_item_desc"))
        self.lbl_form_hsn.setText(t("lbl_hsn"))
        self.lbl_form_wt.setText(t("lbl_weight"))
        self.txt_weight.setPlaceholderText(t("ph_item_wt"))
        self.lbl_form_rate.setText(t("lbl_rate"))
        self.txt_rate.setPlaceholderText(t("ph_item_rate"))
        self.lbl_form_making.setText(t("lbl_making"))
        self.txt_making.setPlaceholderText("e.g. 2000")
        self.lbl_form_amt.setText(t("lbl_amount"))
        self.btn_add_item.setText(t("btn_add_item_to_table"))

        self.setup_table_headers()

        self.chk_apply_gst.setText(t("lbl_apply_gst"))
        self.lbl_inv_title.setText(t("card_invoice_summary"))
        self.lbl_subtotal_tag.setText(t("lbl_subtotal"))
        self.lbl_cgst_tag.setText(t("lbl_cgst"))
        self.lbl_sgst_tag.setText(t("lbl_sgst"))
        self.lbl_grand_tag.setText(t("lbl_grand_total"))
        self.lbl_paid_tag.setText(t("lbl_paid_now"))
        self.txt_paid.setPlaceholderText(t("ph_paid_now"))
        self.lbl_due_tag.setText(t("lbl_balance_due"))
        self.lbl_mode_tag.setText(t("lbl_pay_mode"))
        self.lbl_ref_tag.setText(t("lbl_payment_ref"))
        self.btn_save_print.setText(t("btn_save_with_print"))
        self.btn_save_only.setText(t("btn_save_only"))
        self.lbl_bill_badge.setText(f"{t('bill_no_label')} #{get_next_bill_number()}")
