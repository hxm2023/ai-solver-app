@echo off
echo ========================================
echo    AI解题系统 - 服务启动脚本
echo ========================================
echo.

echo [1/2] 启动后端服务...
start "后端服务" cmd /k "cd backend && python -m uvicorn main:app --reload"
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
start "前端服务" cmd /k "cd frontend\vite-project && npm run dev"

echo.
echo ========================================
echo    服务启动完成！
echo ========================================
echo.
echo 后端服务: http://127.0.0.1:8000
echo 前端服务: 将在几秒后自动显示地址
echo.
echo 【重要】请在新打开的两个命令窗口中查看日志！
echo.
echo 按任意键关闭此窗口...
pause >nul

