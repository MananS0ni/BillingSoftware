"""
bill_details_dialog.py - Full Past Bill Viewer & Re-printer Dialog.
Allows viewing all items, taxes, totals, and 1-click PDF reprinting of any past bill.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from translations import t
from database import get_bill_full_details, get_customer_balance
from print_manager import print_or_pdf_bill, export_bill_to_pdf
from whatsapp_manager import get_whatsapp_status, send_bill_async, ensure_bridge_running
from format_utils import get_caption, format_date_dmy
from app_paths import INVOICES_DIR

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
        lbl_title = QLabel(f"{t('lbl_bill_details_title')} #{self.bill_data['bill_no']}")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B1E19;")
        top_box.addWidget(lbl_title)

        top_box.addStretch()

        lbl_date = QLabel(f"📅 {format_date_dmy(self.bill_data['bill_date'])}")
        lbl_date.setStyleSheet("font-size: 14px; font-weight: bold; color: #6E7A75;")
        top_box.addWidget(lbl_date)
        layout.addLayout(top_box)

        # Customer Info Card
        card_cust = QFrame()
        card_cust.setObjectName("CardFrame")
        c_layout = QGridLayout(card_cust)
        c_layout.setContentsMargins(16, 12, 16, 12)

        c_layout.addWidget(QLabel(f"<b>{t('lbl_cust_name_colon')}</b>"), 0, 0)
        c_layout.addWidget(QLabel(self.bill_data["name_gu"]), 0, 1)

        c_layout.addWidget(QLabel(f"<b>{t('lbl_mobile_colon')}</b>"), 0, 2)
        c_layout.addWidget(QLabel(self.bill_data["mobile"]), 0, 3)

        c_layout.addWidget(QLabel(f"<b>{t('lbl_address_colon')}</b>"), 1, 0)
        c_layout.addWidget(QLabel(self.bill_data["address"] or "-"), 1, 1)

        c_layout.addWidget(QLabel(f"<b>{t('lbl_pay_mode')}</b>"), 1, 2)
        c_layout.addWidget(QLabel(self.bill_data["payment_mode"]), 1, 3)

        layout.addWidget(card_cust)

        # Items Table
        lbl_items = QLabel(t("lbl_items_purchased"))
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

        s_layout.addWidget(QLabel(f"{t('lbl_subtotal')}"), 0, 0)
        s_layout.addWidget(QLabel(f"₹ {subtotal:,.2f}"), 0, 1)

        s_layout.addWidget(QLabel(f"{t('lbl_cgst')}"), 1, 0)
        s_layout.addWidget(QLabel(f"₹ {cgst:,.2f}"), 1, 1)

        s_layout.addWidget(QLabel(f"{t('lbl_sgst')}"), 2, 0)
        s_layout.addWidget(QLabel(f"₹ {sgst:,.2f}"), 2, 1)

        s_layout.addWidget(QLabel(f"<b>{t('lbl_grand_total')}</b>"), 0, 2)
        lbl_grand = QLabel(f"<b>₹ {grand:,.2f}</b>")
        lbl_grand.setStyleSheet("font-size: 18px; color: #0B1E19;")
        s_layout.addWidget(lbl_grand, 0, 3)

        s_layout.addWidget(QLabel(f"{t('lbl_paid_now')}"), 1, 2)
        s_layout.addWidget(QLabel(f"₹ {paid:,.2f}"), 1, 3)

        s_layout.addWidget(QLabel(f"<b>{t('lbl_balance_due')}</b>"), 2, 2)
        lbl_due = QLabel(f"<b>₹ {due:,.2f}</b>")
        lbl_due.setStyleSheet("font-size: 16px; color: #DC2626;" if due > 0 else "color: #16A34A;")
        s_layout.addWidget(lbl_due, 2, 3)

        layout.addWidget(card_summary)

        # Action Buttons (WhatsApp / Reprint Bill / Close)
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_close = QPushButton(t("btn_close"))
        btn_close.setObjectName("SecondaryBtn")
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)

        btn_wa = QPushButton(t("btn_send_wa_bill"))
        btn_wa.setObjectName("GoldActionBtn")
        btn_wa.setStyleSheet("""
            QPushButton {
                background-color: #25D366; color: #FFFFFF;
                font-weight: bold; font-size: 13px;
                padding: 8px 18px; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #1DA851; }
            QPushButton:disabled { background-color: #88C9A0; color: #D0D0D0; }
        """)
        btn_wa.clicked.connect(self.send_to_whatsapp)
        btn_bar.addWidget(btn_wa)
        self.btn_wa = btn_wa

        btn_reprint = QPushButton(t("btn_reprint_pdf"))
        btn_reprint.setObjectName("GoldActionBtn")
        btn_reprint.clicked.connect(self.reprint_bill)
        btn_bar.addWidget(btn_reprint)

        layout.addLayout(btn_bar)

    def _build_bill_dict(self):
        """Builds the standard bill dict used for both printing and WhatsApp export."""
        cust_id = self.bill_data.get("customer_id")
        closing_bal = get_customer_balance(cust_id) if cust_id else 0
        due = self.bill_data.get("balance_paise", 0)
        opening_bal = closing_bal - due

        return {
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

    def reprint_bill(self):
        bill_dict_for_print = self._build_bill_dict()
        print_or_pdf_bill(bill_dict_for_print, self)

    def send_to_whatsapp(self):
        """Exports the bill as PDF and sends it to the customer's WhatsApp."""
        import os

        # 1. Validate mobile number
        mobile = self.bill_data.get("mobile", "").strip()
        if not mobile:
            QMessageBox.warning(self, "WhatsApp", t("msg_wa_no_mobile"))
            return

        # 2. Check WhatsApp bridge status
        status = get_whatsapp_status()
        if status.get("status") != "connected":
            QMessageBox.warning(self, "WhatsApp", t("msg_wa_not_linked"))
            return

        # 3. Confirmation dialog (Bug 15 fix pattern)
        bill_no = self.bill_data["bill_no"]
        grand = self.bill_data["grand_total_paise"] / 100.0
        confirm = QMessageBox.question(
            self, "WhatsApp",
            f"Send Bill #{bill_no} (₹{grand:,.2f}) to {mobile} on WhatsApp?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if confirm != QMessageBox.Yes:
            return

        # 4. Disable button to prevent double-send
        self.btn_wa.setEnabled(False)
        self.btn_wa.setText(t("msg_wa_sending"))

        # 5. Export PDF
        invoices_dir = INVOICES_DIR
        os.makedirs(invoices_dir, exist_ok=True)
        safe_name = self.bill_data["name_gu"].replace(" ", "_")[:30]
        pdf_filename = f"Bill_{bill_no}_{safe_name}.pdf"
        pdf_path = os.path.join(invoices_dir, pdf_filename)

        bill_dict = self._build_bill_dict()
        if not export_bill_to_pdf(bill_dict, pdf_path):
            QMessageBox.critical(self, "WhatsApp", "PDF export failed. Cannot send.")
            self.btn_wa.setEnabled(True)
            self.btn_wa.setText(t("btn_send_wa_bill"))
            return

        # 6. Build WhatsApp message (Standard Gujarati Template A or B)
        message = get_caption(
            customer_name=self.bill_data.get("name_gu", ""),
            bill_no=bill_no,
            bill_date=self.bill_data["bill_date"],
            total=self.bill_data["grand_total_paise"],
            paid=self.bill_data["paid_paise"],
            is_paise=True
        )

        # 7. Send async (non-blocking) with callback
        def _on_result(result):
            # QTimer.singleShot ensures UI updates happen on the main thread
            if result.get("success"):
                QTimer.singleShot(0, lambda: self._wa_send_success(bill_no))
            else:
                err = result.get("error", "Unknown error")
                QTimer.singleShot(0, lambda: self._wa_send_failed(err))

        ensure_bridge_running()
        send_bill_async(mobile, message, pdf_path, callback=_on_result)

    def _wa_send_success(self, bill_no):
        """Called on main thread after successful WhatsApp send."""
        self.btn_wa.setEnabled(True)
        self.btn_wa.setText(t("btn_send_wa_bill"))
        QMessageBox.information(
            self, "WhatsApp",
            t("msg_wa_bill_sent").replace("{bill_no}", str(bill_no))
        )

    def _wa_send_failed(self, error):
        """Called on main thread after failed WhatsApp send."""
        self.btn_wa.setEnabled(True)
        self.btn_wa.setText(t("btn_send_wa_bill"))
        QMessageBox.critical(
            self, "WhatsApp",
            t("msg_wa_bill_failed").replace("{error}", error)
        )

