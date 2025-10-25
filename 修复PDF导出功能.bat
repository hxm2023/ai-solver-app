@echo off
chcp 65001 >nul
echo ========================================
echo   修复PDF导出功能 - Chromium安装
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python未找到，请先安装Python
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [2/3] 关闭可能的Chrome进程...
taskkill /F /IM chrome.exe /T 2>nul
taskkill /F /IM chromedriver.exe /T 2>nul
echo ✅ 进程已清理
echo.

echo [3/3] 以管理员权限重新安装Chromium...
echo 这可能需要2-5分钟，请耐心等待...
echo.

cd backend
python -c "import asyncio; from pyppeteer import launch; asyncio.get_event_loop().run_until_complete(launch())"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 修复成功！
    echo ========================================
    echo.
    echo 现在您可以：
    echo 1. 重启后端服务
    echo 2. 尝试导出PDF功能
    echo.
) else (
    echo.
    echo ========================================
    echo   ⚠️ 自动修复失败
    echo ========================================
    echo.
    echo 请尝试手动修复：
    echo 1. 右键点击此文件
    echo 2. 选择"以管理员身份运行"
    echo 3. 或联系技术支持
    echo.
)

pause

