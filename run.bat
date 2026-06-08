@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    call "%~dp0update.bat"
)
call .venv\Scripts\activate.bat
python src\ensure_playwright.py
set "DEBUG_LOG_DIR=debug_logs"
echo logs: %CD%\logs
echo debug_logs: %CD%\%DEBUG_LOG_DIR%
python src -l logs -d %DEBUG_LOG_DIR% -g info %*
exit /b %ERRORLEVEL%
