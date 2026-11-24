@echo off
title Soni Natvarlal Himmatlal - Reset Test Data
echo ============================================================
echo   Soni Natvarlal Himmatlal - Database Reset Tool
echo ============================================================
echo.
echo WARNING: This will delete all test bills, customers, and ledger
echo entries, resetting everything back to a completely clean state
echo (Bill No. will restart at #1).
echo.
set /p confirm="Are you sure you want to clear all test data? (Type Y and press Enter): "
if /i "%confirm%" neq "Y" (
    echo.
    echo Reset cancelled. No data was changed.
    echo.
    pause
    exit /b
)

echo.
if exist "jewelry_shop.db" (
    del /f /q "jewelry_shop.db"
    echo [OK] Removed jewelry_shop.db
) else (
    echo [INFO] jewelry_shop.db does not exist yet.
)

if exist "invoices\*.pdf" (
    del /f /q "invoices\*.pdf"
    echo [OK] Cleaned up test invoice PDFs from invoices folder.
)

echo.
echo ============================================================
echo [SUCCESS] Database and test bills have been completely reset!
echo When you next open JewelryBilling.exe, a fresh clean database
echo will be automatically created.
echo ============================================================
echo.
pause
