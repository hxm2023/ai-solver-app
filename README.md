# 沐梧AI解题系统

<div align="center">

**基于人工智能的智能教育辅助平台**

[![Version](https://img.shields.io/badge/version-v24.6-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.2.0-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104-009688.svg)](https://fastapi.tiangolo.com/)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [文档](#-文档)

</div>

---

## 📖 项目简介

沐梧AI解题系统是一个集成了**解题、批改、错题管理、智能出题**等多项功能的智能教育辅助平台。系统采用**混合输入架构**（OCR文字识别 + 原图视觉理解），结合阿里云通义千问大模型，为学生提供个性化的学习辅导体验。

### 核心优势

- 🎯 **双重识别保障**：OCR + 视觉AI，识别准确率高
- 📚 **自动错题管理**：批改时自动保存错题，智能提取知识点
- 🧠 **个性化出题**：基于错题生成针对性练习题
- 📐 **完整LaTeX支持**：数学公式完美渲染
- 🛡️ **健壮错误处理**：四层防护机制，不会白屏
- 💾 **本地化存储**：无需数据库，数据完全掌控

---

## ✨ 功能特性

### 1. 🧠 AI智能解题

- 上传题目图片，AI给出详细解答
- 支持三种模式：单题/整张图片/指定题目
- 支持追问，保持上下文对话
- 自动保存历史记录

![解题示例](docs/images/solve-demo.png)

### 2. 📝 AI批改作业

- 自动批改作业，指出对错
- 做错的题目**自动保存到错题本**
- 智能提取知识点标签
- 推测学科分类

![批改示例](docs/images/review-demo.png)

### 3. 📚 智能错题本

- 自动收集批改中的错题
- 按学科、知识点分类管理
- 查看完整的题目和解析
- 支持筛选、统计、导出

![错题本示例](docs/images/mistakes-demo.png)

### 4. 🎯 AI智能出题

- 基于错题生成相似练习题
- 基于知识点生成针对性训练
- 可配置题型、难度、数量
- 支持PDF/Markdown导出

![出题示例](docs/images/generate-demo.png)

---

## 🚀 快速开始

### 环境要求

- **Python**：3.9 - 3.13
- **Node.js**：16.x 或更高
- **操作系统**：Windows / macOS / Linux

---

### 📦 初次部署（首次使用必看）

#### 方式一：一键部署（Windows推荐）⭐

**步骤1：配置API Key**
```bash
# 在 backend/ 目录下创建 .env 文件
# 内容如下：
DASHSCOPE_API_KEY=your_api_key_here
```

> 💡 获取API Key：访问[阿里云百炼平台](https://bailian.console.aliyun.com/)申请免费API Key

**步骤2：安装依赖并启动**
```bash
# 双击运行（会自动安装依赖）
【启动】简化版错题本系统.bat
```

**步骤3：访问应用**
```
浏览器打开：http://localhost:5173/?mode=old
```

**说明**：
- 首次运行会自动安装Python和Node.js依赖（需要几分钟）
- 安装完成后会自动启动前后端服务
- 以后每次启动只需双击bat文件即可

---

#### 方式二：手动部署（所有平台）

**步骤1：配置API Key**
```bash
# 在 backend/ 目录下创建 .env 文件
cd backend
# Windows:
echo DASHSCOPE_API_KEY=your_api_key_here > .env

# macOS/Linux:
echo "DASHSCOPE_API_KEY=your_api_key_here" > .env
```

**步骤2：安装后端依赖**
```bash
cd backend
python -m venv venv                    # 创建虚拟环境
.\venv\Scripts\activate                # Windows激活
# source venv/bin/activate             # macOS/Linux激活
pip install -r requirements.txt        # 安装依赖（约5-10分钟）
```

**步骤3：安装前端依赖**
```bash
cd frontend/vite-project
npm install                            # 安装依赖（约2-5分钟）
```

**步骤4：启动服务**

打开两个终端窗口：

**终端1 - 后端**
```bash
cd backend
.\venv\Scripts\activate                # Windows
# source venv/bin/activate             # macOS/Linux
uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
```

**终端2 - 前端**
```bash
cd frontend/vite-project
npm run dev
```

**步骤5：访问应用**
```
浏览器打开：http://localhost:5173/?mode=old
```

---

### 🔄 重复打开项目（第二次及以后）

#### Windows用户（推荐）

```bash
# 直接双击运行
【启动】简化版错题本系统.bat

# 然后访问
http://localhost:5173/?mode=old
```

**说明**：
- 不需要重新安装依赖
- 自动启动前后端服务
- 关闭命令行窗口即停止服务

---

#### 手动启动（所有平台）

**方法1：使用脚本启动**
```bash
# Windows
【启动】简化版错题本系统.bat

# macOS/Linux（如果有对应启动脚本）
./start.sh
```

**方法2：手动启动两个服务**

**终端1 - 后端**
```bash
cd backend
.\venv\Scripts\activate                # Windows
# source venv/bin/activate             # macOS/Linux
uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
```

**终端2 - 前端**
```bash
cd frontend/vite-project
npm run dev
```

**访问地址**：http://localhost:5173/?mode=old

---

### 🌐 访问地址说明

| 地址 | 用途 | 说明 |
|------|------|------|
| **http://localhost:5173/?mode=old** | 主界面（推荐） | 解题+批改功能 |
| http://localhost:5173 | 错题本界面 | 错题管理+智能出题 |
| http://127.0.0.1:8000/docs | 后端API文档 | 查看所有API接口 |

> ⭐ **推荐使用**: `http://localhost:5173/?mode=old` 访问完整功能

---

### ⚠️ 常见问题

#### Q1: 首次安装很慢？
**A**: 正常现象。Python依赖（尤其是Pix2Text和OpenCV）下载较大，需要5-10分钟。建议保持网络畅通。

#### Q2: 端口被占用？
**A**: 如果8000或5173端口被占用：
```bash
# 后端改用其他端口
uvicorn main_simple:app --reload --port 8001

# 前端会自动选择可用端口
```

#### Q3: 虚拟环境激活失败？
**A**: Windows PowerShell可能需要执行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Q4: 找不到 .env 文件？
**A**: 手动在 `backend/` 目录下创建文本文件，命名为 `.env`（注意开头有点）

---

## 🏗️ 技术架构

### 技术栈

**前端**
- React 18 + TypeScript
- Vite（构建工具）
- MathJax（LaTeX渲染）
- Marked（Markdown解析）
- Axios（HTTP客户端）

**后端**
- FastAPI（Web框架）
- Pix2Text（OCR识别）
- OpenCV（图像处理）
- 通义千问（qwen-vl-max）
- JSON文件存储

### 核心技术

#### 混合输入架构
```
用户上传图片
    ↓
OCR识别文本 ─────┐
                 ├─→ AI分析 → 生成回答
原始图片 ────────┘
```

**优势**：结合文字识别和视觉理解，识别准确率显著提升

#### 自动错题保存
```
AI批改 → 检测错误 → 提取知识点 → 推测学科 → 保存JSON
```

#### LaTeX公式渲染
```
Markdown + LaTeX → marked.parse() → HTML → MathJax → 数学公式
```

**示例**：`$(1+x)^{2n+1}$` → (1+x)²ⁿ⁺¹

---

## 📊 项目结构

```
ai-solver-mvp/
├── backend/
│   ├── main_simple.py          # FastAPI主应用
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
│       └── package.json
├── 【启动】简化版错题本系统.bat  # 一键启动
├── 沐梧AI解题系统_技术文档.md    # 完整技术文档
├── 【快速参考】技术架构速查.md   # 快速参考
└── README.md                    # 本文件
```

---

## 📚 文档

### 用户文档
- [【必看】V24.5白屏调试指南](【必看】V24.5白屏调试指南.md) - 使用指南和故障排查
- [【立即测试】V24.4修复验证](【立即测试】V24.4修复验证.md) - 功能测试清单

### 技术文档
- [**沐梧AI解题系统_技术文档**](沐梧AI解题系统_技术文档.md) - 完整技术文档（80KB+）
- [【快速参考】技术架构速查](【快速参考】技术架构速查.md) - 技术架构速查表

### 版本更新
- [V24.6_生成题目超时与LaTeX渲染修复](V24.6_生成题目超时与LaTeX渲染修复.md)
- [V24.5_全面错误捕获与日志增强](V24.5_全面错误捕获与日志增强.md)
- [V24.4_历史记录白屏与错题过滤修复](V24.4_历史记录白屏与错题过滤修复.md)

---

## 🎯 使用示例

### 解题模式

```typescript
// 1. 用户上传题目图片
// 2. 系统进行OCR识别
// 3. 构建混合输入（文本+图片）
// 4. 调用AI生成详细解答
// 5. Markdown格式化显示，LaTeX公式渲染
```

**效果**：详细的解题步骤和思路，支持追问

### 批改模式

```typescript
// 1. 用户上传题目+答案图片
// 2. AI批改，检测对错
// 3. 如果错误：
//    - AI提取知识点（如"二项式定理"）
//    - 推测学科（如"数学"）
//    - 自动保存到错题本
// 4. 返回批改结果和错题保存提示
```

**效果**：自动化错题管理，无需手动整理

### 智能出题

```typescript
// 1. 用户选择错题或知识点
// 2. 配置生成参数（数量、难度、题型）
// 3. AI分析错题特征
// 4. 生成相似的练习题（含答案和解析）
// 5. 支持导出为PDF
```

**效果**：个性化练习，针对性训练薄弱点

---

## 🔧 常见问题

### Q: OCR识别不准确怎么办？
**A**: 确保图片清晰，避免手写字迹过于潦草。系统会同时发送原图给AI，即使OCR不准确，AI也能通过视觉理解识别。

### Q: 生成题目很慢怎么办？
**A**: 这是正常现象，AI生成题目需要时间。系统已延长超时到10分钟，请耐心等待。建议单次生成3-5道题。

### Q: LaTeX公式不显示？
**A**: 检查网络连接（MathJax从CDN加载），等待页面完全加载，或刷新页面（Ctrl+F5）。

### Q: 数据存储在哪里？
**A**: 所有数据存储在本地JSON文件（`backend/mistakes.json`, `backend/questions.json`），完全本地化，不上传云端。

---

## 📈 性能指标

| 操作 | 时间 |
|------|------|
| 图片上传 | < 1秒 |
| OCR识别 | 2-5秒 |
| AI解题 | 10-30秒 |
| 生成题目（单题） | 30-60秒 |
| 生成试卷（10题） | 3-5分钟 |

---

## 🔒 安全性

- ✅ **数据本地化**：所有数据存储在本地，不上传云端
- ✅ **API Key保护**：存储在.env文件，不提交到Git
- ✅ **CORS配置**：生产环境建议限制域名
- ✅ **无用户系统**：无需注册登录，简化部署

---

## 🛠️ 开发指南

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt  # 后端
npm install  # 前端

# 启动开发服务器
uvicorn main_simple:app --reload  # 后端（自动重载）
npm run dev  # 前端（热更新）
```

### 代码规范

- **Python**: PEP 8
- **TypeScript**: ESLint + Prettier
- **提交规范**: 
  - `feat:` 新功能
  - `fix:` 修复bug
  - `docs:` 文档更新

---

## 🗺️ 路线图

### 已完成 ✅
- [x] AI智能解题
- [x] AI批改作业
- [x] 自动错题保存
- [x] 智能错题本
- [x] AI智能出题
- [x] LaTeX公式渲染
- [x] 混合输入架构
- [x] 错误处理体系

### 计划中 📝
- [ ] 错题打印功能
- [ ] 学习报告生成
- [ ] 多用户支持
- [ ] 云端同步（可选）
- [ ] 移动端适配

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [通义千问](https://tongyi.aliyun.com/) - AI大模型支持
- [Pix2Text](https://github.com/breezedeus/pix2text) - OCR识别引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化Web框架
- [React](https://reactjs.org/) - 前端框架
- [MathJax](https://www.mathjax.org/) - LaTeX渲染引擎

---

## 📞 联系方式

- **项目名称**: 沐梧AI解题系统
- **版本**: V24.6
- **最后更新**: 2025-10-20

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by 沐梧团队

</div>

