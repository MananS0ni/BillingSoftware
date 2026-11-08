"""
print_manager.py - Generates printable bills and official PDF invoices.
Replicates the exact user-designed jewelry invoice for Soni Natvarlal Himmatlal:

- Top Header Box: Sacred Invocations (વાયુ આદિતી | ॥ શ્રી હરિ ॥ | બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫), GSTIN, Vector Monogram Logo & Authentic Gujarati Calligraphy
- Reference No & Date Line with elegant underlines (રેફ. નં.  તા.)
- Framed Customer Box: શેઠશ્રી [Customer Name] & Mobile [Number]
- 8-Column Itemized Jewelry Table:
    ક્રમ | વિગત (Description) | પીસ (Pcs) | ગ્રોસ વજન (Gross g) | નેટ વજન (Net g) | ભાવ (Rate/g) | મજૂરી (Labour) | રકમ (Amount ₹)
    With warm terracotta/peach header background (#F1D9CF) and item description underline
- Totals Row: કુલ / Total with exact column sums (#F6E7DF background)
- Bottom Section:
    - Left Box: અંકે રૂપિયા / Amount in words (Rupees ... Only in Title Case)
    - Right Box: Calculation Table (કરપાત્ર રકમ, CGST 1.5%, SGST 1.5%, Round off, કુલ રકમ / Total, જમા / Received, બાકી / Balance)
- Footer: Terms (શરતો: બાવળા જ્યુરિસ્ટિક્શનને આધીન.) & Dual Signatures (ગ્રાહકની સહી & સોની નટવરલાલ હિંમતલાલ પ્રોપ્રાઇટર)
- Formatted to fit on exactly 1 single A4 page.
"""

import os
import re
import base64
from typing import Optional, Dict

from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QImage, QPainter, QColor
from PySide6.QtCore import QSizeF, QMarginsF, QByteArray, QBuffer, QIODevice
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtSvg import QSvgRenderer

from format_utils import format_inr, num_to_words_title_case
from settings_manager import load_settings

_CACHED_LOGO_B64 = None

def get_nh_logo_base64() -> str:
    """Generates the official 'nh' vector monogram at crisp resolution encoded in base64."""
    global _CACHED_LOGO_B64
    if _CACHED_LOGO_B64:
        return _CACHED_LOGO_B64
    try:
        svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 96" width="240" height="230">
          <rect width="100" height="96" fill="transparent"/>
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
        </svg>"""
        renderer = QSvgRenderer(QByteArray(svg_code.encode('utf-8')))
        img = QImage(240, 230, QImage.Format_ARGB32)
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
    Generates HTML exactly matching the user-designed perfect jewelry invoice.
    """
    if not shop_settings:
        st = load_settings()
        shop_settings = {
            "header_left": st.get("header_left", "વાયુ આદિતી"),
            "header_center": st.get("header_center", "॥ શ્રી હરિ ॥"),
            "header_right": st.get("header_right", "બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫"),
            "phone_display": st.get("owner_phone_display", "98251 62065"),
            "shop_name_gu": st.get("shop_name_gu", "સોની નટવરલાલ હિંમતલાલ"),
            "proprietor": st.get("proprietor", "સોની બ્રિજેશ નટવરલાલ"),
            "tagline": st.get("tagline", "સોના-ચાંદીના દાગીના બનાવનાર તથા વેચનાર."),
            "address": st.get("address", "જૈન દેરાસર પાસે, બાવળા-૩૮૨૨૨૦. જી. અમદાવાદ."),
            "gstin": st.get("gstin", "24BPXPS8279A1Z7")
        }

    logo_b64 = get_nh_logo_base64()
    bill_no = bill_data.get("bill_no", 1)
    bill_date = bill_data.get("bill_date", "")

    # Customer Information
    cust_name = bill_data.get("customer_name", "") or bill_data.get("name_gu", "")
    cust_phone = bill_data.get("customer_mobile", "") or bill_data.get("mobile", "") or ""

    items = bill_data.get("items", [])
    items_html = ""
    tot_pcs = 0
    tot_gr_wt = 0.0
    tot_net_wt = 0.0
    tot_labour = 0.0
    tot_amt = 0.0

    for idx, item in enumerate(items):
        pcs = item.get("pcs", 1)
        gr_wt = item.get("gross_weight_mg", item.get("weight_mg", 0)) / 1000.0
        net_wt = item.get("weight_mg", 0) / 1000.0
        rate_rs = item.get("rate_paise", 0) / 100.0
        making_rs = item.get("making_paise", 0) / 100.0
        amt_rs = item.get("amount_paise", 0) / 100.0

        tot_pcs += pcs
        tot_gr_wt += gr_wt
        tot_net_wt += net_wt
        tot_labour += making_rs
        tot_amt += amt_rs

        items_html += f"""
        <tr>
            <td style="text-align: center; border: 1px solid #82444E; padding: 4px 2px; font-size: 8pt;">{idx + 1}</td>
            <td style="text-align: left; border: 1px solid #82444E; padding: 4px 6px; font-size: 8.2pt; color: #2C1810;">
                <div style="border-bottom: 1px solid #D6C7B8; padding-bottom: 2px;">{item.get('description', '')}</div>
            </td>
            <td style="text-align: center; border: 1px solid #82444E; padding: 4px 2px; font-size: 8pt;">{pcs}</td>
            <td style="text-align: right; border: 1px solid #82444E; padding: 4px 5px; font-size: 8pt;">{gr_wt:.3f}</td>
            <td style="text-align: right; border: 1px solid #82444E; padding: 4px 5px; font-size: 8pt;">{net_wt:.3f}</td>
            <td style="text-align: right; border: 1px solid #82444E; padding: 4px 5px; font-size: 8pt;">{rate_rs:,.0f}</td>
            <td style="text-align: right; border: 1px solid #82444E; padding: 4px 5px; font-size: 8pt;">{making_rs:,.0f}</td>
            <td style="text-align: right; border: 1px solid #82444E; padding: 4px 6px; font-size: 8pt; color: #2C1810;">{amt_rs:,.2f}</td>
        </tr>
        """

    subtotal_rs = tot_amt
    cgst_rs = round(subtotal_rs * 0.015, 2)
    sgst_rs = round(subtotal_rs * 0.015, 2)
    raw_total = subtotal_rs + cgst_rs + sgst_rs
    rounded_grand = round(raw_total)
    round_off = rounded_grand - raw_total

    paid_rs = bill_data.get("paid_paise", 0) / 100.0
    balance_rs = rounded_grand - paid_rs

    words_inr = num_to_words_title_case(rounded_grand)
    round_off_str = f"{round_off:+.2f}" if abs(round_off) >= 0.005 else "0.00"

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
        font-size: 8pt;
    }}
    .border-table {{
        width: 100%;
        border: 1.5px solid #82444E;
        border-collapse: collapse;
    }}
    .th-cell {{
        background-color: #F1D9CF;
        color: #332222;
        border: 1px solid #82444E;
        padding: 3px 2px;
        text-align: center;
        font-weight: bold;
    }}
    .totals-cell {{
        background-color: #F6E7DF;
        border: 1px solid #82444E;
        padding: 3px 4px;
        font-weight: bold;
    }}
    .calc-row td {{
        border: 1px solid #82444E;
        padding: 2.5px 6px;
        font-size: 7.8pt;
    }}
</style>
</head>
<body>

<!-- 1. Header Box (Sacred Invocation, GSTIN, Shop Logo & Calligraphy) -->
<table class="border-table">
    <!-- Row 1: Sacred Invocations & Proprietor Mobile -->
    <tr>
        <td style="width: 30%; padding: 2px 6px; font-weight: bold; font-size: 8.5pt; color: #2C1810;">
            {shop_settings['header_left']}
        </td>
        <td style="width: 40%; text-align: center; padding: 2px 6px; font-weight: bold; font-size: 9pt; color: #2C1810;">
            {shop_settings['header_center']}
        </td>
        <td style="width: 30%; text-align: right; padding: 2px 6px; font-weight: bold; font-size: 8.5pt; color: #2C1810;">
            {shop_settings['header_right']}
        </td>
    </tr>
    <!-- Row 2: GSTIN -->
    <tr>
        <td colspan="3" style="border-top: 1px solid #82444E; border-bottom: 1px solid #82444E; padding: 2px 6px; font-weight: bold; font-size: 8pt; color: #2C1810;">
            GSTIN : {shop_settings['gstin']}
        </td>
    </tr>
    <!-- Row 3: Logo & Shop Details -->
    <tr>
        <td colspan="3" style="padding: 4px 6px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 80px; text-align: left; vertical-align: middle; padding-left: 4px;">
                        <img src="data:image/png;base64,{logo_b64}" width="68" height="65"/>
                    </td>
                    <td style="text-align: center; vertical-align: middle; padding-right: 40px;">
                        <div style="font-size: 17pt; font-weight: bold; color: #6B2433; letter-spacing: 0.5px; line-height: 1.1;">
                            {shop_settings['shop_name_gu']}
                        </div>
                        <div style="font-size: 7.8pt; font-weight: bold; color: #82444E; margin-top: 2px;">
                            પ્રોપરાઇટર : {shop_settings['proprietor']}
                        </div>
                        <div style="font-size: 7.8pt; font-weight: bold; color: #B35446; margin-top: 1px;">
                            {shop_settings['tagline']}
                        </div>
                        <div style="font-size: 7.2pt; color: #4A3B32; margin-top: 1px;">
                            {shop_settings['address']}
                        </div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- 2. Ref No. & Date Line -->
<table width="100%" cellpadding="0" cellspacing="0" style="width: 100%; border-collapse: collapse; margin-top: 5px; margin-bottom: 4px;">
    <tr>
        <td width="50%" align="left" style="width: 50%; text-align: left; vertical-align: middle; font-size: 8.5pt;">
            <b>રેફ. નં.</b> &nbsp;<u>&nbsp;&nbsp;{bill_no}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>
        </td>
        <td width="50%" align="right" style="width: 50%; text-align: right; vertical-align: middle; font-size: 8.5pt;">
            <b>તા.</b> &nbsp;<u>&nbsp;&nbsp;{bill_date}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>
        </td>
    </tr>
</table>

<!-- 3. Customer Box (શેઠશ્રી) -->
<table class="border-table" style="margin-bottom: 4px;">
    <tr>
        <td style="padding: 3px 6px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 70%; font-size: 8.5pt;">
                        <b style="color: #2C1810;">શેઠશ્રી</b> &nbsp;&nbsp;
                        <u>&nbsp;&nbsp;<b>{cust_name}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>
                    </td>
                    <td style="width: 30%; text-align: right; font-size: 8.5pt;">
                        <span style="color: #666666; font-size: 7.8pt;">Mobile </span> &nbsp;
                        <b style="color: #2C1810;">{cust_phone}</b>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- 4. Items Table (8 Columns matching user design) -->
<table style="width: 100%; border-collapse: collapse; border: 1.5px solid #82444E;">
    <thead>
        <tr>
            <th class="th-cell" style="width: 5%;">ક્રમ</th>
            <th class="th-cell" style="width: 41%; text-align: center;">
                <div>વિગત</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Description</div>
            </th>
            <th class="th-cell" style="width: 6%;">
                <div>પીસ</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Pcs</div>
            </th>
            <th class="th-cell" style="width: 9%;">
                <div>ગ્રોસ વજન</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Gross g</div>
            </th>
            <th class="th-cell" style="width: 9%;">
                <div>નેટ વજન</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Net g</div>
            </th>
            <th class="th-cell" style="width: 10%;">
                <div>ભાવ</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Rate/g</div>
            </th>
            <th class="th-cell" style="width: 8%;">
                <div>મજૂરી</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Labour</div>
            </th>
            <th class="th-cell" style="width: 12%;">
                <div>રકમ</div>
                <div style="font-size: 6.8pt; font-weight: normal; color: #444444;">Amount ₹</div>
            </th>
        </tr>
    </thead>
    <tbody>
        {items_html}
        <!-- Totals Row -->
        <tr>
            <td colspan="2" class="totals-cell" style="text-align: right; color: #2C1810; padding-right: 10px;">
                કુલ / Total
            </td>
            <td class="totals-cell" style="text-align: center; color: #2C1810;">{tot_pcs}</td>
            <td class="totals-cell" style="text-align: right; color: #2C1810;">{tot_gr_wt:.3f}</td>
            <td class="totals-cell" style="text-align: right; color: #2C1810;">{tot_net_wt:.3f}</td>
            <td class="totals-cell">&nbsp;</td>
            <td class="totals-cell" style="text-align: right; color: #2C1810;">{tot_labour:,.0f}</td>
            <td class="totals-cell" style="text-align: right; color: #2C1810;">{tot_amt:,.2f}</td>
        </tr>
    </tbody>
</table>

<!-- 5. Bottom Section: Left Words Box & Right Calculation Table -->
<table style="width: 100%; border-collapse: collapse; margin-top: 4px;">
    <tr>
        <!-- Left Amount in Words Box -->
        <td style="width: 55%; vertical-align: top; border: 1.5px solid #82444E; padding: 6px 8px;">
            <div style="font-size: 7.2pt; color: #555555;">અંકે રૂપિયા / Amount in words</div>
            <div style="font-size: 8pt; font-weight: bold; color: #2C1810; margin-top: 4px; line-height: 1.3;">
                {words_inr}
            </div>
        </td>
        <td style="width: 2%;">&nbsp;</td>
        <!-- Right Calculation Table -->
        <td style="width: 43%; vertical-align: top; padding: 0;">
            <table style="width: 100%; border-collapse: collapse; border: 1.5px solid #82444E;">
                <tr class="calc-row">
                    <td style="width: 52%; background-color: #FFFFFF; font-size: 7.8pt;">કરપાત્ર રકમ</td>
                    <td style="width: 48%; text-align: right; font-weight: bold; font-size: 7.8pt; white-space: nowrap;">{subtotal_rs:,.2f}</td>
                </tr>
                <tr class="calc-row">
                    <td style="background-color: #FFFFFF; font-size: 7.8pt;">CGST &nbsp;&nbsp; 1.5 %</td>
                    <td style="text-align: right; font-size: 7.8pt; white-space: nowrap;">{cgst_rs:,.2f}</td>
                </tr>
                <tr class="calc-row">
                    <td style="background-color: #FFFFFF; font-size: 7.8pt;">SGST 1.5 %</td>
                    <td style="text-align: right; font-size: 7.8pt; white-space: nowrap;">{sgst_rs:,.2f}</td>
                </tr>
                <tr class="calc-row">
                    <td style="background-color: #FFFFFF; font-size: 7.8pt;">Round off</td>
                    <td style="text-align: right; font-size: 7.8pt; white-space: nowrap;">{round_off_str}</td>
                </tr>
                <tr class="calc-row" style="background-color: #F1D9CF;">
                    <td style="font-weight: bold; color: #2C1810; font-size: 8pt; white-space: nowrap;">કુલ રકમ / Total</td>
                    <td style="text-align: right; font-weight: bold; color: #2C1810; font-size: 8.5pt; white-space: nowrap;">{rounded_grand:,.2f}</td>
                </tr>
                <tr class="calc-row">
                    <td style="background-color: #FFFFFF; font-size: 7.8pt; white-space: nowrap;">જમા / Received</td>
                    <td style="text-align: right; color: #16A34A; font-weight: bold; font-size: 7.8pt; white-space: nowrap;">{paid_rs:,.0f}</td>
                </tr>
                <tr class="calc-row">
                    <td style="background-color: #FFFFFF; font-weight: bold; font-size: 7.8pt; white-space: nowrap;">બાકી / Balance</td>
                    <td style="text-align: right; font-weight: bold; color: #DC2626; font-size: 8pt; white-space: nowrap;">{balance_rs:,.2f}</td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- 6. Footer Terms & Dual Signatures -->
<table width="100%" cellpadding="0" cellspacing="0" style="width: 100%; border-collapse: collapse; margin-top: 24px;">
    <tr>
        <td width="35%" align="left" style="width: 35%; font-size: 7.8pt; color: #333333; vertical-align: top;">
            શરતો: બાવળા જ્યુરિસ્ટિક્શનને આધીન.
        </td>
        <td width="35%" align="center" style="width: 35%; text-align: center; vertical-align: top;">
            <div style="font-size: 8pt; font-weight: bold; color: #2C1810;">
                ________________________<br>
                ગ્રાહકની સહી
            </div>
        </td>
        <td width="30%" align="right" style="width: 30%; text-align: right; vertical-align: top;">
            <div style="font-size: 8.5pt; font-weight: bold; color: #6B2433;">
                ________________________<br>
                {shop_settings['shop_name_gu']}<br>
                <span style="font-size: 7.2pt; color: #555555; font-weight: normal;">પ્રોપ્રાઇટર</span>
            </div>
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
