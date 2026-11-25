@echo off
title Installer Koding Penggalang (Windows)
cd /d "%~dp0"
echo ================================================================
echo   MEMULAI INSTALLER KODING PENGGALANG (WINDOWS 10 / 11)
echo ================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1" %*
echo.
pause
