@echo off
chcp 65001 >nul
color 0B
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              🎨 错题图片生成器 - 测试工具                   ║
echo ║                                                              ║
echo ║           为错题本系统生成测试用的错题图片样本               ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [INFO] 输出目录：D:\360安全浏览器下载\题目\错题样本
echo.
echo [INFO] 功能说明：
echo   • 可选择科目：数学、物理、化学、英语
echo   • 可选择难度：简单、中等、困难
echo   • 生成JPG格式的错题图片
echo   • 包含题目、错误答案、正确答案、详细分析
echo.
echo [INFO] 正在启动...
echo.

cd backend

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在！
    echo 请先运行主程序启动脚本创建虚拟环境。
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 运行图片生成器
python mistake_image_generator.py

echo.
echo.
echo ════════════════════════════════════════════════════════════════
echo   程序已结束
echo ════════════════════════════════════════════════════════════════
echo.

pause

