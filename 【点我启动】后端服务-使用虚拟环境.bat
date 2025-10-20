@echo off
chcp 65001 > nul
title 沐梧AI后端服务（虚拟环境）
color 0A
echo.
echo ========================================
echo   沐梧AI后端服务 V23.0
echo   使用虚拟环境：backend\venv
echo ========================================
echo.
echo [启动] 正在进入后端目录...
cd /d "%~dp0backend"
if errorlevel 1 (
    echo 错误：无法进入backend目录
    pause
    exit /b 1
)
echo [启动] 当前目录：
cd
echo.

echo [启动] 正在激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误：无法激活虚拟环境
    pause
    exit /b 1
)
echo [启动] 虚拟环境已激活
echo.

echo [启动] 正在启动后端服务...
echo [启动] 请注意观察启动日志！
echo.
echo ======================================== 
echo          关键标志：
echo ======================================== 
echo ✅ 应该看到：数据库和认证模块导入成功
echo ✅ 应该看到：用户认证路由已加载
echo ❌ 不应该看到：No module named 'sqlalchemy'
echo ========================================
echo.

python -m uvicorn main:app --reload

echo.
echo [结束] 后端服务已停止
pause



