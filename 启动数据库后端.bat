@echo off
chcp 65001 >nul
echo.
echo ════════════════════════════════════════════════════════════════
echo   启动数据库版后端服务 (端口 8000)
echo ════════════════════════════════════════════════════════════════
echo.

cd backend
call venv\Scripts\activate.bat
python -m uvicorn main_db:app --reload --host 127.0.0.1 --port 8000

pause

