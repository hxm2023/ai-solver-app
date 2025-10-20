@echo off
chcp 65001 >nul
echo ========================================
echo   沐梧AI - 轻量级错题本系统 V24.0
echo   无需数据库 - 开箱即用
echo ========================================
echo.

cd backend

echo [启动] 正在激活虚拟环境...
call venv\Scripts\activate.bat

echo [启动] 正在启动简化版后端...
echo.
echo ========================================
echo   访问地址：http://127.0.0.1:8000
echo   API文档：http://127.0.0.1:8000/docs
echo ========================================
echo.

python -m uvicorn main_simple:app --reload --host 127.0.0.1 --port 8000

pause

