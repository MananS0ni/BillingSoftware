"""
whatsapp_dialog.py - WhatsApp Connection & QR/Pairing Code Modal Dialog.
Provides TWO seamless linking methods:
1. 8-digit Pairing Code ("Link with phone number instead") - Zero camera scan needed!
2. High-contrast, razor-sharp 290x290 QR Code with FastTransformation (no blur).
Also manages Father's / Owner WhatsApp notification settings.
"""

import base64
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox,
    QLineEdit, QCheckBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage

from translations import t, get_language
from whatsapp_manager import (
    get_whatsapp_status, ensure_bridge_running, logout_whatsapp, request_pairing_code
)
from settings_manager import load_settings, save_settings

class WhatsAppDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WhatsApp Auto-Bill Connect")
        self.setFixedSize(560, 760)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F7F4;
                font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                background-color: transparent;
            }
            QTabWidget::pane {
                border: 1.5px solid #E2D9C8;
                border-radius: 8px;
                background-color: #FFFFFF;
                top: -1px;
            }
            QTabBar::tab {
                background: #EDE8DE;
                color: #55625D;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 18px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #12382C;
                border: 1.5px solid #E2D9C8;
                border-bottom: 1.5px solid #FFFFFF;
            }
        """)

        ensure_bridge_running()
        self.init_ui()

        # Timer to poll status every 2 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2000)

        # Initial fetch
        self.refresh_status()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        # 1. Title Header
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_text = "📲 WhatsApp Automatic Billing" if get_language() == "en" else "📲 WhatsApp ઓટોમેટિક બિલિંગ"
        sub_text = "Connect once; every invoice is automatically sent to the customer and owner." if get_language() == "en" else "એકવાર જોડો, પછી દરેક બિલ ગ્રાહક અને પિતાશ્રીને આપોઆપ મોકલાશે."
        
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0B1E19;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        header_box.addWidget(self.lbl_title)

        self.lbl_sub = QLabel(sub_text)
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #6E7A75;")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        header_box.addWidget(self.lbl_sub)
        layout.addLayout(header_box)

        # 2. Status Frame
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("background-color: #FFFFFF; border: 1.5px solid #E8E4DC; border-radius: 8px; padding: 6px;")
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(8, 6, 8, 6)
        self.lbl_status = QLabel("Checking status..." if get_language() == "en" else "તપાસી રહ્યું છે...")
        self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #1A2521;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.lbl_status)
        layout.addWidget(self.status_frame)

        # 3. Success Card (Shown only when connected)
        self.success_card = QFrame()
        self.success_card.setStyleSheet("background-color: #F0FDF4; border: 2px solid #86EFAC; border-radius: 10px; padding: 16px;")
        succ_layout = QVBoxLayout(self.success_card)
        succ_layout.setSpacing(8)
        self.lbl_succ_title = QLabel("🎉 WhatsApp Connected Successfully!" if get_language() == "en" else "🎉 WhatsApp સફળતાપૂર્વક જોડાયેલું છે!")
        self.lbl_succ_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #166534;")
        self.lbl_succ_title.setAlignment(Qt.AlignCenter)
        succ_layout.addWidget(self.lbl_succ_title)

        self.lbl_succ_desc = QLabel(
            "Every invoice generated will be sent directly to the customer and owner's WhatsApp."
            if get_language() == "en" else
            "હવે તમે જે પણ બિલ બનાવશો (Save & Print અથવા Save Without Print),\nતે ગ્રાહક અને પિતાશ્રી બંનેના WhatsApp પર આપોઆપ પહોંચી જશે."
        )
        self.lbl_succ_desc.setStyleSheet("font-size: 12px; color: #14532D; line-height: 1.4;")
        self.lbl_succ_desc.setAlignment(Qt.AlignCenter)
        succ_layout.addWidget(self.lbl_succ_desc)
        self.success_card.setVisible(False)
        layout.addWidget(self.success_card)

        # 4. Tab Widget for Linking Methods
        self.tabs = QTabWidget()

        # TAB A: 8-digit Pairing Code (Recommended - No Camera Needed)
        self.tab_code = QWidget()
        tab_code_layout = QVBoxLayout(self.tab_code)
        tab_code_layout.setContentsMargins(16, 14, 16, 14)
        tab_code_layout.setSpacing(10)

        tip_msg = "💡 No camera needed! Enter phone number to get 8-digit code:" if get_language() == "en" else "💡 કેમેરા સ્કેન કરવાની જરૂર નથી! ફક્ત તમારો નંબર દાખલ કરી કોડ મેળવો:"
        lbl_code_tip = QLabel(tip_msg)
        lbl_code_tip.setWordWrap(True)
        lbl_code_tip.setStyleSheet("font-size: 12px; color: #166534; font-weight: bold; background-color: #DCFCE7; padding: 8px; border-radius: 6px;")
        tab_code_layout.addWidget(lbl_code_tip)

        # Phone input + Button row
        row_phone = QHBoxLayout()
        row_phone.setSpacing(8)
        self.txt_pair_phone = QLineEdit()
        self.txt_pair_phone.setMaxLength(10)
        self.txt_pair_phone.setPlaceholderText("Your 10-digit WhatsApp number..." if get_language() == "en" else "તમારો ૧૦ આંકડાનો WhatsApp નંબર...")
        self.txt_pair_phone.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
                color: #0F172A;
            }
            QLineEdit:focus {
                border-color: #12382C;
            }
        """)
        # Pre-fill from settings
        saved_owner = load_settings().get("owner_phone", "")
        if saved_owner:
            self.txt_pair_phone.setText(saved_owner)
        row_phone.addWidget(self.txt_pair_phone, stretch=3)

        self.btn_get_code = QPushButton(t("wa_btn_get_code"))
        self.btn_get_code.setStyleSheet("""
            QPushButton {
                background-color: #D4AF37;
                color: #0B1E19;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 8px 16px;
                border: 1px solid #B89628;
            }
            QPushButton:hover {
                background-color: #C39E2E;
            }
        """)
        self.btn_get_code.setCursor(Qt.PointingHandCursor)
        self.btn_get_code.clicked.connect(self.on_request_pairing_code)
        row_phone.addWidget(self.btn_get_code, stretch=2)
        tab_code_layout.addLayout(row_phone)

        # Large Code Display Box
        self.code_box = QFrame()
        self.code_box.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #94A3B8; border-radius: 8px; padding: 12px;")
        code_box_layout = QVBoxLayout(self.code_box)
        code_box_layout.setSpacing(4)
        
        code_prompt = "Enter phone number above and click 'Get Code'" if get_language() == "en" else "ઉપર નંબર લખી 'કોડ મેળવો' બટન દબાવો"
        self.lbl_code_display = QLabel(code_prompt)
        self.lbl_code_display.setAlignment(Qt.AlignCenter)
        self.lbl_code_display.setStyleSheet("font-size: 14px; color: #64748B; font-weight: bold;")
        code_box_layout.addWidget(self.lbl_code_display)
        tab_code_layout.addWidget(self.code_box)

        # Steps for pairing code
        inst_code = QFrame()
        inst_code.setStyleSheet("background-color: #F8F9FA; border: 1px solid #E9ECEF; border-radius: 6px; padding: 8px;")
        inst_code_layout = QVBoxLayout(inst_code)
        inst_code_layout.setSpacing(4)

        if get_language() == "en":
            lbl_ic_title = QLabel("📌 Steps to enter code on phone:")
            lbl_s1 = QLabel("1. Open WhatsApp on your phone")
            lbl_s2 = QLabel("2. Tap menu (⋮) -> Linked Devices")
            lbl_s3 = QLabel("3. Tap 'Link a Device'")
            lbl_s4 = QLabel("4. Tap 'Link with phone number instead' at the bottom")
            lbl_s5 = QLabel("5. Enter your phone number and this 8-digit code. Linked instantly!")
        else:
            lbl_ic_title = QLabel("📌 ફોનમાં કોડ દાખલ કરવાની રીત:")
            lbl_s1 = QLabel("૧. ફોનમાં WhatsApp ખોલો")
            lbl_s2 = QLabel("૨. જમણી બાજુ ત્રણ ટપકાં (⋮) -> Linked Devices પર જાઓ")
            lbl_s3 = QLabel("૩. 'Link a Device' દબાવો")
            lbl_s4 = QLabel("૪. નીચે 'Link with phone number instead' (નંબર વડે લિંક કરો) દબાવો")
            lbl_s5 = QLabel("૫. તમારો નંબર લખી આ ૮ અક્ષરનો કોડ લખો. તરત કનેક્ટ થઈ જશે!")

        lbl_ic_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #1E293B;")
        lbl_s1.setStyleSheet("font-size: 11px; color: #334155;")
        lbl_s2.setStyleSheet("font-size: 11px; color: #334155;")
        lbl_s3.setStyleSheet("font-size: 11px; color: #334155;")
        lbl_s4.setStyleSheet("font-size: 11px; color: #0F766E; font-weight: bold;")
        lbl_s5.setStyleSheet("font-size: 11px; color: #15803D; font-weight: bold;")

        inst_code_layout.addWidget(lbl_ic_title)
        inst_code_layout.addWidget(lbl_s1)
        inst_code_layout.addWidget(lbl_s2)
        inst_code_layout.addWidget(lbl_s3)
        inst_code_layout.addWidget(lbl_s4)
        inst_code_layout.addWidget(lbl_s5)

        tab_code_layout.addWidget(inst_code)
        self.tabs.addTab(self.tab_code, "🔢 8-digit Pairing Code" if get_language() == "en" else "🔢 ૮-આંકડાના કોડથી જોડો (સરળ)")

        # TAB B: QR Code (Crisp, High-Resolution 290x290)
        self.tab_qr = QWidget()
        tab_qr_layout = QVBoxLayout(self.tab_qr)
        tab_qr_layout.setContentsMargins(12, 10, 12, 10)
        tab_qr_layout.setSpacing(8)

        # Crisp QR Box
        self.qr_box = QFrame()
        self.qr_box.setFixedSize(290, 290)
        self.qr_box.setStyleSheet("background-color: #FFFFFF; border: 2px solid #D4AF37; border-radius: 12px;")
        qr_layout = QVBoxLayout(self.qr_box)
        qr_layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_qr = QLabel("Loading QR code..." if get_language() == "en" else "QR કોડ લોડ થઈ રહ્યો છે...")
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        self.lbl_qr.setStyleSheet("color: #6E7A75; font-size: 13px;")
        qr_layout.addWidget(self.lbl_qr)

        tab_qr_layout.addWidget(self.qr_box, alignment=Qt.AlignCenter)

        # Quick QR steps
        qr_steps_text = "1. Open WhatsApp  •  2. Linked Devices -> Link a Device  •  3. Scan QR Code" if get_language() == "en" else "૧. WhatsApp ખોલો  •  ૨. Linked Devices -> Link a Device  •  ૩. QR સ્કેન કરો"
        inst_qr = QLabel(qr_steps_text)
        inst_qr.setAlignment(Qt.AlignCenter)
        inst_qr.setStyleSheet("font-size: 11px; color: #166534; font-weight: bold; background-color: #F0FDF4; padding: 6px; border-radius: 6px;")
        tab_qr_layout.addWidget(inst_qr)

        self.tabs.addTab(self.tab_qr, "📷 Scan QR Code" if get_language() == "en" else "📷 QR કોડ સ્કેન કરો")
        layout.addWidget(self.tabs)

        # 5. Owner / Father's Phone Notification Frame
        self.owner_frame = QFrame()
        self.owner_frame.setStyleSheet("background-color: #FFFFFF; border: 1.5px solid #E8E4DC; border-radius: 8px; padding: 8px 12px;")
        owner_layout = QVBoxLayout(self.owner_frame)
        owner_layout.setContentsMargins(4, 4, 4, 4)
        owner_layout.setSpacing(6)

        owner_title_text = "👑 Owner / Father's WhatsApp Copy Alert:" if get_language() == "en" else "👑 પિતાશ્રી / ઓનર વોટ્સએપ કોપી (Owner Copy Alert):"
        lbl_owner_title = QLabel(owner_title_text)
        lbl_owner_title.setStyleSheet("font-weight: bold; color: #0B1E19; font-size: 12px;")
        owner_layout.addWidget(lbl_owner_title)

        row_owner = QHBoxLayout()
        self.txt_owner_phone = QLineEdit()
        self.txt_owner_phone.setMaxLength(10)
        self.txt_owner_phone.setPlaceholderText("Owner 10-digit mobile number..." if get_language() == "en" else "પિતાશ્રીનો ૧૦ આંકડાનો મોબાઇલ નંબર...")
        self.txt_owner_phone.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.txt_owner_phone.setText(load_settings().get("owner_phone", ""))
        self.txt_owner_phone.textChanged.connect(self.save_owner_settings)
        row_owner.addWidget(self.txt_owner_phone, stretch=3)

        self.chk_owner_copy = QCheckBox("Send every bill copy" if get_language() == "en" else "દરેક બિલ મોકલો")
        self.chk_owner_copy.setStyleSheet("font-size: 12px; font-weight: bold; color: #12382C;")
        self.chk_owner_copy.setChecked(load_settings().get("send_owner_copy", True))
        self.chk_owner_copy.stateChanged.connect(self.save_owner_settings)
        row_owner.addWidget(self.chk_owner_copy, stretch=2)
        owner_layout.addLayout(row_owner)

        layout.addWidget(self.owner_frame)

        # 6. Bottom Buttons (Logout & Close)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_logout = QPushButton(t("wa_btn_disconnect"))
        self.btn_logout.setStyleSheet("background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.clicked.connect(self.on_logout)
        self.btn_logout.setVisible(False)
        btn_layout.addWidget(self.btn_logout)

        self.btn_close = QPushButton(t("btn_close"))
        self.btn_close.setStyleSheet("background-color: #12382C; color: #FFFFFF; border: 1.5px solid #D4AF37; border-radius: 6px; padding: 9px 24px; font-weight: bold; font-size: 14px;")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def on_request_pairing_code(self):
        phone = self.txt_pair_phone.text().strip()
        if not phone or len(phone) < 10:
            QMessageBox.warning(self, "નંબર અધૂરો છે", "કૃપા કરીને પૂરો ૧૦ આંકડાનો WhatsApp મોબાઇલ નંબર દાખલ કરો.")
            return

        self.btn_get_code.setEnabled(False)
        self.btn_get_code.setText("કોડ લાવી રહ્યું છે...")
        self.lbl_code_display.setText("⏳ કોડ જનરેટ થઈ રહ્યો છે...")
        self.lbl_code_display.setStyleSheet("font-size: 14px; color: #D97706; font-weight: bold;")

        # Run via QTimer singleShot or immediate call
        QTimer.singleShot(100, lambda: self._do_fetch_pairing_code(phone))

    def _do_fetch_pairing_code(self, phone: str):
        res = request_pairing_code(phone)
        self.btn_get_code.setEnabled(True)
        self.btn_get_code.setText("🔢 કોડ મેળવો (Get Code)")

        if res.get("success") and res.get("code"):
            raw_code = res.get("code")
            # Format nicely: e.g. "7K9P - MN42"
            formatted = f"{raw_code[:4]} - {raw_code[4:]}" if len(raw_code) == 8 else raw_code
            self.lbl_code_display.setText(formatted)
            self.lbl_code_display.setStyleSheet("""
                font-size: 30px;
                font-weight: bold;
                letter-spacing: 4px;
                color: #166534;
                background-color: #DCFCE7;
                border: 2px solid #86EFAC;
                border-radius: 8px;
                padding: 10px;
            """)
            # Also keep owner phone synced
            self.txt_owner_phone.setText(phone)
            self.save_owner_settings()
        else:
            err = res.get("error", "કોડ મેળવવામાં ભૂલ થઈ.")
            self.lbl_code_display.setText(f"❌ {err}")
            self.lbl_code_display.setStyleSheet("font-size: 13px; color: #DC2626; font-weight: bold;")

    def refresh_status(self):
        data = get_whatsapp_status()
        status = data.get("status", "offline")
        user = data.get("user")
        qr = data.get("qr")

        if status == "connected":
            phone_tag = user.get("id", "").split(":")[0] if user else ""
            status_text = f"🟢 WhatsApp Connected! (+{phone_tag})" if get_language() == "en" else f"🟢 WhatsApp જોડાયેલ છે! (+{phone_tag})"
            self.lbl_status.setText(status_text)
            self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #16A34A;")
            self.tabs.setVisible(False)
            self.success_card.setVisible(True)
            self.btn_logout.setVisible(True)
        elif status == "qr_ready" and qr:
            status_text = "🟡 Use pairing code or scan QR to connect" if get_language() == "en" else "🟡 જોડાવા માટે કોડ અથવા QR કોડ વાપરો"
            self.lbl_status.setText(status_text)
            self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #D97706;")
            self.render_qr(qr)
            self.tabs.setVisible(True)
            self.success_card.setVisible(False)
            self.btn_logout.setVisible(False)
        elif status == "connecting":
            status_text = "⏳ Connecting to WhatsApp..." if get_language() == "en" else "⏳ કનેક્શન શરૂ થઈ રહ્યું છે..."
            self.lbl_status.setText(status_text)
            self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #2563EB;")
            self.lbl_qr.setText("Please wait..." if get_language() == "en" else "કૃપા કરીને રાહ જુઓ...")
            self.btn_logout.setVisible(False)
        else:
            status_text = "🔴 Service starting..." if get_language() == "en" else "🔴 સર્વિસ શરૂ થઈ રહી છે..."
            self.lbl_status.setText(status_text)
            self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #DC2626;")
            self.lbl_qr.setText("Starting service..." if get_language() == "en" else "સર્વિસ શરૂ થઈ રહી છે...")
            ensure_bridge_running()

    def render_qr(self, qr_data_url: str):
        try:
            if "base64," in qr_data_url:
                base64_data = qr_data_url.split("base64,")[1]
            else:
                base64_data = qr_data_url

            img_bytes = base64.b64decode(base64_data)
            qimage = QImage.fromData(img_bytes)
            pixmap = QPixmap.fromImage(qimage)
            # Use FastTransformation (nearest neighbor) to keep crisp pure black/white edges without blurry antialiasing!
            scaled = pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.lbl_qr.setPixmap(scaled)
        except Exception:
            self.lbl_qr.setText("QR કોડ દર્શાવવામાં ભૂલ થઈ.")

    def on_logout(self):
        reply = QMessageBox.question(
            self, "Logout WhatsApp",
            "શું તમે ખરેખર WhatsApp અનલિંક કરવા માંગો છો?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            logout_whatsapp()
            self.refresh_status()

    def save_owner_settings(self):
        phone = self.txt_owner_phone.text().strip()
        save_settings({
            "owner_phone": phone,
            "send_owner_copy": self.chk_owner_copy.isChecked()
        })

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)
