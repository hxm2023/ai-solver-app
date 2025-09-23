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

from dashscope import MultiModalConversation

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
def call_qwen_vl_max(messages: list) -> str:
    """
    调用通义千问VL-Max模型并返回文本结果。
    """
    print("\n--- 正在调用通义千问VL-Max API... ---")
    
    response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=messages)
    # respon = MultiModalConversation.call(
    #     model='qwen-vl-max',
    #     messages=messages,
    #     stream=True
    # )

    # # 拼接所有流式返回的内容
    # full_content = ""
    # for chunk in respon:
    #     if chunk.output and chunk.output.choices:
    #         content = chunk.output.choices[0].message.content
    #         full_content += content
    #     else:
    #         continue  # 忽略无内容的 chunk

    # # 构造一个与原 response 结构一致的 Response 对象
    # # 注意：这里我们手动构建一个等价的 Response 对象
    # # 实际上你可以选择直接返回 full_content，但你想保持类型一致

    # # 创建一个“合成”的 Response 对象
    # response = MultiModalConversation.call(
    #     request_id=respon.request_id,
    #     output={
    #         "choices": [
    #             {
    #                 "finish_reason": "stop",  # 假设结束原因
    #                 "index": 0,
    #                 "message": {
    #                     "content": full_content,
    #                     "role": "assistant"
    #                 }
    #             }
    #         ],
    #         "usage": None  # 可选：可从流中提取 usage 数据，但通常不完整
    #     },
    #     code=200,
    #     message="OK",
    #     headers=respon.headers,
    #     raw=respon.raw
    # )

    
    content = response.output.choices[0].message.content
    
    # 从返回的列表中提取文本
    if isinstance(content, list):
        for part in content:
            if part.get("text"):
                print("--- 通义千问API调用成功，已提取文本。 ---")
                return part["text"]
    elif isinstance(content, str):
        print("--- 通义千问API调用成功，已提取文本。 ---")
        return content
        
    raise ValueError("通义千问未返回有效的文本内容。")

# --- 【核心】: 创建一个统一的、处理单图请求的函数 ---
async def process_single_image_request(prompt_text: str, image: UploadFile):
    """
    这是一个可复用的函数，负责处理所有接收单张图片的请求。
    """
    print(f"\n收到请求, prompt: '{prompt_text[:80]}...'")
    
    # 使用 /tmp 目录在Linux/macOS和Windows的WSL环境中更通用
    temp_dir = "/tmp" if os.path.exists("/tmp") else "."
    temp_image_path = os.path.join(temp_dir, f"temp_image_{uuid.uuid4()}.png")

    try:
        image_bytes = await image.read()
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)
        
        # 构建发送给模型的消息
        messages = [{
            'role': 'user',
            'content': [
                {'text': prompt_text},
                {'image': f'file://{os.path.abspath(temp_image_path)}'}
            ]
        }]
        
        result = call_qwen_vl_max(messages)
        return PlainTextResponse(content=result, media_type="text/markdown; charset=utf-8")
        
    except Exception as e:
        print(f"!!! 接口发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)


# --- API 接口 ---

@app.post("/solve")
async def solve_from_image(
    prompt_text: str = Form(...),
    file: UploadFile = File(...) # 注意: key是 'file'
):
    """解题接口：调用统一的处理函数"""
    return await process_single_image_request(prompt_text, file)


@app.post("/review")
async def review_from_image(
    prompt_text: str = Form(...),
    file: UploadFile = File(...) # 注意: key也是 'file'
):
    """改题接口：也调用统一的处理函数"""
    return await process_single_image_request(prompt_text, file)




































# # ==============================================================================
# # 完整 main.py - 【V12.0 终极教师版】
# # ==============================================================================

# # --- 【核心】: 在所有import之前，设置环境变量禁用多进程 ---
# import os
# # os.environ["TOKENIZERS_PARALLELISM"] = "false"
# # os.environ["OMP_NUM_THREADS"] = "1"
# # os.environ["MKL_NUM_THREADS"] = "1"

# # --- Python标准库 ---
# import io
# import base64
# import cv2
# import re
# import uuid
# import numpy as np



# # --- 第三方库 ---
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import PlainTextResponse
# from PIL import Image, ImageOps
# from pix2text import Pix2Text
# from dotenv import load_dotenv

# # --- AI库 ---
# from openai import OpenAI
# import dashscope

# # --- 1. 初始化 ---
# load_dotenv()
# app = FastAPI()

# # 懒加载 Pix2Text
# p2t = None
# def initialize_pix2text():
#     global p2t
#     if p2t is None:
#         print("首次请求：正在以安全模式初始化 Pix2Text...")
#         # 在云环境中，/tmp是保证可写的临时目录
#         cache_dir = "/tmp/pix2text_cache"
#         os.makedirs(cache_dir, exist_ok=True)
#         p2t = Pix2Text(device='cpu', root=cache_dir)
#         print("Pix2Text 初始化完成。")

# print("正在初始化Kimi客户端 (OpenAI兼容模式)...")
# try:
#     kimi_client = OpenAI(
#         api_key=os.getenv("MOONSHOT_API_KEY"),
#         base_url="https://api.moonshot.cn/v1",
#     )
#     if not os.getenv("MOONSHOT_API_KEY"): raise ValueError("API Key not found in .env")
#     print("Kimi客户端初始化成功。")
# except Exception as e:
#     print(f"!!! 初始化Kimi客户端失败: {e}")
#     kimi_client = None

# print("正在配置通义千问API Key...")
# try:
#     dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
#     if not dashscope.api_key: raise ValueError("API Key not found in .env")
#     print("通义千问API Key配置成功。")
# except Exception as e:
#     print(f"!!! 配置通义千问API Key失败: {e}")
    
    
# # --- 2. 核心辅助函数 (来自Kimi的建议) ---

# def image_preprocess_v2(image_bytes: bytes, max_size: int = 2048) -> Image.Image:
#     """
#     一个工程级的图片预处理流水线。
#     :param image_bytes: 原始图片字节流
#     :param max_size: 图片长边的最大尺寸
#     :return: 经过优化处理的PIL Image对象 (灰度图)
#     """
#     try:
#         # 1. 从字节流加载图片 (使用OpenCV)
#         nparr = np.frombuffer(image_bytes, np.uint8)
#         img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#         # 2. 尺寸归一化
#         h, w = img_cv.shape[:2]
#         if max(h, w) > max_size:
#             scale = max_size / max(h, w)
#             img_cv = cv2.resize(img_cv, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

#         # 3. 转换为灰度图
#         gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

#         # 4. 角度校正 (Deskew)
#         # 这是一个简化的实现，基于寻找最小面积的包围矩形
#         coords = np.column_stack(np.where(gray < 128))
#         angle = cv2.minAreaRect(coords)[-1]
#         if angle < -45:
#             angle = -(90 + angle)
#         else:
#             angle = -angle
        
#         if abs(angle) > 1: # 只对倾斜超过1度的图片进行校正
#             (h, w) = gray.shape[:2]
#             center = (w // 2, h // 2)
#             M = cv2.getRotationMatrix2D(center, angle, 1.0)
#             gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
#             print(f"--- 图片已自动校正角度: {angle:.2f} 度 ---")

#         # 5. 降噪 (使用高斯模糊)
#         blurred = cv2.GaussianBlur(gray, (5, 5), 0)

#         # 6. 智能自适应二值化 (处理光照不均)
#         # ADAPTIVE_THRESH_GAUSSIAN_C 效果通常比 MEAN_C 更好
#         binary = cv2.adaptiveThreshold(
#             blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#             cv2.THRESH_BINARY, 11, 2
#         )

#         # 7. (可选) 锐化 - 拉普拉斯算子
#         sharpened = cv2.Laplacian(binary, cv2.CV_64F)
#         sharpened = np.uint8(np.clip(binary - 0.5 * sharpened, 0, 255))

#         # 8. 将处理后的OpenCV图像转回PIL Image对象
#         img_pil = Image.fromarray(binary)
        
#         return img_pil

#     except Exception as e:
#         print(f"!!! 图片预处理失败: {e}. 将使用原始图片进行识别。")
#         # 如果预处理失败，优雅降级，返回原始的灰度图
#         return Image.open(io.BytesIO(image_bytes)).convert('L')

# def ocr_text_clean_v2(raw_text: str) -> str:
#     """
#     一个工程级的、多阶段的OCR文本清洗函数。
#     """
#     # 检查输入是否为字符串
#     if not isinstance(raw_text, str):
#         print(f"!!! 文本清洗函数收到非字符串类型: {type(raw_text)}，将返回空字符串。")
#         return ""
    
#     # --- 阶段1: 基础字符归一化 ---
#     # 替换所有中文标点和常见错认字符
#     replacements_char = {
#         '（': '(', '）': ')', '【': '[', '】': ']', '，': ',', '。': '.',
#         '＋': '+', '－': '-', '×': '*', '÷': '/', '＝': '=',
#         'α': '\\alpha', 'β': '\\beta', 'γ': '\\gamma', 'θ': '\\theta', 'π': '\\pi',
#         'Δ': '\\Delta', 'Ω': '\\Omega',
#         '≤': '\\leq', '≥': '\\geq', '≠': '\\neq',
#         '∈': '\\in', '∀': '\\forall', '∃': '\\exists',
#         '→': '\\rightarrow',
#         '⊥': '\\perp',
#     }
#     for old, new in replacements_char.items():
#         raw_text = raw_text.replace(old, new)
        
#     cleaned_text = raw_text
    
#     # --- 阶段2: 基于模式的通用修复 (高频错误) ---
#     # 使用正则表达式，按优先级顺序执行
#     # (key是正则表达式, value是替换格式)
#     replacements_pattern = {
#         # 修复 sqrt, e.g., "sqrt3" -> "\sqrt{3}"
#         r'sqrt\s*(\d+|[a-zA-Z])': r'\\sqrt{\1}',
#         # 修复 frac, e.g., "frac12" -> "\frac{1}{2}", "fracab" -> "\frac{a}{b}"
#         r'frac\s*(\d+|[a-zA-Z])\s*(\d+|[a-zA-Z])': r'\\frac{\1}{\2}',
#         # 修复上下标, e.g., "x^2", "x_1" -> "$x^2$", "$x_1$" (先不加$, 后续处理)
#         # 这里只做规范化
#         r'([a-zA-Z\)])\s*\^\s*(\d+|[a-zA-Z])': r'\1^{\2}',
#         r'([a-zA-Z\)])\s*_\s*(\d+|[a-zA-Z])': r'\1_{\2}',
#         # 修复常见的函数名, e.g., "sin x" -> "\sin x"
#         r'\b(sin|cos|tan|log|ln)\b': r'\\\1',
#         # 修复向量表示, e.g., "vec a" -> "\vec{a}"
#         r'\bvec\s*([a-zA-Z])': r'\\vec{\1}',
#     }

#     for pattern, replacement in replacements_pattern.items():
#         cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
#     # --- 阶段3: 上下文感知修复 ---
#     # e.g., 修复被空格隔开的 "x ^ 2"
#     # 这个比较复杂，可以通过分词后检查，或者更复杂的正则
    
#     # --- 阶段4: 最终清理 ---
#     # 移除公式和文本之间的多余空格
#     cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text).strip()
    
#     return cleaned_text

# # --- 【新增】可复用的OCR处理总管 ---
# def get_ocr_text_from_image(image_bytes: bytes) -> str:
#     """
#     封装了 预处理 -> OCR识别 -> 类型适配 -> 文本清洗 的完整流程。
#     这是解决'Page'对象问题的最终方案。
#     """
#     print("\n--- [子流程] 开始OCR处理... ---")
#     preprocessed_image = image_preprocess_v2(image_bytes)
    
#     # 强制Pix2Text返回字符串，这是最关键的修复
#     ocr_result = p2t(preprocessed_image, return_text=True)
    
#     # 双重保险：检查返回类型
#     if not isinstance(ocr_result, str):
#         print(f"--- [警告] Pix2Text未返回字符串，类型为: {type(ocr_result)}。尝试调用.to_text()。")
#         if hasattr(ocr_result, 'to_text'):
#             ocr_result = ocr_result.to_text()
#         else:
#             ocr_result = str(ocr_result)
            
#     cleaned_text = ocr_text_clean_v2(ocr_result)
#     print(f"--- [子流程] OCR处理完成，清洗后文本: {cleaned_text[:80].strip()}...")
#     return cleaned_text

# def get_vision_description(image_bytes: bytes, temp_dir: str = "/tmp") -> str:
#     """封装了Vision识别的完整流程。"""
#     print("\n--- [子流程] 开始Vision处理... ---")
#     temp_image_path = os.path.join(temp_dir, f"temp_vision_{uuid.uuid4()}.png")
    
#     try:
#         with open(temp_image_path, "wb") as f:
#             f.write(image_bytes)
        
#         vision_prompt = """
# **核心任务**:
# 你是一个专业的图像分析引擎。请彻底解析下方图片中的所有【视觉信息】，并将其转化为对解题至关重要的、结构化的文字描述。

# **分析原则**:
# 1.  **绝对专注视觉**: **彻底忽略**图片中的所有长段文字（如题目、问题描述、选项）。你的分析对象仅限于**图形、图表、图像、示意图及其内部的标注**。
# 2.  **提取关键信息**: 你的目标是提取所有**无法**通过纯文本OCR获得的关键信息。例如：
#     *   **几何**: 图形类型、顶点/线段/角的关系（平行、垂直、相等）、标注的数值。
#     *   **图表**: 坐标轴含义、单位、关键点坐标（顶点、交点）、数据趋势。
#     *   **物理/化学/生物**: 装置连接关系、物质流向、受力方向、细胞结构、食物网关系等。
#     *   **地理**: 地图要素（等高线、河流、图例）、空间分布规律。
# 3.  **简洁且结构化**: 使用清晰的Markdown标题和列表来组织你的分析结果，语言要精炼、客观。

# **最终指令**:
# 如果图片中不包含任何有意义的、用于解题的视觉图形（例如，只是一段纯文字的截图），请直接回答：“图中未包含额外的视觉信息。” 否则，请开始你的分析。
# """
#         messages = [{'role': 'user', 'content': [{'text': vision_prompt}, {'image': f'file://{os.path.abspath(temp_image_path)}'}]}]
#         response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=messages)
        
#         if response.status_code == 200:
#             content = response.output.choices[0].message.content
#             if isinstance(content, list):
#                 for part in content:
#                     if part.get("text"):
#                         desc = part["text"]
#                         print(f"--- [子流程] Vision处理完成，描述: {desc[:80].strip()}...")
#                         return desc
#             elif isinstance(content, str):
#                 print(f"--- [子流程] Vision处理完成，描述: {content[:80].strip()}...")
#                 return content
#         else:
#              print(f"!!! Vision API调用失败: {response.message}")
#              return "视觉模型分析失败。"
#     finally:
#         if os.path.exists(temp_image_path):
#             os.remove(temp_image_path)
#     return "视觉模型未返回有效描述。"
# # ==============================================================================
# # 完整 main.py - 第二部分: FastAPI应用配置
# # ==============================================================================

# # --- 2. FastAPI应用配置 ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/")
# def read_root():
#     return {"message": "AI解题后端服务正在运行 (V14.2 终极重构版)"}
# # ==============================================================================
# # 完整 main.py - 第三部分: 核心API接口
# # ==============================================================================
# @app.post("/solve")
# async def solve_from_image(file: UploadFile = File(...)):
#     try:
#         initialize_pix2text()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"核心OCR服务初始化失败: {e}")

#     if not p2t or not kimi_client or not dashscope.api_key:
#         raise HTTPException(status_code=500, detail="核心AI服务未就绪")

    
#     temp_image_path = f"/tmp/temp_{uuid.uuid4()}.png"
#     try:
#         image_bytes = await file.read()
        
#         # --- 图像层 & 识别层 (A路) ---
#         preprocessed_image = image_preprocess_v2(image_bytes)
#         full_page_ocr_text = p2t(preprocessed_image, return_text=True)
        
#         # --- 【新增】专注力模块 (A.2路) ---
#         print("\n--- [A.2路] 正在提取题目主体... ---")
#         extractor_prompt = f"""
#         **核心任务**:
#         你是一个专业的文档分析师。下面是一张图片OCR识别出的所有文本。请从中**只提取出属于“题目”本身的核心内容**。

#         **提取规则**:
#         1.  **包含**: 题目的题干、问题(例如(1)(2))、所有选项（A, B, C, D等）、以及题目附带的公式和条件。
#         2.  **忽略**: 必须忽略所有与题目无关的内容，例如：“解题详情”、“答案解析”、“核心思路”、“第一个元素”、“页眉页脚”、“图1”、“选择题”等标题性或解释性文字。
#         3.  **输出**: 只输出提取出的、纯净的题目文本。如果OCR全文看起来就是一个干净的题目，就返回原文。

#         **【待处理的OCR全文】**:
#         ```
#         {full_page_ocr_text}
#         ```
#         """

#         extractor_response = kimi_client.chat.completions.create(
#             model="moonshot-v1-8k",
#             messages=[
#                 {"role": "system", "content": "你是一个精确的文本提取助手，严格遵循指令，只输出提取的题目内容，不加任何额外解释。"},
#                 {"role": "user", "content": extractor_prompt}
#             ],
#             temperature=0.0,
#         )
#         question_text = extractor_response.choices[0].message.content.strip()
#         print(f"--- [A.2路] 提取出的题目主体: {question_text[:200].strip()}...")
    
#         geometry_description = get_vision_description(image_bytes)

#         # --- C路: 【终极教师版Prompt】 ---
#         print("\n--- [C路] 开始信息融合并调用Kimi ---")
# #         
#         final_prompt = f"""
#         **核心任务**:
#         请根据下面提供的题目信息，为学生生成一份详尽、完整、步骤清晰的解题答案。

#         **【不可违背的黄金法则】**:

#         1.  **必须给出最终答案**:
#             *   对于计算题，必须给出最终的数值结果。
#             *   对于选择题，必须明确指出哪个选项是正确的 (例如, "因此，正确答案是 B。")。
#             *   对于证明题，必须给出最终的证明结论。
#             *   **绝对禁止**只提供解题思路或分析，而不给出最终答案。

#         2.  **必须展示完整过程**:
#             *   必须展示所有关键的推导、计算或论证步骤。
#             *   **绝对禁止**以“过程复杂”等任何理由省略步骤。

#         3.  **输出格式**:
#             *   **必须**使用标准的Markdown文本和LaTeX数学公式。
#             *   行内公式: **必须**严格使用 `$...$` 包裹。
#             *   块级公式: **必须**严格使用 `$$...$$` 包裹。

#         ---
#         **【题目信息】**

#         [OCR识别出的文字与公式]:
#         {question_text}

#         [视觉模型分析的图形信息]:
#         {geometry_description}
#         ---
#         """
#         print(final_prompt)
#         # system_prompt = """你是一位遵循指令的顶级的、极其负责任的高中全学科老师。你的任务是解析<INSTRUCTIONS>，处理<DATA>，然后生成最终的教学回答。"""
#         system_prompt = "你是一位经验丰富、富有同理心的全学科在线辅导老师。"
#         solution_response = kimi_client.chat.completions.create(
#             model="moonshot-v1-32k",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": final_prompt}
#             ],
#             temperature=0.2,# 降低温度，让逻辑更严谨
#             max_tokens=8192
#         )
#         final_markdown = solution_response.choices[0].message.content
#         return PlainTextResponse(content=final_markdown, media_type="text/markdown; charset=utf-8")
#     except Exception as e:
#         print(f"!!! 发生严重错误 !!!")
#         print(f"错误类型: {type(e).__name__}")
#         print(f"错误详情: {e}")
#         raise HTTPException(status_code=500, detail=f"处理时发生错误: {str(e)}")

# # ==============================================================================
# # 完整 main.py - 新增: 批改作业API接口
# # ==============================================================================
# @app.post("/review")
# async def review_from_images(
#     question_image: UploadFile = File(...),
#     answer_image: UploadFile = File(...)
# ):
#     try:
#         initialize_pix2text()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"核心OCR服务初始化失败: {e}")

#     if not p2t or not kimi_client or not dashscope.api_key:
#         raise HTTPException(status_code=500, detail="核心AI服务未就绪")
    

#     try:
#         # --- 1. 读取两张图片的字节流 ---
#         # --- 1. 处理题目图片 ---
        
#         # ... (通义千问获取 question_visual_info 的逻辑不变) ...

#         # --- 1. 处理题目图片 (OCR + 提纯) ---
#         print("\n--- 正在处理【题目】图片... ---")
#         question_image_bytes = await question_image.read()
#         q_preprocessed = image_preprocess_v2(question_image_bytes)
#         q_full_ocr = p2t(q_preprocessed, return_text=True)
#         # 调用AI进行提纯
#         extractor_prompt_q = f"""
#         **核心任务**:
#         你是一个专业的文档分析师。下面是一张图片OCR识别出的所有文本。请从中**只提取出属于“题目”本身的核心内容**。

#         **提取规则**:
#         1.  **包含**: 题目的题干、问题(例如(1)(2))、所有选项（A, B, C, D等）、以及题目附带的公式和条件。
#         2.  **忽略**: 必须忽略所有与题目无关的内容，例如：“解题详情”、“答案解析”、“核心思路”、“第一个元素”、“页眉页脚”、“图1”、“选择题”等标题性或解释性文字。
#         3.  **输出**: 只输出提取出的、纯净的题目文本。如果OCR全文看起来就是一个干净的题目，就返回原文。

#         **【待处理的OCR全文】**:
#         ```
#         {q_full_ocr}
#         ```
#         """
#         extractor_response_q = kimi_client.chat.completions.create(...) # (调用Kimi 8k)
#         question_ocr_text = extractor_response_q.choices[0].message.content.strip()
        
#         question_visual_info = get_vision_description(question_image_bytes)

#         # --- 2. 处理答案图片 (OCR + 提纯) ---
#         print("\n--- 正在处理【答案】图片... ---")
#         answer_image_bytes = await answer_image.read()
#         a_preprocessed = image_preprocess_v2(answer_image_bytes)
#         a_full_ocr = p2t(a_preprocessed, return_text=True)
#         # 调用AI进行提纯
#         extractor_prompt_a = f"""
#         **核心任务**:
#         你是一个专业的文档分析师。下面是一张图片OCR识别出的所有文本。请从中**只提取出属于“题目”本身的核心内容**。

#         **提取规则**:
#         1.  **包含**: 题目的题干、问题(例如(1)(2))、所有选项（A, B, C, D等）、以及题目附带的公式和条件。
#         2.  **忽略**: 必须忽略所有与题目无关的内容，例如：“解题详情”、“答案解析”、“核心思路”、“第一个元素”、“页眉页脚”、“图1”、“选择题”等标题性或解释性文字。
#         3.  **输出**: 只输出提取出的、纯净的题目文本。如果OCR全文看起来就是一个干净的题目，就返回原文。

#         **【待处理的OCR全文】**:
#         ```
#         {a_full_ocr}
#         ```
#         """
#         extractor_response_a = kimi_client.chat.completions.create(...) # (调用Kimi 8k)
#         answer_ocr_text = extractor_response_a.choices[0].message.content.strip()

#         answer_visual_info = get_vision_description(answer_image_bytes)

#         # --- 4. 构造【批改模式】的终极Prompt ---
#         print("\n--- 正在构造批改Prompt... ---")
#         review_prompt = f"""
#         **角色**: 你是一位极其专业、富有经验且鼓励性的批改老师。你的任务是仔细比对“标准题目”和“学生答案”，给出一份全面、有建设性的批改报告。

#         **核心任务**:
#         1.  **判断对错**: 首先，明确判断学生的最终答案是否正确。
#         2.  **分析过程**: 逐一分析学生答案中的解题步骤。

#         **【批改报告黄金法则】**:

#         1.  **如果答案正确**:
#             *   **明确表扬**: 首先要用积极、鼓励的语言肯定学生的成果，例如：“非常棒！你的答案是完全正确的，解题思路也很清晰！”
#             *   **点出亮点**: 指出学生做得好的地方，例如：“特别欣赏你在这里使用了配方法，非常巧妙。”
#             *   **提供优化建议**: 在肯定的基础上，提出可以优化的地方，例如：“如果这里能多一步关于定义域的讨论，那就更完美了。”或者“其实还有另一种更简洁的方法，你想了解一下吗？”

#         2.  **如果答案错误**:
#             *   **先肯定，后指正**: 不要直接否定。先找到学生做得对的部分并予以肯定，例如：“同学你好，你对正弦定理的理解和应用非常到位，这是一个很好的开始！”
#             *   **精准定位错误**: 明确指出学生**第一个**出错的步骤，并解释**为什么**错了。例如：“问题出在第二步的化简上，这里应该同乘以`2a`而不是`a`，因为...”
#             *   **给出正确示范**: 在指出错误后，给出从错误点开始的、正确的解题步骤和最终答案。
#             *   **鼓励结尾**: 用鼓励的话语结束，例如：“这只是一个小的疏忽，下次注意就好。你已经很接近正确答案了，加油！”

#         3.  **格式要求**:
#             *   使用清晰的Markdown格式，可以用“✅ 亮点解析”、“❌ 错误分析”、“💡 优化建议”等标题来组织报告。
#             *   所有数学公式必须使用标准的LaTeX语法。

#         ---
#         **【批改材料】**

#         <QUESTION_DATA>
#             <OCR_TEXT>{question_ocr_text}</OCR_TEXT>
#             <VISUAL_INFO>{question_visual_info}</VISUAL_INFO>
#         </QUESTION_DATA>

#         <STUDENT_ANSWER_DATA>
#             <OCR_TEXT>{answer_ocr_text}</OCR_TEXT>
#             <VISUAL_INFO>{answer_visual_info}</VISUAL_INFO>
#         </STUDENT_ANSWER_DATA>
#         """

#         # --- 5. 调用Kimi API并返回结果 ---
#         print("\n--- 正在调用Kimi生成批改报告... ---")
#         system_prompt_review = "你是一位负责批改作业、并提供高质量、鼓励性反馈的辅导老师。"
        
#         solution_response = kimi_client.chat.completions.create(
#             model="moonshot-v1-32k",
#             messages=[
#                 {"role": "system", "content": system_prompt_review},
#                 {"role": "user", "content": review_prompt}
#             ],
#             temperature=0.2,
#             max_tokens=8192
#         )
#         final_markdown = solution_response.choices[0].message.content
        
#         return {"solution": final_markdown}

#     except Exception as e:
#         print(f"!!! 发生严重错误 !!!")
#         print(f"错误类型: {type(e).__name__}")
#         print(f"错误详情: {e}")
#         raise HTTPException(status_code=500, detail=f"处理时发生错误: {str(e)}")
    