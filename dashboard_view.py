"""
dashboard_view.py - Executive Jewelry Business Dashboard.
Provides high-level metrics, quick actions, and recent invoices at a glance.
Supports 100% dynamic translation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from translations import t
from database import get_dashboard_metrics
from bill_details_dialog import BillDetailsDialog
from format_utils import format_inr

class DashboardView(QWidget):
    def __init__(self, on_new_bill_callback, on_customers_callback):
        super().__init__()
        self.on_new_bill_callback = on_new_bill_callback
        self.on_customers_callback = on_customers_callback
        self.init_ui()
        self.refresh_metrics()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)

        # 1. Top Greeting & Quick Actions Bar
        top_bar = QHBoxLayout()
        
        greeting_box = QVBoxLayout()
        self.lbl_welcome = QLabel(t("nav_dashboard"))
        self.lbl_welcome.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B1E19;")
        self.lbl_subtext = QLabel(t("tagline"))
        self.lbl_subtext.setStyleSheet("font-size: 13px; color: #6E7A75;")
        greeting_box.addWidget(self.lbl_welcome)
        greeting_box.addWidget(self.lbl_subtext)
        top_bar.addLayout(greeting_box)

        top_bar.addStretch()

        self.btn_quick_bill = QPushButton(t("btn_quick_bill"))
        self.btn_quick_bill.setObjectName("GoldActionBtn")
        self.btn_quick_bill.setCursor(Qt.PointingHandCursor)
        self.btn_quick_bill.clicked.connect(self.on_new_bill_callback)
        top_bar.addWidget(self.btn_quick_bill)

        self.btn_quick_cust = QPushButton(t("btn_quick_customer"))
        self.btn_quick_cust.setObjectName("SecondaryBtn")
        self.btn_quick_cust.setCursor(Qt.PointingHandCursor)
        self.btn_quick_cust.clicked.connect(self.on_customers_callback)
        top_bar.addWidget(self.btn_quick_cust)

        main_layout.addLayout(top_bar)

        # 2. Four Executive Stat Cards
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)

        # Card 1: Today's Sales
        self.card_sales = QFrame()
        self.card_sales.setObjectName("StatCard")
        l1 = QVBoxLayout(self.card_sales)
        self.lbl_title_sales = QLabel(t("stat_today_sales"))
        self.lbl_title_sales.setObjectName("StatTitle")
        self.lbl_val_sales = QLabel("₹ 0.00")
        self.lbl_val_sales.setObjectName("StatValue")
        self.lbl_val_sales.setStyleSheet("color: #16A34A;") # Green
        l1.addWidget(self.lbl_title_sales)
        l1.addWidget(self.lbl_val_sales)
        stats_grid.addWidget(self.card_sales, 0, 0)

        # Card 2: Today's Invoices
        self.card_bills = QFrame()
        self.card_bills.setObjectName("StatCard")
        l2 = QVBoxLayout(self.card_bills)
        self.lbl_title_bills = QLabel(t("stat_today_bills"))
        self.lbl_title_bills.setObjectName("StatTitle")
        self.lbl_val_bills = QLabel("0")
        self.lbl_val_bills.setObjectName("StatValue")
        l2.addWidget(self.lbl_title_bills)
        l2.addWidget(self.lbl_val_bills)
        stats_grid.addWidget(self.card_bills, 0, 1)

        # Card 3: Total Customers
        self.card_cust = QFrame()
        self.card_cust.setObjectName("StatCard")
        l3 = QVBoxLayout(self.card_cust)
        self.lbl_title_cust = QLabel(t("stat_total_cust"))
        self.lbl_title_cust.setObjectName("StatTitle")
        self.lbl_val_cust = QLabel("0")
        self.lbl_val_cust.setObjectName("StatValue")
        l3.addWidget(self.lbl_title_cust)
        l3.addWidget(self.lbl_val_cust)
        stats_grid.addWidget(self.card_cust, 0, 2)

        # Card 4: Total Outstanding Udhar
        self.card_udhar = QFrame()
        self.card_udhar.setObjectName("StatCard")
        l4 = QVBoxLayout(self.card_udhar)
        self.lbl_title_udhar = QLabel(t("stat_total_udhar"))
        self.lbl_title_udhar.setObjectName("StatTitle")
        self.lbl_val_udhar = QLabel("₹ 0.00")
        self.lbl_val_udhar.setObjectName("StatValue")
        self.lbl_val_udhar.setStyleSheet("color: #DC2626;") # Red
        l4.addWidget(self.lbl_title_udhar)
        l4.addWidget(self.lbl_val_udhar)
        stats_grid.addWidget(self.card_udhar, 0, 3)

        main_layout.addLayout(stats_grid)

        # GST Tax Center Frame (CA Tax Summary)
        gst_frame = QFrame()
        gst_frame.setStyleSheet("background-color: #FFFFFF; border: 1.5px solid #D4AF37; border-radius: 10px; padding: 6px 14px;")
        gst_layout = QHBoxLayout(gst_frame)
        gst_layout.setContentsMargins(12, 8, 12, 8)

        self.lbl_gst_title = QLabel("⚖️ " + t("stat_gst_summary"))
        self.lbl_gst_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #0B1E19;")
        gst_layout.addWidget(self.lbl_gst_title)
        gst_layout.addStretch()

        self.lbl_val_gst_out = QLabel(f"{t('stat_gst_output')}: ₹ 0.00")
        self.lbl_val_gst_out.setStyleSheet("font-weight: bold; font-size: 13px; color: #DC2626; margin-right: 18px;")
        gst_layout.addWidget(self.lbl_val_gst_out)

        self.lbl_val_gst_in = QLabel(f"{t('stat_gst_input')}: ₹ 0.00")
        self.lbl_val_gst_in.setStyleSheet("font-weight: bold; font-size: 13px; color: #16A34A; margin-right: 18px;")
        gst_layout.addWidget(self.lbl_val_gst_in)

        self.lbl_val_gst_net = QLabel(f"{t('stat_gst_net')}: ₹ 0.00")
        self.lbl_val_gst_net.setStyleSheet("font-weight: bold; font-size: 14px; color: #0B1E19; background: #F3EBD8; padding: 4px 10px; border-radius: 6px;")
        gst_layout.addWidget(self.lbl_val_gst_net)

        main_layout.addWidget(gst_frame)

        # 3. Recent Bills Section
        self.lbl_recent_title = QLabel(t("recent_bills_title"))
        self.lbl_recent_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(self.lbl_recent_title)

        self.table_recent = QTableWidget()
        self.table_recent.setColumnCount(7)
        self.setup_table_headers()
        
        h = self.table_recent.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.table_recent.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_recent.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_recent.verticalHeader().setDefaultSectionSize(38)
        main_layout.addWidget(self.table_recent)

    def setup_table_headers(self):
        self.table_recent.setHorizontalHeaderLabels([
            t("bill_no_label"),
            t("bill_date_label"),
            t("th_cust_name"),
            t("lbl_grand_total"),
            t("lbl_balance_due"),
            t("lbl_pay_mode"),
            t("th_action")
        ])

    def refresh_metrics(self):
        """Loads and updates all live numbers and recent invoices."""
        metrics = get_dashboard_metrics()
        
        sales_rs = metrics["today_sales_paise"] / 100.0
        self.lbl_val_sales.setText(format_inr(sales_rs))
        self.lbl_val_bills.setText(str(metrics["today_bills_count"]))
        self.lbl_val_cust.setText(str(metrics["total_customers"]))

        udhar_rs = metrics["total_market_udhar_paise"] / 100.0
        self.lbl_val_udhar.setText(format_inr(udhar_rs))

        # GST Metrics
        out_gst = metrics.get("output_gst_paise", 0) / 100.0
        in_gst = metrics.get("input_gst_paise", 0) / 100.0
        net_gst = metrics.get("net_gst_paise", 0) / 100.0

        self.lbl_val_gst_out.setText(f"{t('stat_gst_output')}: {format_inr(out_gst)}")
        self.lbl_val_gst_in.setText(f"{t('stat_gst_input')}: {format_inr(in_gst)}")
        self.lbl_val_gst_net.setText(f"{t('stat_gst_net')}: {format_inr(net_gst)}")

        # Populate Recent Invoices
        self.table_recent.setRowCount(0)
        for row_idx, b in enumerate(metrics["recent_bills"]):
            self.table_recent.insertRow(row_idx)
            self.table_recent.setItem(row_idx, 0, QTableWidgetItem(f"#{b['bill_no']}"))
            self.table_recent.setItem(row_idx, 1, QTableWidgetItem(b["bill_date"]))
            
            cust_name = b["name_gu"]
            if b.get("mobile"):
                cust_name += f" ({b['mobile']})"
            self.table_recent.setItem(row_idx, 2, QTableWidgetItem(cust_name))

            total_rs = b["grand_total_paise"] / 100.0
            self.table_recent.setItem(row_idx, 3, QTableWidgetItem(format_inr(total_rs)))

            bal_rs = b["balance_paise"] / 100.0
            bal_item = QTableWidgetItem(format_inr(bal_rs))
            bal_item.setForeground(Qt.red if bal_rs > 0 else Qt.darkGreen)
            self.table_recent.setItem(row_idx, 4, bal_item)

            self.table_recent.setItem(row_idx, 5, QTableWidgetItem(b["payment_mode"]))

            btn_view = QPushButton("🧾 " + t("btn_print"))
            btn_view.setObjectName("SecondaryBtn")
            btn_view.clicked.connect(lambda _, b_id=b["id"]: BillDetailsDialog(b_id, self).exec())
            self.table_recent.setCellWidget(row_idx, 6, btn_view)

    def retranslate_ui(self):
        """Called whenever language switches between Gujarati and English."""
        self.lbl_welcome.setText(t("nav_dashboard"))
        self.lbl_subtext.setText(t("tagline"))
        self.btn_quick_bill.setText(t("btn_quick_bill"))
        self.btn_quick_cust.setText(t("btn_quick_customer"))
        self.lbl_title_sales.setText(t("stat_today_sales"))
        self.lbl_title_bills.setText(t("stat_today_bills"))
        self.lbl_title_cust.setText(t("stat_total_cust"))
        self.lbl_title_udhar.setText(t("stat_total_udhar"))
        self.lbl_gst_title.setText("⚖️ " + t("stat_gst_summary"))
        self.lbl_recent_title.setText(t("recent_bills_title"))
        self.setup_table_headers()
        self.refresh_metrics()

