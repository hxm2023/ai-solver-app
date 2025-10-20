# Feature 1: 用户认证系统完整文档 (V23.0)

## 📋 功能概述

**用户故事**：  
作为一个学生，我希望能注册一个账户并登录，以便系统能安全地保存我所有的学习数据。

**实现功能**：
- ✅ 用户注册（学生/教师）
- ✅ 用户登录（JWT token）
- ✅ 密码安全哈希存储（bcrypt）
- ✅ JWT认证保护路由
- ✅ 获取当前用户信息
- ✅ 角色权限控制

---

## 🏗️ 架构设计

### 技术栈
```
后端：FastAPI + SQLAlchemy + SQLite
认证：JWT (JSON Web Token)
密码：bcrypt哈希
ORM：SQLAlchemy
数据库：SQLite（开发环境）
```

### 文件结构
```
backend/
  ├── models.py              # 数据库模型（User, Mistake等）
  ├── database.py            # 数据库连接管理
  ├── auth.py                # JWT认证工具
  ├── auth_routes.py         # 认证API路由
  ├── main.py                # 主应用（已修改）
  ├── requirements.txt       # 依赖清单（已更新）
  ├── test_feature1_auth.py  # 测试脚本
  └── muwu_ai.db             # SQLite数据库文件（运行后自动生成）
```

---

## 📊 数据库模型

### User模型
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    email = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    role = Column(String(20), default="student")  # student或teacher
    
    # 关系
    mistakes = relationship("Mistake", back_populates="owner")
    generated_questions = relationship("GeneratedQuestion", back_populates="creator")
```

**字段说明**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键，自动递增 |
| `username` | String(50) | 用户名，唯一索引 |
| `hashed_password` | String(255) | bcrypt哈希后的密码 |
| `email` | String(100) | 邮箱（可选） |
| `created_at` | DateTime | 注册时间 |
| `last_login` | DateTime | 最后登录时间 |
| `role` | String(20) | 角色：student/teacher |

---

## 🔌 API接口

### 1. 用户注册
```http
POST /auth/register
Content-Type: application/json

{
  "username": "test_student",
  "password": "password123",
  "email": "student@test.com",
  "role": "student"
}
```

**响应（成功）**：
```json
{
  "id": 1,
  "username": "test_student",
  "email": "student@test.com",
  "role": "student",
  "created_at": "2025-10-18T12:00:00",
  "last_login": null
}
```

**响应（失败）**：
```json
{
  "detail": "用户名已被注册"
}
```

### 2. 用户登录
```http
POST /auth/login
Content-Type: application/json

{
  "username": "test_student",
  "password": "password123"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user_info": {
    "id": 1,
    "username": "test_student",
    "email": "student@test.com",
    "role": "student"
  }
}
```

### 3. 获取当前用户信息（受保护）
```http
GET /auth/me
Authorization: Bearer <token>
```

**响应**：
```json
{
  "id": 1,
  "username": "test_student",
  "email": "student@test.com",
  "role": "student",
  "created_at": "2025-10-18T12:00:00",
  "last_login": "2025-10-18T12:30:00"
}
```

### 4. 登出
```http
POST /auth/logout
Authorization: Bearer <token>
```

**响应**：
```json
{
  "message": "登出成功",
  "tip": "请在客户端删除token"
}
```

---

## 🔐 JWT认证流程

### 认证流程图
```
1. 用户登录 → 后端验证
   ↓
2. 生成JWT token（包含用户ID和用户名）
   ↓
3. 前端保存token到localStorage
   ↓
4. 后续请求携带token（Authorization: Bearer <token>）
   ↓
5. 后端验证token → 提取用户信息 → 执行业务逻辑
```

### JWT Payload示例
```json
{
  "sub": "test_student",      // 用户名
  "user_id": 1,                // 用户ID
  "exp": 1729526400            // 过期时间（Unix时间戳）
}
```

### 认证依赖使用
```python
# 在需要认证的路由中
@router.get("/mistakes")
async def get_my_mistakes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # current_user 自动注入当前登录用户
    mistakes = db.query(Mistake).filter(
        Mistake.owner_id == current_user.id
    ).all()
    return mistakes
```

---

## 🚀 快速开始

### 步骤1：安装依赖
```bash
cd backend
pip install sqlalchemy==2.0.23 passlib[bcrypt]==1.7.4 python-jose[cryptography]==3.3.0
```

### 步骤2：初始化数据库
```bash
# 方法1：直接运行database.py
python database.py

# 方法2：启动服务时自动初始化
uvicorn main:app --reload
```

### 步骤3：测试API
```bash
# 运行测试脚本
python test_feature1_auth.py

# 或访问Swagger文档
浏览器打开：http://127.0.0.1:8000/docs
```

### 步骤4：注册第一个用户
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "teacher"
  }'
```

---

## 💻 前端集成指南

### 1. 创建Auth上下文（React）
```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  email?: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, password: string, email?: string) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('access_token')
  );

  // 配置axios拦截器
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // 验证token并获取用户信息
      fetchUserInfo();
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/auth/me');
      setUser(response.data);
    } catch (error) {
      // Token无效，清除
      logout();
    }
  };

  const login = async (username: string, password: string) => {
    const response = await axios.post('http://127.0.0.1:8000/auth/login', {
      username,
      password
    });
    
    const { access_token, user_info } = response.data;
    
    setToken(access_token);
    setUser(user_info);
    localStorage.setItem('access_token', access_token);
  };

  const register = async (username: string, password: string, email?: string) => {
    await axios.post('http://127.0.0.1:8000/auth/register', {
      username,
      password,
      email,
      role: 'student'
    });
    
    // 注册成功后自动登录
    await login(username, password);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      register,
      isAuthenticated: !!token
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### 2. 创建登录组件
```typescript
// src/components/LoginForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export const LoginForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await login(username, password);
      // 登录成功，跳转到主页
    } catch (err: any) {
      setError(err.response?.data?.detail || '登录失败');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h2>登录</h2>
      
      {error && <div className="error">{error}</div>}
      
      <input
        type="text"
        placeholder="用户名"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      
      <input
        type="password"
        placeholder="密码"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      
      <button type="submit">登录</button>
    </form>
  );
};
```

### 3. 修改App.tsx集成认证
```typescript
// src/App.tsx
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginForm } from './components/LoginForm';

function AppContent() {
  const { isAuthenticated, user, logout } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <div className="App">
      <header>
        <h1>沐梧AI解题系统</h1>
        <div className="user-info">
          <span>欢迎, {user?.username}</span>
          <button onClick={logout}>登出</button>
        </div>
      </header>
      
      {/* 原有的应用内容 */}
      <MainApp />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
```

---

## 🧪 测试指南

### 使用测试脚本
```bash
cd backend
python test_feature1_auth.py
```

**预期输出**：
```
✅ Feature 1 用户认证系统测试完成！

功能验证：
  ✅ 用户注册（学生和教师）
  ✅ 用户登录（JWT token生成）
  ✅ JWT认证（受保护路由）
  ✅ Token验证（有效/无效）
  ✅ 用户信息获取
```

### 使用Swagger UI测试
1. 访问：http://127.0.0.1:8000/docs
2. 点击"Authorize"按钮
3. 输入token（或使用OAuth2表单登录）
4. 测试所有受保护的端点

---

## 🔧 配置说明

### JWT配置（auth.py）
```python
# 密钥（生产环境必须更换！）
SECRET_KEY = "muWuAI_SECRET_KEY_2024_CHANGE_THIS_IN_PRODUCTION"

# 算法
ALGORITHM = "HS256"

# Token有效期（7天）
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
```

### 数据库配置（database.py）
```python
# SQLite数据库文件路径
DATABASE_URL = "sqlite:///./muwu_ai.db"

# 可改为PostgreSQL（生产环境）
# DATABASE_URL = "postgresql://user:password@localhost/muwu_ai"
```

---

## 📊 数据库查看

### 使用SQLite命令行
```bash
# 进入数据库
sqlite3 muwu_ai.db

# 查看所有表
.tables

# 查看用户表结构
.schema users

# 查询所有用户
SELECT * FROM users;

# 退出
.quit
```

### 使用Python脚本
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User

engine = create_engine("sqlite:///./muwu_ai.db")
Session = sessionmaker(bind=engine)
db = Session()

# 查询所有用户
users = db.query(User).all()
for user in users:
    print(f"{user.id}: {user.username} ({user.role})")
```

---

## 🛡️ 安全最佳实践

### 已实现
✅ 密码bcrypt哈希存储  
✅ JWT token有效期控制  
✅ 用户名唯一性检查  
✅ SQL注入防护（SQLAlchemy ORM）  
✅ CORS跨域配置  

### 生产环境建议
⚠️ 更换SECRET_KEY为强随机字符串  
⚠️ 使用HTTPS协议  
⚠️ 实现Token黑名单（登出时撤销）  
⚠️ 添加验证码防暴力破解  
⚠️ 实现邮箱验证和密码找回  
⚠️ 添加API请求频率限制  

---

## 📈 性能指标

| 操作 | 响应时间 | 说明 |
|------|---------|------|
| 注册 | < 100ms | bcrypt哈希计算 |
| 登录 | < 100ms | 数据库查询+JWT生成 |
| 验证token | < 10ms | JWT解码 |

---

## 🎯 下一步：Feature 2

Feature 1完成后，可以继续开发：

**Feature 2: 错题数据库**
- 修改 `/chat` 接口自动保存错题
- 实现 `GET /mistakes` 接口
- 前端显示错题本

详情见：[Feature2_错题数据库文档.md]（待创建）

---

## 📞 技术支持

- **API文档**：http://127.0.0.1:8000/docs
- **测试脚本**：`python test_feature1_auth.py`
- **数据库文件**：`backend/muwu_ai.db`

---

**🎉 Feature 1 用户认证系统已完成！可以开始使用或继续开发Feature 2！**

