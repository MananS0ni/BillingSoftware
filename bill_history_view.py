"""
bill_history_view.py - Complete Archive & History of All Past Billing Records.
Enables the jeweler to:
1. Filter by Quick Presets (All Time, Today, This Month, This Year) or Custom Date Range.
2. Search in real time by Bill #, Customer Name, Mobile, or Payment Mode.
3. View summary metrics for the filtered period (Total Bills, Total Sales, Paid, Pending Udhar).
4. View full historical table with 1-click actions:
   - 👁️ View Full Item Details (Weight, Rate, Making, GST, PAN, Aadhaar)
   - 🖨️ Reprint Tax Invoice
   - 📲 1-Click WhatsApp Resend to Customer & Father
Full 100% dynamic bilingual translation support.
"""

import os
import re
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate

from translations import t
from database import get_all_bills_history, get_bill_full_details
from format_utils import format_inr
from bill_details_dialog import BillDetailsDialog
from print_manager import print_or_pdf_bill, export_bill_to_pdf
from whatsapp_manager import send_bill_async, get_whatsapp_status
from settings_manager import get_owner_phone, is_owner_copy_enabled

class BillHistoryView(QWidget):
    def __init__(self, on_back_callback=None):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.active_preset = "all"
        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Top Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        if self.on_back_callback:
            self.btn_back = QPushButton(t("btn_back"))
            self.btn_back.setObjectName("SecondaryBtn")
            self.btn_back.clicked.connect(self.on_back_callback)
            header_row.addWidget(self.btn_back)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_title = QLabel(t("history_title"))
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0B1E19;")
        title_box.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel(t("history_subtitle"))
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #6E7A75;")
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box)

        header_row.addStretch()

        # Instant Search Box
        self.txt_search = QLineEdit()
        self.txt_search.setFixedWidth(340)
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setPlaceholderText(t("ph_search_history"))
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #12382C;
            }
        """)
        self.txt_search.textChanged.connect(self.load_history)
        header_row.addWidget(self.txt_search)

        layout.addLayout(header_row)

        # 2. Date Filter Bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1.5px solid #E8E4DC;
                border-radius: 8px;
                padding: 8px 14px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(4, 4, 4, 4)
        filter_layout.setSpacing(8)

        # Preset filter buttons
        self.btn_all = QPushButton(t("btn_filter_all"))
        self.btn_all.setObjectName("SecondaryBtn")
        self.btn_all.clicked.connect(lambda: self.set_preset("all"))
        filter_layout.addWidget(self.btn_all)

        self.btn_today = QPushButton(t("btn_filter_today"))
        self.btn_today.setObjectName("SecondaryBtn")
        self.btn_today.clicked.connect(lambda: self.set_preset("today"))
        filter_layout.addWidget(self.btn_today)

        self.btn_month = QPushButton(t("btn_filter_month"))
        self.btn_month.setObjectName("SecondaryBtn")
        self.btn_month.clicked.connect(lambda: self.set_preset("month"))
        filter_layout.addWidget(self.btn_month)

        self.btn_year = QPushButton(t("btn_filter_year"))
        self.btn_year.setObjectName("SecondaryBtn")
        self.btn_year.clicked.connect(lambda: self.set_preset("year"))
        filter_layout.addWidget(self.btn_year)

        filter_layout.addSpacing(16)
        filter_layout.addWidget(QFrame(frameShape=QFrame.VLine))
        filter_layout.addSpacing(16)

        # Custom date pickers
        self.lbl_from = QLabel(t("lbl_date_from"))
        self.lbl_from.setStyleSheet("font-weight: bold; color: #12382C; font-size: 13px;")
        filter_layout.addWidget(self.lbl_from)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumWidth(125)
        self.date_from.setStyleSheet("padding: 4px 8px; font-weight: bold; font-size: 13px; background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px;")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        filter_layout.addWidget(self.date_from)

        self.lbl_to = QLabel(t("lbl_date_to"))
        self.lbl_to.setStyleSheet("font-weight: bold; color: #12382C; font-size: 13px;")
        filter_layout.addWidget(self.lbl_to)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumWidth(125)
        self.date_to.setStyleSheet("padding: 4px 8px; font-weight: bold; font-size: 13px; background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px;")
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to)

        self.btn_apply = QPushButton(t("btn_apply_filter"))
        self.btn_apply.setObjectName("PrimaryBtn")
        self.btn_apply.setCursor(Qt.PointingHandCursor)
        self.btn_apply.setStyleSheet("padding: 6px 16px; font-weight: bold;")
        self.btn_apply.clicked.connect(lambda: self.set_preset("custom"))
        filter_layout.addWidget(self.btn_apply)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # 3. Summary Metric Cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)

        self.card_bills = self.create_metric_card(t("stat_hist_total_bills"), "0", "#0B1E19")
        self.card_sales = self.create_metric_card(t("stat_hist_total_sales"), "₹ 0.00", "#12382C")
        self.card_paid = self.create_metric_card(t("stat_hist_total_paid"), "₹ 0.00", "#16A34A")
        self.card_due = self.create_metric_card(t("stat_hist_total_due"), "₹ 0.00", "#DC2626")

        self.cards_layout.addWidget(self.card_bills)
        self.cards_layout.addWidget(self.card_sales)
        self.cards_layout.addWidget(self.card_paid)
        self.cards_layout.addWidget(self.card_due)
        layout.addLayout(self.cards_layout)

        # 4. Historical Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.setup_table_headers()

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Sr
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Bill No
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Date
        h.setSectionResizeMode(3, QHeaderView.Interactive)      # Customer
        self.table.setColumnWidth(3, 270)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Grand Total
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Paid
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Balance
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents) # Mode
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents) # Action

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.table)

        self.update_preset_button_styles()

    def create_metric_card(self, title: str, initial_val: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1.5px solid #E8E4DC;
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(4)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; font-weight: bold; color: #6E7A75;")
        c_layout.addWidget(lbl_t)

        lbl_v = QLabel(initial_val)
        lbl_v.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        c_layout.addWidget(lbl_v)

        card.lbl_title = lbl_t
        card.lbl_val = lbl_v
        return card

    def setup_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            t("th_hist_sr"),
            t("th_hist_bill_no"),
            t("th_hist_date"),
            t("th_hist_customer"),
            t("th_hist_grand"),
            t("th_hist_paid"),
            t("th_hist_due"),
            t("th_hist_mode"),
            t("th_hist_action")
        ])

    def set_preset(self, preset: str):
        self.active_preset = preset
        today = QDate.currentDate()

        if preset == "today":
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif preset == "month":
            first_of_month = QDate(today.year(), today.month(), 1)
            self.date_from.setDate(first_of_month)
            self.date_to.setDate(today)
        elif preset == "year":
            first_of_year = QDate(today.year(), 1, 1)
            self.date_from.setDate(first_of_year)
            self.date_to.setDate(today)

        self.update_preset_button_styles()
        self.load_history()

    def update_preset_button_styles(self):
        active_style = "background-color: #12382C; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 6px 14px; min-width: 90px;"
        inactive_style = "background-color: #F8F7F4; color: #12382C; font-weight: 500; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 6px 14px; min-width: 90px;"

        self.btn_all.setStyleSheet(active_style if self.active_preset == "all" else inactive_style)
        self.btn_today.setStyleSheet(active_style if self.active_preset == "today" else inactive_style)
        self.btn_month.setStyleSheet(active_style if self.active_preset == "month" else inactive_style)
        self.btn_year.setStyleSheet(active_style if self.active_preset == "year" else inactive_style)

    def load_history(self):
        start_date = None
        end_date = None

        if self.active_preset != "all":
            start_date = self.date_from.date().toString("yyyy-MM-dd")
            end_date = self.date_to.date().toString("yyyy-MM-dd")

        keyword = self.txt_search.text().strip()
        bills = get_all_bills_history(start_date=start_date, end_date=end_date, keyword=keyword)

        # Update summary metrics
        total_bills = len(bills)
        total_sales = sum(b["grand_total_paise"] for b in bills)
        total_paid = sum(b["paid_paise"] for b in bills)
        total_due = sum(b["balance_paise"] for b in bills)

        self.card_bills.lbl_val.setText(str(total_bills))
        self.card_sales.lbl_val.setText(format_inr(total_sales, is_paise=True))
        self.card_paid.lbl_val.setText(format_inr(total_paid, is_paise=True))
        self.card_due.lbl_val.setText(format_inr(total_due, is_paise=True))

        # Populate table
        self.table.setRowCount(0)
        for row_idx, b in enumerate(bills):
            self.table.insertRow(row_idx)

            # 0. Sr
            item_sr = QTableWidgetItem(str(row_idx + 1))
            item_sr.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, item_sr)

            # 1. Bill No
            item_no = QTableWidgetItem(f"#{b['bill_no']}")
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setForeground(Qt.darkGreen)
            self.table.setItem(row_idx, 1, item_no)

            # 2. Date
            item_dt = QTableWidgetItem(b["bill_date"])
            item_dt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, item_dt)

            # 3. Customer
            cust_text = b["name_gu"]
            if b.get("name_en"):
                cust_text += f" ({b['name_en']})"
            cust_text += f" - {b['mobile']}"
            self.table.setItem(row_idx, 3, QTableWidgetItem(cust_text))

            # 4. Grand Total
            item_gt = QTableWidgetItem(format_inr(b["grand_total_paise"], is_paise=True))
            item_gt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 4, item_gt)

            # 5. Paid
            item_pd = QTableWidgetItem(format_inr(b["paid_paise"], is_paise=True))
            item_pd.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 5, item_pd)

            # 6. Balance Due (Udhar)
            bal = b["balance_paise"]
            item_bal = QTableWidgetItem(format_inr(bal, is_paise=True))
            item_bal.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_bal.setForeground(Qt.red if bal > 0 else Qt.darkGreen)
            self.table.setItem(row_idx, 6, item_bal)

            # 7. Payment Mode
            mode_str = b.get("payment_mode", "CASH")
            if b.get("payment_ref"):
                mode_str += f" ({b['payment_ref']})"
            self.table.setItem(row_idx, 7, QTableWidgetItem(mode_str))

            # 8. Action Buttons Container
            action_widget = QWidget()
            a_layout = QHBoxLayout(action_widget)
            a_layout.setContentsMargins(4, 2, 4, 2)
            a_layout.setSpacing(6)

            # View Details Button
            btn_view = QPushButton("👁️ વિગત")
            btn_view.setStyleSheet("""
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
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.clicked.connect(lambda _, b_id=b["id"]: BillDetailsDialog(b_id, self).exec())
            a_layout.addWidget(btn_view)

            # Print Button
            btn_print = QPushButton("🖨️ પ્રિન્ટ")
            btn_print.setStyleSheet("""
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
            btn_print.setCursor(Qt.PointingHandCursor)
            btn_print.clicked.connect(lambda _, b_id=b["id"]: self.on_print_bill(b_id))
            a_layout.addWidget(btn_print)

            # WhatsApp Resend Button
            btn_wa = QPushButton("📲 WA")
            btn_wa.setStyleSheet("""
                QPushButton {
                    background-color: #DCFCE7;
                    color: #166534;
                    border: 1px solid #86EFAC;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #BBF7D0; }
            """)
            btn_wa.setCursor(Qt.PointingHandCursor)
            btn_wa.clicked.connect(lambda _, b_id=b["id"]: self.on_resend_whatsapp(b_id))
            a_layout.addWidget(btn_wa)

            self.table.setCellWidget(row_idx, 8, action_widget)

    def on_print_bill(self, bill_id: int):
        bill_data = get_bill_full_details(bill_id)
        if bill_data:
            print_or_pdf_bill(bill_data, self)

    def on_resend_whatsapp(self, bill_id: int):
        bill_data = get_bill_full_details(bill_id)
        if not bill_data:
            QMessageBox.warning(self, "Error", "Bill not found.")
            return

        wa_status = get_whatsapp_status()
        if wa_status.get("status") != "connected":
            QMessageBox.warning(
                self, "WhatsApp જોડેલ નથી",
                "WhatsApp કનેક્ટ થયેલું નથી. ઉપર જમણી બાજુ 'Connect WhatsApp' બટન દબાવીને ફોન જોડો."
            )
            return

        cust_mobile = bill_data.get("mobile", "")
        cust_name = bill_data.get("name_gu", "") or bill_data.get("name_en", "Customer")
        grand = bill_data["grand_total_paise"]
        paid = bill_data["paid_paise"]
        due = bill_data["balance_paise"]

        invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
        os.makedirs(invoices_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_\u0A80-\u0AFF]', '_', cust_name)
        pdf_path = os.path.join(invoices_dir, f"Invoice_Bill_{bill_data['bill_no']}_{safe_name}.pdf")
        export_bill_to_pdf(bill_data, pdf_path)

        grand_fmt = format_inr(grand, is_paise=True)
        paid_fmt = format_inr(paid, is_paise=True)
        due_fmt = format_inr(due, is_paise=True)

        msg_body = (
            f"નમસ્તે {cust_name} શેઠ,\n\n"
            f"આપનું સોની નટવરલાલ હિંમતલાલ (Soni Natvarlal Himmatlal) નું ટેક્સ ઇન્વોઇસ નં. #{bill_data['bill_no']} સામેલ છે.\n"
            f"• તારીખ: {bill_data['bill_date']}\n"
            f"• કુલ રકમ: {grand_fmt}\n"
            f"• ચૂકવેલ રકમ: {paid_fmt}\n"
            f"• બાકી ઉધાર રકમ: {due_fmt}\n\n"
            f"આપની મુલાકાત બદલ ખૂબ ખૂબ આભાર! 🪙\n\n"
            f"સોની નટવરલાલ હિંમતલાલ\n"
            f"Soni Natvarlal Himmatlal"
        )

        send_bill_async(cust_mobile, msg_body, pdf_path)

        if is_owner_copy_enabled():
            owner_num = get_owner_phone()
            if owner_num:
                owner_msg = (
                    f"👑 [સોની નટવરલાલ હિંમતલાલ - ફરી મોકલેલ બિલ #{bill_data['bill_no']}]\n"
                    f"ગ્રાહક: {cust_name} ({cust_mobile})\n"
                    f"કુલ રકમ: {grand_fmt} | જમા: {paid_fmt} | બાકી ઉધાર: {due_fmt}"
                )
                send_bill_async(owner_num, owner_msg, pdf_path)

        QMessageBox.information(
            self, "WhatsApp મોકલાયું",
            f"બિલ નં. #{bill_data['bill_no']} ગ્રાહક ({cust_mobile}) અને પિતાશ્રીને સફળતાપૂર્વક ફરીથી મોકલવામાં આવ્યું છે!"
        )

    def update_translations(self):
        self.lbl_title.setText(t("history_title"))
        self.lbl_subtitle.setText(t("history_subtitle"))
        self.txt_search.setPlaceholderText(t("ph_search_history"))
        self.btn_all.setText(t("btn_filter_all"))
        self.btn_today.setText(t("btn_filter_today"))
        self.btn_month.setText(t("btn_filter_month"))
        self.btn_year.setText(t("btn_filter_year"))
        self.lbl_from.setText(t("lbl_date_from"))
        self.lbl_to.setText(t("lbl_date_to"))
        self.btn_apply.setText(t("btn_apply_filter"))

        self.card_bills.lbl_title.setText(t("stat_hist_total_bills"))
        self.card_sales.lbl_title.setText(t("stat_hist_total_sales"))
        self.card_paid.lbl_title.setText(t("stat_hist_total_paid"))
        self.card_due.lbl_title.setText(t("stat_hist_total_due"))

        if hasattr(self, "btn_back"):
            self.btn_back.setText(t("btn_back"))

        self.setup_table_headers()
        self.load_history()
