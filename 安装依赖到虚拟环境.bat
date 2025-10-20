@echo off
chcp 65001 > nul
echo ========================================
echo  安装依赖到虚拟环境
echo ========================================
echo.

cd /d "%~dp0backend\venv\Scripts"
if errorlevel 1 (
    echo 错误：无法进入虚拟环境目录
    pause
    exit /b 1
)

echo 当前目录：
cd
echo.

echo 正在安装依赖包...
echo.

pip.exe install sqlalchemy passlib[bcrypt] python-jose[cryptography] python-multipart reportlab python-docx

echo.
echo ========================================
echo  安装完成！
echo ========================================
echo.
echo 请检查上方是否有"Successfully installed"字样
echo.
pause

