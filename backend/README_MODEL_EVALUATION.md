# 大模型替换与评测框架 - README

## 🎯 项目简介

为"沐梧AI解题系统"开发的**大模型切换机制**和**完整评测框架**，支持从闭源模型（qwen-vl-max）向开源模型的平滑迁移和量化评估。

---

## 📦 核心模块

### 1. config.py - 模型配置中心
**一键切换模型，无需修改业务代码**

```python
# 只需修改这一行
ACTIVE_MODEL_KEY = "qwen3-vl-32b-instruct"
```

**支持5种模型：**
- `qwen-vl-max` - 闭源基准
- `qwen3-vl-32b-thinking` - 开源，思考链
- `qwen3-vl-32b-instruct` - 开源，直接指令（推荐）
- `qwen3-vl-235b-a22b-thinking` - 高性能，思考链
- `qwen3-vl-235b-a22b-instruct` - 高性能，直接指令

### 2. model_adapter.py - 统一适配器
**自动适配不同API格式，保持接口一致**

```python
from model_adapter import get_multimodal_adapter

adapter = get_multimodal_adapter()  # 自动使用配置的模型
for chunk in adapter.call(messages, stream=True):
    print(chunk["content"], end="")
```

### 3. evaluation_suite.py - 评测框架
**自动记录评测数据，生成对比报告**

```python
from evaluation_suite import quick_evaluate_and_log

quick_evaluate_and_log(
    model_name="qwen3-vl-32b-instruct",
    task_type="solve",
    input_prompt="解这道题...",
    raw_output="解答：...",
    notes="OCR准确"
)
```

---

## 🚀 5分钟快速开始

### Step 1: 测试框架
```bash
cd backend
python run_evaluation_test.py
```

### Step 2: 切换模型
编辑 `config.py`:
```python
ACTIVE_MODEL_KEY = "qwen3-vl-32b-instruct"
```

### Step 3: 集成到项目
参考 `【集成指南】大模型切换与评测框架.md`

核心修改：
```python
# 1. 导入
from model_adapter import get_multimodal_adapter
from evaluation_suite import quick_evaluate_and_log

# 2. 使用适配器
adapter = get_multimodal_adapter()
response = adapter.call(messages)

# 3. 记录评测
quick_evaluate_and_log(model_name, task_type, prompt, output)
```

---

## 📊 评测流程

### 1. 收集数据（建议每模型20+样本）

自动记录到 `evaluation_data/evaluation_results.csv`

### 2. 人工评分（1-5分制）

在CSV中填写13个维度的评分：
- 通用：指令遵循、格式正确、无幻觉
- 解题：OCR准确、答案正确、推理质量
- 批改：错误检测、解析清晰、知识点准确
- 生题：题目相关、创新难度、答案完整

### 3. 生成报告

```python
from evaluation_suite import EvaluationLogger, ReportGenerator

generator = ReportGenerator(EvaluationLogger())
generator.generate_report()
```

报告保存在 `evaluation_reports/evaluation_report_{timestamp}.md`

---

## 📁 文件清单

| 文件 | 说明 | 行数 |
|------|------|------|
| `config.py` | 模型配置中心 | 254 |
| `model_adapter.py` | 统一适配器 | 457 |
| `evaluation_suite.py` | 评测框架 | 852 |
| `run_evaluation_test.py` | 快速测试脚本 | 246 |
| `【集成指南】大模型切换与评测框架.md` | 详细集成指南 | - |
| `【完成】大模型替换与评测框架开发报告.md` | 开发报告 | - |
| `README_MODEL_EVALUATION.md` | 本文档 | - |

---

## 💡 设计亮点

✅ **零侵入**：对现有代码无侵入  
✅ **一键切换**：修改1行代码即可  
✅ **统一接口**：无需关心模型差异  
✅ **自动评测**：不影响业务性能  
✅ **定性分析**：记录典型问题，指导微调  
✅ **自动报告**：数据驱动决策  

---

## 🎯 评测维度（13个）

### 通用维度（3个）
1. instruction_following_score - 指令遵循
2. format_correction_score - 格式正确性
3. hallucination_score - 幻觉检测

### 解题任务（3个）
4. ocr_accuracy_score - OCR准确率
5. correctness_score - 答案正确性
6. reasoning_quality_score - 逻辑推理质量

### 批改任务（3个）
7. error_detection_score - 错误检测能力
8. explanation_clarity_score - 解析清晰度
9. knowledge_point_accuracy_score - 知识点准确性

### 生题任务（3个）
10. relevance_score - 题目相关性
11. creativity_difficulty_score - 创新与难度
12. answer_integrity_score - 答案完整性

### 性能指标（2个）
13. response_time_seconds - 响应时间
14. token_count - Token数量

---

## 🔧 本地模型部署

使用vLLM：

```bash
# 32B模型（单GPU）
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-32B-Instruct \
    --host 0.0.0.0 \
    --port 8001

# 235B模型（多GPU）
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-235B-A22B-Instruct \
    --host 0.0.0.0 \
    --port 8002 \
    --tensor-parallel-size 4
```

---

## 📈 预期评测结果

基于Qwen3-VL特点：

| 模型 | 性价比 | 指令遵循 | 推理能力 | OCR能力 | 推荐场景 |
|------|--------|----------|----------|---------|----------|
| 32B-Instruct | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 生产首选 |
| 32B-Thinking | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 复杂推理 |
| 235B-Instruct | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高质量要求 |
| 235B-Thinking | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 最高性能 |

**推荐策略：**
- 开发/测试 → 32B-Instruct
- 生产（高并发） → 32B-Instruct
- 生产（高质量） → 235B-A22B-Thinking

---

## 🛠️ 依赖安装

```bash
pip install httpx pandas matplotlib
```

---

## 📝 使用示例

### 示例1：切换模型并测试

```bash
# 1. 切换到32B-Instruct
# 编辑 config.py: ACTIVE_MODEL_KEY = "qwen3-vl-32b-instruct"

# 2. 测试
python run_evaluation_test.py

# 3. 查看结果
cat evaluation_data/evaluation_results.csv
```

### 示例2：在业务代码中使用

```python
# 原代码
response = dashscope.MultiModalConversation.call(
    model='qwen-vl-max',
    messages=messages
)

# 新代码（使用适配器）
from model_adapter import get_multimodal_adapter

adapter = get_multimodal_adapter()  # 自动使用config.py中的模型
for chunk in adapter.call(messages, stream=True):
    # 业务逻辑不变
    yield chunk["content"]
```

### 示例3：记录评测并生成报告

```python
from evaluation_suite import (
    quick_evaluate_and_log,
    EvaluationLogger,
    ReportGenerator
)

# 在AI响应完成后记录
quick_evaluate_and_log(
    model_name=config.ACTIVE_MODEL_KEY,
    task_type="solve",
    input_prompt=user_input,
    raw_output=ai_output,
    response_time=2.5,
    notes="手写体识别准确"
)

# 收集足够样本后生成报告
generator = ReportGenerator(EvaluationLogger())
report = generator.generate_report()
```

---

## ⚠️ 注意事项

1. **环境变量**：确保`.env`包含`DASHSCOPE_API_KEY`
2. **本地模型**：需要先启动推理服务
3. **GPU资源**：235B模型需要多GPU
4. **API兼容**：本地模型需要OpenAI兼容接口

---

## 🔗 相关文档

- **集成指南**：`【集成指南】大模型切换与评测框架.md`
- **开发报告**：`【完成】大模型替换与评测框架开发报告.md`
- **技术报告**：`../【工程文档】沐梧AI解题系统完整技术报告V2.md`

---

## ✅ 测试清单

- [ ] config.py加载正常
- [ ] 模型切换成功
- [ ] 适配器调用正常
- [ ] 评测记录正常
- [ ] 报告生成成功
- [ ] 本地模型连接成功（如使用）

---

## 📞 问题排查

### Q1: 模型切换不生效？
**A**: 重启Python进程/后端服务

### Q2: 本地模型连接失败？
**A**: 
1. 检查推理服务是否启动
2. 验证API地址：`curl http://localhost:8001/v1/models`
3. 检查防火墙

### Q3: 评测数据不保存？
**A**: 检查`evaluation_data/`目录权限

### Q4: 报告生成失败？
**A**: 
1. 确保至少有1条评测记录
2. 检查pandas是否安装：`pip install pandas`

---

## 🎉 快速测试

```bash
# 一键测试所有功能
cd backend
python run_evaluation_test.py

# 预期输出：
# ✅ 模型配置正常
# ✅ 模型适配器正常
# ✅ 评测记录正常
# ✅ 报告生成正常
```

---

**开发完成**: 2025-10-30  
**状态**: ✅ 已完成，待集成  
**维护**: 沐梧AI解题系统开发团队

**祝评测顺利！** 🚀

