"""
bill_details_dialog.py - Full Past Bill Viewer & Re-printer Dialog.
Allows viewing all items, taxes, totals, and 1-click PDF reprinting of any past bill.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt
from translations import t
from database import get_bill_full_details, get_customer_balance
from print_manager import print_or_pdf_bill

class BillDetailsDialog(QDialog):
    def __init__(self, bill_id: int, parent=None):
        super().__init__(parent)
        self.bill_id = bill_id
        self.bill_data = get_bill_full_details(bill_id)
        self.setWindowTitle(f"Bill Details - #{self.bill_data['bill_no'] if self.bill_data else bill_id}")
        self.resize(750, 600)
        self.init_ui()

    def init_ui(self):
        if not self.bill_data:
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Bill not found in database."))
            return

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header Badge
        top_box = QHBoxLayout()
        lbl_title = QLabel(f"Tax Invoice #{self.bill_data['bill_no']}")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B1E19;")
        top_box.addWidget(lbl_title)

        top_box.addStretch()

        lbl_date = QLabel(f"📅 {self.bill_data['bill_date']}")
        lbl_date.setStyleSheet("font-size: 14px; font-weight: bold; color: #6E7A75;")
        top_box.addWidget(lbl_date)
        layout.addLayout(top_box)

        # Customer Info Card
        card_cust = QFrame()
        card_cust.setObjectName("CardFrame")
        c_layout = QGridLayout(card_cust)
        c_layout.setContentsMargins(16, 12, 16, 12)

        c_layout.addWidget(QLabel("<b>Customer Name:</b>"), 0, 0)
        c_layout.addWidget(QLabel(self.bill_data["name_gu"]), 0, 1)

        c_layout.addWidget(QLabel("<b>Mobile Number:</b>"), 0, 2)
        c_layout.addWidget(QLabel(self.bill_data["mobile"]), 0, 3)

        c_layout.addWidget(QLabel("<b>Address:</b>"), 1, 0)
        c_layout.addWidget(QLabel(self.bill_data["address"] or "-"), 1, 1)

        c_layout.addWidget(QLabel("<b>Payment Mode:</b>"), 1, 2)
        c_layout.addWidget(QLabel(self.bill_data["payment_mode"]), 1, 3)

        layout.addWidget(card_cust)

        # Items Table
        lbl_items = QLabel("Items Purchased (દાગીનાની વિગત):")
        lbl_items.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(lbl_items)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            t("th_desc"), t("th_hsn"), t("th_weight"), t("th_rate"), t("th_amount")
        ])
        h = table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        for row_idx, item in enumerate(self.bill_data.get("items", [])):
            table.insertRow(row_idx)
            table.setItem(row_idx, 0, QTableWidgetItem(item["description"]))
            table.setItem(row_idx, 1, QTableWidgetItem(item.get("hsn_code", "") or "-"))
            
            wt = item["weight_mg"] / 1000.0
            table.setItem(row_idx, 2, QTableWidgetItem(f"{wt:.3f} g"))

            rate = item["rate_paise"] / 100.0
            table.setItem(row_idx, 3, QTableWidgetItem(f"₹ {rate:,.2f}"))

            amt = item["amount_paise"] / 100.0
            table.setItem(row_idx, 4, QTableWidgetItem(f"₹ {amt:,.2f}"))

        layout.addWidget(table)

        # Financial Summary Card
        card_summary = QFrame()
        card_summary.setObjectName("CardFrame")
        s_layout = QGridLayout(card_summary)
        s_layout.setContentsMargins(16, 12, 16, 12)

        subtotal = self.bill_data["subtotal_paise"] / 100.0
        cgst = self.bill_data["cgst_paise"] / 100.0
        sgst = self.bill_data["sgst_paise"] / 100.0
        grand = self.bill_data["grand_total_paise"] / 100.0
        paid = self.bill_data["paid_paise"] / 100.0
        due = self.bill_data["balance_paise"] / 100.0

        s_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        s_layout.addWidget(QLabel(f"₹ {subtotal:,.2f}"), 0, 1)

        s_layout.addWidget(QLabel("CGST (1.5%):"), 1, 0)
        s_layout.addWidget(QLabel(f"₹ {cgst:,.2f}"), 1, 1)

        s_layout.addWidget(QLabel("SGST (1.5%):"), 2, 0)
        s_layout.addWidget(QLabel(f"₹ {sgst:,.2f}"), 2, 1)

        s_layout.addWidget(QLabel("<b>Grand Total:</b>"), 0, 2)
        lbl_grand = QLabel(f"<b>₹ {grand:,.2f}</b>")
        lbl_grand.setStyleSheet("font-size: 18px; color: #0B1E19;")
        s_layout.addWidget(lbl_grand, 0, 3)

        s_layout.addWidget(QLabel("Paid Amount:"), 1, 2)
        s_layout.addWidget(QLabel(f"₹ {paid:,.2f}"), 1, 3)

        s_layout.addWidget(QLabel("<b>Balance Due (Udhar):</b>"), 2, 2)
        lbl_due = QLabel(f"<b>₹ {due:,.2f}</b>")
        lbl_due.setStyleSheet("font-size: 16px; color: #DC2626;" if due > 0 else "color: #16A34A;")
        s_layout.addWidget(lbl_due, 2, 3)

        layout.addWidget(card_summary)

        # Action Buttons (Reprint Bill / Close)
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("SecondaryBtn")
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)

        btn_reprint = QPushButton("🖨️ Re-Print / Save PDF")
        btn_reprint.setObjectName("GoldActionBtn")
        btn_reprint.clicked.connect(self.reprint_bill)
        btn_bar.addWidget(btn_reprint)

        layout.addLayout(btn_bar)

    def reprint_bill(self):
        cust_id = self.bill_data.get("customer_id")
        closing_bal = get_customer_balance(cust_id) if cust_id else 0
        due = self.bill_data.get("balance_paise", 0)
        opening_bal = closing_bal - due

        bill_dict_for_print = {
            "bill_no": self.bill_data["bill_no"],
            "book_no": self.bill_data.get("book_no", 1),
            "bill_date": self.bill_data["bill_date"],
            "customer_name": self.bill_data["name_gu"],
            "name_gu": self.bill_data["name_gu"],
            "name_en": self.bill_data.get("name_en", ""),
            "customer_mobile": self.bill_data["mobile"],
            "customer_address": self.bill_data["address"],
            "gstin": self.bill_data.get("gstin", ""),
            "pan_no": self.bill_data.get("pan_no", ""),
            "aadhaar_no": self.bill_data.get("aadhaar_no", ""),
            "items": self.bill_data["items"],
            "subtotal_paise": self.bill_data["subtotal_paise"],
            "cgst_paise": self.bill_data["cgst_paise"],
            "sgst_paise": self.bill_data["sgst_paise"],
            "grand_total_paise": self.bill_data["grand_total_paise"],
            "paid_paise": self.bill_data["paid_paise"],
            "balance_paise": self.bill_data["balance_paise"],
            "payment_mode": self.bill_data["payment_mode"],
            "payment_ref": self.bill_data.get("payment_ref", ""),
            "opening_balance_paise": opening_bal,
            "closing_balance_paise": closing_bal
        }
        print_or_pdf_bill(bill_dict_for_print, self)

