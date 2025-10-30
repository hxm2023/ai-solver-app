@echo off
chcp 65001 >nul
color 0E
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║        🗄️ 沐梧AI - MySQL数据库依赖安装 V25.1               ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [INFO] 正在为虚拟环境安装MySQL数据库依赖...
echo.

cd /d "%~dp0backend"
call venv\Scripts\activate.bat

echo [1/2] 安装MySQL和认证相关依赖...
pip install pymysql==1.1.0 cryptography==41.0.7 pyjwt==2.8.0

if %errorlevel% equ 0 (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo   ✅ MySQL依赖安装成功！
    echo.
    echo   💡 接下来测试数据库连接：
    echo      python database.py
    echo ════════════════════════════════════════════════════════════════
) else (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo   ❌ 依赖安装失败！
    echo   请检查网络连接或查看错误信息。
    echo ════════════════════════════════════════════════════════════════
)

echo.
pause

