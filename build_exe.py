"""
build_exe.py - Automated PyInstaller Executable Builder for Jewelry Billing & Ledger.
Builds a standalone, production-ready desktop package for Windows.
Includes all UI templates, fonts, assets, and the WhatsApp Node.js bridge.
"""

import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
APP_NAME = "JewelryBilling"
OUTPUT_DIR = os.path.join(DIST_DIR, APP_NAME)

def clean_previous():
    """Removes previous build artifacts to ensure a pristine build."""
    print("🧹 Cleaning previous build folders...")
    for folder in [BUILD_DIR, OUTPUT_DIR]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"   Removed: {folder}")
            except Exception as e:
                print(f"   Warning: Could not remove {folder}: {e}")

def run_pyinstaller():
    """Runs PyInstaller to compile main.py and all dependencies into a standalone onedir bundle."""
    print("🔨 Running PyInstaller compilation...")
    icon_path = os.path.join(BASE_DIR, "assets", "app_icon.ico")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        f"--icon={icon_path}" if os.path.exists(icon_path) else "",
        "--hidden-import=PySide6.QtPdf",
        "--hidden-import=PySide6.QtPrintSupport",
        "--hidden-import=sqlite3",
        "--hidden-import=urllib.request",
        "--hidden-import=urllib.error",
        os.path.join(BASE_DIR, "main.py")
    ]
    # Filter out empty arguments
    cmd = [arg for arg in cmd if arg]

    print("Command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"❌ PyInstaller failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print("✅ PyInstaller compilation finished successfully!")

def copy_runtime_assets():
    """Copies required templates, assets, settings, and WhatsApp bridge to the distribution bundle."""
    print("📦 Bundling runtime assets into dist package...")

    # 1. invoice_app.html template
    html_src = os.path.join(BASE_DIR, "invoice_app.html")
    if os.path.exists(html_src):
        shutil.copy2(html_src, OUTPUT_DIR)
        print("   Copied: invoice_app.html")

    # 2. Assets directory (logos, icons)
    assets_src = os.path.join(BASE_DIR, "assets")
    assets_dst = os.path.join(OUTPUT_DIR, "assets")
    if os.path.exists(assets_src):
        if os.path.exists(assets_dst):
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        print("   Copied: assets/")

    # 3. Settings template (ensure a clean settings.json exists)
    settings_src = os.path.join(BASE_DIR, "settings.json")
    settings_dst = os.path.join(OUTPUT_DIR, "settings.json")
    if os.path.exists(settings_src):
        shutil.copy2(settings_src, settings_dst)
        print("   Copied: settings.json")

    # 4. WhatsApp Node.js Bridge (exclude auth_info session so each laptop links freshly)
    bridge_src = os.path.join(BASE_DIR, "bridge")
    bridge_dst = os.path.join(OUTPUT_DIR, "bridge")
    if os.path.exists(bridge_src):
        if os.path.exists(bridge_dst):
            shutil.rmtree(bridge_dst)
        
        def _ignore_auth(dir, contents):
            # Do NOT bundle active session or git files
            ignored = []
            if "auth_info" in contents:
                ignored.append("auth_info")
            if ".git" in contents:
                ignored.append(".git")
            return ignored

        shutil.copytree(bridge_src, bridge_dst, ignore=_ignore_auth)
        # Ensure an empty auth_info directory exists
        os.makedirs(os.path.join(bridge_dst, "auth_info"), exist_ok=True)
        print("   Copied: bridge/ (fresh session initialized)")

    # 5. Invoices folder
    invoices_dst = os.path.join(OUTPUT_DIR, "invoices")
    os.makedirs(invoices_dst, exist_ok=True)
    print("   Created: invoices/ folder")

    # 6. Database Reset Helper Script
    reset_src = os.path.join(BASE_DIR, "Reset_Database.bat")
    if os.path.exists(reset_src):
        shutil.copy2(reset_src, OUTPUT_DIR)
        print("   Copied: Reset_Database.bat")

def main():
    print("=" * 60)
    print(f"   Building {APP_NAME} Standalone Desktop Package")
    print("=" * 60)
    
    clean_previous()
    run_pyinstaller()
    copy_runtime_assets()

    print("\n" + "=" * 60)
    print("🎉 BUILD COMPLETE!")
    print(f"📁 Distribution folder: {OUTPUT_DIR}")
    print(f"🚀 Main Executable:     {os.path.join(OUTPUT_DIR, f'{APP_NAME}.exe')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
