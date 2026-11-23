"""
database.py - SQLite Database Engine.
Calculates balances dynamically. Stored in integer paise.
Includes analytics for the Executive Dashboard.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jewelry_shop.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_gu TEXT NOT NULL,
            name_en TEXT DEFAULT '',
            mobile TEXT NOT NULL,
            address TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no INTEGER NOT NULL,
            book_no INTEGER DEFAULT 1,
            bill_date TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            subtotal_paise INTEGER NOT NULL,
            cgst_paise INTEGER NOT NULL,
            sgst_paise INTEGER NOT NULL,
            grand_total_paise INTEGER NOT NULL,
            paid_paise INTEGER NOT NULL,
            balance_paise INTEGER NOT NULL,
            payment_mode TEXT DEFAULT 'CASH',
            status TEXT DEFAULT 'ACTIVE',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            hsn_code TEXT DEFAULT '',
            weight_mg INTEGER NOT NULL,
            rate_paise INTEGER NOT NULL,
            making_paise INTEGER DEFAULT 0,
            amount_paise INTEGER NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        );
    """)

    try:
        c.execute("ALTER TABLE bill_items ADD COLUMN making_paise INTEGER DEFAULT 0;")
    except:
        pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            entry_type TEXT NOT NULL CHECK(entry_type IN ('UDHAR', 'JAMA')),
            amount_paise INTEGER NOT NULL,
            bill_id INTEGER,
            payment_mode TEXT DEFAULT 'CASH',
            remark TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        );
    """)

    # Purchases Table (Wholesale Inward Inventory & GST ITC Tracking)
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            supplier_name TEXT NOT NULL,
            supplier_gstin TEXT DEFAULT '',
            description TEXT NOT NULL,
            weight_mg INTEGER NOT NULL,
            rate_paise INTEGER NOT NULL,
            subtotal_paise INTEGER NOT NULL,
            gst_paise INTEGER NOT NULL,
            total_paise INTEGER NOT NULL,
            payment_mode TEXT DEFAULT 'CASH',
            payment_ref TEXT DEFAULT '',
            payment_status TEXT DEFAULT 'PAID',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Safe Schema Migrations
    for tbl, col, col_type in [
        ("customers", "pan_no", "TEXT DEFAULT ''"),
        ("customers", "aadhaar_no", "TEXT DEFAULT ''"),
        ("bills", "payment_ref", "TEXT DEFAULT ''"),
        ("ledger", "payment_ref", "TEXT DEFAULT ''"),
        ("purchases", "purchase_type", "TEXT DEFAULT 'DEALER'"),
        ("purchases", "customer_id", "INTEGER DEFAULT NULL"),
        ("purchases", "supplier_uid", "TEXT DEFAULT ''"),
        ("purchases", "touch_purity", "REAL DEFAULT 100.0"),
        ("purchases", "fine_weight_mg", "INTEGER DEFAULT 0"),
        ("purchases", "gst_rate_percent", "REAL DEFAULT 3.0"),
        ("purchases", "gst_treatment", "TEXT DEFAULT 'ADDED'"),
        ("purchases", "net_payout_paise", "INTEGER DEFAULT 0"),
    ]:
        try:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};")
        except:
            pass

    conn.commit()
    conn.close()

    # Automatically ensure historical ledger data is 100% accurate
    try:
        migrate_ledger_records()
    except Exception as e:
        print(f"[DB] Migration warning: {e}")

# ----------------- Customer Helpers -----------------

def add_customer(name_gu: str, mobile: str, address: str = "", name_en: str = "", gstin: str = "", pan_no: str = "", aadhaar_no: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO customers (name_gu, name_en, mobile, address, gstin, pan_no, aadhaar_no)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (name_gu.strip(), name_en.strip(), mobile.strip(), address.strip(), gstin.strip(), pan_no.strip().upper(), aadhaar_no.strip()))
    cust_id = c.lastrowid
    conn.commit()
    conn.close()
    return cust_id

def get_all_customers() -> List[Dict]:
    """Returns all customers sorted alphabetically for selection dropdowns."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers ORDER BY name_gu ASC, name_en ASC, id DESC;")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def search_customers(keyword: str) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    q = f"%{keyword.strip()}%"
    c.execute("""
        SELECT * FROM customers 
        WHERE mobile LIKE ? OR name_gu LIKE ? OR name_en LIKE ?
        ORDER BY id DESC LIMIT 50;
    """, (q, q, q))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_customer_by_mobile(mobile: str) -> Optional[Dict]:
    """Returns customer record only if the mobile number matches strictly and exactly."""
    clean_mob = mobile.strip()
    if not clean_mob:
        return None
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE mobile = ? ORDER BY id DESC LIMIT 1;", (clean_mob,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# ----------------- Balance Calculation -----------------

def get_customer_balance(customer_id: int) -> int:
    """Calculates: Total Udhar minus Total Jama in paise."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(amount_paise), 0) FROM ledger WHERE customer_id = ? AND entry_type = 'UDHAR';", (customer_id,))
    udhar = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount_paise), 0) FROM ledger WHERE customer_id = ? AND entry_type = 'JAMA';", (customer_id,))
    jama = c.fetchone()[0]
    conn.close()
    return udhar - jama

def add_payment(customer_id: int, amount_paise: int, payment_mode: str = "CASH", remark: str = "", date_str: str = None, payment_ref: str = "") -> int:
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, payment_mode, remark, payment_ref)
        VALUES (?, ?, 'JAMA', ?, ?, ?, ?);
    """, (customer_id, date_str, amount_paise, payment_mode, remark, payment_ref.strip()))
    lid = c.lastrowid
    conn.commit()
    conn.close()
    return lid

def get_customer_ledger(customer_id: int) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT l.*, b.bill_no 
        FROM ledger l
        LEFT JOIN bills b ON l.bill_id = b.id
        WHERE l.customer_id = ?
        ORDER BY l.entry_date ASC, l.id ASC;
    """, (customer_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ----------------- Bill Helpers -----------------

def get_next_bill_number() -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COALESCE(MAX(bill_no), 0) + 1 FROM bills;")
    next_no = c.fetchone()[0]
    conn.close()
    return next_no

def get_customer_bills(customer_id: int) -> List[Dict]:
    """Returns all past bills for a specific customer."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM bills 
        WHERE customer_id = ? 
        ORDER BY id DESC;
    """, (customer_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_bill_full_details(bill_id: int) -> Optional[Dict]:
    """Returns complete bill details with customer info, pan/aadhaar, payment_ref, and all line items for viewing/reprinting."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT b.*, c.name_gu, c.name_en, c.mobile, c.address, c.gstin, c.pan_no, c.aadhaar_no
        FROM bills b
        JOIN customers c ON b.customer_id = c.id
        WHERE b.id = ?;
    """, (bill_id,))
    bill_row = c.fetchone()
    if not bill_row:
        conn.close()
        return None

    bill_dict = dict(bill_row)

    # Fetch items
    c.execute("""
        SELECT * FROM bill_items WHERE bill_id = ?;
    """, (bill_id,))
    bill_dict["items"] = [dict(r) for r in c.fetchall()]
    conn.close()
    return bill_dict

def create_bill(customer_id: int, bill_date: str, items: List[Dict], paid_paise: int, payment_mode: str = "CASH", payment_ref: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    
    subtotal_paise = sum(item["amount_paise"] for item in items)
    cgst_paise = round(subtotal_paise * 0.015)
    sgst_paise = round(subtotal_paise * 0.015)
    grand_total_paise = subtotal_paise + cgst_paise + sgst_paise
    balance_paise = max(0, grand_total_paise - paid_paise)
    bill_no = get_next_bill_number()

    c.execute("""
        INSERT INTO bills (
            bill_no, bill_date, customer_id, subtotal_paise,
            cgst_paise, sgst_paise, grand_total_paise, paid_paise,
            balance_paise, payment_mode, payment_ref
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (bill_no, bill_date, customer_id, subtotal_paise, cgst_paise, sgst_paise, grand_total_paise, paid_paise, balance_paise, payment_mode, payment_ref.strip()))
    
    bill_id = c.lastrowid

    for item in items:
        c.execute("""
            INSERT INTO bill_items (bill_id, description, hsn_code, weight_mg, rate_paise, making_paise, amount_paise)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (bill_id, item["description"], item.get("hsn_code", ""), item["weight_mg"], item["rate_paise"], item.get("making_paise", 0), item["amount_paise"]))

    # 1. Full Grand Total goes to UDHAR (Debit - Customer bought goods)
    c.execute("""
        INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark)
        VALUES (?, ?, 'UDHAR', ?, ?, 'BILL', ?);
    """, (customer_id, bill_date, grand_total_paise, bill_id, f"બિલ નં. {bill_no} (કુલ ખરીદી / Total Bill)"))

    # 2. Payment made at billing goes to JAMA (Credit - Payment received)
    if paid_paise > 0:
        remark_txt = f"બિલ નં. {bill_no} પેમેન્ટ"
        if payment_ref.strip():
            remark_txt += f" ({payment_ref.strip()})"
        c.execute("""
            INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark, payment_ref)
            VALUES (?, ?, 'JAMA', ?, ?, ?, ?, ?);
        """, (customer_id, bill_date, paid_paise, bill_id, payment_mode, remark_txt, payment_ref.strip()))

    conn.commit()
    conn.close()
    return bill_id

# ----------------- Dashboard Analytics -----------------

def get_dashboard_metrics() -> Dict:
    """Returns today's metrics and total outstanding ledger balances."""
    conn = get_connection()
    c = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Today's Total Sales
    c.execute("SELECT COALESCE(SUM(grand_total_paise), 0), COUNT(id) FROM bills WHERE bill_date = ? AND status = 'ACTIVE';", (today_str,))
    row_today = c.fetchone()
    today_sales_paise = row_today[0]
    today_bills_count = row_today[1]

    # 2. Total Customers
    c.execute("SELECT COUNT(id) FROM customers;")
    total_customers = c.fetchone()[0]

    # 3. Total Market Udhar (Sum of all positive outstanding customer balances)
    c.execute("""
        SELECT COALESCE(SUM(balance), 0) FROM (
            SELECT customer_id, 
                   SUM(CASE WHEN entry_type = 'UDHAR' THEN amount_paise ELSE -amount_paise END) as balance
            FROM ledger
            GROUP BY customer_id
            HAVING balance > 0
        );
    """)
    total_market_udhar = c.fetchone()[0]

    # 4. Recent Bills (Last 8)
    c.execute("""
        SELECT b.id, b.bill_no, b.bill_date, b.grand_total_paise, b.balance_paise, b.payment_mode, c.name_gu, c.mobile
        FROM bills b
        JOIN customers c ON b.customer_id = c.id
        ORDER BY b.id DESC LIMIT 8;
    """)
    recent_bills = [dict(r) for r in c.fetchall()]

    # 5. GST Analytics (Sales Output GST vs Purchase Input Tax Credit)
    c.execute("SELECT COALESCE(SUM(cgst_paise + sgst_paise), 0) FROM bills WHERE status = 'ACTIVE';")
    output_gst_paise = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(gst_paise), 0) FROM purchases;")
    input_gst_paise = c.fetchone()[0]

    net_gst_paise = output_gst_paise - input_gst_paise

    conn.close()
    return {
        "today_sales_paise": today_sales_paise,
        "today_bills_count": today_bills_count,
        "total_customers": total_customers,
        "total_market_udhar_paise": total_market_udhar,
        "recent_bills": recent_bills,
        "output_gst_paise": output_gst_paise,
        "input_gst_paise": input_gst_paise,
        "net_gst_paise": net_gst_paise
    }

# ----------------- Wholesale Purchases & URD Customer Old Gold -----------------

def add_purchase(
    invoice_no: str,
    purchase_date: str,
    supplier_name: str,
    supplier_gstin: str,
    description: str,
    weight_mg: int,
    rate_paise: int,
    subtotal_paise: int,
    gst_paise: int,
    total_paise: int,
    payment_mode: str = "CASH",
    payment_ref: str = "",
    payment_status: str = "PAID",
    purchase_type: str = "DEALER",
    customer_id: Optional[int] = None,
    supplier_uid: str = "",
    touch_purity: float = 100.0,
    fine_weight_mg: int = 0,
    gst_rate_percent: float = 3.0,
    gst_treatment: str = "ADDED",
    net_payout_paise: int = 0
) -> int:
    conn = get_connection()
    c = conn.cursor()
    if net_payout_paise <= 0:
        net_payout_paise = total_paise

    c.execute("""
        INSERT INTO purchases (
            invoice_no, purchase_date, supplier_name, supplier_gstin,
            description, weight_mg, rate_paise, subtotal_paise,
            gst_paise, total_paise, payment_mode, payment_ref, payment_status,
            purchase_type, customer_id, supplier_uid, touch_purity,
            fine_weight_mg, gst_rate_percent, gst_treatment, net_payout_paise
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        invoice_no.strip(), purchase_date, supplier_name.strip(), supplier_gstin.strip().upper(),
        description.strip(), weight_mg, rate_paise, subtotal_paise,
        gst_paise, total_paise, payment_mode, payment_ref.strip(), payment_status,
        purchase_type, customer_id, supplier_uid.strip(), touch_purity,
        fine_weight_mg, gst_rate_percent, gst_treatment, net_payout_paise
    ))
    pid = c.lastrowid

    # If this is an URD purchase and payment mode is KHATA, credit customer's ledger!
    if purchase_type == "URD" and customer_id and payment_mode.upper() in ["KHATA", "ADJUST IN KHATA", "LEDGER"]:
        c.execute("""
            INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark, payment_ref)
            VALUES (?, ?, 'JAMA', ?, NULL, 'OLD GOLD (URD)', ?, ?);
        """, (customer_id, purchase_date, net_payout_paise, f"URD જૂનું સોનું ખરીદી વાઉચર #{invoice_no}", payment_ref.strip()))

    conn.commit()
    conn.close()
    return pid

def add_urd_purchase(
    voucher_no: str,
    purchase_date: str,
    customer_name: str,
    customer_uid: str,
    customer_id: Optional[int],
    description: str,
    gross_weight_mg: int,
    touch_purity: float,
    fine_weight_mg: int,
    rate_paise: int,
    subtotal_paise: int,
    gst_rate_percent: float,
    gst_paise: int,
    gst_treatment: str,
    net_payout_paise: int,
    payment_mode: str = "CASH",
    payment_ref: str = ""
) -> int:
    """Convenience method to record an official URD Purchase / Old Gold buyback."""
    total_paise = subtotal_paise + (gst_paise if gst_treatment == "ADDED" else -gst_paise)
    return add_purchase(
        invoice_no=voucher_no,
        purchase_date=purchase_date,
        supplier_name=customer_name,
        supplier_gstin="",
        description=description,
        weight_mg=gross_weight_mg,
        rate_paise=rate_paise,
        subtotal_paise=subtotal_paise,
        gst_paise=gst_paise,
        total_paise=total_paise,
        payment_mode=payment_mode,
        payment_ref=payment_ref,
        payment_status="PAID",
        purchase_type="URD",
        customer_id=customer_id,
        supplier_uid=customer_uid,
        touch_purity=touch_purity,
        fine_weight_mg=fine_weight_mg,
        gst_rate_percent=gst_rate_percent,
        gst_treatment=gst_treatment,
        net_payout_paise=net_payout_paise
    )

def get_next_urd_voucher_number() -> int:
    """Calculates the next sequential URD voucher number."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT invoice_no FROM purchases WHERE purchase_type = 'URD';")
    rows = c.fetchall()
    max_no = 0
    for r in rows:
        inv = str(r[0])
        nums = re.findall(r'\d+', inv)
        if nums:
            val = int(nums[-1])
            if val > max_no:
                max_no = val
    conn.close()
    return max_no + 1

def get_purchase_by_id(purchase_id: int) -> Optional[Dict]:
    """Fetches full details of a specific purchase or URD voucher by ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM purchases WHERE id = ?;", (purchase_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_purchases(keyword: str = "", purchase_type: str = None) -> List[Dict]:
    """
    Returns purchases with optional keyword search and purchase_type filtering.
    Searches across supplier/customer name, UID, GSTIN, invoice/voucher no, and description.
    """
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM purchases WHERE 1=1"
    params = []

    if purchase_type and purchase_type.upper() in ["URD", "DEALER"]:
        query += " AND purchase_type = ?"
        params.append(purchase_type.upper())

    if keyword.strip():
        q = f"%{keyword.strip()}%"
        query += """ AND (
            supplier_name LIKE ? OR 
            supplier_uid LIKE ? OR 
            supplier_gstin LIKE ? OR 
            invoice_no LIKE ? OR 
            description LIKE ?
        )"""
        params.extend([q, q, q, q, q])

    query += " ORDER BY purchase_date DESC, id DESC;"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def delete_purchase(purchase_id: int) -> bool:
    conn = get_connection()
    c = conn.cursor()
    # Check if URD with linked KHATA entry
    c.execute("SELECT invoice_no, purchase_type FROM purchases WHERE id = ?;", (purchase_id,))
    row = c.fetchone()
    if row and row["purchase_type"] == "URD":
        inv = row["invoice_no"]
        c.execute("DELETE FROM ledger WHERE remark LIKE ?;", (f"%#{inv}%",))
    c.execute("DELETE FROM purchases WHERE id = ?;", (purchase_id,))
    conn.commit()
    conn.close()
    return True

def backup_database(destination_folder: str) -> str:
    os.makedirs(destination_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(destination_folder, f"jewelry_shop_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_file)
    return backup_file

def migrate_ledger_records():
    """
    Ensures every bill has:
    1) An UDHAR ledger entry equal to its full grand_total_paise (Debit / Sale).
    2) A JAMA ledger entry equal to paid_paise (if paid_paise > 0).
    Fixes legacy data where down-payments were subtracted twice.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bills;")
    bills = [dict(r) for r in c.fetchall()]

    for b in bills:
        b_id = b["id"]
        b_no = b["bill_no"]
        c_id = b["customer_id"]
        b_date = b["bill_date"]
        gt = b["grand_total_paise"]
        paid = b["paid_paise"]
        pref = b.get("payment_ref", "") or ""
        pmode = b.get("payment_mode", "CASH") or "CASH"

        # Check existing UDHAR for this bill
        c.execute("SELECT id FROM ledger WHERE bill_id = ? AND entry_type = 'UDHAR';", (b_id,))
        u_row = c.fetchone()
        if u_row:
            c.execute("""
                UPDATE ledger 
                SET amount_paise = ?, remark = ?, payment_mode = 'BILL'
                WHERE id = ?;
            """, (gt, f"બિલ નં. {b_no} (કુલ ખરીદી / Total Bill)", u_row[0]))
        else:
            c.execute("""
                INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark)
                VALUES (?, ?, 'UDHAR', ?, ?, 'BILL', ?);
            """, (c_id, b_date, gt, b_id, f"બિલ નં. {b_no} (કુલ ખરીદી / Total Bill)"))

        # Check existing JAMA for this bill
        if paid > 0:
            c.execute("SELECT id FROM ledger WHERE bill_id = ? AND entry_type = 'JAMA';", (b_id,))
            j_row = c.fetchone()
            remark_txt = f"બિલ નં. {b_no} પેમેન્ટ"
            if pref.strip():
                remark_txt += f" ({pref.strip()})"
            if j_row:
                c.execute("""
                    UPDATE ledger 
                    SET amount_paise = ?, remark = ?, payment_ref = ?
                    WHERE id = ?;
                """, (paid, remark_txt, pref.strip(), j_row[0]))
            else:
                c.execute("""
                    INSERT INTO ledger (customer_id, entry_date, entry_type, amount_paise, bill_id, payment_mode, remark, payment_ref)
                    VALUES (?, ?, 'JAMA', ?, ?, ?, ?, ?);
                """, (c_id, b_date, paid, b_id, pmode, remark_txt, pref.strip()))

    conn.commit()
    conn.close()

def get_all_bills_history(start_date: str = None, end_date: str = None, keyword: str = "") -> List[Dict]:
    """
    Returns full list of bills with customer details and line-item summaries.
    Supports date range filtering and keyword searching.
    """
    conn = get_connection()
    c = conn.cursor()
    
    query = """
        SELECT b.*, c.name_gu, c.name_en, c.mobile, c.address, c.pan_no, c.aadhaar_no,
               (SELECT COUNT(bi.id) FROM bill_items bi WHERE bi.bill_id = b.id) as item_count
        FROM bills b
        JOIN customers c ON b.customer_id = c.id
        WHERE b.status = 'ACTIVE'
    """
    params = []
    
    if start_date:
        query += " AND b.bill_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND b.bill_date <= ?"
        params.append(end_date)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query += """ AND (
            CAST(b.bill_no AS TEXT) LIKE ? OR
            c.name_gu LIKE ? OR
            c.name_en LIKE ? OR
            c.mobile LIKE ? OR
            b.payment_mode LIKE ? OR
            b.payment_ref LIKE ?
        )"""
        params.extend([kw, kw, kw, kw, kw, kw])
        
    query += " ORDER BY b.id DESC;"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
