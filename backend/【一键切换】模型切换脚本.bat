@echo off
chcp 65001 >nul
echo ================================================================
echo 沐梧AI解题系统 - 5大模型一键切换工具
echo ================================================================
echo.

echo 当前可用的模型：
echo.
echo 1. qwen-vl-max               (阿里云闭源旗舰版)
echo 2. qwen3-vl-32b-thinking     (32B 思考链版本)
echo 3. qwen3-vl-32b-instruct     (32B 直接指令版本)
echo 4. qwen3-vl-235b-a22b-thinking  (235B 思考链版本)
echo 5. qwen3-vl-235b-a22b-instruct  (235B 直接指令版本)
echo.
echo 0. 查看当前激活的模型
echo 9. 测试当前模型连接
echo.

set /p choice=请选择要切换的模型 (输入数字): 

if "%choice%"=="1" set MODEL_KEY=qwen-vl-max
if "%choice%"=="2" set MODEL_KEY=qwen3-vl-32b-thinking
if "%choice%"=="3" set MODEL_KEY=qwen3-vl-32b-instruct
if "%choice%"=="4" set MODEL_KEY=qwen3-vl-235b-a22b-thinking
if "%choice%"=="5" set MODEL_KEY=qwen3-vl-235b-a22b-instruct

if "%choice%"=="0" (
    echo.
    echo [当前配置]
    python -c "import config_api_models as config; print(config.get_model_info())"
    echo.
    pause
    exit /b
)

if "%choice%"=="9" (
    echo.
    echo [测试当前模型]
    python test_5_models.py
    echo.
    pause
    exit /b
)

if not defined MODEL_KEY (
    echo.
    echo ❌ 无效的选择！
    pause
    exit /b
)

echo.
echo [正在切换模型到: %MODEL_KEY%]

:: 使用Python修改配置文件
python -c "import re; content = open('config_api_models.py', 'r', encoding='utf-8').read(); new_content = re.sub(r'ACTIVE_MODEL_KEY = \".*?\"', 'ACTIVE_MODEL_KEY = \"%MODEL_KEY%\"', content); open('config_api_models.py', 'w', encoding='utf-8').write(new_content); print('✅ 切换成功！')"

echo.
echo [新配置信息]
python -c "import config_api_models as config; print(config.get_model_info())"

echo.
echo ================================================================
echo 💡 提示：请重启后端服务以使配置生效
echo ================================================================
echo.

pause

