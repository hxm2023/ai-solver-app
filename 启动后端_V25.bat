@echo off
chcp 65001 >nul
color 0A
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║           🚀 沐梧AI后端服务 V25.0                            ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [INFO] 正在启动后端服务...
echo.

cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python -m uvicorn main_simple:app --reload --host 127.0.0.1 --port 8000

pause

