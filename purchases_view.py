"""
purchases_view.py - Wholesale Purchases (Inward Register & GST ITC Tracking).
Allows the owner to record bullion, raw gold, ornaments, and silver bought from dealers.
Tracks Input Tax Credit (ITC) for CA filing and monthly profit/loss accounting.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QMessageBox, QComboBox, QFrame, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

from translations import t
from database import add_purchase, get_purchases, delete_purchase
from format_utils import format_inr

class AddPurchaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("btn_add_purchase"))
        self.setFixedSize(540, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F7F4;
                font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                background-color: transparent;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel(t("btn_add_purchase"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0B1E19;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_supplier = QLineEdit()
        self.txt_supplier.setPlaceholderText("દા.ત. સુરત બુલિયન / અમદાવાદ ઝવેરી")
        form.addRow(t("lbl_supplier_name"), self.txt_supplier)

        self.txt_gstin = QLineEdit()
        self.txt_gstin.setPlaceholderText("24AAAAA0000A1Z5")
        form.addRow(t("lbl_supplier_gstin"), self.txt_gstin)

        self.txt_inv_no = QLineEdit()
        self.txt_inv_no.setPlaceholderText("દા.ત. INV-8921")
        form.addRow(t("lbl_inv_no"), self.txt_inv_no)

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow(t("lbl_purchase_date"), self.dt_date)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("દા.ત. ૨૪K સોનાનો બાર (Gold Bar) / ૨૨K દાગીના")
        form.addRow(t("lbl_purchase_desc"), self.txt_desc)

        self.txt_weight = QLineEdit()
        self.txt_weight.setPlaceholderText("દા.ત. 100.000")
        self.txt_weight.textChanged.connect(self.calculate_totals)
        form.addRow(t("th_weight"), self.txt_weight)

        self.txt_rate = QLineEdit()
        self.txt_rate.setPlaceholderText("દા.ત. 74500")
        self.txt_rate.textChanged.connect(self.calculate_totals)
        form.addRow(t("th_rate"), self.txt_rate)

        # Calculation Display Box
        calc_box = QFrame()
        calc_box.setStyleSheet("background-color: #FFFFFF; border: 1.5px solid #E8E4DC; border-radius: 8px; padding: 10px;")
        cb_layout = QVBoxLayout(calc_box)
        cb_layout.setSpacing(6)

        self.lbl_subtotal = QLabel("માલ રકમ (Subtotal): ₹ 0.00")
        self.lbl_subtotal.setStyleSheet("font-size: 13px; color: #1A2521;")
        cb_layout.addWidget(self.lbl_subtotal)

        self.lbl_gst = QLabel("૩% GST ઇનપુટ ક્રેડિટ (ITC): ₹ 0.00")
        self.lbl_gst.setStyleSheet("font-size: 13px; font-weight: bold; color: #16A34A;")
        cb_layout.addWidget(self.lbl_gst)

        self.lbl_total = QLabel("કુલ બિલ રકમ: ₹ 0.00")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #0B1E19;")
        cb_layout.addWidget(self.lbl_total)

        form.addRow("હિસાબ (Totals):", calc_box)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["BANK TRANSFER / RTGS", "CHEQUE", "CASH", "UPI"])
        form.addRow(t("lbl_pay_mode"), self.cmb_mode)

        self.txt_ref = QLineEdit()
        self.txt_ref.setPlaceholderText("UTR / ચેક નં. / રીમાર્ક")
        form.addRow("UTR / Cheque Ref:", self.txt_ref)

        # Seamless Enter-key navigation
        self.txt_supplier.returnPressed.connect(lambda: self.txt_gstin.setFocus())
        self.txt_gstin.returnPressed.connect(lambda: self.txt_inv_no.setFocus())
        self.txt_inv_no.returnPressed.connect(lambda: self.txt_desc.setFocus())
        self.txt_desc.returnPressed.connect(lambda: self.txt_weight.setFocus())
        self.txt_weight.returnPressed.connect(lambda: self.txt_rate.setFocus())
        self.txt_rate.returnPressed.connect(lambda: self.txt_ref.setFocus())
        self.txt_ref.returnPressed.connect(lambda: self.btn_save.setFocus())

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_cancel = QPushButton(t("btn_cancel"))
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton(t("btn_save"))
        self.btn_save.setObjectName("GoldActionBtn")
        self.btn_save.clicked.connect(self.save)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addLayout(btns)

    def calculate_totals(self):
        try:
            wt = float(self.txt_weight.text() or 0)
            rate = float(self.txt_rate.text() or 0)
            subtotal = wt * rate
            gst = round(subtotal * 0.03, 2)
            total = subtotal + gst

            self.lbl_subtotal.setText(f"માલ રકમ (Subtotal): {format_inr(subtotal)}")
            self.lbl_gst.setText(f"૩% GST ઇનપુટ ક્રેડિટ (ITC): {format_inr(gst)}")
            self.lbl_total.setText(f"કુલ બિલ રકમ: {format_inr(total)}")
        except Exception:
            pass

    def save(self):
        supplier = self.txt_supplier.text().strip()
        inv_no = self.txt_inv_no.text().strip()
        desc = self.txt_desc.text().strip()

        if not supplier or not inv_no or not desc:
            QMessageBox.warning(self, "Attention", "કૃપા કરીને વેપારીનું નામ, બિલ નં. અને વસ્તુની વિગત દાખલ કરો.")
            return

        try:
            wt = float(self.txt_weight.text().strip())
            rate = float(self.txt_rate.text().strip())
            if wt <= 0 or rate <= 0:
                raise ValueError
        except:
            QMessageBox.warning(self, "Attention", "કૃપા કરીને સાચું વજન અને ભાવ દાખલ કરો.")
            return

        subtotal = round(wt * rate, 2)
        gst = round(subtotal * 0.03, 2)
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
            payment_ref=self.txt_ref.text().strip()
        )

        self.accept()

class PurchasesView(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.init_ui()
        self.load_purchases()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(t("btn_back"))
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.on_back_callback)
        top_bar.addWidget(self.btn_back)

        self.lbl_title = QLabel(t("purchases_title"))
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0B1E19; margin-left: 12px;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        self.btn_add = QPushButton(t("btn_add_purchase"))
        self.btn_add.setObjectName("GoldActionBtn")
        self.btn_add.clicked.connect(self.open_add_dialog)
        top_bar.addWidget(self.btn_add)

        layout.addLayout(top_bar)

        # Search Bar
        search_bar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_purchases"))
        self.txt_search.textChanged.connect(self.load_purchases)
        search_bar.addWidget(self.txt_search)
        layout.addLayout(search_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.setup_table_headers()
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def setup_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            t("bill_date_label"),
            t("th_inv_no"),
            t("th_supplier"),
            t("th_desc"),
            t("th_weight"),
            t("th_rate"),
            t("th_gst_paid"),
            t("th_total_amt"),
            t("th_action")
        ])

    def load_purchases(self, keyword: str = ""):
        purchases = get_purchases(keyword)
        self.table.setRowCount(0)

        for row_idx, p in enumerate(purchases):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(p["purchase_date"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"#{p['invoice_no']}"))
            
            supp = p["supplier_name"]
            if p.get("supplier_gstin"):
                supp += f"\nGST: {p['supplier_gstin']}"
            self.table.setItem(row_idx, 2, QTableWidgetItem(supp))

            self.table.setItem(row_idx, 3, QTableWidgetItem(p["description"]))

            wt = p["weight_mg"] / 1000.0
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{wt:.3f} g"))

            rate = p["rate_paise"] / 100.0
            self.table.setItem(row_idx, 5, QTableWidgetItem(format_inr(rate)))

            gst = p["gst_paise"] / 100.0
            gst_item = QTableWidgetItem(format_inr(gst))
            gst_item.setForeground(Qt.darkGreen)
            self.table.setItem(row_idx, 6, gst_item)

            tot = p["total_paise"] / 100.0
            self.table.setItem(row_idx, 7, QTableWidgetItem(format_inr(tot)))

            btn_del = QPushButton("❌")
            btn_del.setMaximumWidth(40)
            btn_del.clicked.connect(lambda _, pid=p["id"]: self.delete_entry(pid))
            self.table.setCellWidget(row_idx, 8, btn_del)

    def delete_entry(self, purchase_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "શું તમે ખરેખર આ ખરીદી એન્ટ્રી કાઢી નાખવા માંગો છો?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_purchase(purchase_id)
            self.load_purchases(self.txt_search.text())

    def open_add_dialog(self):
        if AddPurchaseDialog(self).exec():
            self.load_purchases(self.txt_search.text())

    def retranslate_ui(self):
        self.btn_back.setText(t("btn_back"))
        self.lbl_title.setText(t("purchases_title"))
        self.btn_add.setText(t("btn_add_purchase"))
        self.txt_search.setPlaceholderText("🔍 " + t("lbl_search_purchases"))
        self.setup_table_headers()
        self.load_purchases(self.txt_search.text())

