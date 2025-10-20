# ==============================================================================
# models.py - 数据库模型定义
# 功能：用户认证、错题本、知识点等数据模型
# 技术：SQLAlchemy ORM + SQLite
# ==============================================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from passlib.context import CryptContext

# 密码哈希上下文（使用bcrypt算法）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SQLAlchemy基类
Base = declarative_base()


# ==============================================================================
# 用户模型 (Feature 1)
# ==============================================================================

class User(Base):
    """
    用户模型
    
    功能：
    - 用户注册和登录
    - 存储用户基本信息
    - 密码安全哈希存储
    """
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户名（唯一，索引）
    username = Column(String(50), unique=True, index=True, nullable=False)
    
    # 密码哈希值（不存储明文密码）
    hashed_password = Column(String(255), nullable=False)
    
    # 邮箱（可选，用于找回密码）
    email = Column(String(100), unique=True, nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 最后登录时间
    last_login = Column(DateTime, nullable=True)
    
    # 用户角色（student=学生, teacher=教师）
    role = Column(String(20), default="student")
    
    # 关系：一个用户有多个错题
    mistakes = relationship("Mistake", back_populates="owner", cascade="all, delete-orphan")
    
    # 关系：一个用户有多个生成的题目
    generated_questions = relationship("GeneratedQuestion", back_populates="creator", cascade="all, delete-orphan")
    
    def verify_password(self, plain_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


# ==============================================================================
# 错题模型 (Feature 2)
# ==============================================================================

class Mistake(Base):
    """
    错题模型
    
    功能：
    - 存储用户的错题记录
    - 关联题目图片和AI分析
    - 支持知识点标签
    """
    __tablename__ = "mistakes"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 所属用户（外键）
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 题目原始图片（Base64编码）
    original_image_base64 = Column(Text, nullable=True)
    
    # 题目文字内容（OCR识别结果或用户输入）
    question_text = Column(Text, nullable=False)
    
    # 学生的错误答案
    wrong_answer = Column(Text, nullable=True)
    
    # AI的批改分析和正确解法
    ai_analysis = Column(Text, nullable=False)
    
    # 学科分类（数学、物理、化学等）
    subject = Column(String(50), nullable=True, index=True)
    
    # 知识点标签（JSON格式存储，如：'["函数", "导数"]'）
    knowledge_points = Column(Text, nullable=True)
    
    # 难度等级（1-5）
    difficulty = Column(Integer, nullable=True)
    
    # 是否已复习
    reviewed = Column(Boolean, default=False)
    
    # 复习次数
    review_count = Column(Integer, default=0)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 最后复习时间
    last_reviewed_at = Column(DateTime, nullable=True)
    
    # 关系：多个错题属于一个用户
    owner = relationship("User", back_populates="mistakes")
    
    def __repr__(self):
        return f"<Mistake(id={self.id}, owner_id={self.owner_id}, subject='{self.subject}')>"


# ==============================================================================
# 生成题目模型 (Feature 3)
# ==============================================================================

class GeneratedQuestion(Base):
    """
    AI生成的题目模型
    
    功能：
    - 存储AI生成的练习题
    - 记录生成来源（基于哪些知识点）
    - 支持组卷
    """
    __tablename__ = "generated_questions"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 创建者（外键）
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 题目类型（选择题、填空题、解答题等）
    question_type = Column(String(50), nullable=False)
    
    # 题目内容（JSON格式，包含题干、选项等）
    # 例如：{"stem": "...", "options": ["A", "B", "C", "D"], "answer": "C"}
    content = Column(Text, nullable=False)
    
    # 正确答案
    answer = Column(Text, nullable=False)
    
    # 详细解析
    explanation = Column(Text, nullable=True)
    
    # 关联的知识点（JSON格式）
    knowledge_points = Column(Text, nullable=False)
    
    # 难度（简单、中等、困难）
    difficulty = Column(String(20), nullable=False)
    
    # 学科
    subject = Column(String(50), nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 是否已用于试卷
    used_in_paper = Column(Boolean, default=False)
    
    # 关系：多个题目属于一个创建者
    creator = relationship("User", back_populates="generated_questions")
    
    def __repr__(self):
        return f"<GeneratedQuestion(id={self.id}, type='{self.question_type}', difficulty='{self.difficulty}')>"


# ==============================================================================
# 试卷模型 (Feature 4)
# ==============================================================================

class TestPaper(Base):
    """
    试卷模型
    
    功能：
    - 存储生成的试卷
    - 记录试卷包含的题目
    - 支持学生版和教师版
    """
    __tablename__ = "test_papers"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 创建者（外键）
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 试卷标题
    title = Column(String(200), nullable=False)
    
    # 包含的题目ID列表（JSON格式）
    question_ids = Column(Text, nullable=False)
    
    # 总分
    total_score = Column(Float, nullable=False)
    
    # 考试时长（分钟）
    duration_minutes = Column(Integer, nullable=True)
    
    # 学科
    subject = Column(String(50), nullable=True)
    
    # PDF文件路径（学生版）
    student_pdf_path = Column(String(500), nullable=True)
    
    # PDF文件路径（教师版）
    teacher_pdf_path = Column(String(500), nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TestPaper(id={self.id}, title='{self.title}')>"


# ==============================================================================
# 数据库初始化函数
# ==============================================================================

def init_database(engine):
    """
    初始化数据库
    创建所有表
    """
    print("\n[数据库初始化] 正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("[数据库初始化] [OK] 所有表创建完成")
    print(f"[数据库初始化] 表列表: {list(Base.metadata.tables.keys())}")

