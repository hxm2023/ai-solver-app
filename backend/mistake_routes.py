# ==============================================================================
# mistake_routes.py - 错题本API路由 (Feature 2)
# 功能：错题的增删改查、复习管理
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json

from database import get_db
from models import User, Mistake
from auth import get_current_active_user

# 创建路由器
router = APIRouter(prefix="/mistakes", tags=["错题本"])


# ==============================================================================
# Pydantic数据模型
# ==============================================================================

class MistakeCreate(BaseModel):
    """创建错题请求"""
    question_text: str = Field(..., description="题目文字内容")
    wrong_answer: Optional[str] = Field(None, description="学生的错误答案")
    ai_analysis: str = Field(..., description="AI的批改分析")
    original_image_base64: Optional[str] = Field(None, description="题目图片Base64")
    subject: Optional[str] = Field("数学", description="学科")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度等级1-5")


class MistakeUpdate(BaseModel):
    """更新错题请求"""
    reviewed: Optional[bool] = Field(None, description="是否已复习")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度等级")


class MistakeResponse(BaseModel):
    """错题响应"""
    id: int
    owner_id: int
    question_text: str
    wrong_answer: Optional[str]
    ai_analysis: str
    subject: Optional[str]
    knowledge_points: Optional[str]  # JSON字符串
    difficulty: Optional[int]
    reviewed: bool
    review_count: int
    created_at: datetime
    last_reviewed_at: Optional[datetime]
    has_image: bool  # 是否有图片
    
    class Config:
        from_attributes = True


class MistakeListResponse(BaseModel):
    """错题列表响应"""
    total: int
    page: int
    page_size: int
    mistakes: List[MistakeResponse]


# ==============================================================================
# API端点
# ==============================================================================

@router.post("/", response_model=MistakeResponse, status_code=status.HTTP_201_CREATED)
async def create_mistake(
    mistake_data: MistakeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    手动创建错题记录
    
    功能：
    - 用户可以手动添加错题
    - 通常由AI批改自动调用
    """
    print(f"\n[错题创建] 收到创建请求")
    print(f"[错题创建] 用户: {current_user.username} (id={current_user.id})")
    print(f"[错题创建] 学科: {mistake_data.subject}")
    print(f"[错题创建] 题目长度: {len(mistake_data.question_text)} 字符")
    
    # 转换知识点列表为JSON字符串
    knowledge_points_json = None
    if mistake_data.knowledge_points:
        knowledge_points_json = json.dumps(mistake_data.knowledge_points, ensure_ascii=False)
        print(f"[错题创建] 知识点: {mistake_data.knowledge_points}")
    
    # 创建错题记录
    new_mistake = Mistake(
        owner_id=current_user.id,
        question_text=mistake_data.question_text,
        wrong_answer=mistake_data.wrong_answer,
        ai_analysis=mistake_data.ai_analysis,
        original_image_base64=mistake_data.original_image_base64,
        subject=mistake_data.subject,
        knowledge_points=knowledge_points_json,
        difficulty=mistake_data.difficulty,
        created_at=datetime.utcnow()
    )
    
    print(f"[错题创建] 正在保存到数据库...")
    db.add(new_mistake)
    db.commit()
    db.refresh(new_mistake)
    
    print(f"[错题创建] ✅ 错题保存成功! id={new_mistake.id}")
    
    # 构建响应（添加has_image字段）
    response = MistakeResponse.from_orm(new_mistake)
    response.has_image = bool(new_mistake.original_image_base64)
    
    return response


@router.get("/", response_model=MistakeListResponse)
async def get_my_mistakes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    subject: Optional[str] = Query(None, description="筛选学科"),
    reviewed: Optional[bool] = Query(None, description="筛选是否已复习"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的错题列表
    
    功能：
    - 分页获取错题
    - 支持按学科筛选
    - 支持按复习状态筛选
    """
    print(f"\n[错题列表] 收到请求")
    print(f"[错题列表] 用户: {current_user.username} (id={current_user.id})")
    print(f"[错题列表] 页码: {page}, 每页: {page_size}")
    print(f"[错题列表] 筛选条件 - 学科: {subject}, 已复习: {reviewed}")
    
    # 构建查询
    query = db.query(Mistake).filter(Mistake.owner_id == current_user.id)
    
    # 应用筛选条件
    if subject:
        query = query.filter(Mistake.subject == subject)
        print(f"[错题列表] 筛选学科: {subject}")
    
    if reviewed is not None:
        query = query.filter(Mistake.reviewed == reviewed)
        print(f"[错题列表] 筛选复习状态: {reviewed}")
    
    # 按创建时间倒序排列（最新的在前）
    query = query.order_by(Mistake.created_at.desc())
    
    # 计算总数
    total = query.count()
    print(f"[错题列表] 总计: {total} 条错题")
    
    # 分页
    offset = (page - 1) * page_size
    mistakes = query.offset(offset).limit(page_size).all()
    
    print(f"[错题列表] 返回: {len(mistakes)} 条错题 (第{page}页)")
    
    # 构建响应
    mistake_responses = []
    for mistake in mistakes:
        response = MistakeResponse.from_orm(mistake)
        response.has_image = bool(mistake.original_image_base64)
        mistake_responses.append(response)
    
    print(f"[错题列表] ✅ 数据准备完成")
    
    return MistakeListResponse(
        total=total,
        page=page,
        page_size=page_size,
        mistakes=mistake_responses
    )


@router.get("/{mistake_id}", response_model=MistakeResponse)
async def get_mistake_detail(
    mistake_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取单个错题详情（包含图片）
    
    功能：
    - 返回错题的完整信息
    - 包含原始图片Base64（如果有）
    """
    print(f"\n[错题详情] 获取错题 id={mistake_id}")
    print(f"[错题详情] 请求用户: {current_user.username}")
    
    # 查询错题
    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.owner_id == current_user.id
    ).first()
    
    if not mistake:
        print(f"[错题详情] ❌ 错题不存在或无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在或无权访问"
        )
    
    print(f"[错题详情] ✅ 找到错题")
    print(f"[错题详情] 学科: {mistake.subject}")
    print(f"[错题详情] 有图片: {bool(mistake.original_image_base64)}")
    
    # 构建响应
    response = MistakeResponse.from_orm(mistake)
    response.has_image = bool(mistake.original_image_base64)
    
    return response


@router.put("/{mistake_id}", response_model=MistakeResponse)
async def update_mistake(
    mistake_id: int,
    update_data: MistakeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新错题信息
    
    功能：
    - 标记为已复习
    - 更新知识点
    - 更新难度
    """
    print(f"\n[错题更新] 更新错题 id={mistake_id}")
    print(f"[错题更新] 请求用户: {current_user.username}")
    
    # 查询错题
    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.owner_id == current_user.id
    ).first()
    
    if not mistake:
        print(f"[错题更新] ❌ 错题不存在或无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在或无权访问"
        )
    
    # 更新字段
    updated = False
    
    if update_data.reviewed is not None:
        mistake.reviewed = update_data.reviewed
        if update_data.reviewed:
            mistake.review_count += 1
            mistake.last_reviewed_at = datetime.utcnow()
            print(f"[错题更新] 标记为已复习 (复习次数: {mistake.review_count})")
        updated = True
    
    if update_data.knowledge_points is not None:
        mistake.knowledge_points = json.dumps(update_data.knowledge_points, ensure_ascii=False)
        print(f"[错题更新] 更新知识点: {update_data.knowledge_points}")
        updated = True
    
    if update_data.difficulty is not None:
        mistake.difficulty = update_data.difficulty
        print(f"[错题更新] 更新难度: {update_data.difficulty}")
        updated = True
    
    if updated:
        db.commit()
        db.refresh(mistake)
        print(f"[错题更新] ✅ 更新成功")
    else:
        print(f"[错题更新] ⚠️ 没有需要更新的字段")
    
    # 构建响应
    response = MistakeResponse.from_orm(mistake)
    response.has_image = bool(mistake.original_image_base64)
    
    return response


@router.delete("/{mistake_id}")
async def delete_mistake(
    mistake_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除错题
    
    功能：
    - 彻底删除错题记录
    """
    print(f"\n[错题删除] 删除错题 id={mistake_id}")
    print(f"[错题删除] 请求用户: {current_user.username}")
    
    # 查询错题
    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.owner_id == current_user.id
    ).first()
    
    if not mistake:
        print(f"[错题删除] ❌ 错题不存在或无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在或无权访问"
        )
    
    db.delete(mistake)
    db.commit()
    
    print(f"[错题删除] ✅ 删除成功")
    
    return {"message": "错题已删除", "mistake_id": mistake_id}


@router.get("/stats/summary")
async def get_mistake_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取错题统计信息
    
    功能：
    - 总错题数
    - 各学科错题数
    - 已复习/未复习数量
    """
    print(f"\n[错题统计] 用户: {current_user.username}")
    
    # 总错题数
    total = db.query(Mistake).filter(Mistake.owner_id == current_user.id).count()
    print(f"[错题统计] 总计: {total} 条")
    
    # 已复习数
    reviewed_count = db.query(Mistake).filter(
        Mistake.owner_id == current_user.id,
        Mistake.reviewed == True
    ).count()
    print(f"[错题统计] 已复习: {reviewed_count} 条")
    
    # 按学科统计
    from sqlalchemy import func
    subject_stats = db.query(
        Mistake.subject,
        func.count(Mistake.id).label('count')
    ).filter(
        Mistake.owner_id == current_user.id
    ).group_by(Mistake.subject).all()
    
    subject_dict = {subject: count for subject, count in subject_stats if subject}
    print(f"[错题统计] 学科分布: {subject_dict}")
    
    print(f"[错题统计] ✅ 统计完成")
    
    return {
        "total": total,
        "reviewed": reviewed_count,
        "not_reviewed": total - reviewed_count,
        "by_subject": subject_dict,
        "review_progress": round(reviewed_count / total * 100, 1) if total > 0 else 0
    }

