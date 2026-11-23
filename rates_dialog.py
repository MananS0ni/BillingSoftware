"""
rates_dialog.py - Comprehensive Live Bullion Product Rate Master Dialog.
Displays all 7+ precious metal product categories cleanly without technical HSN codes:
- Gold Lagdi (24K Pure)
- Gold Ornaments (22K 916)
- Gold Jewellery (18K)
- Silver Lagdi / Chorsa (999)
- Silver Ornaments (Payal, Kada, Chains)
- Silver Utensils (Pooja Vasan, Thali, Kalash)
- Gold & Silver Coins

100% Bilingual in Gujarati and English.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from translations import t, get_language
from format_utils import format_inr
from rates_manager import get_rates_manager

class RatesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("dialog_rates_title"))
        self.resize(860, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F7F4;
                font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                background-color: transparent;
            }
            QTableWidget {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                gridline-color: #E2E8F0;
            }
            QTableWidget::item {
                color: #0F172A;
                padding: 6px 10px;
            }
            QHeaderView::section {
                background-color: #12382C;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 10px;
                border: none;
            }
            QPushButton#SecondaryBtn {
                background-color: #12382C;
                color: #FFFFFF;
                border: 1.5px solid #D4AF37;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #D4AF37;
                color: #0B1E19;
            }
        """)

        self.rates_mgr = get_rates_manager()
        self.init_ui()
        self.update_rates_display(self.rates_mgr.get_latest_rates())
        self.rates_mgr.rates_changed.connect(self.update_rates_display)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title
        top_box = QVBoxLayout()
        top_box.setSpacing(2)
        self.lbl_title = QLabel(t("dialog_rates_title"))
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0B1E19;")
        self.lbl_sub = QLabel(t("dialog_rates_sub"))
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #6E7A75;")
        top_box.addWidget(self.lbl_title)
        top_box.addWidget(self.lbl_sub)
        layout.addLayout(top_box)

        # Live Status Ribbon
        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("🟢 " + t("lbl_live_market"))
        self.lbl_status.setStyleSheet("font-weight: bold; color: #16A34A; font-size: 13px;")
        status_bar.addWidget(self.lbl_status)

        status_bar.addStretch()

        self.lbl_time = QLabel("")
        self.lbl_time.setStyleSheet("font-size: 12px; color: #64748B; font-style: italic;")
        status_bar.addWidget(self.lbl_time)
        layout.addLayout(status_bar)

        # Full Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            t("th_rate_product"),
            t("th_rate_purity"),
            t("th_rate_per_gram"),
            t("th_rate_bulk"),
            t("th_rate_movement")
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.table)

        # Close Button
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.btn_close = QPushButton(t("btn_close"))
        self.btn_close.setObjectName("SecondaryBtn")
        self.btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(self.btn_close)
        layout.addLayout(btn_bar)

    def update_rates_display(self, r: dict):
        if not r:
            return

        self.setWindowTitle(t("dialog_rates_title"))
        self.lbl_title.setText(t("dialog_rates_title"))
        self.lbl_sub.setText(t("dialog_rates_sub"))
        self.btn_close.setText(t("btn_close"))
        self.table.setHorizontalHeaderLabels([
            t("th_rate_product"),
            t("th_rate_purity"),
            t("th_rate_per_gram"),
            t("th_rate_bulk"),
            t("th_rate_movement")
        ])

        is_live = r.get("status") == "LIVE"
        self.lbl_status.setText("🟢 " + t("lbl_live_market") if is_live else t("lbl_rate_offline"))
        self.lbl_status.setStyleSheet("font-weight: bold; color: #16A34A; font-size: 13px;" if is_live else "font-weight: bold; color: #D97706; font-size: 13px;")
        self.lbl_time.setText(f"🕒 {r.get('timestamp', '')}")

        g_dir = r.get("gold_direction", "equal")
        s_dir = r.get("silver_direction", "equal")

        def make_mov(direction, chg_val):
            if direction == "up":
                item = QTableWidgetItem(f"▲ +₹{abs(chg_val):.2f}")
                item.setForeground(QColor("#16A34A")) # Green
            elif direction == "down":
                item = QTableWidgetItem(f"▼ -₹{abs(chg_val):.2f}")
                item.setForeground(QColor("#DC2626")) # Red
            else:
                item = QTableWidgetItem("=")
                item.setForeground(QColor("#64748B"))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            return item

        products = [
            (
                "🟡 " + t("rate_gold_24k"),
                "99.9% (24K)",
                format_inr(r.get("gold_24k_1g", 0)),
                f"{format_inr(r.get('gold_24k_10g', 0))} / 10g",
                make_mov(g_dir, r.get("gold_change", 0))
            ),
            (
                "🟠 " + t("rate_gold_22k"),
                "91.6% (916)",
                format_inr(r.get("gold_22k_1g", 0)),
                f"{format_inr(r.get('gold_22k_10g', 0))} / 10g",
                make_mov(g_dir, round(r.get("gold_change", 0) * 0.9167, 2))
            ),
            (
                "⚪ " + t("rate_gold_18k"),
                "75.0% (750)",
                format_inr(r.get("gold_18k_1g", 0)),
                "-",
                make_mov(g_dir, round(r.get("gold_change", 0) * 0.75, 2))
            ),
            (
                "🪙 " + t("rate_silver_lagdi"),
                "99.9% (Fine)",
                format_inr(r.get("silver_lagdi_1g", 0)),
                f"{format_inr(r.get('silver_lagdi_1kg', 0))} / 1kg",
                make_mov(s_dir, r.get("silver_change", 0))
            ),
            (
                "🥈 " + t("rate_silver_ornaments"),
                "92.5% (Sterling)",
                format_inr(r.get("silver_ornaments_1g", 0)),
                "-",
                make_mov(s_dir, round(r.get("silver_change", 0) * 0.925, 2))
            ),
            (
                "🍽️ " + t("rate_silver_utensils"),
                "85.0% (Pooja/Vasan)",
                format_inr(r.get("silver_utensils_1g", 0)),
                "-",
                make_mov(s_dir, round(r.get("silver_change", 0) * 0.85, 2))
            ),
            (
                "👑 " + t("rate_gold_coin"),
                "99.9% (24K)",
                format_inr(r.get("gold_coin_1g", 0)),
                "-",
                make_mov(g_dir, r.get("gold_change", 0))
            ),
            (
                "🪙 " + t("rate_silver_coin"),
                "99.9% (Pure)",
                format_inr(r.get("silver_coin_1g", 0)),
                "-",
                make_mov(s_dir, r.get("silver_change", 0))
            )
        ]

        self.table.setRowCount(0)
        for row_idx, (p_name, purity, r_1g, r_bulk, mov_item) in enumerate(products):
            self.table.insertRow(row_idx)

            # Product Name
            item_name = QTableWidgetItem(p_name)
            item_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item_name.setForeground(QColor("#0F172A"))
            self.table.setItem(row_idx, 0, item_name)

            # Purity
            item_pur = QTableWidgetItem(purity)
            item_pur.setTextAlignment(Qt.AlignCenter)
            item_pur.setForeground(QColor("#334155"))
            self.table.setItem(row_idx, 1, item_pur)

            # Rate 1g
            item_1g = QTableWidgetItem(r_1g)
            item_1g.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_1g.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item_1g.setForeground(QColor("#0F172A"))
            self.table.setItem(row_idx, 2, item_1g)

            # Rate bulk
            item_bulk = QTableWidgetItem(r_bulk)
            item_bulk.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_bulk.setForeground(QColor("#334155"))
            self.table.setItem(row_idx, 3, item_bulk)

            # Movement
            self.table.setItem(row_idx, 4, mov_item)
