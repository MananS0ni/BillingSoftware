"""
print_manager.py - Generates printable bills and official letterhead PDF invoices.
Replicates the exact physical bill pad of Soni Natvarlal Himmatlal:
- Deep Maroon (#5C1D24) & Warm Terracotta (#B86B4B) traditional Gujarati jewelry theme
- Official sacred invocations: વાયુ આદિતી | ॥ શ્રી હરિ ॥ | બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫
- Authentic GSTIN (24BPXPS8279A1Z7) and Bavla shop address
- Vector-rendered 'nh' monogram logo
- Full itemized table with HSN, Net Weight (g), Rate, Making, and Amount
- Clear GST breakdown, Grand Total box, Paid, Balance Udhar, Terms & Dual Signatures
- Formatted precisely to fit on exactly 1 single A4 page
"""

import os
import base64
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QImage, QPainter, QColor
from PySide6.QtCore import QSizeF, QMarginsF, QByteArray, QBuffer, QIODevice
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtSvg import QSvgRenderer

from format_utils import format_inr
from settings_manager import load_settings

_CACHED_LOGO_B64 = None

def get_nh_logo_base64() -> str:
    """Generates the official 'nh' monogram logo at crisp vector resolution encoded in base64."""
    global _CACHED_LOGO_B64
    if _CACHED_LOGO_B64:
        return _CACHED_LOGO_B64
    try:
        svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
          <rect width="100" height="100" fill="transparent"/>
          <!-- 'n' in warm terracotta (#B86B4B) -->
          <rect x="6" y="28" width="18" height="54" fill="#B86B4B"/>
          <path d="M 6 42 C 6 24, 20 16, 36 16 C 50 16, 56 26, 56 38 L 56 82 L 38 82 L 38 42 C 38 34, 34 30, 26 30 C 18 30, 16 34, 16 42 Z" fill="#B86B4B"/>
          
          <!-- 'h' in dark bronze/charcoal (#2C2122) -->
          <rect x="42" y="2" width="16" height="80" fill="#2C2122"/>
          <path d="M 42 42 C 42 24, 56 16, 72 16 C 86 16, 92 26, 92 38 L 92 82 L 74 82 L 74 42 C 74 34, 70 30, 62 30 C 54 30, 50 34, 50 42 Z" fill="#2C2122"/>
          
          <!-- Dot grid on lower right leg of 'h' (3 columns x 4 rows) -->
          <circle cx="79" cy="56" r="2" fill="#FFFFFF"/>
          <circle cx="84" cy="56" r="2" fill="#FFFFFF"/>
          <circle cx="89" cy="56" r="2" fill="#FFFFFF"/>
          
          <circle cx="79" cy="63" r="2" fill="#FFFFFF"/>
          <circle cx="84" cy="63" r="2" fill="#FFFFFF"/>
          <circle cx="89" cy="63" r="2" fill="#FFFFFF"/>
          
          <circle cx="79" cy="70" r="2" fill="#FFFFFF"/>
          <circle cx="84" cy="70" r="2" fill="#FFFFFF"/>
          <circle cx="89" cy="70" r="2" fill="#FFFFFF"/>

          <circle cx="79" cy="77" r="2" fill="#FFFFFF"/>
          <circle cx="84" cy="77" r="2" fill="#FFFFFF"/>
          <circle cx="89" cy="77" r="2" fill="#FFFFFF"/>
          
          <!-- Bottom solid terracotta underline bar -->
          <rect x="6" y="88" width="86" height="7" fill="#B86B4B"/>
        </svg>"""
        renderer = QSvgRenderer(QByteArray(svg_code.encode('utf-8')))
        img = QImage(240, 240, QImage.Format_ARGB32)
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
    Generates an HTML receipt strictly matching the real paper bill pad of Soni Natvarlal Himmatlal.
    """
    if not shop_settings:
        st = load_settings()
        shop_settings = {
            "header_left": st.get("header_left", "વાયુ આદિતી"),
            "header_center": st.get("header_center", "॥ શ્રી હરિ ॥"),
            "header_right": st.get("header_right", "બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫"),
            "phone_display": st.get("owner_phone_display", "98251 62065"),
            "shop_name_gu": st.get("shop_name_gu", "સોની નટવરલાલ હિંમતલાલ"),
            "shop_name_en": st.get("shop_name_en", "Soni Natvarlal Himmatlal"),
            "proprietor": st.get("proprietor", "સોની બ્રિજેશ નટવરલાલ"),
            "tagline": st.get("tagline", "સોના-ચાંદીના દાગીના બનાવનાર તથા વેચનાર."),
            "address": st.get("address", "જૈન દેરાસર પાસે, બાવળા-૩૮૨૨૨૦. જી. અમદાવાદ."),
            "gstin": st.get("gstin", "24BPXPS8279A1Z7"),
        }

    logo_b64 = get_nh_logo_base64()

    items_html = ""
    for idx, item in enumerate(bill_data.get("items", [])):
        wt_g = item.get("weight_mg", 0) / 1000.0
        rate_rs = item.get("rate_paise", 0) / 100.0
        making_rs = item.get("making_paise", 0) / 100.0
        amt_rs = item.get("amount_paise", 0) / 100.0
        hsn_val = item.get("hsn_code", "") or "7113"
        
        items_html += f"""
        <tr>
            <td style="padding: 4px 3px; border: 1px solid #D6C7B8; text-align: center; font-size: 8.5pt;">{idx + 1}</td>
            <td style="padding: 4px 5px; border: 1px solid #D6C7B8; font-weight: bold; font-size: 8.5pt; color: #2C1810;">{item.get('description', '')}</td>
            <td style="padding: 4px 3px; border: 1px solid #D6C7B8; text-align: center; font-size: 8pt; color: #555555;">{hsn_val}</td>
            <td style="padding: 4px 5px; border: 1px solid #D6C7B8; text-align: right; font-weight: bold; font-size: 8.5pt;">{wt_g:.3f} g</td>
            <td style="padding: 4px 5px; border: 1px solid #D6C7B8; text-align: right; font-size: 8pt;">{format_inr(rate_rs)}</td>
            <td style="padding: 4px 5px; border: 1px solid #D6C7B8; text-align: right; font-size: 8pt;">{format_inr(making_rs)}</td>
            <td style="padding: 4px 5px; border: 1px solid #D6C7B8; text-align: right; font-weight: bold; font-size: 8.5pt; color: #5C1D24;">{format_inr(amt_rs)}</td>
        </tr>
        """

    subtotal_rs = bill_data.get("subtotal_paise", 0) / 100.0
    cgst_rs = bill_data.get("cgst_paise", 0) / 100.0
    sgst_rs = bill_data.get("sgst_paise", 0) / 100.0
    grand_rs = bill_data.get("grand_total_paise", 0) / 100.0
    paid_rs = bill_data.get("paid_paise", 0) / 100.0
    balance_rs = bill_data.get("balance_paise", 0) / 100.0

    cust_name = bill_data.get("name_gu", "") or bill_data.get("customer_name", "")
    cust_en = f" ({bill_data.get('name_en')})" if bill_data.get("name_en") else ""
    cust_phone = bill_data.get("mobile", "") or bill_data.get("customer_mobile", "")
    cust_addr = bill_data.get("address", "") or bill_data.get("customer_address", "") or "-"
    pan_display = bill_data.get("pan_no", "") or "-"
    aadhaar_display = bill_data.get("aadhaar_no", "") or "-"

    mode_display = bill_data.get("payment_mode", "CASH")
    if bill_data.get("payment_ref"):
        mode_display += f" ({bill_data.get('payment_ref')})"

    balance_color = "#DC2626" if balance_rs > 0 else "#16A34A"
    balance_status = "બાકી ઉધાર (Udhar Due)" if balance_rs > 0 else "ચૂકતે હિસાબ (Settled)"

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
    }}
    .top-header-table {{
        width: 100%;
        border-collapse: collapse;
        padding-bottom: 2px;
        border-bottom: 1.5px solid #5C1D24;
    }}
    .brand-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 2px;
        padding-bottom: 2px;
        border-bottom: 1px solid #B86B4B;
    }}
    .ref-date-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 2px;
    }}
    .cust-box {{
        width: 100%;
        border: 1.5px solid #5C1D24;
        background-color: #FFFFFF;
        border-collapse: collapse;
        margin-top: 2px;
    }}
    .cust-box td {{
        padding: 2px 6px;
        font-size: 8pt;
        line-height: 1.25;
    }}
    .items-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 3px;
    }}
    .items-table th {{
        background-color: #5C1D24;
        color: #FFFFFF;
        font-size: 8pt;
        font-weight: bold;
        padding: 3px 3px;
        border: 1px solid #5C1D24;
    }}
    .totals-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 3px;
    }}
    .grand-box {{
        background-color: #FAF0E6;
        border: 1.5px solid #5C1D24;
        font-size: 9pt;
        font-weight: bold;
        color: #5C1D24;
    }}
    .terms {{
        font-size: 6.5pt;
        color: #555555;
        border-top: 1px solid #D6C7B8;
        padding-top: 2px;
        margin-top: 3px;
        line-height: 1.2;
    }}
    .sig-table {{
        width: 100%;
        margin-top: 3px;
        font-size: 7.5pt;
        font-weight: bold;
    }}
</style>
</head>
<body>
<table style="width: 100%; border: 2.5px solid #5C1D24; border-collapse: collapse; background-color: #FCFAF6;">
<tr>
<td style="padding: 4px 8px; vertical-align: top;">

    <!-- 1. Top Sacred & Contact Bar (matching pad) -->
    <table class="top-header-table">
        <tr>
            <td style="width: 33%; vertical-align: top;">
                <span style="font-size: 8.5pt; font-weight: bold; color: #5C1D24;">{shop_settings['header_left']}</span><br>
                <span style="font-size: 7.5pt; font-weight: bold; color: #2C1810;">GSTIN : {shop_settings['gstin']}</span>
            </td>
            <td style="width: 34%; text-align: center; vertical-align: middle;">
                <span style="font-size: 11pt; font-weight: bold; color: #5C1D24; letter-spacing: 2px;">{shop_settings['header_center']}</span>
            </td>
            <td style="width: 33%; text-align: right; vertical-align: top;">
                <span style="font-size: 9pt; font-weight: bold; color: #5C1D24;">{shop_settings['header_right']}</span><br>
                <span style="font-size: 7.5pt; color: #555555;">મો. +91 {shop_settings['phone_display']}</span>
            </td>
        </tr>
    </table>

    <!-- 2. Main Brand Letterhead (Logo + Gujarati Typography) -->
    <table class="brand-table">
        <tr>
            <td style="width: 58px; vertical-align: middle; padding: 1px 4px 1px 0;">
                <img src="data:image/png;base64,{logo_b64}" width="52" height="52"/>
            </td>
            <td style="vertical-align: middle; padding-left: 4px;">
                <div style="font-size: 18pt; font-weight: bold; color: #5C1D24; letter-spacing: 0.5px; line-height: 1.1;">{shop_settings['shop_name_gu']}</div>
                <div style="font-size: 8.5pt; font-weight: bold; color: #B86B4B; margin-top: 1px;">પ્રોપરાઈટર : {shop_settings['proprietor']}</div>
                <div style="font-size: 8pt; font-weight: 600; color: #3A2426; margin-top: 1px;">{shop_settings['tagline']} ({shop_settings['shop_name_en']})</div>
                <div style="font-size: 7.5pt; color: #4A3B32; margin-top: 1px;">{shop_settings['address']}</div>
            </td>
        </tr>
    </table>

    <!-- 3. Ref No. & Date Line (Exact matching pad) -->
    <table class="ref-date-table">
        <tr>
            <td style="width: 50%; font-size: 9pt; padding: 2px 0;">
                <b style="color: #5C1D24;">રેફ. નં. :</b> <span style="font-size: 10.5pt; font-weight: bold; color: #2C1810;">#{bill_data.get('bill_no', '')}</span>
                &nbsp;&nbsp;<span style="background-color: #5C1D24; color: #FFFFFF; font-size: 7pt; font-weight: bold; padding: 1px 5px; border-radius: 2px;">TAX INVOICE (પાકું બિલ)</span>
            </td>
            <td style="width: 50%; text-align: right; font-size: 9pt; padding: 2px 0;">
                <b style="color: #5C1D24;">તા. :</b> <span style="font-weight: bold; color: #2C1810;">{bill_data.get('bill_date', '')}</span>
            </td>
        </tr>
    </table>

    <!-- 4. Customer Info Card (શેઠશ્રી) -->
    <table class="cust-box">
        <tr>
            <td style="width: 60%; border-right: 1px solid #D6C7B8;">
                <b style="color: #5C1D24;">શેઠશ્રી (Customer) :</b> <span style="font-size: 9.5pt; font-weight: bold; color: #2C1810;">{cust_name}{cust_en}</span><br>
                <b>સરનામું (Address) :</b> {cust_addr}
            </td>
            <td style="width: 40%;">
                <b>મોબાઇલ :</b> <span style="font-weight: bold;">{cust_phone}</span><br>
                <b>PAN :</b> {pan_display} &nbsp;|&nbsp; <b>આધાર :</b> {aadhaar_display}
            </td>
        </tr>
    </table>

    <!-- 5. Itemized Table (દાગીનાની વિગત) -->
    <table class="items-table">
        <thead>
            <tr>
                <th style="width: 5%;">#</th>
                <th style="width: 35%; text-align: left;">દાગીનાની વિગત (Description)</th>
                <th style="width: 9%; text-align: center;">HSN</th>
                <th style="width: 12%; text-align: right;">વજન (Weight)</th>
                <th style="width: 13%; text-align: right;">ભાવ (Rate)</th>
                <th style="width: 11%; text-align: right;">મજૂરી (Making)</th>
                <th style="width: 15%; text-align: right;">રકમ (Amount)</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>

    <!-- 6. Totals & Payment Breakdown -->
    <table class="totals-table">
        <tr>
            <td style="width: 44%; vertical-align: top; padding-right: 4px;">
                <div style="background-color: #FAF6EE; border: 1px solid #D6C7B8; padding: 5px; border-radius: 3px; font-size: 7.8pt; line-height: 1.4;">
                    <b style="color: #5C1D24;">ચુકવણી પદ્ધતિ (Payment Mode):</b> {mode_display}<br>
                    <b>GST વિગત:</b> CGST (1.5%) + SGST (1.5%) = 3% GST<br>
                    <b>નોંધ:</b> અધિકૃત કોમ્પ્યુટરાઈઝ્ડ એકાઉન્ટિંગ જી.એસ.ટી. બિલ
                </div>
            </td>
            <td style="width: 56%; vertical-align: top;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="border: 1px solid #D6C7B8; background: #FFFFFF; padding: 2px 5px; font-size: 7.8pt;">માલ રકમ (Subtotal):</td>
                        <td style="border: 1px solid #D6C7B8; text-align: right; font-weight: bold; padding: 2px 5px; font-size: 7.8pt;">{format_inr(subtotal_rs)}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #D6C7B8; background: #FFFFFF; padding: 2px 5px; font-size: 7.8pt;">CGST @ 1.5%:</td>
                        <td style="border: 1px solid #D6C7B8; text-align: right; padding: 2px 5px; font-size: 7.8pt;">{format_inr(cgst_rs)}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #D6C7B8; background: #FFFFFF; padding: 2px 5px; font-size: 7.8pt;">SGST @ 1.5%:</td>
                        <td style="border: 1px solid #D6C7B8; text-align: right; padding: 2px 5px; font-size: 7.8pt;">{format_inr(sgst_rs)}</td>
                    </tr>
                    <tr class="grand-box">
                        <td style="border: 1.5px solid #5C1D24; padding: 3px 5px;">GRAND TOTAL (કુલ પાકું બિલ):</td>
                        <td style="border: 1.5px solid #5C1D24; text-align: right; padding: 3px 5px;">{format_inr(grand_rs)}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #D6C7B8; font-weight: bold; color: #16A34A; padding: 2px 5px; font-size: 7.8pt;">જમા આપ્યા (Paid Amount):</td>
                        <td style="border: 1px solid #D6C7B8; text-align: right; font-weight: bold; color: #16A34A; padding: 2px 5px; font-size: 7.8pt;">{format_inr(paid_rs)}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #D6C7B8; font-weight: bold; color: {balance_color}; padding: 2px 5px; font-size: 7.8pt;">{balance_status}:</td>
                        <td style="border: 1px solid #D6C7B8; text-align: right; font-weight: bold; color: {balance_color}; padding: 2px 5px; font-size: 7.8pt;">{format_inr(balance_rs)}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- 7. Guarantee Terms & Conditions -->
    <div class="terms">
        <b>ગેરંટી શરતો :</b> અમારે ત્યાંથી લીધેલો દાગીનો પાછો લાવશો ત્યારે વજન અને ઝારણ/મજૂરી નિયમ મુજબ કાપી બજાર ભાવે પાછો લેવામાં આવશે. ઉચક આપેલો માલ પાછો લેવામાં આવશે નહીં.<br>
        <b>નોંધ :</b> આપના જૂના સોના-ચાંદીના દાગીનામાંથી નવા આકર્ષક હોલમાર્ક દાગીના બનાવી આપવામાં આવશે.
    </div>

    <!-- 8. Dual Signatures -->
    <table class="sig-table">
        <tr>
            <td style="width: 50%; vertical-align: bottom;">
                ____________________________<br>
                ગ્રાહકની સહી (Customer Signature)
            </td>
            <td style="width: 50%; text-align: right; vertical-align: bottom;">
                ફોર, <b>{shop_settings['shop_name_gu']}</b><br><br>
                <small>ઓથોરાઇઝ્ડ સહી (Authorized Signatory)</small>
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

def print_or_pdf_bill(bill_data: dict, parent_window=None, save_pdf_path: str = None):
    """
    Renders the bill and opens print dialog or exports to PDF at true 1-page A4 proportions.
    """
    html_content = generate_bill_html(bill_data)
    
    printer = QPrinter(QPrinter.PrinterResolution)
    printer.setPageSize(QPageSize(QPageSize.A4))
    printer.setPageMargins(QMarginsF(6, 6, 6, 6), QPageLayout.Millimeter)

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
        printer.setPageMargins(QMarginsF(6, 6, 6, 6), QPageLayout.Millimeter)
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
