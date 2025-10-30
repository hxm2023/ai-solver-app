@echo off
chcp 65001 >nul
title 沐梧AI - 数据库版本系统启动

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║          沐梧AI解题系统 - 数据库版本 V25.2                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [1/3] 启动后端服务（FastAPI + MySQL）...
echo.

cd /d "%~dp0backend"

start "沐梧AI后端(数据库版)" cmd /k "venv\Scripts\activate && python main_db.py"

timeout /t 3 /nobreak >nul

echo.
echo [2/3] 启动前端服务（React + Vite）...
echo.

cd /d "%~dp0frontend\vite-project"

start "沐梧AI前端(数据库版)" cmd /k "npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║  ✅ 数据库版本系统已启动！                                    ║
echo ║                                                              ║
echo ║  📌 前端访问地址:                                            ║
echo ║     http://localhost:5173/?mode=db                           ║
echo ║                                                              ║
echo ║  📌 功能特点:                                                ║
echo ║     • 用户登录注册（账号密码）                               ║
echo ║     • MySQL数据库存储                                        ║
echo ║     • 错题自动保存到数据库                                   ║
echo ║     • 会话历史同步云端                                       ║
echo ║                                                              ║
echo ║  💡 首次使用:                                                ║
echo ║     1. 点击"注册"创建账号                                    ║
echo ║     2. 登录后选择功能模式                                    ║
echo ║     3. 开始使用！                                            ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 按任意键关闭本窗口（前后端将继续运行）...
pause >nul

exit
