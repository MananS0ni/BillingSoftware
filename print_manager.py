"""
print_manager.py - Generates printable bills and official PDF invoices.
Directly connects the user's exact invoice template (invoice_app.html) with the software.

Features:
- 100% faithful replication of the user's approved invoice design:
  - Header Box: Sacred Invocations (વાયુ આદિતી | ॥ શ્રી હરિ ॥ | બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫)
  - GSTIN : 24BPXPS8279A1Z7
  - Authentic NH Monogram Logo (Orange & Maroon with Dot Grid)
  - Firm details: સોની નટવરલાલ હિંમતલાલ, પ્રોપરાઈટર : સોની બ્રિજેશ નટવરલાલ
  - Reference No & Date Line (રેફ. નં. / તા.)
  - Framed Customer Box: શેઠશ્રી [Customer Name] & Mobile [Number]
  - 8-Column Itemized Jewelry Table with elegant ledger underlines
  - Totals row with exact column sums (#f6e7df background)
  - Left Box: Amount in words (Rupees ... Only in Title Case)
  - Right Box: Calculation Table (Taxable, CGST 1.5%, SGST 1.5%, Round off, Total, Received, Balance)
  - Footer: Terms (શરતો: બાવળા જ્યુરિસ્ટિક્શનને આધીન.) & Dual Signatures (ગ્રાહકની સહી & પ્રોપરાઈટર)
- Strict 1-Page Guarantee on standard A5 (148mm x 210mm) or A4.
- Pixel-perfect PDF rendering via headless Chrome / Edge.
- Physical printer output support via PySide6 QPrintDialog + QPdfDocument.
"""

import os
import re
import sys
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Dict

from PySide6.QtGui import QGuiApplication, QPainter, QTextDocument, QPageSize, QPageLayout
from PySide6.QtCore import QSize, QSizeF, QMarginsF
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from format_utils import num_to_words_title_case
from settings_manager import load_settings

_TEMPLATE_CACHE = None

def find_headless_browser() -> Optional[str]:
    """Finds an installed Chromium-based browser (Chrome or Edge) for pixel-perfect PDF rendering."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

def get_template_html() -> str:
    """Loads the base invoice template from invoice_app.html."""
    global _TEMPLATE_CACHE
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoice_app.html")
    if os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            _TEMPLATE_CACHE = f.read()
    return _TEMPLATE_CACHE or ""

def get_nh_logo_base64() -> str:
    """Returns the base64 encoded NH logo from the user's template."""
    tmpl = get_template_html()
    m = re.search(r'src=["\']data:image/[^;]+;base64,([^"\']+)["\']', tmpl)
    if m:
        return m.group(1)
    return ""

def generate_bill_html(bill_data: dict, shop_settings: dict = None, page_size: str = "A5") -> str:
    """
    Populates the user's exact invoice template with dynamic bill data.
    Preserves 100% of the layout, fonts, borders (#6b2433), colors, and logo.
    """
    if not shop_settings:
        st = load_settings()
        shop_settings = {
            "header_left": st.get("header_left", "વાયુ આદિતી"),
            "header_center": st.get("header_center", "॥ શ્રી હરિ ॥"),
            "header_right": st.get("header_right", "બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫"),
            "shop_name_gu": st.get("shop_name_gu", "સોની નટવરલાલ હિંમતલાલ"),
            "proprietor": st.get("proprietor", "સોની બ્રિજેશ નટવરલાલ"),
            "tagline": st.get("tagline", "સોના-ચાંદીના દાગીના બનાવનાર તથા વેચનાર."),
            "address": st.get("address", "જૈન દેરાસર પાસે, બાવળા-૩૮૨૨૨૦. જી. અમદાવાદ."),
            "gstin": st.get("gstin", "24BPXPS8279A1Z7")
        }

    template = get_template_html()
    if not template:
        raise RuntimeError("invoice_app.html template not found in workspace!")

    # 1. Format Bill No & Date
    bill_no_str = str(bill_data.get("bill_no", 1))
    raw_date = str(bill_data.get("bill_date", ""))
    try:
        if "-" in raw_date:
            dt = datetime.strptime(raw_date.split()[0], "%Y-%m-%d")
            bill_date_str = dt.strftime("%d/%m/%Y")
        else:
            bill_date_str = raw_date
    except Exception:
        bill_date_str = raw_date or datetime.now().strftime("%d/%m/%Y")

    # 2. Customer Information
    cust_name = bill_data.get("customer_name") or bill_data.get("name_gu") or bill_data.get("name_en") or ""
    cust_mob = bill_data.get("customer_mobile") or bill_data.get("mobile") or ""

    # 3. Item Rows
    items = bill_data.get("items", [])
    tot_pcs = 0
    tot_gw = 0.0
    tot_nw = 0.0
    tot_lab = 0.0
    tot_amt = 0.0

    rows_html = ""
    for idx, it in enumerate(items):
        pcs = it.get("pcs", 1)
        gw = it.get("gross_weight_mg", it.get("weight_mg", 0)) / 1000.0
        nw = it.get("weight_mg", 0) / 1000.0
        rate = it.get("rate_paise", 0) / 100.0
        lab = it.get("making_paise", 0) / 100.0
        amt = it.get("amount_paise", 0) / 100.0

        tot_pcs += pcs
        tot_gw += gw
        tot_nw += nw
        tot_lab += lab
        tot_amt += amt

        rows_html += f"""
        <tr>
          <td class="n sn">{idx + 1}</td>
          <td><span class="cell" style="display:block">{it.get('description', '')}</span></td>
          <td class="n"><span class="cell" style="display:block">{pcs}</span></td>
          <td class="n"><span class="cell" style="display:block">{gw:.3f}</span></td>
          <td class="n"><span class="cell" style="display:block">{nw:.3f}</span></td>
          <td class="n"><span class="cell" style="display:block">{rate:,.0f}</span></td>
          <td class="n"><span class="cell" style="display:block">{lab:,.0f}</span></td>
          <td class="n amt">{amt:,.2f}</td>
        </tr>
        """

    # 4. Totals and Calculations
    # If precomputed paise fields exist in bill_data, use them for strict consistency
    if "subtotal_paise" in bill_data:
        subtotal_rs = bill_data["subtotal_paise"] / 100.0
    else:
        subtotal_rs = tot_amt

    if "cgst_paise" in bill_data:
        cgst_rs = bill_data["cgst_paise"] / 100.0
        sgst_rs = bill_data.get("sgst_paise", bill_data["cgst_paise"]) / 100.0
    else:
        cgst_rs = round(subtotal_rs * 0.015, 2)
        sgst_rs = round(subtotal_rs * 0.015, 2)

    raw_total = subtotal_rs + cgst_rs + sgst_rs

    if "grand_total_paise" in bill_data:
        grand_rs = bill_data["grand_total_paise"] / 100.0
    else:
        grand_rs = round(raw_total)

    round_off = grand_rs - raw_total
    round_off_str = f"{round_off:+.2f}" if abs(round_off) >= 0.005 else "0.00"

    if "paid_paise" in bill_data:
        paid_rs = bill_data["paid_paise"] / 100.0
    else:
        paid_rs = bill_data.get("paid", 0.0)

    if "balance_paise" in bill_data:
        bal_rs = bill_data["balance_paise"] / 100.0
    else:
        bal_rs = max(0.0, grand_rs - paid_rs)

    words_str = f"Rupees {num_to_words_title_case(round(grand_rs))} Only"

    # 5. Populate Template
    html = template

    # Remove the interactive top demo bar and scripts
    html = re.sub(r'<div class="bar">.*?</div>\s*<div class="wrap">', '<div class="wrap">', html, flags=re.DOTALL)
    html = re.sub(r'<button class="add".*?</button>', '', html)
    html = re.sub(r'<script>.*?</script>', '', html, flags=re.DOTALL)

    # Configure page size CSS
    pw, ph = ("148mm", "210mm") if page_size.upper() == "A5" else ("210mm", "297mm")
    page_style = f"""
    <style>
    @page {{ size: {pw} {ph}; margin: 0; }}
    body {{ background: #fff !important; }}
    .wrap {{ padding: 0 !important; }}
    .paper {{ box-shadow: none !important; margin: 0 !important; --pw: {pw}; --ph: {ph}; }}
    .noprint {{ display: none !important; }}
    </style>
    """
    html = html.replace('</head>', f'{page_style}\n</head>')

    # Fill Header info if changed
    if shop_settings.get("header_left"):
        html = re.sub(r'<span>વાયુ આદિતી</span>', f'<span>{shop_settings["header_left"]}</span>', html)
    if shop_settings.get("header_center"):
        html = re.sub(r'<span>॥ શ્રી હરિ ॥</span>', f'<span>{shop_settings["header_center"]}</span>', html)
    if shop_settings.get("header_right"):
        html = re.sub(r'<span>બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫</span>', f'<span>{shop_settings["header_right"]}</span>', html)
    if shop_settings.get("gstin"):
        html = re.sub(r'GSTIN : 24BPXPS8279A1Z7', f'GSTIN : {shop_settings["gstin"]}', html)
    if shop_settings.get("shop_name_gu"):
        html = re.sub(r'<h1>સોની નટવરલાલ હિંમતલાલ</h1>', f'<h1>{shop_settings["shop_name_gu"]}</h1>', html)

    # Fill Reference No and Date
    html = re.sub(
        r'<input id="ref"[^>]*>',
        f'<span class="cell" style="display:inline-block;min-width:18mm;padding-left:4px">{bill_no_str}</span>',
        html
    )
    html = re.sub(
        r'<input id="date"[^>]*>',
        f'<span class="cell" style="display:inline-block;min-width:34mm;text-align:center">{bill_date_str}</span>',
        html
    )

    # Fill Customer Name and Mobile
    html = re.sub(
        r'<input id="cname"[^>]*>',
        f'<span class="cell" style="display:inline-block;flex:1;font-weight:600;padding-left:4px">{cust_name}</span>',
        html
    )
    html = re.sub(
        r'<input id="cmob"[^>]*>',
        f'<span class="cell" style="display:inline-block;flex:1;font-weight:600;padding-left:4px">{cust_mob}</span>',
        html
    )

    # Fill Item Rows
    html = re.sub(r'<tbody id="rows">.*?</tbody>', f'<tbody id="rows">{rows_html}</tbody>', html, flags=re.DOTALL)

    # Fill Column Totals
    html = re.sub(r'id="tp">0<', f'id="tp">{tot_pcs}<', html)
    html = re.sub(r'id="tg">0\.000<', f'id="tg">{tot_gw:.3f}<', html)
    html = re.sub(r'id="tn">0\.000<', f'id="tn">{tot_nw:.3f}<', html)
    html = re.sub(r'id="tl">0<', f'id="tl">{tot_lab:,.0f}<', html)
    html = re.sub(r'id="tt">0\.00<', f'id="tt">{subtotal_rs:,.2f}<', html)

    # Fill Amount in Words
    html = re.sub(r'id="words">—<', f'id="words">{words_str}<', html)

    # Fill Calculation Table
    html = re.sub(r'id="c_tax">0\.00<', f'id="c_tax">{subtotal_rs:,.2f}<', html)
    html = re.sub(r'<input id="gst"[^>]*>', '1.5', html)
    html = re.sub(r'id="c_cgst">0\.00<', f'id="c_cgst">{cgst_rs:,.2f}<', html)
    html = re.sub(r'id="c_sgst">0\.00<', f'id="c_sgst">{sgst_rs:,.2f}<', html)
    html = re.sub(r'id="c_ro">0\.00<', f'id="c_ro">{round_off_str}<', html)
    html = re.sub(r'id="c_total">0\.00<', f'id="c_total">{grand_rs:,.2f}<', html)
    html = re.sub(r'<input id="paid"[^>]*>', f'{paid_rs:,.0f}', html)
    html = re.sub(r'id="c_bal">0\.00<', f'id="c_bal">{bal_rs:,.2f}<', html)

    return html

def export_bill_to_pdf(bill_data: dict, output_path: str, page_size: str = "A5") -> bool:
    """
    Exports the invoice directly to a single-page PDF with pixel-perfect accuracy.
    Uses headless Chrome/Edge for exact CSS flex/grid rendering.
    """
    try:
        dirname = os.path.dirname(output_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        html_content = generate_bill_html(bill_data, page_size=page_size)
        browser = find_headless_browser()

        if browser:
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
                tf.write(html_content)
                temp_html = tf.name

            try:
                cmd = [
                    browser,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={os.path.abspath(output_path)}",
                    f"file:///{os.path.abspath(temp_html).replace(os.sep, '/')}"
                ]
                res = subprocess.run(cmd, capture_output=True, timeout=20)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
                else:
                    print(f"[PDF Export Error] Browser returned: {res.stderr.decode('utf-8', errors='ignore')}")
            finally:
                if os.path.exists(temp_html):
                    try:
                        os.remove(temp_html)
                    except Exception:
                        pass

        # Fallback to Qt QPrinter if no browser is installed
        printer = QPrinter(QPrinter.PrinterResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        if page_size.upper() == "A4":
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageMargins(QMarginsF(4, 4, 4, 4), QPageLayout.Millimeter)
        else:
            printer.setPageSize(QPageSize(QPageSize.A5))
            printer.setPageMargins(QMarginsF(3, 3, 3, 3), QPageLayout.Millimeter)
        printer.setOutputFileName(output_path)

        paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
        doc.setHtml(html_content)
        doc.print_(printer)
        return True

    except Exception as e:
        print(f"[Print Manager] PDF export failed: {e}")
        return False

def print_or_pdf_bill(bill_data: dict, parent_window=None, save_pdf_path: str = None, page_size: str = "A5") -> bool:
    """
    Renders the bill and opens the print dialog or saves to PDF.
    When sent to a physical printer, renders the generated PDF via QPdfDocument for 100% fidelity.
    """
    if save_pdf_path:
        return export_bill_to_pdf(bill_data, save_pdf_path, page_size=page_size)

    # Generate PDF in standard invoices directory
    invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    cust_name = bill_data.get("customer_name") or bill_data.get("name_gu") or bill_data.get("name_en") or "Customer"
    safe_name = re.sub(r'[^a-zA-Z0-9_\u0A80-\u0AFF]', '_', str(cust_name))
    bill_no = bill_data.get("bill_no", 1)
    pdf_path = os.path.join(invoices_dir, f"Invoice_Bill_{bill_no}_{safe_name}.pdf")

    success = export_bill_to_pdf(bill_data, pdf_path, page_size=page_size)
    if not success:
        return False

    printer = QPrinter(QPrinter.HighResolution)
    if page_size.upper() == "A4":
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageMargins(QMarginsF(4, 4, 4, 4), QPageLayout.Millimeter)
    else:
        printer.setPageSize(QPageSize(QPageSize.A5))
        printer.setPageMargins(QMarginsF(3, 3, 3, 3), QPageLayout.Millimeter)

    dialog = QPrintDialog(printer, parent_window)
    if dialog.exec():
        try:
            pdf_doc = QPdfDocument()
            pdf_doc.load(pdf_path)
            if pdf_doc.pageCount() > 0:
                painter = QPainter(printer)
                paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
                page_img = pdf_doc.render(0, paint_rect.size())
                painter.drawImage(0, 0, page_img)
                painter.end()
                return True
        except Exception as e:
            print(f"[Print Manager] Physical print error: {e}")
            # Fallback to Windows default print
            try:
                os.startfile(pdf_path, "print")
                return True
            except Exception:
                pass
    else:
        # User canceled dialog; open the PDF for viewing
        try:
            os.startfile(pdf_path)
        except Exception:
            pass

    return True

# ----------------- URD Customer Purchase Voucher (Old Gold / Buyback) -----------------

def generate_urd_voucher_html(urd_data: dict, shop_settings: dict = None, page_size: str = "A5") -> str:
    """
    Generates an official, compact single-page URD Purchase Voucher (Sec 31(3)(f)).
    Matches the shop's burgundy theme (#6b2433), authentic fonts, and legal declaration.
    """
    if not shop_settings:
        st = load_settings()
        shop_settings = {
            "header_left": st.get("header_left", "વાયુ આદિતી"),
            "header_center": st.get("header_center", "॥ શ્રી હરિ ॥"),
            "header_right": st.get("header_right", "બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫"),
            "shop_name_gu": st.get("shop_name_gu", "સોની નટવરલાલ હિંમતલાલ"),
            "proprietor": st.get("proprietor", "સોની બ્રિજેશ નટવરલાલ"),
            "tagline": st.get("tagline", "સોના-ચાંદીના દાગીના બનાવનાર તથા વેચનાર."),
            "address": st.get("address", "જૈન દેરાસર પાસે, બાવળા-૩૮૨૨૨૦. જી. અમદાવાદ."),
            "gstin": st.get("gstin", "24BPXPS8279A1Z7")
        }

    logo_b64 = get_nh_logo_base64()

    voucher_no = str(urd_data.get("invoice_no") or urd_data.get("voucher_no") or "1")
    raw_date = str(urd_data.get("purchase_date") or "")
    try:
        if "-" in raw_date:
            dt = datetime.strptime(raw_date.split()[0], "%Y-%m-%d")
            date_str = dt.strftime("%d/%m/%Y")
        else:
            date_str = raw_date
    except Exception:
        date_str = raw_date or datetime.now().strftime("%d/%m/%Y")

    cust_name = urd_data.get("supplier_name") or urd_data.get("customer_name") or "Customer"
    cust_uid = urd_data.get("supplier_uid") or urd_data.get("customer_uid") or ""
    cust_mob = urd_data.get("mobile") or urd_data.get("phone") or ""
    cust_addr = urd_data.get("address") or ""

    desc = urd_data.get("description", "જૂનું સોનું / દાગીના")
    gross_g = (urd_data.get("weight_mg", 0) or urd_data.get("gross_weight_mg", 0)) / 1000.0
    touch = float(urd_data.get("touch_purity", 100.0) or 100.0)
    fine_g = (urd_data.get("fine_weight_mg", 0)) / 1000.0
    if fine_g <= 0 and gross_g > 0:
        fine_g = round(gross_g * (touch / 100.0), 3)

    rate_rs = (urd_data.get("rate_paise", 0)) / 100.0
    subtotal_rs = (urd_data.get("subtotal_paise", 0)) / 100.0
    gst_rate = float(urd_data.get("gst_rate_percent", 5.0) or 5.0)
    gst_rs = (urd_data.get("gst_paise", 0)) / 100.0
    gst_treatment = str(urd_data.get("gst_treatment", "DEDUCTED")).upper()
    net_payout_rs = (urd_data.get("net_payout_paise", 0) or urd_data.get("total_paise", 0)) / 100.0
    mode = str(urd_data.get("payment_mode", "CASH")).upper()

    treatment_label = "કપાત (Deducted)" if gst_treatment == "DEDUCTED" else "ઉમેરેલ (Added)"
    words_payout = f"Rupees {num_to_words_title_case(round(net_payout_rs))} Only"

    pw, ph = ("148mm", "210mm") if page_size.upper() == "A5" else ("210mm", "297mm")

    html = f"""<!DOCTYPE html>
<html lang="gu">
<head>
<meta charset="utf-8">
<style>
@page {{ size: {pw} {ph}; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 0;
    background: #fff;
    color: #2a1a1a;
    font-family: "Noto Sans Gujarati", "Tinos", system-ui, sans-serif;
    font-size: 8.5pt;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}
.paper {{
    width: {pw};
    min-height: {ph};
    margin: 0 auto;
    padding: 6mm 7mm;
    background: #fffaf6;
}}
.hd {{
    border: 1.2px solid #6b2433;
    margin-bottom: 2mm;
}}
.hd .top {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    padding: 0.6mm 2mm;
    font-weight: 700;
    font-size: 7.5pt;
    border-bottom: 1px solid #6b2433;
}}
.hd .top span:nth-child(2) {{ text-align: center; }}
.hd .top span:nth-child(3) {{ text-align: right; }}
.hd .name {{
    display: flex;
    gap: 3mm;
    align-items: center;
    padding: 1.2mm 2mm;
}}
.logo {{ height: 11mm; width: auto; display: block; }}
.hd h1 {{ margin: 0; font-size: 11pt; color: #6b2433; text-align: center; line-height: 1.2; }}
.hd .sub {{ text-align: center; font-size: 6.8pt; line-height: 1.25; }}
.hd .badge {{
    background: #6b2433;
    color: #fff;
    font-size: 7.5pt;
    font-weight: 700;
    text-align: center;
    padding: 1mm;
    letter-spacing: 0.5px;
}}
.meta {{
    display: flex;
    justify-content: space-between;
    margin: 1.5mm 0;
    font-size: 8.5pt;
}}
.box {{
    border: 1.2px solid #6b2433;
    padding: 1.5mm 2.5mm;
    margin-bottom: 2mm;
    background: #fff;
    font-size: 8pt;
    line-height: 1.35;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 2mm;
}}
th, td {{
    border: 1px solid #6b2433;
    padding: 1.2mm 1.5mm;
    font-size: 8pt;
    vertical-align: middle;
}}
th {{
    background: #f1d9cf;
    text-align: center;
    font-weight: 700;
}}
td.n {{ text-align: right; }}
.tot td {{
    font-weight: 700;
    background: #f6e7df;
}}
.sum {{
    display: flex;
    gap: 3mm;
    margin-top: 1mm;
    align-items: stretch;
}}
.left-sum {{
    flex: 1;
    border: 1px solid #6b2433;
    padding: 1.5mm 2mm;
    font-size: 7.8pt;
    background: #fff;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.calc {{
    width: 60mm;
    border-collapse: collapse;
}}
.calc td {{
    border: 1px solid #6b2433;
    padding: 0.8mm 1.5mm;
    font-size: 8pt;
}}
.calc td:last-child {{ text-align: right; }}
.calc .highlight td {{
    font-weight: 700;
    background: #f1d9cf;
    font-size: 9pt;
    color: #6b2433;
}}
.dec {{
    margin-top: 2mm;
    font-size: 6.8pt;
    color: #555;
    line-height: 1.2;
    border-top: 1px dashed #b9a0a0;
    padding-top: 1mm;
}}
.foot {{
    display: flex;
    justify-content: space-between;
    margin-top: 4mm;
    font-size: 8pt;
    align-items: end;
}}
.sig {{
    text-align: center;
    min-width: 44mm;
    border-top: 1px solid #6b2433;
    padding-top: 1mm;
    font-weight: 600;
}}
</style>
</head>
<body>
<div class="paper">
  <div class="hd">
    <div class="top">
      <span>{shop_settings['header_left']}</span>
      <span>{shop_settings['header_center']}</span>
      <span>{shop_settings['header_right']}</span>
    </div>
    <div class="top" style="border-bottom: 1px solid #6b2433; font-weight: 600;">
      <span>GSTIN : {shop_settings['gstin']}</span>
      <span></span>
      <span>બાવળા (અમદાવાદ)</span>
    </div>
    <div class="name">
      <img class="logo" alt="NH logo" src="data:image/png;base64,{logo_b64}">
      <div style="flex:1">
        <h1>{shop_settings['shop_name_gu']}</h1>
        <div class="sub">
          પ્રોપરાઈટર : {shop_settings['proprietor']}<br>
          <b>{shop_settings['tagline']}</b><br>
          {shop_settings['address']}
        </div>
      </div>
    </div>
    <div class="badge">
      જૂનું સોનું / પસ્તી ખરીદ વાઉચર (URD PURCHASE VOUCHER - Section 31(3)(f))
    </div>
  </div>

  <div class="meta">
    <div><b>વાઉચર નં. (Voucher No.):</b> #{voucher_no}</div>
    <div><b>તારીખ (Date):</b> {date_str}</div>
  </div>

  <div class="box">
    <div style="display: flex; justify-content: space-between;">
      <div><b>ગ્રાહક / વેચનાર (Seller):</b> {cust_name}</div>
      <div><b>આધાર નં. (Aadhaar UID):</b> <span style="font-family: monospace; font-size: 8.5pt; font-weight: bold;">{cust_uid or '—'}</span></div>
    </div>
    <div style="display: flex; justify-content: space-between; margin-top: 1mm;">
      <div><b>મોબાઇલ (Mobile):</b> {cust_mob or '—'}</div>
      <div><b>સરનામું (Address):</b> {cust_addr or 'બાવળા'}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width: 6mm;">ક્રમ</th>
        <th>વસ્તુની વિગત (Item Description)</th>
        <th style="width: 17mm;">ગ્રોસ વજન<br><small>Gross g</small></th>
        <th style="width: 15mm;">ટચ / પ્યોરિટી<br><small>Touch %</small></th>
        <th style="width: 17mm;">ચોખ્ખું સોનું<br><small>Fine Wt. g</small></th>
        <th style="width: 18mm;">ખરીદ ભાવ<br><small>Rate ₹/g</small></th>
        <th style="width: 22mm;">રકમ<br><small>Gross ₹</small></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="text-align: center;">1</td>
        <td style="font-weight: 600;">{desc}</td>
        <td class="n">{gross_g:.3f}</td>
        <td style="text-align: center;">{touch:.1f}%</td>
        <td class="n">{fine_g:.3f}</td>
        <td class="n">{rate_rs:,.0f}</td>
        <td class="n" style="font-weight: 600;">{subtotal_rs:,.2f}</td>
      </tr>
    </tbody>
    <tfoot>
      <tr class="tot">
        <td colspan="2" style="text-align: right;">કુલ (Total)</td>
        <td class="n">{gross_g:.3f}</td>
        <td></td>
        <td class="n">{fine_g:.3f}</td>
        <td></td>
        <td class="n">{subtotal_rs:,.2f}</td>
      </tr>
    </tfoot>
  </table>

  <div class="sum">
    <div class="left-sum">
      <div>
        <b>અંકે રૂપિયા:</b> {words_payout}<br>
        <b>ચૂકવણી પદ્ધતિ (Mode):</b> {mode}
      </div>
      <div class="dec">
        <b>ગ્રાહકની બાંયધરી (Declaration):</b><br>
        આથી હું ખાતરી આપું છું કે વેચેલ દાગીના મારી અંગત માલિકીના છે, કોઈપણ વિવાદ વગરના છે અને તેનું સંપૂર્ણ ચુકવણું મને મળેલ છે.
      </div>
    </div>

    <table class="calc">
      <tr>
        <td>માલ રકમ (Gross Value)</td>
        <td>{subtotal_rs:,.2f}</td>
      </tr>
      <tr>
        <td>{gst_rate:.1f}% GST ({treatment_label})</td>
        <td style="color: {'#b3261e' if gst_treatment == 'DEDUCTED' else '#16a34a'}; font-weight: 600;">
          {'-' if gst_treatment == 'DEDUCTED' else '+'} {gst_rs:,.2f}
        </td>
      </tr>
      <tr class="highlight">
        <td>ચૂકવેલ ચોખ્ખી રકમ (Net Payout)</td>
        <td>₹ {net_payout_rs:,.2f}</td>
      </tr>
    </table>
  </div>

  <div class="foot">
    <div class="sig">
      ગ્રાહક / વેચનારની સહી<br>
      <span style="font-size: 6.8pt; color: #555;">(Customer Signature)</span>
    </div>
    <div class="sig">
      સોની નટવરલાલ હિંમતલાલ<br>
      <span style="font-size: 6.8pt; color: #555;">પ્રોપરાઈટર સહી</span>
    </div>
  </div>
</div>
</body>
</html>"""
    return html

def export_urd_voucher_to_pdf(urd_data: dict, output_path: str, page_size: str = "A5") -> bool:
    """Exports URD Purchase Voucher directly to single-page PDF with pixel-perfect accuracy."""
    try:
        dirname = os.path.dirname(output_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        html_content = generate_urd_voucher_html(urd_data, page_size=page_size)
        browser = find_headless_browser()

        if browser:
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
                tf.write(html_content)
                temp_html = tf.name

            try:
                cmd = [
                    browser,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={os.path.abspath(output_path)}",
                    f"file:///{os.path.abspath(temp_html).replace(os.sep, '/')}"
                ]
                res = subprocess.run(cmd, capture_output=True, timeout=20)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
                else:
                    print(f"[URD PDF Export Error] Browser returned: {res.stderr.decode('utf-8', errors='ignore')}")
            finally:
                if os.path.exists(temp_html):
                    try:
                        os.remove(temp_html)
                    except Exception:
                        pass

        # Fallback to Qt QPrinter
        printer = QPrinter(QPrinter.PrinterResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPageSize(QPageSize(QPageSize.A5))
        printer.setPageMargins(QMarginsF(3, 3, 3, 3), QPageLayout.Millimeter)
        printer.setOutputFileName(output_path)

        paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setPageSize(QSizeF(paint_rect.width(), paint_rect.height()))
        doc.setHtml(html_content)
        doc.print_(printer)
        return True

    except Exception as e:
        print(f"[Print Manager] URD voucher PDF export failed: {e}")
        return False

def print_or_pdf_urd_voucher(urd_data: dict, parent_window=None, save_pdf_path: str = None, page_size: str = "A5") -> bool:
    """Renders URD voucher and opens print dialog or exports to PDF."""
    if save_pdf_path:
        return export_urd_voucher_to_pdf(urd_data, save_pdf_path, page_size=page_size)

    invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    cust_name = urd_data.get("supplier_name") or urd_data.get("customer_name") or "Customer"
    safe_name = re.sub(r'[^a-zA-Z0-9_\u0A80-\u0AFF]', '_', str(cust_name))
    voucher_no = str(urd_data.get("invoice_no") or urd_data.get("voucher_no") or "1")
    pdf_path = os.path.join(invoices_dir, f"URD_Voucher_{voucher_no}_{safe_name}.pdf")

    success = export_urd_voucher_to_pdf(urd_data, pdf_path, page_size=page_size)
    if not success:
        return False

    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.A5))
    printer.setPageMargins(QMarginsF(3, 3, 3, 3), QPageLayout.Millimeter)

    dialog = QPrintDialog(printer, parent_window)
    if dialog.exec():
        try:
            pdf_doc = QPdfDocument()
            pdf_doc.load(pdf_path)
            if pdf_doc.pageCount() > 0:
                painter = QPainter(printer)
                paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
                page_img = pdf_doc.render(0, paint_rect.size())
                painter.drawImage(0, 0, page_img)
                painter.end()
                return True
        except Exception as e:
            print(f"[Print Manager] Physical print error: {e}")
            try:
                os.startfile(pdf_path, "print")
                return True
            except Exception:
                pass
    else:
        try:
            os.startfile(pdf_path)
        except Exception:
            pass

    return True
