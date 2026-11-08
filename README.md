# Soni Natvarlal Himmatlal - Jewelry Billing & Udhar/Jama Accounting Software
### સોની નટવરલાલ હિંમતલાલ - જ્વેલરી બિલિંગ અને ખાતાવહી સોફ્ટવેર

A modern, 100% offline desktop billing, inventory, and Khata (Credit/Debit) accounting software built with **Python 3.12**, **PySide6 (Qt6)**, and **SQLite**, designed specifically for traditional Indian retail and wholesale gold/silver jewellers.

---

## 🌟 Key Features

### 1. POS Billing & Item Management
- **Bilingual UI:** Seamless toggle between English and Gujarati across all screens, tables, and dialogs.
- **Smart HSN Selection:** Preset dropdown for standard Indian GST Chapter 71 & 74 HSN codes:
  - `7113`: Gold & Silver Jewellery (સોના-ચાંદીના દાગીના)
  - `7108`: Gold Bullion / Ingot / Lagdi / Biscuit (સોનાની લગડી/બિસ્કિટ)
  - `7106`: Silver Ingot / Bullion / Lagdi / Chorsa (ચાંદીની લગડી/ચોરસા)
  - `7114`: Silver Utensils & Articles (ચાંદીના વાસણ/પૂજા સામગ્રી)
  - `7118`: Gold & Silver Coins (સોના-ચાંદીના સિક્કા)
  - `7117`: Imitation / Fashion Jewellery (આર્ટિફિશિયલ દાગીના)
  - `7418`: Copper Utensils & Articles (તાંબાના વાસણ/પૂજા પાત્ર)
  - `7403`: Refined Copper / Alloys (શુદ્ધ તાંબુ/મિશ્ર ધાતુ)
- **Keyboard-Only Rapid Billing:** Full `Enter`-key navigation allows cashiers and owners to complete entire bills without touching the mouse or `Tab` key.
- **Automatic Price Calculation:** Net weight in grams $\times$ Rate + Making charges + 3% GST (1.5% CGST + 1.5% SGST).

### 2. Physical Bill Book Digital Twin (Tax Invoice PDF)
- **1:1 Replication:** Perfectly matches the official physical letterhead of Soni Natvarlal Himmatlal (Bavla, Ahmedabad).
- **Embedded Vector Logo:** Inline SVG rendition of the official terracotta & bronze `nh` monogram badge.
- **Strict 1-Page A4 Proportion:** High-contrast Deep Maroon (`#5C1D24`) and Warm Parchment styling, formatted to fit on a single A4 sheet without spilling.

### 3. Automated Local WhatsApp Dispatch
- Integrated local **Baileys Node.js bridge** runs silently in the background on port `5001`.
- Automatically delivers PDF tax invoices and itemized Gujarati delivery summaries to customers upon saving.
- Optional automatic CC / Owner copy dispatch to the shop owner's WhatsApp number.

### 4. Double-Entry Udhar / Jama Customer Khata
- Accurate ledger tracking based on Indian retail accounting norms (full bill as Debit, payments as Credit).
- Live calculation of total market outstanding without zeroing out by customer advances.
- 1-click repayments dialog with UPI UTR, Cheque, and Bank Transfer tracking.

### 5. Inward Wholesale Purchase Register & GST ITC Center
- Record supplier purchases of gold bars, silver bullion, and finished jewelry.
- Automatically calculates and tracks Input Tax Credit (ITC) for GST filing.

### 6. Bill History & Records Archive
- Filter historical invoices by All Time, Today, This Month, Financial Year, or Custom Date Range.
- Live period metrics (Total Sales, Collected Cash/UPI, Pending Udhar).
- 1-click View, Reprint, and WhatsApp Resend actions.

---

## 🛠️ Tech Stack
- **Frontend / GUI:** PySide6 (Qt for Python 6)
- **Database:** SQLite (Embedded, zero setup, foreign-key enforced)
- **PDF Engine:** PySide6.QtPrintSupport & PySide6.QtPdf
- **WhatsApp Bridge:** Node.js + @whiskeysockets/baileys (100% free, no third-party paid API)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ (for WhatsApp bridge)

### Setup & Run
1. Install Python dependencies:
   ```bash
   pip install PySide6 qrcode requests
   ```
2. Install WhatsApp bridge dependencies:
   ```bash
   cd bridge
   npm install
   cd ..
   ```
3. Launch the desktop application:
   ```bash
   START_APP.bat
   # or
   python main.py
   ```

---

## 🔒 Security & Privacy
- **100% Offline Database:** All customer KYC, transactions, and bill histories reside locally on disk in `jewelry_shop.db`.
- **No Cloud Dependency:** Zero external database servers or recurring subscription costs.
