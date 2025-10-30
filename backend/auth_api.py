"""
==============================================================================
沐梧AI解题系统 - 用户认证API (V25.1)
==============================================================================
功能：
- 用户注册
- 用户登录
- JWT令牌生成与验证
- 认证中间件
==============================================================================
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
from database import UserManager

# ==============================================================================
# 配置
# ==============================================================================

# JWT配置
JWT_SECRET_KEY = "muwu_ai_solver_secret_key_2024"  # 生产环境应使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7天有效期

# ==============================================================================
# 数据模型
# ==============================================================================

class RegisterRequest(BaseModel):
    """注册请求"""
    account: str
    password: str

class LoginRequest(BaseModel):
    """登录请求"""
    account: str
    password: str

class AuthResponse(BaseModel):
    """认证响应"""
    success: bool
    message: str
    token: Optional[str] = None
    user_id: Optional[str] = None
    account: Optional[str] = None

class LoginResponse(BaseModel):
    """登录响应（前端兼容格式）"""
    access_token: str
    token_type: str = "bearer"
    user_info: dict

# ==============================================================================
# JWT令牌工具函数
# ==============================================================================

def create_access_token(user_id: str, account: str) -> str:
    """
    创建JWT访问令牌
    
    Args:
        user_id: 用户ID
        account: 用户账号
    
    Returns:
        JWT令牌字符串
    """
    from datetime import timezone
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "account": account,
        "exp": expire
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> dict:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        解码后的payload字典
    
    Raises:
        HTTPException: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")


async def get_current_user(authorization: Optional[str] = Header(None, alias="Authorization")) -> dict:
    """
    依赖注入：获取当前登录用户
    
    用法：
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    
    Args:
        authorization: HTTP请求头中的Authorization字段
    
    Returns:
        用户信息字典 {"user_id": str, "account": str}
    
    Raises:
        HTTPException: 未提供令牌或令牌无效
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    # 解析 "Bearer <token>" 格式
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="无效的认证格式")
    
    token = parts[1]
    payload = verify_access_token(token)
    
    return {
        "user_id": payload["user_id"],
        "account": payload["account"]
    }


# ==============================================================================
# API路由
# ==============================================================================

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """
    用户注册
    
    请求体:
        {
            "account": "用户账号",
            "password": "密码"
        }
    
    响应:
        {
            "success": true,
            "message": "注册成功",
            "token": "JWT令牌",
            "user_id": "用户ID",
            "account": "用户账号"
        }
    """
    # 调用数据库管理器
    result = UserManager.register(request.account, request.password)
    
    if result["success"]:
        # 注册成功，自动登录，生成令牌
        token = create_access_token(result["user_id"], request.account)
        return AuthResponse(
            success=True,
            message=result["message"],
            token=token,
            user_id=result["user_id"],
            account=request.account
        )
    else:
        # 注册失败
        return AuthResponse(
            success=False,
            message=result["message"]
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    请求体:
        {
            "account": "用户账号",
            "password": "密码"
        }
    
    响应:
        {
            "access_token": "JWT令牌",
            "token_type": "bearer",
            "user_info": {
                "user_id": "用户ID",
                "account": "用户账号",
                "nickname": "昵称"
            }
        }
    """
    # 调用数据库管理器
    result = UserManager.login(request.account, request.password)
    
    if result["success"]:
        # 登录成功，生成令牌
        token = create_access_token(result["user_id"], result["account"])
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user_info={
                "user_id": result["user_id"],
                "account": result["account"],
                "nickname": result.get("nickname", result["account"])
            }
        )
    else:
        # 登录失败
        raise HTTPException(status_code=401, detail=result["message"])


@router.get("/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    """
    验证令牌有效性
    
    请求头:
        Authorization: Bearer <JWT令牌>
    
    响应:
        {
            "valid": true,
            "user_id": "用户ID",
            "account": "用户账号"
        }
    """
    return {
        "valid": True,
        "user_id": user["user_id"],
        "account": user["account"]
    }


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    请求头:
        Authorization: Bearer <JWT令牌>
    
    响应:
        {
            "user_id": "用户ID",
            "account": "用户账号"
        }
    """
    user_info = UserManager.get_user_info(user["user_id"])
    
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="用户不存在")


# ==============================================================================
# 测试代码
# ==============================================================================

if __name__ == "__main__":
    # 测试令牌生成
    token = create_access_token("test_user_123", "testuser")
    print(f"生成的令牌: {token}")
    
    # 测试令牌验证
    try:
        payload = verify_access_token(token)
        print(f"令牌验证成功: {payload}")
    except Exception as e:
        print(f"令牌验证失败: {e}")

