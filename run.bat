@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    call "%~dp0update.bat"
)
call .venv\Scripts\activate.bat
set "DEBUG_LOG_DIR=debug_logs"
echo 普通日志目录: %CD%\logs
echo debug 日志目录: %CD%\%DEBUG_LOG_DIR%
python src -l logs -d %DEBUG_LOG_DIR% -g info %*
exit /b %ERRORLEVEL%
