@echo off
chcp 65001 >nul
echo ================================================================
echo 沐梧AI解题系统 - 数据库升级到V25.2
echo ================================================================
echo.
echo 【重要提示】
echo 1. 升级前请确保已备份数据库
echo 2. 本脚本将添加新表和字段，不会删除现有数据
echo 3. 如果字段已存在会报错，但可以忽略
echo.
echo ================================================================
echo.

set /p confirm=是否继续执行升级？(Y/N): 
if /i not "%confirm%"=="Y" (
    echo 取消升级
    pause
    exit
)

echo.
echo [1/3] 正在连接数据库...
echo.

rem 检查MySQL命令是否可用
mysql --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到mysql命令
    echo.
    echo 请安装MySQL客户端或将MySQL的bin目录添加到系统PATH环境变量
    echo 例如：C:\Program Files\MySQL\MySQL Server 8.0\bin
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] 执行升级脚本...
echo.
echo 数据库信息：
echo - 主机：14.103.127.20
echo - 端口：3306
echo - 数据库：edu
echo - 用户：root
echo.

rem 执行升级脚本
mysql -h 14.103.127.20 -P 3306 -u root -p edu < backend\database_schema_v25.2.sql

if errorlevel 1 (
    echo.
    echo ⚠️  执行过程中出现错误
    echo.
    echo 常见错误说明：
    echo - Error 1060: Duplicate column name - 字段已存在（可忽略）
    echo - Error 1061: Duplicate key name - 索引已存在（可忽略）
    echo - Error 1050: Table already exists - 表已存在（可忽略）
    echo.
    echo 如果是上述错误，升级可能已经完成，请验证表结构
    echo 如果是其他错误，请检查错误信息
    echo.
) else (
    echo.
    echo ✅ 升级脚本执行完成
    echo.
)

echo.
echo [3/3] 验证升级结果...
echo.

rem 创建临时验证脚本
echo SELECT 'Chat Session Table' AS Check_Item, COUNT(*) AS Count FROM information_schema.tables WHERE table_schema='edu' AND table_name='chat_session'; > temp_verify.sql
echo SELECT 'Chat History Table' AS Check_Item, COUNT(*) AS Count FROM information_schema.tables WHERE table_schema='edu' AND table_name='chat_history'; >> temp_verify.sql
echo SELECT 'Knowledge Tag Table' AS Check_Item, COUNT(*) AS Count FROM information_schema.tables WHERE table_schema='edu' AND table_name='knowledge_tag'; >> temp_verify.sql

mysql -h 14.103.127.20 -P 3306 -u root -p edu < temp_verify.sql

del temp_verify.sql

echo.
echo ================================================================
echo 升级完成！
echo ================================================================
echo.
echo 【验证步骤】
echo 1. 登录MySQL客户端或Navicat
echo 2. 连接到edu数据库
echo 3. 执行以下SQL验证新表：
echo    SHOW TABLES LIKE 'chat%%';
echo    DESC chat_session;
echo    DESC chat_history;
echo.
echo 【下一步】
echo 1. 重启后端服务：【启动】数据库版本系统.bat
echo 2. 查看新功能文档：【完成】V25.2新功能开发报告.md
echo 3. 测试新API：使用Postman或前端调用
echo.
echo ================================================================
pause

