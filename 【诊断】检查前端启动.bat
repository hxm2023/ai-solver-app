@echo off
chcp 65001 >nul
title 前端诊断工具

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║                    前端诊断工具                              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/4] 检查 Node.js 是否安装...
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装或未配置到 PATH
    echo 请从 https://nodejs.org/ 下载安装 Node.js
    pause
    exit /b
)
echo ✅ Node.js 已安装
echo.

echo [2/4] 检查前端目录...
cd /d "%~dp0frontend\vite-project"
if %errorlevel% neq 0 (
    echo ❌ 前端目录不存在
    pause
    exit /b
)
echo ✅ 前端目录存在
echo.

echo [3/4] 检查依赖安装...
if not exist "node_modules" (
    echo ⚠️ node_modules 不存在，正在安装依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b
    )
) else (
    echo ✅ 依赖已安装
)
echo.

echo [4/4] 启动前端开发服务器...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║  前端即将启动，请等待看到：                                  ║
echo ║  "VITE v5.x.x  ready in xxx ms"                              ║
echo ║                                                              ║
echo ║  如果长时间卡住或报错，请按 Ctrl+C 停止，                    ║
echo ║  然后将错误信息截图反馈。                                    ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

call npm run dev

pause

