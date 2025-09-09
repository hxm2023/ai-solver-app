# # ==============================================================================
# # 完整 main.py - 【V6.5 灵魂注入最终版】
# # ==============================================================================

# # --- Python标准库 ---
# import os
# import io
# import base64
# import re
# import uuid
# import contextlib

# # --- 第三方库 ---
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from PIL import Image
# from pix2text import Pix2Text
# from dotenv import load_dotenv

# # --- AI库 (根据官方推荐的兼容模式) ---
# from openai import OpenAI  # 用于调用Kimi
# import dashscope             # 通义千问官方SDK

# # --- 1. 初始化 ---
# load_dotenv()
# app = FastAPI()

# print("正在初始化 Pix2Text...")
# p2t = Pix2Text()
# print("Pix2Text 初始化完成。")

# print("正在初始化Kimi客户端 (OpenAI兼容模式)...")
# try:
#     kimi_client = OpenAI(
#         api_key=os.getenv("MOONSHOT_API_KEY"),
#         base_url="https://api.moonshot.cn/v1",
#     )
#     if not os.getenv("MOONSHOT_API_KEY"): raise ValueError("API Key not found in .env")
#     print("Kimi客户端初始化成功。")
# except Exception as e:
#     print(f"!!! 初始化Kimi客户端失败，请检查.env文件中的MOONSHOT_API_KEY: {e}")
#     kimi_client = None

# print("正在配置通义千问API Key...")
# try:
#     dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
#     if not dashscope.api_key: raise ValueError("API Key not found in .env")
#     print("通义千问API Key配置成功。")
# except Exception as e:
#     print(f"!!! 配置通义千问API Key失败，请检查.env文件中的DASHSCOPE_API_KEY: {e}")
# # ==============================================================================
# # 完整 main.py - 第二部分: FastAPI配置
# # ==============================================================================

# # --- 2. 静态文件目录与CORS配置 ---
# GENERATED_IMAGES_DIR = "generated_images"
# os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
# app.mount("/static", StaticFiles(directory=GENERATED_IMAGES_DIR), name="static")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def read_root():
#     return {"message": "AI解题后端服务正在运行 (V6.5 灵魂注入版)"}
# # ==============================================================================
# # 完整 main.py - 第三部分: 核心API接口
# # ==============================================================================
# @app.post("/solve")
# async def solve_from_image(file: UploadFile = File(...)):
#     if not kimi_client or not dashscope.api_key:
#         raise HTTPException(status_code=500, detail="核心AI服务客户端未成功初始化，请检查后端日志和API Keys。")

#     temp_image_path = f"temp_{uuid.uuid4()}.png"
#     try:
#         image_bytes = await file.read()
        
#         # --- A路: Pix2Text OCR ---
#         print("\n--- [A路] 开始Pix2Text OCR识别 ---")
#         question_text = p2t.recognize(Image.open(io.BytesIO(image_bytes)), return_text=True)
#         print(f"--- [A路] 识别结果: {question_text[:100].strip()}...")
        
#         # --- B路: 通义千问 qwen-vl-max 进行图形理解 ---
#         print("\n--- [B路] 开始通义千问Vision图形理解 ---")
#         vision_prompt = "请用简洁的语言描述这张图片中的几何图形信息（顶点、关系、已知条件等），忽略所有文字。"
        
#         with open(temp_image_path, "wb") as f:
#             f.write(image_bytes)
            
#         messages = [{
#             'role': 'user',
#             'content': [
#                 {'text': vision_prompt},
#                 {'image': f'file://{os.path.abspath(temp_image_path)}'}
#             ]
#         }]
        
#         vision_response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=messages)
        
#         if vision_response.status_code != 200:
#             raise Exception(f"通义千问API调用失败: Code {vision_response.status_code}, Message: {vision_response.message}")

#         raw_content_list = vision_response.output.choices[0].message.content
#         geometry_description = ""
#         if isinstance(raw_content_list, list):
#             for part in raw_content_list:
#                 if part.get("text"):
#                     geometry_description = part["text"]
#                     break
#         elif isinstance(raw_content_list, str):
#             geometry_description = raw_content_list
        
#         if not geometry_description:
#             print("--- [B路] 通义千问未返回有效的文本描述。")
#         else:
#             print(f"--- [B路] 通义千问描述结果: {geometry_description[:100].strip()}...")
        
#         # --- C路: 【灵魂注入版Prompt】 ---
#         print("\n--- [C路] 开始信息融合并调用Kimi ---")
#         final_prompt = f"""
#         **背景情景**: 你是一位非常有经验和亲和力的数学老师，正在为一名有些困惑的学生进行一对一辅导。你的目标不仅是给出答案，更是要用循循诱导的方式，让学生彻底理解解题的思路和方法。

#         **你的教学风格**:
#         *   **亲切自然**: 使用“好的，同学”、“我们一起来看”、“首先，我们要明确...”这样的口吻，就像在和学生面对面交流。
#         *   **聚焦思路**: 在给出具体计算前，先用一两句话点明这一步的“核心思路”或“关键公式”，让学生知道为什么这么做。
#         *   **自信从容**: 你是老师，已经对答案了然于胸。请直接展示正确、流畅的推导过程。**绝对不要**在回答中出现“我算错了”、“让我们重新检查”、“这里可能存在误解”等自我怀疑或暴露思考过程的语言。你只需要呈现最终的、完美的教学内容。
#         *   **详尽完整**: **绝对不能**以任何理由省略任何关键的证明或计算步骤。每一个问题都必须得到完整的解答。

#         **输出格式**:
#         *   使用标准的Markdown来组织段落和列表。
#         *   所有数学变量、符号和公式，都必须严格使用标准的LaTeX语法包裹（行内公式用`$...$`，块级公式用`$$...$$`）。

#         ---
#         **【辅导材料】**

#         [学生遇到的题目 - 文字与公式]:
#         {question_text}

#         [学生遇到的题目 - 图形信息]:
#         {geometry_description}

#         ---
#         好了，老师，这位同学正在期待你的讲解。请开始吧！
#         """
        
#         # 调用Kimi API
#         solution_response = kimi_client.chat.completions.create(
#             model="moonshot-v1-32k",
#             messages=[
#                 {"role": "system", "content": "你是一位顶级的、富有同理心的数学家教，擅长将复杂问题讲得清晰易懂。"},
#                 {"role": "user", "content": final_prompt}
#             ],
#             temperature=0.3,
#             max_tokens=8192
#         )
#         raw_solution_markdown = solution_response.choices[0].message.content
        
#         # --- D路: 直接返回原始输出 ---
#         print("\n--- [D路] AI返回原始答案，交由前端处理格式 ---")
#         return {"solution": raw_solution_markdown}

#     except Exception as e:
#         print(f"!!! 发生严重错误 !!!")
#         print(f"错误类型: {type(e).__name__}")
#         print(f"错误详情: {e}")
#         raise HTTPException(status_code=500, detail=f"处理时发生错误: {str(e)}")
#     finally:
#         # 无论成功或失败，都确保临时文件被删除
#         if os.path.exists(temp_image_path):
#             os.remove(temp_image_path)



# ==============================================================================
# 完整 main.py - 【V10.0 最终架构版，AI规划+计算机执行+AI总结】
# ==============================================================================

# --- Python标准库 ---
# --- 【核心修复】: 在所有import之前，设置环境变量禁用多进程 ---
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import io
import base64
import re
import uuid
import contextlib

# --- 第三方库 ---
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pix2text import Pix2Text
from dotenv import load_dotenv

# --- AI库 ---
from openai import OpenAI  # 用于调用Kimi
import dashscope             # 通义千问官方SDK

# --- 数学计算库 ---
import sympy as sp
import numpy as np

# --- 1. 初始化 ---
load_dotenv()
app = FastAPI()

# print("正在初始化 Pix2Text...")
# # --- 【核心修复】: 强制指定使用CPU ---
# p2t = Pix2Text(device='cpu') 
# print("Pix2Text 初始化完成，已强制使用CPU模式。")

# 【核心修复】: 只在全局定义一个空的p2t变量
p2t = None

# 【核心修复】: 创建一个函数来处理耗时的初始化
def initialize_pix2text():
    global p2t
    if p2t is None:
        print("首次请求：正在初始化 Pix2Text (这可能需要一些时间)...")
        # 强制指定缓存目录到/tmp，这是一个保证可写的临时目录
        cache_dir = "/tmp/pix2text_cache"
        os.makedirs(cache_dir, exist_ok=True)
        p2t = Pix2Text(device='cpu', root=cache_dir)
        print("Pix2Text 初始化完成。")

print("正在初始化Kimi客户端 (OpenAI兼容模式)...")
try:
    kimi_client = OpenAI(
        api_key=os.getenv("MOONSHOT_API_KEY"),
        base_url="https://api.moonshot.cn/v1",
    )
    if not os.getenv("MOONSHOT_API_KEY"): raise ValueError("API Key not found in .env")
    print("Kimi客户端初始化成功。")
except Exception as e:
    print(f"!!! 初始化Kimi客户端失败，请检查.env文件中的MOONSHOT_API_KEY: {e}")
    kimi_client = None

print("正在配置通义千问API Key...")
try:
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key: raise ValueError("API Key not found in .env")
    print("通义千问API Key配置成功。")
except Exception as e:
    print(f"!!! 配置通义千问API Key失败，请检查.env文件中的DASHSCOPE_API_KEY: {e}")

# --- 2. FastAPI应用配置 ---
GENERATED_IMAGES_DIR = "generated_images"
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=GENERATED_IMAGES_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI解题后端服务正在运行 (V10.0 最终架构版)"}
# ==============================================================================
# 完整 main.py - 第二部分: 核心API接口
# ==============================================================================

@app.post("/solve")
async def solve_from_image(file: UploadFile = File(...)):
    # 【核心修复】: 在处理请求的开始，调用初始化函数
    try:
        initialize_pix2text()
    except Exception as e:
        print(f"!!! Pix2Text 初始化失败: {e}")
        raise HTTPException(status_code=500, detail=f"核心OCR服务初始化失败: {e}")

    if not p2t or not kimi_client or not dashscope.api_key:
        raise HTTPException(status_code=500, detail="核心AI服务未就绪")

    temp_image_path = f"/tmp/temp_{uuid.uuid4()}.png" # 使用/tmp目录
    try:
        image_bytes = await file.read()
        
        # --- A路 & B路: 提取题目信息 ---
        print("\n--- [A&B路] 提取题目信息... ---")
        question_text = p2t.recognize(Image.open(io.BytesIO(image_bytes)), return_text=True)
        
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)
        
        vision_prompt = "请用简洁的语言描述这张图片中的几何图形信息（顶点、关系、已知条件等），忽略所有文字。"
        messages = [{'role': 'user', 'content': [{'text': vision_prompt}, {'image': f'file://{os.path.abspath(temp_image_path)}'}]}]
        vision_response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=messages)
        
        if vision_response.status_code != 200:
            geometry_description = "视觉模型分析失败。"
            print(f"!!! 通义千问API调用失败: {vision_response.message}")
        else:
            raw_content_list = vision_response.output.choices[0].message.content
            geometry_description = ""
            if isinstance(raw_content_list, list):
                for part in raw_content_list:
                    if part.get("text"):
                        geometry_description = part["text"]
                        break
            elif isinstance(raw_content_list, str):
                geometry_description = raw_content_list

        print(f"--- 识别到的文本: {question_text[:100].strip()}...")
        print(f"--- 识别到的图形信息: {geometry_description[:100].strip()}...")

        # --- 步骤 1: 【终极版】AI规划师Prompt ---
        planner_prompt = f"""
        **角色**: 你是一个顶级的Python程序员和数学专家，任务是为下面的数学题编写一个**单一、完整、自给自足**的Python脚本来解决它。
        
        **脚本核心要求**:
        1.  **展示过程 (Show Your Work)**: 在进行任何求解或化简之前，**必须**先用 `print()` 和 `sp.pretty()` 打印出你将要操作的**原始符号方程式**。
        2.  **清晰输出**: **必须** 通过 `print()` 语句，分步输出所有关键的中间计算结果和最终答案。每个print输出前，请用一个简短的描述性文字说明。
        3.  **精确计算**: 使用 `sympy` 库进行所有代数运算。
        4.  **代码块**: 整个脚本必须被包裹在 ````python ... ``` ` 中。

        **【一个完美的脚本示例】**:
        ```python
        import sympy as sp
        x = sp.Symbol('x')
        # 首先，打印出要解的方程
        print("需要求解的方程是:")
        equation = sp.Eq(x**2 - 4, 0)
        print(sp.pretty(equation))
        # 然后，求解并打印结果
        solutions = sp.solve(equation, x)
        print("方程的解是:")
        print(solutions)
        ```

        **题目信息**:
        [OCR文本]: {question_text}
        [图形描述]: {geometry_description}

        请开始编写一个能够展示完整思考过程的Python脚本。
        """
        
        print("\n--- [步骤 1] 正在请求AI生成解题脚本... ---")
        script_response = kimi_client.chat.completions.create(model="moonshot-v1-32k", messages=[{"role": "user", "content": planner_prompt}], temperature=0.0)
        script_markdown = script_response.choices[0].message.content

        # --- 步骤 2: 后端执行脚本并捕获结果 ---
        print("\n--- [步骤 2] 正在执行AI脚本并捕获结果... ---")
        pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)
        match = pattern.search(script_markdown)
        if not match:
            print("--- [步骤 2] AI未生成代码，将其回答作为最终讲解。")
            return {"solution": script_markdown}

        code_to_execute = match.group(1)
        
        image_url = None
        if 'plt.savefig' in code_to_execute:
            image_filename = f"{uuid.uuid4()}.png"
            image_path = os.path.join(GENERATED_IMAGES_DIR, image_filename)
            code_to_execute = code_to_execute.replace("savefig('image.png')", f"savefig('{image_path}')")
            image_url = f"/static/{image_filename}"
        
        # 捕获脚本的所有print输出
        stdout_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout_capture):
                # 为sympy的pretty print准备环境，并提供所有需要的库
                execution_scope = {
                    "sp": sp,
                    "np": np,
                    "plt": plt,
                    "__builtins__": None,
                }
                exec("import sympy as sp; import numpy as np; import matplotlib.pyplot as plt", execution_scope)
                # 执行AI生成的代码
                exec(code_to_execute, execution_scope)
            
            if image_url:
                print(f"--- 图片生成成功: {image_url} ---")

        except Exception as e:
            print(f"!!! AI脚本执行失败: {e}")
            stdout_capture.write(f"\n在执行解题代码时发生了错误: {e}")

        calculation_results = stdout_capture.getvalue()
        print(f"--- 捕获的计算结果 ---\n{calculation_results}")

        # --- 步骤 3: 【终极版】AI讲解员Prompt ---
        teacher_prompt = f"""
        **背景情景**: 你是一位和蔼可亲、经验丰富的数学老师。
        **核心任务**: 这里有一份由计算机程序生成的、**包含详细中间步骤**的计算日志。请你**只使用**这些材料，为学生写一篇流畅、自然、循序渐进的讲解。

        **【不可违背的黄金法则】**:
        1.  **忠于过程**: 你必须将“计算结果日志”中提供的**所有中间方程式和推导步骤**，自然地融入到你的讲解中，向学生展示问题是如何一步步被解决的。
        2.  **严禁自己计算**: 你的所有结论都必须基于日志内容。
        3.  **严禁出现代码**: 你的回答中 **绝对不能** 出现任何Python代码。
        4.  **扮演好老师**: 解释每一步的“为什么”，而不仅仅是“是什么”。

        **【可使用的材料】**

        [原始题目]:
        {question_text}

        [计算机生成的、包含过程的计算结果日志]:
        ```
        {calculation_results}
        ```
        ---
        好了，老师，请用上面的详细材料，为学生带来一堂完美的解题课吧！
        """
        
        print("\n--- [步骤 3] 正在请求AI生成最终讲解... ---")
        final_solution_response = kimi_client.chat.completions.create(model="moonshot-v1-32k", messages=[
            {"role": "system", "content": "你是一位顶级的数学家教，擅长将复杂的计算过程，转述为学生能听懂的、富有亲和力的讲解。"},
            {"role": "user", "content": teacher_prompt}
        ], temperature=0.5, max_tokens=8192)
        final_solution_markdown = final_solution_response.choices[0].message.content

        return {"solution": final_solution_markdown}

    except Exception as e:
        print(f"!!! 发生严重错误 !!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        raise HTTPException(status_code=500, detail=f"处理时发生错误: {str(e)}")
    finally:
        # 无论成功或失败，都确保临时文件被删除
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)