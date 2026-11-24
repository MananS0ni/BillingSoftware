"""
khatabook_view.py - Khatabook & Backdated Billing Interface for Soni Natvarlal Himmatlal.
Allows shop owner to enter offline / past years' bills with:
- Fully editable Bill Date (with calendar popup)
- Fully editable Bill Number (matching physical paper bills)
- Customer lookup & auto-add
- Item entry with weight, rate, making charges & calculations
- GST toggle (defaults to 0% for traditional khata, or 3% for tax bills)
- Paid amount & remaining balance tracking
- Save directly to Khatabook without printing
100% full dynamic bilingual translation support.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QFrame, QGridLayout, QCheckBox,
    QDateEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDate, QEvent
from datetime import datetime
import os
import re
import math

from translations import t
from database import (
    search_customers, add_customer, update_customer, create_bill, 
    get_next_bill_number, get_customer_by_mobile, get_customer_balance,
    get_bill_full_details
)
from print_manager import print_or_pdf_bill, export_bill_to_pdf
from format_utils import format_inr
from whatsapp_manager import send_bill_async, get_whatsapp_status
from settings_manager import get_owner_phone, is_owner_copy_enabled
from app_paths import INVOICES_DIR

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

class KhatabookView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.selected_customer = None
        self.items_data = []
        self.init_ui()
        self.reset_form()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(8)

        # 1. Top Header Row
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(t("btn_back"))
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.on_back_callback)
        top_bar.addWidget(self.btn_back)

        title_box = QVBoxLayout()
        self.lbl_screen_title = QLabel(t("khatabook_title"))
        self.lbl_screen_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 10px; color: #D4AF37;")
        self.lbl_screen_subtitle = QLabel(t("khatabook_subtitle"))
        self.lbl_screen_subtitle.setStyleSheet("font-size: 12px; color: #94A3B8; margin-left: 10px;")
        title_box.addWidget(self.lbl_screen_title)
        title_box.addWidget(self.lbl_screen_subtitle)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.lbl_badge = QLabel("📖 KHATABOOK")
        self.lbl_badge.setStyleSheet(
            "font-size: 14px; font-weight: bold; background: #0B1E19; color: #D4AF37; "
            "padding: 5px 14px; border: 1.5px solid #D4AF37; border-radius: 8px;"
        )
        top_bar.addWidget(self.lbl_badge)
        main_layout.addLayout(top_bar)

        # 2. Main Two-Column Split Layout
        split_layout = QHBoxLayout()
        split_layout.setSpacing(12)

        # ================= LEFT COLUMN: Data Entry =================
        left_column = QVBoxLayout()
        left_column.setSpacing(10)

        # --- Card A: Bill Meta & Customer Info ---
        self.card_cust = QFrame()
        self.card_cust.setObjectName("CardFrame")
        cust_layout = QVBoxLayout(self.card_cust)
        cust_layout.setContentsMargins(12, 8, 12, 8)
        cust_layout.setSpacing(6)

        # Row 1: Bill Date & Bill Number
        meta_grid = QGridLayout()
        meta_grid.setSpacing(6)
        meta_grid.setColumnStretch(0, 3)
        meta_grid.setColumnStretch(1, 2)
        meta_grid.setColumnStretch(2, 4)

        self.lbl_bill_date = QLabel(t("lbl_bill_date"))
        self.lbl_bill_date.setProperty("class", "FormLabel")
        self.date_bill = QDateEdit()
        self.date_bill.setCalendarPopup(True)
        self.date_bill.setDisplayFormat("dd-MM-yyyy")
        self.date_bill.setDate(QDate.currentDate())
        self.date_bill.setFixedHeight(28)
        self.date_bill.setMinimumWidth(135)
        self.date_bill.setStyleSheet("""
            QDateEdit {
                background-color: #FFFDF9;
                border: 1.5px solid #94A3B8;
                border-radius: 6px;
                padding: 4px 26px 4px 8px;
                font-weight: bold;
                font-size: 13px;
                color: #0F172A;
            }
        """)
        meta_grid.addWidget(self.lbl_bill_date, 0, 0)
        meta_grid.addWidget(self.date_bill, 1, 0)

        self.lbl_bill_no = QLabel(t("lbl_custom_bill_no"))
        self.lbl_bill_no.setProperty("class", "FormLabel")
        self.txt_bill_no = QLineEdit()
        self.txt_bill_no.setFixedHeight(28)
        self.txt_bill_no.setPlaceholderText("e.g. 102")
        self.txt_bill_no.setStyleSheet("""
            QLineEdit {
                background-color: #FFFDF9;
                border: 1.5px solid #94A3B8;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 13px;
                color: #0F172A;
            }
        """)
        meta_grid.addWidget(self.lbl_bill_no, 0, 1)
        meta_grid.addWidget(self.txt_bill_no, 1, 1)

        # Mobile Search
        self.lbl_cust_phone = QLabel(t("lbl_cust_mobile"))
        self.lbl_cust_phone.setProperty("class", "FormLabel")
        self.txt_cust_phone = QLineEdit()
        self.txt_cust_phone.setMaxLength(10)
        self.txt_cust_phone.setFixedHeight(28)
        self.txt_cust_phone.setPlaceholderText(t("ph_cust_phone"))
        self.txt_cust_phone.textChanged.connect(self.on_phone_changed)
        meta_grid.addWidget(self.lbl_cust_phone, 0, 2)
        meta_grid.addWidget(self.txt_cust_phone, 1, 2)

        # Name
        self.lbl_cust_name = QLabel(t("lbl_cust_name"))
        self.lbl_cust_name.setProperty("class", "FormLabel")
        self.txt_cust_name = QLineEdit()
        self.txt_cust_name.setFixedHeight(28)
        self.txt_cust_name.setPlaceholderText(t("ph_cust_name"))
        meta_grid.addWidget(self.lbl_cust_name, 2, 0, 1, 2)
        meta_grid.addWidget(self.txt_cust_name, 3, 0, 1, 2)

        # Address
        self.lbl_cust_addr = QLabel(t("lbl_cust_address"))
        self.lbl_cust_addr.setProperty("class", "FormLabel")
        self.txt_cust_address = QLineEdit()
        self.txt_cust_address.setFixedHeight(28)
        self.txt_cust_address.setPlaceholderText(t("ph_cust_addr"))
        meta_grid.addWidget(self.lbl_cust_addr, 2, 2)
        meta_grid.addWidget(self.txt_cust_address, 3, 2)

        cust_layout.addLayout(meta_grid)
        left_column.addWidget(self.card_cust)

        # --- Card B: Jewelry Item Entry ---
        self.card_item = QFrame()
        self.card_item.setObjectName("CardFrame")
        item_card_layout = QVBoxLayout(self.card_item)
        item_card_layout.setContentsMargins(12, 8, 12, 8)
        item_card_layout.setSpacing(6)

        self.lbl_card_item_title = QLabel(t("card_item_entry"))
        self.lbl_card_item_title.setObjectName("CardHeaderTitle")
        item_card_layout.addWidget(self.lbl_card_item_title)

        item_grid = QGridLayout()
        item_grid.setSpacing(6)

        # Description + HSN
        self.lbl_form_desc = QLabel(t("lbl_item_desc"))
        self.lbl_form_desc.setProperty("class", "FormLabel")
        self.txt_item_desc = QLineEdit()
        self.txt_item_desc.setFixedHeight(28)
        self.txt_item_desc.setPlaceholderText(t("ph_item_desc"))
        item_grid.addWidget(self.lbl_form_desc, 0, 0, 1, 2)
        item_grid.addWidget(self.txt_item_desc, 1, 0, 1, 2)

        self.lbl_form_hsn = QLabel(t("lbl_hsn"))
        self.lbl_form_hsn.setProperty("class", "FormLabel")
        self.cmb_hsn = QComboBox()
        self.cmb_hsn.setEditable(True)
        for label, code in HSN_PRESETS:
            self.cmb_hsn.addItem(label, code)
        self.cmb_hsn.setCurrentIndex(0)
        self.cmb_hsn.setMinimumWidth(280)
        self.cmb_hsn.setFixedHeight(28)
        item_grid.addWidget(self.lbl_form_hsn, 0, 2, 1, 3)
        item_grid.addWidget(self.cmb_hsn, 1, 2, 1, 3)

        # Weight | Rate | Making | Amount | + Add Button
        self.lbl_form_wt = QLabel(t("lbl_weight"))
        self.lbl_form_wt.setProperty("class", "FormLabel")
        self.txt_weight = QLineEdit()
        self.txt_weight.setFixedHeight(28)
        self.txt_weight.setPlaceholderText("e.g. 50.000")
        self.txt_weight.textChanged.connect(self.calculate_row_amount)
        item_grid.addWidget(self.lbl_form_wt, 2, 0)
        item_grid.addWidget(self.txt_weight, 3, 0)

        rate_hdr_box = QHBoxLayout()
        self.lbl_form_rate = QLabel(t("lbl_rate"))
        self.lbl_form_rate.setProperty("class", "FormLabel")
        self.btn_live_rate = QPushButton(t("btn_live_rate"))
        self.btn_live_rate.setCursor(Qt.PointingHandCursor)
        self.btn_live_rate.setStyleSheet("""
            QPushButton {
                background: #FEF3C7;
                color: #92400E;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #F59E0B;
                padding: 1px 6px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #FDE68A;
                color: #78350F;
            }
        """)
        self.btn_live_rate.setToolTip("Click to populate live market rate for this item")
        self.btn_live_rate.clicked.connect(self.apply_live_item_rate)
        rate_hdr_box.addWidget(self.lbl_form_rate)
        rate_hdr_box.addStretch()
        rate_hdr_box.addWidget(self.btn_live_rate)

        self.txt_rate = QLineEdit()
        self.txt_rate.setFixedHeight(28)
        self.txt_rate.setPlaceholderText("e.g. 7300")
        self.txt_rate.textChanged.connect(self.calculate_row_amount)
        item_grid.addLayout(rate_hdr_box, 2, 1)
        item_grid.addWidget(self.txt_rate, 3, 1)

        self.lbl_form_making = QLabel(t("lbl_making"))
        self.lbl_form_making.setProperty("class", "FormLabel")
        self.txt_making = QLineEdit()
        self.txt_making.setFixedHeight(28)
        self.txt_making.setPlaceholderText("e.g. 2000")
        self.txt_making.textChanged.connect(self.calculate_row_amount)
        item_grid.addWidget(self.lbl_form_making, 2, 2)
        item_grid.addWidget(self.txt_making, 3, 2)

        self.lbl_form_amt = QLabel(t("lbl_amount"))
        self.lbl_form_amt.setProperty("class", "FormLabel")
        self.txt_amount = QLineEdit()
        self.txt_amount.setFixedHeight(28)
        self.txt_amount.setPlaceholderText("0.00")
        self.txt_amount.setStyleSheet("background-color: #FFFDF9; font-weight: bold; font-size: 15px; color: #0B1E19; border: 2px solid #D4AF37;")
        item_grid.addWidget(self.lbl_form_amt, 2, 3)
        item_grid.addWidget(self.txt_amount, 3, 3)

        self.btn_add_item = QPushButton(t("btn_add_item_to_table"))
        self.btn_add_item.setObjectName("PrimaryBtn")
        self.btn_add_item.setFixedHeight(28)
        self.btn_add_item.setCursor(Qt.PointingHandCursor)
        self.btn_add_item.clicked.connect(self.add_item_to_table)
        item_grid.addWidget(self.btn_add_item, 3, 4)

        item_card_layout.addLayout(item_grid)
        left_column.addWidget(self.card_item)

        # --- Items Table ---
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(7)
        self.setup_table_headers()
        self.table_items.setMinimumHeight(180)
        self.table_items.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_items.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        th = self.table_items.horizontalHeader()
        th.setSectionResizeMode(0, QHeaderView.Stretch)
        th.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_items.verticalHeader().setDefaultSectionSize(32)

        left_column.addWidget(self.table_items, stretch=1)
        split_layout.addLayout(left_column, stretch=6)

        # ================= RIGHT COLUMN: Khata Summary & Save =================
        self.card_invoice = QFrame()
        self.card_invoice.setObjectName("InvoiceSlipCard")
        self.card_invoice.setMinimumWidth(300)
        self.card_invoice.setMaximumWidth(350)
        
        inv_layout = QVBoxLayout(self.card_invoice)
        inv_layout.setContentsMargins(12, 10, 12, 10)
        inv_layout.setSpacing(6)

        self.lbl_inv_title = QLabel(t("card_invoice_summary"))
        self.lbl_inv_title.setObjectName("CardHeaderTitle")
        inv_layout.addWidget(self.lbl_inv_title)

        # GST Toggle Checkbox (Default False for traditional Khata)
        self.chk_apply_gst = QCheckBox(t("lbl_apply_gst"))
        self.chk_apply_gst.setChecked(False)  # Traditional Khata default: 0% GST
        self.chk_apply_gst.setStyleSheet("font-weight: bold; margin-bottom: 2px; font-size: 12px;")
        self.chk_apply_gst.stateChanged.connect(self.update_totals_display)
        inv_layout.addWidget(self.chk_apply_gst)

        # Summary Rows (Subtotal, CGST, SGST)
        summary_grid = QGridLayout()
        summary_grid.setSpacing(4)

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
        pill_layout.setContentsMargins(10, 6, 10, 6)
        pill_layout.setSpacing(2)
        
        self.lbl_grand_tag = QLabel(t("lbl_grand_total"))
        self.lbl_grand_tag.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")
        self.lbl_grand_val = QLabel("₹ 0.00")
        self.lbl_grand_val.setObjectName("GrandTotalNumber")
        pill_layout.addWidget(self.lbl_grand_tag)
        pill_layout.addWidget(self.lbl_grand_val)
        inv_layout.addWidget(total_pill)

        # Paid Now & Balance Due
        pay_grid = QGridLayout()
        pay_grid.setSpacing(5)

        self.lbl_paid_tag = QLabel(t("lbl_paid_now"))
        self.lbl_paid_tag.setProperty("class", "FormLabel")
        self.txt_paid = QLineEdit()
        self.txt_paid.setFixedHeight(28)
        self.txt_paid.setPlaceholderText(t("ph_paid_now"))
        self.txt_paid.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_paid_tag, 0, 0)
        pay_grid.addWidget(self.txt_paid, 0, 1)

        self.lbl_due_tag = QLabel(t("lbl_balance_due"))
        self.lbl_due_tag.setProperty("class", "FormLabel")
        self.lbl_due_val = QLabel("₹ 0.00")
        self.lbl_due_val.setStyleSheet("color: #DC2626; font-size: 15px; font-weight: bold;")
        pay_grid.addWidget(self.lbl_due_tag, 1, 0)
        pay_grid.addWidget(self.lbl_due_val, 1, 1)

        self.lbl_mode_tag = QLabel(t("lbl_pay_mode"))
        self.lbl_mode_tag.setProperty("class", "FormLabel")
        self.cmb_mode = QComboBox()
        self.cmb_mode.setFixedHeight(28)
        self.cmb_mode.addItems(["CASH", "CREDIT / UDHAR", "UPI", "CHEQUE"])
        pay_grid.addWidget(self.lbl_mode_tag, 2, 0)
        pay_grid.addWidget(self.cmb_mode, 2, 1)

        self.lbl_ref_tag = QLabel(t("lbl_payment_ref"))
        self.lbl_ref_tag.setProperty("class", "FormLabel")
        self.txt_payment_ref = QLineEdit()
        self.txt_payment_ref.setFixedHeight(28)
        self.txt_payment_ref.setPlaceholderText(t("ph_upi_ref"))
        pay_grid.addWidget(self.lbl_ref_tag, 3, 0)
        pay_grid.addWidget(self.txt_payment_ref, 3, 1)

        self.cmb_mode.currentTextChanged.connect(self.on_payment_mode_changed)
        self.on_payment_mode_changed(self.cmb_mode.currentText())

        inv_layout.addLayout(pay_grid)
        inv_layout.addStretch()

        # Action Buttons
        btn_box = QVBoxLayout()
        btn_box.setSpacing(6)

        # 1. Primary Gold Button: Save to Khatabook (No Print Pop-up)
        self.btn_save_khata = QPushButton(t("btn_save_khatabook"))
        self.btn_save_khata.setObjectName("GoldActionBtn")
        self.btn_save_khata.setFixedHeight(36)
        self.btn_save_khata.setCursor(Qt.PointingHandCursor)
        self.btn_save_khata.clicked.connect(lambda: self.save_khata_bill(with_print=False))
        btn_box.addWidget(self.btn_save_khata)

        # 2. Secondary Button: Save & Print
        self.btn_save_print = QPushButton(t("btn_save_khatabook_print"))
        self.btn_save_print.setObjectName("PrimaryBtn")
        self.btn_save_print.setFixedHeight(32)
        self.btn_save_print.setCursor(Qt.PointingHandCursor)
        self.btn_save_print.clicked.connect(lambda: self.save_khata_bill(with_print=True))
        btn_box.addWidget(self.btn_save_print)

        inv_layout.addLayout(btn_box)

        # Wire Enter-key navigation
        self.txt_bill_no.returnPressed.connect(lambda: self.txt_cust_phone.setFocus())
        self.txt_cust_phone.returnPressed.connect(self.on_cust_phone_enter)
        self.txt_cust_name.returnPressed.connect(lambda: (self.txt_cust_address.setFocus(), self.txt_cust_address.selectAll()))
        self.txt_cust_address.returnPressed.connect(lambda: (self.txt_item_desc.setFocus(), self.txt_item_desc.selectAll()))
        self.txt_item_desc.returnPressed.connect(lambda: (self.txt_weight.setFocus(), self.txt_weight.selectAll()))
        self.txt_weight.returnPressed.connect(lambda: (self.txt_rate.setFocus(), self.txt_rate.selectAll()))
        self.txt_rate.returnPressed.connect(lambda: (self.txt_making.setFocus(), self.txt_making.selectAll()))
        self.txt_making.returnPressed.connect(self.add_item_to_table)
        self.txt_paid.returnPressed.connect(lambda: self.btn_save_khata.setFocus())

        split_layout.addWidget(self.card_invoice, stretch=3)
        main_layout.addLayout(split_layout)

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

    def get_selected_hsn(self) -> str:
        txt = self.cmb_hsn.currentText().strip()
        match = re.match(r"^(\d{4,8})", txt)
        if match:
            return match.group(1)
        data = self.cmb_hsn.currentData()
        if data and data != "OTHER":
            return str(data)
        if txt and "Other" not in txt and "પોતાનો" not in txt:
            return txt
        return "7113"

    def setup_table_headers(self):
        self.table_items.setHorizontalHeaderLabels([
            t("th_desc"), t("th_hsn"), t("th_weight"), t("th_rate"), t("th_making"), t("th_amount"), t("th_action")
        ])

    def reset_form(self):
        self.selected_customer = None
        self.date_bill.setDate(QDate.currentDate())
        self.txt_bill_no.setText(str(get_next_bill_number()))
        self.txt_cust_phone.clear()
        self.txt_cust_name.clear()
        self.txt_cust_address.clear()
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
        self.chk_apply_gst.setChecked(False)
        self.update_totals_display()

    def on_phone_changed(self, text):
        phone = text.strip()
        if len(phone) == 10 and phone.isdigit():
            c = get_customer_by_mobile(phone)
            if c:
                self.selected_customer = c
                self.txt_cust_name.setText(c["name_gu"])
                self.txt_cust_address.setText(c["address"] or "")
            else:
                if self.selected_customer:
                    self.selected_customer = None
                    self.txt_cust_name.clear()
                    self.txt_cust_address.clear()
        else:
            if self.selected_customer:
                self.selected_customer = None
                self.txt_cust_name.clear()
                self.txt_cust_address.clear()

    def on_cust_phone_enter(self):
        phone = self.txt_cust_phone.text().strip()
        if len(phone) == 10 and phone.isdigit():
            c = get_customer_by_mobile(phone)
            if c:
                self.selected_customer = c
                self.txt_cust_name.setText(c["name_gu"])
                self.txt_cust_address.setText(c["address"] or "")
                self.txt_item_desc.setFocus()
                return
        self.selected_customer = None
        self.txt_cust_name.setFocus()

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

    def apply_live_item_rate(self):
        try:
            from rates_manager import get_rates_manager
            rm = get_rates_manager()
            desc = self.txt_item_desc.text().strip()
            hsn = self.get_selected_hsn()
            rate = rm.get_rate_by_item(desc, hsn)
            if rate > 0:
                self.txt_rate.setText(str(rate))
                self.calculate_row_amount()
                if not rm.is_live():
                    QMessageBox.warning(
                        self, "ઓફલાઇન ભાવ / Offline Rate",
                        "⚠️ ઇન્ટરનેટ કનેક્શન ન હોવાથી સેવ કરેલો જૂનો ભાવ મુકાયો છે. કૃપા કરીને ચકાસો.\n"
                        "(Applied cached/offline rate. Please verify.)"
                    )
        except Exception:
            pass

    def calculate_row_amount(self):
        try:
            wt = float(self.txt_weight.text() or 0)
            rate = float(self.txt_rate.text() or 0)
            making = float(self.txt_making.text() or 0)
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
            wt = float(self.txt_weight.text() or "0")
            rate = float(self.txt_rate.text() or "0")
            making = float(self.txt_making.text() or "0")
        except ValueError:
            QMessageBox.warning(self, "Invalid Number", "Weight, Rate, and Making must be numbers.")
            return

        if math.isnan(wt) or math.isinf(wt) or wt <= 0:
            QMessageBox.warning(self, "Invalid Weight", "Weight must be greater than zero.")
            self.txt_weight.setFocus()
            return
        if math.isnan(rate) or math.isinf(rate) or rate < 0:
            QMessageBox.warning(self, "Invalid Rate", "Rate cannot be negative.")
            self.txt_rate.setFocus()
            return
        if math.isnan(making) or math.isinf(making) or making < 0:
            QMessageBox.warning(self, "Invalid Making", "Making charge cannot be negative.")
            self.txt_making.setFocus()
            return

        amt = round((wt * rate) + making, 2)
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
        btn_del.clicked.connect(self._make_remove_handler(btn_del))
        self.table_items.setCellWidget(row, 6, btn_del)

        self.txt_item_desc.clear()
        self.txt_weight.clear()
        self.txt_making.clear()
        self.txt_amount.clear()
        self.cmb_hsn.setCurrentIndex(0)
        self.txt_item_desc.setFocus()
        self.update_totals_display()

    def _make_remove_handler(self, btn):
        def _handler():
            for r in range(self.table_items.rowCount()):
                if self.table_items.cellWidget(r, 6) is btn:
                    if r < len(self.items_data):
                        self.items_data.pop(r)
                    self.table_items.removeRow(r)
                    self.update_totals_display()
                    return
        return _handler

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

    def save_khata_bill(self, with_print=False):
        if not self.items_data:
            QMessageBox.warning(self, "Attention", t("msg_add_item_first"))
            return

        cust_phone = self.txt_cust_phone.text().strip()
        cust_name = self.txt_cust_name.text().strip() or "Customer"

        if len(cust_phone) != 10 or not cust_phone.isdigit():
            QMessageBox.warning(
                self, "Invalid Mobile Number (અમાન્ય મોબાઇલ નંબર)",
                f"કૃપા કરીને બરાબર ૧૦ આંકડાનો સાચો મોબાઇલ નંબર દાખલ કરો.\n(Please enter exactly 10 digits)."
            )
            self.txt_cust_phone.setFocus()
            return

        # Bill Date & Custom Bill No from Khatabook input
        bill_date_str = self.date_bill.date().toString("yyyy-MM-dd")
        custom_bill_no_raw = self.txt_bill_no.text().strip()
        try:
            custom_bill_no = int(re.sub(r'\D', '', custom_bill_no_raw)) if custom_bill_no_raw else None
        except ValueError:
            custom_bill_no = None

        mode_text = self.cmb_mode.currentText()
        if "CREDIT" in mode_text.upper() or "UDHAR" in mode_text.upper():
            payment_mode = "CREDIT"
        elif "UPI" in mode_text.upper():
            payment_mode = "UPI"
        elif "CHEQUE" in mode_text.upper() or "CHECK" in mode_text.upper():
            payment_mode = "CHEQUE"
        else:
            payment_mode = "CASH"

        ref_val = self.txt_payment_ref.text().strip()
        addr_val = self.txt_cust_address.text().strip()

        # Resolve or update customer
        try:
            if not self.selected_customer:
                existing_c = get_customer_by_mobile(cust_phone)
                if existing_c:
                    cust_id = existing_c["id"]
                    update_customer(
                        customer_id=cust_id,
                        name_gu=cust_name if cust_name and cust_name != "Customer" else None,
                        address=addr_val
                    )
                else:
                    cust_id = add_customer(
                        name_gu=cust_name, mobile=cust_phone,
                        address=addr_val
                    )
            else:
                cust_id = self.selected_customer["id"]
                update_customer(
                    customer_id=cust_id,
                    name_gu=cust_name if cust_name and cust_name != "Customer" else None,
                    address=addr_val
                )
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ગ્રાહક સેવ કરવામાં ભૂલ:\n{e}")
            return

        try:
            paid_rs = float(self.txt_paid.text() or "0")
        except ValueError:
            paid_rs = 0.0

        paid_paise = int(round(paid_rs * 100))
        apply_gst = self.chk_apply_gst.isChecked()

        # Compute totals
        subtotal_paise = sum(i["amount_paise"] for i in self.items_data)
        if apply_gst:
            cgst_paise = round(subtotal_paise * 0.015)
            sgst_paise = round(subtotal_paise * 0.015)
        else:
            cgst_paise = 0
            sgst_paise = 0
        grand_total_paise = subtotal_paise + cgst_paise + sgst_paise
        balance_paise = max(0, grand_total_paise - paid_paise)

        try:
            bill_id = create_bill(
                customer_id=cust_id,
                bill_date=bill_date_str,
                items=self.items_data,
                paid_paise=paid_paise,
                payment_mode=payment_mode,
                payment_ref=ref_val,
                apply_gst=apply_gst,
                custom_bill_no=custom_bill_no
            )
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ખાતાવહી બિલ સેવ કરવામાં ભૂલ:\n{e}")
            return

        saved_bill = get_bill_full_details(bill_id)
        actual_bill_no = saved_bill["bill_no"] if saved_bill else bill_id

        closing_bal = get_customer_balance(cust_id)
        opening_bal = closing_bal - balance_paise
        cust_gstin_val = self.selected_customer.get("gstin", "") if self.selected_customer else ""
        pan_val = self.selected_customer.get("pan_no", "") if self.selected_customer else ""
        aadhaar_val = self.selected_customer.get("aadhaar_no", "") if self.selected_customer else ""

        bill_data = {
            "bill_no": actual_bill_no,
            "book_no": 1,
            "bill_date": bill_date_str,
            "customer_name": cust_name,
            "customer_mobile": cust_phone,
            "customer_address": addr_val,
            "gstin": cust_gstin_val,
            "pan_no": pan_val,
            "aadhaar_no": aadhaar_val,
            "items": self.items_data,
            "subtotal_paise": subtotal_paise,
            "cgst_paise": cgst_paise,
            "sgst_paise": sgst_paise,
            "grand_total_paise": grand_total_paise,
            "paid_paise": paid_paise,
            "balance_paise": balance_paise,
            "payment_mode": payment_mode,
            "payment_ref": ref_val,
            "opening_balance_paise": opening_bal,
            "closing_balance_paise": closing_bal
        }

        # Export PDF automatically
        invoices_dir = INVOICES_DIR
        os.makedirs(invoices_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_\u0A80-\u0AFF]', '_', cust_name)
        pdf_filename = f"Invoice_Bill_{actual_bill_no}_{safe_name}.pdf"
        pdf_path = os.path.join(invoices_dir, pdf_filename)
        try:
            export_bill_to_pdf(bill_data, pdf_path)
        except Exception:
            pdf_path = None

        grand_fmt = format_inr(grand_total_paise, is_paise=True)
        paid_fmt = format_inr(paid_paise, is_paise=True)
        due_fmt = format_inr(balance_paise, is_paise=True)
        total_bal_fmt = format_inr(closing_bal, is_paise=True)

        if with_print and pdf_path:
            print_or_pdf_bill(bill_data, self)
        else:
            QMessageBox.information(
                self, "Khatabook Updated / ખાતાવહી અપડેટ",
                f"✅ {t('msg_khatabook_saved')}\n\n"
                f"📅 તારીખ / Date: {bill_date_str}\n"
                f"🧾 બિલ નં. / Bill #{actual_bill_no}\n"
                f"👤 ગ્રાહક / Customer: {cust_name}\n"
                f"💎 બિલ રકમ / Total: {grand_fmt}\n"
                f"💵 જમા / Paid: {paid_fmt}\n"
                f"⚖️ આ બિલની બાકી / Due: {due_fmt}\n"
                f"----------------------------------------\n"
                f"📈 ગ્રાહકની કુલ માર્કેટ બાકી: {total_bal_fmt}"
            )

        self.reset_form()

    def retranslate_ui(self):
        self.btn_back.setText(t("btn_back"))
        self.lbl_screen_title.setText(t("khatabook_title"))
        self.lbl_screen_subtitle.setText(t("khatabook_subtitle"))
        self.lbl_bill_date.setText(t("lbl_bill_date"))
        self.lbl_bill_no.setText(t("lbl_custom_bill_no"))
        self.lbl_cust_phone.setText(t("lbl_cust_mobile"))
        self.txt_cust_phone.setPlaceholderText(t("ph_cust_phone"))
        self.lbl_cust_name.setText(t("lbl_cust_name"))
        self.txt_cust_name.setPlaceholderText(t("ph_cust_name"))
        self.lbl_cust_addr.setText(t("lbl_cust_address"))
        self.txt_cust_address.setPlaceholderText(t("ph_cust_addr"))

        self.lbl_card_item_title.setText(t("card_item_entry"))
        self.lbl_form_desc.setText(t("lbl_item_desc"))
        self.txt_item_desc.setPlaceholderText(t("ph_item_desc"))
        self.lbl_form_hsn.setText(t("lbl_hsn"))
        self.lbl_form_wt.setText(t("lbl_weight"))
        self.txt_weight.setPlaceholderText(t("ph_item_wt"))
        self.lbl_form_rate.setText(t("lbl_rate"))
        self.btn_live_rate.setText(t("btn_live_rate"))
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
        self.btn_save_khata.setText(t("btn_save_khatabook"))
        self.btn_save_print.setText(t("btn_save_khatabook_print"))

