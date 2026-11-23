"""
rates_manager.py - Real-Time Live Bullion (Gold & Silver) Pricing Engine.
100% Free, Zero-Subscription, Highly Resilient Background Thread Engine.

Features:
1. Multi-source financial feed (Yahoo Finance chart API + Currency API CDN fallback).
2. Computes all jewellery product tiers:
   - 24K Pure Gold Lagdi (99.9%)
   - 22K Hallmark Gold Ornaments (91.6% Touch / 916)
   - 18K Gold Jewellery (75.0% Touch / 750)
   - Silver Lagdi / Chorsa (99.9% Fine Silver)
   - Silver Ornaments (92.5% Sterling / Payal, Kada, Chains)
   - Silver Utensils & Articles (85.0% Pooja Vasan, Thali, Kalash)
   - Gold & Silver Coins
3. Real-time price movement tracking (Green ▲ Up / Red ▼ Down).
4. Persistent SQLite caching for 100% offline continuity.
"""

import urllib.request
import json
import time
from datetime import datetime
from typing import Dict, Optional

from PySide6.QtCore import QThread, Signal, QObject

from database import save_cached_rates, get_cached_rates

# Standard Indian Bullion Pricing Constants
TROY_OUNCE_TO_GRAMS = 31.1034768
TOUCH_22K = 0.9167
TOUCH_18K = 0.7500
TOUCH_14K = 0.5850
TOUCH_SILVER_ORNAMENTS = 0.9250
TOUCH_SILVER_UTENSILS = 0.8500

DEFAULT_FALLBACK_RATES = {
    "status": "OFFLINE",
    "timestamp": datetime.now().strftime("%H:%M:%S"),
    "gold_24k_1g": 7650.00,
    "gold_24k_10g": 76500.00,
    "gold_22k_1g": 7013.00,
    "gold_22k_10g": 70130.00,
    "gold_18k_1g": 5738.00,
    "gold_14k_1g": 4475.00,
    "silver_lagdi_1g": 92.00,
    "silver_lagdi_1kg": 92000.00,
    "silver_ornaments_1g": 85.10,
    "silver_utensils_1g": 78.20,
    "gold_coin_1g": 7650.00,
    "silver_coin_1g": 92.00,
    "gold_change": 0.0,
    "silver_change": 0.0,
    "gold_direction": "equal",
    "silver_direction": "equal",
}

class LiveRatesWorker(QThread):
    """Background worker thread that pings market feeds without blocking the UI."""
    rates_updated = Signal(dict)

    def __init__(self, parent=None, poll_interval_sec=2):
        super().__init__(parent)
        self.poll_interval_sec = poll_interval_sec
        self.running = True
        self.last_gold_24k = 0.0
        self.last_silver = 0.0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

    def run(self):
        # 1. First broadcast cached rates immediately for instant UI load
        cached = get_cached_rates()
        if cached:
            cached["status"] = "CACHED"
            self.rates_updated.emit(cached)

        while self.running:
            rates = self.fetch_live_rates()
            if rates:
                self.rates_updated.emit(rates)
                try:
                    save_cached_rates(rates)
                except Exception:
                    pass

            # Sleep in small slices so thread stops cleanly when app closes
            for _ in range(self.poll_interval_sec * 5):
                if not self.running:
                    break
                time.sleep(0.2)

    def stop(self):
        self.running = False
        self.wait(1500)

    def fetch_live_rates(self) -> Optional[Dict]:
        """Fetches from free multi-source feeds with resilient fallback."""
        # Method A: Free Yahoo Finance Chart v8 (Live tick-by-tick)
        try:
            # Gold USD
            u_gold = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d"
            req_g = urllib.request.Request(u_gold, headers=self.headers)
            with urllib.request.urlopen(req_g, timeout=4) as r:
                d_g = json.loads(r.read().decode('utf-8'))
                gold_usd = d_g["chart"]["result"][0]["meta"]["regularMarketPrice"]
                prev_g = d_g["chart"]["result"][0]["meta"]["chartPreviousClose"]
                gold_chg_raw = round(gold_usd - prev_g, 2)

            # USD / INR
            u_inr = "https://query1.finance.yahoo.com/v8/finance/chart/INR=X?interval=1m&range=1d"
            req_i = urllib.request.Request(u_inr, headers=self.headers)
            with urllib.request.urlopen(req_i, timeout=4) as r:
                d_i = json.loads(r.read().decode('utf-8'))
                usd_inr = d_i["chart"]["result"][0]["meta"]["regularMarketPrice"]

            # Silver USD
            u_sil = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1m&range=1d"
            req_s = urllib.request.Request(u_sil, headers=self.headers)
            with urllib.request.urlopen(req_s, timeout=4) as r:
                d_s = json.loads(r.read().decode('utf-8'))
                sil_usd = d_s["chart"]["result"][0]["meta"]["regularMarketPrice"]
                prev_s = d_s["chart"]["result"][0]["meta"]["chartPreviousClose"]
                sil_chg_raw = round(sil_usd - prev_s, 2)

            # Standard Indian market parity calculation
            raw_g24 = (gold_usd * usd_inr) / TROY_OUNCE_TO_GRAMS
            raw_sil = (sil_usd * usd_inr) / TROY_OUNCE_TO_GRAMS

            return self._build_rates_payload(raw_g24, raw_sil, gold_chg_raw, sil_chg_raw, source="YAHOO_LIVE")

        except Exception:
            pass

        # Method B: Global CDN Currency API fallback
        try:
            u_xau = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xau.json"
            req_xau = urllib.request.Request(u_xau, headers=self.headers)
            with urllib.request.urlopen(req_xau, timeout=4) as r:
                d_xau = json.loads(r.read().decode('utf-8'))
                inr_oz = d_xau["xau"]["inr"]
                raw_g24 = inr_oz / TROY_OUNCE_TO_GRAMS

            u_xag = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xag.json"
            req_xag = urllib.request.Request(u_xag, headers=self.headers)
            with urllib.request.urlopen(req_xag, timeout=4) as r:
                d_xag = json.loads(r.read().decode('utf-8'))
                inr_sil_oz = d_xag["xag"]["inr"]
                raw_sil = inr_sil_oz / TROY_OUNCE_TO_GRAMS

            return self._build_rates_payload(raw_g24, raw_sil, 0.0, 0.0, source="CDN_LIVE")

        except Exception:
            pass

        # Method C: Database Cache fallback
        cached = get_cached_rates()
        if cached:
            cached["status"] = "OFFLINE"
            return cached

        # Method D: Hardcoded safe default fallback
        return DEFAULT_FALLBACK_RATES

    def _build_rates_payload(self, g24_1g: float, sil_1g: float, g_chg: float, s_chg: float, source: str) -> Dict:
        g24 = round(g24_1g, 2)
        sil = round(sil_1g, 2)

        # Direction tracking
        if self.last_gold_24k > 0:
            if g24 > self.last_gold_24k:
                g_dir = "up"
            elif g24 < self.last_gold_24k:
                g_dir = "down"
            else:
                g_dir = "equal"
        else:
            g_dir = "up" if g_chg > 0 else ("down" if g_chg < 0 else "equal")

        if self.last_silver > 0:
            if sil > self.last_silver:
                s_dir = "up"
            elif sil < self.last_silver:
                s_dir = "down"
            else:
                s_dir = "equal"
        else:
            s_dir = "up" if s_chg > 0 else ("down" if s_chg < 0 else "equal")

        self.last_gold_24k = g24
        self.last_silver = sil

        # Derived Karat & Product calculations
        g22 = round(g24 * TOUCH_22K, 2)
        g18 = round(g24 * TOUCH_18K, 2)
        g14 = round(g24 * TOUCH_14K, 2)
        sil_orn = round(sil * TOUCH_SILVER_ORNAMENTS, 2)
        sil_utn = round(sil * TOUCH_SILVER_UTENSILS, 2)

        return {
            "status": "LIVE",
            "source": source,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "gold_24k_1g": g24,
            "gold_24k_10g": round(g24 * 10, 2),
            "gold_22k_1g": g22,
            "gold_22k_10g": round(g22 * 10, 2),
            "gold_18k_1g": g18,
            "gold_14k_1g": g14,
            "silver_lagdi_1g": sil,
            "silver_lagdi_1kg": round(sil * 1000, 2),
            "silver_ornaments_1g": sil_orn,
            "silver_utensils_1g": sil_utn,
            "gold_coin_1g": g24,
            "silver_coin_1g": sil,
            "gold_change": g_chg,
            "silver_change": s_chg,
            "gold_direction": g_dir,
            "silver_direction": s_dir,
        }

# Global Singleton Manager
class RatesManager(QObject):
    rates_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.latest_rates = get_cached_rates() or DEFAULT_FALLBACK_RATES
        self.worker = LiveRatesWorker()
        self.worker.rates_updated.connect(self._on_worker_update)

    def start(self):
        if not self.worker.isRunning():
            self.worker.start()

    def stop(self):
        if self.worker.isRunning():
            self.worker.stop()

    def _on_worker_update(self, rates: dict):
        self.latest_rates = rates
        self.rates_changed.emit(rates)

    def get_latest_rates(self) -> dict:
        return self.latest_rates

    def get_rate_by_item(self, description: str, hsn_code: str = "") -> float:
        """
        Intelligently matches the entered product description or HSN code
        to the exact corresponding live product rate per gram.
        """
        desc = (description or "").lower()
        hsn = (hsn_code or "").strip()
        r = self.latest_rates

        # 1. Silver checks
        if any(w in desc for w in ["silver", "ચાંદી", "chandi", "payal", "પાયલ", "કડા", "kada", "સાંકળા", "sankla", "લકી"]):
            if any(w in desc for w in ["lagdi", "લગડી", "chorsa", "ચોરસા", "silli", "પાટ", "pure"]) or hsn == "7106":
                return r.get("silver_lagdi_1g", 92.0)
            elif any(w in desc for w in ["vasan", "વાસણ", "pooja", "પૂજા", "thali", "થાળી", "loti", "diya"]) or hsn == "7114":
                return r.get("silver_utensils_1g", 78.2)
            else:
                return r.get("silver_ornaments_1g", 85.1)

        # 2. Gold 24K Lagdi / Bullion check
        if any(w in desc for w in ["24k", "24 k", "૨૪k", "lagdi", "લગડી", "bullion", "biscuit", "બિસ્કિટ"]) or hsn == "7108":
            return r.get("gold_24k_1g", 7650.0)

        # 3. Gold 18K check
        if any(w in desc for w in ["18k", "18 k", "૧૮k", "diamond"]):
            return r.get("gold_18k_1g", 5738.0)

        # 4. Default: Standard 22K (916) Hallmark Gold Jewellery (HSN 7113)
        return r.get("gold_22k_1g", 7013.0)

# Global Instance
_rates_manager_instance: Optional[RatesManager] = None

def get_rates_manager() -> RatesManager:
    global _rates_manager_instance
    if _rates_manager_instance is None:
        _rates_manager_instance = RatesManager()
    return _rates_manager_instance
