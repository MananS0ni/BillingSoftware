"""
generate_guide_pdf.py - Creates an executive PDF explanation document for the advisor/CA.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter
import os
import sys

def create_advisor_pdf():
    app = QApplication(sys.argv)
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Jewelry_Billing_System_Guide.pdf")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 30px;
                color: #1A2521;
                line-height: 1.6;
            }
            .header {
                text-align: center;
                border-bottom: 2px solid #D4AF37;
                padding-bottom: 12px;
                margin-bottom: 24px;
            }
            .title {
                font-size: 24px;
                font-weight: bold;
                color: #0B1E19;
            }
            .subtitle {
                font-size: 14px;
                color: #6E7A75;
                margin-top: 4px;
            }
            h2 {
                color: #0B1E19;
                font-size: 17px;
                border-left: 4px solid #D4AF37;
                padding-left: 10px;
                margin-top: 24px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 14px 0;
                font-size: 13px;
            }
            th, td {
                border: 1px solid #D1D5DB;
                padding: 9px 12px;
                text-align: left;
            }
            th {
                background-color: #F3EBD8;
                color: #0B1E19;
                font-weight: bold;
            }
            .formula-box {
                background-color: #F8F7F4;
                border: 1px solid #E8E4DC;
                border-radius: 8px;
                padding: 12px 16px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                margin: 12px 0;
            }
            .badge {
                display: inline-block;
                background-color: #D4AF37;
                color: #0B1E19;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">JEWELRY SHOP BILLING & LEDGER SOFTWARE</div>
            <div class="subtitle">System Architecture, Calculation Logic & Business Workflow Specification</div>
            <div style="font-size: 11px; color: #888; margin-top: 6px;">Prepared for Shop Owner, CA & Financial Advisor Review</div>
        </div>

        <h2>1. Executive Summary & Purpose</h2>
        <p>
            This software is a 100% offline desktop application built for Windows to manage retail jewelry billing,
            customer credit/debit (Jama/Udhar) accounts, and invoice printing in both <b>Gujarati</b> and <b>English</b>.
            All data resides securely in a local SQLite database file (<code>jewelry_shop.db</code>) on the shop PC with automated daily pen-drive backups.
        </p>

        <h2>2. Core Billing & Pricing Calculation Engine</h2>
        <p>Jewelry billing calculations are divided into 4 transparent stages:</p>
        
        <div class="formula-box">
            <b>STAGE 1: Line Item Calculation</b><br>
            • User inputs: <b>Weight in Grams</b> (e.g., 20.500 g) and <b>Gold/Silver Rate</b>.<br>
            • Standard Gold Rate Unit: Quoted per 10 grams (standard bullion quote in Gujarat).<br>
            • Item Amount Formula: <code>Amount = Weight_Grams × (Rate_per_10g ÷ 10) + Making_Charges</code><br><br>

            <b>STAGE 2: Subtotal</b><br>
            • <code>Subtotal = Sum of all Line Item Amounts</code><br><br>

            <b>STAGE 3: Tax Engine (Configurable / Optional)</b><br>
            • Jewelry GST (Tax Invoices): 3.0% total divided equally:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;→ CGST: 1.5% of Subtotal<br>
            &nbsp;&nbsp;&nbsp;&nbsp;→ SGST: 1.5% of Subtotal<br>
            • Estimate / Non-GST Bills: Tax is 0% (Toggled via checkbox).<br><br>

            <b>STAGE 4: Grand Total & Settlement</b><br>
            • <code>Grand Total = Subtotal + CGST + SGST - Discount</code><br>
            • <code>Balance Due (Udhar) = Grand Total - Paid Now</code>
        </div>

        <h2>3. Jama / Udhar Accounting & Ledger Principles</h2>
        <table>
            <tr>
                <th style="width: 25%;">Transaction</th>
                <th style="width: 35%;">Ledger Classification</th>
                <th style="width: 40%;">Accounting Impact</th>
            </tr>
            <tr>
                <td><b>New Unpaid Bill</b></td>
                <td><b>UDHAR (Debit)</b></td>
                <td>Increases customer debt by remaining unpaid balance.</td>
            </tr>
            <tr>
                <td><b>Customer Payment</b></td>
                <td><b>JAMA (Credit)</b></td>
                <td>Recorded under Cash, UPI, or Cheque. Reduces customer debt.</td>
            </tr>
            <tr>
                <td><b>Running Balance</b></td>
                <td><b>Dynamically Computed</b></td>
                <td><code>Balance = Sum(UDHAR) - Sum(JAMA)</code>. Never manually typed to prevent ledger fraud or math errors.</td>
            </tr>
        </table>

        <h2>4. Customer Management Model</h2>
        <p>
            • <b>Automatic Customer Creation:</b> Entering a customer's 10-digit mobile number and name directly on the bill screen automatically creates their customer account—no separate registration needed.<br>
            • <b>Stand-Alone Customer Directory:</b> Used exclusively when a customer visits the shop simply to deposit money (JAMA payment) or inspect their historic statement without purchasing new jewelry.
        </p>

        <h2>5. Gujarati & English Bilingual Architecture</h2>
        <table>
            <tr>
                <th>Feature</th>
                <th>Implementation</th>
            </tr>
            <tr>
                <td><b>UI Translation</b></td>
                <td>Dynamic 1-click switcher toggling 100% of labels, buttons, cards, and summaries.</td>
            </tr>
            <tr>
                <td><b>Script Typing</b></td>
                <td>Windows Gujarati Phonetic Input or integrated phonetic transliteration.</td>
            </tr>
            <tr>
                <td><b>Printed Invoice</b></td>
                <td>Gujarati Tax Invoice, English Tax Invoice, or Bilingual Header format with Gujarati guarantee terms.</td>
            </tr>
        </table>

        <h2>6. Security & Data Protection</h2>
        <p>
            • <b>Paise-Safe Currency:</b> Stored in integer paise (Rs 100.50 = 10050 paise) eliminating floating-point rounding bugs.<br>
            • <b>Immutable Bills:</b> Bills cannot be silently deleted; they can only be marked as cancelled with an audited reason.<br>
            • <b>1-Click USB Backup:</b> Copies the entire encrypted database file to an external pen drive with timestamp.
        </p>
    </body>
    </html>
    """

    doc = QTextDocument()
    doc.setHtml(html)

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(pdf_path)
    printer.setPageSize(QPageSize(QPageSize.A4))
    doc.print_(printer)

    print(f"SUCCESS: Generated PDF at: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_advisor_pdf()
