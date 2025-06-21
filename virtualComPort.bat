@echo off
rem Създаване на виртуална COM двойка COM8 и COM9
cd "C:\Program Files (x86)\com0com"
setupc.exe install PortName=COM8 PortName=COM9

rem Проверка дали са създадени
setupc.exe list
pause




