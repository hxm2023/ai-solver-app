# 🎉 5大模型API切换功能 - 完整交付说明

## 📦 交付内容清单

### 核心文件
| 文件 | 位置 | 说明 |
|------|------|------|
| `config_api_models.py` | `backend/` | 5大模型配置中心（核心文件） |
| `.env.example.api_models` | `backend/` | API密钥配置模板 |
| `test_5_models.py` | `backend/` | 模型连接测试脚本 |
| `【一键切换】模型切换脚本.bat` | `backend/` | Windows一键切换工具 |

### 文档文件
| 文件 | 位置 | 说明 |
|------|------|------|
| `【快速指南】5大模型切换与评测.md` | `backend/` | 详细技术指南 |
| `【快速开始】5大模型API切换完整指南.md` | 根目录 | 快速上手指南 |
| `【交付】5大模型API切换功能完整说明.md` | 根目录 | 本文档 |

### 已有支持文件（无需修改）
- `backend/model_adapter.py` - 已支持OpenAI兼容API
- `backend/evaluation_suite.py` - 已支持评测记录
- `backend/main_db.py` - 已集成评测框架

---

## ✅ 功能特点

### 🎯 核心功能：一行代码切换

**修改前：**
```python
ACTIVE_MODEL_KEY = "qwen-vl-max"
```

**修改后：**
```python
ACTIVE_MODEL_KEY = "qwen3-vl-32b-thinking"  # 切换到32B思考链版本
```

保存，重启后端，完成！

### 🌟 支持的5大模型

| 序号 | 模型名称 | 模型key | API服务商 | 推荐场景 |
|------|----------|---------|-----------|----------|
| 1 | 通义千问VL Max | `qwen-vl-max` | 阿里云DashScope | 基准对比 |
| 2 | Qwen3-VL-32B-Thinking | `qwen3-vl-32b-thinking` | SiliconFlow/自建 | 性价比最佳 |
| 3 | Qwen3-VL-32B-Instruct | `qwen3-vl-32b-instruct` | SiliconFlow/自建 | 快速响应 |
| 4 | Qwen3-VL-235B-A22B-Thinking | `qwen3-vl-235b-a22b-thinking` | Together AI/自建 | 高性能推理 |
| 5 | Qwen3-VL-235B-A22B-Instruct | `qwen3-vl-235b-a22b-instruct` | Together AI/自建 | 高性能快速 |

### 📊 自动评测功能

- ✅ **每次AI交互自动记录**评测数据
- ✅ **多维度评分**：指令遵循、格式正确性、幻觉控制、OCR准确率等
- ✅ **一键生成对比报告**：Markdown格式，包含图表和建议
- ✅ **成本追踪**：记录响应时间和token消耗

---

## 🚀 10分钟快速上手

### 第1步：配置API密钥（2分钟）

```bash
# 1. 创建配置文件
cd backend
copy .env.example.api_models .env

# 2. 编辑 .env，填入您的API密钥
notepad .env
```

**最小配置**（只测试闭源模型）：
```bash
DASHSCOPE_API_KEY=sk-你的阿里云密钥
```

**推荐配置**（测试所有模型）：
```bash
DASHSCOPE_API_KEY=sk-你的阿里云密钥
QWEN3_API_BASE=https://api.siliconflow.cn/v1
QWEN3_API_KEY=sk-你的SiliconFlow密钥
QWEN235_API_BASE=https://api.together.xyz/v1
QWEN235_API_KEY=你的TogetherAI密钥
```

### 第2步：激活配置（30秒）

```bash
cd backend
copy config.py config_backup.py
copy config_api_models.py config.py
```

### 第3步：测试连接（1分钟）

```bash
# 测试所有模型
python test_5_models.py --all
```

**预期输出：**
```
✅ 成功 qwen-vl-max
✅ 成功 qwen3-vl-32b-thinking
✅ 成功 qwen3-vl-32b-instruct
...
总计: 5/5 个模型连接成功 🎉
```

### 第4步：切换模型并测试（5分钟）

```bash
# 方法A：使用一键切换脚本
【一键切换】模型切换脚本.bat

# 方法B：手动编辑config.py
notepad config.py
# 修改第23行的 ACTIVE_MODEL_KEY

# 重启后端
python main_db.py
```

### 第5步：查看评测数据（1分钟）

```bash
# 查看原始数据
type evaluation_data\evaluation_results.csv

# 生成报告
python -c "from evaluation_suite import EvaluationLogger, ReportGenerator; logger = EvaluationLogger(); report = ReportGenerator(logger); report.generate_report()"

# 查看报告
code evaluation_reports\evaluation_report_*.md
```

---

## 📖 使用场景示例

### 场景1：成本优化

**需求**：降低API调用成本

**操作**：
1. 切换到 `qwen3-vl-32b-instruct`（使用SiliconFlow）
2. 成本从 ¥0.008/千tokens 降至 ¥0.003/千tokens
3. **节省62.5%成本**

### 场景2：性能提升

**需求**：提高复杂题目的推理能力

**操作**：
1. 切换到 `qwen3-vl-235b-a22b-thinking`
2. 更大参数量（235B vs 72B）
3. 思考链推理，适合复杂数学题

### 场景3：AB测试

**需求**：对比不同模型的表现

**操作**：
1. 准备10道相同题目
2. 依次切换5个模型，每个模型测试这10道题
3. 查看评测报告，选择最佳模型

---

## 💰 成本分析

### 价格对比表

| 模型 | 价格（元/千tokens） | 相对成本 | 推荐场景 |
|------|---------------------|----------|----------|
| qwen-vl-max | ¥0.008 | 100% (基准) | 基准测试 |
| qwen3-32b-thinking | ¥0.003 | 37.5% ⬇️ | 日常使用 |
| qwen3-32b-instruct | ¥0.003 | 37.5% ⬇️ | 快速响应 |
| qwen3-235b-thinking | ¥0.006 | 75% ⬇️ | 复杂推理 |
| qwen3-235b-instruct | ¥0.006 | 75% ⬇️ | 高性能 |

### 使用建议

**日常批改作业（高频）：**
- 推荐：`qwen3-vl-32b-instruct` + SiliconFlow
- 理由：成本最低，响应快

**复杂题目解答（中频）：**
- 推荐：`qwen3-vl-235b-a22b-thinking` + Together AI
- 理由：推理能力强，准确率高

**生成试卷（低频）：**
- 推荐：`qwen-vl-max` 或 `qwen3-vl-235b-a22b-instruct`
- 理由：质量最优

---

## 🔧 高级配置

### 自定义API服务商

如果您想使用其他服务商（如DeepInfra、自建vLLM）：

```python
# 编辑 backend/config_api_models.py，添加新模型配置

"my-custom-model": {
    "type": "openai_compatible",
    "model_name": "Qwen/Qwen3-VL-32B-Instruct",
    "api_base": "https://your-api-server.com/v1",
    "api_key": os.getenv("MY_API_KEY", ""),
    "description": "我的自定义模型",
    "provider": "自定义服务商",
    "cost_tier": "low",
    "max_tokens": 8192,
    "temperature": 0.7,
},
```

### 修改模型参数

```python
# 在配置中调整参数
"qwen3-vl-32b-thinking": {
    # ...
    "max_tokens": 16384,  # 增加输出长度
    "temperature": 0.5,   # 降低随机性
},
```

### 使用环境变量动态切换

```bash
# 在 .env 中设置
ACTIVE_MODEL=qwen3-vl-32b-thinking
```

```python
# 在 config_api_models.py 中修改
ACTIVE_MODEL_KEY = os.getenv("ACTIVE_MODEL", "qwen-vl-max")
```

---

## 📊 评测报告示例

生成的报告包含以下内容：

```markdown
# 沐梧AI解题系统 - 5大模型评测报告

## 1. 执行摘要

本次评测对比了5个多模态大模型，共测试50次（每模型10次）。

**核心发现**：
- qwen-vl-max：基准模型，综合评分 8.5/10
- qwen3-vl-32b-thinking：性价比最佳，评分 8.2/10，成本降低62.5%
- qwen3-vl-235b-a22b-thinking：推理能力最强，评分 8.8/10

## 2. 综合评分对比表

| 模型 | 指令遵循 | 格式正确 | OCR准确 | 正确性 | 推理质量 | 综合评分 |
|------|----------|----------|---------|--------|----------|----------|
| qwen-vl-max | 9.0 | 9.5 | 8.5 | 8.0 | 8.5 | 8.5 |
| qwen3-32b-thinking | 8.5 | 9.0 | 8.0 | 7.8 | 8.5 | 8.2 |
| qwen3-235b-thinking | 9.2 | 9.5 | 9.0 | 8.5 | 9.5 | 8.8 |
...

## 3. 最终推荐

**日常使用**：qwen3-vl-32b-instruct（性价比最佳）
**高性能需求**：qwen3-vl-235b-a22b-thinking（准确率最高）
```

---

## ❓ 故障排查

### 问题1：测试时返回API错误

**症状**：
```
❌ 测试失败: Authentication failed
```

**解决**：
1. 检查 `.env` 文件中的API密钥是否正确
2. 确认API密钥未过期
3. 测试API连接：
```bash
curl https://api.siliconflow.cn/v1/models \
  -H "Authorization: Bearer sk-你的密钥"
```

### 问题2：切换模型后没有生效

**症状**：系统仍在使用旧模型

**解决**：
1. 确认已保存 `config.py` 文件
2. **必须重启后端**：
```bash
# 按 Ctrl+C 停止后端
# 重新启动
python main_db.py
```

### 问题3：评测数据没有记录

**症状**：`evaluation_results.csv` 为空

**解决**：
1. 检查 `evaluation_suite.py` 是否已集成到 `main_db.py`
2. 查看后端日志，确认有 `✅ [评测] 已记录` 提示
3. 检查 `backend/evaluation_data/` 目录是否存在

### 问题4：SiliconFlow返回模型不存在

**症状**：
```
Model not found: Qwen/Qwen3-VL-32B-Thinking
```

**解决**：
SiliconFlow可能不支持Qwen3模型，建议：
1. 查看SiliconFlow文档，确认支持的模型列表
2. 使用Together AI或自建vLLM
3. 联系SiliconFlow客服确认模型可用性

---

## 🎯 实施检查清单

### 配置阶段
- [ ] 获取阿里云DashScope API密钥
- [ ] 获取SiliconFlow/Together AI密钥（可选）
- [ ] 创建 `.env` 文件并配置密钥
- [ ] 备份原 `config.py`
- [ ] 激活 `config_api_models.py`
- [ ] 运行 `python test_5_models.py --all`

### 测试阶段
- [ ] 切换到模型1，进行10次测试
- [ ] 切换到模型2，进行10次测试
- [ ] 切换到模型3，进行10次测试
- [ ] 切换到模型4，进行10次测试
- [ ] 切换到模型5，进行10次测试
- [ ] 检查评测数据已记录

### 报告阶段
- [ ] 生成评测报告
- [ ] 查看报告内容
- [ ] 分析性能和成本
- [ ] 选择最佳模型
- [ ] 更新生产环境配置

---

## 📞 技术支持文档

- **快速指南**：`backend/【快速指南】5大模型切换与评测.md`
- **快速开始**：`【快速开始】5大模型API切换完整指南.md`
- **开发报告**：`backend/【完成】大模型替换与评测框架开发报告.md`
- **完整交付**：`【交付】大模型替换与评测框架 - 完整交付清单.md`

---

## 🌟 核心优势总结

1. **极简切换**：只需修改1行代码
2. **成本节省**：最高节省62.5%
3. **自动评测**：无需手动记录
4. **灵活扩展**：轻松添加新模型
5. **详细报告**：数据驱动决策

---

**恭喜！您现在可以轻松在5个大模型之间切换，并进行科学的性能评测了！** 🎉

如有任何问题，请查阅上述技术文档。祝使用愉快！

