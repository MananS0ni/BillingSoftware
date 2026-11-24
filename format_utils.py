"""
format_utils.py - Indian Numbering System & Currency Formatter.
Converts numbers into exact Indian Lakhs and Crores formatting:
e.g. 757050 -> ₹ 7,57,050.00 (instead of US Western 757,050.00)
"""

def format_inr(val, is_paise: bool = False, symbol: str = "₹ ") -> str:
    """
    Formats a number or paise into Indian currency format.
    Example:
        format_inr(757050) -> '₹ 7,57,050.00'
        format_inr(270000000, is_paise=True) -> '₹ 27,00,000.00'
    """
    try:
        if is_paise:
            num = float(val or 0) / 100.0
        else:
            num = float(val or 0)
    except (ValueError, TypeError):
        return f"{symbol}0.00"

    is_negative = num < 0
    num = abs(num)

    parts = f"{num:.2f}".split(".")
    int_p = parts[0]
    dec_p = parts[1]

    if len(int_p) <= 3:
        formatted_int = int_p
    else:
        last3 = int_p[-3:]
        rem = int_p[:-3]
        groups = []
        while len(rem) > 2:
            groups.insert(0, rem[-2:])
            rem = rem[:-2]
        if rem:
            groups.insert(0, rem)
        formatted_int = ",".join(groups) + "," + last3

    result = f"{symbol}{formatted_int}.{dec_p}"
    return f"-{result}" if is_negative else result


def num_to_words_title_case(num: float) -> str:
    """
    Converts a numerical amount into Indian currency words in Title Case.
    Example:
        58268 -> 'Rupees Fifty Eight Thousand Two Hundred and Sixty Eight Only'
    """
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def two_digits(n):
        if n < 20:
            return ones[n]
        rem = n % 10
        return (tens[n // 10] + (' ' + ones[rem] if rem else '')).strip()
    
    def three_digits(n):
        h = n // 100
        rem = n % 100
        res = ''
        if h:
            res += ones[h] + ' Hundred'
        if rem:
            res += (' and ' if res else '') + two_digits(rem)
        return res

    def convert_below_crore(n):
        sub_parts = []
        lakh = n // 100000
        n %= 100000
        thousand = n // 1000
        n %= 1000
        hundreds = n
        
        if lakh:
            sub_parts.append(two_digits(lakh) + ' Lakh')
        if thousand:
            sub_parts.append(two_digits(thousand) + ' Thousand')
        if hundreds:
            sub_parts.append(three_digits(hundreds))
        return ' '.join(p for p in sub_parts if p)

    n = int(round(num))
    if n <= 0:
        return 'Rupees Zero Only'
    
    parts = []
    crore = n // 10000000
    rem_crore = n % 10000000
    
    if crore:
        parts.append(convert_below_crore(crore) + ' Crore')
    if rem_crore:
        rem_str = convert_below_crore(rem_crore)
        if rem_str:
            parts.append(rem_str)
        
    return 'Rupees ' + ' '.join(parts) + ' Only'


# ---------------------------------------------------------------------------
# WhatsApp Invoice Caption Builder
# ---------------------------------------------------------------------------

def format_inr_clean(val: float) -> str:
    """
    Formats a numeric rupee value into Indian numbering format with ₹ symbol.
    Omit decimal digits when there are no paise (e.g. ₹2,48,250 or ₹1,66,991.44).
    """
    try:
        val = round(float(val), 2)
    except (ValueError, TypeError):
        return "₹0"

    is_neg = val < 0
    val = abs(val)

    int_part = int(val)
    paise_part = int(round((val - int_part) * 100))

    s = str(int_part)
    if len(s) <= 3:
        formatted_int = s
    else:
        last3 = s[-3:]
        rem = s[:-3]
        groups = []
        while len(rem) > 2:
            groups.insert(0, rem[-2:])
            rem = rem[:-2]
        if rem:
            groups.insert(0, rem)
        formatted_int = ",".join(groups) + "," + last3

    if paise_part > 0:
        res = f"₹{formatted_int}.{paise_part:02d}"
    else:
        res = f"₹{formatted_int}"

    return f"-{res}" if is_neg else res


def format_date_dmy(date_str: str) -> str:
    """
    Converts YYYY-MM-DD (e.g. 2026-11-24) to Indian DD-MM-YYYY format (24-11-2026).
    If already DD-MM-YYYY or unrecognized, returns cleanly without crashing.
    """
    if not date_str:
        return ""
    import re
    # Match YYYY-MM-DD
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", str(date_str).strip())
    if m:
        year, month, day = m.groups()
        return f"{int(day):02d}-{int(month):02d}-{year}"
    return str(date_str).strip()


def get_caption(customer_name: str, bill_no, bill_date: str, total, paid, is_paise: bool = False, shop_name: str = None) -> str:
    """
    Builds the official WhatsApp invoice caption in Gujarati according to shop rules.

    LOGIC:
    1. Greeting:
       - If customer_name is provided: 'નમસ્તે {customer_name} 🙏'
       - If customer_name is empty/missing: 'નમસ્તે 🙏' (Strictly no 'શેઠ' or prefix/suffix)
    2. Date: Formatted as DD-MM-YYYY.
    3. Due calculation: due_amount = round(total - paid, 2).
    4. Templates:
       - TEMPLATE A: used when due_amount > 0 (polite reminder of pending balance).
       - TEMPLATE B: used when due_amount <= 0 or invalid (fully paid / advance paid / thank you).
    5. Details kept in PDF only: Item names, weights, total amount and paid amount stay in the attached PDF.

    HOW TO EDIT TEMPLATES LATER:
    - Edit TEMPLATE_A or TEMPLATE_B strings below directly.
    - All text is UTF-8 Gujarati with standard line breaks.
    """
    # Fallback to configured shop name from settings if not supplied
    if not shop_name:
        try:
            from settings_manager import load_settings
            shop_name = load_settings().get("shop_name_gu") or "સોની નટવરલાલ હિમતલાલ"
        except Exception:
            shop_name = "સોની નટવરલાલ હિમતલાલ"

    # 1. Clean greeting (No 'શેઠ', just name or plain 'નમસ્તે 🙏')
    cleaned_name = (customer_name or "").strip()
    if cleaned_name:
        greeting = f"નમસ્તે {cleaned_name} 🙏"
    else:
        greeting = "નમસ્તે 🙏"

    # 2. Date in DD-MM-YYYY format
    formatted_date = format_date_dmy(bill_date)

    # 3. Calculate due amount
    try:
        t_val = float(total or 0)
        p_val = float(paid or 0)
        if is_paise:
            t_val /= 100.0
            p_val /= 100.0
        due_amount = round(t_val - p_val, 2)
    except (ValueError, TypeError) as e:
        import sys
        print(f"[WhatsApp Caption Warning] Invalid total or paid amount: {e}", file=sys.stderr)
        due_amount = 0.0

    # ------------------------------------------------------------------
    # TEMPLATE A: Due amount pending (due_amount > 0)
    # ------------------------------------------------------------------
    if due_amount > 0:
        formatted_due = format_inr_clean(due_amount)
        caption = (
            f"{greeting}\n\n"
            f"આપનું બિલ નં. {bill_no} (તારીખ: {formatted_date}) આ સાથે PDF માં મોકલ્યું છે.\n\n"
            f"આપનું {formatted_due} બાકી છે. અનુકૂળતા મુજબ જમા કરાવવા વિનંતી.\n\n"
            f"આભાર! 🙏\n"
            f"{shop_name}"
        )
    # ------------------------------------------------------------------
    # TEMPLATE B: No due / fully paid / advance paid (due_amount <= 0)
    # ------------------------------------------------------------------
    else:
        caption = (
            f"{greeting}\n\n"
            f"આપનું બિલ નં. {bill_no} (તારીખ: {formatted_date}) આ સાથે PDF માં મોકલ્યું છે.\n\n"
            f"આપની મુલાકાત બદલ ખૂબ ખૂબ આભાર!\n\n"
            f"{shop_name}"
        )

    return caption


