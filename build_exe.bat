@echo off
echo ===================================================
echo   BUILDING STANDALONE WINDOWS APP (.EXE)
echo   Jewelry Billing & Ledger Software
echo ===================================================

echo [1/3] Installing PyInstaller if needed...
pip install pyinstaller

echo [2/3] Bundling software into a single folder for Shop Laptop...
pyinstaller --noconsole --name="JewelryBilling" --onedir --clean ^
    --add-data "translations.py;." ^
    --add-data "theme.py;." ^
    main.py

echo.
echo ===================================================
echo   BUILD FINISHED!
echo   Go to folder: dist\JewelryBilling\
echo   Copy that entire "JewelryBilling" folder onto your
echo   Pen Drive and take it to your shop laptop!
echo ===================================================
pause

