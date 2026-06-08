@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [ff14hub] 未找到 .venv，请先安装依赖：
    echo   update.bat
    echo.
    exit /b 1
)
call .venv\Scripts\activate.bat
python src\ensure_playwright.py
if errorlevel 1 exit /b 1
set "DEBUG_LOG_DIR=debug_logs"
echo logs: %CD%\logs
echo debug_logs: %CD%\%DEBUG_LOG_DIR%
python src -l logs -d %DEBUG_LOG_DIR% -g info %*
exit /b %ERRORLEVEL%
