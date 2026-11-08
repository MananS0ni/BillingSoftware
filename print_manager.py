"""
print_manager.py - Official Computerized GST Tax Invoice Generator.
Replicates the authentic Gujarati Jewelry Tax Invoice structure (Umiya Jewellers format)
styled with the deep maroon (#5C1D24) and warm terracotta (#B86B4B) theme of Soni Natvarlal Himmatlal:

- 3-Column Header: Monogram Logo ('nh') + Ref | Sacred Invocation & Complete Shop Branding | Page No & 'ORIGINAL FOR RECIPIENT'
- Tax Invoice Full-Width Bar
- Dual-Column Meta Table: Invoice No, Date, State (Gujarat 24) | Ledger Opening & Closing Balances (Dr/Cr)
- Receiver Card: Name, Address, Mobile, GSTIN & State
- 10-Column Itemized Jewelry Table:
    SNo | Product Description | HSN Code | Pcs | Gr Wt. | Net Wt | Rate | Amount | Labour | Taxable Value
- Bottom Totals Row: Pcs, Gross Wt, Net Wt, Amount, Labour, Taxable Value
- Left Summary: Voucher Desc, Full Amount in English Words (RUPEES ... ONLY), Guarantee Terms & Customer Signatory
- Right Calculation & Authorization:
    Net Amount, CGST 1.5%, SGST 1.5%, Grand Total, Paid Amount, Bill Outstanding Udhar,
    Statutory Certification, Shop Typography & Authorized Signatory
- Strictly engineered to fit on 1 single page of A4.
"""

import os
import re
import base64
from typing import Optional, Dict

from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QImage, QPainter, QColor
from PySide6.QtCore import QSizeF, QMarginsF, QByteArray, QBuffer, QIODevice
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtSvg import QSvgRenderer

from format_utils import format_inr, num_to_words_inr
from settings_manager import load_settings

_CACHED_LOGO_B64 = None

def get_nh_logo_base64() -> str:
    """Generates the official 'nh' jewelry emblem at crisp vector resolution encoded in base64."""
    global _CACHED_LOGO_B64
    if _CACHED_LOGO_B64:
        return _CACHED_LOGO_B64
    try:
        svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="300" height="300">
          <circle cx="60" cy="60" r="58" fill="#FCFAF6" stroke="#96101B" stroke-width="1.2"/>
          <circle cx="60" cy="60" r="54.5" fill="none" stroke="#E7960F" stroke-width="1.5"/>
          <circle cx="60" cy="60" r="51" fill="none" stroke="#96101B" stroke-width="0.8" stroke-dasharray="2, 2"/>
          
          <!-- Outer decorative jewelry beads -->
          <circle cx="112.8" cy="60.0" r="1.1" fill="#96101B"/><circle cx="105.8" cy="73.7" r="1.1" fill="#96101B"/>
          <circle cx="97.3" cy="86.4" r="1.1" fill="#96101B"/><circle cx="86.4" cy="97.3" r="1.1" fill="#96101B"/>
          <circle cx="73.7" cy="105.8" r="1.1" fill="#96101B"/><circle cx="60.0" cy="112.8" r="1.1" fill="#96101B"/>
          <circle cx="46.3" cy="105.8" r="1.1" fill="#96101B"/><circle cx="33.6" cy="97.3" r="1.1" fill="#96101B"/>
          <circle cx="22.7" cy="86.4" r="1.1" fill="#96101B"/><circle cx="14.2" cy="73.7" r="1.1" fill="#96101B"/>
          <circle cx="7.2" cy="60.0" r="1.1" fill="#96101B"/><circle cx="14.2" cy="46.3" r="1.1" fill="#96101B"/>
          <circle cx="22.7" cy="33.6" r="1.1" fill="#96101B"/><circle cx="33.6" cy="22.7" r="1.1" fill="#96101B"/>
          <circle cx="46.3" cy="14.2" r="1.1" fill="#96101B"/><circle cx="60.0" cy="7.2" r="1.1" fill="#96101B"/>
          <circle cx="73.7" cy="14.2" r="1.1" fill="#96101B"/><circle cx="86.4" cy="22.7" r="1.1" fill="#96101B"/>
          <circle cx="97.3" cy="33.6" r="1.1" fill="#96101B"/><circle cx="105.8" cy="46.3" r="1.1" fill="#96101B"/>

          <!-- Inner Monogram matching authentic shop emblem -->
          <g transform="translate(21, 23) scale(0.78)">
            <!-- 'n' Left Stem and top tab in Warm Gold (#E7960F) -->
            <path d="M 6 14 L 25 14 L 25 25 L 18 25 L 18 84 L 6 84 Z" fill="#E7960F"/>
            
            <!-- 'n' Arch and Bottom Baseline in Warm Gold (#E7960F) -->
            <path d="M 28 14 L 37 14 C 44 14 46 16 46 24 L 46 72 L 94 72 L 94 84 L 28 84 Z" fill="#E7960F"/>
            
            <!-- 'h' Stepped Center in Royal Maroon (#96101B) -->
            <path d="M 73 14 L 94 14 L 94 45 L 68 45 L 68 72 L 50 72 L 50 34 L 73 34 Z" fill="#96101B"/>
            
            <!-- Top-Left 12 Maroon Dots (3 columns x 4 rows) -->
            <circle cx="53" cy="11" r="2.2" fill="#96101B"/><circle cx="59" cy="11" r="2.2" fill="#96101B"/><circle cx="65" cy="11" r="2.2" fill="#96101B"/>
            <circle cx="53" cy="17" r="2.2" fill="#96101B"/><circle cx="59" cy="17" r="2.2" fill="#96101B"/><circle cx="65" cy="17" r="2.2" fill="#96101B"/>
            <circle cx="53" cy="23" r="2.2" fill="#96101B"/><circle cx="59" cy="23" r="2.2" fill="#96101B"/><circle cx="65" cy="23" r="2.2" fill="#96101B"/>
            <circle cx="53" cy="29" r="2.2" fill="#96101B"/><circle cx="59" cy="29" r="2.2" fill="#96101B"/><circle cx="65" cy="29" r="2.2" fill="#96101B"/>
            
            <!-- Bottom-Right 9 Maroon Dots (3 columns x 3 rows) -->
            <circle cx="79" cy="50" r="2.2" fill="#96101B"/><circle cx="85" cy="50" r="2.2" fill="#96101B"/><circle cx="91" cy="50" r="2.2" fill="#96101B"/>
            <circle cx="79" cy="56" r="2.2" fill="#96101B"/><circle cx="85" cy="56" r="2.2" fill="#96101B"/><circle cx="91" cy="56" r="2.2" fill="#96101B"/>
            <circle cx="79" cy="62" r="2.2" fill="#96101B"/><circle cx="85" cy="62" r="2.2" fill="#96101B"/><circle cx="91" cy="62" r="2.2" fill="#96101B"/>
          </g>
        </svg>"""
        renderer = QSvgRenderer(QByteArray(svg_code.encode('utf-8')))
        img = QImage(360, 360, QImage.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        p = QPainter(img)
        renderer.render(p)
        p.end()

        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG")
        _CACHED_LOGO_B64 = base64.b64encode(buf.data().data()).decode()
        return _CACHED_LOGO_B64
    except Exception as e:
        print(f"[Logo Error] {e}")
        return ""

def generate_bill_html(bill_data: dict, shop_settings: dict = None) -> str:
    """
    Generates the official Computerized GST Tax Invoice HTML strictly structured
    like the traditional Gujarat jewelry tax invoice (Umiya Jewellers pattern) with
    Soni Natvarlal Himmatlal's deep maroon and terracotta visual identity.
    """
    if not shop_settings:
        st = load_settings()
        shop_settings = {
            "header_left": st.get("header_left", "વાયુ આદિતી"),
            "header_center": st.get("header_center", "॥ શ્રી હરિ ॥"),
            "header_right": st.get("header_right", "બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫"),
            "phone_display": st.get("owner_phone_display", "98251 62065"),
            "shop_name_en": st.get("shop_name_en", "SONI NATVARLAL HIMMATLAL"),
            "shop_name_gu": st.get("shop_name_gu", "સોની નટવરલાલ હિંમતલાલ"),
            "proprietor": st.get("proprietor", "સોની બ્રિજેશ નટવરલાલ"),
            "tagline": st.get("tagline", "સોના-ચાંદીના દાગીના બનાવનાર તથા વેચનાર."),
            "address": st.get("address", "જૈન દેરાસર પાસે, મેઈન બજાર, બાવળા-૩૮૨૨૨૦. જી. અમદાવાદ."),
            "gstin": st.get("gstin", "24BPXPS8279A1Z7"),
            "state": "Gujarat",
            "state_code": "24"
        }

    logo_b64 = get_nh_logo_base64()
    bill_no = bill_data.get("bill_no", 1)
    bill_no_display = f"T1-{bill_no:05d}"
    bill_date = bill_data.get("bill_date", "")

    # Customer Information
    cust_name = bill_data.get("customer_name", "") or bill_data.get("name_gu", "")
    if bill_data.get("name_en") and bill_data.get("name_en") != cust_name:
        cust_name_display = f"{cust_name} ({bill_data.get('name_en')})"
    else:
        cust_name_display = cust_name

    cust_addr = bill_data.get("customer_address", "") or bill_data.get("address", "") or "-"
    cust_phone = bill_data.get("customer_mobile", "") or bill_data.get("mobile", "") or "-"
    cust_gstin = bill_data.get("gstin", "") or "URP (Unregistered)"

    # Ledger Opening & Closing Balances
    opening_bal_paise = bill_data.get("opening_balance_paise", 0)
    closing_bal_paise = bill_data.get("closing_balance_paise", bill_data.get("balance_paise", 0))

    if opening_bal_paise >= 0:
        opening_bal_str = f"{format_inr(opening_bal_paise / 100.0, symbol='')} Dr"
    else:
        opening_bal_str = f"{format_inr(abs(opening_bal_paise) / 100.0, symbol='')} Cr"

    if closing_bal_paise >= 0:
        closing_bal_str = f"{format_inr(closing_bal_paise / 100.0, symbol='')} Dr"
    else:
        closing_bal_str = f"{format_inr(abs(closing_bal_paise) / 100.0, symbol='')} Cr"

    items = bill_data.get("items", [])
    items_html = ""
    tot_pcs = 0
    tot_gr_wt = 0.0
    tot_net_wt = 0.0
    tot_amt = 0.0
    tot_labour = 0.0
    tot_taxable = 0.0

    for idx, item in enumerate(items):
        pcs = item.get("pcs", 1)
        wt_g = item.get("weight_mg", 0) / 1000.0
        gr_wt_g = item.get("gross_weight_mg", item.get("weight_mg", 0)) / 1000.0
        rate_rs = item.get("rate_paise", 0) / 100.0
        making_rs = item.get("making_paise", 0) / 100.0
        amount_rs = item.get("amount_paise", 0) / 100.0
        base_amt_rs = max(0.0, amount_rs - making_rs) if making_rs > 0 else amount_rs
        taxable_rs = amount_rs
        hsn_val = item.get("hsn_code", "") or "7113"

        tot_pcs += pcs
        tot_gr_wt += gr_wt_g
        tot_net_wt += wt_g
        tot_amt += base_amt_rs
        tot_labour += making_rs
        tot_taxable += taxable_rs

        items_html += f"""
        <tr>
            <td style="text-align: center; border-left: 1px solid #5C1D24; border-right: 1px solid #5C1D24; padding: 2.5px 2px; font-size: 7.5pt;">{idx + 1}</td>
            <td style="text-align: left; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-weight: bold; font-size: 7.5pt; color: #2C1810;">{item.get('description', '')}</td>
            <td style="text-align: center; border-right: 1px solid #5C1D24; padding: 2.5px 2px; font-size: 7pt; color: #444444;">{hsn_val}</td>
            <td style="text-align: center; border-right: 1px solid #5C1D24; padding: 2.5px 2px; font-size: 7.5pt;">{pcs}</td>
            <td style="text-align: right; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-size: 7.5pt;">{gr_wt_g:.3f}</td>
            <td style="text-align: right; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-weight: bold; font-size: 7.5pt;">{wt_g:.3f}</td>
            <td style="text-align: right; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-size: 7.5pt;">{rate_rs:,.2f}</td>
            <td style="text-align: right; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-size: 7.5pt;">{base_amt_rs:,.2f}</td>
            <td style="text-align: right; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-size: 7.5pt;">{making_rs:,.2f}</td>
            <td style="text-align: right; border-right: 1px solid #5C1D24; padding: 2.5px 4px; font-weight: bold; font-size: 7.5pt; color: #5C1D24;">{taxable_rs:,.2f}</td>
        </tr>
        """

    # Extra filler rows to give the authentic invoice grid look without causing page overflow
    fill_count = max(0, 2 - len(items))
    for _ in range(fill_count):
        items_html += """
        <tr>
            <td style="border-left: 1px solid #5C1D24; border-right: 1px solid #5C1D24; height: 12px;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
            <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
        </tr>
        """

    subtotal_rs = bill_data.get("subtotal_paise", 0) / 100.0
    cgst_rs = bill_data.get("cgst_paise", 0) / 100.0
    sgst_rs = bill_data.get("sgst_paise", 0) / 100.0
    grand_rs = bill_data.get("grand_total_paise", 0) / 100.0
    paid_rs = bill_data.get("paid_paise", 0) / 100.0
    balance_rs = bill_data.get("balance_paise", 0) / 100.0

    words_inr = num_to_words_inr(grand_rs)

    payment_mode = bill_data.get("payment_mode", "CASH")
    payment_ref = bill_data.get("payment_ref", "")
    vch_desc = payment_mode
    if payment_ref:
        vch_desc += f" (Ref: {payment_ref})"

    paid_mode_label = "Chq Amount :" if "CHQ" in payment_mode or "CHEQUE" in payment_mode else "Paid Amount :"
    outstanding_color = "#DC2626" if balance_rs > 0 else "#16A34A"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Noto Sans Gujarati', 'Segoe UI', Arial, sans-serif;
        margin: 0;
        padding: 0;
        color: #2C1810;
        background-color: #FFFFFF;
        font-size: 7.5pt;
    }}
    .outer-table {{
        width: 100%;
        border: 1.5px solid #5C1D24;
        border-collapse: collapse;
    }}
    .tax-invoice-bar {{
        background-color: #5C1D24;
        color: #FFFFFF;
        text-align: center;
        font-weight: bold;
        font-size: 9.5pt;
        padding: 2.5px 0;
        letter-spacing: 1.5px;
    }}
    .meta-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .meta-table td {{
        padding: 2.5px 4px;
        font-size: 7.2pt;
        line-height: 1.25;
        vertical-align: top;
    }}
    .receiver-header {{
        font-weight: bold;
        font-size: 7.5pt;
        color: #5C1D24;
        background-color: #FBF5F0;
        padding: 2px 4px;
        border-top: 1px solid #5C1D24;
        border-bottom: 1px solid #5C1D24;
    }}
    .receiver-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .receiver-table td {{
        padding: 1.5px 4px;
        font-size: 7.2pt;
        line-height: 1.25;
    }}
    .items-table {{
        width: 100%;
        border-collapse: collapse;
        border-top: 1.2px solid #5C1D24;
    }}
    .items-table th {{
        background-color: #5C1D24;
        color: #FFFFFF;
        font-size: 6.8pt;
        font-weight: bold;
        padding: 3px 2px;
        border: 1px solid #5C1D24;
        text-align: center;
    }}
    .totals-row td {{
        border-top: 1.2px solid #5C1D24;
        border-bottom: 1.2px solid #5C1D24;
        border-left: 1px solid #5C1D24;
        border-right: 1px solid #5C1D24;
        background-color: #FBF5F0;
        font-weight: bold;
        font-size: 7.2pt;
        padding: 2.5px 3px;
    }}
    .calc-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .calc-table td {{
        border: 1px solid #5C1D24;
        padding: 2px 4px;
        font-size: 7.2pt;
        line-height: 1.2;
    }}
    .grand-row td {{
        background-color: #F6ECE6;
        font-weight: bold;
        color: #5C1D24;
        font-size: 8pt;
    }}
</style>
</head>
<body>

<table class="outer-table">
    <!-- 1. Top Three-Column Header (Logo | Shop Header | Page & Original For Recipient) -->
    <tr>
        <td style="width: 18%; border-right: 1px solid #5C1D24; text-align: center; vertical-align: middle; padding: 2px;">
            <img src="data:image/png;base64,{logo_b64}" width="52" height="52"/><br>
            <span style="font-size: 7.5pt; font-weight: bold; color: #5C1D24;">{bill_no_display}</span>
        </td>
        <td style="width: 62%; border-right: 1px solid #5C1D24; text-align: center; vertical-align: top; padding: 2px 5px;">
            <div style="font-size: 7pt; font-weight: bold; color: #5C1D24; letter-spacing: 0.5px;">
                {shop_settings['header_left']} &nbsp;&nbsp;|&nbsp;&nbsp; {shop_settings['header_center']} &nbsp;&nbsp;|&nbsp;&nbsp; {shop_settings['header_right']}
            </div>
            <div style="font-size: 13.5pt; font-weight: bold; color: #5C1D24; letter-spacing: 0.5px; margin-top: 1px; line-height: 1.1;">
                {shop_settings['shop_name_en']}
            </div>
            <div style="font-size: 8.5pt; font-weight: bold; color: #5C1D24; margin-top: 0px;">
                {shop_settings['shop_name_gu']}
            </div>
            <div style="font-size: 7pt; font-weight: bold; color: #B86B4B; margin-top: 0px;">
                પ્રોપરાઇટર : {shop_settings['proprietor']} &nbsp;|&nbsp; {shop_settings['tagline']}
            </div>
            <div style="font-size: 7pt; color: #2C1810; margin-top: 0px;">
                {shop_settings['address']}
            </div>
            <div style="font-size: 7pt; color: #2C1810;">
                BAVLA &nbsp; Mo : {shop_settings['phone_display']} &nbsp;&nbsp; Ph : {shop_settings['phone_display']}
            </div>
            <div style="font-size: 7.5pt; font-weight: bold; color: #5C1D24; margin-top: 0px;">
                GSTIN : {shop_settings['gstin']}
            </div>
        </td>
        <td style="width: 20%; vertical-align: top; padding: 2px 4px;">
            <div style="text-align: right; font-size: 8pt; font-weight: bold; color: #2C1810;">1</div>
            <div style="text-align: center; font-size: 7.5pt; font-weight: bold; color: #5C1D24; margin-top: 8px; line-height: 1.25;">
                ORIGINAL FOR<br>RECIPIENT
            </div>
        </td>
    </tr>

    <!-- 2. Tax Invoice Banner -->
    <tr>
        <td colspan="3" class="tax-invoice-bar">Tax Invoice</td>
    </tr>

    <!-- 3. Metadata Table (Invoice No, Date, State | Ledger Opening & Closing Bal) -->
    <tr>
        <td colspan="3" style="padding: 0;">
            <table class="meta-table">
                <tr>
                    <td style="width: 58%; border-right: 1px solid #5C1D24; border-bottom: 1px solid #5C1D24;">
                        <b>Invoice No :</b> <span style="font-weight: bold; color: #5C1D24;">{bill_no_display}</span><br>
                        <b>Invoice Date :</b> <span style="font-weight: bold;">{bill_date}</span><br>
                        <b>State :</b> {shop_settings['state']} (Code: {shop_settings['state_code']})
                    </td>
                    <td style="width: 42%; border-bottom: 1px solid #5C1D24; padding-left: 6px; padding-right: 4px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 1px 0; font-size: 7.2pt;"><b>Ledger Opening Bal :</b></td>
                                <td style="padding: 1px 0; text-align: right; font-weight: bold; font-size: 7.2pt;">{opening_bal_str}</td>
                            </tr>
                            <tr>
                                <td style="padding: 1px 0; font-size: 7.2pt;"><b>Ledger Closing Bal :</b></td>
                                <td style="padding: 1px 0; text-align: right; font-weight: bold; font-size: 7.2pt;">{closing_bal_str}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- 4. Details of Receiver (Billed to) -->
    <tr>
        <td colspan="3" class="receiver-header">Details of Receiver (Billed to) :</td>
    </tr>
    <tr>
        <td colspan="3" style="padding: 0;">
            <table class="receiver-table">
                <tr>
                    <td style="width: 14%; font-weight: bold; color: #5C1D24;">Name :</td>
                    <td colspan="3" style="width: 86%; font-weight: bold; font-size: 8.2pt; color: #2C1810;">{cust_name_display}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #5C1D24;">Address :</td>
                    <td colspan="3">{cust_addr}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #5C1D24;">Mobile :</td>
                    <td colspan="3" style="font-weight: bold;">{cust_phone}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #5C1D24;">GSTIN :</td>
                    <td style="width: 48%; font-weight: bold;">{cust_gstin}</td>
                    <td style="width: 12%; font-weight: bold; color: #5C1D24; text-align: right;">State :</td>
                    <td style="width: 26%; padding-left: 4px;">Gujarat</td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- 5. Itemized Table (Exact 10 columns matching authentic jewelry tax invoice) -->
    <tr>
        <td colspan="3" style="padding: 0;">
            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width: 4%;">SNo</th>
                        <th style="width: 27%; text-align: left; padding-left: 4px;">Product Description</th>
                        <th style="width: 8%;">HSN Code</th>
                        <th style="width: 5%;">Pcs</th>
                        <th style="width: 8%; text-align: right; padding-right: 3px;">Gr Wt.</th>
                        <th style="width: 8%; text-align: right; padding-right: 3px;">Net Wt</th>
                        <th style="width: 11%; text-align: right; padding-right: 3px;">Rate</th>
                        <th style="width: 12%; text-align: right; padding-right: 3px;">Amount</th>
                        <th style="width: 9%; text-align: right; padding-right: 3px;">Labour</th>
                        <th style="width: 13%; text-align: right; padding-right: 3px;">Taxable Value</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                    <!-- Totals Row -->
                    <tr class="totals-row">
                        <td colspan="3" style="text-align: center; border-right: 1px solid #5C1D24;">&nbsp;</td>
                        <td style="text-align: center; border-right: 1px solid #5C1D24;">{tot_pcs}</td>
                        <td style="text-align: right; border-right: 1px solid #5C1D24;">{tot_gr_wt:.3f}</td>
                        <td style="text-align: right; border-right: 1px solid #5C1D24;">{tot_net_wt:.3f}</td>
                        <td style="border-right: 1px solid #5C1D24;">&nbsp;</td>
                        <td style="text-align: right; border-right: 1px solid #5C1D24;">{tot_amt:,.2f}</td>
                        <td style="text-align: right; border-right: 1px solid #5C1D24;">{tot_labour:,.2f}</td>
                        <td style="text-align: right; color: #5C1D24;">{tot_taxable:,.2f}</td>
                    </tr>
                </tbody>
            </table>
        </td>
    </tr>

    <!-- 6. Bottom Summary Section -->
    <tr>
        <td colspan="3" style="padding: 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <!-- Left Summary Column -->
                    <td style="width: 58%; vertical-align: top; padding: 3px 5px; border-right: 1px solid #5C1D24;">
                        <div style="font-size: 7.2pt;"><b>Vch Desc :</b> {vch_desc}</div>
                        <div style="font-weight: bold; font-size: 7.5pt; color: #5C1D24; margin: 3px 0 2px 0; border: 1px dashed #D6C7B8; padding: 2.5px 4px; background-color: #FCFAF6;">
                            {words_inr}
                        </div>
                        <div style="font-size: 7pt; color: #555555; margin-top: 1px;"><b>Ref By :</b> </div>
                        
                        <div style="margin-top: 3px; font-size: 6.5pt; line-height: 1.2; color: #444444; border-top: 1px solid #E5D7CD; padding-top: 2px;">
                            <b style="color: #2C1810;">Terms &amp; conditions :</b><br>
                            <b>Subject to bavla jurisdiction</b><br>
                            ગેરંટી શરતો : અમારે ત્યાંથી લીધેલો દાગીનો પાછો લાવશો ત્યારે વજન અને ઝારણ/મજૂરી નિયમ મુજબ કાપી બજાર ભાવે પાછો લેવામાં આવશે. ઉચક આપેલો માલ પાછો લેવામાં આવશે નહીં.
                        </div>

                        <div style="margin-top: 10px; text-align: center; width: 60%;">
                            <div style="font-size: 7.2pt; font-weight: bold; color: #2C1810; border-top: 1px solid #2C1810; padding-top: 2px;">
                                Party signatory<br>
                                <small style="font-weight: normal; color: #666666;">(ગ્રાહકની સહી)</small>
                            </div>
                        </div>
                    </td>

                    <!-- Right Calculation & Auth Signatory Column -->
                    <td style="width: 42%; vertical-align: top; padding: 0;">
                        <table class="calc-table">
                            <tr>
                                <td style="width: 55%; background-color: #FFFFFF;">Net Amount :</td>
                                <td style="width: 45%; text-align: right; font-weight: bold;">{format_inr(subtotal_rs, symbol='')}</td>
                            </tr>
                            <tr>
                                <td style="background-color: #FFFFFF;">CGST : 1.50% :</td>
                                <td style="text-align: right;">{format_inr(cgst_rs, symbol='')}</td>
                            </tr>
                            <tr>
                                <td style="background-color: #FFFFFF;">SGST : 1.50% :</td>
                                <td style="text-align: right;">{format_inr(sgst_rs, symbol='')}</td>
                            </tr>
                            <tr class="grand-row">
                                <td style="border-top: 1.2px solid #5C1D24; border-bottom: 1.2px solid #5C1D24;">Total Amount :</td>
                                <td style="border-top: 1.2px solid #5C1D24; border-bottom: 1.2px solid #5C1D24; text-align: right;">{format_inr(grand_rs, symbol='')}</td>
                            </tr>
                            <tr>
                                <td style="background-color: #FFFFFF;">{paid_mode_label}</td>
                                <td style="text-align: right; font-weight: bold; color: #16A34A;">{format_inr(paid_rs, symbol='')}</td>
                            </tr>
                            <tr>
                                <td style="background-color: #FFFFFF; font-weight: bold; color: {outstanding_color};">Bill Outstanding :</td>
                                <td style="text-align: right; font-weight: bold; color: {outstanding_color};">{format_inr(balance_rs, symbol='')}</td>
                            </tr>
                        </table>

                        <div style="padding: 2px; text-align: center;">
                            <div style="font-size: 6.5pt; color: #444444;">Certified that the particulars given above are true and correct</div>
                            <div style="font-size: 7.5pt; font-weight: bold; color: #5C1D24; margin-top: 1px;">For : {shop_settings['shop_name_en']}</div>
                            <div style="font-size: 7.5pt; font-weight: bold; color: #5C1D24;">{shop_settings['shop_name_gu']}</div>
                            
                            <div style="margin-top: 10px; margin-left: 15px; margin-right: 15px; border-top: 1px solid #5C1D24; padding-top: 2px;">
                                <span style="font-size: 7.2pt; font-weight: bold; color: #5C1D24;">પ્રોપ્રાયટર / Authorised signatory</span>
                            </div>
                        </div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

</body>
</html>
    """
    return html

def print_or_pdf_bill(bill_data: dict, parent_window=None, save_pdf_path: str = None) -> bool:
    """
    Renders the bill and opens print dialog or exports to PDF at true 1-page A4 proportions.
    """
    html_content = generate_bill_html(bill_data)
    
    printer = QPrinter(QPrinter.PrinterResolution)
    printer.setPageSize(QPageSize(QPageSize.A4))
    printer.setPageMargins(QMarginsF(4, 4, 4, 4), QPageLayout.Millimeter)

    if save_pdf_path:
        dirname = os.path.dirname(save_pdf_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(save_pdf_path)
        paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        doc = QTextDocument()
        doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
        doc.setHtml(html_content)
        doc.print_(printer)
        return True
    else:
        dialog = QPrintDialog(printer, parent_window)
        if dialog.exec():
            paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
            doc = QTextDocument()
            doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
            doc.setHtml(html_content)
            doc.print_(printer)
            return True
    return False

def export_bill_to_pdf(bill_data: dict, output_path: str) -> bool:
    """Exports bill directly to PDF file silently at true 1-page A4 proportions."""
    try:
        dirname = os.path.dirname(output_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        html_content = generate_bill_html(bill_data)

        printer = QPrinter(QPrinter.PrinterResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageMargins(QMarginsF(4, 4, 4, 4), QPageLayout.Millimeter)
        printer.setOutputFileName(output_path)

        paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        doc = QTextDocument()
        doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
        doc.setHtml(html_content)
        doc.print_(printer)
        return True
    except Exception as e:
        print(f"[Print Manager] PDF export failed: {e}")
        return False
