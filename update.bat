@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -U -e ".[dev]"
python src\ensure_playwright.py
