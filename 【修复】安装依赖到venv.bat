@echo off
chcp 65001 >nul
echo ========================================
echo   V25.0 依赖安装到虚拟环境
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查虚拟环境...
if not exist "backend\venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在
    echo 请先运行: python -m venv backend\venv
    pause
    exit /b 1
)
echo ✅ 虚拟环境存在
echo.

echo [2/3] 激活虚拟环境...
call backend\venv\Scripts\activate.bat
echo ✅ 虚拟环境已激活
echo.

echo [3/3] 安装V25.0依赖...
echo 这可能需要2-3分钟，请耐心等待...
echo.

cd backend
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 依赖安装成功！
    echo ========================================
    echo.
    echo 已安装的V25.0新依赖：
    echo   - pyppeteer (PDF导出)
    echo   - markdown (Markdown转HTML)
    echo   - beautifulsoup4 (网页爬取)
    echo   - requests (HTTP请求)
    echo.
    echo 下一步：
    echo 1. 重启后端服务
    echo 2. 测试PDF导出功能
    echo.
) else (
    echo.
    echo ========================================
    echo   ❌ 安装失败
    echo ========================================
    echo.
    echo 请检查网络连接后重试
    echo.
)

pause
