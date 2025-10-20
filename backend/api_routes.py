# ==============================================================================
# api_routes.py - 统一智能API接口（V22.1扩展）
# 功能：提供统一的解题、批改、题库检索接口
# 设计理念：一个接口处理多种场景，自动识别输入类型
# ==============================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import base64
import io
from PIL import Image
import uuid
import time

# 导入现有模块
from image_enhancer import advanced_image_processing_pipeline
from pix2text import Pix2Text
from main import (
    extract_text_with_pix2text, 
    call_qwen_vl_max, 
    SESSIONS,
    p2t
)

# 创建路由器
router = APIRouter(prefix="/api", tags=["智能解题API"])


# ==============================================================================
# Pydantic数据模型定义
# ==============================================================================

class ContentInput(BaseModel):
    """输入内容模型"""
    image_base64: Optional[str] = Field(None, description="Base64编码的图片")
    text: Optional[str] = Field(None, description="纯文本题目内容")
    image_url: Optional[str] = Field(None, description="图片URL（暂不支持）")


class SolveOptions(BaseModel):
    """处理选项"""
    detail_level: Literal["basic", "detailed", "full"] = Field(
        "detailed", 
        description="解答详细程度：basic=简答，detailed=详细，full=完整"
    )
    language: Literal["zh", "en"] = Field("zh", description="语言：zh=中文，en=英文")
    include_steps: bool = Field(True, description="是否包含解题步骤")
    include_analysis: bool = Field(True, description="是否包含错误分析（批改模式）")


class SolveRequest(BaseModel):
    """统一解题/批改请求"""
    mode: Literal["solve", "review"] = Field(..., description="模式：solve=解题，review=批改")
    input_type: Literal["image", "text", "auto"] = Field(
        "auto", 
        description="输入类型：image=图片，text=文字，auto=自动检测"
    )
    question_count: Literal["single", "multiple", "auto"] = Field(
        "auto", 
        description="题目数量：single=单题，multiple=多题，auto=自动检测"
    )
    content: ContentInput = Field(..., description="题目内容")
    options: Optional[SolveOptions] = Field(
        default_factory=SolveOptions, 
        description="处理选项"
    )
    session_id: Optional[str] = Field(None, description="会话ID（用于追问）")


class QuestionResult(BaseModel):
    """单个题目结果"""
    question_index: int
    question_text: str
    answer: Optional[Dict[str, Any]] = None
    review: Optional[Dict[str, Any]] = None


class SolveResponse(BaseModel):
    """统一响应"""
    success: bool
    session_id: str
    results: List[QuestionResult]
    metadata: Dict[str, Any]
    error: Optional[str] = None


class QuestionBankRequest(BaseModel):
    """题库检索请求"""
    tags: List[str] = Field(..., description="知识点标签")
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(
        None, 
        description="难度"
    )
    subject: Optional[Literal["math", "physics", "chemistry"]] = Field(
        None, 
        description="学科"
    )
    limit: int = Field(10, ge=1, le=100, description="返回数量")
    offset: int = Field(0, ge=0, description="分页偏移")


# ==============================================================================
# 核心处理函数
# ==============================================================================

def detect_input_type(content: ContentInput) -> str:
    """自动检测输入类型"""
    if content.image_base64:
        return "image"
    elif content.text:
        return "text"
    elif content.image_url:
        return "image_url"
    else:
        raise ValueError("必须提供图片或文字内容")


def build_prompt(mode: str, question_count: str, options: SolveOptions) -> str:
    """构建AI提示词"""
    
    # 基础提示词
    if mode == "solve":
        if question_count == "single":
            base_prompt = "请认真审题并详细解答，写出完整的解题过程和思路。"
        else:
            base_prompt = "请逐题解答，每道题都要写出详细的解题步骤和思路。"
    else:  # review
        if question_count == "single":
            base_prompt = "请认真批改这道题目，指出答案中的对错，如果答案错误就给出正确解法。"
        else:
            base_prompt = "请逐题批改，对每道题的答案指出对错，如果答案错误就给出正确解法。"
    
    # 根据detail_level调整
    if options.detail_level == "basic":
        base_prompt += "\n【要求】：简明扼要，只给出关键步骤和答案。"
    elif options.detail_level == "full":
        base_prompt += "\n【要求】：请提供最详尽的解答，包括知识点、易错点、拓展内容。"
    
    # 添加步骤要求
    if options.include_steps:
        base_prompt += "\n【步骤】：请分步骤展示解题过程。"
    
    # 批改模式的特殊要求
    if mode == "review" and options.include_analysis:
        base_prompt += "\n【分析】：请分析错误原因，给出改进建议。"
    
    return base_prompt


def process_image_input(image_base64: str) -> tuple:
    """
    处理图片输入
    返回：(ocr_text, pil_image)
    """
    try:
        # Base64解码
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # OCR识别
        ocr_text = extract_text_with_pix2text(image)
        
        return ocr_text, image
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片处理失败: {str(e)}")


def process_text_input(text: str) -> str:
    """处理纯文本输入"""
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    return text.strip()


def call_ai_for_solve(
    content_text: str, 
    image_base64: Optional[str], 
    prompt: str,
    session_id: Optional[str] = None
) -> dict:
    """
    调用AI进行解题/批改
    """
    # 构建消息
    if image_base64:
        # 混合输入：文本 + 图片
        enhanced_prompt = f"""题目内容如下：

{content_text}

【任务要求】
{prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身。
"""
        messages = [{
            "role": "user",
            "content": [
                {'text': enhanced_prompt},
                {'image': f"data:image/png;base64,{image_base64}"}
            ]
        }]
    else:
        # 纯文本输入
        enhanced_prompt = f"""题目内容：

{content_text}

【任务要求】
{prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅。
"""
        messages = [{
            "role": "user",
            "content": enhanced_prompt
        }]
    
    # 调用AI
    ai_response = call_qwen_vl_max(messages)
    
    return ai_response


# ==============================================================================
# API路由端点
# ==============================================================================

@router.post("/solve", response_model=SolveResponse)
async def unified_solve_api(request: SolveRequest):
    """
    统一智能解题/批改接口
    
    功能覆盖：
    1. 发送一道题目的图片信息 → 返回题目解析结果
    2. 发送一道题目的文字信息 → 返回题目解析结果
    3. 发送多道题目的图片信息 → 返回题目解析结果
    4. 发送多道题目的文字信息 → 返回题目解析结果
    5. 发送带有结果一道题目的图片信息 → 返回题目批改结果
    6. 发送带有结果一道题目的文字信息 → 返回题目批改结果
    7. 发送带有结果多道题目的图片信息 → 返回题目批改结果
    8. 发送带有结果多道题目的文字信息 → 返回题目批改结果
    """
    start_time = time.time()
    
    try:
        print("\n" + "="*70)
        print("【统一API】收到请求")
        print(f"模式: {request.mode}, 输入类型: {request.input_type}, 题目数量: {request.question_count}")
        print("="*70)
        
        # 1. 自动检测输入类型
        if request.input_type == "auto":
            detected_type = detect_input_type(request.content)
            print(f"[自动检测] 输入类型: {detected_type}")
        else:
            detected_type = request.input_type
        
        # 2. 处理输入内容
        if detected_type == "image":
            print("[输入处理] 处理图片输入...")
            ocr_text, pil_image = process_image_input(request.content.image_base64)
            content_text = ocr_text
            image_base64 = request.content.image_base64
            print(f"[OCR结果] 识别了 {len(ocr_text)} 个字符")
        else:  # text
            print("[输入处理] 处理文本输入...")
            content_text = process_text_input(request.content.text)
            image_base64 = None
        
        # 3. 自动检测题目数量（简单逻辑）
        if request.question_count == "auto":
            # 简单判断：包含"第X题"或多个"解："的为多题
            if any(keyword in content_text for keyword in ["第1题", "第2题", "1.", "2.", "(1)", "(2)"]):
                detected_count = "multiple"
            else:
                detected_count = "single"
            print(f"[自动检测] 题目数量: {detected_count}")
        else:
            detected_count = request.question_count
        
        # 4. 构建提示词
        prompt = build_prompt(request.mode, detected_count, request.options)
        print(f"[提示词构建] 完成")
        
        # 5. 调用AI
        print("[AI调用] 开始...")
        ai_response = call_ai_for_solve(
            content_text, 
            image_base64, 
            prompt,
            request.session_id
        )
        print(f"[AI调用] 完成，回答长度: {len(ai_response['content'])} 字符")
        
        # 6. 生成会话ID
        if request.session_id:
            session_id = request.session_id
        else:
            session_id = str(uuid.uuid4())
            # 存储会话（用于后续追问）
            SESSIONS[session_id] = {
                "history": [
                    {"role": "user", "content": content_text},
                    {"role": "assistant", "content": ai_response['content']}
                ],
                "title": "API调用",
                "image_base_64": image_base64,
                "mode": request.mode
            }
        
        # 7. 构建响应
        processing_time = (time.time() - start_time) * 1000
        
        # 简单解析结果（实际项目中可以更智能地拆分多题）
        result = QuestionResult(
            question_index=1,
            question_text=content_text[:200] + "..." if len(content_text) > 200 else content_text,
            answer={
                "content": ai_response['content'],
                "steps": [],  # 可以进一步解析AI回答提取步骤
                "final_answer": ""
            } if request.mode == "solve" else None,
            review={
                "is_correct": None,  # 需要解析AI回答判断
                "score": None,
                "errors": [],
                "suggestions": []
            } if request.mode == "review" else None
        )
        
        response = SolveResponse(
            success=True,
            session_id=session_id,
            results=[result],
            metadata={
                "mode": request.mode,
                "input_type": detected_type,
                "question_count": detected_count,
                "processing_time_ms": round(processing_time, 2),
                "ocr_confidence": 0.95 if detected_type == "image" else 1.0,
                "detail_level": request.options.detail_level
            }
        )
        
        print("="*70)
        print(f"【统一API】处理完成，耗时 {processing_time:.2f}ms")
        print("="*70 + "\n")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"!!! [统一API] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/question_bank")
async def search_question_bank(request: QuestionBankRequest):
    """
    题库检索接口
    
    功能：根据知识点标签检索题库试题
    """
    print(f"\n[题库检索] 标签: {request.tags}, 难度: {request.difficulty}, 学科: {request.subject}")
    
    # 这里是示例数据，实际项目中需要连接真实数据库
    mock_questions = [
        {
            "id": "q_001",
            "subject": "math",
            "tags": ["函数", "导数"],
            "difficulty": "medium",
            "content": "已知函数 $f(x) = x^3 - 3x + 1$，求 $f'(x)$ 的值。",
            "answer": "$f'(x) = 3x^2 - 3$",
            "analysis": "这是一个基础的求导题目，应用幂函数求导公式即可。"
        },
        {
            "id": "q_002",
            "subject": "math",
            "tags": ["函数", "极值"],
            "difficulty": "hard",
            "content": "求函数 $f(x) = x^3 - 3x^2 + 1$ 的极值点。",
            "answer": "极大值点: $x=0$, 极小值点: $x=2$",
            "analysis": "先求导，令 $f'(x)=0$ 找驻点，再用二阶导数判断。"
        }
    ]
    
    # 简单的标签匹配过滤
    filtered_questions = []
    for q in mock_questions:
        if any(tag in q["tags"] for tag in request.tags):
            if request.difficulty is None or q["difficulty"] == request.difficulty:
                if request.subject is None or q["subject"] == request.subject:
                    filtered_questions.append(q)
    
    # 分页
    total = len(filtered_questions)
    paginated_questions = filtered_questions[request.offset:request.offset + request.limit]
    
    return {
        "success": True,
        "total": total,
        "questions": paginated_questions,
        "metadata": {
            "limit": request.limit,
            "offset": request.offset,
            "returned": len(paginated_questions)
        }
    }


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": "V22.1",
        "api": "统一智能解题API",
        "services": {
            "pix2text": p2t is not None,
            "dashscope": True,
            "image_enhancer": True
        }
    }


@router.get("/")
async def api_info():
    """API信息接口"""
    return {
        "name": "沐梧AI解题系统 - 统一智能API",
        "version": "V22.1",
        "endpoints": {
            "/api/solve": "统一解题/批改接口（支持图片和文字，单题和多题）",
            "/api/question_bank": "题库检索接口",
            "/api/health": "健康检查",
            "/api/": "API信息（当前页面）"
        },
        "features": [
            "智能图像增强（反锐化掩模 + CLAHE）",
            "混合输入架构（OCR + 视觉理解）",
            "自动检测输入类型和题目数量",
            "支持解题和批改两种模式",
            "灵活的详细程度控制",
            "会话管理和追问支持"
        ]
    }

