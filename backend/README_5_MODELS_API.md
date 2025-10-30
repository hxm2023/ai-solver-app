# 🌟 5大模型API切换功能 - README

## 📖 简介

本功能允许您在5个大模型之间**只修改1行代码**即可切换，支持通过API调用开源和闭源模型。

### 支持的模型

| 模型 | 类型 | 推荐场景 | 成本 |
|------|------|----------|------|
| qwen-vl-max | 闭源 | 基准对比 | 100% |
| qwen3-vl-32b-thinking | 开源 | 日常使用 | 37.5% ⬇️ |
| qwen3-vl-32b-instruct | 开源 | 快速响应 | 37.5% ⬇️ |
| qwen3-vl-235b-a22b-thinking | 开源 | 复杂推理 | 75% ⬇️ |
| qwen3-vl-235b-a22b-instruct | 开源 | 高性能 | 75% ⬇️ |

---

## ⚡ 60秒快速开始

### 1. 配置API密钥
```bash
cd backend
copy .env.example.api_models .env
notepad .env  # 填入您的API密钥
```

### 2. 激活配置
```bash
copy config_api_models.py config.py
```

### 3. 测试连接
```bash
python test_5_models.py --all
```

### 4. 切换模型
编辑 `config.py` 第23行：
```python
ACTIVE_MODEL_KEY = "qwen3-vl-32b-thinking"  # 改为任意模型
```

### 5. 重启后端
```bash
python main_db.py
```

完成！

---

## 🛠️ 命令行工具

### 查看模型对比
```bash
# 查看当前模型
python show_model_comparison.py

# 查看价格对比
python show_model_comparison.py --price

# 查看所有信息
python show_model_comparison.py --all
```

### 测试模型连接
```bash
# 测试当前模型
python test_5_models.py

# 测试所有模型
python test_5_models.py --all

# 测试指定模型
python test_5_models.py --model qwen3-vl-32b-thinking
```

### 一键切换（Windows）
```bash
【一键切换】模型切换脚本.bat
```

---

## 📊 评测与报告

### 自动评测
系统会**自动记录**每次AI交互的评测数据到：
```
backend/evaluation_data/evaluation_results.csv
```

### 生成报告
```bash
python -c "from evaluation_suite import EvaluationLogger, ReportGenerator; logger = EvaluationLogger(); report = ReportGenerator(logger); report.generate_report()"
```

报告保存在：
```
backend/evaluation_reports/evaluation_report_*.md
```

---

## 🔑 API密钥获取

### 阿里云DashScope（必需）
- 网址：https://dashscope.console.aliyun.com/
- 价格：约 ¥0.008/千tokens
- 用于：qwen-vl-max

### SiliconFlow（推荐，32B模型）
- 网址：https://cloud.siliconflow.cn/
- 价格：约 ¥0.003/千tokens
- 用于：qwen3-vl-32b系列

### Together AI（推荐，235B模型）
- 网址：https://www.together.ai/
- 价格：约 $0.006/千tokens
- 用于：qwen3-vl-235b系列

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `config_api_models.py` | **核心配置文件**，修改此文件切换模型 |
| `.env` | API密钥配置 |
| `test_5_models.py` | 测试模型连接 |
| `show_model_comparison.py` | 查看模型对比 |
| `【一键切换】模型切换脚本.bat` | Windows一键切换工具 |

---

## ❓ 常见问题

### Q: 如何切换模型？
A: 编辑 `config.py` 第23行，修改 `ACTIVE_MODEL_KEY`，然后重启后端。

### Q: 为什么我的模型返回错误？
A: 检查：
1. `.env` 中的API密钥是否正确
2. API服务商是否支持该模型
3. 网络连接是否正常

### Q: 评测数据在哪里？
A: `backend/evaluation_data/evaluation_results.csv`

### Q: 如何查看当前使用的模型？
A: 运行 `python show_model_comparison.py`

---

## 📚 详细文档

- **快速指南**：`【快速指南】5大模型切换与评测.md`
- **快速开始**：`../【快速开始】5大模型API切换完整指南.md`
- **完整说明**：`../【交付】5大模型API切换功能完整说明.md`

---

## 🎯 推荐配置

### 极致性价比（推荐初学者）
```python
ACTIVE_MODEL_KEY = "qwen3-vl-32b-instruct"
```
使用 SiliconFlow，成本最低。

### 高性能（推荐生产环境）
```python
ACTIVE_MODEL_KEY = "qwen3-vl-235b-a22b-thinking"
```
使用 Together AI，推理能力最强。

### 平衡（推荐一般使用）
```python
ACTIVE_MODEL_KEY = "qwen3-vl-32b-thinking"
```
性价比和性能平衡。

---

## 📞 技术支持

如有问题，请查阅详细文档或检查：
1. API密钥配置
2. 网络连接
3. 服务商支持的模型列表

---

**祝您使用愉快！** 🚀

