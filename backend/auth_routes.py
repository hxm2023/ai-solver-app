# ==============================================================================
# auth_routes.py - 用户认证API路由 (Feature 1)
# 功能：注册、登录、获取当前用户信息
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timedelta

from database import get_db
from models import User
from auth import (
    create_access_token,
    get_current_active_user,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# 创建路由器
router = APIRouter(prefix="/auth", tags=["用户认证"])


# ==============================================================================
# Pydantic数据模型
# ==============================================================================

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[str] = Field(None, description="邮箱（可选）")
    role: str = Field("student", description="角色：student或teacher")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """验证用户名只包含字母、数字和下划线"""
        if not v.replace('_', '').isalnum():
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('role')
    def role_valid(cls, v):
        """验证角色值"""
        if v not in ['student', 'teacher']:
            raise ValueError('角色只能是student或teacher')
        return v


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """JWT token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 有效期（秒）
    user_info: dict  # 用户信息


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str]
    role: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==============================================================================
# API端点
# ==============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    用户注册
    
    功能：
    - 创建新用户账户
    - 密码自动加密存储
    - 检查用户名是否已存在
    """
    print(f"\n[注册] 收到注册请求: username={user_data.username}, role={user_data.role}")
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        print(f"[注册] ❌ 用户名已存在: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )
    
    # 检查邮箱是否已存在（如果提供了邮箱）
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            print(f"[注册] ❌ 邮箱已存在: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        hashed_password=User.get_password_hash(user_data.password),
        email=user_data.email,
        role=user_data.role,
        created_at=datetime.utcnow()
    )
    
    # 保存到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"[注册] ✅ 用户注册成功: id={new_user.id}, username={new_user.username}")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录
    
    功能：
    - 验证用户名和密码
    - 生成JWT token
    - 返回用户信息
    """
    print(f"\n[登录] 收到登录请求: username={user_data.username}")
    
    # 验证用户
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        print(f"[登录] ❌ 登录失败: 用户名或密码错误")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 生成JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    print(f"[登录] ✅ 登录成功: id={user.id}, username={user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 转换为秒
        "user_info": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录（OAuth2标准表单格式）
    
    这个端点使用标准的OAuth2密码模式，
    与FastAPI的OAuth2PasswordBearer兼容。
    Swagger文档会自动识别并提供"Authorize"按钮。
    """
    print(f"\n[登录表单] 收到登录请求: username={form_data.username}")
    
    # 验证用户
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        print(f"[登录表单] ❌ 登录失败")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 生成JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    print(f"[登录表单] ✅ 登录成功: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_info": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    获取当前登录用户信息
    
    这是一个受保护的端点，需要JWT认证。
    用于前端验证token有效性和获取用户信息。
    """
    print(f"[获取用户信息] user_id={current_user.id}, username={current_user.username}")
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    用户登出
    
    注意：由于使用JWT，token在客户端存储，
    服务端无法真正"撤销"token（除非引入token黑名单机制）。
    这个端点主要用于记录日志和通知前端删除token。
    """
    print(f"[登出] user_id={current_user.id}, username={current_user.username}")
    
    return {
        "message": "登出成功",
        "tip": "请在客户端删除token"
    }


@router.get("/test-protected")
async def test_protected_route(current_user: User = Depends(get_current_active_user)):
    """
    测试受保护的路由
    用于验证JWT认证是否正常工作
    """
    return {
        "message": "认证成功！这是一个受保护的路由。",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        }
    }

