@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_spiritvale_bot.ps1" %*
echo.
pause

