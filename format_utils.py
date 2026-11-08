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

