@echo off
:: Увери се, че си в папката със main.py

:: Изтрий предишни билдове (по избор)
rmdir /s /q build
rmdir /s /q dist
del main.spec

:: Компилирай
pyinstaller --noconfirm --clean ^
 --onefile ^
 --windowed ^
 --add-data "Screen01.ui;." ^
 --hidden-import=PyQt5.sip ^
 main.py

pause
