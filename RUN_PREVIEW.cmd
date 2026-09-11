@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_spiritvale_bot.ps1" -Preview
echo.
pause

