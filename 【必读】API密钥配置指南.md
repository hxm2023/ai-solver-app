# 🔑 API密钥配置指南

## 问题说明

如果您看到错误信息：
```
No api key provided. You can set by dashscope.api_key = your_api_key in code...
```

这说明后端缺少通义千问的API密钥配置。

---

## 🚀 快速解决方案

### 方法1：使用环境变量（推荐）

#### 步骤1：获取API密钥

1. 访问阿里云通义千问：https://dashscope.console.aliyun.com/
2. 注册/登录账号
3. 进入"API-KEY管理"
4. 创建并复制API Key（格式：sk-xxxxxxxxxx）

#### 步骤2：配置密钥

**创建或编辑 `backend/.env` 文件**：

```env
# 阿里云通义千问API密钥
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx

# 替换上面的 sk-xxxxxxxxxx 为您的实际密钥
```

**注意**：
- ⚠️ `.env` 文件在 `backend` 目录下
- ⚠️ 如果文件不存在，请创建它
- ⚠️ 不要提交 `.env` 文件到Git（已在 `.gitignore` 中）

#### 步骤3：重启后端服务

关闭后端窗口，重新运行：
```batch
【启动】数据库版本系统.bat
```

或手动启动：
```bash
cd backend
venv\Scripts\activate.bat
python -m uvicorn main_db:app --reload --host 127.0.0.1 --port 8000
```

---

### 方法2：直接在代码中配置（临时方案，不推荐）

#### 修改 `backend/main_db.py`

找到文件开头的导入部分，在 `load_dotenv()` 之后添加：

```python
load_dotenv()

# 临时配置API密钥（仅用于测试，不要提交到Git）
import os
if not os.getenv('DASHSCOPE_API_KEY'):
    dashscope.api_key = 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxx'  # 替换为您的密钥
```

**警告**：
- ⚠️ 这种方法会将密钥硬编码到代码中
- ⚠️ 存在泄露风险
- ⚠️ 不适合生产环境
- ⚠️ 仅用于快速测试

---

## 🔍 验证配置

### 检查.env文件

打开 `backend/.env`，确认内容如下：

```env
DASHSCOPE_API_KEY=sk-your-actual-key-here
```

### 测试API密钥

创建测试脚本 `backend/test_api_key.py`：

```python
import os
from dotenv import load_dotenv
import dashscope

load_dotenv()

api_key = os.getenv('DASHSCOPE_API_KEY')

if api_key:
    print(f"✅ API密钥已配置: {api_key[:10]}...")
    
    # 测试API调用
    dashscope.api_key = api_key
    try:
        response = dashscope.Generation.call(
            model='qwen-turbo',
            prompt='你好'
        )
        if response.status_code == 200:
            print("✅ API调用成功！")
            print(f"响应: {response.output.text}")
        else:
            print(f"❌ API调用失败: {response.message}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
else:
    print("❌ 未找到API密钥，请检查.env文件")
```

运行测试：

```bash
cd backend
venv\Scripts\activate.bat
python test_api_key.py
```

---

## 📊 截图中的错误解析

您的截图显示的错误信息：

```
No api key provided. You can set by dashscope.api_key = your_api_key in code, 
or you can set it via environment variable DASHSCOPE_API_KEY= your_api_key. 
You can store your api key to a file, and use dashscope.api_key_file_path=api_key_file_path 
in code, or you can set api key file path via environment variable DASHSCOPE_API_KEY_FILE_PATH, 
You can call save_api_key to api_key_file_path or default path(~/.dashscope/api_key).
```

**原因分析**：
1. ❌ `backend/.env` 文件不存在
2. ❌ `backend/.env` 文件存在但内容为空
3. ❌ `backend/.env` 文件中的密钥格式错误
4. ❌ 环境变量未正确加载

**解决步骤**：
1. 确认 `backend/.env` 文件存在
2. 确认文件中有 `DASHSCOPE_API_KEY=sk-xxx` 这一行
3. 确认密钥是有效的（不是示例密钥）
4. 重启后端服务

---

## 🛡️ 安全建议

### 保护您的API密钥

1. **不要提交到Git**
   - ✅ `.env` 已在 `.gitignore` 中
   - ✅ 检查：`git status` 不应看到 `.env`

2. **不要分享给他人**
   - ❌ 不要在聊天、邮件中发送
   - ❌ 不要截图包含密钥的内容
   - ❌ 不要上传到公开平台

3. **定期更换**
   - 每3-6个月更换一次
   - 怀疑泄露时立即更换

4. **使用子账号**
   - 为不同项目创建不同的子账号
   - 限制每个密钥的权限和配额

### 密钥泄露后的处理

如果您的密钥不慎泄露：

1. 立即前往阿里云控制台
2. 删除泄露的API Key
3. 创建新的API Key
4. 更新 `.env` 文件
5. 重启后端服务

---

## 💰 API费用说明

### 通义千问计费

- **通义千问VL**（图像理解）：按调用次数计费
- **通义千问Turbo**（文本生成）：按token计费

### 预估费用

以每天使用情况为例：

| 功能 | 日均调用 | 单价 | 日费用 | 月费用 |
|------|---------|------|--------|--------|
| AI解题 | 10次 | ¥0.02 | ¥0.20 | ¥6 |
| AI批改 | 5次 | ¥0.02 | ¥0.10 | ¥3 |
| 智能出题 | 3次 | ¥0.01 | ¥0.03 | ¥1 |
| **合计** | - | - | **¥0.33** | **¥10** |

**说明**：
- 以上为示例数据，实际费用以阿里云账单为准
- 新用户通常有免费额度
- 建议开启费用告警

### 控制费用

1. **设置预算**：在阿里云控制台设置月度预算
2. **监控用量**：定期查看API调用统计
3. **合理使用**：避免重复调用、测试时使用小规模数据

---

## 🆘 仍然无法解决？

### 检查清单

- [ ] 已获取通义千问API密钥
- [ ] `backend/.env` 文件存在
- [ ] `.env` 文件中有 `DASHSCOPE_API_KEY=sk-xxx`
- [ ] 密钥格式正确（sk-开头）
- [ ] 已重启后端服务
- [ ] 运行 `test_api_key.py` 测试成功

### 其他可能原因

1. **网络问题**
   - 检查能否访问 dashscope.aliyuncs.com
   - 尝试关闭VPN/代理

2. **Python环境问题**
   - 确认使用虚拟环境：`venv\Scripts\activate.bat`
   - 确认安装了dashscope：`pip list | findstr dashscope`

3. **文件编码问题**
   - `.env` 文件应该是UTF-8编码
   - 使用记事本或VS Code打开，另存为UTF-8

### 获取帮助

如仍无法解决，请提供：
1. `backend/.env` 文件内容（隐藏密钥后10位）
2. 后端启动日志
3. 浏览器控制台错误信息

---

## 📚 相关文档

- 通义千问官方文档：https://help.aliyun.com/zh/dashscope/
- API密钥管理：https://dashscope.console.aliyun.com/apiKey
- Python SDK文档：https://help.aliyun.com/zh/dashscope/developer-reference/quick-start

---

**配置成功后，您将看到：**

```
✅ 数据库连接池初始化成功 (5个连接)
INFO: Started server process [PID]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

系统即可正常使用！🎉

