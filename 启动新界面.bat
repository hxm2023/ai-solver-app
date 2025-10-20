@echo off
chcp 65001 > nul
echo ========================================
echo 沐梧AI学习系统 - 新界面启动脚本
echo ========================================
echo.

echo [1/3] 检查后端服务...
curl -s http://127.0.0.1:8000/ > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务已运行
) else (
    echo ⚠️ 后端服务未运行，正在启动...
    echo.
    echo 请在新窗口中运行以下命令：
    echo    cd backend
    echo    uvicorn main:app --reload
    echo.
    pause
)

echo.
echo [2/3] 检查前端依赖...
cd frontend\vite-project
if not exist "node_modules" (
    echo ⚠️ 前端依赖未安装，正在安装...
    call npm install
) else (
    echo ✅ 前端依赖已安装
)

echo.
echo [3/3] 启动前端服务...
echo.
echo ========================================
echo 🎉 前端服务即将启动
echo.
echo 访问地址：
echo   新界面：http://localhost:5173/
echo   原界面：http://localhost:5173/?mode=old
echo.
echo 快速登录：
echo   用户名：test_student
echo   密码：password123
echo ========================================
echo.

start http://localhost:5173/
call npm run dev

pause

