# ==============================================================================
# 完整 main.py - 【V23.0 个性化学习系统 - 认证 + 错题本 + 智能出题】
# 核心特性：
# 1. OCR增强（Pix2Text）+ 原图视觉（通义千问）= 混合输入架构
# 2. 删除后端自动续答 - 由前端循环处理续答逻辑
# 3. 追问图片记忆修复 - 每次追问都重新发送图片，避免AI遗忘或幻觉
# 4. 完整对话历史 - 追问时重建包含图片的完整消息历史
# 5. 优化提示词 - 避免暴露技术细节，全中文回答
# 6. 【V22.1】智能图像增强 - OCR前自动优化画质（锐化+对比度增强）
# 7. 【V23.0 Feature 1】用户认证系统 - 注册/登录/JWT
# 8. 【V23.0 Feature 2】错题本系统 - 自动保存错题
# 9. 【V23.0 Feature 3】智能出题 - 知识点提取和题目生成
# 10. 【V23.0 Feature 4】试卷生成 - Markdown转PDF下载
# ==============================================================================

import os
import io
import re
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import dashscope
from typing import Optional, List
from pydantic import BaseModel
import base64
from fastapi.responses import JSONResponse
from PIL import Image
import tempfile

from dashscope import MultiModalConversation
from pix2text import Pix2Text

# 【V22.1】导入图像增强模块
from image_enhancer import advanced_image_processing_pipeline

# 【V23.0 Feature 1】导入数据库和认证模块
try:
    from database import init_db
    from auth_routes import router as auth_router
    print("✅ 数据库和认证模块导入成功")
except ImportError as e:
    print(f"⚠️ 数据库/认证模块导入失败: {e}")
    print("   错题本和智能出题功能将不可用")
    auth_router = None


SESSIONS = {}
# --- 1. 初始化 ---
load_dotenv()
app = FastAPI()

# 初始化 阿里云通义千问 (配置API Key)
print("正在配置通义千问API Key...")
try:
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key: raise ValueError("API Key not found in .env file")
    print("通义千问API Key配置成功。")
except Exception as e:
    print(f"!!! 配置通义千问API Key失败: {e}")

# 初始化 Pix2Text OCR引擎
print("正在初始化 Pix2Text OCR引擎...")
try:
    p2t = Pix2Text(analyzer_config=dict(model_name='mfd'))
    print("Pix2Text OCR引擎初始化成功。")
except Exception as e:
    print(f"!!! Pix2Text初始化失败: {e}")
    p2t = None

# --- 2. FastAPI应用配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 【V22.1】集成统一智能API路由
try:
    from api_routes import router as api_router
    app.include_router(api_router)
    print("✅ 统一智能API路由已加载: /api/solve, /api/question_bank")
except ImportError as e:
    print(f"⚠️ 统一API路由加载失败: {e}")
    print("   前端功能不受影响，可选功能模块")

# 【V23.0 Feature 1】集成认证路由
if auth_router:
    app.include_router(auth_router)
    print("✅ 用户认证路由已加载: /auth/register, /auth/login, /auth/me")
    
    # 初始化数据库
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ 数据库初始化失败: {e}")

# 【V23.0 Feature 2】集成错题本路由
try:
    from mistake_routes import router as mistake_router
    app.include_router(mistake_router)
    print("✅ 错题本路由已加载: GET/POST /mistakes, PUT/DELETE /mistakes/{id}")
except ImportError as e:
    print(f"⚠️ 错题本路由加载失败: {e}")
    print("   错题本功能将不可用")

# 【V23.0 Feature 3】集成智能出题路由
try:
    from question_generation_routes import router as question_gen_router
    app.include_router(question_gen_router)
    print("✅ 智能出题路由已加载: /ai-learning/generate_knowledge_points, /ai-learning/generate_questions")
except ImportError as e:
    print(f"⚠️ 智能出题路由加载失败: {e}")
    print("   智能出题功能将不可用")

# 【V23.0 Feature 4】集成试卷生成路由
try:
    from paper_generation_routes import router as paper_router
    app.include_router(paper_router)
    print("✅ 试卷生成路由已加载: POST/GET /papers, GET /papers/{id}/download/{version}")
except ImportError as e:
    print(f"⚠️ 试卷生成路由加载失败: {e}")
    print("   试卷生成功能将不可用")

@app.get("/")
def read_root():
    return {
        "message": "AI解题后端服务正在运行 (V23.0 个性化学习系统 - 全功能完成)",
        "version": "V23.0-F4-COMPLETE",
        "features": [
            "智能图像增强（锐化 + CLAHE对比度增强）",
            "混合输入架构（OCR + 视觉理解）",
            "追问图片记忆修复",
            "统一智能API（/api/solve）",
            "题库检索API（/api/question_bank）",
            "【Feature 1 ✅】用户认证系统（注册/登录/JWT）",
            "【Feature 2 ✅】个性化错题本（自动检测+手动管理）",
            "【Feature 3 ✅】智能出题系统（知识点提炼+AI生成题目）",
            "【Feature 4 ✅】试卷生成与下载（学生版/教师版PDF）"
        ],
        "api_docs": "/docs",
        "auth": {
            "register": "/auth/register",
            "login": "/auth/login",
            "me": "/auth/me"
        },
        "mistakes": {
            "list": "GET /mistakes",
            "create": "POST /mistakes",
            "detail": "GET /mistakes/{id}",
            "update": "PUT /mistakes/{id}",
            "delete": "DELETE /mistakes/{id}",
            "stats": "GET /mistakes/stats/summary"
        },
        "ai_learning": {
            "generate_knowledge_points": "POST /ai-learning/generate_knowledge_points",
            "generate_questions": "POST /ai-learning/generate_questions",
            "my_questions": "GET /ai-learning/my_questions",
            "delete_question": "DELETE /ai-learning/my_questions/{id}"
        },
        "papers": {
            "create": "POST /papers/",
            "list": "GET /papers/",
            "download": "GET /papers/{id}/download/{version}",
            "delete": "DELETE /papers/{id}"
        }
    }
# ==============================================================================
# 完整 main.py - 第二部分: 核心API接口
# ==============================================================================

# --- 图片预处理函数 (增强OCR效果) ---
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

# --- OCR识别函数 (使用Pix2Text) ---
def extract_text_with_pix2text(image: Image.Image) -> str:
    """
    使用Pix2Text识别图片中的文字和公式，返回清洁的LaTeX文本
    
    【V22.1更新】集成智能图像增强流水线：
    1. 基础预处理（尺寸、格式）
    2. 高级画质优化（锐化 + CLAHE对比度增强）
    3. OCR识别（Pix2Text）
    4. 降级策略：如果增强后OCR失败，则使用原始预处理图像重试
    """
    if p2t is None:
        return "[OCR引擎未初始化]"
    
    try:
        # 步骤1：基础预处理（统一格式、调整尺寸）
        print("[OCR流程] 步骤1: 基础预处理")
        processed_img = image_preprocess_v2(image)
        
        # 【新增V22.1】步骤2：高级图像增强（锐化 + 对比度增强）
        print("[OCR流程] 步骤2: 调用高级图像增强流水线")
        enhanced_img = advanced_image_processing_pipeline(
            processed_img, 
            sharpen_amount=1.5,      # 锐化强度（1.0-2.0）
            clahe_clip_limit=2.0     # 对比度限制（1.0-4.0）
        )
        
        # 步骤3：使用增强后的图像进行OCR识别
        print("[OCR流程] 步骤3: 使用增强后的图像进行OCR识别")
        result = p2t.recognize(enhanced_img)
        
        # 提取文本内容
        if isinstance(result, dict) and 'text' in result:
            ocr_text = result['text']
        elif isinstance(result, str):
            ocr_text = result
        else:
            ocr_text = str(result)
        
        # 清理文本 - 移除多余空白但保留结构
        ocr_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ocr_text)  # 多个空行合并为两个
        ocr_text = ocr_text.strip()
        
        print(f"[OCR识别成功] ✅ 提取了 {len(ocr_text)} 个字符")
        return ocr_text
    
    except Exception as e:
        # 【新增V22.1】降级策略：如果增强后OCR失败，尝试使用原始预处理图像
        print(f"!!! [OCR流程] 使用增强图像识别失败: {e}")
        print(f"[OCR流程] 🔄 启动降级策略：尝试使用原始预处理图像...")
        
        try:
            # 使用未经高级增强的 processed_img 重试
            result = p2t.recognize(processed_img)
            
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
            
            print(f"[OCR识别成功] ✅ 降级策略成功，提取了 {len(ocr_text)} 个字符")
            return ocr_text
            
        except Exception as fallback_error:
            # 两次尝试都失败
            print(f"!!! [OCR流程] 降级策略也失败了: {fallback_error}")
            return "[OCR识别失败]"

# --- 统一的AI调用函数 ---
def call_qwen_vl_max(messages: list, model: str = 'qwen-vl-max', max_tokens: int = 8192) -> dict:
    """
    调用通义千问模型并返回包含'content'和'finish_reason'的字典。
    """
    print(f"\n--- 正在调用通义千问 '{model}' API，历史记录有 {len(messages)} 条... ---")
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

    # 更详细的日志输出
    print(f"--- API调用成功, finish_reason: {finish_reason} ,len(text_content): {len(text_content)},(类型: {type(finish_reason)}) ---")
    
    # 判断是否截断：finish_reason为'length'或者响应长度接近max_tokens
    is_truncated = (finish_reason == 'length') or (finish_reason is None and len(text_content) > 4000)
    
    return {"content": text_content, "finish_reason": finish_reason, "is_truncated": is_truncated}

# --- Pydantic模型，用于校验前端发来的JSON数据 ---
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    prompt: str
    image_base_64: Optional[str] = None # 注意：我们用 base_64 替代了文件上传

# --- 【全新】的统一聊天接口 (混合输入架构版) ---
@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
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
    
    temp_image_path = None # 初始化临时文件路径变量
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
                print(f"[错误] 当前所有会话ID: {list(SESSIONS.keys())}")
                raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或已过期")
            
            print(f"[继续会话] session_id: {session_id}")
            print(f"[继续会话] 用户提问: {request.prompt[:80]}...")
            print(f"[继续会话] 历史记录数: {len(SESSIONS[session_id]['history'])}")
            print(f"[继续会话] 有原始图片: {bool(SESSIONS[session_id].get('image_base_64'))}")
            
            
        # --- 【核心创新】: 混合输入架构 - OCR文本 + 原始图片 ---
        messages_to_send = []
        if is_new_session:
            # A路: 使用Pix2Text进行OCR识别
            print("[混合输入架构] 步骤1: 使用Pix2Text进行OCR识别...")
            image_bytes = base64.b64decode(request.image_base_64)
            image = Image.open(io.BytesIO(image_bytes))
            ocr_text = extract_text_with_pix2text(image)
            
            # B路: 保留原始图片
            print("[混合输入架构] 步骤2: 构建混合输入消息...")
            
            # 【Feature 2】检测是否是批改模式
            is_review_mode = any(keyword in request.prompt for keyword in ["批改", "改", "检查", "对错"])
            print(f"[混合输入架构] 是否批改模式: {is_review_mode}")
            
            # 构建增强Prompt - 将OCR文本嵌入到用户提示中
            if is_review_mode:
                # 【Feature 2】批改模式的特殊Prompt（包含错题检测标记）
                enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{request.prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身。

【特别要求】（批改模式）
如果学生的答案有错误，请在回答的开头加上特殊标记：[MISTAKE_DETECTED]
如果学生的答案完全正确，请在回答的开头加上：[CORRECT]
然后再给出详细的批改意见。
"""
                print(f"[混合输入架构] 使用批改模式Prompt（包含错题检测标记）")
            else:
                # 普通解题模式
                enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{request.prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身
"""
                print(f"[混合输入架构] 使用普通解题模式Prompt")
            
            # 构建混合输入消息: text(增强Prompt + OCR结果) + image(原始图片)
            messages_to_send.append({
                "role": "user",
                "content": [
                    {'text': enhanced_prompt},
                    {'image': f"data:image/png;base64,{request.image_base_64}"}
                ]
            })
            
            print("[混合输入架构] 混合消息构建完成，同时包含OCR文本和原始图片")
            
        else:
            # 对于追问，需要重新构建完整的对话历史，包含原始图片
            # 【关键修复】: 每次追问都要带上图片，避免AI遗忘或产生幻觉
            print(f"\n[追问模式] 开始重新构建对话历史...")
            
            # 获取原始图片
            original_image_base64 = SESSIONS[session_id].get("image_base_64")
            
            if not original_image_base64:
                print(f"[错误] 会话中没有找到原始图片！")
                print(f"[错误] session数据: {SESSIONS[session_id].keys()}")
                raise HTTPException(status_code=500, detail="会话图片丢失，请重新开始对话")
            
            print(f"[追问模式] ✓ 找到原始图片，大小: {len(original_image_base64)} 字符")
            
            # 检查历史记录
            history = SESSIONS[session_id]["history"]
            if len(history) == 0: 
                print(f"[错误] 会话历史为空！")
                raise HTTPException(status_code=500, detail="会话历史为空，请重新开始对话")
            
            print(f"[追问模式] ✓ 历史记录数: {len(history)}")
            
            # 第一条消息：用户的首次提问 + 图片
            first_user_message = history[0]
            print(f"[追问模式] ✓ 首次提问: {first_user_message['content'][:50]}...")
            
            messages_to_send = [{
                "role": "user",
                "content": [
                    {'text': first_user_message["content"]},
                    {'image': f"data:image/png;base64,{original_image_base64}"}
                ]
            }]
            print(f"[追问模式] ✓ 第1条消息已构建（包含图片）")
            
            # 添加后续的对话历史（跳过第一条，因为已经处理了）
            for i, msg in enumerate(history[1:], start=2):
                messages_to_send.append(msg)
                print(f"[追问模式] ✓ 第{i}条消息已添加 ({msg['role']})")
            
            # 添加当前的追问
            messages_to_send.append({"role": "user", "content": request.prompt})
            print(f"[追问模式] ✓ 第{len(messages_to_send)}条消息已添加（当前追问）")
            
            print(f"[追问模式] ✅ 对话历史重建完成！")
            print(f"[追问模式] 📊 总消息数: {len(messages_to_send)} 条")
            print(f"[追问模式] 📷 图片位置: 第1条消息中")

        
        # --- 3. 调用大模型 (删除自动续答，直接调用) ---
        print(f"\n{'='*60}")
        print(f"[AI调用] 准备调用通义千问...")
        print(f"[AI调用] 消息数: {len(messages_to_send)} 条")
        print(f"{'='*60}")
        
        try:
            ai_response = call_qwen_vl_max(messages_to_send)
            full_response = ai_response['content']
            
            print(f"\n{'='*60}")
            print(f"✅ [AI调用] 回答生成成功！")
            print(f"   ├─ 回答长度: {len(full_response)} 字符")
            print(f"   ├─ finish_reason: {ai_response.get('finish_reason')}")
            print(f"   └─ is_truncated: {ai_response.get('is_truncated')}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ [AI调用] 调用失败！")
            print(f"   ├─ 错误类型: {type(e).__name__}")
            print(f"   ├─ 错误信息: {str(e)}")
            print(f"   └─ 消息数: {len(messages_to_send)}")
            print(f"{'='*60}\n")
            raise
        
        # --- 【Feature 2】检测并自动保存错题 ---
        print(f"\n{'='*60}")
        print(f"【Feature 2: 错题检测】")
        print(f"{'='*60}")
        
        # 检测是否批改模式且发现错误
        has_mistake = "[MISTAKE_DETECTED]" in full_response
        is_correct = "[CORRECT]" in full_response
        
        print(f"[错题检测] 是否批改模式: {is_review_mode if 'is_review_mode' in locals() else False}")
        print(f"[错题检测] 发现错误标记: {has_mistake}")
        print(f"[错题检测] 完全正确标记: {is_correct}")
        
        # 如果发现错误，尝试自动保存错题
        if has_mistake:
            print(f"[错题检测] ✅ 检测到错误！准备保存错题...")
            
            try:
                # 尝试导入并保存错题
                from models import Mistake as MistakeModel
                from database import SessionLocal
                from auth import decode_access_token
                
                # 这里需要从请求头获取token（如果有的话）
                # 暂时先记录，后续版本可以完善认证集成
                print(f"[错题检测] ⚠️ 注意：当前/chat接口未集成用户认证")
                print(f"[错题检测] ⚠️ 需要用户登录后才能自动保存错题")
                print(f"[错题检测] 💡 提示：可以手动调用 POST /mistakes 接口保存错题")
                
            except Exception as e:
                print(f"[错题检测] ⚠️ 自动保存错题失败: {e}")
                print(f"[错题检测] 💡 用户可以通过错题本API手动添加")
        
        elif is_correct:
            print(f"[错题检测] ✅ 学生答案完全正确，无需保存")
        else:
            print(f"[错题检测] 非批改模式或未检测到特殊标记")
        
        print(f"{'='*60}\n")
        
        # --- 4. 更新会话历史 (只存文本，保持简洁) ---
        print(f"[历史更新] 添加用户消息到历史...")
        SESSIONS[session_id]["history"].append({"role": "user", "content": request.prompt})
        print(f"[历史更新] 添加AI回答到历史...")
        SESSIONS[session_id]["history"].append({"role": "assistant", "content": full_response})
        print(f"[历史更新] ✓ 历史更新完成，当前历史条数: {len(SESSIONS[session_id]['history'])}")

        # --- 5. 准备返回给前端的数据 ---
        # 判断是否截断（用于前端手动续答）
        is_truncated = ai_response.get('is_truncated', False)
        
        print(f"\n[返回数据] 准备返回给前端...")
        print(f"[返回数据] session_id: {session_id[:16]}...")
        print(f"[返回数据] response长度: {len(full_response)} 字符")
        print(f"[返回数据] is_truncated: {is_truncated}")
        
        return_data = {
            "session_id": session_id,
            "title": SESSIONS[session_id].get("title", "新对话"),
            "response": full_response,
            "is_truncated": is_truncated  # 如果截断，前端会继续请求
        }
        
        print(f"[返回数据] ✅ 数据准备完成，即将返回")
        print(f"{'#'*70}\n")
        
        return JSONResponse(content=return_data)

    except HTTPException as http_exc:
        # HTTP异常直接抛出
        print(f"\n{'!'*70}")
        print(f"!!! HTTPException 发生")
        print(f"!!! status_code: {http_exc.status_code}")
        print(f"!!! detail: {http_exc.detail}")
        print(f"{'!'*70}\n")
        raise
        
    except Exception as e:
        print(f"\n{'!'*70}")
        print(f"!!! /chat 接口发生未预期的错误")
        print(f"!!! 错误类型: {type(e).__name__}")
        print(f"!!! 错误信息: {str(e)}")
        print(f"!!! session_id: {session_id if 'session_id' in locals() else 'N/A'}")
        print(f"!!! is_new_session: {is_new_session if 'is_new_session' in locals() else 'N/A'}")
        
        # 如果出错，移除最后一条不成功的用户消息
        try:
            if not is_new_session and session_id in SESSIONS:
                history = SESSIONS[session_id]["history"]
                if len(history) > 0 and history[-1]['role'] == 'user':
                    SESSIONS[session_id]["history"].pop()
                    print(f"!!! 已回滚最后一条用户消息")
        except Exception as rollback_error:
            print(f"!!! 回滚失败: {rollback_error}")
        
        print(f"{'!'*70}\n")
        
        import traceback
        print(f"完整堆栈跟踪：")
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 确保临时文件总能被删除
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

