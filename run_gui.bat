@echo off
title Video Factory - Manim Studio
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Da xay ra loi khi khoi chay giao dien. Nhan phim bat ky de thoat...
    pause >nul
)
