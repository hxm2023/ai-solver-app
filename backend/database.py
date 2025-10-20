# ==============================================================================
# database.py - 数据库连接管理
# 功能：SQLAlchemy引擎、会话管理
# 技术：SQLAlchemy + SQLite
# ==============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# 数据库文件路径
DATABASE_URL = "sqlite:///./muwu_ai.db"

# 创建SQLAlchemy引擎
# check_same_thread=False: 允许多线程访问（SQLite默认限制）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # 设置为True可以看到SQL语句日志
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==============================================================================
# 数据库会话依赖（FastAPI Dependency）
# ==============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖函数）
    
    这是一个生成器函数，用于FastAPI的依赖注入。
    它确保每个请求使用独立的数据库会话，
    并在请求结束后自动关闭会话。
    
    用法示例：
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    
    Yields:
        数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================================
# 数据库初始化
# ==============================================================================

def init_db():
    """
    初始化数据库
    创建所有表（如果不存在）
    """
    from models import Base, init_database
    
    print("\n" + "="*70)
    print("【数据库初始化】沐梧AI - 个性化学习系统")
    print("="*70)
    
    # 检查数据库文件是否已存在
    db_file = DATABASE_URL.replace("sqlite:///./", "")
    if os.path.exists(db_file):
        print(f"[数据库] 数据库文件已存在: {db_file}")
    else:
        print(f"[数据库] 创建新数据库文件: {db_file}")
    
    # 创建所有表
    init_database(engine)
    
    print("="*70)
    print("【数据库初始化】[OK] 完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 直接运行此文件时初始化数据库
    init_db()
    print("✅ 数据库初始化成功！")
    print(f"📁 数据库文件: {DATABASE_URL}")

