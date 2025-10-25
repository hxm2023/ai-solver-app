# ==============================================================================
# 简化版 main.py - 【V24.0 轻量级错题本系统】
# 核心特性：
# 1. OCR增强（Pix2Text）+ 原图视觉（通义千问）= 混合输入架构
# 2. 轻量级错题本 - JSON文件存储，无需数据库
# 3. 智能出题 - 基于错题生成新题目
# 4. 试卷导出 - Markdown/PDF格式
# 5. 无需登录 - 开箱即用
# ==============================================================================

import os
import io
import re
import uuid
import json
import asyncio  # 【V25.0新增】PDF导出需要
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Literal
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import dashscope
from pydantic import BaseModel
import base64
from fastapi.responses import JSONResponse
from PIL import Image

from dashscope import MultiModalConversation
from pix2text import Pix2Text

# 导入图像增强模块
from image_enhancer import advanced_image_processing_pipeline

# --- 全局变量 ---
SESSIONS = {}
DATA_DIR = Path("simple_data")
MISTAKES_FILE = DATA_DIR / "mistakes.json"
QUESTIONS_FILE = DATA_DIR / "generated_questions.json"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

# --- 初始化 ---
load_dotenv()
app = FastAPI(title="沐梧AI - 轻量级错题本系统", version="V24.0")

# 初始化 阿里云通义千问
print("正在配置通义千问API Key...")
try:
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key:
        raise ValueError("API Key not found in .env file")
    print("✅ 通义千问API Key配置成功")
except Exception as e:
    print(f"❌ 配置通义千问API Key失败: {e}")

# 初始化 Pix2Text OCR引擎
print("正在初始化 Pix2Text OCR引擎...")
try:
    p2t = Pix2Text(analyzer_config=dict(model_name='mfd'))
    print("✅ Pix2Text OCR引擎初始化成功")
except Exception as e:
    print(f"❌ Pix2Text初始化失败: {e}")
    p2t = None

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 数据模型
# ==============================================================================

# ChatRequest模型（用于解题和批改功能）
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    prompt: str
    image_base_64: Optional[str] = None

# 微信小程序专用请求模型
class MiniAppRequest(BaseModel):
    """微信小程序专用请求模型"""
    image_base_64: str
    mode: Literal['solve', 'review']

class MistakeCreate(BaseModel):
    """创建错题请求"""
    image_base64: str  # 图片的base64编码
    question_text: Optional[str] = ""  # OCR识别的题目文本
    wrong_answer: Optional[str] = ""  # 错误答案
    ai_analysis: Optional[str] = ""  # AI分析
    subject: Optional[str] = "未分类"  # 科目
    grade: Optional[str] = "未分类"  # 【V25.0新增】年级
    knowledge_points: Optional[List[str]] = []  # 知识点列表

class MistakeResponse(BaseModel):
    """错题响应"""
    id: str
    image_base64: str
    question_text: str
    wrong_answer: str
    ai_analysis: str
    subject: str
    grade: str  # 【V25.0新增】年级
    knowledge_points: List[str]
    created_at: str
    reviewed_count: int

class QuestionGenerateRequest(BaseModel):
    """生成题目请求"""
    mistake_ids: List[str]  # 基于哪些错题生成
    count: int = 3  # 生成题目数量
    difficulty: str = "中等"  # 难度级别
    allow_web_search: bool = False  # 【V25.0新增】是否允许网络搜索辅助出题

class QuestionResponse(BaseModel):
    """题目响应"""
    id: str
    content: str  # 题目内容（Markdown格式）
    answer: str  # 答案
    explanation: str  # 解析
    knowledge_points: List[str]
    difficulty: str
    created_at: str

# ==============================================================================
# JSON存储工具函数
# ==============================================================================

def load_mistakes() -> List[Dict]:
    """加载错题数据"""
    if not MISTAKES_FILE.exists():
        return []
    try:
        with open(MISTAKES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_mistakes(mistakes: List[Dict]):
    """保存错题数据"""
    with open(MISTAKES_FILE, 'w', encoding='utf-8') as f:
        json.dump(mistakes, f, ensure_ascii=False, indent=2)

def load_questions() -> List[Dict]:
    """加载生成的题目"""
    if not QUESTIONS_FILE.exists():
        return []
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_questions(questions: List[Dict]):
    """保存生成的题目"""
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

# ==============================================================================
# 辅助函数（用于解题功能）
# ==============================================================================

def image_preprocess_v2(img: Image.Image) -> Image.Image:
    """
    对图片进行预处理，优化OCR识别效果
    """
    # 转为RGB模式
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 调整尺寸 - 确保图片不会太小或太大
    width, height = img.size
    max_dimension = 2000
    if max(width, height) > max_dimension:
        scale = max_dimension / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return img

def extract_text_with_pix2text(image: Image.Image) -> str:
    """
    使用Pix2Text识别图片中的文字和公式
    """
    if p2t is None:
        return "[OCR引擎未初始化]"
    
    try:
        # 基础预处理
        processed_img = image_preprocess_v2(image)
        
        # 高级图像增强
        enhanced_img = advanced_image_processing_pipeline(processed_img)
        
        # OCR识别
        result = p2t.recognize(enhanced_img)
        
        # 提取文本内容
        if isinstance(result, dict) and 'text' in result:
            ocr_text = result['text']
        elif isinstance(result, str):
            ocr_text = result
        else:
            ocr_text = str(result)
        
        # 清理文本
        ocr_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ocr_text)
        ocr_text = ocr_text.strip()
        
        return ocr_text
    
    except Exception as e:
        # 降级策略
        try:
            processed_img = image_preprocess_v2(image)
            result = p2t.recognize(processed_img)
            
            if isinstance(result, dict) and 'text' in result:
                ocr_text = result['text']
            elif isinstance(result, str):
                ocr_text = result
            else:
                ocr_text = str(result)
            
            ocr_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ocr_text)
            ocr_text = ocr_text.strip()
            
            return ocr_text
        except:
            return "[OCR识别失败]"

def call_qwen_vl_max(messages: list, model: str = 'qwen-vl-max', max_tokens: int = 8192) -> dict:
    """
    调用通义千问模型并返回包含'content'和'finish_reason'的字典
    """
    response = dashscope.MultiModalConversation.call(
        model=model,
        messages=messages,
        max_output_tokens=max_tokens
    )
    
    if response.status_code != 200:
        raise Exception(f"通义千问API调用失败: {response.message}")
    
    choice = response.output.choices[0]
    content_data = choice.message.content
    finish_reason = choice.finish_reason if hasattr(choice, 'finish_reason') else None

    text_content = ""
    if isinstance(content_data, list):
        for part in content_data:
            if part.get("text"):
                text_content = part["text"]
                break
    elif isinstance(content_data, str):
        text_content = content_data
        
    if not text_content:
        raise ValueError("通义千问未返回有效的文本内容。")
    
    # 判断是否截断
    is_truncated = (finish_reason == 'length')
    
    return {
        'content': text_content,
        'finish_reason': finish_reason,
        'is_truncated': is_truncated
    }

# ==============================================================================
# 核心API端点
# ==============================================================================

@app.get("/")
def read_root():
    """根端点"""
    mistakes = load_mistakes()
    questions = load_questions()
    return {
        "message": "沐梧AI - 轻量级错题本系统（含解题功能）",
        "version": "V24.1",
        "features": {
            "chat": "AI智能解题和批改 - /chat",
            "mistake_book": "智能错题本 - 无需数据库",
            "ai_generation": "AI智能出题 - 基于错题生成",
            "export": "试卷导出 - Markdown/PDF"
        },
        "stats": {
            "mistakes_count": len(mistakes),
            "questions_count": len(questions),
            "active_sessions": len(SESSIONS)
        },
        "endpoints": {
            "chat": "POST /chat - AI解题和批改",
            "mistakes": {
                "create": "POST /mistakes/",
                "list": "GET /mistakes/",
                "get": "GET /mistakes/{id}",
                "delete": "DELETE /mistakes/{id}"
            },
            "questions": {
                "generate": "POST /questions/generate",
                "list": "GET /questions/",
                "delete": "DELETE /questions/{id}"
            },
            "export": {
                "markdown": "POST /export/markdown"
            }
        }
    }

# ==============================================================================
# AI解题和批改功能
# ==============================================================================

@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """AI智能解题和批改接口"""
    print(f"\n{'#'*70}")
    print(f"# /chat 接口被调用")
    print(f"# session_id: {request.session_id}")
    print(f"# prompt: {request.prompt[:80]}...")
    print(f"# has_image: {bool(request.image_base_64)}")
    print(f"{'#'*70}")
    
    session_id = request.session_id or str(uuid.uuid4())
    is_new_session = session_id not in SESSIONS
    
    print(f"[会话检查] session_id: {session_id[:16]}...")
    print(f"[会话检查] is_new_session: {is_new_session}")
    print(f"[会话检查] 当前活跃会话数: {len(SESSIONS)}")
    
    try:
        # --- 1. 初始化或加载会话历史 ---
        if is_new_session:
            print(f"\n{'='*60}")
            print(f"【新会话流程】")
            print(f"{'='*60}")
            
            if not request.image_base_64:
                print(f"[错误] 新会话必须包含图片！")
                raise HTTPException(status_code=400, detail="新会话必须包含图片")
            
            print(f"[新会话] 创建会话: {session_id}")
            print(f"[新会话] 图片大小: {len(request.image_base_64)} 字符")
            
            SESSIONS[session_id] = {
                "history": [], 
                "title": "新对话",
                "image_base_64": request.image_base_64 
            }
            print(f"[新会话] 会话创建成功")
            
        else:
            print(f"\n{'='*60}")
            print(f"【继续会话流程】")
            print(f"{'='*60}")
            
            # 检查会话是否存在
            if session_id not in SESSIONS:
                print(f"[错误] 会话不存在: {session_id}")
                raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或已过期")
            
            print(f"[继续会话] session_id: {session_id}")
            print(f"[继续会话] 用户提问: {request.prompt[:80]}...")
            print(f"[继续会话] 历史记录数: {len(SESSIONS[session_id]['history'])}")
            
        # --- 2. 混合输入架构 - OCR文本 + 原始图片 ---
        messages_to_send = []
        if is_new_session:
            # 使用Pix2Text进行OCR识别
            print("[混合输入架构] 步骤1: 使用Pix2Text进行OCR识别...")
            image_bytes = base64.b64decode(request.image_base_64)
            image = Image.open(io.BytesIO(image_bytes))
            ocr_text = extract_text_with_pix2text(image)
            
            print("[混合输入架构] 步骤2: 构建混合输入消息...")
            
            # 检测是否是批改模式
            is_review_mode = any(keyword in request.prompt for keyword in ["批改", "改", "检查", "对错"])
            print(f"[混合输入架构] 是否批改模式: {is_review_mode}")
            
            # 构建增强Prompt
            if is_review_mode:
                enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{request.prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身。

【特别要求】（批改模式 - 请严格按照以下规则添加标记）
1. **只有在学生的答案存在实质性错误时**（如计算错误、概念理解错误、步骤缺失等），才在回答的开头加上：[MISTAKE_DETECTED]
2. **如果学生的答案完全正确**（即使步骤可以优化，只要结果和逻辑都对），请在回答的开头加上：[CORRECT]
3. **请务必精确判断**：小瑕疵、格式问题、表述不够完美等，如果不影响答案正确性，请标记为[CORRECT]
4. 然后再给出详细的批改意见。

【判断标准】
- ✅ [CORRECT]：答案正确，逻辑合理，即使有小瑕疵
- ❌ [MISTAKE_DETECTED]：答案错误、计算有误、概念理解错误、关键步骤缺失
"""
            else:
                enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{request.prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身。
"""
            
            # 构建混合输入消息
            messages_to_send.append({
                "role": "user",
                "content": [
                    {'text': enhanced_prompt},
                    {'image': f"data:image/png;base64,{request.image_base_64}"}
                ]
            })
            
            print("[混合输入架构] 混合消息构建完成")
            
        else:
            # 追问模式 - 重建完整对话历史
            print(f"\n[追问模式] 开始重新构建对话历史...")
            
            original_image_base64 = SESSIONS[session_id].get("image_base_64")
            
            if not original_image_base64:
                print(f"[错误] 会话中没有找到原始图片！")
                raise HTTPException(status_code=500, detail="会话图片丢失，请重新开始对话")
            
            history = SESSIONS[session_id]["history"]
            if len(history) == 0:
                print(f"[错误] 会话历史为空！")
                raise HTTPException(status_code=500, detail="会话历史为空，请重新开始对话")
            
            # 第一条消息：用户的首次提问 + 图片
            first_user_message = history[0]
            messages_to_send = [{
                "role": "user",
                "content": [
                    {'text': first_user_message["content"]},
                    {'image': f"data:image/png;base64,{original_image_base64}"}
                ]
            }]
            
            # 添加后续的对话历史
            for msg in history[1:]:
                messages_to_send.append(msg)
            
            # 添加当前的追问
            messages_to_send.append({"role": "user", "content": request.prompt})
            
            print(f"[追问模式] ✅ 对话历史重建完成！总消息数: {len(messages_to_send)}")

        
        # --- 3. 调用大模型 ---
        print(f"\n{'='*60}")
        print(f"[AI调用] 准备调用通义千问...")
        print(f"{'='*60}")
        
        ai_response = call_qwen_vl_max(messages_to_send)
        full_response = ai_response['content']
        
        print(f"\n{'='*60}")
        print(f"✅ [AI调用] 回答生成成功！")
        print(f"   ├─ 回答长度: {len(full_response)} 字符")
        print(f"   ├─ finish_reason: {ai_response.get('finish_reason')}")
        print(f"   └─ is_truncated: {ai_response.get('is_truncated')}")
        print(f"{'='*60}\n")
        
        # --- 4. 自动保存错题（如果是批改模式且发现错误）---
        mistake_saved = False
        detected_knowledge_points = []
        
        if is_new_session:
            # 检测是否批改模式且发现错误
            has_mistake = "[MISTAKE_DETECTED]" in full_response
            
            if has_mistake and 'is_review_mode' in locals() and is_review_mode:
                print(f"\n{'='*60}")
                print(f"【错题自动保存】")
                print(f"{'='*60}")
                print(f"[错题保存] ✅ 检测到错误！准备自动保存到错题本...")
                
                try:
                    # 清理AI回复中的特殊标记
                    cleaned_response = full_response.replace("[MISTAKE_DETECTED]", "").strip()
                    
                    # 使用AI提取知识点
                    print(f"[错题保存] 步骤1: 提取知识点...")
                    knowledge_prompt = f"""请分析以下题目和批改内容，提取出3-5个精确的知识点标签。

题目内容：
{ocr_text[:500]}

批改内容：
{cleaned_response[:500]}

要求：
1. 每个知识点标签要精确到具体概念（如"一元二次方程求根公式"而非"方程"）
2. 返回格式：每行一个知识点，使用"- "开头
3. 限制3-5个知识点
4. 按重要性排序

请直接返回知识点列表："""

                    knowledge_messages = [{
                        "role": "user",
                        "content": knowledge_prompt
                    }]
                    
                    knowledge_response = call_qwen_vl_max(knowledge_messages, max_tokens=500)
                    knowledge_text = knowledge_response['content']
                    
                    # 解析知识点
                    import re
                    detected_knowledge_points = [
                        line.strip().lstrip('- ').lstrip('* ').strip()
                        for line in knowledge_text.split('\n')
                        if line.strip() and (line.strip().startswith('-') or line.strip().startswith('*'))
                    ][:5]  # 限制5个
                    
                    if not detected_knowledge_points:
                        detected_knowledge_points = ["综合题型"]
                    
                    print(f"[错题保存] ✓ 提取到 {len(detected_knowledge_points)} 个知识点:")
                    for kp in detected_knowledge_points:
                        print(f"           - {kp}")
                    
                    # 推测学科和年级
                    subject = "未分类"
                    grade = "未分类"  # 【V25.0新增】
                    
                    if any(keyword in ocr_text for keyword in ["方程", "函数", "几何", "代数", "三角", "x", "y", "="]):
                        subject = "数学"
                    elif any(keyword in ocr_text for keyword in ["单词", "语法", "词汇", "句子", "翻译"]):
                        subject = "英语"
                    elif any(keyword in ocr_text for keyword in ["力", "能量", "速度", "电", "光"]):
                        subject = "物理"
                    elif any(keyword in ocr_text for keyword in ["化学", "元素", "反应", "分子"]):
                        subject = "化学"
                    
                    # 【V25.0新增】简单推测年级
                    if any(keyword in ocr_text for keyword in ["小学", "一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]):
                        grade = "小学"
                    elif any(keyword in ocr_text for keyword in ["初中", "初一", "初二", "初三", "七年级", "八年级", "九年级"]):
                        grade = "初中"
                    elif any(keyword in ocr_text for keyword in ["高中", "高一", "高二", "高三"]):
                        grade = "高中"
                    
                    print(f"[错题保存] ✓ 推测学科: {subject}, 年级: {grade}")
                    
                    # 保存到错题本
                    print(f"[错题保存] 步骤2: 保存到错题本...")
                    mistakes = load_mistakes()
                    
                    new_mistake = {
                        "id": str(uuid.uuid4()),
                        "image_base64": request.image_base_64,
                        "question_text": ocr_text,
                        "wrong_answer": "(从批改中提取)",
                        "ai_analysis": cleaned_response,
                        "subject": subject,
                        "grade": grade,  # 【V25.0新增】
                        "knowledge_points": detected_knowledge_points,
                        "created_at": datetime.now().isoformat(),
                        "reviewed_count": 0
                    }
                    
                    mistakes.append(new_mistake)
                    save_mistakes(mistakes)
                    
                    mistake_saved = True
                    print(f"[错题保存] ✅ 错题已自动保存！")
                    print(f"[错题保存] ID: {new_mistake['id'][:8]}...")
                    print(f"{'='*60}\n")
                    
                except Exception as e:
                    print(f"[错题保存] ⚠️ 自动保存失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 保存失败不影响主流程，继续返回AI回答
                    mistake_saved = False
                    detected_knowledge_points = []
            else:
                if 'is_review_mode' in locals() and not is_review_mode:
                    print(f"[错题保存] 非批改模式，跳过错题保存")
                else:
                    print(f"[错题保存] 未检测到错误标记，跳过保存")
        
        # --- 5. 更新会话历史 ---
        print(f"[历史更新] 添加消息到历史...")
        SESSIONS[session_id]["history"].append({"role": "user", "content": request.prompt})
        SESSIONS[session_id]["history"].append({"role": "assistant", "content": full_response})
        print(f"[历史更新] ✓ 当前历史条数: {len(SESSIONS[session_id]['history'])}")

        # --- 6. 准备返回数据 ---
        is_truncated = ai_response.get('is_truncated', False)
        
        return_data = {
            "session_id": session_id,
            "title": SESSIONS[session_id].get("title", "新对话"),
            "response": full_response,
            "is_truncated": is_truncated,
            "mistake_saved": mistake_saved,
            "knowledge_points": detected_knowledge_points if mistake_saved else []
        }
        
        print(f"[返回数据] ✅ 数据准备完成")
        if mistake_saved:
            print(f"[返回数据] ✅ 错题已自动保存并返回知识点")
        print(f"{'#'*70}\n")
        
        return JSONResponse(content=return_data)

    except HTTPException as http_exc:
        print(f"\n{'!'*70}")
        print(f"!!! HTTPException: {http_exc.status_code} - {http_exc.detail}")
        print(f"{'!'*70}\n")
        raise
        
    except Exception as e:
        print(f"\n{'!'*70}")
        print(f"!!! /chat 接口发生错误")
        print(f"!!! 错误类型: {type(e).__name__}")
        print(f"!!! 错误信息: {str(e)}")
        print(f"{'!'*70}\n")
        
        import traceback
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# 错题本API
# ==============================================================================

@app.post("/mistakes/", response_model=MistakeResponse)
def create_mistake(mistake: MistakeCreate):
    """创建新错题"""
    mistakes = load_mistakes()
    
    new_mistake = {
        "id": str(uuid.uuid4()),
        "image_base64": mistake.image_base64,
        "question_text": mistake.question_text,
        "wrong_answer": mistake.wrong_answer,
        "ai_analysis": mistake.ai_analysis,
        "subject": mistake.subject,
        "grade": mistake.grade,  # 【V25.0新增】
        "knowledge_points": mistake.knowledge_points,
        "created_at": datetime.now().isoformat(),
        "reviewed_count": 0
    }
    
    mistakes.append(new_mistake)
    save_mistakes(mistakes)
    
    print(f"✅ 新增错题: ID={new_mistake['id']}, 科目={mistake.subject}, 年级={mistake.grade}")
    return new_mistake

@app.get("/mistakes/")
def get_mistakes(
    subject: Optional[str] = None,
    grade: Optional[str] = None,  # 【V25.0新增】按年级过滤
    limit: int = 100,
    offset: int = 0
):
    """
    【V25.0增强】获取错题列表
    - 支持按科目过滤
    - 支持按年级过滤
    """
    mistakes = load_mistakes()
    
    # 过滤科目
    if subject:
        mistakes = [m for m in mistakes if m.get("subject") == subject]
    
    # 【V25.0新增】过滤年级
    if grade:
        mistakes = [m for m in mistakes if m.get("grade") == grade]
    
    # 排序（最新的在前）
    mistakes = sorted(mistakes, key=lambda x: x.get("created_at", ""), reverse=True)
    
    # 分页
    total = len(mistakes)
    mistakes = mistakes[offset:offset + limit]
    
    return {
        "total": total,
        "items": mistakes,
        "offset": offset,
        "limit": limit
    }

@app.get("/mistakes/{mistake_id}")
def get_mistake(mistake_id: str):
    """获取单个错题详情"""
    mistakes = load_mistakes()
    mistake = next((m for m in mistakes if m["id"] == mistake_id), None)
    
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    # 增加查看次数
    mistake["reviewed_count"] = mistake.get("reviewed_count", 0) + 1
    save_mistakes(mistakes)
    
    return mistake

@app.delete("/mistakes/{mistake_id}")
def delete_mistake(mistake_id: str):
    """删除错题"""
    mistakes = load_mistakes()
    initial_len = len(mistakes)
    mistakes = [m for m in mistakes if m["id"] != mistake_id]
    
    if len(mistakes) == initial_len:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    save_mistakes(mistakes)
    print(f"🗑️ 删除错题: ID={mistake_id}")
    return {"message": "删除成功"}

@app.get("/mistakes/stats/summary")
def get_mistakes_stats():
    """
    【V25.0增强】获取错题统计信息
    - 新增年级统计
    """
    mistakes = load_mistakes()
    
    # 按科目分类
    subjects = {}
    grades = {}  # 【V25.0新增】
    knowledge_points = {}
    
    for mistake in mistakes:
        subject = mistake.get("subject", "未分类")
        subjects[subject] = subjects.get(subject, 0) + 1
        
        # 【V25.0新增】统计年级
        grade = mistake.get("grade", "未分类")
        grades[grade] = grades.get(grade, 0) + 1
        
        for kp in mistake.get("knowledge_points", []):
            knowledge_points[kp] = knowledge_points.get(kp, 0) + 1
    
    return {
        "total_mistakes": len(mistakes),
        "subjects": subjects,
        "grades": grades,  # 【V25.0新增】
        "top_knowledge_points": sorted(
            knowledge_points.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    }

# ==============================================================================
# 【V25.0新增】网络辅助出题工具函数
# ==============================================================================

async def search_web_for_questions(subject: str, knowledge_points: List[str], difficulty: str) -> str:
    """
    【V25.0增强】网络深度爬取辅助出题功能
    
    策略升级：
    1. 搜索并识别题库网站（菁优网、学科网等）
    2. 深度爬取题目详情页
    3. 提取题目文本和图片
    4. 下载图片并转换为可用格式
    5. 返回结构化的真实题目数据
    
    Args:
        subject: 学科
        knowledge_points: 知识点列表
        difficulty: 难度级别
    
    Returns:
        结构化的题目数据（包含图片）
    """
    import requests
    from bs4 import BeautifulSoup
    import base64
    from urllib.parse import urljoin
    
    # 构建搜索关键词（针对题库网站）
    kp_str = " ".join(knowledge_points[:2])
    # 添加图片关键词，增加找到带图题目的概率
    search_query = f"{subject} {kp_str} {difficulty} 练习题 含图 site:jyeoo.com OR site:zujuan.com OR site:cooco.net.cn"
    
    print(f"[深度爬取] 搜索关键词: {search_query}")
    print(f"[深度爬取] 目标: 带图片的真实题目")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # ---- 步骤1: 搜索题库网站 ----
        search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(search_query)}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取题库网站链接（改进版：提取真实URL）
        question_urls = []
        target_sites = ['jyeoo.com', 'zujuan.com', 'cooco.net.cn', '1010jiajiao.com', 'zybang.com']
        
        for result in soup.find_all('div', class_=['result', 'c-container'], limit=20):
            # 方法1：从mu属性提取真实URL（百度搜索结果特有）
            mu_url = result.get('mu')
            if mu_url and any(site in mu_url for site in target_sites):
                question_urls.append(mu_url)
                continue
            
            # 方法2：从data-log属性解析
            data_log = result.get('data-log')
            if data_log:
                try:
                    import re
                    url_match = re.search(r'http[s]?://[^\s"\']+', data_log)
                    if url_match:
                        extracted_url = url_match.group(0)
                        if any(site in extracted_url for site in target_sites):
                            question_urls.append(extracted_url)
                            continue
                except:
                    pass
            
            # 方法3：从链接文本中寻找（备用）
            link = result.find('a', href=True)
            if link and link['href']:
                href = link['href']
                # 尝试访问百度跳转链接获取真实URL
                if 'baidu.com' in href and 'url=' in href:
                    try:
                        real_url_match = re.search(r'url=([^&]+)', href)
                        if real_url_match:
                            import urllib.parse
                            real_url = urllib.parse.unquote(real_url_match.group(1))
                            if any(site in real_url for site in target_sites):
                                question_urls.append(real_url)
                    except:
                        pass
        
        # 去重
        question_urls = list(set(question_urls))
        print(f"[深度爬取] ✓ 找到 {len(question_urls)} 个题库链接")
        
        # 【V25.0增强】如果没找到链接，尝试直接访问题库网站
        if len(question_urls) == 0:
            print(f"[深度爬取] ⚠️ 搜索引擎未返回题库链接，尝试直接访问题库...")
            
            # 构造菁优网搜索URL（最常用的题库网站）
            jyeoo_keywords = f"{subject} {' '.join(knowledge_points[:2])}"
            jyeoo_search_url = f"https://www.jyeoo.com/search?q={requests.utils.quote(jyeoo_keywords)}&type=question"
            question_urls.append(jyeoo_search_url)
            
            print(f"[深度爬取] 直接访问菁优网: {jyeoo_search_url[:60]}...")
        
        # ---- 步骤2: 爬取题目详情（简化版）----
        questions_data = []
        
        for url in question_urls[:3]:  # 只爬取前3个，避免过慢
            try:
                print(f"[深度爬取] 正在访问: {url[:50]}...")
                
                # 访问详情页
                detail_response = requests.get(url, headers=headers, timeout=8)
                detail_response.encoding = 'utf-8'
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                
                # 提取题目文本（通用策略）
                question_text = ""
                
                # 尝试多种选择器（不同网站结构不同）
                possible_selectors = [
                    {'class': 'question'},
                    {'class': 'stem'},
                    {'class': 'timu'},
                    {'class': 'topic-title'},
                    {'id': 'question'}
                ]
                
                for selector in possible_selectors:
                    elem = detail_soup.find('div', selector)
                    if elem:
                        question_text = elem.get_text(strip=True)[:500]  # 限制长度
                        break
                
                # 提取图片URL
                images = []
                img_tags = detail_soup.find_all('img', limit=5)
                for img in img_tags:
                    src = img.get('src') or img.get('data-src')
                    if src and ('question' in src.lower() or 'upload' in src.lower()):
                        # 转换为绝对URL
                        absolute_url = urljoin(url, src)
                        images.append(absolute_url)
                
                if question_text or images:
                    questions_data.append({
                        'text': question_text,
                        'images': images,
                        'source': url
                    })
                    print(f"[深度爬取] ✓ 提取题目: {len(question_text)}字符, {len(images)}张图片")
                    
            except Exception as e:
                print(f"[深度爬取] ⚠️ 爬取失败: {str(e)[:50]}")
                continue
        
        # ---- 步骤3: 格式化返回数据 ----
        if questions_data:
            result_text = f"【网络爬取到 {len(questions_data)} 道真实题目】\n\n"
            
            for i, q in enumerate(questions_data, 1):
                result_text += f"题目{i}:\n"
                result_text += f"内容: {q['text'][:300]}\n"
                
                if q['images']:
                    result_text += f"包含图片: {len(q['images'])}张\n"
                    result_text += f"图片URL: {q['images'][0]}\n"
                    result_text += "【重要】此题包含精确图形，建议直接使用或轻微改编，不要让AI重新生成图形\n"
                
                result_text += f"来源: {q['source'][:80]}...\n"
                result_text += "---\n\n"
            
            result_text += """
【出题建议】
1. 对于包含复杂图形的题目，建议：
   - 直接使用原题（修改数字或文字）
   - 保留图片URL或描述图片内容
   - 不要尝试用SVG重新绘制复杂图形
   
2. 对于纯文字题目：
   - 可以自由改编
   - 适当增加图表辅助（简单图形）
"""
            
            print(f"[深度爬取] ✓ 成功爬取 {len(questions_data)} 道题目")
            return result_text
        else:
            # 降级：返回搜索摘要
            print(f"[深度爬取] ⚠️ 未能爬取到题目，降级为摘要模式")
            return await _fallback_simple_search(subject, knowledge_points, difficulty, headers)
            
    except Exception as e:
        print(f"[深度爬取] ❌ 爬取失败: {e}")
        # 降级策略
        try:
            return await _fallback_simple_search(subject, knowledge_points, difficulty, headers)
        except:
            raise


async def _fallback_simple_search(subject: str, knowledge_points: List[str], difficulty: str, headers: dict) -> str:
    """
    【V25.0增强】降级策略：简单摘要搜索
    即使无法爬取到具体题目，也提供有用的题型指导
    """
    import requests
    from bs4 import BeautifulSoup
    
    kp_str = " ".join(knowledge_points[:3])
    search_query = f"{subject} {kp_str} {difficulty} 练习题"
    search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(search_query)}"
    
    print(f"[降级搜索] 搜索关键词: {search_query}")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result_texts = []
        for result in soup.find_all('div', class_=['result', 'c-container'], limit=10):
            # 提取标题
            title_elem = result.find(['h3', 'a'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 10:  # 过滤太短的标题
                    result_texts.append(f"【题型参考】{title}")
            
            # 提取摘要
            abstract_elem = result.find(['div', 'span'], class_=['c-abstract', 'content-right_8Zs40'])
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
                if len(abstract) > 20:  # 过滤太短的摘要
                    result_texts.append(f"内容: {abstract[:200]}")
            
            result_texts.append("---")
        
        combined_text = "\n".join(result_texts)
        if len(combined_text) > 3000:
            combined_text = combined_text[:3000] + "\n...(已截断)"
        
        print(f"[降级搜索] 提取到 {len(result_texts)//3} 条参考信息，总长度: {len(combined_text)} 字符")
        
        # 如果搜索结果太少，添加通用指导
        if len(combined_text) < 200:
            combined_text += f"""

【出题指导（网络资源不足时）】
主题：{subject} - {kp_str}
难度：{difficulty}

建议题型：
1. 概念理解题：考查{knowledge_points[0] if knowledge_points else '核心概念'}的定义和性质
2. 计算应用题：结合实际场景进行{subject}计算
3. 综合分析题：多个知识点的综合运用

题目要求：
- 难度适中，贴近{difficulty}水平
- 注重知识点的实际应用
- 如需图形，使用简单SVG或详细文字描述
"""
        
        return combined_text if combined_text.strip() else "（网络搜索未返回结果）"
    
    except Exception as e:
        print(f"[降级搜索] ❌ 搜索失败: {e}")
        # 最终降级：返回基础指导
        return f"""
【网络搜索不可用 - 使用AI独立出题】
主题：{subject} - {' '.join(knowledge_points[:3])}
难度：{difficulty}

请根据上述主题，结合学生错题特点，独立生成高质量练习题。
注意：
1. 如需图形，使用简单SVG代码或详细文字描述
2. 避免过于复杂的图形（AI绘制不够精确）
3. 题目应具有典型性和针对性
"""

# ==============================================================================
# AI智能出题API
# ==============================================================================

@app.post("/questions/generate")
async def generate_questions(request: QuestionGenerateRequest):
    """
    【V25.0增强】基于错题生成新题目
    - 支持图表生成（SVG、Markdown表格）
    - 支持网络辅助出题（可选）
    """
    mistakes = load_mistakes()
    
    # 获取指定的错题
    selected_mistakes = [m for m in mistakes if m["id"] in request.mistake_ids]
    
    if not selected_mistakes:
        raise HTTPException(status_code=400, detail="未找到指定的错题")
    
    # 提取知识点和学科信息
    all_knowledge_points = []
    subjects = set()
    for mistake in selected_mistakes:
        all_knowledge_points.extend(mistake.get("knowledge_points", []))
        if mistake.get("subject"):
            subjects.add(mistake["subject"])
    
    knowledge_points_str = "、".join(set(all_knowledge_points)) if all_knowledge_points else "综合知识"
    subject_str = "、".join(subjects) if subjects else "综合"
    
    # 【V25.0新功能】网络辅助出题
    web_reference_text = ""
    if request.allow_web_search:
        print(f"\n{'='*70}")
        print(f"[网络辅助出题] 启用网络搜索模式")
        print(f"{'='*70}\n")
        
        try:
            web_reference_text = await search_web_for_questions(
                subject=subject_str,
                knowledge_points=list(set(all_knowledge_points)),
                difficulty=request.difficulty
            )
            print(f"[网络辅助出题] ✓ 获取到参考资料，长度: {len(web_reference_text)} 字符")
        except Exception as e:
            print(f"[网络辅助出题] ⚠️ 网络搜索失败，降级为纯AI出题: {e}")
            web_reference_text = ""
    
    # 【V25.0增强】构建支持图表生成的AI提示词
    if web_reference_text:
        # 网络辅助模式的Prompt - 强调处理真实题目和图片
        prompt = f"""你是一位经验丰富的教师。我刚刚从题库网站爬取了"{subject_str} {knowledge_points_str}"的真实题目，其中部分包含精确绘制的图形。请你**基于以下真实题目和学生的错题记录**，为学生生成{request.count}道高质量的练习题。

【重要原则】
1. **对于包含复杂图形的题目**（如几何图形、函数图像、实验装置等）：
   - ✅ 直接使用原题，可以修改题干文字或数字
   - ✅ 如果有图片URL，请在题目中说明："请参考原题图片：[图片URL]"
   - ✅ 可以描述图片内容，但不要尝试用SVG重新绘制
   - ❌ 不要让AI生成复杂的SVG图形（AI绘图不够精确）

2. **对于纯文字题目**：
   - 可以自由改编创新
   - 可以添加简单的表格或简单几何图形（圆、三角形等）

【网络爬取的真实题目】
{web_reference_text}

【学生错题分析】
"""
        for i, mistake in enumerate(selected_mistakes, 1):
            prompt += f"""
错题{i}：
- 题目：{mistake.get('question_text', '(无文字识别)')}
- 错误分析：{mistake.get('ai_analysis', '(无分析)')}
- 知识点：{', '.join(mistake.get('knowledge_points', ['未标注']))}
"""
        
        prompt += f"""
【出题要求】
- 难度级别：{request.difficulty}
- 题目数量：{request.count}道
- 知识点：{knowledge_points_str}
- 题型：选择题、填空题、解答题均可
- **请参考网络资料的题型和风格，但务必原创或深度改编，确保题目质量和针对性**

【V25.0新功能 - 图表支持】
你现在可以在题目中加入图表，增强题目的可视化效果：

1. **SVG图形**：当题目需要几何图形、函数图像时，你可以直接在题目内容中嵌入SVG代码
   示例：
   ```
   <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
     <circle cx="100" cy="100" r="50" fill="none" stroke="black" stroke-width="2"/>
     <line x1="100" y1="100" x2="150" y2="100" stroke="blue" stroke-width="2"/>
     <text x="125" y="95" font-size="14">r=50</text>
   </svg>
   ```

2. **Markdown表格**：当题目需要数据表格时，使用Markdown表格语法
   示例：
   ```
   | x | 0 | 1 | 2 | 3 |
   |---|---|---|---|---|
   | y | 1 | 3 | 5 | 7 |
   ```

3. **LaTeX数学公式**：继续使用 $ 或 $$ 包裹公式
   示例：行内公式 $x^2 + y^2 = r^2$，或独立公式 $$\\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}$$

请根据题目需要，适当使用这些可视化工具，让题目更加生动和易于理解。

【输出格式】
请严格按照以下格式输出每道题：

---题目1---
题目内容：
[题目正文，可以包含数学公式、SVG图形或Markdown表格]

答案：
[标准答案]

解析：
[详细解题步骤和知识点说明]

知识点：[知识点1, 知识点2]

---题目2---
...

请确保题目质量高、有针对性、能帮助学生巩固薄弱环节。"""
    else:
        # 纯AI模式的Prompt
        prompt = f"""你是一位经验丰富的教师。请根据学生的错题记录，生成{request.count}道新的练习题。

【错题分析】
"""
        for i, mistake in enumerate(selected_mistakes, 1):
            prompt += f"""
错题{i}：
- 题目：{mistake.get('question_text', '(无文字识别)')}
- 错误分析：{mistake.get('ai_analysis', '(无分析)')}
- 知识点：{', '.join(mistake.get('knowledge_points', ['未标注']))}
"""
        
        prompt += f"""
【出题要求】
- 难度级别：{request.difficulty}
- 题目数量：{request.count}道
- 知识点：{knowledge_points_str}
- 题型：选择题、填空题、解答题均可

【V25.0新功能 - 图表支持】
你现在可以在题目中加入图表，增强题目的可视化效果：

1. **SVG图形**：当题目需要几何图形、函数图像时，你可以直接在题目内容中嵌入SVG代码
   示例：
   ```
   <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
     <circle cx="100" cy="100" r="50" fill="none" stroke="black" stroke-width="2"/>
     <line x1="100" y1="100" x2="150" y2="100" stroke="blue" stroke-width="2"/>
     <text x="125" y="95" font-size="14">r=50</text>
   </svg>
   ```

2. **Markdown表格**：当题目需要数据表格时，使用Markdown表格语法
   示例：
   ```
   | x | 0 | 1 | 2 | 3 |
   |---|---|---|---|---|
   | y | 1 | 3 | 5 | 7 |
   ```

3. **LaTeX数学公式**：继续使用 $ 或 $$ 包裹公式
   示例：行内公式 $x^2 + y^2 = r^2$，或独立公式 $$\\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}$$

请根据题目需要，适当使用这些可视化工具，让题目更加生动和易于理解。

【输出格式】
请严格按照以下格式输出每道题：

---题目1---
题目内容：
[题目正文，可以包含数学公式、SVG图形或Markdown表格]

答案：
[标准答案]

解析：
[详细解题步骤和知识点说明]

知识点：[知识点1, 知识点2]

---题目2---
...

请确保题目质量高、有针对性、能帮助学生巩固薄弱环节。"""

    try:
        # 调用通义千问API
        messages = [{"role": "user", "content": prompt}]
        response = dashscope.Generation.call(
            model="qwen-plus",
            messages=messages,
            result_format='message'
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI服务调用失败")
        
        ai_response = response.output.choices[0].message.content
        
        # 解析生成的题目
        generated_questions = []
        question_blocks = re.split(r'---题目\d+---', ai_response)[1:]  # 跳过第一个空块
        
        for block in question_blocks:
            try:
                # 提取题目内容
                content_match = re.search(r'题目内容：\s*\n(.*?)\n\n答案：', block, re.DOTALL)
                answer_match = re.search(r'答案：\s*\n(.*?)\n\n解析：', block, re.DOTALL)
                explanation_match = re.search(r'解析：\s*\n(.*?)\n\n知识点：', block, re.DOTALL)
                kp_match = re.search(r'知识点：\[(.*?)\]', block)
                
                if content_match and answer_match:
                    question_id = str(uuid.uuid4())
                    question = {
                        "id": question_id,
                        "content": content_match.group(1).strip(),
                        "answer": answer_match.group(1).strip(),
                        "explanation": explanation_match.group(1).strip() if explanation_match else "",
                        "knowledge_points": [kp.strip() for kp in kp_match.group(1).split(',')] if kp_match else [],
                        "difficulty": request.difficulty,
                        "source_mistake_ids": request.mistake_ids,
                        "created_at": datetime.now().isoformat()
                    }
                    generated_questions.append(question)
            except Exception as e:
                print(f"⚠️ 解析题目块失败: {e}")
                continue
        
        if not generated_questions:
            # 如果解析失败，返回原始文本
            generated_questions = [{
                "id": str(uuid.uuid4()),
                "content": ai_response,
                "answer": "请参考解析",
                "explanation": "",
                "knowledge_points": list(set(all_knowledge_points)),
                "difficulty": request.difficulty,
                "source_mistake_ids": request.mistake_ids,
                "created_at": datetime.now().isoformat()
            }]
        
        # 保存生成的题目
        questions = load_questions()
        questions.extend(generated_questions)
        save_questions(questions)
        
        print(f"✅ 成功生成{len(generated_questions)}道题目")
        return {
            "message": f"成功生成{len(generated_questions)}道题目",
            "questions": generated_questions
        }
        
    except Exception as e:
        print(f"❌ 生成题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成题目失败: {str(e)}")

@app.get("/questions/")
def get_questions(limit: int = 100, offset: int = 0):
    """获取生成的题目列表"""
    questions = load_questions()
    
    # 排序（最新的在前）
    questions = sorted(questions, key=lambda x: x.get("created_at", ""), reverse=True)
    
    # 分页
    total = len(questions)
    questions = questions[offset:offset + limit]
    
    return {
        "total": total,
        "items": questions,
        "offset": offset,
        "limit": limit
    }

@app.delete("/questions/{question_id}")
def delete_question(question_id: str):
    """删除生成的题目"""
    questions = load_questions()
    initial_len = len(questions)
    questions = [q for q in questions if q["id"] != question_id]
    
    if len(questions) == initial_len:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    save_questions(questions)
    print(f"🗑️ 删除题目: ID={question_id}")
    return {"message": "删除成功"}

# ==============================================================================
# 试卷导出API
# ==============================================================================

class ExportRequest(BaseModel):
    """导出试卷请求"""
    question_ids: List[str]
    title: str = "练习题集"

@app.post("/export/markdown")
def export_markdown(request: ExportRequest):
    """导出为Markdown格式"""
    questions = load_questions()
    selected = [q for q in questions if q["id"] in request.question_ids]
    
    if not selected:
        raise HTTPException(status_code=400, detail="未找到指定的题目")
    
    # 生成Markdown
    markdown = f"# {request.title}\n\n"
    markdown += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown += f"---\n\n"
    
    for i, q in enumerate(selected, 1):
        markdown += f"## 题目{i}\n\n"
        markdown += f"{q['content']}\n\n"
        markdown += f"**答案：** {q['answer']}\n\n"
        if q.get('explanation'):
            markdown += f"**解析：** {q['explanation']}\n\n"
        if q.get('knowledge_points'):
            markdown += f"**知识点：** {', '.join(q['knowledge_points'])}\n\n"
        markdown += f"---\n\n"
    
    return {
        "content": markdown,
        "filename": f"{request.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    }

@app.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """
    【V25.0新功能】导出为PDF格式（支持LaTeX公式渲染）
    
    技术方案：
    1. 将题目的Markdown内容转换为HTML
    2. 在HTML中注入MathJax配置和CDN
    3. 使用Pyppeteer（无头浏览器）加载HTML并执行MathJax渲染
    4. 将渲染后的页面打印为PDF
    
    这确保了LaTeX公式能够正确显示在PDF中
    """
    from pyppeteer import launch
    import tempfile
    import markdown
    import asyncio
    
    questions = load_questions()
    selected = [q for q in questions if q["id"] in request.question_ids]
    
    if not selected:
        raise HTTPException(status_code=400, detail="未找到指定的题目")
    
    print(f"\n{'='*70}")
    print(f"[PDF导出] 准备导出{len(selected)}道题目")
    print(f"{'='*70}\n")
    
    try:
        # ---- 步骤1: 构建包含MathJax的自包含HTML ----
        print("[PDF导出] 步骤1: 构建HTML文档...")
        
        # HTML头部 - 注入MathJax配置
        html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>练习题集</title>
    
    <!-- 【V25.0优化】MathJax 3配置 - 使用同步加载确保渲染 -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
                processEscapes: true,
                processEnvironments: true
            },
            svg: {
                fontCache: 'global',
                displayAlign: 'left'
            },
            startup: {
                pageReady: () => {
                    return MathJax.startup.defaultPageReady().then(() => {
                        console.log('✅ MathJax渲染完成');
                        document.body.setAttribute('data-mathjax-ready', 'true');
                    }).catch((err) => {
                        console.error('❌ MathJax渲染失败:', err);
                        document.body.setAttribute('data-mathjax-ready', 'error');
                    });
                }
            },
            options: {
                enableMenu: false,
                renderActions: {
                    addMenu: []
                }
            }
        };
    </script>
    <!-- 使用CDN备用方案：jsDelivr（主）-> unpkg（备用） -->
    <script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    
    <!-- 样式 -->
    <style>
        body {
            font-family: "SimSun", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #5C6AC4;
            border-bottom: 3px solid #5C6AC4;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        .question {
            margin-bottom: 40px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 10px;
            border-left: 4px solid #5C6AC4;
        }
        .question-title {
            font-size: 18px;
            font-weight: bold;
            color: #5C6AC4;
            margin-bottom: 15px;
        }
        .question-content {
            margin-bottom: 15px;
            font-size: 14px;
            white-space: pre-wrap;
        }
        .answer {
            background: #e8f5e9;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .explanation {
            background: #fff3e0;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .knowledge-points {
            margin-top: 10px;
            font-size: 12px;
        }
        .knowledge-point {
            display: inline-block;
            background: #e3f2fd;
            padding: 4px 10px;
            border-radius: 4px;
            margin-right: 8px;
            margin-top: 5px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        table td, table th {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
    </style>
</head>
<body>
"""
        
        # 添加标题
        html_content += f"""
    <h1>{request.title}</h1>
    <p style="text-align: center; color: #999; margin-bottom: 40px;">
        生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
    </p>
"""
        
        # ---- 步骤2: 添加每道题目 ----
        print(f"[PDF导出] 步骤2: 转换{len(selected)}道题目为HTML...")
        
        for i, q in enumerate(selected, 1):
            # 使用markdown库转换Markdown为HTML
            content_html = markdown.markdown(q['content'], extensions=['extra', 'nl2br'])
            answer_html = markdown.markdown(q['answer'])
            explanation_html = markdown.markdown(q.get('explanation', '')) if q.get('explanation') else ''
            
            html_content += f"""
    <div class="question">
        <div class="question-title">题目 {i}</div>
        <div class="question-content">{content_html}</div>
        
        <div class="answer">
            <strong style="color: #4CAF50;">答案：</strong>
            {answer_html}
        </div>
"""
            
            if explanation_html:
                html_content += f"""
        <div class="explanation">
            <strong style="color: #FF9800;">解析：</strong>
            {explanation_html}
        </div>
"""
            
            # 知识点
            if q.get('knowledge_points'):
                kp_tags = ''.join([f'<span class="knowledge-point">{kp}</span>' 
                                   for kp in q['knowledge_points']])
                html_content += f"""
        <div class="knowledge-points">
            <strong>知识点：</strong>{kp_tags}
        </div>
"""
            
            html_content += "    </div>\n"
        
        # HTML尾部
        html_content += """
    <!-- 等待MathJax渲染完成的标记 -->
    <script>
        // 渲染完成后设置标记
        if (window.MathJax) {
            MathJax.startup.promise.then(() => {
                document.body.setAttribute('data-mathjax-ready', 'true');
            });
        }
    </script>
</body>
</html>
"""
        
        print(f"[PDF导出] ✓ HTML文档构建完成, 大小: {len(html_content)} 字符")
        
        # ---- 步骤3: 保存临时HTML文件 ----
        temp_html = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.html')
        temp_html.write(html_content)
        temp_html_path = temp_html.name
        temp_html.close()
        
        print(f"[PDF导出] ✓ HTML文件保存至: {temp_html_path}")
        
        # 【调试功能】同时保存一份到固定位置，方便调试
        try:
            # 使用绝对路径确保目录创建成功
            debug_dir = Path(__file__).parent / "generated_papers"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_html_path = debug_dir / "latest_export_debug.html"
            
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"[PDF导出] 📝 调试HTML已保存至: {debug_html_path}")
            print(f"[PDF导出] 💡 提示：可在浏览器中打开此文件检查公式渲染")
        except Exception as debug_err:
            print(f"[PDF导出] ⚠️ 调试HTML保存失败（不影响PDF生成）: {debug_err}")
        
        # ---- 步骤4: 使用Pyppeteer启动无头浏览器并渲染 ----
        print("[PDF导出] 步骤3: 启动无头浏览器...")
        
        browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.newPage()
        
        print("[PDF导出] ✓ 浏览器启动成功")
        print(f"[PDF导出] 步骤4: 加载HTML并执行MathJax渲染...")
        
        # 【V25.0优化】计算超时时间：每道题2分钟
        question_count = len(selected)
        timeout_per_question = 120000  # 2分钟 = 120秒 = 120000毫秒
        total_timeout = question_count * timeout_per_question
        print(f"[PDF导出] 题目数量: {question_count}道, 超时时间: {total_timeout/1000}秒")
        
        # 加载HTML文件
        await page.goto(f'file://{temp_html_path}', {
            'waitUntil': 'networkidle0',
            'timeout': total_timeout
        })
        
        # 【V25.0优化】等待MathJax渲染完成（动态超时时间）
        print("[PDF导出] 等待MathJax渲染...")
        mathjax_ready = False
        
        try:
            # 第一次尝试：等待渲染完成标记
            await page.waitForSelector('body[data-mathjax-ready="true"]', {'timeout': total_timeout})
            mathjax_ready = True
            print("[PDF导出] ✓ MathJax渲染完成（通过标记检测）")
        except Exception as e:
            # 如果标记检测失败，手动等待并检查
            print(f"[PDF导出] ⚠️ 标记检测超时，尝试手动等待...")
            
            try:
                # 额外等待5秒让MathJax完成渲染
                await asyncio.sleep(5)
                
                # 检查是否有MathJax渲染后的元素（.MathJax或.mjx-chtml）
                has_mathjax = await page.evaluate('''() => {
                    const mjElements = document.querySelectorAll('.MathJax, .mjx-chtml, mjx-container');
                    return mjElements.length > 0;
                }''')
                
                if has_mathjax:
                    mathjax_ready = True
                    print(f"[PDF导出] ✓ MathJax渲染完成（检测到渲染元素）")
                else:
                    print(f"[PDF导出] ⚠️ 未检测到MathJax元素，可能渲染失败")
            except Exception as e2:
                print(f"[PDF导出] ⚠️ 手动检测失败: {e2}")
        
        if not mathjax_ready:
            print("[PDF导出] ⚠️ MathJax可能未完全渲染，但继续生成PDF")
        
        # ---- 步骤5: 生成PDF ----
        print("[PDF导出] 步骤5: 生成PDF文件...")
        
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf_path = temp_pdf.name
        temp_pdf.close()
        
        await page.pdf({
            'path': temp_pdf_path,
            'format': 'A4',
            'margin': {
                'top': '20mm',
                'bottom': '20mm',
                'left': '15mm',
                'right': '15mm'
            },
            'printBackground': True
        })
        
        print(f"[PDF导出] ✓ PDF生成成功: {temp_pdf_path}")
        
        # 关闭浏览器
        await browser.close()
        
        # 清理临时HTML文件
        os.remove(temp_html_path)
        
        print(f"{'='*70}")
        print(f"[PDF导出] ✅ 导出完成")
        print(f"{'='*70}\n")
        
        # 返回PDF文件
        return FileResponse(
            temp_pdf_path,
            media_type='application/pdf',
            filename=f"{request.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            background=None  # 让FastAPI自动管理临时文件清理
        )
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"[PDF导出] ❌ 导出失败")
        print(f"[PDF导出] 错误: {e}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")

# ==============================================================================
# 微信小程序API接口
# ==============================================================================

@app.post("/process_image_for_miniapp")
async def process_image_for_miniapp(request: MiniAppRequest):
    """
    【微信小程序专用接口】处理单张图片的解题或批改
    
    功能：
    - 接收Base64编码的图片和操作模式
    - 复用现有的OCR和AI处理流程
    - 返回简化的JSON响应
    
    Args:
        request: MiniAppRequest对象
            - image_base_64: Base64编码的图片
            - mode: 'solve'(解题) 或 'review'(批改)
    
    Returns:
        成功: {"status": "success", "result": "AI生成的Markdown文本..."}
        失败: {"status": "error", "message": "错误信息"}
    """
    
    print(f"\n{'='*70}")
    print(f"[小程序API] 收到请求")
    print(f"[小程序API] 模式: {request.mode}")
    print(f"[小程序API] 图片大小: {len(request.image_base_64)} 字符")
    print(f"{'='*70}\n")
    
    try:
        # ---- 步骤1: Base64解码图片 ----
        print("[小程序API] 步骤1: 解码Base64图片...")
        image_bytes = base64.b64decode(request.image_base_64)
        image = Image.open(io.BytesIO(image_bytes))
        print(f"[小程序API] ✓ 图片解码成功, 尺寸: {image.size}")
        
        # ---- 步骤2: OCR识别 ----
        print("[小程序API] 步骤2: 执行OCR识别...")
        ocr_text = extract_text_with_pix2text(image)
        print(f"[小程序API] ✓ OCR识别完成, 提取文本长度: {len(ocr_text)} 字符")
        print(f"[小程序API] OCR文本预览: {ocr_text[:100]}...")
        
        # ---- 步骤3: 根据模式构建Prompt ----
        print(f"[小程序API] 步骤3: 构建{request.mode}模式的Prompt...")
        
        if request.mode == 'solve':
            base_prompt = "请对图片中的所有题目进行详细解答，写出完整的解题过程和思路。"
            enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{base_prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身。
"""
        else:  # mode == 'review'
            base_prompt = "请对图片中的所有题目及其答案进行批改，指出对错，如果答案错误请给出正确解法。"
            enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{base_prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身。
"""
        
        print(f"[小程序API] ✓ Prompt构建完成")
        
        # ---- 步骤4: 构建多模态消息（复用现有架构）----
        print("[小程序API] 步骤4: 构建多模态消息...")
        messages = [{
            "role": "user",
            "content": [
                {'text': enhanced_prompt},
                {'image': f"data:image/png;base64,{request.image_base_64}"}
            ]
        }]
        print(f"[小程序API] ✓ 混合输入消息构建完成（OCR文本 + 原图）")
        
        # ---- 步骤5: 调用通义千问AI ----
        print("[小程序API] 步骤5: 调用通义千问AI...")
        ai_response = call_qwen_vl_max(messages)
        result_text = ai_response['content']
        print(f"[小程序API] ✓ AI回答生成成功")
        print(f"[小程序API] 回答长度: {len(result_text)} 字符")
        print(f"[小程序API] 回答预览: {result_text[:150]}...")
        
        # ---- 步骤6: 返回成功响应 ----
        print(f"\n{'='*70}")
        print(f"[小程序API] ✅ 处理成功")
        print(f"{'='*70}\n")
        
        return JSONResponse(content={
            "status": "success",
            "result": result_text
        })
        
    except Exception as e:
        # ---- 错误处理 ----
        error_message = str(e)
        print(f"\n{'='*70}")
        print(f"[小程序API] ❌ 处理失败")
        print(f"[小程序API] 错误类型: {type(e).__name__}")
        print(f"[小程序API] 错误信息: {error_message}")
        print(f"{'='*70}\n")
        
        import traceback
        print(f"[小程序API] 完整堆栈跟踪：")
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"{type(e).__name__}: {error_message}"
            }
        )

# ==============================================================================
# 原有的聊天功能保留
# ==============================================================================

# ... (保留原来的图片处理和聊天功能)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

