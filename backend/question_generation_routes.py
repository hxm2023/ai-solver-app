# ==============================================================================
# question_generation_routes.py - 知识点生成与智能出题API (Feature 3)
# 功能：从错题提炼知识点、AI生成新题
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import json
from datetime import datetime
import dashscope
from http import HTTPStatus

from database import get_db
from models import User, Mistake, GeneratedQuestion
from auth import get_current_active_user

# 创建路由器
router = APIRouter(prefix="/ai-learning", tags=["智能出题"])


# ==============================================================================
# Pydantic数据模型
# ==============================================================================

class KnowledgePointsRequest(BaseModel):
    """生成知识点请求"""
    mistake_ids: List[int] = Field(..., description="错题ID列表", min_items=1)
    subject: Optional[str] = Field(None, description="学科（用于优化提示词）")


class KnowledgePointsResponse(BaseModel):
    """知识点响应"""
    knowledge_points: List[str] = Field(..., description="提炼的知识点列表")
    source_mistakes: List[int] = Field(..., description="来源错题ID")
    subject: Optional[str]
    ai_analysis: str = Field(..., description="AI的详细分析")


class QuestionGenerationRequest(BaseModel):
    """生成题目请求"""
    knowledge_points: List[str] = Field(..., description="知识点列表", min_items=1)
    difficulty: str = Field(..., description="难度", pattern="^(简单|中等|困难)$")
    question_types: Dict[str, int] = Field(
        ..., 
        description="题型和数量，如 {'选择题': 5, '填空题': 3}"
    )
    subject: Optional[str] = Field("数学", description="学科")


class GeneratedQuestionDetail(BaseModel):
    """单个生成的题目"""
    question_type: str
    content: str  # JSON字符串
    answer: str
    explanation: Optional[str]
    knowledge_points: List[str]
    difficulty: str


class QuestionGenerationResponse(BaseModel):
    """生成题目响应"""
    total_generated: int
    questions: List[GeneratedQuestionDetail]
    generation_time: str


# ==============================================================================
# 核心功能：调用AI生成知识点
# ==============================================================================

def call_ai_for_knowledge_points(mistake_analyses: List[str], subject: Optional[str]) -> Dict:
    """
    调用通义千问提炼知识点
    
    Args:
        mistake_analyses: 错题的AI分析列表
        subject: 学科（用于优化提示词）
    
    Returns:
        dict: {"knowledge_points": [...], "analysis": "..."}
    """
    print(f"\n{'='*70}")
    print(f"【AI知识点提炼】")
    print(f"{'='*70}")
    print(f"[AI调用] 准备调用通义千问...")
    print(f"[AI调用] 错题分析数量: {len(mistake_analyses)}")
    print(f"[AI调用] 学科: {subject or '未指定'}")
    
    # 构建Prompt
    analyses_text = "\n\n".join([f"错题{i+1}:\n{text}" for i, text in enumerate(mistake_analyses)])
    
    prompt = f"""你是一位经验丰富的{subject or ''}教师。请分析以下学生的错题，总结出这些错题背后共通的、核心的知识点。

【错题分析内容】
{analyses_text}

【任务要求】
1. 仔细分析这些错题的共同点
2. 提炼出3-5个核心知识点
3. 知识点应该具体、明确，便于后续出题
4. 按重要性排序

【输出格式】
请严格按照以下JSON格式输出（不要有其他文字）：
{{
  "knowledge_points": ["知识点1", "知识点2", "知识点3"],
  "analysis": "这些错题主要考察了..."
}}
"""
    
    print(f"[AI调用] Prompt构建完成，长度: {len(prompt)} 字符")
    print(f"[AI调用] 正在调用通义千问...")
    
    try:
        # 调用通义千问
        messages = [{"role": "user", "content": prompt}]
        
        response = dashscope.Generation.call(
            model='qwen-turbo',
            messages=messages,
            result_format='message',
            max_tokens=1500,
            temperature=0.7
        )
        
        if response.status_code != HTTPStatus.OK:
            print(f"[AI调用] ❌ API调用失败")
            print(f"[AI调用] 状态码: {response.status_code}")
            print(f"[AI调用] 错误信息: {response.message}")
            raise Exception(f"API调用失败: {response.message}")
        
        # 提取响应
        ai_text = response.output.choices[0].message.content
        print(f"[AI调用] ✅ API调用成功")
        print(f"[AI调用] 响应长度: {len(ai_text)} 字符")
        
        # 解析JSON
        print(f"[AI调用] 正在解析JSON响应...")
        try:
            result = json.loads(ai_text)
            print(f"[AI调用] ✅ JSON解析成功")
            print(f"[AI调用] 提炼知识点数量: {len(result.get('knowledge_points', []))}")
            print(f"[AI调用] 知识点列表: {result.get('knowledge_points', [])}")
            return result
        except json.JSONDecodeError as e:
            print(f"[AI调用] ⚠️ JSON解析失败，尝试提取知识点...")
            print(f"[AI调用] 原始响应: {ai_text[:200]}...")
            
            # 备用方案：从文本中提取
            lines = ai_text.split('\n')
            knowledge_points = []
            for line in lines:
                if line.strip() and not line.startswith('{') and not line.startswith('}'):
                    knowledge_points.append(line.strip('- ').strip())
            
            result = {
                "knowledge_points": knowledge_points[:5],  # 最多5个
                "analysis": ai_text
            }
            print(f"[AI调用] ✅ 备用提取成功: {result['knowledge_points']}")
            return result
            
    except Exception as e:
        print(f"[AI调用] ❌ 调用过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise


# ==============================================================================
# 核心功能：调用AI生成题目
# ==============================================================================

def call_ai_for_question_generation(
    knowledge_points: List[str],
    question_type: str,
    count: int,
    difficulty: str,
    subject: str
) -> List[Dict]:
    """
    调用通义千问生成题目
    
    Args:
        knowledge_points: 知识点列表
        question_type: 题型（选择题、填空题等）
        count: 数量
        difficulty: 难度
        subject: 学科
    
    Returns:
        List[Dict]: 生成的题目列表
    """
    print(f"\n{'='*70}")
    print(f"【AI题目生成】")
    print(f"{'='*70}")
    print(f"[AI生题] 题型: {question_type}")
    print(f"[AI生题] 数量: {count}")
    print(f"[AI生题] 难度: {difficulty}")
    print(f"[AI生题] 知识点: {knowledge_points}")
    print(f"[AI生题] 学科: {subject}")
    
    # 构建详细的Prompt
    kp_text = "、".join(knowledge_points)
    
    # 根据题型定制输出格式
    if question_type == "选择题":
        format_example = """
{
  "questions": [
    {
      "stem": "题干内容",
      "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
      "answer": "B",
      "explanation": "详细解析"
    }
  ]
}
"""
    elif question_type == "填空题":
        format_example = """
{
  "questions": [
    {
      "stem": "题干内容，答案用____表示",
      "answer": "正确答案",
      "explanation": "详细解析"
    }
  ]
}
"""
    elif question_type == "解答题":
        format_example = """
{
  "questions": [
    {
      "stem": "题干内容",
      "answer": "完整解答过程",
      "explanation": "解题思路和关键步骤"
    }
  ]
}
"""
    else:
        format_example = """
{
  "questions": [
    {
      "stem": "题干内容",
      "answer": "正确答案",
      "explanation": "详细解析"
    }
  ]
}
"""
    
    prompt = f"""你是一位经验丰富的{subject}出题专家。请根据以下要求生成{count}道{question_type}。

【知识点】
{kp_text}

【难度要求】
{difficulty}

【题目要求】
1. 题目必须紧扣上述知识点
2. 难度符合"{difficulty}"标准
3. 题目质量要高，具有区分度
4. 题目新颖，不要过于常规
5. 每道题都要有详细解析

【输出格式】
请严格按照以下JSON格式输出（不要有其他文字）：
{format_example}

请生成{count}道高质量的{question_type}。
"""
    
    print(f"[AI生题] Prompt构建完成，长度: {len(prompt)} 字符")
    print(f"[AI生题] 正在调用通义千问...")
    
    try:
        messages = [{"role": "user", "content": prompt}]
        
        response = dashscope.Generation.call(
            model='qwen-turbo',
            messages=messages,
            result_format='message',
            max_tokens=3000,
            temperature=0.8  # 稍高的温度以增加题目多样性
        )
        
        if response.status_code != HTTPStatus.OK:
            print(f"[AI生题] ❌ API调用失败: {response.message}")
            raise Exception(f"API调用失败: {response.message}")
        
        ai_text = response.output.choices[0].message.content
        print(f"[AI生题] ✅ API调用成功，响应长度: {len(ai_text)} 字符")
        
        # 解析JSON
        print(f"[AI生题] 正在解析JSON响应...")
        try:
            result = json.loads(ai_text)
            questions = result.get('questions', [])
            print(f"[AI生题] ✅ JSON解析成功")
            print(f"[AI生题] 生成题目数量: {len(questions)}")
            
            for i, q in enumerate(questions):
                print(f"[AI生题] 题目{i+1}: {q.get('stem', '')[:50]}...")
            
            return questions
            
        except json.JSONDecodeError as e:
            print(f"[AI生题] ⚠️ JSON解析失败: {e}")
            print(f"[AI生题] 原始响应: {ai_text[:300]}...")
            
            # 备用方案：返回简单格式
            return [{
                "stem": ai_text[:500],
                "answer": "请查看AI原始回答",
                "explanation": ai_text
            }]
            
    except Exception as e:
        print(f"[AI生题] ❌ 生成过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise


# ==============================================================================
# API端点
# ==============================================================================

@router.post("/generate_knowledge_points", response_model=KnowledgePointsResponse)
async def generate_knowledge_points(
    request: KnowledgePointsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    从错题中提炼知识点
    
    功能：
    - 接收错题ID列表
    - 从数据库获取错题的AI分析
    - 调用AI总结知识点
    """
    print(f"\n{'#'*70}")
    print(f"# POST /ai-learning/generate_knowledge_points")
    print(f"# 用户: {current_user.username} (id={current_user.id})")
    print(f"# 错题数量: {len(request.mistake_ids)}")
    print(f"{'#'*70}")
    
    print(f"[知识点生成] 收到请求")
    print(f"[知识点生成] 错题ID列表: {request.mistake_ids}")
    
    # 1. 从数据库获取错题
    print(f"[知识点生成] 正在从数据库获取错题...")
    mistakes = db.query(Mistake).filter(
        Mistake.id.in_(request.mistake_ids),
        Mistake.owner_id == current_user.id
    ).all()
    
    if not mistakes:
        print(f"[知识点生成] ❌ 未找到任何错题")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到指定的错题或无权访问"
        )
    
    print(f"[知识点生成] ✅ 找到 {len(mistakes)} 条错题")
    
    # 2. 提取AI分析内容
    print(f"[知识点生成] 提取AI分析内容...")
    analyses = []
    for m in mistakes:
        analyses.append(m.ai_analysis)
        print(f"[知识点生成]   - 错题ID {m.id}: {m.question_text[:50]}...")
    
    # 3. 调用AI提炼知识点
    print(f"[知识点生成] 调用AI提炼知识点...")
    try:
        ai_result = call_ai_for_knowledge_points(analyses, request.subject)
        
        knowledge_points = ai_result.get('knowledge_points', [])
        analysis = ai_result.get('analysis', '')
        
        print(f"[知识点生成] ✅ AI提炼完成")
        print(f"[知识点生成] 提炼出 {len(knowledge_points)} 个知识点")
        
        response = KnowledgePointsResponse(
            knowledge_points=knowledge_points,
            source_mistakes=request.mistake_ids,
            subject=request.subject,
            ai_analysis=analysis
        )
        
        print(f"[知识点生成] ✅ 响应准备完成")
        return response
        
    except Exception as e:
        print(f"[知识点生成] ❌ AI调用失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI知识点提炼失败: {str(e)}"
        )


@router.post("/generate_questions", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    基于知识点生成题目
    
    功能：
    - 接收知识点、难度、题型要求
    - 调用AI生成题目
    - 保存到数据库
    """
    print(f"\n{'#'*70}")
    print(f"# POST /ai-learning/generate_questions")
    print(f"# 用户: {current_user.username} (id={current_user.id})")
    print(f"# 知识点: {request.knowledge_points}")
    print(f"# 难度: {request.difficulty}")
    print(f"# 题型要求: {request.question_types}")
    print(f"{'#'*70}")
    
    start_time = datetime.utcnow()
    print(f"[题目生成] 开始时间: {start_time}")
    
    all_questions = []
    
    # 遍历每种题型
    for question_type, count in request.question_types.items():
        if count <= 0:
            continue
        
        print(f"\n[题目生成] ========== 生成 {question_type} ==========")
        print(f"[题目生成] 需要生成: {count} 道")
        
        try:
            # 调用AI生成题目
            generated = call_ai_for_question_generation(
                knowledge_points=request.knowledge_points,
                question_type=question_type,
                count=count,
                difficulty=request.difficulty,
                subject=request.subject
            )
            
            print(f"[题目生成] AI返回 {len(generated)} 道题目")
            
            # 保存到数据库
            print(f"[题目生成] 正在保存到数据库...")
            for q_data in generated:
                # 构建content JSON
                content_json = json.dumps(q_data, ensure_ascii=False)
                
                new_question = GeneratedQuestion(
                    creator_id=current_user.id,
                    question_type=question_type,
                    content=content_json,
                    answer=q_data.get('answer', ''),
                    explanation=q_data.get('explanation', ''),
                    knowledge_points=json.dumps(request.knowledge_points, ensure_ascii=False),
                    difficulty=request.difficulty,
                    subject=request.subject,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_question)
                
                # 构建响应对象
                all_questions.append(GeneratedQuestionDetail(
                    question_type=question_type,
                    content=content_json,
                    answer=q_data.get('answer', ''),
                    explanation=q_data.get('explanation', ''),
                    knowledge_points=request.knowledge_points,
                    difficulty=request.difficulty
                ))
            
            db.commit()
            print(f"[题目生成] ✅ {question_type} 保存完成")
            
        except Exception as e:
            print(f"[题目生成] ❌ {question_type} 生成失败: {e}")
            # 继续生成其他题型
            continue
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n[题目生成] ========== 生成完成 ==========")
    print(f"[题目生成] 总计生成: {len(all_questions)} 道题目")
    print(f"[题目生成] 耗时: {duration:.2f} 秒")
    print(f"[题目生成] ✅ 全部完成！")
    
    return QuestionGenerationResponse(
        total_generated=len(all_questions),
        questions=all_questions,
        generation_time=f"{duration:.2f}秒"
    )


@router.get("/my_questions")
async def get_my_generated_questions(
    page: int = 1,
    page_size: int = 20,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取我生成的题目列表
    
    功能：
    - 分页获取
    - 按题型筛选
    - 按难度筛选
    """
    print(f"\n[我的题目] 用户: {current_user.username}")
    print(f"[我的题目] 页码: {page}, 每页: {page_size}")
    print(f"[我的题目] 筛选 - 题型: {question_type}, 难度: {difficulty}")
    
    query = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.creator_id == current_user.id
    )
    
    if question_type:
        query = query.filter(GeneratedQuestion.question_type == question_type)
    
    if difficulty:
        query = query.filter(GeneratedQuestion.difficulty == difficulty)
    
    query = query.order_by(GeneratedQuestion.created_at.desc())
    
    total = query.count()
    print(f"[我的题目] 总计: {total} 道题目")
    
    offset = (page - 1) * page_size
    questions = query.offset(offset).limit(page_size).all()
    
    print(f"[我的题目] 返回: {len(questions)} 道题目")
    
    result = []
    for q in questions:
        result.append({
            "id": q.id,
            "question_type": q.question_type,
            "content": json.loads(q.content),
            "answer": q.answer,
            "explanation": q.explanation,
            "knowledge_points": json.loads(q.knowledge_points),
            "difficulty": q.difficulty,
            "subject": q.subject,
            "created_at": q.created_at.isoformat(),
            "used_in_paper": q.used_in_paper
        })
    
    print(f"[我的题目] ✅ 数据准备完成")
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "questions": result
    }


@router.delete("/my_questions/{question_id}")
async def delete_generated_question(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除生成的题目"""
    print(f"\n[删除题目] ID: {question_id}, 用户: {current_user.username}")
    
    question = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.id == question_id,
        GeneratedQuestion.creator_id == current_user.id
    ).first()
    
    if not question:
        print(f"[删除题目] ❌ 题目不存在或无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在或无权访问"
        )
    
    db.delete(question)
    db.commit()
    
    print(f"[删除题目] ✅ 删除成功")
    
    return {"message": "题目已删除", "question_id": question_id}

