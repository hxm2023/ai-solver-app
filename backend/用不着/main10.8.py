# ==============================================================================
# 完整 main.py - 【V23.0 单题识别精度增强版】
# 核心特性：
# 1. OCR增强（Pix2Text + OpenCV高级图像处理）+ 原图视觉（通义千问）= 混合输入架构
# 2. 删除后端自动续答 - 由前端循环处理续答逻辑
# 3. 追问图片记忆修复 - 每次追问都重新发送图片，避免AI遗忘或幻觉
# 4. 完整对话历史 - 追问时重建包含图片的完整消息历史
# 5. 优化提示词 - 避免暴露技术细节，全中文回答
# 6. 【V23.0新增】高级图像增强流水线 - 对抗模糊、光照不均、污渍
# 7. 【V23.0新增】AI智能校正 - 引导模型比对图片修正OCR错误
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
import numpy as np
import cv2

from dashscope import MultiModalConversation
from pix2text import Pix2Text
from image_enhancer import advanced_image_processing_pipeline
# V24.0 新增: 导入题目分割器模块
from question_splitter import find_question_boxes


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
    return {"message": "AI解题后端服务正在运行 (V24.0 整页多题并行处理版)"}

# --- Pydantic模型定义（需要在使用前定义） ---
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    prompt: str
    image_base_64: Optional[str] = None

class SheetProcessRequest(BaseModel):
    prompt: str
    image_base_64: str

# ==============================================================================
# V24.0 新增端点: 整页题目分割处理
# ==============================================================================

@app.post("/process_sheet")
async def process_sheet(request: SheetProcessRequest):
    """
    V24.0 新增: 处理完整题目页的端点。
    
    工作流程：
    1. 接收一张完整的页面图片
    2. 使用题目分割器找到独立的题目区域
    3. 将每个题目裁剪成独立的图片
    4. 将裁剪后的题目单元列表（ID和图片数据）返回给前端
    
    返回格式：
    {
        "job_id": "job_xxx",
        "questions": [
            {"id": "q_xxx", "image_base_64": "...", "index": 0},
            {"id": "q_yyy", "image_base_64": "...", "index": 1},
            ...
        ]
    }
    """
    print(f"\n{'#'*80}")
    print(f"# /process_sheet 端点被调用 - V24.0 整页分割处理")
    print(f"# prompt: {request.prompt[:50]}...")
    print(f"{'#'*80}")
    
    try:
        # 1. 解码完整图片
        print("[/process_sheet] 步骤1/4: 解码图片...")
        image_bytes = base64.b64decode(request.image_base_64)
        full_image = Image.open(io.BytesIO(image_bytes))
        print(f"[/process_sheet] ✓ 图片解码成功，尺寸: {full_image.width}x{full_image.height}")
        
        # 2. 使用题目分割器寻找所有题目的边界框
        print("[/process_sheet] 步骤2/4: 智能检测题目区域...")
        question_boxes = find_question_boxes(full_image)
        
        # 【可选】生成调试可视化图片
        # 取消注释以启用调试
        # from question_splitter import visualize_detected_boxes
        # visualize_detected_boxes(full_image, question_boxes, "debug/detected_boxes.png")
        
        # 如果未找到任何框，则将整张图片视为一个题目
        if not question_boxes or len(question_boxes) == 0:
            print("[/process_sheet] ⚠️ 未找到独立的题目框，将整张图视为单个题目。")
            question_boxes = [(0, 0, full_image.width, full_image.height)]
        
        # 3. 裁剪每个题目并准备响应数据
        print(f"[/process_sheet] 步骤3/4: 裁剪 {len(question_boxes)} 个题目区域...")
        question_units = []
        
        for i, (x, y, w, h) in enumerate(question_boxes):
            # 【V24.1优化】增加边距padding，避免切到文字
            # 从10px增加到20px，确保不遗漏边缘文字
            padding = 20
            crop_box = (
                max(0, x - padding), 
                max(0, y - padding), 
                min(full_image.width, x + w + padding), 
                min(full_image.height, y + h + padding)
            )
            
            # 使用 Pillow 裁剪图片
            question_image = full_image.crop(crop_box)
            
            # 将裁剪后的图片重新编码为 Base64 字符串
            buffered = io.BytesIO()
            question_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            question_units.append({
                "id": f"q_{uuid.uuid4()}",  # 为每个题目单元生成唯一ID
                "image_base_64": img_str,
                "index": i  # 题目序号（从0开始）
            })
            
            print(f"[/process_sheet]   ✓ 题目 {i+1}/{len(question_boxes)} 裁剪完成")
        
        # 4. 准备返回数据
        job_id = f"job_{uuid.uuid4()}"
        print(f"\n[/process_sheet] 步骤4/4: 准备返回数据...")
        print(f"[/process_sheet] ✅ 成功将图片分割为 {len(question_units)} 个独立题目单元")
        print(f"[/process_sheet] 📦 Job ID: {job_id}")
        print(f"{'#'*80}\n")
        
        return JSONResponse(content={
            "job_id": job_id,
            "questions": question_units,
            "total_count": len(question_units)
        })
        
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"!!! 在 /process_sheet 中发生错误")
        print(f"!!! 错误类型: {type(e).__name__}")
        print(f"!!! 错误信息: {str(e)}")
        print(f"{'!'*80}\n")
        
        import traceback
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=f"题目分割处理失败: {str(e)}")
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

# --- OCR识别函数 (使用Pix2Text) - V23.0升级版 ---
def extract_text_with_pix2text(image: Image.Image, enhancement_mode: str = 'light') -> str:
    """
    使用Pix2Text识别图片中的文字和公式，返回清洁的LaTeX文本。
    
    【V24.1 优化】: 默认改为轻量增强，避免过度处理丢失信息
    
    参数:
        image: PIL格式的输入图像
        enhancement_mode: 增强模式
            - 'none': 无处理（推荐清晰图片）
            - 'light': 轻量增强（新默认，推荐）
            - 'standard': 标准增强
            - 'aggressive': 激进增强（适合严重模糊/污损）
            - 'binary': 二值化（适合极端光照）
    """
    if p2t is None:
        return "[OCR引擎未初始化]"
    
    try:
        print(f"\n[OCR流程] 开始识别... (增强模式: {enhancement_mode})")
        
        # 步骤1: 基础标准化 (尺寸调整等)
        print("[OCR流程] 步骤1/3: 基础标准化...")
        base_processed_img = image_preprocess_v2(image)
        
        # 步骤2: 调用高级图像增强流水线
        print("[OCR流程] 步骤2/3: 高级图像增强...")
        enhanced_img = advanced_image_processing_pipeline(base_processed_img, mode=enhancement_mode)
        
        # 步骤3: 使用增强后的图片进行Pix2Text识别
        print("[OCR流程] 步骤3/3: Pix2Text识别...")
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
        
        print(f"\n{'='*60}")
        print(f"[OCR识别成功] ✅ 提取了 {len(ocr_text)} 个字符")
        print(f"{'='*60}\n")
        
        return ocr_text
    
    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"!!! OCR识别失败: {e}")
        print(f"{'!'*60}\n")
        
        # 降级策略：如果增强后识别失败，尝试用原图再识别一次
        if enhancement_mode != 'none':
            print("[OCR流程] 尝试降级策略：使用原图重新识别...")
            try:
                result = p2t.recognize(image)
                if isinstance(result, dict) and 'text' in result:
                    ocr_text = result['text']
                elif isinstance(result, str):
                    ocr_text = result
                else:
                    ocr_text = str(result)
                
                ocr_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ocr_text)
                ocr_text = ocr_text.strip()
                print(f"[OCR降级策略] ✓ 识别成功，提取了 {len(ocr_text)} 个字符")
                return ocr_text
            except Exception as fallback_error:
                print(f"[OCR降级策略] ✗ 降级识别也失败: {fallback_error}")
                return "[OCR识别失败]"
        
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
            
            # 【V23.0 升级】构建带有容错和校正指令的增强Prompt
            enhanced_prompt = f"""【任务背景】
用户上传了一张题目图片。由于拍摄或试卷本身的原因，图片可能存在模糊、光照不均、少量污渍或手写笔记。
我已经使用OCR工具对图片进行了初步识别，结果如下。

【OCR初步识别结果】

{ocr_text}

【你的核心任务】
请你扮演一位严谨且经验丰富的学科辅导老师。你的首要任务是**将OCR结果与原始图片进行智能比对和校正**。

1. **核对与修正**：仔细查看原始图片，如果发现OCR结果与图片内容有出入（例如，数字`1`被识别为`l`，`+`号模糊不清，某个文字因污渍无法识别），请**以原始图片为准，在你的分析中默默修正这些错误**。
2. **专注解答**：基于你修正后的、最准确的题目内容，为用户提供清晰、详尽的解答或批改。
3. **专业呈现**：在回答中，请直接使用你校正后的正确题目进行讲解。**不要向用户提及"OCR识别错误"、"图片模糊"等技术细节或问题诊断过程**，给用户一个无缝、专业的辅导体验。

【用户的具体要求】
{request.prompt}
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

