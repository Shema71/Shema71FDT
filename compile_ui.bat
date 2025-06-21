@echo off
REM === Проверка дали pyuic5 е налична ===
where pyuic5 >nul 2>nul
if errorlevel 1 (
    echo [Грешка] pyuic5 не е намерена в PATH.
    echo Моля, инсталирайте PyQt5 и се уверете, че pyuic5 е в PATH.
    pause
    exit /b
)

REM === Компилиране на UI файла ===
echo Компилиране на Screen01.ui до Screen01_ui.py...
pyuic5 -x Screen01.ui -o Screen01_ui.py

IF EXIST Screen01_ui.py (
    echo Успешно компилирано: Screen01_ui.py
) ELSE (
    echo [Грешка] Неуспешно компилиране.
)

pause
