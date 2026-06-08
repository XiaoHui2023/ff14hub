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
pytest %*
