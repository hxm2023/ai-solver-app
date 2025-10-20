@echo off
chcp 65001 > nul
echo ========================================
echo  沐梧AI后端服务 - 重启工具
echo ========================================
echo.
echo 【重要】所有依赖已安装完成！
echo 【重要】数据库已初始化完成！
echo 【重要】现在需要重启后端服务来加载新功能！
echo.
pause
echo.

echo [1/4] 正在关闭旧的后端进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 找到进程ID: %%a，正在终止...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo 完成！
echo.

echo [2/4] 检查端口是否释放...
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo 警告：端口8000仍被占用，请手动终止相关进程
    pause
)
echo 端口已释放！
echo.

echo [3/4] 正在切换到后端目录...
cd backend
if errorlevel 1 (
    echo 错误：无法进入backend目录
    pause
    exit /b 1
)
echo 完成！
echo.

echo [4/4] 正在启动新的后端服务...
echo 提示：新窗口将打开，请查看启动日志
echo 应该看到：【数据库初始化】[OK] 完成！
echo.
timeout /t 2 /nobreak >nul

start "沐梧AI-后端服务-V23.0" cmd /k "title 沐梧AI-后端服务-V23.0 && color 0A && echo ======================================== && echo  沐梧AI后端服务 V23.0 && echo ======================================== && echo. && echo [启动] 正在初始化... && echo. && python main.py"

cd ..
echo.
echo ========================================
echo  ✓ 后端服务正在启动中...
echo ========================================
echo.
echo 【下一步操作】
echo 1. 查看新打开的后端窗口
echo 2. 等待看到"Application startup complete"
echo 3. 确认看到"用户认证路由已加载"
echo 4. 访问 http://localhost:5173/?mode=new
echo 5. 尝试注册新用户
echo.
echo 【验证方式】
echo - API文档: http://127.0.0.1:8000/docs
echo - 应该能看到"用户认证"分组
echo.
echo ========================================
pause

