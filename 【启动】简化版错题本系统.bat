@echo off
chcp 65001 >nul
color 0A
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║           🎓 沐梧AI - 轻量级智能错题本系统 V24.0            ║
echo ║                                                              ║
echo ║              ✨ 无需登录 · 开箱即用 · AI助学 ✨              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [INFO] 正在启动服务...
echo.

REM 启动后端服务
echo [1/2] 启动后端服务...
cd backend
start "沐梧AI后端" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn main_simple:app --reload --host 127.0.0.1 --port 8000"
cd ..

REM 等待2秒让后端先启动
timeout /t 2 /nobreak >nul

REM 启动前端服务
echo [2/2] 启动前端服务...
cd frontend\vite-project
start "沐梧AI前端" cmd /k "npm run dev"
cd ..\..

echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo   ✅ 服务启动完成！
echo.
echo   📱 访问地址：
echo      前端界面：http://localhost:5173/
echo      API文档： http://127.0.0.1:8000/docs
echo.
echo   📚 功能说明：
echo      • 智能错题本 - 保存和管理错题
echo      • AI智能出题 - 基于错题生成练习
echo      • 试卷导出   - Markdown格式下载
echo.
echo   ⚙️  模式切换：
echo      简化版（默认）: http://localhost:5173/
echo      原解题界面:    http://localhost:5173/?mode=old
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo   💡 提示：关闭此窗口不会停止服务
echo           需要手动关闭后端和前端窗口
echo.

pause

