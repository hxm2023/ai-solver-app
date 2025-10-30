# 🗄️ 沐梧AI解题系统 V25.1 - MySQL数据库版本

[![Version](https://img.shields.io/badge/version-V25.1-blue.svg)](https://github.com/your-repo)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-5.7+-orange.svg)](https://www.mysql.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

**企业级AI错题管理系统 • MySQL存储 • JWT认证 • 多用户支持**

---

## 🌟 核心特性

### ✅ 已完成功能

- 🔐 **用户认证系统** - JWT令牌机制，SHA256密码加密
- 🗄️ **MySQL数据库** - 连接池管理，事务支持
- 👥 **多用户支持** - 完整的数据隔离
- 📝 **错题本管理** - CRUD完整功能
- 📚 **题目库管理** - 自动分类存储
- 📊 **数据统计** - 实时统计学科、年级、知识点
- 🎨 **现代化UI** - React + TypeScript
- 🔄 **数据迁移** - 平滑从JSON升级

### ⏳ 开发中功能

- 📄 **PDF导出** - 集成Pyppeteer + MathJax
- 🌐 **网络辅助出题** - 集成BeautifulSoup4爬虫
- 🤖 **AI智能出题** - 基于错题生成新题

---

## 🚀 快速开始（3步，共2分钟）

### 第1步：启动系统
双击运行：
```
【启动】数据库版本系统.bat
```

### 第2步：访问前端
浏览器打开：
```
http://localhost:5173/?mode=db
```

### 第3步：登录系统
使用测试账号：
- **账号：** demo_user
- **密码：** demo123456

或点击"立即注册"创建新账号。

**就这么简单！** 🎉

---

## 📚 完整文档导航

### 🔥 必读文档
1. [【必读】V25.1数据库版本快速启动.md](./【必读】V25.1数据库版本快速启动.md) ⭐ **新手推荐**
2. [V25.1_MySQL数据库集成完成报告.md](./V25.1_MySQL数据库集成完成报告.md) - 完整交付报告
3. [V25.1_系统功能速查表.md](./V25.1_系统功能速查表.md) - API/表结构速查

### 📖 技术文档
4. [V25.1_MySQL数据库集成指南.md](./V25.1_MySQL数据库集成指南.md) - 开发者指南
5. [【必读】V25.1快速部署指南.md](./【必读】V25.1快速部署指南.md) - 部署指南
6. [API文档](http://127.0.0.1:8000/docs) - 在线API文档（需启动后端）

### 🔧 运维文档
7. [backend/database_schema_upgrade.sql](./backend/database_schema_upgrade.sql) - 表结构升级
8. [backend/fix_subject_title.sql](./backend/fix_subject_title.sql) - 字段长度修复
9. [backend/clean_migrated_data.sql](./backend/clean_migrated_data.sql) - 数据清理

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                                │
│                  http://localhost:5173/?mode=db                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      前端 (React + TS)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ AuthModal    │  │ SimpleMistake │  │ QuestionItem │          │
│  │ 登录/注册    │  │ BookDB       │  │ (MathJax)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                           ↓                                      │
│                    utils/api.ts (JWT管理)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/JSON + JWT Token
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                                │
│                 http://127.0.0.1:8000                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ main_db.py   │  │ auth_api.py  │  │ database.py  │          │
│  │ (主服务)     │  │ (JWT认证)    │  │ (连接池)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                           ↓                                      │
│                    PyMySQL (连接池)                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQL查询
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MySQL数据库                                    │
│               14.103.127.20:3306/edu                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  user    │  │  exam    │  │ subject  │  │user_exam │       │
│  │  用户表  │  │  试卷表  │  │ 题目表   │  │ 答题记录 │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 数据库设计

### 核心表关系
```
user (用户表)
  ├─ 1:N → user_exam (答题记录)
  └─ 1:N → exam (试卷，通过user_exam关联)

exam (试卷表)
  └─ 1:N → user_exam (答题记录)
            └─ N:1 → subject (题目表)

subject (题目表)
  ├─ subject_type = 'mistake' (错题)
  └─ subject_type = 'generated' (生成题)
```

### 表结构统计
- **user表：** 1个用户（demo_user）
- **exam表：** 2个试卷（错题本 + 练习题集）
- **subject表：** 67条题目（5错题 + 62生成题）
- **user_exam表：** 67条记录（用户-题目关联）

---

## 🔐 API端点一览

### 认证相关（无需令牌）
| 方法 | 端点 | 说明 |
|-----|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录（返回JWT） |

### 错题本（需要JWT令牌）
| 方法 | 端点 | 说明 |
|-----|------|------|
| POST | `/mistakes/` | 创建错题 |
| GET | `/mistakes/` | 获取错题列表 |
| DELETE | `/mistakes/{id}` | 删除错题 |
| GET | `/mistakes/stats/summary` | 获取统计 |

### 题目库（需要JWT令牌）
| 方法 | 端点 | 说明 |
|-----|------|------|
| POST | `/questions/generate` | 生成题目 |
| GET | `/questions/` | 获取题目列表 |
| DELETE | `/questions/{id}` | 删除题目 |

### 用户信息（需要JWT令牌）
| 方法 | 端点 | 说明 |
|-----|------|------|
| GET | `/auth/verify` | 验证令牌 |
| GET | `/auth/me` | 获取当前用户信息 |

---

## 💻 技术栈

### 后端
- **框架：** FastAPI 0.104.1
- **数据库：** MySQL 5.7+ (PyMySQL)
- **认证：** PyJWT 2.8.0
- **密码：** cryptography 41.0.7 (SHA256)
- **AI引擎：** DashScope (Qwen-VL-Max)
- **PDF导出：** Pyppeteer 1.0.2 + MathJax 3
- **网络爬虫：** BeautifulSoup4 4.12.2 + Requests

### 前端
- **框架：** React 18 + TypeScript
- **构建：** Vite 5
- **样式：** CSS3（自定义）
- **数学公式：** MathJax 3
- **Markdown：** marked 9.1.6

### 数据库
- **类型：** MySQL 5.7+
- **编码：** utf8mb4（支持emoji）
- **表数量：** 4张核心表
- **索引：** 9个优化索引

---

## 📦 目录结构

```
ai-solver-mvp/
├── backend/                          # 后端代码
│   ├── main_simple.py                # JSON版本后端（V24.6）
│   ├── main_db.py                    # 数据库版本后端（V25.1）✨
│   ├── database.py                   # 数据库连接模块✨
│   ├── auth_api.py                   # 用户认证API✨
│   ├── migrate_data.py               # 数据迁移脚本✨
│   ├── database_schema_upgrade.sql   # 表结构升级SQL✨
│   ├── requirements.txt              # Python依赖
│   └── venv/                         # 虚拟环境
│
├── frontend/vite-project/            # 前端代码
│   ├── src/
│   │   ├── SimpleMistakeBook.tsx    # JSON版本界面
│   │   ├── SimpleMistakeBookDB.tsx  # 数据库版本界面✨
│   │   ├── components/
│   │   │   ├── QuestionItem.tsx     # 题目组件（LaTeX）
│   │   │   ├── AuthModal.tsx        # 登录/注册组件✨
│   │   │   └── AuthModal.css        # 认证组件样式✨
│   │   └── utils/
│   │       └── api.ts               # API请求工具✨
│   └── package.json                  # 前端依赖
│
├── 【启动】简化版错题本系统.bat      # JSON版本启动
├── 【启动】数据库版本系统.bat        # 数据库版本启动✨
├── 【测试】数据库连接.bat             # 连接测试✨
├── 【测试】用户认证.bat               # 认证测试✨
├── 【执行】数据迁移-简化版.bat        # 数据迁移✨
│
├── V25.1_MySQL数据库集成完成报告.md  # 完整交付报告✨
├── V25.1_系统功能速查表.md            # 速查表✨
├── 【必读】V25.1数据库版本快速启动.md # 快速启动✨
└── README_V25.1.md                    # 本文档✨

✨ 表示V25.1新增文件
```

---

## 🔄 版本对比

| 特性 | V24.6 (JSON版) | V25.1 (数据库版) |
|-----|---------------|----------------|
| 数据存储 | 📄 JSON文件 | 🗄️ MySQL数据库 |
| 用户认证 | ❌ | ✅ JWT令牌 |
| 多用户支持 | ❌ | ✅ 完整隔离 |
| 并发访问 | ⚠️ 有锁问题 | ✅ 事务保证 |
| 数据持久化 | ⚠️ 易丢失 | ✅ 永久存储 |
| 查询性能 | ⚠️ 全表扫描 | ✅ 索引优化 |
| AI解题 | ✅ | ✅ |
| PDF导出 | ✅ | ⏳ 集成中 |
| 网络出题 | ✅ | ⏳ 集成中 |

**建议：** 新用户直接使用V25.1数据库版本！

---

## 🎓 使用场景

### 个人学习
- 记录错题，AI分析
- 生成练习题
- 导出PDF复习

### 班级管理
- 每个学生独立账号
- 老师查看学生数据
- 统计班级薄弱知识点

### 培训机构
- 多用户并发使用
- 数据永久保存
- 学习轨迹追踪

---

## 🐛 故障排查

### 问题1：后端启动失败
**症状：** 点击启动脚本后窗口闪退  
**排查：**
```bash
cd backend
call venv\Scripts\activate.bat
python main_db.py
# 查看错误信息
```

### 问题2：数据库连接失败
**症状：** "数据库连接池初始化失败"  
**排查：**
```bash
【测试】数据库连接.bat
# 检查输出信息
```

### 问题3：前端登录失败
**症状：** 点击登录无反应  
**排查：**
1. F12打开浏览器控制台
2. 查看Network标签的请求
3. 确认后端已启动（http://127.0.0.1:8000）

### 问题4：JWT令牌过期
**症状：** "未授权"错误  
**解决：** 重新登录即可（令牌有效期24小时）

---

## 📞 获取支持

### 📚 文档
- [完整交付报告](./V25.1_MySQL数据库集成完成报告.md)
- [快速启动指南](./【必读】V25.1数据库版本快速启动.md)
- [API速查表](./V25.1_系统功能速查表.md)

### 🔗 在线资源
- [API文档](http://127.0.0.1:8000/docs) - 需启动后端
- [GitHub Issues](https://github.com/your-repo/issues)
- [开发者文档](https://docs.example.com)

### 💬 联系方式
- Email: support@example.com
- QQ群: 123456789
- 微信：your_wechat

---

## 🗓️ 更新日志

### V25.1 (2025-10-25)
- ✅ 新增MySQL数据库支持
- ✅ 新增JWT用户认证
- ✅ 新增多用户数据隔离
- ✅ 新增数据迁移工具
- ✅ 优化前端登录界面
- ✅ 扩展数据库表结构（14个新字段）

### V24.6 (2025-10-XX)
- ✅ PDF导出支持LaTeX
- ✅ 网络辅助智能出题
- ✅ 错题本基础功能

### V24.0 (2025-10-XX)
- ✅ 基础错题管理
- ✅ AI解题功能

---

## 📄 许可证

MIT License

Copyright (c) 2025 沐梧AI团队

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化Web框架
- [React](https://reactjs.org/) - 前端UI框架
- [PyMySQL](https://github.com/PyMySQL/PyMySQL) - MySQL客户端
- [PyJWT](https://pyjwt.readthedocs.io/) - JWT令牌实现
- [MathJax](https://www.mathjax.org/) - 数学公式渲染
- [DashScope](https://dashscope.aliyun.com/) - AI大模型服务

---

## 🚀 下一步计划

### V25.2（短期）
- [ ] 集成PDF导出到数据库版本
- [ ] 集成网络辅助出题到数据库版本
- [ ] 添加题目收藏功能
- [ ] 添加学习进度可视化

### V26.0（中期）
- [ ] 图片存储迁移到OSS
- [ ] 添加题目标签系统
- [ ] 学习计划功能
- [ ] 错题复习提醒

### 长期规划
- [ ] 微信小程序版本
- [ ] 移动端响应式优化
- [ ] 班级/小组协作功能
- [ ] 题目分享社区

---

<div align="center">

**🎉 享受您的V25.1数据库版本体验！**

Made with ❤️ by 沐梧AI团队

[快速开始](./【必读】V25.1数据库版本快速启动.md) •
[完整报告](./V25.1_MySQL数据库集成完成报告.md) •
[API文档](http://127.0.0.1:8000/docs)

</div>

