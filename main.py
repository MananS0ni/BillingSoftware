"""
main.py - Executive Main Window with Sleek Sidebar Navigation.
Includes Dashboard, Modern Billing POS, Customer Directory, and Ledger.
100% full bilingual dynamic translation across all views.
"""

import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QFrame, QFileDialog, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer

from translations import t, toggle_language, set_lang
from database import init_db, backup_database
from theme import GLOBAL_STYLESHEET

from dashboard_view import DashboardView
from customers_view import CustomersView
from ledger_view import LedgerView
from billing_view import BillingView
from purchases_view import PurchasesView
from bill_history_view import BillHistoryView
from whatsapp_dialog import WhatsAppDialog
from whatsapp_manager import get_whatsapp_status, ensure_bridge_running

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soni Natvarlal Himmatlal - સોની નટવરલાલ હિંમતલાલ")
        self.resize(1200, 780)
        self.setMinimumSize(1024, 700)
        
        init_db()
        self.init_ui()

        ensure_bridge_running()
        self.wa_timer = QTimer(self)
        self.wa_timer.timeout.connect(self.update_wa_header_status)
        self.wa_timer.start(4000)
        self.update_wa_header_status()

    def update_wa_header_status(self):
        data = get_whatsapp_status()
        if data.get("status") == "connected":
            self.btn_wa.setText("🟢 WhatsApp")
            self.btn_wa.setStyleSheet("background-color: #14532D; color: #FFFFFF; border: 1.5px solid #22C55E; border-radius: 8px; padding: 6px 14px; font-weight: bold; font-size: 13px; margin-right: 14px;")
        else:
            self.btn_wa.setText(t("btn_wa_not_connected"))
            self.btn_wa.setStyleSheet("background-color: #12382C; color: #D4AF37; border: 1.5px solid #D4AF37; border-radius: 8px; padding: 6px 14px; font-weight: bold; font-size: 13px; margin-right: 14px;")

    def open_whatsapp_dialog(self):
        dlg = WhatsAppDialog(self)
        dlg.exec()
        self.update_wa_header_status()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Executive Header Bar
        header = QFrame()
        header.setObjectName("TopHeaderBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)

        title_box = QVBoxLayout()
        title_row = QHBoxLayout()
        
        self.lbl_title = QLabel(t("app_title"))
        self.lbl_title.setObjectName("AppBrandTitle")
        title_row.addWidget(self.lbl_title)

        self.lbl_shop_badge = QLabel(" ✨ " + t("shop_badge") + " ")
        self.lbl_shop_badge.setStyleSheet("background: #D4AF37; color: #0B1E19; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 6px;")
        title_row.addWidget(self.lbl_shop_badge)
        title_row.addStretch()

        self.lbl_tagline = QLabel(t("tagline"))
        self.lbl_tagline.setObjectName("AppBrandTagline")
        title_box.addLayout(title_row)
        title_box.addWidget(self.lbl_tagline)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Date Display
        today_formatted = datetime.now().strftime("%d %b, %Y")
        self.lbl_date = QLabel(f"📅 {today_formatted}")
        self.lbl_date.setStyleSheet("background-color: #12382C; color: #FFFFFF; border: 1.5px solid #D4AF37; border-radius: 8px; padding: 6px 14px; font-weight: bold; font-size: 13px; margin-right: 14px;")
        header_layout.addWidget(self.lbl_date)

        # WhatsApp Status Button
        self.btn_wa = QPushButton(t("btn_wa_not_connected"))
        self.btn_wa.setStyleSheet("background-color: #12382C; color: #D4AF37; border: 1.5px solid #D4AF37; border-radius: 8px; padding: 6px 14px; font-weight: bold; font-size: 13px; margin-right: 14px;")
        self.btn_wa.setCursor(Qt.PointingHandCursor)
        self.btn_wa.clicked.connect(self.open_whatsapp_dialog)
        header_layout.addWidget(self.btn_wa)

        # Language Switcher Pill Button
        self.btn_lang = QPushButton(t("btn_switch_lang"))
        self.btn_lang.setObjectName("LangPillBtn")
        self.btn_lang.setCursor(Qt.PointingHandCursor)
        self.btn_lang.clicked.connect(self.on_switch_language)
        header_layout.addWidget(self.btn_lang)

        main_layout.addWidget(header)

        # 2. Body Area (Left Sidebar + Right Stacked Screens)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("LeftSidebar")
        self.sidebar.setFixedWidth(248)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 16, 0, 16)
        side_layout.setSpacing(4)

        self.btn_nav_dashboard = QPushButton(f"  📊  {t('nav_dashboard')}")
        self.btn_nav_dashboard.setProperty("class", "NavButton")
        self.btn_nav_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_nav_dashboard.clicked.connect(lambda: self.switch_screen(0))

        self.btn_nav_billing = QPushButton(f"  🧾  {t('nav_new_bill')}")
        self.btn_nav_billing.setProperty("class", "NavButton")
        self.btn_nav_billing.setCursor(Qt.PointingHandCursor)
        self.btn_nav_billing.clicked.connect(lambda: self.switch_screen(1))

        self.btn_nav_purchases = QPushButton(f"  📦  {t('nav_purchases')}")
        self.btn_nav_purchases.setProperty("class", "NavButton")
        self.btn_nav_purchases.setCursor(Qt.PointingHandCursor)
        self.btn_nav_purchases.clicked.connect(lambda: self.switch_screen(2))

        self.btn_nav_customers = QPushButton(f"  👥  {t('nav_customers')}")
        self.btn_nav_customers.setProperty("class", "NavButton")
        self.btn_nav_customers.setCursor(Qt.PointingHandCursor)
        self.btn_nav_customers.clicked.connect(lambda: self.switch_screen(3))

        self.btn_nav_ledger = QPushButton(f"  📖  {t('nav_ledger')}")
        self.btn_nav_ledger.setProperty("class", "NavButton")
        self.btn_nav_ledger.setCursor(Qt.PointingHandCursor)
        self.btn_nav_ledger.clicked.connect(lambda: self.switch_screen(4))

        self.btn_nav_bill_history = QPushButton(f"  📜  {t('nav_bill_history')}")
        self.btn_nav_bill_history.setProperty("class", "NavButton")
        self.btn_nav_bill_history.setCursor(Qt.PointingHandCursor)
        self.btn_nav_bill_history.clicked.connect(lambda: self.switch_screen(5))

        self.btn_nav_backup = QPushButton(f"  💾  {t('nav_backup')}")
        self.btn_nav_backup.setProperty("class", "NavButton")
        self.btn_nav_backup.setCursor(Qt.PointingHandCursor)
        self.btn_nav_backup.clicked.connect(self.on_backup_clicked)

        side_layout.addWidget(self.btn_nav_dashboard)
        side_layout.addWidget(self.btn_nav_billing)
        side_layout.addWidget(self.btn_nav_purchases)
        side_layout.addWidget(self.btn_nav_customers)
        side_layout.addWidget(self.btn_nav_ledger)
        side_layout.addWidget(self.btn_nav_bill_history)
        side_layout.addSpacing(20)
        side_layout.addWidget(self.btn_nav_backup)
        side_layout.addStretch()

        body_layout.addWidget(self.sidebar)

        # Right Stacked Screens
        self.stack = QStackedWidget()

        # Screen 0: Executive Dashboard
        self.dashboard_view = DashboardView(
            on_new_bill_callback=lambda: self.switch_screen(1),
            on_customers_callback=lambda: self.switch_screen(3)
        )
        self.stack.addWidget(self.dashboard_view)

        # Screen 1: Modern Billing
        self.billing_view = BillingView(on_back_callback=lambda: self.switch_screen(0))
        self.stack.addWidget(self.billing_view)

        # Screen 2: Wholesale Purchases View
        self.purchases_view = PurchasesView(on_back_callback=lambda: self.switch_screen(0))
        self.stack.addWidget(self.purchases_view)

        # Screen 3: Customers Directory (with 1-click shortcut to Ledger)
        self.customers_view = CustomersView(
            on_back_callback=lambda: self.switch_screen(0),
            on_open_ledger_callback=self.open_customer_ledger
        )
        self.stack.addWidget(self.customers_view)

        # Screen 4: Ledger View
        self.ledger_view = LedgerView(on_back_callback=lambda: self.switch_screen(0))
        self.stack.addWidget(self.ledger_view)

        # Screen 5: Billing History View (All Past Records)
        self.bill_history_view = BillHistoryView(on_back_callback=lambda: self.switch_screen(0))
        self.stack.addWidget(self.bill_history_view)

        body_layout.addWidget(self.stack, stretch=1)
        main_layout.addLayout(body_layout)

        self.switch_screen(0)

    def switch_screen(self, index: int):
        self.stack.setCurrentIndex(index)
        
        # Update Nav Button Active styling
        nav_buttons = [
            self.btn_nav_dashboard,
            self.btn_nav_billing,
            self.btn_nav_purchases,
            self.btn_nav_customers,
            self.btn_nav_ledger,
            self.btn_nav_bill_history
        ]
        for i, btn in enumerate(nav_buttons):
            if i == index:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh data when opening screens
        if index == 0:
            self.dashboard_view.refresh_metrics()
        elif index == 1:
            self.billing_view.reset_form()
        elif index == 2:
            self.purchases_view.load_purchases()
        elif index == 3:
            self.customers_view.load_customers()
        elif index == 4:
            self.ledger_view.refresh_customer_dropdown()
        elif index == 5:
            self.bill_history_view.load_history()

    def open_customer_ledger(self, customer):
        self.switch_screen(4)
        self.ledger_view.load_customer_ledger(customer)

    def on_switch_language(self):
        """Switches language and retranslates 100% of all views."""
        toggle_language()

        # 1. Update Header & Shell
        self.lbl_title.setText(t("app_title"))
        self.lbl_tagline.setText(t("tagline"))
        self.lbl_shop_badge.setText(" ✨ " + t("shop_badge") + " ")
        self.btn_lang.setText(t("btn_switch_lang"))
        self.update_wa_header_status()

        # 2. Update Sidebar
        self.btn_nav_dashboard.setText(f"  📊  {t('nav_dashboard')}")
        self.btn_nav_billing.setText(f"  🧾  {t('nav_new_bill')}")
        self.btn_nav_purchases.setText(f"  📦  {t('nav_purchases')}")
        self.btn_nav_customers.setText(f"  👥  {t('nav_customers')}")
        self.btn_nav_ledger.setText(f"  📖  {t('nav_ledger')}")
        self.btn_nav_bill_history.setText(f"  📜  {t('nav_bill_history')}")
        self.btn_nav_backup.setText(f"  💾  {t('nav_backup')}")

        # 3. Retranslate All Views
        self.dashboard_view.retranslate_ui()
        self.billing_view.retranslate_ui()
        self.purchases_view.retranslate_ui()
        self.customers_view.retranslate_ui()
        self.ledger_view.retranslate_ui()
        self.bill_history_view.update_translations()

    def on_backup_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "પેન ડ્રાઈવ અથવા ફોલ્ડર પસંદ કરો (Select Backup Folder)")
        if folder:
            backup_file = backup_database(folder)
            QMessageBox.information(self, "Backup Success", f"{t('msg_backup_success')}\n\n{backup_file}")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
