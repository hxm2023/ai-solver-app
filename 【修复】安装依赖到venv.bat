@echo off
chcp 65001 > nul
title 安装依赖到虚拟环境
echo.
echo ========================================
echo   安装Python依赖到虚拟环境
echo ========================================
echo.

echo [步骤1] 进入后端目录...
cd /d "%~dp0backend"
if errorlevel 1 (
    echo 错误：无法进入backend目录
    pause
    exit /b 1
)
echo 当前目录：%CD%
echo.

echo [步骤2] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误：无法激活虚拟环境
    pause
    exit /b 1
)
echo 虚拟环境已激活
echo.

echo [步骤3] 检查Python路径...
python -c "import sys; print('Python路径:', sys.executable)"
echo.

echo [步骤4] 安装依赖包（这可能需要1-2分钟）...
echo.
echo 正在安装 sqlalchemy...
pip install sqlalchemy
echo.
echo 正在安装 passlib...
pip install "passlib[bcrypt]"
echo.
echo 正在安装 python-jose...
pip install "python-jose[cryptography]"
echo.
echo 正在安装 python-multipart...
pip install python-multipart
echo.
echo 正在安装 reportlab...
pip install reportlab
echo.
echo 正在安装 python-docx...
pip install python-docx
echo.

echo [步骤5] 验证安装...
echo.
echo 已安装的包：
pip list | findstr /i "sqlalchemy passlib jose multipart reportlab docx"
echo.

echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 请检查上方是否显示了以下包：
echo   - sqlalchemy
echo   - passlib
echo   - python-jose
echo   - python-multipart
echo   - reportlab
echo   - python-docx
echo.
echo 如果都显示了，说明安装成功！
echo 请关闭后端服务窗口，然后重新启动。
echo.
pause

