# ==============================================================================
# paper_generation_routes.py - 试卷生成与下载API (Feature 4)
# 功能：组卷、生成PDF（学生版/教师版）、下载
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
from pathlib import Path

# PDF生成库
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from database import get_db
from models import User, GeneratedQuestion, TestPaper
from auth import get_current_active_user

# 创建路由器
router = APIRouter(prefix="/papers", tags=["试卷生成"])

# PDF输出目录
PDF_OUTPUT_DIR = Path("generated_papers")
PDF_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


# ==============================================================================
# Pydantic数据模型
# ==============================================================================

class PaperCreateRequest(BaseModel):
    """创建试卷请求"""
    title: str = Field(..., description="试卷标题", min_length=1, max_length=200)
    question_ids: List[int] = Field(..., description="题目ID列表", min_items=1)
    total_score: float = Field(..., description="总分", gt=0)
    duration_minutes: Optional[int] = Field(60, description="考试时长（分钟）", gt=0)
    subject: Optional[str] = Field("数学", description="学科")
    show_answer: bool = Field(False, description="是否显示答案（教师版）")


class PaperResponse(BaseModel):
    """试卷响应"""
    paper_id: int
    title: str
    question_count: int
    total_score: float
    duration_minutes: int
    subject: str
    student_pdf_path: Optional[str]
    teacher_pdf_path: Optional[str]
    created_at: datetime


# ==============================================================================
# 核心功能：PDF生成
# ==============================================================================

def register_chinese_font():
    """
    注册中文字体
    
    注意：这需要系统安装了中文字体
    Windows: C:/Windows/Fonts/simhei.ttf (黑体)
    Linux: /usr/share/fonts/truetype/
    """
    print(f"[PDF生成] 尝试注册中文字体...")
    
    # 尝试多个常见的中文字体路径
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
        "C:/Windows/Fonts/msyh.ttf",    # Windows 微软雅黑
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux
        "/System/Library/Fonts/PingFang.ttc",  # macOS
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                print(f"[PDF生成] ✅ 成功注册中文字体: {font_path}")
                return True
            except Exception as e:
                print(f"[PDF生成] ⚠️ 注册字体失败 {font_path}: {e}")
                continue
    
    print(f"[PDF生成] ⚠️ 未找到中文字体，将使用默认字体（可能不支持中文）")
    return False


def create_pdf_styles(has_chinese_font: bool):
    """
    创建PDF样式
    
    Args:
        has_chinese_font: 是否已注册中文字体
    
    Returns:
        dict: 样式字典
    """
    print(f"[PDF生成] 创建PDF样式...")
    
    styles = getSampleStyleSheet()
    font_name = 'ChineseFont' if has_chinese_font else 'Helvetica'
    
    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # 副标题样式
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    # 题目样式
    question_style = ParagraphStyle(
        'CustomQuestion',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=10,
        leftIndent=20
    )
    
    # 答案样式
    answer_style = ParagraphStyle(
        'CustomAnswer',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        alignment=TA_LEFT,
        textColor=colors.blue,
        leftIndent=30,
        spaceAfter=5
    )
    
    print(f"[PDF生成] ✅ 样式创建完成")
    
    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'question': question_style,
        'answer': answer_style
    }


def generate_pdf(
    paper_title: str,
    questions: List[Dict],
    total_score: float,
    duration_minutes: int,
    output_path: str,
    show_answer: bool = False
):
    """
    生成PDF试卷
    
    Args:
        paper_title: 试卷标题
        questions: 题目列表
        total_score: 总分
        duration_minutes: 考试时长
        output_path: 输出路径
        show_answer: 是否显示答案
    """
    print(f"\n{'='*70}")
    print(f"【PDF生成】")
    print(f"{'='*70}")
    print(f"[PDF生成] 试卷标题: {paper_title}")
    print(f"[PDF生成] 题目数量: {len(questions)}")
    print(f"[PDF生成] 总分: {total_score}")
    print(f"[PDF生成] 时长: {duration_minutes}分钟")
    print(f"[PDF生成] 显示答案: {show_answer}")
    print(f"[PDF生成] 输出路径: {output_path}")
    
    # 注册中文字体
    has_chinese_font = register_chinese_font()
    
    # 创建样式
    styles = create_pdf_styles(has_chinese_font)
    
    # 创建PDF文档
    print(f"[PDF生成] 创建PDF文档对象...")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 构建PDF内容
    story = []
    
    # 标题
    print(f"[PDF生成] 添加标题...")
    story.append(Paragraph(paper_title, styles['title']))
    story.append(Spacer(1, 0.5*cm))
    
    # 副标题信息
    subtitle_text = f"总分: {total_score}分 | 时长: {duration_minutes}分钟 | 题目数: {len(questions)}"
    if show_answer:
        subtitle_text += " | 【教师版 - 含答案】"
    else:
        subtitle_text += " | 【学生版】"
    
    story.append(Paragraph(subtitle_text, styles['subtitle']))
    story.append(Spacer(1, 0.8*cm))
    
    # 添加题目
    print(f"[PDF生成] 添加题目...")
    for i, q in enumerate(questions, 1):
        content = json.loads(q['content'])
        question_type = q['question_type']
        
        print(f"[PDF生成]   题目{i}: {question_type}")
        
        # 题目标题
        question_title = f"{i}. ({question_type})"
        story.append(Paragraph(question_title, styles['question']))
        
        # 题干
        stem = content.get('stem', '')
        story.append(Paragraph(stem, styles['question']))
        story.append(Spacer(1, 0.3*cm))
        
        # 选择题的选项
        if question_type == "选择题" and 'options' in content:
            options = content['options']
            for key in sorted(options.keys()):
                option_text = f"{key}. {options[key]}"
                story.append(Paragraph(option_text, styles['question']))
            story.append(Spacer(1, 0.3*cm))
        
        # 显示答案（教师版）
        if show_answer:
            answer_text = f"<b>答案:</b> {q['answer']}"
            story.append(Paragraph(answer_text, styles['answer']))
            
            if q.get('explanation'):
                explanation_text = f"<b>解析:</b> {q['explanation'][:200]}..."  # 限制长度
                story.append(Paragraph(explanation_text, styles['answer']))
        
        story.append(Spacer(1, 0.5*cm))
    
    # 生成PDF
    print(f"[PDF生成] 正在写入PDF文件...")
    try:
        doc.build(story)
        print(f"[PDF生成] ✅ PDF生成成功: {output_path}")
        return True
    except Exception as e:
        print(f"[PDF生成] ❌ PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# API端点
# ==============================================================================

@router.post("/", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
async def create_paper(
    request: PaperCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建试卷并生成PDF
    
    功能：
    - 从题目ID列表中获取题目
    - 生成学生版PDF（无答案）
    - 生成教师版PDF（含答案）
    - 保存试卷信息到数据库
    """
    print(f"\n{'#'*70}")
    print(f"# POST /papers/")
    print(f"# 用户: {current_user.username} (id={current_user.id})")
    print(f"# 试卷标题: {request.title}")
    print(f"# 题目数量: {len(request.question_ids)}")
    print(f"{'#'*70}")
    
    print(f"[试卷创建] 收到创建请求")
    print(f"[试卷创建] 题目ID列表: {request.question_ids}")
    
    # 1. 从数据库获取题目
    print(f"[试卷创建] 正在从数据库获取题目...")
    questions = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.id.in_(request.question_ids),
        GeneratedQuestion.creator_id == current_user.id
    ).all()
    
    if not questions:
        print(f"[试卷创建] ❌ 未找到任何题目")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到指定的题目或无权访问"
        )
    
    print(f"[试卷创建] ✅ 找到 {len(questions)} 道题目")
    
    # 2. 构建题目数据
    print(f"[试卷创建] 构建题目数据...")
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'question_type': q.question_type,
            'content': q.content,
            'answer': q.answer,
            'explanation': q.explanation
        })
        print(f"[试卷创建]   - 题目ID {q.id}: {q.question_type}")
    
    # 3. 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in request.title if c.isalnum() or c in (' ', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_')[:30]  # 限制长度
    
    student_filename = f"{safe_title}_学生版_{timestamp}.pdf"
    teacher_filename = f"{safe_title}_教师版_{timestamp}.pdf"
    
    student_path = PDF_OUTPUT_DIR / student_filename
    teacher_path = PDF_OUTPUT_DIR / teacher_filename
    
    print(f"[试卷创建] 学生版文件: {student_filename}")
    print(f"[试卷创建] 教师版文件: {teacher_filename}")
    
    # 4. 生成学生版PDF
    print(f"\n[试卷创建] ========== 生成学生版PDF ==========")
    student_success = generate_pdf(
        paper_title=request.title,
        questions=questions_data,
        total_score=request.total_score,
        duration_minutes=request.duration_minutes,
        output_path=str(student_path),
        show_answer=False
    )
    
    if not student_success:
        print(f"[试卷创建] ❌ 学生版PDF生成失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="学生版PDF生成失败"
        )
    
    # 5. 生成教师版PDF
    print(f"\n[试卷创建] ========== 生成教师版PDF ==========")
    teacher_success = generate_pdf(
        paper_title=request.title + " (教师版)",
        questions=questions_data,
        total_score=request.total_score,
        duration_minutes=request.duration_minutes,
        output_path=str(teacher_path),
        show_answer=True
    )
    
    if not teacher_success:
        print(f"[试卷创建] ❌ 教师版PDF生成失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="教师版PDF生成失败"
        )
    
    # 6. 保存到数据库
    print(f"\n[试卷创建] 保存试卷信息到数据库...")
    new_paper = TestPaper(
        creator_id=current_user.id,
        title=request.title,
        question_ids=json.dumps(request.question_ids),
        total_score=request.total_score,
        duration_minutes=request.duration_minutes,
        subject=request.subject,
        student_pdf_path=str(student_path),
        teacher_pdf_path=str(teacher_path),
        created_at=datetime.utcnow()
    )
    
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)
    
    print(f"[试卷创建] ✅ 试卷信息保存成功，ID: {new_paper.id}")
    
    print(f"\n{'='*70}")
    print(f"【试卷创建完成】")
    print(f"  试卷ID: {new_paper.id}")
    print(f"  学生版: {student_filename}")
    print(f"  教师版: {teacher_filename}")
    print(f"{'='*70}\n")
    
    # 7. 返回响应
    return PaperResponse(
        paper_id=new_paper.id,
        title=new_paper.title,
        question_count=len(questions),
        total_score=new_paper.total_score,
        duration_minutes=new_paper.duration_minutes,
        subject=new_paper.subject,
        student_pdf_path=student_filename,
        teacher_pdf_path=teacher_filename,
        created_at=new_paper.created_at
    )


@router.get("/{paper_id}/download/{version}")
async def download_paper(
    paper_id: int,
    version: str,  # "student" or "teacher"
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    下载试卷PDF
    
    Args:
        paper_id: 试卷ID
        version: 版本（student=学生版, teacher=教师版）
    """
    print(f"\n[PDF下载] 试卷ID: {paper_id}, 版本: {version}")
    print(f"[PDF下载] 用户: {current_user.username}")
    
    # 验证版本参数
    if version not in ["student", "teacher"]:
        print(f"[PDF下载] ❌ 无效的版本参数: {version}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="版本参数必须是 'student' 或 'teacher'"
        )
    
    # 查询试卷
    print(f"[PDF下载] 正在查询试卷...")
    paper = db.query(TestPaper).filter(
        TestPaper.id == paper_id,
        TestPaper.creator_id == current_user.id
    ).first()
    
    if not paper:
        print(f"[PDF下载] ❌ 试卷不存在或无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="试卷不存在或无权访问"
        )
    
    # 获取文件路径
    file_path = paper.student_pdf_path if version == "student" else paper.teacher_pdf_path
    
    if not file_path or not os.path.exists(file_path):
        print(f"[PDF下载] ❌ PDF文件不存在: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF文件不存在"
        )
    
    print(f"[PDF下载] ✅ 找到文件: {file_path}")
    print(f"[PDF下载] 准备发送文件...")
    
    # 返回文件
    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/")
async def get_my_papers(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取我创建的试卷列表"""
    print(f"\n[我的试卷] 用户: {current_user.username}")
    print(f"[我的试卷] 页码: {page}, 每页: {page_size}")
    
    query = db.query(TestPaper).filter(
        TestPaper.creator_id == current_user.id
    ).order_by(TestPaper.created_at.desc())
    
    total = query.count()
    print(f"[我的试卷] 总计: {total} 份试卷")
    
    offset = (page - 1) * page_size
    papers = query.offset(offset).limit(page_size).all()
    
    print(f"[我的试卷] 返回: {len(papers)} 份试卷")
    
    result = []
    for p in papers:
        result.append({
            "id": p.id,
            "title": p.title,
            "question_count": len(json.loads(p.question_ids)),
            "total_score": p.total_score,
            "duration_minutes": p.duration_minutes,
            "subject": p.subject,
            "created_at": p.created_at.isoformat(),
            "student_pdf_available": bool(p.student_pdf_path and os.path.exists(p.student_pdf_path)),
            "teacher_pdf_available": bool(p.teacher_pdf_path and os.path.exists(p.teacher_pdf_path))
        })
    
    print(f"[我的试卷] ✅ 数据准备完成")
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "papers": result
    }


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除试卷（包括PDF文件）"""
    print(f"\n[删除试卷] ID: {paper_id}, 用户: {current_user.username}")
    
    paper = db.query(TestPaper).filter(
        TestPaper.id == paper_id,
        TestPaper.creator_id == current_user.id
    ).first()
    
    if not paper:
        print(f"[删除试卷] ❌ 试卷不存在或无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="试卷不存在或无权访问"
        )
    
    # 删除PDF文件
    print(f"[删除试卷] 正在删除PDF文件...")
    for pdf_path in [paper.student_pdf_path, paper.teacher_pdf_path]:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"[删除试卷] ✅ 已删除: {pdf_path}")
            except Exception as e:
                print(f"[删除试卷] ⚠️ 删除文件失败: {e}")
    
    # 删除数据库记录
    db.delete(paper)
    db.commit()
    
    print(f"[删除试卷] ✅ 试卷删除成功")
    
    return {"message": "试卷已删除", "paper_id": paper_id}

