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


def num_to_words_inr(num: float) -> str:
    """
    Converts a numerical amount into Indian currency words in English uppercase.
    Example:
        58360 -> 'RUPEES : FIFTY-EIGHT THOUSAND THREE HUNDRED SIXTY ONLY'
    """
    ones = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
            'TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN',
            'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
    tens = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY']
    
    def two_digits(n):
        if n < 20:
            return ones[n]
        rem = n % 10
        return (tens[n // 10] + ('-' + ones[rem] if rem else '')).strip()
    
    def three_digits(n):
        h = n // 100
        rem = n % 100
        res = ''
        if h:
            res += ones[h] + ' HUNDRED'
        if rem:
            res += (' ' if res else '') + two_digits(rem)
        return res

    def convert_below_crore(n):
        sub_parts = []
        lakh = n // 100000
        n %= 100000
        thousand = n // 1000
        n %= 1000
        hundreds = n
        
        if lakh:
            sub_parts.append(two_digits(lakh) + ' LAKH')
        if thousand:
            sub_parts.append(two_digits(thousand) + ' THOUSAND')
        if hundreds:
            sub_parts.append(three_digits(hundreds))
        return ' '.join(p for p in sub_parts if p)

    n = int(round(num))
    if n <= 0:
        return 'RUPEES : ZERO ONLY'
    
    parts = []
    crore = n // 10000000
    rem_crore = n % 10000000
    
    if crore:
        parts.append(convert_below_crore(crore) + ' CRORE')
    if rem_crore:
        rem_str = convert_below_crore(rem_crore)
        if rem_str:
            parts.append(rem_str)
        
    return 'RUPEES : ' + ' '.join(parts) + ' ONLY'

