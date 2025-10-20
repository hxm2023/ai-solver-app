# ==============================================================================
# 微信小程序API接口 - 新增代码片段
# 添加到 backend/main_simple.py 中
# ==============================================================================

# ---- 在文件开头的导入部分添加 ----
from typing import Literal
from pydantic import BaseModel, Field

# ---- 在 ChatRequest 模型后添加新的请求模型 ----
class MiniAppRequest(BaseModel):
    """微信小程序专用请求模型"""
    image_base_64: str = Field(..., description="用户上传的完整图片，经过Base64编码")
    mode: Literal['solve', 'review'] = Field(..., description="操作模式：'solve'为解题，'review'为批改")


# ---- 在所有现有API端点之后添加新的端点 ----
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
# 使用说明：
# 1. 将上述代码添加到 backend/main_simple.py 的相应位置
# 2. MiniAppRequest 模型添加在 ChatRequest 模型之后
# 3. API端点函数添加在所有现有端点之后
# 4. 确保已导入所需的模块（Literal, Field等）
# ==============================================================================

