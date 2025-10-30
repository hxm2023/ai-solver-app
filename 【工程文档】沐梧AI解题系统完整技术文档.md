# 沐梧AI解题系统 - 完整技术文档

> 版本：V25.1 数据库版本（含本地JSON版本）  
> 最后更新：2025-01-26  
> 作者：沐梧AI团队

---

## 📋 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [技术栈](#技术栈)
4. [目录结构](#目录结构)
5. [核心模块](#核心模块)
6. [数据库设计](#数据库设计)
7. [API接口](#api接口)
8. [前端组件](#前端组件)
9. [部署指南](#部署指南)
10. [开发指南](#开发指南)
11. [常见问题](#常见问题)

---

## 📖 项目概述

### 项目简介

**沐梧AI解题系统**是一个基于大语言模型（LLM）的智能学习辅助平台，提供：
- 🤖 **AI智能解题**：上传题目图片，AI自动识别并详细解答
- 📝 **AI批改作业**：上传作业照片，AI自动批改并识别错题
- 📚 **错题本管理**：自动分类管理错题，支持知识点标签
- 🎯 **智能出题**：基于错题生成个性化练习题
- 🌐 **网络辅助出题**：搜索真实题库网站，提升题目质量
- 📄 **PDF导出**：支持公式和图片的完整导出

### 版本说明

#### V25.1 数据库版本（当前主推版本）
- ✅ MySQL云端存储
- ✅ 多用户支持（JWT认证）
- ✅ 数据隔离和安全
- ✅ 自动保存错题
- ✅ 完整功能（与本地版本100%一致）

#### 本地JSON版本（简化版）
- ✅ 无需数据库
- ✅ 本地JSON存储
- ✅ 单用户使用
- ✅ 快速启动

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                           │
│                    (React + TypeScript)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/WebSocket
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      前端服务 (Vite)                        │
│  - React 18 + TypeScript                                   │
│  - Marked (Markdown渲染)                                    │
│  - MathJax (公式渲染)                                       │
│  - React-Image-Crop (图片裁剪)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  后端API服务 (FastAPI)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  路由层                                             │   │
│  │  - auth_routes.py (认证)                           │   │
│  │  - main_db.py / main_simple.py (核心业务)         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  服务层                                             │   │
│  │  - 通义千问VL (图像理解)                           │   │
│  │  - 通义千问 (文本生成)                             │   │
│  │  - Pyppeteer (PDF生成)                             │   │
│  │  - BeautifulSoup4 (网页爬取)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  数据层                                             │   │
│  │  - database.py (MySQL操作)                         │   │
│  │  - JSON文件操作 (本地版本)                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  数据存储层                                 │
│  - MySQL 5.7+ (数据库版本)                                 │
│  - JSON文件 (本地版本)                                     │
└─────────────────────────────────────────────────────────────┘
```

### 数据流图

#### 1. AI解题流程

```
用户上传图片
    ↓
前端 (图片裁剪/预处理)
    ↓
后端接收 (base64编码)
    ↓
调用通义千问VL (图像理解+解题)
    ↓
返回解答
    ↓
前端渲染 (Markdown + MathJax)
    ↓
用户追问 (可选)
    ↓
继续调用AI (带图片上下文)
```

#### 2. AI批改作业流程

```
用户上传作业照片
    ↓
AI批改并识别对错
    ↓
检测到错误？
    ├─ Yes → 提取知识点 → 保存到数据库
    └─ No → 仅返回批改结果
    ↓
用户查看批改结果和知识点
```

#### 3. 智能出题流程

```
用户选择错题/知识点
    ↓
后端分析错题特征
    ↓
网络辅助开启？
    ├─ Yes → 搜索题库网站 → 爬取真题 → 作为参考
    └─ No → 直接生成
    ↓
AI生成题目+答案+解析
    ↓
保存到数据库/JSON
    ↓
用户查看和导出
```

---

## 🛠️ 技术栈

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2.0 | UI框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 4.x | 构建工具 |
| Marked | 9.x | Markdown渲染 |
| MathJax | 3.x | 数学公式渲染 |
| React-Image-Crop | 10.x | 图片裁剪 |
| Axios | 1.x | HTTP请求（本地版本） |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 编程语言 |
| FastAPI | 0.104.x | Web框架 |
| Uvicorn | 0.24.x | ASGI服务器 |
| PyMySQL | 1.1.x | MySQL驱动 |
| PyJWT | 2.8.x | JWT令牌 |
| Dashscope | 1.17.x | 阿里云通义千问SDK |
| Pyppeteer | 1.0.x | 无头浏览器（PDF生成） |
| BeautifulSoup4 | 4.12.x | 网页解析 |
| Requests | 2.31.x | HTTP请求 |
| Cryptography | 41.0.x | 密码加密 |
| Python-Multipart | 0.0.6 | 文件上传 |
| Python-Dotenv | 1.0.x | 环境变量 |

### 数据库

| 数据库 | 版本 | 用途 |
|--------|------|------|
| MySQL | 5.7+ | 主数据库（数据库版本） |

---

## 📁 目录结构

```
ai-solver-mvp/
│
├── frontend/                          # 前端项目目录
│   └── vite-project/                  # Vite项目
│       ├── src/
│       │   ├── components/            # React组件
│       │   │   ├── AuthModal.tsx      # 登录注册模态框
│       │   │   ├── AuthModal.css
│       │   │   ├── QuestionItem.tsx   # 题目项组件
│       │   │   └── TextItem.tsx       # 文本项组件
│       │   ├── utils/
│       │   │   └── api.ts             # API工具函数（JWT管理）
│       │   ├── App.tsx                # 本地JSON版本主应用
│       │   ├── App.css                # 本地版本样式
│       │   ├── AppDB.tsx              # 数据库版本主应用
│       │   ├── MainApp.tsx            # 带登录的个性化学习系统
│       │   ├── SimpleMistakeBook.tsx  # 简化错题本（本地JSON）
│       │   ├── SimpleMistakeBookDB.tsx # 数据库版错题本
│       │   ├── SimpleMistakeBookDB.css # 数据库版样式
│       │   ├── ModeSelector.css       # 模式选择器样式
│       │   ├── main.tsx               # 前端入口
│       │   └── index.css              # 全局样式
│       ├── public/                    # 静态资源
│       ├── index.html                 # HTML模板
│       ├── package.json               # NPM依赖
│       ├── tsconfig.json              # TypeScript配置
│       └── vite.config.ts             # Vite配置
│
├── backend/                           # 后端项目目录
│   ├── venv/                          # Python虚拟环境
│   ├── simple_data/                   # 简化版数据目录
│   │   ├── mistakes.json              # 错题数据（本地版本）
│   │   └── generated_questions.json   # 生成的题目（本地版本）
│   ├── generated_images/              # 生成的图片
│   ├── generated_papers/              # 生成的PDF试卷
│   ├── main_simple.py                 # 简化版后端（本地JSON）
│   ├── main_db.py                     # 数据库版后端（MySQL）
│   ├── auth_api.py                    # 认证API（JWT）
│   ├── database.py                    # 数据库操作模块
│   ├── image_enhancer.py              # 图像增强模块
│   ├── mistake_image_generator.py     # 错题图片生成
│   ├── models.py                      # 数据模型
│   ├── requirements.txt               # Python依赖
│   ├── .env                           # 环境变量（API密钥）
│   └── muwu_ai.db                     # SQLite数据库（已弃用）
│
├── 启动脚本/                          # 各种启动脚本
│   ├── 【启动】数据库版本系统.bat    # 数据库版本启动（推荐）
│   ├── 【启动】简化版错题本系统.bat  # 本地JSON版本启动
│   ├── 启动数据库后端.bat            # 仅启动数据库后端
│   └── 启动新界面.bat                # 启动其他界面
│
├── 文档/                              # 项目文档
│   ├── 【必读】V25.1完整功能使用指南.md
│   ├── V25.1功能对比与完整清单.md
│   ├── 修复连接问题指南.md
│   ├── V25.1_MySQL数据库集成指南.md
│   ├── V25.1_MySQL数据库集成完成报告.md
│   └── ... (更多文档)
│
├── 数据库脚本/                        # SQL脚本
│   ├── database_schema_upgrade.sql    # 数据库结构升级
│   ├── fix_subject_title.sql          # 修复字段长度
│   └── clean_migrated_data.sql        # 清理迁移数据
│
├── 工具脚本/                          # 辅助工具
│   ├── migrate_data.py                # 数据迁移工具
│   ├── 【安装】MySQL数据库依赖.bat
│   ├── 【测试】数据库连接.bat
│   ├── 【测试】用户认证.bat
│   └── 【执行】数据迁移.bat
│
└── README.md                          # 项目说明
```

---

## 🔧 核心模块

### 1. 前端核心模块

#### 1.1 App.tsx / AppDB.tsx（主应用）

**职责**：
- 模式选择（解题/批改/错题本）
- 图片上传和裁剪
- AI对话管理
- 消息历史展示
- 追问功能

**核心状态**：
```typescript
const [mode, setMode] = useState<'solve' | 'review' | 'mistakeBook' | null>(null);
const [messages, setMessages] = useState<Message[]>([]);
const [chatImageSrc, setChatImageSrc] = useState<string>('');
const [userInput, setUserInput] = useState<string>('');
const [isLoading, setIsLoading] = useState<boolean>(false);
```

**核心函数**：
- `sendMessage()` - 发送消息到后端
- `handleInitialSend()` - 处理首次图片上传
- `handleCropAndSend()` - 处理裁剪后的图片
- `handleAskQuestion()` - 处理追问

#### 1.2 SimpleMistakeBookDB.tsx（错题本）

**职责**：
- 错题列表展示
- 练习题库管理
- 智能出题配置
- PDF导出

**核心功能**：
- 知识点选择
- 错题批量选择
- 出题参数配置
- 网络辅助开关

#### 1.3 AuthModal.tsx（认证模态框）

**职责**：
- 用户注册
- 用户登录
- 表单验证

### 2. 后端核心模块

#### 2.1 main_db.py / main_simple.py（主服务）

**核心端点**：

```python
# 认证
POST /auth/register  # 用户注册
POST /auth/login     # 用户登录

# AI功能
POST /chat           # 统一对话接口（解题/批改）

# 错题本
GET  /mistakes/      # 获取错题列表
POST /mistakes/      # 创建错题
DELETE /mistakes/{id} # 删除错题

# 题目
GET  /questions/     # 获取题目列表
POST /questions/generate  # 生成题目
DELETE /questions/{id}    # 删除题目

# 导出
POST /export/pdf     # 导出PDF
```

**核心函数**：
- `generate_questions()` - 智能出题
- `search_web_for_questions()` - 网络搜索题目
- `export_pdf()` - 生成PDF
- `chat_with_image()` - 统一对话接口

#### 2.2 database.py（数据库操作）

**核心类**：

```python
class UserManager:
    """用户管理"""
    @staticmethod
    def register(account: str, password: str) -> Dict
    @staticmethod
    def login(account: str, password: str) -> Dict

class SubjectManager:
    """题目管理"""
    @staticmethod
    def create(user_id: str, subject_data: Dict) -> str
    @staticmethod
    def get_list(user_id: str, filters: Dict) -> List[Dict]

class ExamManager:
    """试卷管理"""
    @staticmethod
    def create(exam_data: Dict) -> str
    @staticmethod
    def get_by_id(exam_id: str) -> Dict

class UserExamManager:
    """用户-试卷关联管理"""
    @staticmethod
    def create_relation(user_id: str, subject_id: str, exam_id: str) -> str
```

#### 2.3 auth_api.py（认证API）

**核心函数**：

```python
def create_access_token(user_id: str, account: str) -> str:
    """创建JWT令牌"""
    
def verify_access_token(token: str) -> dict:
    """验证JWT令牌"""
    
async def get_current_user(authorization: str = Header(...)) -> dict:
    """获取当前登录用户（依赖注入）"""
```

---

## 🗄️ 数据库设计

### 数据库连接信息

```
主机: 14.103.127.20
端口: 3306
用户: root
密码: Jiuzhi#2024
数据库: edu
```

### 表结构

#### 1. user（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | VARCHAR(100) PK | 用户ID |
| account | VARCHAR(100) UNIQUE | 账号 |
| pwd | VARCHAR(100) | 密码（SHA-256加密） |
| create_time | DATETIME | 创建时间 |

#### 2. subject（题目表）

| 字段 | 类型 | 说明 |
|------|------|------|
| subject_id | VARCHAR(100) PK | 题目ID |
| subject_title | LONGTEXT | 题目标题 |
| subject_desc | LONGTEXT | 题目描述 |
| solve | LONGTEXT | 解答过程 |
| answer | LONGTEXT | 答案 |
| explanation | LONGTEXT | 解析 |
| subject_type | VARCHAR(50) | 类型（practice/mistake） |
| difficulty | VARCHAR(20) | 难度 |
| knowledge_points | TEXT | 知识点（JSON数组） |
| subject_name | VARCHAR(50) | 学科名称 |
| grade | VARCHAR(20) | 年级 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 3. exam（试卷表）

| 字段 | 类型 | 说明 |
|------|------|------|
| exam_id | VARCHAR(100) PK | 试卷ID |
| exam_title | VARCHAR(100) | 试卷标题 |
| exam_content | TEXT | 试卷内容 |
| created_at | DATETIME | 创建时间 |
| exam_type | VARCHAR(50) | 类型（custom/mistake） |

#### 4. user_exam（用户-试卷关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(100) PK | 关联ID |
| user_info | VARCHAR(100) | 用户ID（外键） |
| subject_id | VARCHAR(100) | 题目ID（外键） |
| exam_id | VARCHAR(100) | 试卷ID（外键） |
| answered_at | DATETIME | 答题时间 |
| user_answer | TEXT | 用户答案 |
| status | VARCHAR(20) | 状态（unanswered/correct/wrong） |

### 数据关系图

```
user (1) ─────< user_exam (N) >───── (1) subject
                  │
                  │
                  ↓
                 (N)
                  │
                 exam
```

---

## 🔌 API接口

### 认证接口

#### POST /auth/register

注册新用户

**请求体**：
```json
{
  "account": "testuser",
  "password": "password123"
}
```

**响应**：
```json
{
  "success": true,
  "message": "注册成功",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "uuid-string",
  "account": "testuser"
}
```

#### POST /auth/login

用户登录

**请求体**：
```json
{
  "account": "demo_user",
  "password": "demo123456"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_info": {
    "user_id": "uuid-string",
    "account": "demo_user",
    "nickname": "demo_user"
  }
}
```

### AI功能接口

#### POST /chat

统一对话接口（需要认证）

**Headers**：
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
```

**请求参数**：
- `image` (File, 可选) - 题目图片
- `mode` (String) - "solve" 或 "review"
- `prompt` (String) - 用户提问
- `solve_type` (String, 可选) - "single", "full", "specific"
- `specific_question` (String, 可选) - 指定题目

**响应**：
```json
{
  "success": true,
  "response": "AI的回答内容...",
  "mistake_saved": true,
  "knowledge_points": ["函数", "不等式"],
  "user_id": "uuid-string"
}
```

### 错题本接口

#### GET /mistakes/

获取用户的错题列表（需要认证）

**查询参数**：
- `limit` (int, 可选) - 返回数量，默认100
- `subject` (String, 可选) - 按学科筛选
- `grade` (String, 可选) - 按年级筛选

**响应**：
```json
{
  "items": [
    {
      "id": "uuid-string",
      "image_base64": "base64编码图片",
      "question_text": "题目文本",
      "wrong_answer": "错误答案",
      "ai_analysis": "AI分析",
      "subject": "数学",
      "grade": "高一",
      "knowledge_points": ["函数", "不等式"],
      "created_at": "2025-01-26T10:00:00",
      "reviewed_count": 0
    }
  ],
  "total": 10
}
```

#### POST /mistakes/

创建新错题（需要认证）

**请求体**：
```json
{
  "image_base64": "base64编码图片",
  "question_text": "题目文本",
  "wrong_answer": "错误答案",
  "ai_analysis": "AI分析",
  "subject": "数学",
  "grade": "高一",
  "knowledge_points": ["函数", "不等式"]
}
```

#### DELETE /mistakes/{id}

删除错题（需要认证）

### 题目接口

#### GET /questions/

获取用户的题目列表（需要认证）

**查询参数**：
- `limit` (int, 可选) - 返回数量，默认100

**响应**：
```json
{
  "items": [
    {
      "id": "uuid-string",
      "content": "题目内容",
      "answer": "答案",
      "explanation": "详细解析",
      "knowledge_points": ["函数", "不等式"],
      "difficulty": "中等",
      "created_at": "2025-01-26T10:00:00",
      "subject": "数学",
      "grade": "高一"
    }
  ],
  "total": 20
}
```

#### POST /questions/generate

智能生成题目（需要认证）

**请求体**：
```json
{
  "mistake_ids": ["uuid1", "uuid2"],
  "count": 5,
  "difficulty": "中等",
  "allow_web_search": true
}
```

**响应**：
```json
{
  "questions": [
    {
      "id": "uuid-string",
      "content": "生成的题目内容",
      "answer": "答案",
      "explanation": "详细解析",
      "knowledge_points": ["函数"],
      "difficulty": "中等"
    }
  ]
}
```

### 导出接口

#### POST /export/pdf

导出题目为PDF（需要认证）

**请求体**：
```json
{
  "question_ids": ["uuid1", "uuid2"],
  "title": "练习题集",
  "include_answers": true
}
```

**响应**：
- Content-Type: application/pdf
- 文件流（PDF）

---

## 🎨 前端组件

### 组件层次结构

```
main.tsx
  └── AppDB (数据库版本) 或 App (本地版本)
      ├── ModeSelector
      │   └── 模式选择卡片
      │
      ├── MainAppDBContent
      │   ├── 上传区域
      │   │   ├── 文件选择
      │   │   └── 图片裁剪 (ReactCrop)
      │   │
      │   ├── 聊天界面
      │   │   ├── 题目图片回显
      │   │   ├── 消息气泡
      │   │   └── 输入框
      │   │
      │   └── SimpleMistakeBookDB (hideAuth=true)
      │       ├── 统计卡片
      │       ├── 标签页导航
      │       ├── 我的错题
      │       ├── 练习题库
      │       └── 智能出题
      │
      └── AuthModal
          ├── 登录表单
          └── 注册表单
```

### 主要组件说明

#### AuthModal.tsx

用户认证模态框

**Props**：
```typescript
interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (userInfo: any) => void;
}
```

**功能**：
- 登录/注册切换
- 表单验证
- JWT令牌存储
- 错误提示

#### QuestionItem.tsx

题目渲染组件

**Props**：
```typescript
interface QuestionItemProps {
  question: Question;
}
```

**功能**：
- Markdown渲染
- MathJax公式渲染
- 自动触发渲染

#### TextItem.tsx

简单文本渲染组件

**Props**：
```typescript
interface TextItemProps {
  content: string;
}
```

**功能**：
- Markdown渲染
- MathJax公式渲染

---

## 🚀 部署指南

### 环境要求

#### 前端
- Node.js >= 14
- npm >= 6

#### 后端
- Python >= 3.8
- MySQL >= 5.7（数据库版本）

### 快速启动

#### 方法1：使用批处理文件（推荐）

**数据库版本（V25.1）**：

```batch
双击运行：【启动】数据库版本系统.bat
访问：http://localhost:5173/?mode=db
```

**本地JSON版本**：

```batch
双击运行：【启动】简化版错题本系统.bat
访问：http://localhost:5173
```

#### 方法2：手动启动

**步骤1：启动后端**

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
venv\Scripts\activate.bat

# 启动数据库版本
python -m uvicorn main_db:app --reload --host 127.0.0.1 --port 8000

# 或启动本地JSON版本
python -m uvicorn main_simple:app --reload --host 127.0.0.1 --port 8000
```

**步骤2：启动前端**

```bash
# 进入前端目录
cd frontend\vite-project

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

**步骤3：访问系统**

- 数据库版本：`http://localhost:5173/?mode=db`
- 本地JSON版本（完整）：`http://localhost:5173/?mode=old`
- 本地JSON版本（简化）：`http://localhost:5173/`

### 生产部署

#### 前端构建

```bash
cd frontend/vite-project
npm run build
```

构建产物在 `dist/` 目录。

#### 后端部署

使用 Gunicorn + Uvicorn workers：

```bash
gunicorn main_db:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 💻 开发指南

### 环境配置

#### 1. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 2. 配置环境变量

创建 `backend/.env` 文件：

```env
# 阿里云通义千问API密钥
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# JWT密钥（可选，默认使用内置密钥）
JWT_SECRET_KEY=your_secret_key_here

# 数据库配置（数据库版本）
DB_HOST=14.103.127.20
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Jiuzhi#2024
DB_NAME=edu
```

#### 3. 安装Chromium（PDF导出功能）

```bash
python -m pyppeteer_install
```

如果遇到权限问题，使用管理员权限运行：

```batch
双击运行：修复PDF导出功能.bat
```

### 开发流程

#### 1. 创建新功能分支

```bash
git checkout -b feature/new-feature
```

#### 2. 修改代码

- 前端：修改 `frontend/vite-project/src/` 下的文件
- 后端：修改 `backend/` 下的文件

#### 3. 测试

```bash
# 后端测试
cd backend
python -m pytest

# 前端测试
cd frontend/vite-project
npm test
```

#### 4. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/new-feature
```

### 代码规范

#### Python（后端）

- 遵循 PEP 8
- 使用类型注解
- 函数添加文档字符串

```python
def example_function(param1: str, param2: int) -> dict:
    """
    函数说明
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        返回值说明
    """
    pass
```

#### TypeScript（前端）

- 使用 TypeScript 类型
- React函数组件使用 `React.FC`
- Props使用接口定义

```typescript
interface ComponentProps {
  title: string;
  onClose: () => void;
}

const Component: React.FC<ComponentProps> = ({ title, onClose }) => {
  return <div>{title}</div>;
};
```

### 调试技巧

#### 后端调试

1. 查看Uvicorn日志
2. 使用 `print()` 或 `logging`
3. 使用FastAPI的 `/docs` 接口测试

#### 前端调试

1. 打开浏览器开发者工具（F12）
2. 查看Console日志
3. 使用React DevTools
4. 查看Network请求

---

## 🤔 常见问题

### 1. 后端无法启动

**问题**：`ModuleNotFoundError: No module named 'xxx'`

**解决**：
```bash
cd backend
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. 前端白屏

**问题**：页面加载后显示空白

**解决**：
1. 检查浏览器Console是否有错误
2. 确认后端是否正常启动
3. 检查CORS配置

### 3. PDF导出失败

**问题**：`PermissionError` 或 `Chromium not found`

**解决**：
```batch
双击运行：修复PDF导出功能.bat
```

### 4. 数据库连接失败

**问题**：`Can't connect to MySQL server`

**解决**：
1. 检查MySQL服务是否启动
2. 检查连接信息是否正确
3. 检查防火墙设置

### 5. 登录后401 Unauthorized

**问题**：登录成功但后续请求返回401

**解决**：
1. 检查JWT令牌是否正确存储
2. 检查后端CORS配置
3. 清除浏览器缓存和localStorage

### 6. 图片无法显示

**问题**：上传图片后无法显示

**解决**：
1. 检查base64编码是否正确
2. 检查图片大小（建议<5MB）
3. 检查浏览器控制台错误

---

## 📞 技术支持

### 联系方式

- 技术文档：查看项目根目录下的Markdown文件
- 问题反馈：提交GitHub Issue（如有）
- 快速修复：查看 `修复连接问题指南.md`

### 相关文档

1. **使用指南**：
   - 【必读】V25.1完整功能使用指南.md
   - V25.1功能对比与完整清单.md

2. **技术文档**：
   - V25.1_MySQL数据库集成指南.md
   - V25.1_MySQL数据库集成完成报告.md

3. **故障排查**：
   - 修复连接问题指南.md
   - PDF导出公式渲染修复指南.md

---

## 📝 更新日志

### V25.1 (2025-01-26)

**新增功能**：
- ✅ MySQL数据库集成
- ✅ 多用户支持（JWT认证）
- ✅ 自动保存错题功能
- ✅ 数据库版完整UI恢复
- ✅ 聊天界面UI优化（气泡样式、头像）

**修复问题**：
- ✅ CORS跨域问题
- ✅ 登录后401问题
- ✅ 前端白屏问题
- ✅ 数据库字段长度问题

**优化**：
- ✅ UI/UX与本地版本完全一致
- ✅ 代码结构优化
- ✅ 文档完善

### V25.0 (2025-01-25)

**新增功能**：
- ✅ 网络辅助出题
- ✅ PDF导出（MathJax渲染）
- ✅ 学科和年级标签
- ✅ 知识点筛选

### V24.x

- V24.6：生成题目超时修复
- V24.5：全面错误捕获
- V24.4：历史记录白屏修复
- V24.3：LaTeX渲染修复
- V24.2：白屏问题修复
- V24.1：三模块集成
- V24.0：轻量级重构

---

## 🎯 总结

沐梧AI解题系统是一个功能完整、技术先进的智能学习辅助平台。通过本文档，您应该能够：

1. ✅ 理解系统的整体架构
2. ✅ 掌握核心技术栈
3. ✅ 了解数据库设计
4. ✅ 熟悉API接口
5. ✅ 进行本地开发和部署
6. ✅ 解决常见问题

如有任何问题，请参考相关文档或联系技术支持。

---

**文档版本**：V1.0  
**最后更新**：2025-01-26  
**维护者**：沐梧AI团队

