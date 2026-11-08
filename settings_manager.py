"""
settings_manager.py - Persistent shop settings.
Stores Owner / Father's WhatsApp number and shop configuration in settings.json.
"""

import os
import json

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_SETTINGS = {
    "owner_phone": "9313268100",
    "owner_phone_display": "98251 62065",
    "send_owner_copy": True,
    "shop_name_gu": "સોની નટવરલાલ હિંમતલાલ",
    "shop_name_en": "Soni Natvarlal Himmatlal",
    "proprietor": "સોની બ્રિજેશ નટવરલાલ",
    "tagline": "સોના-ચાંદીના દાગીના બનાવનાર તથા વેચનાર.",
    "address": "જૈન દેરાસર પાસે, બાવળા-૩૮૨૨૨૦. જી. અમદાવાદ.",
    "gstin": "24BPXPS8279A1Z7",
    "header_left": "વાયુ આદિતી",
    "header_center": "॥ શ્રી હરિ ॥",
    "header_right": "બ્રિજેશભાઈ ૯૮૨૫૧ ૬૨૦૬૫",
}

def load_settings() -> dict:
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = DEFAULT_SETTINGS.copy()
                res.update(data)
                return res
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(data: dict) -> bool:
    try:
        curr = load_settings()
        curr.update(data)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(curr, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Settings] Error saving settings: {e}")
        return False

def get_owner_phone() -> str:
    return load_settings().get("owner_phone", "").strip()

def is_owner_copy_enabled() -> bool:
    s = load_settings()
    return bool(s.get("send_owner_copy", True) and s.get("owner_phone", "").strip())

