# API接口快速启动指南

## 🚀 3分钟上手

### 步骤1：启动服务

```bash
cd backend
uvicorn main:app --reload
```

看到以下输出说明成功：
```
✅ 统一智能API路由已加载: /api/solve, /api/question_bank
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 步骤2：运行测试脚本

```bash
python test_api.py
```

### 步骤3：查看API文档

浏览器打开：http://127.0.0.1:8000/docs

---

## 📋 接口功能对照表

根据您的需求，所有功能已实现：

| **功能需求** | **API调用** | **示例** |
|------------|------------|---------|
| 发送一道题目的图片信息 → 返回题目解析结果 | `POST /api/solve` | `{"mode":"solve","content":{"image_base64":"..."}}` |
| 发送一道题目的文字信息 → 返回题目解析结果 | `POST /api/solve` | `{"mode":"solve","content":{"text":"求1+1"}}` |
| 发送多道题目的图片信息 → 返回题目解析结果 | `POST /api/solve` | `{"mode":"solve","question_count":"multiple","content":{"image_base64":"..."}}` |
| 发送多道题目的文字信息 → 返回题目解析结果 | `POST /api/solve` | `{"mode":"solve","content":{"text":"第1题...第2题..."}}` |
| 发送带有结果一道题目的图片信息 → 返回题目批改结果 | `POST /api/solve` | `{"mode":"review","content":{"image_base64":"..."}}` |
| 发送带有结果一道题目的文字信息 → 返回题目批改结果 | `POST /api/solve` | `{"mode":"review","content":{"text":"题目+答案"}}` |
| 发送带有结果多道题目的图片信息 → 返回题目批改结果 | `POST /api/solve` | `{"mode":"review","question_count":"multiple","content":{"image_base64":"..."}}` |
| 发送带有结果多道题目的文字信息 → 返回题目批改结果 | `POST /api/solve` | `{"mode":"review","content":{"text":"多道题+答案"}}` |
| 发送知识点标签等 → 返回题库试题 | `POST /api/question_bank` | `{"tags":["函数","导数"],"limit":10}` |

---

## 💻 代码示例

### Python调用

```python
import requests
import base64

# 文字解题
response = requests.post('http://127.0.0.1:8000/api/solve', json={
    'mode': 'solve',
    'content': {'text': '求 f(x) = x^2 的导数'}
})
print(response.json()['results'][0]['answer']['content'])

# 图片解题
with open('question.png', 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode()

response = requests.post('http://127.0.0.1:8000/api/solve', json={
    'mode': 'solve',
    'content': {'image_base64': img_base64}
})
print(response.json())
```

### cURL测试

```bash
# 文字解题
curl -X POST http://127.0.0.1:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"mode":"solve","content":{"text":"求1+1的值"}}'

# 文字批改
curl -X POST http://127.0.0.1:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"mode":"review","content":{"text":"题目：1+1=? 答案：3"}}'

# 题库检索
curl -X POST http://127.0.0.1:8000/api/question_bank \
  -H "Content-Type: application/json" \
  -d '{"tags":["函数","导数"],"limit":5}'
```

---

## 📚 完整文档

- **详细API文档**：[API接口使用指南.md](./API接口使用指南.md)
- **在线文档**：http://127.0.0.1:8000/docs
- **测试脚本**：`python backend/test_api.py`

---

## ✅ 文件清单

```
backend/
  ├── api_routes.py          【新增】统一智能API实现
  ├── test_api.py            【新增】API测试脚本
  └── main.py                【已修改】集成API路由

根目录/
  ├── API接口使用指南.md       【新增】完整API文档
  └── API快速启动指南.md       【新增】本文件
```

---

## 🎯 核心特性

✅ **统一接口**：一个 `/api/solve` 处理8种功能  
✅ **自动识别**：输入类型和题目数量自动检测  
✅ **灵活配置**：支持多种详细程度和选项  
✅ **完整文档**：自动生成Swagger文档  
✅ **易于测试**：提供测试脚本和示例  

---

## 💡 提示

1. 所有功能已按您的需求表统一到 `/api/solve` 接口
2. 通过 `mode` 参数区分解题(solve)和批改(review)
3. 支持图片和文字两种输入方式
4. 自动检测单题还是多题
5. 题库检索使用独立的 `/api/question_bank` 接口

---

**🎉 现在开始使用这套强大的API接口吧！**

