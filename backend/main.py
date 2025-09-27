# ==============================================================================
# 完整 main.py - 【V18.0 终极单图统一版】
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

from dashscope import MultiModalConversation


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
    return {"message": "AI解题后端服务正在运行 (V18.0 终极单图统一版)"}
# ==============================================================================
# 完整 main.py - 第二部分: 核心API接口
# ==============================================================================

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
    finish_reason = choice.finish_reason

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

    print(f"--- API调用成功, finish_reason: {finish_reason} ---")
    return {"content": text_content, "finish_reason": finish_reason}

# --- Pydantic模型，用于校验前端发来的JSON数据 ---
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    prompt: str
    image_base_64: Optional[str] = None # 注意：我们用 base_64 替代了文件上传

# --- 【全新】的统一聊天接口 ---
@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    is_new_session = session_id not in SESSIONS
    
    temp_image_path = None # 初始化临时文件路径变量
    try:
        # --- 1. 初始化或加载会话历史 ---
        if is_new_session:
            if not request.image_base_64:
                raise HTTPException(status_code=400, detail="新会话必须包含图片")
            
            print(f"--- 创建新会话: {session_id} ---")
            SESSIONS[session_id] = {
                "history": [], 
                "title": "新对话",
                "image_base_64": request.image_base_64 
            }
            
            
        # --- 【核心修复】: 重构消息构建逻辑 ---
        messages_to_send = []
        if is_new_session:
            messages_to_send.append({
                "role": "user",
                "content": [
                    {'text': request.prompt},
                    {'image': f"data:image/png;base64,{request.image_base_64}"}
                ]
            })
        else:
            # 对于追问，使用已有的文本历史记录，并追加新问题
            # 【重要】: 不再发送旧的图片信息，因为AI已经记住了
            messages_to_send = SESSIONS[session_id]["history"]
            messages_to_send.append({"role": "user", "content": request.prompt})

        
        # --- 3. 调用大模型 ---
        ai_response = call_qwen_vl_max(messages_to_send)
        
        # --- 4. 更新会话历史 (只存文本) ---
        if is_new_session:
            # 新会话的历史，是刚才发送的user消息的【文本部分】 + AI的回答
            SESSIONS[session_id]["history"].append({"role": "user", "content": request.prompt})
        else:
            # 追问时，也只追加纯文本的用户消息
            SESSIONS[session_id]["history"].append({"role": "user", "content": request.prompt})
        
        # 统一追加AI的回答
        SESSIONS[session_id]["history"].append({"role": "assistant", "content": ai_response['content']})

        # --- 4. 准备返回给前端的数据 ---
        is_truncated = ai_response['finish_reason'] == 'length'
        
        return JSONResponse(content={
            "session_id": session_id,
            "title": SESSIONS[session_id].get("title", "新对话"),
            "response": ai_response['content'],
            "is_truncated": is_truncated
        })

    except Exception as e:
        print(f"!!! /chat 接口发生错误: {e}")
        # 如果出错，移除最后一条不成功的用户消息
        if not is_new_session and session_id in SESSIONS and SESSIONS[session_id]["history"][-1]['role'] == 'user':
            SESSIONS[session_id]["history"].pop()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 确保临时文件总能被删除
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

