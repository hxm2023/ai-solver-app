# 微信小程序API集成指南

## 📦 交付物清单

作为首席后端工程师，我已为您完成以下交付物：

- ✅ **backend/miniapp_api_addition.py** - 新增代码片段
- ✅ **MiniApp_API_Documentation.md** - 完整API文档
- ✅ **test_miniapp_api.py** - Python测试脚本
- ✅ **本文档** - 集成步骤指南

---

## 🚀 快速集成步骤

### 步骤 1: 修改 backend/main_simple.py

#### 1.1 添加导入语句

在 `backend/main_simple.py` 文件的**导入部分**，找到其他导入语句，添加：

```python
from typing import Literal  # 如果已有此行，跳过
from pydantic import BaseModel, Field  # 如果已有此行，跳过
```

**位置参考**：通常在文件开头，其他 `from typing import ...` 语句附近

---

#### 1.2 添加请求模型

在 `backend/main_simple.py` 中，找到 `ChatRequest` 类定义（或其他 Pydantic 模型），在其**之后**添加：

```python
class MiniAppRequest(BaseModel):
    """微信小程序专用请求模型"""
    image_base_64: str = Field(..., description="用户上传的完整图片，经过Base64编码")
    mode: Literal['solve', 'review'] = Field(..., description="操作模式：'solve'为解题，'review'为批改")
```

**位置参考**：
```python
class ChatRequest(BaseModel):
    # ... 现有代码 ...

# ← 在这里添加 MiniAppRequest 类
class MiniAppRequest(BaseModel):
    # ...
```

---

#### 1.3 添加API端点

在 `backend/main_simple.py` 的**最后**，在所有现有 API 端点（如 `@app.post("/chat")`, `@app.get("/mistakes/")` 等）之后，添加完整的端点函数。

**完整代码见**：`backend/miniapp_api_addition.py` 中的 `@app.post("/process_image_for_miniapp")` 函数

**位置参考**：
```python
@app.get("/mistakes/stats/summary")
async def get_mistakes_summary():
    # ... 现有代码 ...

# ← 在这里添加新的小程序API端点
@app.post("/process_image_for_miniapp")
async def process_image_for_miniapp(request: MiniAppRequest):
    # ... 新增代码 ...
```

---

### 步骤 2: 验证修改

#### 2.1 检查语法

```bash
cd backend
python -m py_compile main_simple.py
```

如果没有输出，说明语法正确 ✅

#### 2.2 启动后端服务

**Windows**：
```bash
.\venv\Scripts\activate
uvicorn main_simple:app --reload
```

**macOS/Linux**：
```bash
source venv/bin/activate
uvicorn main_simple:app --reload
```

#### 2.3 检查API文档

浏览器访问：`http://127.0.0.1:8000/docs`

在 Swagger UI 中，您应该能看到新的端点：

```
POST /process_image_for_miniapp
```

点击展开，确认请求体包含：
- `image_base_64` (string)
- `mode` (string, enum: solve, review)

---

### 步骤 3: 运行测试脚本

#### 3.1 准备测试图片

准备一张题目图片，例如：
```
D:\360安全浏览器下载\题目\错题样本\test_question.png
```

#### 3.2 修改测试脚本配置

编辑 `test_miniapp_api.py`，修改第 20 行：

```python
TEST_IMAGE_PATH = r"你的图片路径"
```

#### 3.3 运行测试

```bash
# 确保后端服务正在运行
python test_miniapp_api.py
```

**预期输出**：
```
======================================================================
  微信小程序API接口测试
======================================================================

📷 测试图片: D:\360安全浏览器下载\题目\错题样本\test_question.png
🔗 API地址: http://127.0.0.1:8000/process_image_for_miniapp
⏱️ 超时设置: 60秒

[准备] 正在读取并转换图片为Base64...
[准备] ✓ Base64编码完成

======================================================================
  测试 1/2: 解题模式 (solve)
======================================================================

[请求] 正在发送请求到 http://127.0.0.1:8000/process_image_for_miniapp
[请求] 模式: solve
[请求] 图片大小: 123456 字符
[响应] HTTP状态码: 200
[响应] 状态: success
[响应] 结果长度: 2345 字符

──────────────────────────────────────────────────────────────────────
【AI生成内容预览】(solve模式)
──────────────────────────────────────────────────────────────────────
## 题目解答

### 第1题

**题目分析**：这是一道关于二项式定理的题目...
...
──────────────────────────────────────────────────────────────────────

✅ 测试成功！
💾 完整结果已保存到: miniapp_test_result_solve.md
```

---

## 📝 代码集成检查清单

完成以下检查，确保集成正确：

- [ ] **导入语句已添加**
  ```python
  from typing import Literal
  from pydantic import BaseModel, Field
  ```

- [ ] **MiniAppRequest 模型已添加**
  ```python
  class MiniAppRequest(BaseModel):
      image_base_64: str = Field(...)
      mode: Literal['solve', 'review'] = Field(...)
  ```

- [ ] **API端点函数已添加**
  ```python
  @app.post("/process_image_for_miniapp")
  async def process_image_for_miniapp(request: MiniAppRequest):
      # ... 完整实现 ...
  ```

- [ ] **后端服务可以启动** - 无语法错误

- [ ] **Swagger文档显示新端点** - `http://127.0.0.1:8000/docs`

- [ ] **测试脚本运行成功** - 两种模式都返回结果

- [ ] **生成的Markdown文件可读** - 包含LaTeX公式

---

## 🎯 完整的 main_simple.py 结构参考

集成后，您的 `main_simple.py` 文件结构应该是：

```python
# 1. 导入语句
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal  # ← 确保有 Literal
import base64
import io
# ... 其他导入 ...

# 2. 初始化应用
app = FastAPI(title="沐梧AI解题系统", version="V24.6")

# 3. CORS中间件
app.add_middleware(CORSMiddleware, ...)

# 4. Pydantic模型定义
class ChatRequest(BaseModel):
    # ... 现有代码 ...

class MiniAppRequest(BaseModel):  # ← 新增
    image_base_64: str = Field(...)
    mode: Literal['solve', 'review'] = Field(...)

# 5. 辅助函数
def image_preprocess_v2(...):
    # ... 现有代码 ...

def extract_text_with_pix2text(...):
    # ... 现有代码 ...

def call_qwen_vl_max(...):
    # ... 现有代码 ...

# 6. API端点
@app.get("/")
async def root():
    # ... 现有代码 ...

@app.post("/chat")
async def chat(...):
    # ... 现有代码 ...

@app.get("/mistakes/")
async def get_mistakes():
    # ... 现有代码 ...

# ... 其他现有端点 ...

@app.post("/process_image_for_miniapp")  # ← 新增
async def process_image_for_miniapp(request: MiniAppRequest):
    # ... 新增的完整实现 ...
```

---

## 🔍 常见问题排查

### Q1: 启动时报错 `NameError: name 'Literal' is not defined`

**原因**：未导入 `Literal`

**解决**：在文件开头添加
```python
from typing import Literal
```

---

### Q2: 启动时报错 `NameError: name 'Field' is not defined`

**原因**：未导入 `Field`

**解决**：检查导入语句，确保有
```python
from pydantic import BaseModel, Field
```

---

### Q3: 测试时报错 `404 Not Found`

**原因**：端点函数未正确添加

**解决**：
1. 检查 `@app.post("/process_image_for_miniapp")` 装饰器是否正确
2. 访问 `http://127.0.0.1:8000/docs` 检查端点是否出现
3. 确认后端服务已重启（`--reload`模式会自动重启）

---

### Q4: 测试时返回 500 错误

**原因**：运行时错误

**解决**：
1. 查看后端控制台的详细错误堆栈
2. 检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否配置
3. 检查 `pix2text` 模型是否已下载

---

### Q5: AI响应很慢或超时

**原因**：通义千问API响应时间较长

**解决**：
1. 修改测试脚本的 `TIMEOUT` 为 120 或更高
2. 确认网络连接正常
3. 检查通义千问服务状态

---

## 📚 相关文档

完成集成后，建议阅读：

1. **MiniApp_API_Documentation.md** - 完整的API文档，提供给小程序开发者
2. **沐梧AI解题系统_技术文档.md** - 项目整体技术架构
3. **FastAPI官方文档** - https://fastapi.tiangolo.com/

---

## 🎉 集成完成后的下一步

### 对于后端工程师

- ✅ 提交代码到Git仓库
- ✅ 更新API文档
- ✅ 通知前端团队新接口已就绪

### 对于小程序开发者

- 📖 阅读 `MiniApp_API_Documentation.md`
- 🧪 使用测试账号进行联调
- 📱 集成到小程序中

### 建议的小程序端实现

1. **选择图片** - 使用 `wx.chooseImage`
2. **Base64编码** - 使用 `wx.getFileSystemManager().readFile`
3. **调用API** - 使用 `wx.request`
4. **渲染结果** - 使用 `towxml` 或 `wxParse` + MathJax

---

## 📞 技术支持

如遇到任何问题，请：

1. **检查日志**：后端控制台 + 小程序控制台
2. **查看文档**：本指南 + API文档
3. **联系团队**：提供详细的错误信息和堆栈跟踪

---

**版本**：V1.0  
**创建时间**：2025-10-20  
**适用后端版本**：V24.6+  
**作者**：Claude (首席后端工程师) 😊


