@echo off
chcp 65001 > nul
echo ========================================
echo  Installing dependencies to venv
echo ========================================
echo.

cd /d "%~dp0backend\venv\Scripts"
if errorlevel 1 (
    echo ERROR: Cannot enter venv directory
    pause
    exit /b 1
)

echo Current directory:
cd
echo.

echo Installing packages...
echo.

pip.exe install sqlalchemy passlib[bcrypt] python-jose[cryptography] python-multipart reportlab python-docx

echo.
echo ========================================
echo  Installation complete!
echo ========================================
echo.
pause

