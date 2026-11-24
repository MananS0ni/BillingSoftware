"""
kachu_khatu_view.py - Traditional Jeweler's Chopda / Counter Ledger (કાચું ખાતું).
Tailored specifically for Indian / Gujarati jewelry shop counter workflow:
1. Zero grams, zero rates, zero making charges.
2. Direct entry: Customer Info + Product Name (વિગત) + Amount (રકમ ₹).
3. Round Figure / Kasar (કસર):
   - Ability to enter custom round off adjustment (e.g. -₹4 or -₹94).
   - Quick 1-click round buttons: Round to ₹10, Round to ₹100.
4. Multi-Mode / Split Payments (મિશ્ર ચુકવણી):
   - Customer can pay simultaneously in:
     * 🪙 Old Gold (જૂનું સોનું)
     * 🥈 Old Silver (જૂની ચાંદી)
     * 💵 Cash (રોકડ)
     * 📱 UPI / Online
     * 🏦 Cheque / Bank
5. Automatically calculates Total Paid (કુલ જમા) and Balance Due (બાકી ઉધાર).
6. Atomically records itemized payment entries into Customer Khata / Ledger.
7. 100% Bilingual Gujarati & English support.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QDateEdit, QScrollArea,
    QCompleter
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
import re
import math

from translations import t
from database import (
    search_customers, add_customer, update_customer,
    get_next_bill_number, get_customer_by_mobile, get_customer_balance,
    create_kachu_bill
)
from print_manager import print_or_pdf_bill
from format_utils import format_inr, format_date_dmy, get_caption
from whatsapp_manager import send_bill_async, get_whatsapp_status
from settings_manager import get_owner_phone, is_owner_copy_enabled

# Common jewelry product suggestions for fast counter typing
JEWELRY_SUGGESTIONS = [
    "સોનાનો હાર (Gold Necklace)",
    "સોનાની ચેઈન (Gold Chain)",
    "સોનાની વીંટી (Gold Ring)",
    "સોનાની બંગડી (Gold Bangles)",
    "કાનની બુટ્ટી / એરિંગ્સ (Earrings)",
    "સોનાનું મંગળસૂત્ર (Mangalsutra)",
    "સોનાનું લકી (Gold Lucky / Bracelet)",
    "સોનાનો પેન્ડન્ટ (Gold Pendant)",
    "સોનાનો સિક્કો (Gold Coin / Lagdi)",
    "ચાંદીની પાયલ (Silver Payal)",
    "ચાંદીના છડા (Silver Chhada)",
    "ચાંદીના સાંકળા (Silver Sankla)",
    "ચાંદીના વાસણ (Silver Utensils)",
    "ચાંદીની પૂજા સામગ્રી (Pooja Items)",
    "ચાંદીના સિક્કા (Silver Coins)",
    "ચાંદીની લગડી / ચોરસા (Silver Ingot)",
    "જૂના દાગીના રિપેરિંગ (Jewelry Repairing)",
    "અન્ય દાગીના (Other Jewelry)",
]

class KachuKhatuView(QWidget):
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
        self.lbl_screen_title = QLabel(t("kachu_title"))
        self.lbl_screen_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 10px; color: #D4AF37;")
        self.lbl_screen_subtitle = QLabel(t("kachu_subtitle"))
        self.lbl_screen_subtitle.setStyleSheet("font-size: 12px; color: #94A3B8; margin-left: 10px;")
        title_box.addWidget(self.lbl_screen_title)
        title_box.addWidget(self.lbl_screen_subtitle)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.lbl_badge = QLabel(t("kachu_badge"))
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

        self.lbl_card_cust_title = QLabel(t("card_customer_info"))
        self.lbl_card_cust_title.setObjectName("CardHeaderTitle")
        cust_layout.addWidget(self.lbl_card_cust_title)

        meta_grid = QGridLayout()
        meta_grid.setSpacing(6)
        meta_grid.setColumnStretch(0, 3)
        meta_grid.setColumnStretch(1, 2)
        meta_grid.setColumnStretch(2, 4)

        # Date
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

        # Entry / Bill Number
        self.lbl_bill_no = QLabel(t("lbl_kachu_bill_no"))
        self.lbl_bill_no.setProperty("class", "FormLabel")
        self.txt_bill_no = QLineEdit()
        self.txt_bill_no.setFixedHeight(28)
        self.txt_bill_no.setPlaceholderText("e.g. 101")
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

        # Customer Name
        self.lbl_cust_name = QLabel(t("lbl_cust_name"))
        self.lbl_cust_name.setProperty("class", "FormLabel")
        self.txt_cust_name = QLineEdit()
        self.txt_cust_name.setFixedHeight(28)
        self.txt_cust_name.setPlaceholderText(t("ph_cust_name"))
        meta_grid.addWidget(self.lbl_cust_name, 2, 0, 1, 2)
        meta_grid.addWidget(self.txt_cust_name, 3, 0, 1, 2)

        # Address / Village
        self.lbl_cust_addr = QLabel(t("lbl_cust_address"))
        self.lbl_cust_addr.setProperty("class", "FormLabel")
        self.txt_cust_address = QLineEdit()
        self.txt_cust_address.setFixedHeight(28)
        self.txt_cust_address.setPlaceholderText(t("ph_cust_addr"))
        meta_grid.addWidget(self.lbl_cust_addr, 2, 2)
        meta_grid.addWidget(self.txt_cust_address, 3, 2)

        cust_layout.addLayout(meta_grid)
        left_column.addWidget(self.card_cust)

        # --- Card B: Simplified Jewelry Item Entry (Zero Grams / Formulas) ---
        self.card_item = QFrame()
        self.card_item.setObjectName("CardFrame")
        item_card_layout = QVBoxLayout(self.card_item)
        item_card_layout.setContentsMargins(12, 8, 12, 8)
        item_card_layout.setSpacing(6)

        self.lbl_card_item_title = QLabel(t("card_kachu_item_entry"))
        self.lbl_card_item_title.setObjectName("CardHeaderTitle")
        item_card_layout.addWidget(self.lbl_card_item_title)

        item_grid = QGridLayout()
        item_grid.setSpacing(6)

        # 1. Product Name / Description (with auto-completer)
        self.lbl_item_name = QLabel(t("lbl_kachu_item_name"))
        self.lbl_item_name.setProperty("class", "FormLabel")
        self.txt_item_desc = QLineEdit()
        self.txt_item_desc.setFixedHeight(28)
        self.txt_item_desc.setPlaceholderText(t("ph_kachu_item_name"))
        
        completer = QCompleter(JEWELRY_SUGGESTIONS, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.txt_item_desc.setCompleter(completer)
        
        item_grid.addWidget(self.lbl_item_name, 0, 0, 1, 3)
        item_grid.addWidget(self.txt_item_desc, 1, 0, 1, 3)

        # 2. Amount (₹)
        self.lbl_item_amt = QLabel(t("lbl_kachu_item_amt"))
        self.lbl_item_amt.setProperty("class", "FormLabel")
        self.txt_item_amount = QLineEdit()
        self.txt_item_amount.setFixedHeight(28)
        self.txt_item_amount.setPlaceholderText("e.g. 50000")
        self.txt_item_amount.setStyleSheet("""
            QLineEdit {
                background-color: #FFFDF9;
                font-weight: bold;
                font-size: 14px;
                color: #0B1E19;
                border: 2px solid #D4AF37;
            }
        """)
        item_grid.addWidget(self.lbl_item_amt, 0, 3)
        item_grid.addWidget(self.txt_item_amount, 1, 3)

        # 3. Add Item Button
        self.btn_add_item = QPushButton(t("btn_kachu_add_item"))
        self.btn_add_item.setObjectName("PrimaryBtn")
        self.btn_add_item.setFixedHeight(28)
        self.btn_add_item.setCursor(Qt.PointingHandCursor)
        self.btn_add_item.clicked.connect(self.add_item_to_table)
        item_grid.addWidget(self.btn_add_item, 1, 4)

        item_card_layout.addLayout(item_grid)
        left_column.addWidget(self.card_item)

        # --- Items Table ---
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(4)
        self.setup_table_headers()
        self.table_items.setMinimumHeight(180)
        self.table_items.verticalHeader().setVisible(False)
        self.table_items.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_items.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        th = self.table_items.horizontalHeader()
        th.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Sr
        th.setSectionResizeMode(1, QHeaderView.Stretch)           # Description
        th.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Amount
        th.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Action
        self.table_items.verticalHeader().setDefaultSectionSize(32)

        left_column.addWidget(self.table_items, stretch=1)
        split_layout.addLayout(left_column, stretch=6)

        # ================= RIGHT COLUMN: Khata Summary & Split Payments =================
        self.card_summary = QFrame()
        self.card_summary.setObjectName("InvoiceSlipCard")
        self.card_summary.setMinimumWidth(320)
        self.card_summary.setMaximumWidth(360)

        sum_layout = QVBoxLayout(self.card_summary)
        sum_layout.setContentsMargins(12, 10, 12, 10)
        sum_layout.setSpacing(6)

        self.lbl_summary_title = QLabel("💰 " + t("card_invoice_summary"))
        self.lbl_summary_title.setObjectName("CardHeaderTitle")
        sum_layout.addWidget(self.lbl_summary_title)

        # Subtotal Row
        sub_box = QHBoxLayout()
        self.lbl_sub_tag = QLabel(t("lbl_subtotal"))
        self.lbl_sub_tag.setProperty("class", "FormLabel")
        self.lbl_sub_val = QLabel("₹ 0.00")
        self.lbl_sub_val.setAlignment(Qt.AlignRight)
        self.lbl_sub_val.setStyleSheet("font-weight: bold; font-size: 14px; color: #0B1E19;")
        sub_box.addWidget(self.lbl_sub_tag)
        sub_box.addWidget(self.lbl_sub_val)
        sum_layout.addLayout(sub_box)

        # Round Figure / Kasar Section
        kasar_frame = QFrame()
        kasar_frame.setStyleSheet("background: #F8F9FA; border: 1px dashed #CBD5E1; border-radius: 6px; padding: 4px 6px;")
        kasar_layout = QVBoxLayout(kasar_frame)
        kasar_layout.setContentsMargins(4, 4, 4, 4)
        kasar_layout.setSpacing(4)

        k_title_row = QHBoxLayout()
        self.lbl_kasar_tag = QLabel(t("lbl_kachu_round_off"))
        self.lbl_kasar_tag.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        k_title_row.addWidget(self.lbl_kasar_tag)
        kasar_layout.addLayout(k_title_row)

        k_input_row = QHBoxLayout()
        k_input_row.setSpacing(4)

        self.txt_round_off = QLineEdit()
        self.txt_round_off.setFixedHeight(26)
        self.txt_round_off.setPlaceholderText("0.00")
        self.txt_round_off.setStyleSheet("font-weight: bold; font-size: 12px; border: 1px solid #94A3B8; border-radius: 4px; padding: 2px 6px;")
        self.txt_round_off.textChanged.connect(self.update_totals_display)
        k_input_row.addWidget(self.txt_round_off)

        self.btn_round_10 = QPushButton(t("btn_round_10"))
        self.btn_round_10.setObjectName("SecondaryBtn")
        self.btn_round_10.setFixedHeight(26)
        self.btn_round_10.setStyleSheet("font-size: 10px; font-weight: bold; padding: 2px 6px;")
        self.btn_round_10.clicked.connect(self.round_to_nearest_10)
        k_input_row.addWidget(self.btn_round_10)

        self.btn_round_100 = QPushButton(t("btn_round_100"))
        self.btn_round_100.setObjectName("SecondaryBtn")
        self.btn_round_100.setFixedHeight(26)
        self.btn_round_100.setStyleSheet("font-size: 10px; font-weight: bold; padding: 2px 6px;")
        self.btn_round_100.clicked.connect(self.round_to_nearest_100)
        k_input_row.addWidget(self.btn_round_100)

        kasar_layout.addLayout(k_input_row)
        sum_layout.addWidget(kasar_frame)

        # High-Contrast Grand Total Pill
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
        sum_layout.addWidget(total_pill)

        # Split Payment Breakdown Section
        pay_hdr_row = QHBoxLayout()
        self.lbl_split_hdr = QLabel(t("lbl_split_pay_hdr"))
        self.lbl_split_hdr.setStyleSheet("font-size: 12px; font-weight: bold; color: #0B1E19; margin-top: 2px;")
        pay_hdr_row.addWidget(self.lbl_split_hdr)
        pay_hdr_row.addStretch()

        self.btn_full_cash = QPushButton(t("btn_full_cash"))
        self.btn_full_cash.setCursor(Qt.PointingHandCursor)
        self.btn_full_cash.setStyleSheet("""
            QPushButton {
                background: #E0E7FF;
                color: #3730A3;
                font-size: 10px;
                font-weight: bold;
                border: 1px solid #C7D2FE;
                border-radius: 4px;
                padding: 1px 6px;
            }
            QPushButton:hover {
                background: #C7D2FE;
            }
        """)
        self.btn_full_cash.clicked.connect(self.set_full_cash)
        pay_hdr_row.addWidget(self.btn_full_cash)
        sum_layout.addLayout(pay_hdr_row)

        pay_grid = QGridLayout()
        pay_grid.setSpacing(4)

        # 1. Old Gold (જૂનું સોનું)
        self.lbl_gold = QLabel(t("lbl_pay_gold"))
        self.lbl_gold.setProperty("class", "FormLabel")
        self.txt_pay_gold = QLineEdit()
        self.txt_pay_gold.setFixedHeight(26)
        self.txt_pay_gold.setPlaceholderText("0.00")
        self.txt_pay_gold.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_gold, 0, 0)
        pay_grid.addWidget(self.txt_pay_gold, 0, 1)

        # 2. Old Silver (જૂની ચાંદી)
        self.lbl_silver = QLabel(t("lbl_pay_silver"))
        self.lbl_silver.setProperty("class", "FormLabel")
        self.txt_pay_silver = QLineEdit()
        self.txt_pay_silver.setFixedHeight(26)
        self.txt_pay_silver.setPlaceholderText("0.00")
        self.txt_pay_silver.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_silver, 1, 0)
        pay_grid.addWidget(self.txt_pay_silver, 1, 1)

        # 3. Cash (રોકડ)
        self.lbl_cash = QLabel(t("lbl_pay_cash"))
        self.lbl_cash.setProperty("class", "FormLabel")
        self.txt_pay_cash = QLineEdit()
        self.txt_pay_cash.setFixedHeight(26)
        self.txt_pay_cash.setPlaceholderText("0.00")
        self.txt_pay_cash.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_cash, 2, 0)
        pay_grid.addWidget(self.txt_pay_cash, 2, 1)

        # 4. UPI (ઓનલાઇન)
        self.lbl_upi = QLabel(t("lbl_pay_upi"))
        self.lbl_upi.setProperty("class", "FormLabel")
        self.txt_pay_upi = QLineEdit()
        self.txt_pay_upi.setFixedHeight(26)
        self.txt_pay_upi.setPlaceholderText("0.00")
        self.txt_pay_upi.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_upi, 3, 0)
        pay_grid.addWidget(self.txt_pay_upi, 3, 1)

        # 5. Cheque (ચેક)
        self.lbl_cheque = QLabel(t("lbl_pay_cheque"))
        self.lbl_cheque.setProperty("class", "FormLabel")
        self.txt_pay_cheque = QLineEdit()
        self.txt_pay_cheque.setFixedHeight(26)
        self.txt_pay_cheque.setPlaceholderText("0.00")
        self.txt_pay_cheque.textChanged.connect(self.update_totals_display)
        pay_grid.addWidget(self.lbl_cheque, 4, 0)
        pay_grid.addWidget(self.txt_pay_cheque, 4, 1)

        sum_layout.addLayout(pay_grid)

        # Total Paid (કુલ જમા) Row
        paid_box = QHBoxLayout()
        self.lbl_paid_tag = QLabel(t("lbl_paid_now"))
        self.lbl_paid_tag.setProperty("class", "FormLabel")
        self.lbl_paid_val = QLabel("₹ 0.00")
        self.lbl_paid_val.setAlignment(Qt.AlignRight)
        self.lbl_paid_val.setStyleSheet("font-weight: bold; font-size: 14px; color: #16A34A;")
        paid_box.addWidget(self.lbl_paid_tag)
        paid_box.addWidget(self.lbl_paid_val)
        sum_layout.addLayout(paid_box)

        # Balance Due / Udhar (બાકી ઉધાર) Row
        due_box = QHBoxLayout()
        self.lbl_due_tag = QLabel(t("lbl_balance_due"))
        self.lbl_due_tag.setProperty("class", "FormLabel")
        self.lbl_due_val = QLabel("₹ 0.00")
        self.lbl_due_val.setAlignment(Qt.AlignRight)
        self.lbl_due_val.setStyleSheet("font-weight: bold; font-size: 16px; color: #DC2626;")
        due_box.addWidget(self.lbl_due_tag)
        due_box.addWidget(self.lbl_due_val)
        sum_layout.addLayout(due_box)

        sum_layout.addStretch()

        # Action Buttons
        btn_box = QVBoxLayout()
        btn_box.setSpacing(6)

        # 1. Primary Gold Button: Save to Kachu Khatu
        self.btn_save_kachu = QPushButton(t("btn_save_kachu"))
        self.btn_save_kachu.setObjectName("GoldActionBtn")
        self.btn_save_kachu.setFixedHeight(36)
        self.btn_save_kachu.setCursor(Qt.PointingHandCursor)
        self.btn_save_kachu.clicked.connect(lambda: self.save_kachu_entry(with_print=False))
        btn_box.addWidget(self.btn_save_kachu)

        # 2. Secondary Button: Save & Print Slip
        self.btn_save_print = QPushButton(t("btn_save_print_kachu"))
        self.btn_save_print.setObjectName("PrimaryBtn")
        self.btn_save_print.setFixedHeight(32)
        self.btn_save_print.setCursor(Qt.PointingHandCursor)
        self.btn_save_print.clicked.connect(lambda: self.save_kachu_entry(with_print=True))
        btn_box.addWidget(self.btn_save_print)

        sum_layout.addLayout(btn_box)

        # Wire Enter-key workflow
        self.txt_bill_no.returnPressed.connect(lambda: self.txt_cust_phone.setFocus())
        self.txt_cust_phone.returnPressed.connect(self.on_cust_phone_enter)
        self.txt_cust_name.returnPressed.connect(lambda: self.txt_cust_address.setFocus())
        self.txt_cust_address.returnPressed.connect(lambda: self.txt_item_desc.setFocus())
        self.txt_item_desc.returnPressed.connect(lambda: self.txt_item_amount.setFocus())
        self.txt_item_amount.returnPressed.connect(self.add_item_to_table)
        self.txt_pay_cash.returnPressed.connect(lambda: self.btn_save_kachu.setFocus())

        split_layout.addWidget(self.card_summary, stretch=3)
        main_layout.addLayout(split_layout)

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

    def setup_table_headers(self):
        self.table_items.setHorizontalHeaderLabels([
            t("th_kachu_sr"),
            t("th_kachu_item"),
            t("th_kachu_amount"),
            t("th_kachu_action")
        ])

    def reset_form(self):
        self.selected_customer = None
        self.items_data.clear()
        self.table_items.setRowCount(0)

        self.date_bill.setDate(QDate.currentDate())
        try:
            next_no = get_next_bill_number(book_no=2)
            self.txt_bill_no.setText(str(next_no))
        except Exception:
            self.txt_bill_no.setText("1")

        self.txt_cust_phone.clear()
        self.txt_cust_name.clear()
        self.txt_cust_address.clear()

        self.txt_item_desc.clear()
        self.txt_item_amount.clear()

        self.txt_round_off.setText("0.00")
        self.txt_pay_gold.clear()
        self.txt_pay_silver.clear()
        self.txt_pay_cash.clear()
        self.txt_pay_upi.clear()
        self.txt_pay_cheque.clear()

        self.update_totals_display()

    def on_phone_changed(self, text: str):
        cleaned = re.sub(r"\D", "", text)
        if len(cleaned) == 10:
            cust = get_customer_by_mobile(cleaned)
            if cust:
                self.selected_customer = cust
                self.txt_cust_name.setText(cust["name_gu"])
                self.txt_cust_address.setText(cust.get("address", ""))
            else:
                self.selected_customer = None
        else:
            self.selected_customer = None

    def on_cust_phone_enter(self):
        if not self.txt_cust_name.text().strip():
            self.txt_cust_name.setFocus()
        else:
            self.txt_item_desc.setFocus()

    def add_item_to_table(self):
        desc = self.txt_item_desc.text().strip()
        amt_str = self.txt_item_amount.text().strip()

        if not desc:
            QMessageBox.warning(self, "Invalid Entry", "કૃપા કરીને દાગીનાનું નામ અથવા વિગત લખો (Please enter Product Name).")
            self.txt_item_desc.setFocus()
            return

        try:
            amt = float(amt_str)
            if amt <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "કૃપા કરીને સાચી રકમ લખો (Please enter valid amount).")
            self.txt_item_amount.setFocus()
            return

        item_entry = {
            "description": desc,
            "amount_paise": int(round(amt * 100))
        }
        self.items_data.append(item_entry)

        self.refresh_table()

        # Clear inputs for next item
        self.txt_item_desc.clear()
        self.txt_item_amount.clear()
        self.txt_item_desc.setFocus()

        self.update_totals_display()

    def remove_item(self, row_idx: int):
        if 0 <= row_idx < len(self.items_data):
            self.items_data.pop(row_idx)
            self.refresh_table()
            self.update_totals_display()

    def refresh_table(self):
        self.table_items.setRowCount(0)
        for idx, item in enumerate(self.items_data):
            self.table_items.insertRow(idx)

            item_sr = QTableWidgetItem(str(idx + 1))
            item_sr.setTextAlignment(Qt.AlignCenter)
            self.table_items.setItem(idx, 0, item_sr)

            item_d = QTableWidgetItem(item["description"])
            self.table_items.setItem(idx, 1, item_d)

            amt = item["amount_paise"] / 100.0
            item_a = QTableWidgetItem(format_inr(amt))
            item_a.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            font = item_a.font()
            font.setBold(True)
            item_a.setFont(font)
            self.table_items.setItem(idx, 2, item_a)

            btn_del = QPushButton("❌")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setMaximumWidth(45)
            btn_del.setStyleSheet("""
                QPushButton {
                    background: #FEE2E2;
                    color: #DC2626;
                    border: 1px solid #FCA5A5;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background: #FCA5A5;
                }
            """)
            btn_del.clicked.connect(self._make_remove_handler(btn_del))
            self.table_items.setCellWidget(idx, 3, btn_del)

    def _make_remove_handler(self, btn):
        def _handler():
            for r in range(self.table_items.rowCount()):
                if self.table_items.cellWidget(r, 3) is btn:
                    if r < len(self.items_data):
                        self.items_data.pop(r)
                    self.refresh_table()
                    self.update_totals_display()
                    break
        return _handler

    def calculate_subtotal(self) -> float:
        return sum(item["amount_paise"] for item in self.items_data) / 100.0

    def round_to_nearest_10(self):
        sub = self.calculate_subtotal()
        if sub <= 0:
            return
        rem = sub % 10.0
        # If e.g. 198994 -> rem is 4 -> round off is -4 -> new total 198990
        round_adj = -rem if rem > 0 else 0.0
        self.txt_round_off.setText(f"{round_adj:.2f}")

    def round_to_nearest_100(self):
        sub = self.calculate_subtotal()
        if sub <= 0:
            return
        rem = sub % 100.0
        # If e.g. 198994 -> rem is 94 -> round off is -94 -> new total 198900
        round_adj = -rem if rem > 0 else 0.0
        self.txt_round_off.setText(f"{round_adj:.2f}")

    def set_full_cash(self):
        sub = self.calculate_subtotal()
        try:
            kasar = float(self.txt_round_off.text().strip() or 0)
        except ValueError:
            kasar = 0.0
        grand = max(0.0, sub + kasar)

        # Clear other payments and set full cash
        self.txt_pay_gold.clear()
        self.txt_pay_silver.clear()
        self.txt_pay_upi.clear()
        self.txt_pay_cheque.clear()
        self.txt_pay_cash.setText(f"{grand:.2f}".rstrip('0').rstrip('.'))

    def update_totals_display(self):
        sub = self.calculate_subtotal()
        self.lbl_sub_val.setText(format_inr(sub))

        # Kasar / Round Off
        try:
            kasar = float(self.txt_round_off.text().strip() or 0)
        except ValueError:
            kasar = 0.0

        grand = max(0.0, sub + kasar)
        self.lbl_grand_val.setText(format_inr(grand))

        # Sum of split payments
        def _get_val(txt_widget):
            try:
                v = float(txt_widget.text().strip() or 0)
                return max(0.0, v)
            except ValueError:
                return 0.0

        p_gold = _get_val(self.txt_pay_gold)
        p_silver = _get_val(self.txt_pay_silver)
        p_cash = _get_val(self.txt_pay_cash)
        p_upi = _get_val(self.txt_pay_upi)
        p_cheque = _get_val(self.txt_pay_cheque)

        total_paid = p_gold + p_silver + p_cash + p_upi + p_cheque
        due = max(0.0, grand - total_paid)

        self.lbl_paid_val.setText(format_inr(total_paid))
        self.lbl_due_val.setText(format_inr(due))
        self.lbl_due_val.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {'#DC2626' if due > 0 else '#16A34A'};")

    def save_kachu_entry(self, with_print: bool = False):
        if not self.items_data:
            QMessageBox.warning(self, "No Items", "ખાતામાં ઓછામાં ઓછી એક આઇટમ ઉમેરો (Please add at least one item).")
            self.txt_item_desc.setFocus()
            return

        name = self.txt_cust_name.text().strip()
        phone = self.txt_cust_phone.text().strip()
        addr = self.txt_cust_address.text().strip()

        if not name:
            QMessageBox.warning(self, "Missing Name", "કૃપા કરીને ગ્રાહકનું નામ લખો (Customer name is required).")
            self.txt_cust_name.setFocus()
            return

        if not phone or len(phone) < 10:
            QMessageBox.warning(self, "Missing Mobile", "કૃપા કરીને 10 આંકડાનો મોબાઇલ નંબર લખો (Valid 10-digit mobile required).")
            self.txt_cust_phone.setFocus()
            return

        # 1. Resolve or create customer
        cust_id = None
        if self.selected_customer:
            cust_id = self.selected_customer["id"]
            if addr and addr != self.selected_customer.get("address", ""):
                try:
                    update_customer(cust_id, name_gu=name, mobile=phone, address=addr)
                except Exception:
                    pass
        else:
            try:
                cust_id = add_customer(name_gu=name, name_en="", mobile=phone, address=addr)
            except Exception as e:
                existing = get_customer_by_mobile(phone)
                if existing:
                    cust_id = existing["id"]
                else:
                    QMessageBox.critical(self, "Customer Error", f"ગ્રાહક ઉમેરવામાં ભૂલ આવી: {e}")
                    return

        # 2. Extract Numbers
        sub_paise = sum(item["amount_paise"] for item in self.items_data)
        try:
            kasar_rs = float(self.txt_round_off.text().strip() or 0)
        except ValueError:
            kasar_rs = 0.0
        round_off_paise = int(round(kasar_rs * 100))

        def _get_paise(widget):
            try:
                v = float(widget.text().strip() or 0)
                return int(round(max(0.0, v) * 100))
            except ValueError:
                return 0

        p_gold_paise = _get_paise(self.txt_pay_gold)
        p_silver_paise = _get_paise(self.txt_pay_silver)
        p_cash_paise = _get_paise(self.txt_pay_cash)
        p_upi_paise = _get_paise(self.txt_pay_upi)
        p_cheque_paise = _get_paise(self.txt_pay_cheque)

        bill_date_str = self.date_bill.date().toString("yyyy-MM-dd")

        # Custom entry / bill number
        custom_no = None
        raw_no = self.txt_bill_no.text().strip()
        if raw_no.isdigit():
            custom_no = int(raw_no)

        try:
            bill_id = create_kachu_bill(
                customer_id=cust_id,
                bill_date=bill_date_str,
                items=self.items_data,
                round_off_paise=round_off_paise,
                cash_paise=p_cash_paise,
                gold_paise=p_gold_paise,
                silver_paise=p_silver_paise,
                upi_paise=p_upi_paise,
                cheque_paise=p_cheque_paise,
                custom_bill_no=custom_no
            )

            # Auto-send WhatsApp if bridge is connected
            total_paid_paise = p_gold_paise + p_silver_paise + p_cash_paise + p_upi_paise + p_cheque_paise
            grand_total_paise = max(0, sub_paise + round_off_paise)
            caption = get_caption(
                customer_name=name,
                bill_no=custom_no or bill_id,
                bill_date=bill_date_str,
                total=grand_total_paise,
                paid=total_paid_paise,
                is_paise=True
            )
            try:
                send_bill_async(phone, bill_id, custom_caption=caption)
            except Exception:
                pass

            if with_print:
                try:
                    print_or_pdf_bill(bill_id, self, show_print_dialog=True)
                except Exception as pe:
                    QMessageBox.warning(self, "Print Warning", f"બિલ સેવ થઈ ગયું પણ પ્રિન્ટ થઈ શક્યું નથી: {pe}")
            else:
                QMessageBox.information(self, "Success", f"✅ {t('msg_kachu_saved')}\n\nખાતા એન્ટ્રી નં: #{custom_no or bill_id}\nગ્રાહક: {name}")

            self.reset_form()

        except Exception as e:
            QMessageBox.critical(self, "Error Saving", f"ખાતું સાચવવામાં ક્ષતિ આવી:\n{e}")

    def retranslate_ui(self):
        self.btn_back.setText(t("btn_back"))
        self.lbl_screen_title.setText(t("kachu_title"))
        self.lbl_screen_subtitle.setText(t("kachu_subtitle"))
        self.lbl_badge.setText(t("kachu_badge"))
        self.lbl_card_cust_title.setText(t("card_customer_info"))
        self.lbl_bill_date.setText(t("lbl_bill_date"))
        self.lbl_bill_no.setText(t("lbl_kachu_bill_no"))
        self.lbl_cust_phone.setText(t("lbl_cust_mobile"))
        self.lbl_cust_name.setText(t("lbl_cust_name"))
        self.lbl_cust_addr.setText(t("lbl_cust_address"))
        self.lbl_card_item_title.setText(t("card_kachu_item_entry"))
        self.lbl_item_name.setText(t("lbl_kachu_item_name"))
        self.txt_item_desc.setPlaceholderText(t("ph_kachu_item_name"))
        self.lbl_item_amt.setText(t("lbl_kachu_item_amt"))
        self.btn_add_item.setText(t("btn_kachu_add_item"))
        self.setup_table_headers()
        self.lbl_sub_tag.setText(t("lbl_subtotal"))
        self.lbl_kasar_tag.setText(t("lbl_kachu_round_off"))
        self.btn_round_10.setText(t("btn_round_10"))
        self.btn_round_100.setText(t("btn_round_100"))
        self.lbl_grand_tag.setText(t("lbl_grand_total"))
        self.lbl_split_hdr.setText(t("lbl_split_pay_hdr"))
        self.lbl_gold.setText(t("lbl_pay_gold"))
        self.lbl_silver.setText(t("lbl_pay_silver"))
        self.lbl_cash.setText(t("lbl_pay_cash"))
        self.lbl_upi.setText(t("lbl_pay_upi"))
        self.lbl_cheque.setText(t("lbl_pay_cheque"))
        self.btn_full_cash.setText(t("btn_full_cash"))
        self.lbl_paid_tag.setText(t("lbl_paid_now"))
        self.lbl_due_tag.setText(t("lbl_balance_due"))
        self.btn_save_kachu.setText(t("btn_save_kachu"))
        self.btn_save_print.setText(t("btn_save_print_kachu"))
        self.update_totals_display()
