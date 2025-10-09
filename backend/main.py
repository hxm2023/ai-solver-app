# ==============================================================================
# 完整 main.py - 【V22.0 追问图片记忆修复版 - 混合输入 + 前端续答】
# 核心特性：
# 1. OCR增强（Pix2Text）+ 原图视觉（通义千问）= 混合输入架构
# 2. 删除后端自动续答 - 由前端循环处理续答逻辑
# 3. 追问图片记忆修复 - 每次追问都重新发送图片，避免AI遗忘或幻觉
# 4. 完整对话历史 - 追问时重建包含图片的完整消息历史
# 5. 优化提示词 - 避免暴露技术细节，全中文回答
# ==============================================================================

import os
import io
import re
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import dashscope
from typing import Optional, List
from pydantic import BaseModel
import base64
from fastapi.responses import JSONResponse
from PIL import Image
import tempfile
import json
import asyncio

from dashscope import MultiModalConversation
from pix2text import Pix2Text


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

@app.get("/")
def read_root():
    return {"message": "AI解题后端服务正在运行 (V22.0 追问图片记忆修复版)"}
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
    """
    if p2t is None:
        return "[OCR引擎未初始化]"
    
    try:
        # 预处理图片
        processed_img = image_preprocess_v2(image)
        
        # 使用Pix2Text识别
        result = p2t.recognize(processed_img)
        
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
        
        print(f"[OCR识别成功] 提取了 {len(ocr_text)} 个字符")
        return ocr_text
    
    except Exception as e:
        print(f"!!! OCR识别失败: {e}")
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

# --- 流式调用通义千问 (生成器函数) ---
def call_qwen_vl_max_stream(messages: list, model: str = 'qwen-vl-max', max_tokens: int = 8192):
    """
    流式调用通义千问模型，逐块返回内容
    """
    print(f"\n--- 正在流式调用通义千问 '{model}' API，历史记录有 {len(messages)} 条... ---")
    
    try:
        responses = dashscope.MultiModalConversation.call(
            model=model,
            messages=messages,
            max_output_tokens=max_tokens,
            stream=True,
            incremental_output=True  # 增量输出模式
        )
        
        print(f"[API] 流式响应对象已创建，开始接收数据...")
        
        full_content = ""
        chunk_count = 0
        
        for response in responses:
            chunk_count += 1
            print(f"[API] 收到第 {chunk_count} 个数据块")
            print(f"[API] status_code: {response.status_code}")
            
            if response.status_code == 200:
                choice = response.output.choices[0]
                content_data = choice.message.content
                finish_reason = choice.finish_reason if hasattr(choice, 'finish_reason') else None
                
                print(f"[API] finish_reason: {finish_reason}")
                
                # 提取文本内容
                text_chunk = ""
                if isinstance(content_data, list):
                    for part in content_data:
                        if part.get("text"):
                            text_chunk = part["text"]
                            break
                elif isinstance(content_data, str):
                    text_chunk = content_data
                
                if text_chunk:
                    full_content += text_chunk
                    print(f"[API] 本次收到 {len(text_chunk)} 字符，累计 {len(full_content)} 字符")
                    yield {
                        "chunk": text_chunk,
                        "full_content": full_content,
                        "finish_reason": finish_reason,
                        "done": finish_reason is not None
                    }
                
                # 如果完成了，退出
                if finish_reason:
                    print(f"--- 流式API调用完成, finish_reason: {finish_reason}, 总长度: {len(full_content)} ---")
                    break
            else:
                error_msg = f"通义千问API调用失败: status_code={response.status_code}, message={response.message}"
                print(f"!!! {error_msg}")
                if hasattr(response, 'code'):
                    print(f"!!! error code: {response.code}")
                if hasattr(response, 'request_id'):
                    print(f"!!! request_id: {response.request_id}")
                yield {"error": error_msg, "done": True}
                break
                
    except Exception as e:
        error_msg = f"流式API调用异常: {type(e).__name__}: {str(e)}"
        print(f"!!! {error_msg}")
        import traceback
        traceback.print_exc()
        yield {"error": error_msg, "done": True}

# --- Pydantic模型，用于校验前端发来的JSON数据 ---
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    prompt: str
    image_base_64: Optional[str] = None # 注意：我们用 base_64 替代了文件上传

class RestoreSessionRequest(BaseModel):
    session_id: str
    image_base_64: str
    history: List[dict]  # 消息历史

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
                # 【修复】如果前端发送了session_id但后端不存在（服务重启），返回特殊错误
                if request.session_id:
                    print(f"[错误] 会话已失效（可能是服务重启），session_id: {session_id}")
                    raise HTTPException(status_code=404, detail="会话已失效，请重新开始对话")
                else:
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
            
        # --- 【核心创新 + 优化】: 混合输入架构 + 滑动窗口机制 ---
        messages_to_send = []
        if is_new_session:
            # A路: 使用Pix2Text进行OCR识别
            print("[混合输入架构] 步骤1: 使用Pix2Text进行OCR识别...")
            image_bytes = base64.b64decode(request.image_base_64)
            image = Image.open(io.BytesIO(image_bytes))
            ocr_text = extract_text_with_pix2text(image)
            
            # B路: 保留原始图片
            print("[混合输入架构] 步骤2: 构建混合输入消息...")
            
            # 构建增强Prompt - 将OCR文本嵌入到用户提示中
            enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{request.prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身

【LaTeX 书写规范】
- 化学方程式：使用 \\ce{{}} 命令，如 \\ce{{H2O}}、\\ce{{A + B -> C}}
- **禁止使用** \\chemfig 命令（不被支持），如需表示化学结构，直接用文字或 \\ce{{}} 描述
- 数学公式：使用标准 LaTeX，支持 \\frac、\\sqrt、\\int、\\sum 等常用命令
- 行内公式用 $...$ 包裹，独立公式用 $$...$$ 包裹
"""
            
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
            # 【优化】追问模式 + 滑动窗口机制
            print(f"\n[追问模式] 开始构建对话历史（滑动窗口优化）...")
            
            # 获取原始图片
            original_image_base64 = SESSIONS[session_id].get("image_base_64")
            
            if not original_image_base64:
                print(f"[错误] 会话中没有找到原始图片！")
                raise HTTPException(status_code=500, detail="会话图片丢失，请重新开始对话")
            
            print(f"[追问模式] ✓ 找到原始图片，大小: {len(original_image_base64)} 字符")
            
            # 检查历史记录
            history = SESSIONS[session_id]["history"]
            if len(history) == 0:
                print(f"[错误] 会话历史为空！")
                raise HTTPException(status_code=500, detail="会话历史为空，请重新开始对话")
            
            print(f"[追问模式] 📊 完整历史记录数: {len(history)}")
            
            # 【滑动窗口优化】只保留最近的对话
            WINDOW_SIZE = 6  # 保留最近3轮对话（6条消息：3个问答对）
            
            # 第一条消息：用户的首次提问 + 图片（永远保留）
            first_user_message = history[0]
            messages_to_send = [{
                "role": "user",
                "content": [
                    {'text': first_user_message["content"]},
                    {'image': f"data:image/png;base64,{original_image_base64}"}
                ]
            }]
            print(f"[追问模式] ✓ 第1条消息（首次提问+图片）已添加")
            
            # 计算窗口：从历史记录中取最近的N条
            if len(history) > 1:
                # 跳过第一条（已添加），取最后WINDOW_SIZE条
                recent_history = history[1:]  # 去掉第一条
                if len(recent_history) > WINDOW_SIZE:
                    recent_history = recent_history[-WINDOW_SIZE:]  # 只取最后N条
                    print(f"[追问模式] ⚡ 使用滑动窗口：保留最近 {len(recent_history)} 条消息")
                else:
                    print(f"[追问模式] 📝 历史较短：保留全部 {len(recent_history)} 条消息")
                
                # 添加窗口内的历史消息
                for i, msg in enumerate(recent_history, start=2):
                    messages_to_send.append(msg)
            
            # 添加当前的追问
            messages_to_send.append({"role": "user", "content": request.prompt})
            
            print(f"[追问模式] ✅ 对话历史构建完成！")
            print(f"[追问模式] 📊 发送消息数: {len(messages_to_send)} 条（含首条+窗口+新问题）")
            print(f"[追问模式] 💾 完整历史: {len(history)} 条 → 🚀 实际发送: {len(messages_to_send)} 条")
            print(f"[追问模式] 📷 图片位置: 第1条消息中（始终保留）")

        
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

# --- 【新增】会话恢复接口 ---
@app.post("/restore_session")
async def restore_session(request: RestoreSessionRequest):
    """
    恢复会话状态，用于从localStorage加载历史对话
    """
    print(f"\n{'='*70}")
    print(f"[会话恢复] 开始恢复会话")
    print(f"[会话恢复] session_id: {request.session_id}")
    print(f"[会话恢复] 历史消息数: {len(request.history)}")
    print(f"{'='*70}")
    
    try:
        # 重建会话状态
        SESSIONS[request.session_id] = {
            "history": request.history,
            "title": "恢复的对话",
            "image_base_64": request.image_base_64
        }
        
        print(f"[会话恢复] ✅ 会话恢复成功")
        print(f"[会话恢复] 保存的历史记录数: {len(request.history)}")
        
        return JSONResponse(content={
            "success": True,
            "message": "会话恢复成功",
            "history_count": len(request.history)
        })
        
    except Exception as e:
        print(f"[会话恢复] ❌ 恢复失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"会话恢复失败: {str(e)}")

# --- 【新增】流式聊天接口 ---
@app.post("/chat_stream")
async def chat_with_ai_stream(request: ChatRequest):
    """
    流式聊天接口，使用Server-Sent Events (SSE)实时返回内容
    """
    print(f"\n{'#'*70}")
    print(f"# /chat_stream 接口被调用")
    print(f"# session_id: {request.session_id}")
    print(f"# prompt: {request.prompt[:80]}...")
    print(f"# has_image: {bool(request.image_base_64)}")
    print(f"{'#'*70}")
    
    session_id = request.session_id or str(uuid.uuid4())
    is_new_session = session_id not in SESSIONS
    
    async def event_generator():
        try:
            print(f"[流式] event_generator 开始执行")
            print(f"[流式] is_new_session: {is_new_session}")
            print(f"[流式] has_image: {bool(request.image_base_64)}")
            if request.image_base_64:
                print(f"[流式] image_base_64 长度: {len(request.image_base_64)}")
            
            # --- 1. 初始化或加载会话 ---
            if is_new_session:
                if not request.image_base_64:
                    print("[流式错误] 新会话缺少图片！")
                    yield f"data: {json.dumps({'error': '新会话必须包含图片'})}\n\n"
                    return
                
                print(f"[流式] 创建新会话，图片大小: {len(request.image_base_64)} 字符")
                SESSIONS[session_id] = {
                    "history": [],
                    "title": "新对话",
                    "image_base_64": request.image_base_64
                }
                # 发送session_id给前端
                yield f"data: {json.dumps({'session_id': session_id, 'title': '新对话'})}\n\n"
                print(f"[流式] 会话创建完成: {session_id}")
            else:
                if session_id not in SESSIONS:
                    yield f"data: {json.dumps({'error': f'会话 {session_id} 不存在'})}\n\n"
                    return
            
            # --- 2. 构建消息（与原逻辑相同）---
            messages_to_send = []
            if is_new_session:
                # OCR识别
                print("[流式] 开始进行OCR识别...")
                image_bytes = base64.b64decode(request.image_base_64)
                print(f"[流式] 图片解码完成，字节数: {len(image_bytes)}")
                image = Image.open(io.BytesIO(image_bytes))
                print(f"[流式] 图片打开完成，尺寸: {image.size}")
                ocr_text = extract_text_with_pix2text(image)
                print(f"[流式] OCR识别完成！提取了 {len(ocr_text)} 个字符")
                print(f"[流式] OCR文本预览: {ocr_text[:200]}...")
                
                # 构建混合输入消息
                enhanced_prompt = f"""题目内容如下：

{ocr_text}

【任务要求】
{request.prompt}

【重要说明】
你是一个专业的学科辅导AI助手，请认真分析题目，回答要像一位老师在面对面讲解，自然流畅，专注于教学内容本身

【LaTeX 书写规范】
- 化学方程式：使用 \\ce{{}} 命令，如 \\ce{{H2O}}、\\ce{{A + B -> C}}
- **禁止使用** \\chemfig 命令（不被支持），如需表示化学结构，直接用文字或 \\ce{{}} 描述
- 数学公式：使用标准 LaTeX，支持 \\frac、\\sqrt、\\int、\\sum 等常用命令
- 行内公式用 $...$ 包裹，独立公式用 $$...$$ 包裹
"""
                print(f"[流式] 增强Prompt已构建，总长度: {len(enhanced_prompt)}")
                messages_to_send.append({
                    "role": "user",
                    "content": [
                        {'text': enhanced_prompt},
                        {'image': f"data:image/png;base64,{request.image_base_64}"}
                    ]
                })
                print(f"[流式] 消息已添加，包含OCR文本和原始图片")
            else:
                # 追问模式：重建对话历史
                original_image_base64 = SESSIONS[session_id].get("image_base_64")
                if not original_image_base64:
                    yield f"data: {json.dumps({'error': '会话图片丢失'})}\n\n"
                    return
                
                history = SESSIONS[session_id]["history"]
                first_user_message = history[0]
                
                messages_to_send = [{
                    "role": "user",
                    "content": [
                        {'text': first_user_message["content"]},
                        {'image': f"data:image/png;base64,{original_image_base64}"}
                    ]
                }]
                
                for msg in history[1:]:
                    messages_to_send.append(msg)
                
                messages_to_send.append({"role": "user", "content": request.prompt})
            
            # --- 3. 流式调用AI ---
            print(f"\n[流式] 准备调用通义千问API")
            print(f"[流式] messages_to_send 数量: {len(messages_to_send)}")
            for i, msg in enumerate(messages_to_send):
                print(f"[流式] Message {i}: role={msg.get('role')}")
                content = msg.get('content')
                if isinstance(content, list):
                    print(f"[流式]   content是列表，包含 {len(content)} 个元素")
                    for j, item in enumerate(content):
                        if 'text' in item:
                            text_preview = item['text'][:100] if len(item['text']) > 100 else item['text']
                            print(f"[流式]     [{j}] text: {text_preview}...")
                        if 'image' in item:
                            image_data = item['image']
                            if image_data.startswith('data:image'):
                                print(f"[流式]     [{j}] image: data:image/png;base64,... (长度: {len(image_data)})")
                            else:
                                print(f"[流式]     [{j}] image: {image_data[:50]}...")
                elif isinstance(content, str):
                    preview = content[:100] if len(content) > 100 else content
                    print(f"[流式]   content是字符串: {preview}...")
            
            full_response = ""
            for chunk_data in call_qwen_vl_max_stream(messages_to_send):
                if "error" in chunk_data:
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    break
                
                full_response = chunk_data["full_content"]
                # 发送增量数据给前端
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                if chunk_data.get("done"):
                    break
            
            # --- 4. 更新会话历史 ---
            SESSIONS[session_id]["history"].append({"role": "user", "content": request.prompt})
            SESSIONS[session_id]["history"].append({"role": "assistant", "content": full_response})
            
            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
            
        except Exception as e:
            print(f"!!! /chat_stream 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )

