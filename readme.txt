这份文档将分为三个部分：
1.  **快速启动指南**：给已经配置好环境的你，明天回来如何快速恢复工作。
2.  **环境重置指南**：介绍如何安全地“格式化”环境并重新开始。
3.  **全新部署指南**：给一个拿到代码的全新同学，如何从零开始把项目跑起来。
4.安装新的包和更新requirements.txt
---

### **AI拍照解题项目 - 运行与部署说明文档**

**项目简介**:
本项目是一个基于AI大语言模型的拍照解题应用（MVP）。用户上传题目图片，后端通过`Pix2Text`识别图片中的文字与公式，调用Kimi AI大模型获取解答，最终在前端`React`界面上展示出来。

**技术栈**:
- **后端**: Python, FastAPI, Pix2Text, Kimi AI ,通义千问
- **前端**: React (Vite), TypeScript, Axios, KaTeX

---

### **第一部分：快速启动指南 (给已经配置好的你)**

假设你昨天已经成功运行了项目，现在需要重新启动它。

**1. 启动后端服务:**

   a. **打开终端** (推荐使用VS Code的集成终端)。

   b. **导航到后端目录**:
      ```bash
      cd path/to/your/project/ai-solver-mvp/backend
      例如cd "C:\Users\hxm\有用的东西\ai-solver-mvp\backend"
      ```

   c. **激活Python虚拟环境**:
      ```bash
      # Windows
      .\venv\Scripts\activate
      # macOS / Linux
      source venv/bin/activate
      ```
      *(确保命令行提示符前出现 `(venv)`)*

   d. **启动FastAPI服务器**:
      ```bash
      uvicorn main:app --reload
      ```
   *后端服务现已在 `http://127.0.0.1:8000` 运行。请保持此终端窗口开启。*

**2. 启动前端服务:**

   a. **打开一个新的终端窗口**。

   b. **导航到前端目录**:
      ```bash
      cd path/to/your/project/ai-solver-mvp/frontend/vite-project
      例如cd "C:\Users\hxm\有用的东西\ai-solver-mvp\frontend\vite-project"
      ```

   c. **启动Vite开发服务器**:
      ```bash
      npm run dev
      ```
   *前端服务现已在 `http://localhost:5173` (或类似地址) 运行。*

**3. 访问应用:**
   在浏览器中打开 `http://localhost:5173` 即可开始使用。

---

### **第二部分：环境重置指南 (如何“格式化”并重装)**

有时候你想从一个干净的环境重新开始。

**1. 可以安全删除的文件/文件夹:**

   - **`backend/venv/`**: 这是Python的虚拟环境文件夹。删除它会移除所有下载的Python库，但不会影响你的源代码。
   - **`frontend/vite-project/node_modules/`**: 这是Node.js的项目依赖文件夹。删除它会移除所有下载的前端库。
   - **`C:\Users\YourUsername\AppData\Roaming\pix2text\`**: 这是`Pix2Text`下载的模型缓存。删除后，下次运行时会自动重新下载。

   **警告：绝对不要删除以下文件！**
   - `backend/main.py`
   - `backend/requirements.txt`
   - `backend/.env`
   - `frontend/vite-project/` 目录下的 `src/` 文件夹, `package.json`, `index.html` 等你编写或配置过的核心文件。

**2. 如何重置并重新安装:**

   a. **删除虚拟环境**: 手动在文件管理器中删除 `backend/venv` 文件夹。

   b. **创建新的虚拟环境**:
      - 打开终端，进入 `backend` 目录。
      - `python -m venv venv`

   c. **激活新的虚拟环境**:
      - `.\venv\Scripts\activate`

   d. **一键安装所有后端依赖**:
      - `pip install -r requirements.txt`
（更新requirements.txt:  pip freeze > requirements.txt）
   e. **重置前端依赖**:
      - (可选) 手动删除 `frontend/vite-project/node_modules` 文件夹。
      - 打开新终端，进入 `frontend/vite-project` 目录。
      - `npm install`

   f. **按照【快速启动指南】启动前后端服务即可。**

---

### **第三部分：全新部署指南 (给拿到项目的新同学)**

一位新同学拿到了你的项目代码压缩包，他/她需要按以下步骤从零开始运行。

**前提条件：**
- 电脑已安装 **Python** (版本 3.8+)。
- 电脑已安装 **Node.js** (LTS 长期支持版)。
- 已获得 **KimiAI和通义千问的API Key**。（在后端的.env里有）

**步骤 1: 项目设置**

   a. **解压项目**: 将项目代码解压到电脑任意位置。

   b. **配置API Key**:
      - 进入 `backend` 目录。
      - 找到 `.env.example` 文件（如果提供了），将其**重命名**为 `.env`。
      - 打开 `.env` 文件，将你的AI API Key填入：
        ```
       

**步骤 2: 搭建并运行后端**

   a. **打开终端**，导航到 `backend` 目录。

   b. **创建并激活虚拟环境**:
      ```bash
      python -m venv venv
      .\venv\Scripts\activate
      ```

   c. **安装后端所有依赖**:
      ```bash
      pip install -r requirements.txt
      ```
      *(这一步会自动安装FastAPI, Pillow, Pix2Text等所有必需的库)*

   d. **启动后端服务器**:
      ```bash
      uvicorn main:app --reload
      ```
      *看到 `Uvicorn running on http://127.0.0.1:8000` 后，保持此窗口开启。*
      *首次运行时，`Pix2Text`会自动下载AI模型，可能需要几分钟，请耐心等待。*

**步骤 3: 搭建并运行前端**

   a. **打开一个新的终端**，导航到 `frontend/vite-project` 目录。

   b. **安装前端所有依赖**:
      ```bash
      npm install
      ```
      *(这一步会根据 `package.json` 文件下载React, Axios等所有库)*

   c. **启动前端开发服务器**:
      ```bash
      npm run dev
      ```
      *看到 `Local: http://localhost:5173/` 后，前端启动成功。*

**步骤 4: 访问和测试**

   a. 在浏览器中打开 `http://localhost:5173`。
   b. 上传一张题目图片，验证整个流程是否正常工作。

---
这份文档应该足够详尽了，无论是你自己继续开发，还是交接给其他同学，都能提供清晰的指引。祝你今天下班愉快！```
<<<<<<< HEAD

四。
**1. 启动后端服务:**

   a. **打开终端** (推荐使用VS Code的集成终端)。

   b. **导航到后端目录**:
      ```bash
      cd path/to/your/project/ai-solver-mvp/backend
      cd "C:\Users\hxm\有用的东西\ai-solver-mvp\backend"
      ```

   c. **激活Python虚拟环境**:
      ```bash
      # Windows
      .\venv\Scripts\activate
      # macOS / Linux
      source venv/bin/activate
      ```
      *(确保命令行提示符前出现 `(venv)`)*
d. 安装或者卸载某些包
pip install opencv-python-headless    pip uninstall some-old-package
在前端安装，就在你的前端终端（frontend/vite-project目录下）运行，例如npm install marked
npm install @types/marked --save-dev # 安装类型定义
e.更新清单pip freeze > requirements.txt
=======
>>>>>>> dde465c82517162418fff510524005c434406521
