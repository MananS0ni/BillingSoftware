"""
app_paths.py - Centralized path resolution for dev mode and compiled PyInstaller .exe.
Ensures database, settings, templates, assets, and WhatsApp bridge are always
located relative to the executable / application directory.
"""

import os
import sys

def get_base_dir() -> str:
    """
    Returns the root directory where the application is installed.
    - When frozen (.exe via PyInstaller): directory containing the .exe
    - When running in Python dev mode: directory containing this source file
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# Critical data and configuration paths
DB_PATH = os.path.join(BASE_DIR, "jewelry_shop.db")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
INVOICE_TEMPLATE_PATH = os.path.join(BASE_DIR, "invoice_app.html")
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")
BRIDGE_DIR = os.path.join(BASE_DIR, "bridge")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
