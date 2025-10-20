# ==============================================================================
# auth.py - 用户认证工具
# 功能：JWT token生成和验证、用户认证依赖
# 技术：python-jose, FastAPI依赖注入
# ==============================================================================

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import User
from database import get_db

# JWT配置
SECRET_KEY = "muWuAI_SECRET_KEY_2024_CHANGE_THIS_IN_PRODUCTION"  # 生产环境需要更换
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天有效期

# OAuth2密码模式（用于获取token）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ==============================================================================
# JWT Token相关函数
# ==============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据（通常包含用户ID和用户名）
        expires_delta: 过期时间增量
        
    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # 编码生成token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码JWT令牌
    
    Args:
        token: JWT token字符串
        
    Returns:
        解码后的payload数据
        
    Raises:
        HTTPException: token无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==============================================================================
# 用户认证依赖（FastAPI Dependency）
# ==============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户（依赖函数）
    
    这个函数会被FastAPI的依赖注入系统调用。
    它从请求头的Authorization Bearer token中提取用户信息。
    
    Args:
        token: JWT token（自动从请求头提取）
        db: 数据库会话（自动注入）
        
    Returns:
        当前登录的User对象
        
    Raises:
        HTTPException: token无效或用户不存在
    """
    # 解码token
    payload = decode_access_token(token)
    
    # 从payload中提取用户名
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库查询用户
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前激活的用户（可扩展用于检查用户状态）
    
    Args:
        current_user: 当前用户（依赖注入）
        
    Returns:
        当前用户
    """
    # 这里可以添加额外的用户状态检查
    # 例如：检查用户是否被禁用、是否需要验证邮箱等
    
    return current_user


def require_teacher(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    要求教师权限的依赖函数
    
    Args:
        current_user: 当前用户
        
    Returns:
        教师用户
        
    Raises:
        HTTPException: 如果用户不是教师
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user


# ==============================================================================
# 密码验证辅助函数
# ==============================================================================

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户名和密码
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 明文密码
        
    Returns:
        验证成功返回User对象，失败返回None
    """
    # 查询用户
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    # 验证密码
    if not user.verify_password(password):
        return None
    
    return user

