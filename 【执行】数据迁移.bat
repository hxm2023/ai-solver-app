@echo off
chcp 65001 >nul
color 0C
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║        🔄 沐梧AI - JSON数据迁移到MySQL V25.1                ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [警告] 此操作将会：
echo   1. 创建默认测试用户 (demo_user)
echo   2. 将JSON文件中的错题和题目迁移到MySQL数据库
echo   3. 创建错题本和练习题集试卷
echo.
echo 请确认已完成以下准备工作：
echo   ✓ MySQL依赖已安装
echo   ✓ 数据库表结构已扩展
echo   ✓ 数据库连接测试通过
echo.
pause
echo.
echo [INFO] 正在执行数据迁移...
echo.

cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python migrate_data.py

echo.
echo ════════════════════════════════════════════════════════════════
echo   迁移完成！请查看上方统计信息
echo ════════════════════════════════════════════════════════════════
echo.
pause

