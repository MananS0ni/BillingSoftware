"""
purchases_view.py - Wholesale Purchases & URD Customer Old Gold Register.
Handles:
1. URD Customer Old Gold / Scrap Purchases with Aadhaar UID tracking, Purity Touch %, and 5% GST deduction.
2. Wholesale Dealer Inward Purchases with GST Input Tax Credit (ITC).
3. Seamless integration with Customer Khata and Dashboard GST Tax Center.
4. One-click 1-page A5 URD Purchase Voucher printing.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QMessageBox, QComboBox, QFrame, QDateEdit,
    QScrollArea
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from datetime import datetime

from translations import t, get_language
from database import (
    add_purchase, add_urd_purchase, get_purchases, delete_purchase,
    get_purchase_by_id, get_next_urd_voucher_number, get_all_customers
)
from format_utils import format_inr, format_date_dmy
from print_manager import print_or_pdf_urd_voucher

# ----------------- URD Customer Old Gold Purchase Dialog -----------------

class AddURDPurchaseDialog(QDialog):
    """
    Dedicated dialog for purchasing old gold/jewelry from unregistered retail customers (URD).
    Captures Customer KYC (Aadhaar UID), Gross Weight, Touch/Purity %, Rate, and 5% GST deduction.
    100% Bilingual in both English and Gujarati.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("urd_dialog_window_title"))
        self.resize(680, 740)
        self.setMinimumWidth(660)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F7F4;
                font-family: 'Noto Sans Gujarati', 'Tinos', 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                background-color: transparent;
                font-size: 13px;
                color: #2A1A1A;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #FFFFFF;
                border: 1.2px solid #B9A0A0;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                color: #2A1A1A;
            }
            QPushButton#SecondaryBtn {
                background-color: #E2E8F0;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #CBD5E1;
                color: #0F172A;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1.5px solid #6B2433;
                background-color: #FFFAF6;
            }
            QPushButton#SecondaryBtn {
                background-color: #E2E8F0;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #CBD5E1;
                color: #0F172A;
            }
        """)
        self.customers_list = get_all_customers()
        self.init_ui()
        self.calculate_totals()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(10)

        # Title Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background: #6B2433; border-radius: 6px; padding: 6px 12px;")
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        title = QLabel(t("urd_banner_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        sub = QLabel(t("urd_banner_sub"))
        sub.setStyleSheet("font-size: 11px; color: #F1D9CF;")
        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        main_layout.addWidget(header_frame)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Voucher Number & Date (Side by Side)
        top_row = QHBoxLayout()
        self.txt_voucher = QLineEdit()
        next_no = get_next_urd_voucher_number()
        self.txt_voucher.setText(f"URD-{next_no}")
        self.txt_voucher.setPlaceholderText("URD-1")

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setDisplayFormat("dd-MM-yyyy")

        top_row.addWidget(self.txt_voucher)
        top_row.addWidget(QLabel(t("lbl_date_colon")))
        top_row.addWidget(self.dt_date)
        form.addRow(t("lbl_voucher_no_date"), top_row)

        # 2. Customer Search / Selection
        self.cmb_customer = QComboBox()
        self.cmb_customer.setEditable(True)
        self.cmb_customer.addItem(t("ph_select_customer"), None)
        for c in self.customers_list:
            display_text = f"{c['name_gu'] or c['name_en']} ({c['mobile']})"
            self.cmb_customer.addItem(display_text, c)
        self.cmb_customer.currentIndexChanged.connect(self.on_customer_selected)
        form.addRow(t("lbl_select_customer"), self.cmb_customer)

        # 3. Customer Name & Aadhaar UID
        cust_row = QHBoxLayout()
        self.txt_cust_name = QLineEdit()
        self.txt_cust_name.setPlaceholderText(t("ph_cust_name_input"))

        self.txt_uid = QLineEdit()
        self.txt_uid.setMaxLength(14)
        self.txt_uid.setPlaceholderText(t("ph_cust_uid_input"))
        self.txt_uid.setStyleSheet("font-family: monospace; font-weight: bold;")

        cust_row.addWidget(self.txt_cust_name)
        cust_row.addWidget(self.txt_uid)
        form.addRow(t("lbl_name_uid"), cust_row)

        # 4. Mobile & Address
        contact_row = QHBoxLayout()
        self.txt_mobile = QLineEdit()
        self.txt_mobile.setPlaceholderText(t("ph_cust_mobile_input"))
        self.txt_mobile.setMaxLength(10)

        self.txt_address = QLineEdit()
        self.txt_address.setPlaceholderText(t("ph_cust_addr_input"))

        contact_row.addWidget(self.txt_mobile)
        contact_row.addWidget(self.txt_address)
        form.addRow(t("lbl_mobile_address"), contact_row)

        # 5. Item Description
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText(t("ph_urd_item_desc"))
        form.addRow(t("lbl_item_details_colon"), self.txt_desc)

        # 6. Weight & Touch Purity (Side by Side)
        wt_row = QHBoxLayout()
        self.txt_weight = QLineEdit()
        self.txt_weight.setPlaceholderText("15.500")
        self.txt_weight.textChanged.connect(self.calculate_totals)

        self.txt_touch = QLineEdit("91.6")
        self.txt_touch.setPlaceholderText("91.6")
        self.txt_touch.textChanged.connect(self.calculate_totals)

        self.lbl_fine_wt = QLabel(f"{t('lbl_fine_calc')}: 0.000 g")
        self.lbl_fine_wt.setStyleSheet("font-weight: bold; color: #6B2433; padding: 0 4px;")

        wt_row.addWidget(self.txt_weight)
        wt_row.addWidget(QLabel(t("lbl_touch_pct")))
        wt_row.addWidget(self.txt_touch)
        wt_row.addWidget(self.lbl_fine_wt)
        form.addRow(t("lbl_gross_touch"), wt_row)

        # 7. Buy Rate per Gram with 1-Click Live Market Auto-Fill
        rate_row = QHBoxLayout()
        self.txt_rate = QLineEdit()
        self.txt_rate.setPlaceholderText(t("ph_buy_rate"))
        self.txt_rate.textChanged.connect(self.calculate_totals)

        self.btn_live_rate = QPushButton(t("btn_live_rate"))
        self.btn_live_rate.setCursor(Qt.PointingHandCursor)
        self.btn_live_rate.setToolTip("Click to calculate live rate from today's bullion market based on purity touch")
        self.btn_live_rate.setStyleSheet("""
            QPushButton {
                background: #FEF3C7;
                color: #92400E;
                font-size: 11px;
                font-weight: bold;
                border: 1.2px solid #F59E0B;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #FDE68A;
                color: #78350F;
            }
        """)
        self.btn_live_rate.clicked.connect(self.apply_live_buy_rate)

        rate_row.addWidget(self.txt_rate, stretch=3)
        rate_row.addWidget(self.btn_live_rate, stretch=1)
        form.addRow(t("lbl_buy_rate_colon"), rate_row)

        # 8. GST Rate & Treatment
        gst_row = QHBoxLayout()
        self.cmb_gst = QComboBox()
        self.cmb_gst.addItem(t("opt_gst_5_default"), 5.0)
        self.cmb_gst.addItem(t("opt_gst_3_gold"), 3.0)
        self.cmb_gst.addItem(t("opt_gst_0_nil"), 0.0)
        self.cmb_gst.currentIndexChanged.connect(self.calculate_totals)

        self.cmb_treatment = QComboBox()
        self.cmb_treatment.addItem(t("opt_treatment_deduct"), "DEDUCTED")
        self.cmb_treatment.addItem(t("opt_treatment_add"), "ADDED")
        self.cmb_treatment.currentIndexChanged.connect(self.calculate_totals)

        gst_row.addWidget(self.cmb_gst)
        gst_row.addWidget(self.cmb_treatment)
        form.addRow(t("lbl_gst_method"), gst_row)

        # 9. Payment Mode & Ref
        pay_row = QHBoxLayout()
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["CASH", "BANK / UPI", "CHEQUE", "KHATA"])

        self.txt_ref = QLineEdit()
        self.txt_ref.setPlaceholderText(t("ph_payment_ref_notes"))

        pay_row.addWidget(self.cmb_mode)
        pay_row.addWidget(self.txt_ref)
        form.addRow(t("lbl_pay_mode_notes"), pay_row)

        main_layout.addLayout(form)

        # 10. Financial Summary Card
        calc_box = QFrame()
        calc_box.setStyleSheet("background-color: #FFFFFF; border: 1.5px solid #6B2433; border-radius: 8px; padding: 10px;")
        cb_layout = QVBoxLayout(calc_box)
        cb_layout.setSpacing(4)

        self.lbl_subtotal = QLabel(f"{t('lbl_gross_val_card')}: ₹ 0.00")
        self.lbl_subtotal.setStyleSheet("font-size: 13px; color: #2A1A1A;")
        cb_layout.addWidget(self.lbl_subtotal)

        self.lbl_gst = QLabel(f"{t('lbl_gst_deduct_card')}: (-) ₹ 0.00")
        self.lbl_gst.setStyleSheet("font-size: 13px; font-weight: bold; color: #DC2626;")
        cb_layout.addWidget(self.lbl_gst)

        self.lbl_net_payout = QLabel(f"{t('lbl_net_payout_card')}: ₹ 0.00")
        self.lbl_net_payout.setStyleSheet("font-size: 16px; font-weight: bold; color: #16A34A; background: #F6E7DF; padding: 4px 8px; border-radius: 4px;")
        cb_layout.addWidget(self.lbl_net_payout)

        main_layout.addWidget(calc_box)

        # Action Buttons
        btns = QHBoxLayout()
        self.btn_cancel = QPushButton(t("btn_cancel_short"))
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save_only = QPushButton(t("btn_save_only_short"))
        self.btn_save_only.setObjectName("SecondaryBtn")
        self.btn_save_only.clicked.connect(lambda: self.save(print_voucher=False))

        self.btn_save_print = QPushButton(t("btn_save_and_print_voucher"))
        self.btn_save_print.setObjectName("GoldActionBtn")
        self.btn_save_print.setStyleSheet("background-color: #6B2433; color: #FFFFFF; font-weight: bold; padding: 8px 14px; border-radius: 4px;")
        self.btn_save_print.clicked.connect(lambda: self.save(print_voucher=True))

        btns.addWidget(self.btn_cancel)
        btns.addStretch()
        btns.addWidget(self.btn_save_only)
        btns.addWidget(self.btn_save_print)
        main_layout.addLayout(btns)

    def apply_live_buy_rate(self):
        try:
            from rates_manager import get_rates_manager
            rm = get_rates_manager()
            rates = rm.get_latest_rates()
            desc = (self.txt_desc.text() or "").lower()
            if any(w in desc for w in ["silver", "ચાંદી", "chandi", "payal", "પાયલ"]):
                base_rate = rates.get("silver_lagdi_1g", 155.0)
            else:
                base_rate = rates.get("gold_24k_1g", 12880.0)
            touch = float(self.txt_touch.text().strip() or 100.0)
            calc_rate = round(base_rate * (touch / 100.0), 2)
            self.txt_rate.setText(str(calc_rate))
            if not rm.is_live():
                QMessageBox.warning(
                    self, "ઓફલાઇન ભાવ / Offline Rate",
                    "⚠️ ઇન્ટરનેટ કનેક્શન ન હોવાથી સેવ કરેલો જૂનો ભાવ મુકાયો છે. કૃપા કરીને ચકાસો.\n"
                    "(Applied cached/offline rate. Please verify.)"
                )
        except Exception:
            pass

    def on_customer_selected(self, index):
        data = self.cmb_customer.currentData()
        if data:
            self.txt_cust_name.setText(data.get("name_gu") or data.get("name_en", ""))
            self.txt_mobile.setText(data.get("mobile", ""))
            self.txt_address.setText(data.get("address", ""))
            self.txt_uid.setText(data.get("aadhaar_no", ""))

    def calculate_totals(self):
        try:
            wt = float(self.txt_weight.text().strip() or 0)
            touch = float(self.txt_touch.text().strip() or 100.0)
            fine_wt = round(wt * (touch / 100.0), 3)
            self.lbl_fine_wt.setText(f"{t('lbl_fine_calc')}: {fine_wt:.3f} g")

            rate = float(self.txt_rate.text().strip() or 0)
            subtotal = round(fine_wt * rate, 2)

            gst_rate = self.cmb_gst.currentData() or 0.0
            gst = round(subtotal * (gst_rate / 100.0), 2)

            treatment = self.cmb_treatment.currentData()
            if treatment == "DEDUCTED":
                net_payout = round(subtotal - gst, 2)
                gst_text = f"{gst_rate:.1f}% {t('lbl_gst_deduct_card')}: (-) {format_inr(gst)}"
                self.lbl_gst.setStyleSheet("font-size: 13px; font-weight: bold; color: #DC2626;")
            else:
                net_payout = round(subtotal + gst, 2)
                gst_text = f"{gst_rate:.1f}% {t('lbl_gst_added_card')}: (+) {format_inr(gst)}"
                self.lbl_gst.setStyleSheet("font-size: 13px; font-weight: bold; color: #16A34A;")

            self.lbl_subtotal.setText(f"{t('lbl_gross_val_card')}: {format_inr(subtotal)}")
            self.lbl_gst.setText(gst_text)
            self.lbl_net_payout.setText(f"{t('lbl_net_payout_card')}: {format_inr(net_payout)}")
        except Exception:
            pass

    def save(self, print_voucher: bool = False):
        cust_name = self.txt_cust_name.text().strip()
        uid = self.txt_uid.text().strip()
        desc = self.txt_desc.text().strip()
        voucher_no = self.txt_voucher.text().strip()

        if not cust_name:
            err = "Please enter customer name." if get_language() == "en" else "કૃપા કરીને ગ્રાહકનું નામ દાખલ કરો."
            QMessageBox.warning(self, "Attention", err)
            return
        if not desc:
            err = "Please enter old gold / item description." if get_language() == "en" else "કૃપા કરીને જૂના સોના / વસ્તુની વિગત દાખલ કરો."
            QMessageBox.warning(self, "Attention", err)
            return

        try:
            wt = float(self.txt_weight.text().strip())
            touch = float(self.txt_touch.text().strip() or 100.0)
            rate = float(self.txt_rate.text().strip())
            if wt <= 0 or rate <= 0:
                raise ValueError
        except Exception:
            err = "Please enter valid weight and rate." if get_language() == "en" else "કૃપા કરીને સાચું વજન અને ભાવ દાખલ કરો."
            QMessageBox.warning(self, "Attention", err)
            return

        fine_wt = round(wt * (touch / 100.0), 3)
        subtotal = round(fine_wt * rate, 2)
        gst_rate = self.cmb_gst.currentData() or 0.0
        gst = round(subtotal * (gst_rate / 100.0), 2)
        treatment = self.cmb_treatment.currentData()
        net_payout = round(subtotal - gst if treatment == "DEDUCTED" else subtotal + gst, 2)

        cust_data = self.cmb_customer.currentData()
        cust_id = cust_data.get("id") if cust_data else None

        pid = add_urd_purchase(
            voucher_no=voucher_no,
            purchase_date=self.dt_date.date().toString("yyyy-MM-dd"),
            customer_name=cust_name,
            customer_uid=uid,
            customer_id=cust_id,
            description=desc,
            gross_weight_mg=int(round(wt * 1000)),
            touch_purity=touch,
            fine_weight_mg=int(round(fine_wt * 1000)),
            rate_paise=int(round(rate * 100)),
            subtotal_paise=int(round(subtotal * 100)),
            gst_rate_percent=gst_rate,
            gst_paise=int(round(gst * 100)),
            gst_treatment=treatment,
            net_payout_paise=int(round(net_payout * 100)),
            payment_mode=self.cmb_mode.currentText().split()[0],
            payment_ref=self.txt_ref.text().strip()
        )

        if print_voucher:
            urd_dict = get_purchase_by_id(pid)
            if urd_dict:
                urd_dict["mobile"] = self.txt_mobile.text().strip()
                urd_dict["address"] = self.txt_address.text().strip()
                print_or_pdf_urd_voucher(urd_dict, self)

        self.accept()

# ----------------- Wholesale Dealer Purchase Dialog -----------------

class AddPurchaseDialog(QDialog):
    """
    Standard dialog for wholesale purchases from registered bullion dealers / merchants.
    100% Bilingual in both English and Gujarati.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("dealer_dialog_title"))
        self.setFixedSize(580, 650)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F7F4;
                font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
            }
            QLabel { background-color: transparent; font-size: 13px; color: #2A1A1A; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #FFFFFF;
                border: 1.2px solid #B9A0A0;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                color: #2A1A1A;
            }
            QPushButton#SecondaryBtn {
                background-color: #E2E8F0;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #CBD5E1;
                color: #0F172A;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel(t("dealer_dialog_title"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0B1E19;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_supplier = QLineEdit()
        self.txt_supplier.setPlaceholderText(t("ph_dealer_supplier"))
        form.addRow(t("lbl_supplier_name"), self.txt_supplier)

        self.txt_gstin = QLineEdit()
        self.txt_gstin.setPlaceholderText("24AAAAA0000A1Z5")
        form.addRow(t("lbl_supplier_gstin"), self.txt_gstin)

        self.txt_inv_no = QLineEdit()
        self.txt_inv_no.setPlaceholderText("INV-8921")
        form.addRow(t("lbl_inv_no"), self.txt_inv_no)

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setDisplayFormat("dd-MM-yyyy")
        form.addRow(t("lbl_purchase_date"), self.dt_date)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText(t("ph_dealer_desc"))
        form.addRow(t("lbl_purchase_desc"), self.txt_desc)

        self.txt_weight = QLineEdit()
        self.txt_weight.setPlaceholderText("100.000")
        self.txt_weight.textChanged.connect(self.calculate_totals)
        form.addRow(t("th_weight"), self.txt_weight)

        rate_row = QHBoxLayout()
        self.txt_rate = QLineEdit()
        self.txt_rate.setPlaceholderText("74500")
        self.txt_rate.textChanged.connect(self.calculate_totals)

        self.btn_live_rate = QPushButton(t("btn_live_rate"))
        self.btn_live_rate.setCursor(Qt.PointingHandCursor)
        self.btn_live_rate.setStyleSheet("""
            QPushButton {
                background: #FEF3C7;
                color: #92400E;
                font-size: 11px;
                font-weight: bold;
                border: 1.2px solid #F59E0B;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #FDE68A;
                color: #78350F;
            }
        """)
        self.btn_live_rate.clicked.connect(self.apply_live_dealer_rate)
        rate_row.addWidget(self.txt_rate, stretch=3)
        rate_row.addWidget(self.btn_live_rate, stretch=1)
        form.addRow(t("th_rate"), rate_row)

        # GST Rate Selector
        self.cmb_gst = QComboBox()
        self.cmb_gst.addItem(t("opt_gst_3_dealer"), 3.0)
        self.cmb_gst.addItem(t("opt_gst_5_dealer"), 5.0)
        self.cmb_gst.addItem(t("opt_gst_0_nil"), 0.0)
        self.cmb_gst.currentIndexChanged.connect(self.calculate_totals)
        form.addRow(t("lbl_gst_rate"), self.cmb_gst)

        # Calculation Display Box
        calc_box = QFrame()
        calc_box.setStyleSheet("background-color: #FFFFFF; border: 1.5px solid #E8E4DC; border-radius: 8px; padding: 10px;")
        cb_layout = QVBoxLayout(calc_box)
        cb_layout.setSpacing(6)

        self.lbl_subtotal = QLabel(f"{t('lbl_gross_val_card')}: ₹ 0.00")
        self.lbl_subtotal.setStyleSheet("font-size: 13px; color: #1A2521;")
        cb_layout.addWidget(self.lbl_subtotal)

        self.lbl_gst = QLabel(f"{t('lbl_itc_credit')}: ₹ 0.00")
        self.lbl_gst.setStyleSheet("font-size: 13px; font-weight: bold; color: #16A34A;")
        cb_layout.addWidget(self.lbl_gst)

        self.lbl_total = QLabel(f"{t('lbl_total_bill_amt')}: ₹ 0.00")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #0B1E19;")
        cb_layout.addWidget(self.lbl_total)

        form.addRow(t("lbl_totals_box"), calc_box)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["BANK TRANSFER / RTGS", "CHEQUE", "CASH", "UPI"])
        form.addRow(t("lbl_pay_mode"), self.cmb_mode)

        self.txt_ref = QLineEdit()
        self.txt_ref.setPlaceholderText(t("ph_payment_ref_notes"))
        form.addRow(t("lbl_payment_ref"), self.txt_ref)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_cancel = QPushButton(t("btn_cancel_short"))
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton(t("btn_save"))
        self.btn_save.setObjectName("GoldActionBtn")
        self.btn_save.clicked.connect(self.save)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addLayout(btns)

    def apply_live_dealer_rate(self):
        try:
            from rates_manager import get_rates_manager
            rm = get_rates_manager()
            desc = (self.txt_desc.text() or "").lower()
            rates = rm.get_latest_rates()
            if any(w in desc for w in ["silver", "ચાંદી", "chandi"]):
                rate = rates.get("silver_lagdi_1g", 155.0)
            elif any(w in desc for w in ["22k", "૨૨k", "916"]):
                rate = rates.get("gold_22k_1g", 11807.0)
            else:
                rate = rates.get("gold_24k_1g", 12880.0)
            self.txt_rate.setText(str(rate))
            if not rm.is_live():
                QMessageBox.warning(
                    self, "ઓફલાઇન ભાવ / Offline Rate",
                    "⚠️ ઇન્ટરનેટ કનેક્શન ન હોવાથી સેવ કરેલો જૂનો ભાવ મુકાયો છે. કૃપા કરીને ચકાસો.\n"
                    "(Applied cached/offline rate. Please verify.)"
                )
        except Exception:
            pass

    def calculate_totals(self):
        try:
            wt = float(self.txt_weight.text().strip() or 0)
            rate = float(self.txt_rate.text().strip() or 0)
            subtotal = round(wt * rate, 2)
            gst_rate = self.cmb_gst.currentData() or 0.0
            gst = round(subtotal * (gst_rate / 100.0), 2)
            total = round(subtotal + gst, 2)

            self.lbl_subtotal.setText(f"{t('lbl_gross_val_card')}: {format_inr(subtotal)}")
            self.lbl_gst.setText(f"{gst_rate:.1f}% {t('lbl_itc_credit')}: {format_inr(gst)}")
            self.lbl_total.setText(f"{t('lbl_total_bill_amt')}: {format_inr(total)}")
        except Exception:
            pass

    def save(self):
        supplier = self.txt_supplier.text().strip()
        inv_no = self.txt_inv_no.text().strip()
        desc = self.txt_desc.text().strip()

        if not supplier or not inv_no or not desc:
            err = "Please enter supplier name, invoice no, and description." if get_language() == "en" else "કૃપા કરીને વેપારીનું નામ, બિલ નં. અને વસ્તુની વિગત દાખલ કરો."
            QMessageBox.warning(self, "Attention", err)
            return

        try:
            wt = float(self.txt_weight.text().strip())
            rate = float(self.txt_rate.text().strip())
            if wt <= 0 or rate <= 0:
                raise ValueError
        except Exception:
            err = "Please enter valid weight and rate." if get_language() == "en" else "કૃપા કરીને સાચું વજન અને ભાવ દાખલ કરો."
            QMessageBox.warning(self, "Attention", err)
            return

        subtotal = round(wt * rate, 2)
        gst_rate = self.cmb_gst.currentData() or 0.0
        gst = round(subtotal * (gst_rate / 100.0), 2)
        total = round(subtotal + gst, 2)

        add_purchase(
            invoice_no=inv_no,
            purchase_date=self.dt_date.date().toString("yyyy-MM-dd"),
            supplier_name=supplier,
            supplier_gstin=self.txt_gstin.text().strip(),
            description=desc,
            weight_mg=int(round(wt * 1000)),
            rate_paise=int(round(rate * 100)),
            subtotal_paise=int(round(subtotal * 100)),
            gst_paise=int(round(gst * 100)),
            total_paise=int(round(total * 100)),
            payment_mode=self.cmb_mode.currentText().split()[0],
            payment_ref=self.txt_ref.text().strip(),
            purchase_type="DEALER",
            gst_rate_percent=gst_rate,
            net_payout_paise=int(round(total * 100))
        )

        self.accept()

# ----------------- Main Purchases View Screen -----------------

class PurchasesView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.current_filter_type = None  # None = All, 'URD', 'DEALER'
        self.init_ui()
        self.load_purchases()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Bar
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(t("btn_back"))
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.on_back_callback)
        top_bar.addWidget(self.btn_back)

        self.lbl_title = QLabel(t("purchases_title"))
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0B1E19; margin-left: 12px;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        # Action Buttons: URD Customer Buyback (Gold/Wine) & Dealer Purchase (Secondary)
        self.btn_add_urd = QPushButton(t("btn_add_urd_purchase"))
        self.btn_add_urd.setObjectName("GoldActionBtn")
        self.btn_add_urd.setCursor(Qt.PointingHandCursor)
        self.btn_add_urd.setStyleSheet("""
            QPushButton {
                background-color: #6B2433;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #7A2E3A;
            }
            QPushButton:hover {
                background-color: #832C3E;
            }
        """)
        self.btn_add_urd.clicked.connect(self.open_add_urd_dialog)
        top_bar.addWidget(self.btn_add_urd)

        self.btn_add_dealer = QPushButton(t("btn_add_dealer_purchase"))
        self.btn_add_dealer.setObjectName("SecondaryBtn")
        self.btn_add_dealer.setCursor(Qt.PointingHandCursor)
        self.btn_add_dealer.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #0B1E19;
                font-weight: 600;
                font-size: 13px;
                padding: 8px 14px;
                border-radius: 6px;
                border: 1.5px solid #D4AF37;
            }
            QPushButton:hover {
                background-color: #F8F5EE;
            }
        """)
        self.btn_add_dealer.clicked.connect(self.open_add_dealer_dialog)
        top_bar.addWidget(self.btn_add_dealer)

        layout.addLayout(top_bar)

        # Filter & Search Controls
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.btn_filter_all = QPushButton(t("btn_filter_all_purchases"))
        self.btn_filter_urd = QPushButton(t("btn_filter_urd_purchases"))
        self.btn_filter_dealer = QPushButton(t("btn_filter_dealer_purchases"))

        for btn, ptype in [(self.btn_filter_all, None), (self.btn_filter_urd, "URD"), (self.btn_filter_dealer, "DEALER")]:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 12px;
                    border: 1.2px solid #D4AF37;
                    border-radius: 15px;
                    font-size: 12px;
                    background: #FFFFFF;
                    color: #0B1E19;
                }
                QPushButton:checked {
                    background: #6B2433;
                    color: #FFFFFF;
                    font-weight: bold;
                    border-color: #6B2433;
                }
            """)
            btn.clicked.connect(lambda _, t=ptype: self.set_filter_type(t))
            filter_bar.addWidget(btn)

        self.btn_filter_all.setChecked(True)
        filter_bar.addSpacing(16)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_purchases"))
        self.txt_search.textChanged.connect(lambda: self.load_purchases())
        filter_bar.addWidget(self.txt_search, stretch=1)

        layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.setup_table_headers()
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(10, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)

    def set_filter_type(self, ptype):
        self.current_filter_type = ptype
        self.btn_filter_all.setChecked(ptype is None)
        self.btn_filter_urd.setChecked(ptype == "URD")
        self.btn_filter_dealer.setChecked(ptype == "DEALER")
        self.load_purchases()

    def setup_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            t("th_pur_date"),
            t("th_pur_voucher"),
            t("th_pur_type"),
            t("th_pur_party"),
            t("th_pur_desc"),
            t("th_pur_gross_wt"),
            t("th_pur_touch_fine"),
            t("th_pur_rate"),
            t("th_pur_gst_itc"),
            t("th_pur_payout"),
            t("th_pur_action")
        ])

    def load_purchases(self):
        keyword = self.txt_search.text()
        purchases = get_purchases(keyword, purchase_type=self.current_filter_type)
        self.table.setRowCount(0)

        for row_idx, p in enumerate(purchases):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(format_date_dmy(p["purchase_date"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"#{p['invoice_no']}"))

            # Type Badge (URD vs DEALER)
            ptype = p.get("purchase_type", "DEALER")
            if ptype == "URD":
                type_lbl = t("badge_urd_cust")
                type_color = QColor("#6B2433")
            else:
                type_lbl = t("badge_dealer")
                type_color = QColor("#1E3A8A")

            type_item = QTableWidgetItem(type_lbl)
            type_item.setForeground(type_color)
            type_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 2, type_item)

            # Name and UID / GSTIN
            name_text = p["supplier_name"]
            if p.get("supplier_uid"):
                name_text += f"\nUID: {p['supplier_uid']}"
            elif p.get("supplier_gstin"):
                name_text += f"\nGST: {p['supplier_gstin']}"
            self.table.setItem(row_idx, 3, QTableWidgetItem(name_text))

            # Description
            self.table.setItem(row_idx, 4, QTableWidgetItem(p["description"]))

            # Gross Weight
            wt = p["weight_mg"] / 1000.0
            self.table.setItem(row_idx, 5, QTableWidgetItem(f"{wt:.3f} g"))

            # Touch / Fine Wt
            touch = p.get("touch_purity", 100.0) or 100.0
            fine_wt = p.get("fine_weight_mg", 0) / 1000.0
            if fine_wt <= 0:
                fine_wt = round(wt * (touch / 100.0), 3)
            self.table.setItem(row_idx, 6, QTableWidgetItem(f"{touch:.1f}% ({fine_wt:.3f}g)"))

            # Rate
            rate = p["rate_paise"] / 100.0
            self.table.setItem(row_idx, 7, QTableWidgetItem(format_inr(rate)))

            # GST
            gst = p["gst_paise"] / 100.0
            rate_pct = p.get("gst_rate_percent", 5.0 if ptype == "URD" else 3.0) or 0.0
            gst_item = QTableWidgetItem(f"{format_inr(gst)}\n({rate_pct:.1f}%)")
            gst_item.setForeground(QColor("#16A34A"))
            gst_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 8, gst_item)

            # Net Payout / Total
            net_amt = (p.get("net_payout_paise", 0) or p["total_paise"]) / 100.0
            tot_item = QTableWidgetItem(format_inr(net_amt))
            tot_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 9, tot_item)

            # Actions Container
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            # Print Voucher button (Available for URD purchases)
            if ptype == "URD":
                btn_print = QPushButton("🖨️")
                btn_print.setToolTip(t("tip_print_urd"))
                btn_print.setMaximumWidth(32)
                btn_print.setCursor(Qt.PointingHandCursor)
                btn_print.clicked.connect(lambda _, pid=p["id"]: self.print_urd_voucher(pid))
                act_layout.addWidget(btn_print)

            # Delete button
            btn_del = QPushButton("❌")
            btn_del.setToolTip(t("tip_delete_entry"))
            btn_del.setMaximumWidth(32)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(lambda _, pid=p["id"]: self.delete_entry(pid))
            act_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 10, act_widget)

    def print_urd_voucher(self, purchase_id: int):
        urd_dict = get_purchase_by_id(purchase_id)
        if urd_dict:
            print_or_pdf_urd_voucher(urd_dict, self)

    def delete_entry(self, purchase_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            t("msg_confirm_delete_purchase"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_purchase(purchase_id)
            self.load_purchases()

    def open_add_urd_dialog(self):
        if AddURDPurchaseDialog(self).exec():
            self.load_purchases()

    def open_add_dealer_dialog(self):
        if AddPurchaseDialog(self).exec():
            self.load_purchases()

    def retranslate_ui(self):
        self.btn_back.setText(t("btn_back"))
        self.lbl_title.setText(t("purchases_title"))
        self.btn_add_urd.setText(t("btn_add_urd_purchase"))
        self.btn_add_dealer.setText(t("btn_add_dealer_purchase"))
        self.btn_filter_all.setText(t("btn_filter_all_purchases"))
        self.btn_filter_urd.setText(t("btn_filter_urd_purchases"))
        self.btn_filter_dealer.setText(t("btn_filter_dealer_purchases"))
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_purchases"))
        self.setup_table_headers()
        self.load_purchases()
