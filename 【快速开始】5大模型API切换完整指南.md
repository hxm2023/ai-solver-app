# 🚀 5大模型API切换 - 完整快速指南

## 📌 核心功能

✨ **只需修改1行代码，即可在5个大模型之间自由切换！**

支持的模型：
1. **qwen-vl-max** - 通义千问VL Max（闭源基准）
2. **qwen3-vl-32b-thinking** - Qwen3-VL 32B 思考链版本
3. **qwen3-vl-32b-instruct** - Qwen3-VL 32B 指令版本
4. **qwen3-vl-235b-a22b-thinking** - Qwen3-VL 235B 思考链版本
5. **qwen3-vl-235b-a22b-instruct** - Qwen3-VL 235B 指令版本

---

## 🎯 三步快速上手

### 步骤1️⃣：配置API密钥

#### 1.1 创建 `.env` 文件

```bash
cd backend
copy .env.example.api_models .env
```

#### 1.2 编辑 `.env` 文件，填入您的API密钥

**最小配置（仅测试闭源模型）：**
```bash
DASHSCOPE_API_KEY=sk-你的阿里云API密钥
```

**推荐配置（测试所有模型）：**
```bash
# 阿里云DashScope（qwen-vl-max）
DASHSCOPE_API_KEY=sk-你的阿里云API密钥

# SiliconFlow（qwen3-32b系列，推荐）
QWEN3_API_BASE=https://api.siliconflow.cn/v1
QWEN3_API_KEY=sk-你的SiliconFlow密钥

# Together AI（qwen3-235b系列，推荐）
QWEN235_API_BASE=https://api.together.xyz/v1
QWEN235_API_KEY=你的TogetherAI密钥
```

### 步骤2️⃣：激活配置文件

**方式A：替换config.py（推荐）**
```bash
cd backend
copy config.py config_backup.py
copy config_api_models.py config.py
```

**方式B：修改main_db.py导入（如果不想覆盖原文件）**
```python
# 编辑 backend/main_db.py
# 找到 import config，改为：
import config_api_models as config
```

### 步骤3️⃣：测试配置

```bash
cd backend

# 查看所有模型配置
python config_api_models.py

# 测试当前激活的模型
python test_5_models.py

# 测试所有5个模型（推荐）
python test_5_models.py --all
```

**预期输出：**
```
✅ 成功 qwen-vl-max
✅ 成功 qwen3-vl-32b-thinking
✅ 成功 qwen3-vl-32b-instruct
⚠️  失败 qwen3-vl-235b-a22b-thinking  (未配置API密钥)
⚠️  失败 qwen3-vl-235b-a22b-instruct  (未配置API密钥)

总计: 3/5 个模型连接成功
```

---

## 🔄 如何切换模型

### 方法1：手动修改（1行代码）

编辑 `backend/config_api_models.py`，找到第 **23** 行：

```python
ACTIVE_MODEL_KEY = "qwen-vl-max"
```

改为：
```python
ACTIVE_MODEL_KEY = "qwen3-vl-32b-thinking"  # 或其他任意模型
```

保存后重启后端即可。

### 方法2：使用一键切换脚本（Windows）

```bash
cd backend
【一键切换】模型切换脚本.bat
```

按提示输入数字即可切换。

---

## 📊 完整评测流程

### 评测准备

确保所有模型API已配置并测试通过：
```bash
cd backend
python test_5_models.py --all
```

### 评测步骤

#### 第1轮：测试 qwen-vl-max

1. 修改配置：
```python
# backend/config_api_models.py 第23行
ACTIVE_MODEL_KEY = "qwen-vl-max"
```

2. 启动系统：
```bash
# 终端1：启动后端
cd backend
python main_db.py

# 终端2：启动前端
cd frontend/vite-project
npm run dev
```

3. 在浏览器访问 `http://localhost:5173`，进行**至少10次**测试：
   - 上传题目图片，让AI解题
   - 上传作业图片，让AI批改
   - 生成试卷

4. 每次AI交互都会**自动记录评测数据**到：
```
backend/evaluation_data/evaluation_results.csv
```

#### 第2-5轮：依次测试其他4个模型

重复以上步骤，依次切换到：
- `qwen3-vl-32b-thinking`
- `qwen3-vl-32b-instruct`
- `qwen3-vl-235b-a22b-thinking`
- `qwen3-vl-235b-a22b-instruct`

每个模型至少进行10次测试。

---

## 📈 生成对比报告

完成所有模型评测后：

```bash
cd backend

# 方法1：使用Python命令
python -c "from evaluation_suite import EvaluationLogger, ReportGenerator; logger = EvaluationLogger(); report = ReportGenerator(logger); report.generate_report()"

# 方法2：使用评测脚本
python run_evaluation_test.py
```

**报告位置：**
```
backend/evaluation_reports/evaluation_report_YYYYMMDD_HHMMSS.md
```

**报告内容包括：**
- ✅ 执行摘要（综合对比结论）
- 📊 综合评分对比表（5个模型全维度对比）
- 🔍 任务专项分析（解题/批改/生成）
- ⚠️ 定性问题日志（典型失败案例）
- 💡 最终推荐（性能+成本综合建议）

---

## 🔑 API密钥获取指南

### 阿里云DashScope（qwen-vl-max必需）

1. 访问：https://dashscope.console.aliyun.com/
2. 注册/登录阿里云账号
3. 开通"模型服务灵积"
4. 创建API Key
5. **价格**：约 ¥0.008/千tokens

### SiliconFlow（推荐用于32B模型）

1. 访问：https://cloud.siliconflow.cn/
2. 注册/登录
3. 进入"API密钥"页面
4. 创建新密钥
5. **价格**：约 ¥0.003/千tokens（非常便宜）

### Together AI（推荐用于235B大模型）

1. 访问：https://www.together.ai/
2. 注册/登录（支持Google账号）
3. 进入"API Keys"
4. 创建新密钥
5. **价格**：约 $0.006/千tokens

---

## 💡 成本对比分析

| 模型 | 服务商 | 价格（元/千tokens） | 相对成本 |
|------|--------|---------------------|----------|
| qwen-vl-max | 阿里云 | ¥0.008 | 基准 (100%) |
| qwen3-vl-32b-thinking | SiliconFlow | ¥0.003 | 37.5% |
| qwen3-vl-32b-instruct | SiliconFlow | ¥0.003 | 37.5% |
| qwen3-vl-235b-a22b-thinking | Together AI | ¥0.006 | 75% |
| qwen3-vl-235b-a22b-instruct | Together AI | ¥0.006 | 75% |

**结论**：
- 32B模型比闭源Max便宜**62.5%**
- 235B大模型比Max便宜**25%**，但性能可能更强

---

## ❓ 常见问题解答

### Q1: 为什么我的开源模型返回错误？

**A**: 排查步骤：

1. **检查API密钥**
```bash
# 查看环境变量是否正确加载
python -c "import os; print(os.getenv('QWEN3_API_KEY'))"
```

2. **检查API地址**
```bash
# 测试API连接
curl https://api.siliconflow.cn/v1/models -H "Authorization: Bearer sk-你的密钥"
```

3. **查看详细错误**
```bash
# 运行测试脚本查看完整错误信息
python test_5_models.py --model qwen3-vl-32b-thinking
```

### Q2: 模型切换后需要重启吗？

**A**: 是的。修改 `config_api_models.py` 后，必须：
1. 停止后端（Ctrl+C）
2. 重新运行 `python main_db.py`

前端无需重启。

### Q3: 能否在运行时动态切换模型？

**A**: 当前版本需要重启后端。如需动态切换，可以：
1. 在API请求中添加 `model` 参数
2. 修改 `main_db.py` 中的模型调用逻辑

### Q4: 评测数据会自动记录吗？

**A**: 是的！系统已集成评测框架，每次AI交互都会自动记录：
- 模型名称
- 任务类型（解题/批改/生成）
- 输入输出
- 响应时间
- 多维度评分

无需手动操作。

### Q5: 如何查看已记录的评测数据？

**A**: 
```bash
# 查看原始CSV数据
excel backend/evaluation_data/evaluation_results.csv

# 或用Python查看
python -c "import pandas as pd; df = pd.read_csv('backend/evaluation_data/evaluation_results.csv'); print(df.head())"
```

---

## 🎯 完整操作检查清单

- [ ] 步骤1：获取阿里云DashScope API密钥
- [ ] 步骤2：获取SiliconFlow API密钥（可选，用于32B模型）
- [ ] 步骤3：获取Together AI API密钥（可选，用于235B模型）
- [ ] 步骤4：创建 `.env` 文件并填入密钥
- [ ] 步骤5：激活 `config_api_models.py` 配置
- [ ] 步骤6：运行 `python test_5_models.py --all` 测试所有模型
- [ ] 步骤7：切换到第一个模型，启动系统
- [ ] 步骤8：进行10-20次测试（解题/批改/生成）
- [ ] 步骤9：重复步骤7-8，测试所有5个模型
- [ ] 步骤10：生成评测报告
- [ ] 步骤11：查看报告，选择最佳模型

---

## 📞 技术文档参考

- **详细配置说明**：`backend/【快速指南】5大模型切换与评测.md`
- **开发报告**：`backend/【完成】大模型替换与评测框架开发报告.md`
- **完整交付清单**：`【交付】大模型替换与评测框架 - 完整交付清单.md`
- **系统技术报告**：`【工程文档】沐梧AI解题系统完整技术报告V2.md`

---

## 🎉 下一步

完成评测后，您可以：

1. **选择最佳模型**：基于性能和成本综合考虑
2. **部署生产环境**：将 `ACTIVE_MODEL_KEY` 设置为最优模型
3. **持续优化**：根据实际使用情况调整prompt和参数
4. **成本监控**：跟踪API调用量，优化使用策略

---

**祝您评测顺利！如有问题，欢迎查阅技术文档。** 🚀

