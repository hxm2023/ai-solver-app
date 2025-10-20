# 沐梧AI解题系统 - API接口使用指南 V22.1

## 📋 接口列表

根据您的需求表格，我设计了以下API接口：

| **输入** | **返回** | **接口** | **说明** |
|---------|---------|---------|---------|
| 发送一道题目的图片信息 | 返回题目解析结果 | `POST /api/solve` | mode=solve, question_count=single |
| 发送一道题目的文字信息 | 返回题目解析结果 | `POST /api/solve` | mode=solve, input_type=text |
| 发送多道题目的图片信息 | 返回题目解析结果 | `POST /api/solve` | mode=solve, question_count=multiple |
| 发送多道题目的文字信息 | 返回题目解析结果 | `POST /api/solve` | mode=solve, input_type=text |
| 发送带有结果一道题目的图片信息 | 返回题目批改结果 | `POST /api/solve` | mode=review, question_count=single |
| 发送带有结果一道题目的文字信息 | 返回题目批改结果 | `POST /api/solve` | mode=review, input_type=text |
| 发送带有结果多道题目的图片信息 | 返回题目批改结果 | `POST /api/solve` | mode=review, question_count=multiple |
| 发送带有结果多道题目的文字信息 | 返回题目批改结果 | `POST /api/solve` | mode=review, input_type=text |
| 发送知识点标签等 | 返回题库试题 | `POST /api/question_bank` | 题库检索 |

**注**：根据您的要求，我们将所有解题/批改功能统一到 `/api/solve` 接口，通过参数区分功能。

---

## 🔌 接口1：统一解题/批改接口

### **基本信息**

- **接口地址**：`POST /api/solve`
- **功能**：统一处理解题和批改请求（图片/文字，单题/多题）
- **特点**：智能识别输入类型和题目数量

### **请求格式**

#### **请求头**
```http
POST /api/solve HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
```

#### **请求体（JSON格式）**

```json
{
  "mode": "solve",                    // 必需：solve=解题，review=批改
  "input_type": "auto",               // 可选：image/text/auto（自动检测）
  "question_count": "auto",           // 可选：single/multiple/auto（自动检测）
  "content": {
    "image_base64": "iVBORw0KGgo...",  // 图片Base64（二选一）
    "text": "题目文字内容"              // 文字内容（二选一）
  },
  "options": {
    "detail_level": "detailed",        // 可选：basic/detailed/full
    "language": "zh",                  // 可选：zh/en
    "include_steps": true,             // 可选：是否包含解题步骤
    "include_analysis": true           // 可选：是否包含错误分析
  },
  "session_id": null                   // 可选：会话ID（用于追问）
}
```

#### **参数说明**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `mode` | string | ✅ | `solve`=解题，`review`=批改 |
| `input_type` | string | ⭕ | `image`=图片，`text`=文字，`auto`=自动检测（默认） |
| `question_count` | string | ⭕ | `single`=单题，`multiple`=多题，`auto`=自动检测（默认） |
| `content.image_base64` | string | 📷 | Base64编码的图片（与text二选一） |
| `content.text` | string | 📝 | 纯文本题目（与image_base64二选一） |
| `options.detail_level` | string | ⭕ | `basic`=简答，`detailed`=详细（默认），`full`=完整 |
| `options.language` | string | ⭕ | `zh`=中文（默认），`en`=英文 |
| `options.include_steps` | boolean | ⭕ | 是否包含解题步骤（默认true） |
| `options.include_analysis` | boolean | ⭕ | 是否包含错误分析（默认true） |
| `session_id` | string | ⭕ | 会话ID（用于追问功能） |

### **响应格式**

```json
{
  "success": true,
  "session_id": "f123e7c8-8333-456d-b355-687a8f0ff20f",
  "results": [
    {
      "question_index": 1,
      "question_text": "已知函数 f(x) = x^2 + 2x + 1，求...",
      "answer": {
        "content": "### 解答\n\n这是一个二次函数...",
        "steps": [
          "步骤1：分析函数特征",
          "步骤2：配方法..."
        ],
        "final_answer": "f(x) = (x+1)^2"
      },
      "review": null
    }
  ],
  "metadata": {
    "mode": "solve",
    "input_type": "image",
    "question_count": "single",
    "processing_time_ms": 2350.45,
    "ocr_confidence": 0.95,
    "detail_level": "detailed"
  }
}
```

#### **响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 请求是否成功 |
| `session_id` | string | 会话ID（用于追问） |
| `results` | array | 题目结果列表 |
| `results[].question_index` | number | 题目序号 |
| `results[].question_text` | string | 题目内容（OCR识别或原文） |
| `results[].answer` | object | 解答内容（mode=solve时） |
| `results[].answer.content` | string | 完整解答（Markdown格式） |
| `results[].answer.steps` | array | 解题步骤列表 |
| `results[].answer.final_answer` | string | 最终答案 |
| `results[].review` | object | 批改结果（mode=review时） |
| `metadata` | object | 元数据信息 |

### **使用示例**

#### **示例1：单道题目图片解题**

```bash
curl -X POST http://127.0.0.1:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "solve",
    "input_type": "image",
    "question_count": "single",
    "content": {
      "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  }'
```

#### **示例2：多道题目文字批改**

```bash
curl -X POST http://127.0.0.1:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "review",
    "input_type": "text",
    "question_count": "multiple",
    "content": {
      "text": "第1题：计算 1+1=? 学生答案：2\n第2题：计算 2+2=? 学生答案：5"
    },
    "options": {
      "include_analysis": true
    }
  }'
```

#### **示例3：自动检测模式（最简单）**

```bash
curl -X POST http://127.0.0.1:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "solve",
    "content": {
      "text": "求函数 f(x) = x^2 的导数"
    }
  }'
```

#### **示例4：Python调用示例**

```python
import requests
import base64

# 读取图片并转Base64
with open('question.png', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# 发送请求
response = requests.post(
    'http://127.0.0.1:8000/api/solve',
    json={
        'mode': 'solve',
        'input_type': 'image',
        'content': {
            'image_base64': image_base64
        },
        'options': {
            'detail_level': 'full',
            'include_steps': True
        }
    }
)

# 处理响应
result = response.json()
if result['success']:
    answer = result['results'][0]['answer']['content']
    print('AI解答：\n', answer)
else:
    print('错误：', result.get('error'))
```

#### **示例5：JavaScript/TypeScript调用**

```typescript
async function solveQuestion(imageBase64: string) {
  const response = await fetch('http://127.0.0.1:8000/api/solve', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      mode: 'solve',
      input_type: 'image',
      content: {
        image_base64: imageBase64
      },
      options: {
        detail_level: 'detailed',
        include_steps: true
      }
    })
  });
  
  const result = await response.json();
  return result;
}
```

---

## 🔍 接口2：题库检索接口

### **基本信息**

- **接口地址**：`POST /api/question_bank`
- **功能**：根据知识点标签检索题库试题

### **请求格式**

```json
{
  "tags": ["函数", "导数"],           // 必需：知识点标签列表
  "difficulty": "medium",            // 可选：easy/medium/hard
  "subject": "math",                 // 可选：math/physics/chemistry
  "limit": 10,                       // 可选：返回数量（默认10，最大100）
  "offset": 0                        // 可选：分页偏移（默认0）
}
```

### **响应格式**

```json
{
  "success": true,
  "total": 156,
  "questions": [
    {
      "id": "q_001",
      "subject": "math",
      "tags": ["函数", "导数"],
      "difficulty": "medium",
      "content": "已知函数 f(x) = x^3 - 3x + 1，求 f'(x) 的值。",
      "answer": "f'(x) = 3x^2 - 3",
      "analysis": "这是一个基础的求导题目，应用幂函数求导公式即可。"
    }
  ],
  "metadata": {
    "limit": 10,
    "offset": 0,
    "returned": 2
  }
}
```

### **使用示例**

```bash
curl -X POST http://127.0.0.1:8000/api/question_bank \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["函数", "导数"],
    "difficulty": "medium",
    "subject": "math",
    "limit": 10
  }'
```

---

## 🛠️ 接口3：健康检查

### **接口地址**：`GET /api/health`

```bash
curl http://127.0.0.1:8000/api/health
```

**响应**：
```json
{
  "status": "healthy",
  "version": "V22.1",
  "api": "统一智能解题API",
  "services": {
    "pix2text": true,
    "dashscope": true,
    "image_enhancer": true
  }
}
```

---

## 📚 接口4：API信息

### **接口地址**：`GET /api/`

```bash
curl http://127.0.0.1:8000/api/
```

**响应**：
```json
{
  "name": "沐梧AI解题系统 - 统一智能API",
  "version": "V22.1",
  "endpoints": {
    "/api/solve": "统一解题/批改接口",
    "/api/question_bank": "题库检索接口",
    "/api/health": "健康检查",
    "/api/": "API信息"
  }
}
```

---

## 🔐 错误处理

### **标准错误响应**

```json
{
  "success": false,
  "error": "错误描述信息",
  "detail": "详细错误信息",
  "status_code": 400
}
```

### **常见错误码**

| 状态码 | 说明 | 解决方法 |
|--------|------|---------|
| 400 | 请求参数错误 | 检查请求格式和必需参数 |
| 404 | 会话不存在 | 会话已过期，重新开始新对话 |
| 500 | 服务器内部错误 | 查看后端日志，联系技术支持 |

---

## 🚀 快速开始

### **1. 启动服务**

```bash
cd backend
uvicorn main:app --reload
```

### **2. 访问API文档**

浏览器打开：`http://127.0.0.1:8000/docs`

FastAPI会自动生成交互式API文档（Swagger UI）

### **3. 测试接口**

```bash
# 方法1：使用curl
curl -X POST http://127.0.0.1:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"mode":"solve","content":{"text":"求1+1的值"}}'

# 方法2：使用Postman
打开Postman，导入collection

# 方法3：使用Python
python test_api.py
```

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **响应时间** | 1-3秒 | 包含OCR+AI推理 |
| **并发支持** | 10+ | 取决于服务器配置 |
| **图片大小限制** | 10MB | 建议压缩到2MB以下 |
| **文本长度限制** | 10000字符 | 超长文本会被截断 |

---

## 💡 最佳实践

### **1. 图片上传建议**

```python
# 压缩图片后再上传
from PIL import Image
import io
import base64

def compress_and_encode(image_path, max_size_mb=2):
    img = Image.open(image_path)
    
    # 调整尺寸
    max_dimension = 2000
    if max(img.size) > max_dimension:
        ratio = max_dimension / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.LANCZOS)
    
    # 压缩质量
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    
    # Base64编码
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
```

### **2. 批量处理**

```python
# 批量处理多张图片
import asyncio
import aiohttp

async def batch_solve(image_paths):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for path in image_paths:
            image_base64 = compress_and_encode(path)
            task = session.post(
                'http://127.0.0.1:8000/api/solve',
                json={'mode': 'solve', 'content': {'image_base64': image_base64}}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        results = [await r.json() for r in responses]
        return results

# 使用
results = asyncio.run(batch_solve(['q1.png', 'q2.png', 'q3.png']))
```

### **3. 错误重试**

```python
import time

def solve_with_retry(data, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.post(
                'http://127.0.0.1:8000/api/solve',
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if i == max_retries - 1:
                raise
            print(f'重试 {i+1}/{max_retries}...')
            time.sleep(2 ** i)  # 指数退避
```

---

## 🔧 配置说明

### **环境变量**

在 `backend/.env` 文件中配置：

```bash
# 必需
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 可选
API_RATE_LIMIT=100        # 每分钟请求限制
MAX_UPLOAD_SIZE_MB=10     # 最大上传大小
OCR_TIMEOUT_SECONDS=30    # OCR超时时间
```

---

## 📞 技术支持

- **API文档**：http://127.0.0.1:8000/docs
- **健康检查**：http://127.0.0.1:8000/api/health
- **版本信息**：http://127.0.0.1:8000/

---

## 🎉 总结

✅ **统一接口设计**：一个 `/api/solve` 接口覆盖8种功能场景  
✅ **智能参数检测**：自动识别输入类型和题目数量  
✅ **灵活配置选项**：支持不同详细程度和语言  
✅ **完善错误处理**：清晰的错误信息和状态码  
✅ **高性能处理**：集成V22.1图像增强技术  
✅ **开发者友好**：自动生成API文档，多种调用示例  

**现在就开始使用这套强大的AI解题API吧！** 🚀

