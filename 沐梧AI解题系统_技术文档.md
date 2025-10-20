# 沐梧AI解题系统 - 完整技术文档

## 📋 项目概述

**沐梧AI解题系统**是一个基于人工智能的智能教育辅助平台，集成了解题、批改、错题管理、智能出题等多项功能，旨在为学生提供个性化的学习辅导体验。

### 核心定位
- **智能解题助手**：上传题目图片，AI给出详细解答
- **作业批改系统**：自动批改作业，指出错误并给出正解
- **个性化错题本**：自动保存错题，按知识点分类管理
- **智能出题引擎**：基于错题生成个性化练习题

### 技术特色
- **混合输入架构**：OCR文字识别 + 原图视觉理解，双重保障
- **自动化错题管理**：批改时自动识别错误，提取知识点，保存错题
- **LaTeX公式支持**：完整的数学公式渲染，支持Markdown格式
- **本地化存储**：使用JSON文件存储，无需数据库，轻量级部署

---

## 🎯 核心功能模块

### 1. AI智能解题

#### 功能描述
用户上传题目图片，系统通过AI进行智能解答，提供详细的解题步骤和思路。

#### 使用场景
- 学生遇到难题，需要详细解答
- 想学习某道题的解题方法
- 需要逐步解题指导

#### 技术流程
```
用户上传图片
    ↓
图像预处理（调整尺寸、格式转换）
    ↓
OCR识别（Pix2Text提取文字和公式）
    ↓
图像增强（锐化、对比度增强）
    ↓
混合输入构建（OCR文本 + 原始图片）
    ↓
调用通义千问AI（qwen-vl-max）
    ↓
AI生成详细解答
    ↓
Markdown格式化显示
    ↓
MathJax渲染LaTeX公式
```

#### 关键特性
- **三种解题模式**：
  - 单题解答：处理一道题
  - 整张图片：解答所有题目
  - 指定题目：只解答特定题号
  
- **追问功能**：
  - 可以针对AI的回答继续提问
  - 保持上下文，AI记住之前的对话
  - 重新发送原图，避免AI遗忘

- **历史记录**：
  - 自动保存对话历史
  - 可恢复之前的会话
  - 按时间排序，快速查找

### 2. AI批改作业

#### 功能描述
用户上传包含题目和答案的图片，AI自动批改，指出对错，给出正确解法。

#### 使用场景
- 学生完成作业后自查
- 家长辅导孩子检查作业
- 教师批量批改作业

#### 技术流程
```
用户上传题目+答案图片
    ↓
OCR识别（提取题目和答案）
    ↓
AI批改分析
    ↓
检测错误 → 添加 [MISTAKE_DETECTED] 标记
检测正确 → 添加 [CORRECT] 标记
    ↓
【自动错题保存流程】
    ↓
提取错误部分解析
    ↓
AI提取知识点（3-5个精确知识点）
    ↓
推测学科（数学、物理、英语等）
    ↓
保存到错题本（JSON文件）
    ↓
返回批改结果 + 错题保存提示
```

#### 关键特性
- **智能判断标准**：
  ```
  ✅ [CORRECT]：答案正确，逻辑合理，即使有小瑕疵
  ❌ [MISTAKE_DETECTED]：答案错误、计算有误、概念理解错误
  ```

- **自动错题保存**：
  - 只保存做错的题目
  - 自动提取知识点（如"二项式定理"、"组合数计算"）
  - 推测学科分类
  - 保存完整的题目图片、解析、知识点

- **知识点精确化**：
  - AI提示要求精确到具体概念
  - 如"一元二次方程求根公式"而非"方程"
  - 限制3-5个知识点，按重要性排序

### 3. 智能错题本

#### 功能描述
自动管理用户的错题，按知识点分类，提供统计分析，支持筛选和导出。

#### 数据结构
```json
{
  "id": "uuid",
  "image_base64": "错题原图",
  "question_text": "OCR识别的题目文本",
  "wrong_answer": "学生的错误答案",
  "ai_analysis": "AI的批改解析",
  "subject": "数学",
  "knowledge_points": ["二项式定理", "组合数计算"],
  "created_at": "2025-10-20T13:57:07",
  "reviewed_count": 0
}
```

#### 核心功能

**A. 错题管理**
- 查看所有错题（按时间倒序）
- 查看错题原图
- 查看AI解析
- 按学科筛选（数学、物理、化学等）
- 删除错题

**B. 统计分析**
```javascript
{
  "total_mistakes": 15,        // 总错题数
  "by_subject": {              // 按学科统计
    "数学": 10,
    "物理": 3,
    "英语": 2
  },
  "recent_mistakes": [...]     // 最近错题
}
```

**C. 知识点标签系统**
- 自动提取所有唯一知识点
- 可选择知识点筛选错题
- 基于知识点生成练习

#### 存储方案
- 使用JSON文件本地存储（`backend/mistakes.json`）
- 无需数据库，轻量级
- 支持并发读写（文件锁机制）

### 4. AI智能出题

#### 功能描述
基于用户的错题生成相似的练习题，帮助巩固薄弱知识点。

#### 生成模式

**A. 基于错题生成**
```
选择错题 → AI分析错题类型 → 生成相似题目
```

**B. 基于知识点生成**
```
选择知识点 → 筛选相关错题 → AI生成针对性练习
```

#### 技术流程
```
用户选择错题/知识点
    ↓
配置生成参数：
- 题目数量（1-20题）
- 难度等级（简单/中等/困难）
- 题型（选择题/填空题/解答题/综合）
    ↓
后端调用AI（通义千问）
    ↓
AI分析错题：
- 考查知识点
- 题目难度
- 解题方法
    ↓
AI生成新题目：
- 题目内容（Markdown + LaTeX）
- 标准答案
- 详细解析
- 关联知识点
    ↓
保存到题库（questions.json）
    ↓
前端展示（LaTeX渲染）
```

#### 题目数据结构
```json
{
  "id": "uuid",
  "content": "题目内容（Markdown格式，含LaTeX）",
  "answer": "标准答案",
  "explanation": "详细解析",
  "difficulty": "中等",
  "question_type": "解答题",
  "knowledge_points": ["二项式定理", "组合数"],
  "source_mistake_ids": ["原错题ID"],
  "created_at": "2025-10-20T13:57:07"
}
```

#### 关键特性
- **Markdown + LaTeX支持**：题目中的数学公式自动渲染
- **批量生成**：一次可生成多道题目
- **智能导出**：
  - 支持PDF导出（保留公式渲染）
  - 支持Markdown导出
  - 可选择部分题目导出
- **题目管理**：
  - 查看所有生成的题目
  - 删除不需要的题目
  - 按知识点筛选

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI智能解题   │  │ AI批改作业   │  │ 智能错题本   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ AI智能出题   │  │ 历史记录     │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                      前端应用层 (React)                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │ React Components                                  │       │
│  │  - App.tsx (解题/批改)                            │       │
│  │  - SimpleMistakeBook.tsx (错题本/出题)           │       │
│  │  - ModeSelector.tsx (模式选择)                   │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 前端功能模块                                       │       │
│  │  - ErrorBoundary (错误边界)                       │       │
│  │  - 全局错误监听器                                  │       │
│  │  - MathJax渲染引擎                                │       │
│  │  - Marked Markdown解析                           │       │
│  │  - LocalStorage会话管理                          │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                    后端API层 (FastAPI)                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │ RESTful API Endpoints                             │       │
│  │  - POST /chat (解题/批改)                         │       │
│  │  - GET/POST/DELETE /mistakes/* (错题管理)        │       │
│  │  - GET/POST/DELETE /questions/* (题目管理)       │       │
│  │  - GET /mistakes/stats/* (统计分析)              │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 中间件 & 配置                                      │       │
│  │  - CORS (跨域支持)                                │       │
│  │  - 会话管理 (内存存储)                            │       │
│  │  - 文件锁机制                                      │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ OCR引擎      │  │ 图像增强     │  │ AI调用       │      │
│  │ (Pix2Text)   │  │ (OpenCV)     │  │ (通义千问)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 错题提取     │  │ 知识点识别   │  │ 题目生成     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ mistakes.json│  │ questions.json│  │ 会话内存    │      │
│  │ (错题数据)   │  │ (题目数据)   │  │ (临时会话)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                            │
│  │ LocalStorage │ (前端会话持久化)                          │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

### 部署架构

```
用户浏览器 (http://localhost:5173)
        ↓
Vite开发服务器 (前端)
        ↓ API调用
Uvicorn服务器 (http://127.0.0.1:8000)
        ↓
FastAPI应用 (后端)
        ↓ ├─→ Pix2Text OCR引擎
        │ ├─→ OpenCV图像处理
        │ ├─→ 通义千问API (外部AI服务)
        │ └─→ JSON文件存储
        ↓
本地文件系统
```

---

## 🔧 技术栈详解

### 前端技术栈

#### 核心框架
- **React 18.x**：用户界面构建
- **TypeScript**：类型安全的JavaScript
- **Vite**：现代化前端构建工具

#### UI相关
- **React-Image-Crop**：图片裁剪功能
- **Marked**：Markdown解析库
- **MathJax 3.x**：LaTeX数学公式渲染

#### 状态管理
- **React Hooks**：useState, useEffect, useRef
- **LocalStorage**：会话持久化存储

#### 网络请求
- **Axios**：HTTP客户端
  - 超时配置：5-10分钟（适应AI生成）
  - 错误处理：详细的错误分类

#### 错误处理
- **ErrorBoundary**：React错误边界组件
- **全局错误监听**：window.onerror, unhandledrejection
- **三层渲染防护**：过滤 → 容错 → 降级

### 后端技术栈

#### 核心框架
- **FastAPI**：现代化Python Web框架
  - 异步支持
  - 自动API文档（Swagger）
  - 类型验证（Pydantic）

#### 图像处理
- **Pix2Text**：OCR文字识别引擎
  - 支持中英文识别
  - 数学公式识别（LaTeX输出）
  - MFD (Math Formula Detection)

- **Pillow (PIL)**：图像基础操作
  - 格式转换
  - 尺寸调整
  - 模式转换（RGB, RGBA等）

- **OpenCV (cv2)**：高级图像处理
  - 锐化（反锐化掩模）
  - 对比度增强（CLAHE）
  - 色彩空间转换

#### AI服务
- **Dashscope SDK**：阿里云通义千问
  - 模型：qwen-vl-max（多模态大模型）
  - 支持文本+图像混合输入
  - 最大输出：8192 tokens

#### 数据处理
- **JSON**：轻量级数据存储
  - mistakes.json：错题数据
  - questions.json：题目数据
  - 自动备份机制

#### 工具库
- **python-dotenv**：环境变量管理
- **uuid**：唯一标识符生成
- **datetime**：时间戳处理
- **base64**：图片编码/解码

---

## 🔑 核心技术细节

### 1. 混合输入架构 (OCR + 原图)

#### 设计理念
结合OCR文字识别和原始图像视觉理解，双重保障识别准确性。

#### 技术实现

**步骤1：图像预处理**
```python
def image_preprocess_v2(img: Image.Image) -> Image.Image:
    # 1. 转为RGB模式
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 2. 调整尺寸（防止过大或过小）
    width, height = img.size
    max_dimension = 2000
    if max(width, height) > max_dimension:
        scale = max_dimension / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return img
```

**步骤2：图像增强**
```python
def advanced_image_processing_pipeline(img, sharpen_amount=1.5, clahe_clip_limit=2.0):
    # 1. PIL → OpenCV格式
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # 2. 反锐化掩模（增强边缘）
    gaussian = cv2.GaussianBlur(img_cv, (5, 5), 0)
    sharpened = cv2.addWeighted(img_cv, 1 + sharpen_amount, gaussian, -sharpen_amount, 0)
    
    # 3. CLAHE对比度增强
    lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    enhanced = cv2.merge([l_clahe, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    # 4. OpenCV → PIL格式
    return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
```

**步骤3：OCR识别**
```python
def extract_text_with_pix2text(image: Image.Image) -> str:
    processed_img = image_preprocess_v2(image)
    enhanced_img = advanced_image_processing_pipeline(processed_img)
    
    # Pix2Text识别
    result = p2t.recognize(enhanced_img)
    ocr_text = result['text'] if isinstance(result, dict) else str(result)
    
    # 清理文本
    ocr_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ocr_text)
    return ocr_text.strip()
```

**步骤4：构建混合输入**
```python
# 增强Prompt（嵌入OCR结果）
enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{user_request}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目...
"""

# 混合消息（文本 + 图片）
messages = [{
    "role": "user",
    "content": [
        {'text': enhanced_prompt},
        {'image': f"data:image/png;base64,{image_base64}"}
    ]
}]
```

#### 优势分析
| 方案 | 优点 | 缺点 |
|------|------|------|
| **纯OCR** | 识别快速 | 手写字迹识别差，复杂公式易错 |
| **纯图像** | 视觉理解好 | 图片模糊时识别困难 |
| **混合输入** | ✅ 兼具两者优势 | 处理时间稍长 |

### 2. 自动错题保存机制

#### 触发条件
```python
# AI回答中包含特殊标记
has_mistake = "[MISTAKE_DETECTED]" in full_response
is_review_mode = any(keyword in request.prompt for keyword in ["批改", "改", "检查"])

if has_mistake and is_review_mode:
    # 触发自动保存流程
```

#### 知识点提取
```python
knowledge_prompt = f"""请分析以下题目和批改内容，提取出3-5个精确的知识点标签。

题目内容：
{ocr_text[:500]}

批改内容：
{cleaned_response[:500]}

要求：
1. 每个知识点标签要精确到具体概念（如"一元二次方程求根公式"而非"方程"）
2. 返回格式：每行一个知识点，使用"- "开头
3. 限制3-5个知识点
4. 按重要性排序

请直接返回知识点列表："""

# AI提取知识点
knowledge_response = call_qwen_vl_max(knowledge_prompt)
knowledge_points = [
    line.strip().lstrip('- ')
    for line in knowledge_response.split('\n')
    if line.strip().startswith('-')
][:5]
```

#### 学科推测
```python
subject = "未分类"
if any(keyword in ocr_text for keyword in ["方程", "函数", "几何", "x", "y", "="]):
    subject = "数学"
elif any(keyword in ocr_text for keyword in ["单词", "语法", "词汇"]):
    subject = "英语"
elif any(keyword in ocr_text for keyword in ["力", "能量", "速度"]):
    subject = "物理"
```

#### 数据保存
```python
mistake = {
    "id": str(uuid.uuid4()),
    "image_base64": image_base64,
    "question_text": ocr_text,
    "wrong_answer": "(从批改中提取)",
    "ai_analysis": cleaned_response,
    "subject": subject,
    "knowledge_points": knowledge_points,
    "created_at": datetime.now().isoformat(),
    "reviewed_count": 0
}

mistakes.append(mistake)
save_mistakes(mistakes)  # 写入 mistakes.json
```

### 3. LaTeX公式渲染流程

#### 前端渲染管线

**步骤1：Markdown解析**
```typescript
// 使用marked库解析Markdown
const htmlContent = marked.parse(question.content) as string;
// 输入: 设 $(1+x)^{2n+1} = a_0 + \cdots$
// 输出: <p>设 <code class="language-math">$(1+x)^{2n+1}$</code> = a₀ + ⋯</p>
```

**步骤2：插入DOM**
```typescript
<div 
  className="math-content"
  dangerouslySetInnerHTML={{ __html: htmlContent }}
/>
```

**步骤3：MathJax渲染**
```typescript
useEffect(() => {
  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise()
      .then(() => console.log('LaTeX渲染成功'))
      .catch(err => console.error('LaTeX渲染失败:', err));
  }
}, [questions, messages]);
```

**最终效果**：
```
$(1+x)^{2n+1}$  →  (1+x)²ⁿ⁺¹  (上标正确显示)
\binom{2n}{n}   →  (₂ₙ)       (组合数符号)
                    ⁿ
```

#### 容错机制
```typescript
try {
  return marked.parse(content) as string;
} catch (err) {
  console.error('Markdown解析失败:', err);
  // 降级：使用纯文本
  return content.replace(/\n/g, '<br/>');
}
```

### 4. 会话管理机制

#### 前端会话持久化

**存储结构**
```typescript
interface SessionInfo {
  sessionId: string;
  title: string;
  timestamp: number;
  mode: 'solve' | 'review';
  imageSrc?: string;  // 题目缩略图
  messages?: Message[];  // 完整对话历史
}

// 保存到 localStorage
localStorage.setItem('ai_solver_sessions', JSON.stringify(sessions));
```

**自动保存时机**
```typescript
useEffect(() => {
  if (sessionId && messages.length > 0) {
    saveSession({
      sessionId,
      title: chatTitle,
      timestamp: Date.now(),
      mode,
      messages: messages
    });
  }
}, [sessionId, messages]);
```

#### 后端会话管理

**内存存储**
```python
SESSIONS = {}  # 全局会话字典

SESSIONS[session_id] = {
    "history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "title": "新对话",
    "image_base64": "..."
}
```

**追问时重建历史**
```python
# 第一条消息：包含图片
messages_to_send = [{
    "role": "user",
    "content": [
        {'text': first_user_message["content"]},
        {'image': f"data:image/png;base64,{original_image_base64}"}
    ]
}]

# 添加后续对话历史
for msg in history[1:]:
    messages_to_send.append(msg)

# 添加当前追问
messages_to_send.append({"role": "user", "content": current_prompt})
```

### 5. 错误处理体系

#### 四层防护机制

**第一层：React错误边界**
```typescript
class ErrorBoundary extends React.Component {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorPage error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

**第二层：组件级try-catch**
```typescript
{messages.map((msg, index) => {
  try {
    const htmlContent = marked.parse(msg.content);
    return <MessageBubble html={htmlContent} />;
  } catch (err) {
    return <ErrorPlaceholder error={err} />;
  }
})}
```

**第三层：全局错误监听**
```typescript
window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error);
  showErrorToast(event.message);
  event.preventDefault();  // 阻止白屏
});
```

**第四层：优雅降级**
```typescript
// Markdown解析失败 → 纯文本显示
// MathJax渲染失败 → 显示LaTeX代码
// 图片加载失败 → 占位符
```

---

## 📦 部署指南

### 环境要求

#### 系统要求
- **操作系统**：Windows 10/11, macOS, Linux
- **Python版本**：3.9 - 3.13
- **Node.js版本**：16.x 或更高

#### 硬件要求
- **CPU**：双核及以上
- **内存**：4GB 及以上（推荐8GB）
- **磁盘空间**：2GB（用于依赖和模型）

### 快速部署

#### 方式1：一键启动（Windows）
```bash
# 双击运行
【启动】简化版错题本系统.bat
```

#### 方式2：手动启动

**后端启动**
```bash
cd backend
python -m venv venv  # 创建虚拟环境（首次）
.\venv\Scripts\activate  # 激活虚拟环境（Windows）
pip install -r requirements.txt  # 安装依赖（首次）
uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
```

**前端启动**
```bash
cd frontend/vite-project
npm install  # 安装依赖（首次）
npm run dev
```

### 配置说明

#### 后端配置

**.env文件**
```bash
# 阿里云通义千问API Key
DASHSCOPE_API_KEY=your_api_key_here
```

#### 前端配置

**API地址**（`SimpleMistakeBook.tsx`）
```typescript
const API_BASE_URL = 'http://127.0.0.1:8000';
```

### 目录结构
```
ai-solver-mvp/
├── backend/
│   ├── main_simple.py          # 主应用
│   ├── requirements.txt        # Python依赖
│   ├── mistakes.json           # 错题数据
│   ├── questions.json          # 题目数据
│   └── venv/                   # 虚拟环境
├── frontend/
│   └── vite-project/
│       ├── src/
│       │   ├── App.tsx         # 解题/批改界面
│       │   ├── SimpleMistakeBook.tsx  # 错题本/出题界面
│       │   └── main.tsx        # 入口文件
│       ├── package.json        # Node依赖
│       └── vite.config.ts      # Vite配置
├── 【启动】简化版错题本系统.bat  # 一键启动脚本
└── README.md
```

---

## 📊 性能指标

### 响应时间

| 操作 | 平均时间 | 说明 |
|------|---------|------|
| **图片上传** | < 1s | 取决于图片大小 |
| **OCR识别** | 2-5s | 取决于图片复杂度 |
| **AI解题** | 10-30s | 取决于题目难度 |
| **批改作业** | 10-30s | 同上 |
| **生成题目（单题）** | 30-60s | AI生成需要时间 |
| **生成试卷（10题）** | 3-5分钟 | 批量生成较慢 |

### 并发能力

- **单机并发**：10-20个用户
- **限制因素**：
  - AI API调用频率限制
  - 内存存储会话数量
  - OCR引擎处理能力

### 存储容量

- **错题存储**：约100KB/题（含图片）
- **题目存储**：约5KB/题
- **建议**：定期清理旧数据

---

## 🔐 安全性说明

### 数据安全

**本地存储**
- 所有数据存储在本地JSON文件
- 不上传到云端服务器
- 用户完全控制数据

**敏感信息**
- API Key存储在 `.env` 文件
- 不提交到Git仓库
- 使用环境变量管理

### API安全

**CORS配置**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**建议生产环境配置**：
- 限制 `allow_origins` 为具体域名
- 添加速率限制
- 添加请求签名验证

---

## 🐛 常见问题

### Q1: OCR识别不准确
**解决方案**：
- 确保图片清晰度足够
- 避免手写字迹过于潦草
- 使用扫描件而非拍照（如果可能）

### Q2: AI回答不够详细
**解决方案**：
- 使用追问功能："请详细解释第3步"
- 明确要求："请写出完整的计算过程"

### Q3: 生成题目超时
**解决方案**：
- 减少单次生成题目数量
- 检查网络连接
- 等待更长时间（已延长到10分钟）

### Q4: LaTeX公式不显示
**解决方案**：
- 等待页面完全加载
- 检查浏览器控制台是否有错误
- 刷新页面（Ctrl+F5）

---

## 🔄 版本历史

### V24.6 (2025-10-20) - 当前版本
- ✅ 延长生成题目超时5倍
- ✅ 修复LaTeX公式渲染
- ✅ Markdown格式正确解析

### V24.5 (2025-10-20)
- ✅ 全面错误捕获机制
- ✅ 详尽的日志系统
- ✅ ErrorBoundary组件

### V24.4 (2025-10-20)
- ✅ 修复历史记录白屏
- ✅ 优化错题过滤逻辑
- ✅ 三层消息渲染防护

### V24.1-V24.3
- ✅ 三模块集成（解题+批改+错题本）
- ✅ 自动错题保存机制
- ✅ 智能出题功能

### V22.1
- ✅ 图像增强功能
- ✅ 混合输入架构
- ✅ 追问图片记忆

---

## 📞 技术支持

### 开发团队
- **项目名称**：沐梧AI解题系统
- **版本**：V24.6
- **最后更新**：2025-10-20

### 技术文档
- 用户指南：`【必看】V24.5白屏调试指南.md`
- 修复记录：`V24.x_*.md` 系列文档
- API文档：http://127.0.0.1:8000/docs

---

## 📝 总结

**沐梧AI解题系统**是一个功能完整、技术先进的智能教育辅助平台。系统采用**混合输入架构**，结合OCR和视觉AI，提供了解题、批改、错题管理、智能出题等全方位功能。

### 核心亮点
1. ✅ **双重识别保障**：OCR + 原图视觉，识别更准确
2. ✅ **自动化错题管理**：批改时自动保存，智能提取知识点
3. ✅ **个性化出题**：基于错题生成，针对性训练
4. ✅ **完整LaTeX支持**：数学公式完美渲染
5. ✅ **健壮的错误处理**：四层防护，不会白屏

### 技术优势
- 轻量级部署（无需数据库）
- 本地化存储（数据安全）
- 模块化设计（易于扩展）
- 详尽日志（便于调试）

适合教育机构、家庭辅导、学生自学等多种场景使用。

