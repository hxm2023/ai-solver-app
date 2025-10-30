# 【快速指南】通过API使用开源模型

## 🎯 核心优势

✅ **无需GPU** - 完全通过API调用  
✅ **即开即用** - 注册即可使用  
✅ **超低成本** - 比本地部署更便宜  
✅ **零运维** - 无需维护服务器  

---

## 📋 三种推荐方案

### 🥇 方案一：阿里云DashScope（最简单）

**优势：**
- 使用现有的API密钥
- 无需额外注册
- 与qwen-vl-max相同的API
- 稳定可靠

**支持的模型：**
- `qwen-vl-plus` - 性价比版（比Max便宜70%）
- `qwen2-vl-72b-instruct` - 高性能版（72B参数）

**价格：**
- qwen-vl-plus: ¥0.002/千tokens
- qwen2-vl-72b: ¥0.004/千tokens
- qwen-vl-max: ¥0.008/千tokens（对比）

### 🥈 方案二：SiliconFlow（最便宜）

**优势：**
- **超低价格**（比阿里云便宜80%）
- 支持多种Qwen模型
- 国内访问快

**支持的模型：**
- Qwen2-VL-7B-Instruct: ¥0.0007/千tokens
- Qwen2-VL-72B-Instruct: ¥0.0035/千tokens

**注册地址：** https://cloud.siliconflow.cn/

### 🥉 方案三：Together AI（国际化）

**优势：**
- 国际化服务
- 稳定性高
- 支持多种开源模型

**价格：** $0.001/千tokens

**注册地址：** https://www.together.ai/

---

## 🚀 5分钟快速开始

### Step 1: 选择服务商并注册

#### 选项A：使用阿里云（推荐新手）

**跳过此步**，您已经有DashScope API密钥了！

#### 选项B：注册SiliconFlow（推荐省钱）

1. 访问 https://cloud.siliconflow.cn/
2. 注册账号
3. 在"API密钥"页面创建密钥
4. 复制API密钥（格式：`sk-xxxxx`）

#### 选项C：注册Together AI

1. 访问 https://www.together.ai/
2. 注册账号
3. 在设置中创建API密钥
4. 复制API密钥

### Step 2: 配置API密钥

编辑 `backend/.env` 文件：

```env
# 原有的阿里云密钥（保留）
DASHSCOPE_API_KEY=sk-your-dashscope-key

# 【新增】如果使用SiliconFlow
SILICONFLOW_API_KEY=sk-your-siliconflow-key

# 【新增】如果使用Together AI
TOGETHER_API_KEY=your-together-key
```

### Step 3: 替换配置文件

**备份原配置：**
```bash
cd backend
copy config.py config_backup.py
```

**使用新配置：**
```bash
copy config_with_api_models.py config.py
```

或者手动复制 `config_with_api_models.py` 的内容到 `config.py`。

### Step 4: 选择模型

编辑 `backend/config.py` 第18行：

```python
# 阿里云选项
ACTIVE_MODEL_KEY = "qwen-vl-plus"       # 性价比版
# ACTIVE_MODEL_KEY = "qwen2-vl-72b"     # 高性能版

# SiliconFlow选项
# ACTIVE_MODEL_KEY = "qwen-vl-7b-siliconflow"   # 超便宜
# ACTIVE_MODEL_KEY = "qwen-vl-72b-siliconflow"  # 性能好

# Together AI选项
# ACTIVE_MODEL_KEY = "qwen-vl-72b-together"
```

### Step 5: 测试

```bash
cd backend
python -c "import config; print(config.get_model_info())"
```

**预期输出：**
```
[当前模型] qwen-vl-plus
  描述: 通义千问VL Plus - 性价比开源版（API）
  提供商: 阿里云DashScope
  类型: dashscope_api
  成本等级: medium
  价格: 约0.002元/千tokens（比Max便宜70%）
  能力: multimodal, streaming, cost_effective
```

### Step 6: 运行测试

```bash
python run_evaluation_test.py
```

---

## 💰 成本对比

### 处理1000次请求（每次2000 tokens）

| 模型 | 服务商 | 总成本 | 说明 |
|------|--------|--------|------|
| **qwen-vl-7b** | SiliconFlow | ¥1.4 | 🏆 最便宜 |
| **qwen-vl-plus** | 阿里云 | ¥4 | ⭐ 推荐 |
| **qwen2-vl-72b** | SiliconFlow | ¥7 | 高性价比 |
| **qwen2-vl-72b** | 阿里云 | ¥8 | 稳定可靠 |
| **qwen-vl-max** | 阿里云 | ¥16 | 闭源旗舰 |

**省钱建议：**
- 开发测试 → SiliconFlow 7B（省钱）
- 生产环境 → 阿里云Plus（稳定）
- 高质量需求 → 72B版本

---

## 📊 性能对比

### 阿里云DashScope

| 指标 | qwen-vl-plus | qwen2-vl-72b | qwen-vl-max |
|------|--------------|--------------|-------------|
| 参数量 | ~30B | 72B | 未公开 |
| 推理速度 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 准确率 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 成本 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### SiliconFlow

| 指标 | 7B版本 | 72B版本 |
|------|--------|---------|
| 推理速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 准确率 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 成本 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 稳定性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 使用场景推荐

### 场景1：开发测试

**推荐：** SiliconFlow 7B  
**原因：** 极低成本，快速迭代  
**配置：** `ACTIVE_MODEL_KEY = "qwen-vl-7b-siliconflow"`

### 场景2：生产环境（高并发）

**推荐：** 阿里云 qwen-vl-plus  
**原因：** 稳定可靠，性价比高  
**配置：** `ACTIVE_MODEL_KEY = "qwen-vl-plus"`

### 场景3：高质量要求

**推荐：** 阿里云 qwen2-vl-72b  
**原因：** 72B参数，推理能力强  
**配置：** `ACTIVE_MODEL_KEY = "qwen2-vl-72b"`

### 场景4：国际化部署

**推荐：** Together AI  
**原因：** 全球CDN，稳定性好  
**配置：** `ACTIVE_MODEL_KEY = "qwen-vl-72b-together"`

---

## 🔄 切换模型对比测试

### 快速对比流程

#### 1. 测试阿里云Plus版

```bash
# 编辑config.py
ACTIVE_MODEL_KEY = "qwen-vl-plus"

# 重启后端
【启动】数据库版本系统.bat

# 测试5-10个样本
# 记录评分
```

#### 2. 测试SiliconFlow版

```bash
# 编辑config.py
ACTIVE_MODEL_KEY = "qwen-vl-7b-siliconflow"

# 重启后端
# 测试相同的5-10个样本
# 记录评分
```

#### 3. 生成对比报告

```bash
python -c "from evaluation_suite import *; ReportGenerator(EvaluationLogger()).generate_report()"
```

---

## ⚙️ 高级配置

### 自定义API参数

如果需要调整API参数，编辑模型配置：

```python
"qwen-vl-plus": {
    "type": "dashscope_api",
    "model_name": "qwen-vl-plus",
    "api_key_env": "DASHSCOPE_API_KEY",
    "temperature": 0.5,      # 降低随机性
    "max_tokens": 4096,      # 减少最大token
    "top_p": 0.8,           # 调整采样参数
    # ...
}
```

### 添加新的API服务商

```python
"your-custom-model": {
    "type": "openai_compatible",
    "model_name": "model-name-on-provider",
    "api_base": "https://api.provider.com/v1",
    "api_key": os.getenv("YOUR_API_KEY", ""),
    "description": "您的自定义模型",
    # ...
}
```

---

## 🆘 常见问题

### Q1: API密钥无效？

**A:** 检查：
1. `.env`文件是否在`backend/`目录下
2. API密钥是否正确（包括`sk-`前缀）
3. 重启Python进程

### Q2: 请求速度慢？

**A:** 
- SiliconFlow: 国内访问快
- 阿里云: 稳定但可能限流
- Together AI: 可能需要代理

### Q3: 响应格式不对？

**A:** 检查：
1. `model_name`是否正确
2. `api_base`是否正确
3. 查看`model_adapter.py`的格式转换

### Q4: 成本太高？

**A:** 
- 使用SiliconFlow（最便宜）
- 减小`max_tokens`
- 使用7B而非72B模型

---

## 📈 成本监控

### 查看API使用量

**阿里云：**
1. 登录 https://dashscope.console.aliyun.com/
2. 查看"用量统计"

**SiliconFlow：**
1. 登录控制台
2. 查看"使用详情"

### 设置预算提醒

建议在API平台设置：
- 每日预算上限
- 异常使用提醒
- 自动停止阈值

---

## ✅ 验证清单

使用API模型前，请确认：

- [ ] API密钥已正确配置在`.env`文件
- [ ] `config.py`已更新为新版本
- [ ] 已选择合适的模型
- [ ] 运行`python -c "import config; print(config.get_model_info())"`成功
- [ ] 运行`python run_evaluation_test.py`成功
- [ ] 查看API使用统计正常

---

## 🎉 总结

### 最佳实践

1. **开发阶段**：使用SiliconFlow 7B（便宜快速）
2. **评测阶段**：对比3-5个模型，选出最优
3. **生产阶段**：使用阿里云Plus或72B（稳定）
4. **成本优化**：根据实际使用量调整模型

### 推荐组合

```python
# 开发测试
ACTIVE_MODEL_KEY = "qwen-vl-7b-siliconflow"

# 生产环境
ACTIVE_MODEL_KEY = "qwen-vl-plus"  # 或 "qwen2-vl-72b"
```

---

**立即开始：** 选择一个服务商，5分钟即可使用开源模型！ 🚀

