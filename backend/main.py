# ==============================================================================
# 完整 main.py - 【V12.0 终极教师版】
# ==============================================================================

# --- 【核心】: 在所有import之前，设置环境变量禁用多进程 ---
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# --- Python标准库 ---
import io
import base64
import cv2
import re
import uuid
import numpy as np



# --- 第三方库 ---
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from PIL import Image, ImageOps
from pix2text import Pix2Text
from dotenv import load_dotenv

# --- AI库 ---
from openai import OpenAI
import dashscope

# --- 1. 初始化 ---
load_dotenv()
app = FastAPI()

# 懒加载 Pix2Text
p2t = None
def initialize_pix2text():
    global p2t
    if p2t is None:
        print("首次请求：正在以安全模式初始化 Pix2Text...")
        # 在云环境中，/tmp是保证可写的临时目录
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
    print(f"!!! 初始化Kimi客户端失败: {e}")
    kimi_client = None

print("正在配置通义千问API Key...")
try:
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key: raise ValueError("API Key not found in .env")
    print("通义千问API Key配置成功。")
except Exception as e:
    print(f"!!! 配置通义千问API Key失败: {e}")
    
    
# --- 2. 核心辅助函数 (来自Kimi的建议) ---

def image_preprocess_v2(image_bytes: bytes, max_size: int = 2048) -> Image.Image:
    """
    一个工程级的图片预处理流水线。
    :param image_bytes: 原始图片字节流
    :param max_size: 图片长边的最大尺寸
    :return: 经过优化处理的PIL Image对象 (灰度图)
    """
    try:
        # 1. 从字节流加载图片 (使用OpenCV)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 2. 尺寸归一化
        h, w = img_cv.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            img_cv = cv2.resize(img_cv, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        # 3. 转换为灰度图
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # 4. 角度校正 (Deskew)
        # 这是一个简化的实现，基于寻找最小面积的包围矩形
        coords = np.column_stack(np.where(gray < 128))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        if abs(angle) > 1: # 只对倾斜超过1度的图片进行校正
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            print(f"--- 图片已自动校正角度: {angle:.2f} 度 ---")

        # 5. 降噪 (使用高斯模糊)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 6. 智能自适应二值化 (处理光照不均)
        # ADAPTIVE_THRESH_GAUSSIAN_C 效果通常比 MEAN_C 更好
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # 7. (可选) 锐化 - 拉普拉斯算子
        sharpened = cv2.Laplacian(binary, cv2.CV_64F)
        sharpened = np.uint8(np.clip(binary - 0.5 * sharpened, 0, 255))

        # 8. 将处理后的OpenCV图像转回PIL Image对象
        img_pil = Image.fromarray(binary)
        
        return img_pil

    except Exception as e:
        print(f"!!! 图片预处理失败: {e}. 将使用原始图片进行识别。")
        # 如果预处理失败，优雅降级，返回原始的灰度图
        return Image.open(io.BytesIO(image_bytes)).convert('L')

def ocr_text_clean_v2(raw_text: str) -> str:
    """
    一个工程级的、多阶段的OCR文本清洗函数。
    """
    # 检查输入是否为字符串
    if not isinstance(raw_text, str):
        print(f"!!! 文本清洗函数收到非字符串类型: {type(raw_text)}，将返回空字符串。")
        return ""
    
    # --- 阶段1: 基础字符归一化 ---
    # 替换所有中文标点和常见错认字符
    replacements_char = {
        '（': '(', '）': ')', '【': '[', '】': ']', '，': ',', '。': '.',
        '＋': '+', '－': '-', '×': '*', '÷': '/', '＝': '=',
        'α': '\\alpha', 'β': '\\beta', 'γ': '\\gamma', 'θ': '\\theta', 'π': '\\pi',
        'Δ': '\\Delta', 'Ω': '\\Omega',
        '≤': '\\leq', '≥': '\\geq', '≠': '\\neq',
        '∈': '\\in', '∀': '\\forall', '∃': '\\exists',
        '→': '\\rightarrow',
        '⊥': '\\perp',
    }
    for old, new in replacements_char.items():
        raw_text = raw_text.replace(old, new)
        
    cleaned_text = raw_text
    
    # --- 阶段2: 基于模式的通用修复 (高频错误) ---
    # 使用正则表达式，按优先级顺序执行
    # (key是正则表达式, value是替换格式)
    replacements_pattern = {
        # 修复 sqrt, e.g., "sqrt3" -> "\sqrt{3}"
        r'sqrt\s*(\d+|[a-zA-Z])': r'\\sqrt{\1}',
        # 修复 frac, e.g., "frac12" -> "\frac{1}{2}", "fracab" -> "\frac{a}{b}"
        r'frac\s*(\d+|[a-zA-Z])\s*(\d+|[a-zA-Z])': r'\\frac{\1}{\2}',
        # 修复上下标, e.g., "x^2", "x_1" -> "$x^2$", "$x_1$" (先不加$, 后续处理)
        # 这里只做规范化
        r'([a-zA-Z\)])\s*\^\s*(\d+|[a-zA-Z])': r'\1^{\2}',
        r'([a-zA-Z\)])\s*_\s*(\d+|[a-zA-Z])': r'\1_{\2}',
        # 修复常见的函数名, e.g., "sin x" -> "\sin x"
        r'\b(sin|cos|tan|log|ln)\b': r'\\\1',
        # 修复向量表示, e.g., "vec a" -> "\vec{a}"
        r'\bvec\s*([a-zA-Z])': r'\\vec{\1}',
    }

    for pattern, replacement in replacements_pattern.items():
        cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
    # --- 阶段3: 上下文感知修复 ---
    # e.g., 修复被空格隔开的 "x ^ 2"
    # 这个比较复杂，可以通过分词后检查，或者更复杂的正则
    
    # --- 阶段4: 最终清理 ---
    # 移除公式和文本之间的多余空格
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text).strip()
    
    return cleaned_text
# ==============================================================================
# 完整 main.py - 第二部分: FastAPI应用配置
# ==============================================================================

# --- 2. FastAPI应用配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- 【新增】可复用的OCR处理函数 ---
def process_ocr(image: Image.Image) -> str:
    """封装了OCR识别、类型适配和文本清洗的完整流程"""
    ocr_result = p2t(image, return_text=True)
    
    raw_ocr_text = ""
    if isinstance(ocr_result, str):
        raw_ocr_text = ocr_result
    elif hasattr(ocr_result, '__iter__'):
        try:
            text_parts = [item['text'] for item in ocr_result if 'text' in item]
            raw_ocr_text = "\n".join(text_parts)
        except Exception:
            raw_ocr_text = str(ocr_result)
    else:
        raw_ocr_text = str(ocr_result)
        
    return ocr_text_clean_v2(raw_ocr_text)

@app.get("/")
def read_root():
    return {"message": "AI解题后端服务正在运行 (V12.0 终极教师版)"}
# ==============================================================================
# 完整 main.py - 第三部分: 核心API接口
# ==============================================================================
@app.post("/solve")
async def solve_from_image(file: UploadFile = File(...)):
    try:
        initialize_pix2text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"核心OCR服务初始化失败: {e}")

    if not p2t or not kimi_client or not dashscope.api_key:
        raise HTTPException(status_code=500, detail="核心AI服务未就绪")

    temp_image_path = f"/tmp/temp_{uuid.uuid4()}.png"
    try:
        image_bytes = await file.read()
        print("\n--- [预处理] 正在进行图像修复与增强... ---")
        # 步骤1: 调用【新】的图片预处理函数
        preprocessed_image = image_preprocess_v2(image_bytes)

        # --- A路: OCR识别 (【核心修复】: 增加万能适配器) ---
        print("\n--- [A路] 开始Pix2Text OCR识别 ---")
        # 我们继续使用 return_text=True，因为它在大多数情况下是有效的
        ocr_result = p2t(preprocessed_image, return_text=True)

        raw_ocr_text = ""
        # --- 万能适配器逻辑 ---
        if isinstance(ocr_result, str):
            # 情况1: Pix2Text按预期返回了字符串
            print("--- [A路] Pix2Text返回了字符串(正常)。")
            raw_ocr_text = ocr_result
        elif hasattr(ocr_result, '__iter__'): 
            # 情况2: Pix2Text返回了一个可迭代对象 (比如列表或Page对象)
            print(f"--- [A路] Pix2Text返回了非字符串对象: {type(ocr_result)}，正在提取文本...")
            # Page对象可以像列表一样迭代，每个元素是一个包含'text'的字典
            try:
                # Page对象的标准提取方式
                text_parts = [item['text'] for item in ocr_result if 'text' in item]
                raw_ocr_text = "\n".join(text_parts)
            except Exception as extract_error:
                print(f"!!! 从{type(ocr_result)}对象中提取文本失败: {extract_error}")
                # 最后的备用方案：尝试将其转换为字符串
                raw_ocr_text = str(ocr_result)
        else:
            # 情况3: 返回了其他未知类型，做最后的转换尝试
            print(f"--- [A路] Pix2Text返回了未知类型: {type(ocr_result)}，将尝试强制转换。")
            raw_ocr_text = str(ocr_result)

        # --- 清洗OCR文本 ---
        print("\n--- [清洗] 正在修复OCR识别错误... ---")
        cleaned_ocr_text = ocr_text_clean_v2(raw_ocr_text)
        print(f"--- 清洗后的OCR文本: {cleaned_ocr_text[:100].strip()}...")
        # --- B路: 使用【原始】图片进行Vision识别 ---
        # Vision模型通常在原始彩色图上表现更好
        print("\n--- [B路] 开始通义千问Vision图形理解 ---")
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)
        
        vision_prompt = """
        **最高指令**: 你是一个极其精密和严谨的多模态图像分析引擎。你的唯一任务是彻底解析下方图片中的所有非文本视觉信息，并将其转化为结构化的、对解题至关重要的文字描述。

        **核心原则**:
        1.  **绝对专注**: 彻底忽略图片中所有的题目文本、问题描述、选项文字。你的眼中只有图形、图表、符号和数据本身。
        2.  **结构化输出**: 使用清晰的Markdown标题和列表来组织你的分析结果。
        3.  **智能适配**: 根据图片内容，自动选择并深度遵循下方最匹配的分析框架。

        ---
        **【分析框架库】**

        **1. 如果是【平面或立体几何图形】:**
            *   **图形识别**:
                *   **类型**: 明确指出是平面几何还是立体几何。识别所有基础图形（如：三角形、四边形、圆形、扇形）和组合图形（如：由...和...组成的图形），以及立体几何体（如：棱柱、棱锥、圆柱、球体）。
                *   **特殊性质**: 识别并强调图形的特殊性质（如：等腰直角三角形、正六边形、正四面体、圆锥内切于圆柱）。
            *   **元素与标注**:
                *   **点**: 列出所有顶点、中点、垂足、切点、交点、重心、内心等，并注明其标签（如: A, B, C, O, M, H）。
                *   **线**: 识别所有线段、射线、直线、辅助线（特别是虚线），并描述其特征（如：中位线、角平分线、高线、切线）。
                *   **面**: 对于立体几何，识别并命名所有重要的平面（如：平面 ABCD, 侧面 A_1ABB_1）。
            *   **关系与条件**:
                *   **位置关系**: 精确描述线与线（平行、垂直、相交、异面）、线与面（平行、垂直、在平面内）、面与面（平行、垂直）的关系。
                *   **角度关系**: 提取所有明确标注的角度值（如：∠ABC = 90°），并指出隐含的角度关系（如：对顶角相等、同位角相等）。
                *   **长度/数值关系**: 提取所有标注的长度、面积、体积等数值，并指出隐含的相等关系（如：AB = AC，由等腰三角形符号可知）。

        **2. 如果是【函数图像或数据图表】 (折线图, 柱状图, 散点图, 饼图等):**
            *   **图表识别**:
                *   **类型**: 明确图表类型。
                *   **标题与单位**: 识别图表的主标题，以及X轴和Y轴分别代表的物理量或统计量及其单位（如：X轴-时间(s), Y轴-速度(m/s)）。
            *   **数据点与特征**:
                *   **特殊点**: 精确提取并描述所有关键点的坐标，包括但不限于：与坐标轴的交点（截距）、顶点、极值点（极大/极小）、拐点、奇点、函数的周期。
                *   **交点**: 如果有多条曲线，描述它们之间的交点坐标。
                *   **数据值**: 对于柱状图/饼图，精确读出每个类别对应的数值或百分比。
            *   **趋势与行为**:
                *   **单调性**: 描述函数在不同区间的增减性。
                *   **凹凸性/曲率**: 描述函数的凹凸性变化。
                *   **相关性**: 对于散点图，描述变量之间可能存在的正相关、负相关或不相关。
                *   **比较**: 对于多组数据，进行横向或纵向的比较分析（如：A组的增长率高于B组）。

        **3. 如果是【物理模型图】 (力学, 电磁学, 光学, 热学等):**
            *   **场景识别**: 识别物理场景（如：天体运动、单摆、碰撞、斜面滑块、带电粒子在磁场中运动、光的折射/反射、热力学循环）。
            *   **物体与状态**:
                *   **物体**: 列出所有研究对象（如：物体A, 小球m, 活塞, 光滑/粗糙表面）。
                *   **初始状态**: 描述系统在t=0时刻的状态（如：静止、初速度v_0、开关S断开）。
                *   **过程**: 描述将要发生或正在发生的物理过程（如：自由落体、匀速圆周运动、弹性碰撞）。
            *   **受力/场线分析**:
                *   **力**: 如果有受力分析图，列出所有画出的力（如：重力G, 支持力N, 摩擦力f, 拉力T）。
                *   **场**: 描述电场线或磁感线的方向、疏密分布。
            *   **元器件与连接 (电学)**:
                *   **元件**: 识别电源（直流/交流）、电阻、电容、电感、电压表、电流表、滑动变阻器等，并注明其标签（R1, L2）。
                *   **连接**: 精确描述是串联还是并联。

        **4. 如果是【化学模型图】 (实验装置, 分子结构, 反应坐标图):**
            *   **仪器与装置**:
                *   **识别**: 列出所有实验仪器（如：烧杯, 锥形瓶, 分液漏斗, 冷凝管, 气密性检查装置）。
                *   **连接**: 描述仪器的连接顺序和物质的流向。
                *   **条件**: 识别反应所需的条件（如：加热（△）, 催化剂, 高温高压）。
            *   **物质与反应**:
                *   **物质**: 识别关键的反应物、生成物、催化剂，并注明其化学式和状态（(s), (l), (g), (aq)）。
                *   **微观结构**: 对于分子/晶体结构图，描述其化学键类型（单键/双键）、空间构型（平面/四面体）、官能团。
            *   **能量/速率图**: 对于反应坐标图，提取活化能、反应热（焓变ΔH）的数值和正负。

        **5. 如果是【地理/地质图】 (地图, 等高线, 地质剖面, 大气环流等):**
            *   **图表类型**: 识别图表类型（如：等高线地形图、洋流模式图、气候类型分布图、地质剖面图、天气系统图）。
            *   **核心要素与图例**:
                *   **要素**: 提取所有关键地理要素（如：山脉, 山脊, 山谷, 河流, 湖泊, 海岸线, 经纬线, 城市, 比例尺, 指向标）。
                *   **图例解读**: 详细解释图例中所有符号、颜色、线条的含义。
            *   **空间分析**:
                *   **数值读取**: 读出等高线/等温线/等压线的数值，并判断高低趋势。
                *   **位置关系**: 描述地理要素的精确或相对位置（如：A城位于B山的东南方向）。
                *   **分布规律**: 总结图中地理现象的分布特征（如：降水由东南沿海向西北内陆递减）。

        **6. 如果是【生物模型图】 (细胞结构, 生态系统, 遗传图谱, 生理过程):**
            *   **结构与标注**:
                *   **宏观/微观**: 判断是宏观层面（生态系统、食物网）还是微观层面（细胞、分子）。
                *   **识别**: 列出所有被标注的生物结构（如：细胞核, 叶绿体, 神经元, 基因A/a）及其名称。
            *   **过程与关系**:
                *   **流程**: 描述图中展示的生命活动过程（如：光合作用、呼吸作用、神经冲动传导、蛋白质合成、基因遗传）。
                *   **关系**: 描述生物体之间或结构之间的关系（如：捕食关系、物质循环、能量流动、信息传递）。
                *   **遗传分析**: 对于遗传图谱，识别显性/隐性关系、判断遗传病类型（常染色体/性染色体遗传）。

        ---
        **最终指令**: 如果图片内容不属于以上任何一种，或者极其模糊无法辨认，请回答“图中未包含可供分析的有效视觉信息”。否则，请严格按照最匹配的框架进行详细分析。
        """
        messages = [{'role': 'user', 'content': [{'text': vision_prompt}, {'image': f'file://{os.path.abspath(temp_image_path)}'}]}]
        vision_response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=messages)
        
        geometry_description = ""
        if vision_response.status_code == 200:
            raw_content_list = vision_response.output.choices[0].message.content
            if isinstance(raw_content_list, list):
                for part in raw_content_list:
                    if part.get("text"):
                        geometry_description = part["text"]
                        break
            elif isinstance(raw_content_list, str):
                geometry_description = raw_content_list

        print(f"--- 识别到的图形信息: {geometry_description[:100].strip()}...")

        # --- C路: 【终极教师版Prompt】 ---
        print("\n--- [C路] 开始信息融合并调用Kimi ---")
        final_prompt = f"""
    <INSTRUCTIONS>
        **你的角色**: 你是一位顶级的在线全学科家教，你的核心任务是**回答问题**，而不是描述图片，或者只给解析不给最终答案。

        **你的核心任务**:
        仔细阅读下方 `<QUESTION>` 标签中提供的、从图片中识别出的**【学生的问题】**。然后，利用 `<CONTEXT>` 标签中提供的**【辅助性视觉信息】**作为参考，首先判断题目所属的【学科领域】，然后调用你对应领域的专家知识，生成一份详尽、完整、富有启发性且绝对正确的解题步骤。你的目标是不仅让学生知道答案，也要让他理解背后的原理。
        ---
        **【第一步：学科判断与思维模式切换】**
        请在开始解答前，先在内心判断题目属于哪个学科（语文、历史、政治、英语、数学、物理、化学、生物、地理），然后采用该学科最专业的分析框架和术语进行解答。

        ---
        **【第二步：不可违背的教学风格与内容黄金法则】**:
        1.  **聚焦问题**: 你的回答**必须**围绕 `<QUESTION>` 中的问题展开。`<CONTEXT>` 里的视觉信息只是帮助你理解题目的工具，**绝对不能**复述或详细描述视觉信息本身，除非题目明确要求。

        2.  **扮演老师，而非AI**:
            *   **语气**: 必须使用循循善诱、富有亲和力的口吻。多使用“好的，同学，我们一起来分析一下”、“首先，我们要注意到题目的关键点是...”、“接下来，顺着这个思路...”、“你看，顺着这个思路，结论是不是就清晰了？”等引导性、对话式的语言。
            *   **避免AI习语**: 绝对禁止使用“首先，... 其次，... 最后，...”、“综上所述”、“总而言之”等刻板的AI常用语。讲解应该是自然流畅的。
            *   **自信与清晰**: 你是老师，请直接、清晰地展示你的推导过程。绝对不要出现“我算错了”、“这里可能存在误解”等自我怀疑的言论。

        3.  **必须解答到底**:
            *   **完整性**:  **必须**将 `<QUESTION>` 中的每一个子问题都解答到最终的结论。**绝对禁止**只给思路或分析，而不给出最终答案，也不要光回答一部分就结束。
            *   **禁止省略**: 绝对不能以任何理由省略任何关键的推导、计算、论证或史实引用。学生需要看到完整的答案是如何得出的。
            *   你 **必须** 将题目解答到最终的数值答案或明确的证明结论。
            *   **绝对禁止** 以“过程复杂”、“计算繁琐”、“信息不足”或任何其他理由，只提供解题思路而不给出具体计算过程和最终结果。
            *   如果题目真的条件不足，你必须明确指出缺失哪个条件，并尝试用符号表示最终答案。

        4.  **必须展示过程**:
            *   **禁止跳步**: 必须展示每一个关键的推导、化简和计算步骤。绝对不能以“过程复杂”、“计算繁琐”、“证明略”等任何理由，省略任何关键的推导和计算步骤。学生需要看到完整的“心路历程”。
            *   **思路先行**: 在进行关键计算或复杂分析前，先用一两句话点明这一步的“核心思路”或“将要使用的关键公式”或“分析角度”，做到“授人以渔”（例如，对于历史题，可以是“我们先从经济背景入手分析...”；对于数学题，可以是“这里我们要用到的是正弦定理...”）。

        5.  **针对不同学科的解答侧重点**:
        *   **对于【数理化生】**: 重点在于**逻辑的严谨性**和**步骤的完整性**。每一步计算和推导都必须清晰无误。
        *   **对于【文史哲政地】**: 重点在于**论证的充分性**和**知识的广度与深度**。需要旁征博引，结合相关的背景知识、理论框架或史实材料进行多角度分析。
        *   **对于【英语】**: 重点在于**语法的准确性**和**语言的地道性**。如果是翻译或作文，需要给出高质量的译文或范文；如果是语法题，需要详细解释语法规则。
        *   **对于【语文】**: 重点在于**文本的细读**和**思想的深度**。分析诗歌或阅读理解时，要结合上下文，挖掘深层含义和艺术手法。
        
        **【第三步：不可违背的输出格式黄金法则】**:

        1.  **纯文本与LaTeX**: 你的回答只能包含标准的Markdown文本和LaTeX数学公式。**绝对不能**包含任何Python代码或其他代码。
        2.  **LaTeX标准**:
            *   **行内公式**: 必须严格使用 `$...$` 包裹，例如：`$a^2 + b^2 = c^2$`。
            *   **块级公式 (独占一行)**: 必须严格使用 `$$...$$` 包裹。
            *   **标准命令**: 确保使用标准的LaTeX命令，如 `\frac`, `\sqrt`, `\sin`, `\cdot` 等。
            *   所有数学、物理公式和化学方程式，都必须严格使用标准的LaTeX语法。关键步骤用加粗提示。
        **重要**: 你的输出 **绝对不能** 包含 `<INSTRUCTIONS>`, `<DATA>`, `<QUESTION>`, `<CONTEXT>` 这些标签本身。直接开始你的教学讲解。
</INSTRUCTIONS>
    <DATA>
        ---
        **【辅导材料】**
        <QUESTION>
        [学生遇到的题目 - 文字与公式]:
        {cleaned_ocr_text}
        </QUESTION>
        
        <CONTEXT>
        [学生遇到的题目 - 图形信息]:
        {geometry_description}
        </CONTEXT>
    </DATA>
        ---

        好了，全能的认真负责的正确的老师，请开始你最详尽、最负责任的讲解，确保学生能看到每一个步骤和最终的答案。
        """
        system_prompt = """你是一位遵循指令的顶级的、极其负责任的高中全学科老师。你的任务是解析<INSTRUCTIONS>，处理<DATA>，然后生成最终的教学回答。"""
        solution_response = kimi_client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.2,# 降低温度，让逻辑更严谨
            max_tokens=22000
        )
        final_markdown = solution_response.choices[0].message.content
        return PlainTextResponse(content=final_markdown, media_type="text/markdown; charset=utf-8")
    except Exception as e:
        print(f"!!! 发生严重错误 !!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        raise HTTPException(status_code=500, detail=f"处理时发生错误: {str(e)}")
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            
# ==============================================================================
# 完整 main.py - 新增: 批改作业API接口
# ==============================================================================
@app.post("/review")
async def review_from_images(
    question_image: UploadFile = File(...),
    answer_image: UploadFile = File(...)
):
    try:
        initialize_pix2text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"核心OCR服务初始化失败: {e}")

    if not p2t or not kimi_client or not dashscope.api_key:
        raise HTTPException(status_code=500, detail="核心AI服务未就绪")
    
    # 为通义千问API创建临时文件
    temp_q_image_path = f"/tmp/temp_q_{uuid.uuid4()}.png"
    temp_a_image_path = f"/tmp/temp_a_{uuid.uuid4()}.png"

    try:
        # --- 1. 读取两张图片的字节流 ---
        # --- 1. 处理题目图片 ---
        print("\n--- 正在处理【题目】图片... ---")
        q_image_bytes = await question_image.read()
        q_preprocessed = image_preprocess_v2(q_image_bytes)
        question_ocr_text = process_ocr(q_preprocessed) # <<< 调用新函数
        
        # ... (通义千问获取 question_visual_info 的逻辑不变) ...

        
        
        with open(temp_q_image_path, "wb") as f:
            f.write(q_image_bytes)
        
        vision_prompt = "请用简洁的语言描述这张图片中的几何图形信息（顶点、关系、已知条件等），忽略所有文字。"
        q_messages = [{'role': 'user', 'content': [{'text': vision_prompt}, {'image': f'file://{os.path.abspath(temp_q_image_path)}'}]}]
        q_vision_response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=q_messages)
        
        question_visual_info = ""
        if q_vision_response.status_code == 200:
            raw_content_list = q_vision_response.output.choices[0].message.content
            if isinstance(raw_content_list, list):
                for part in raw_content_list:
                    if part.get("text"):
                        question_visual_info = part["text"]
                        break
            elif isinstance(raw_content_list, str):
                question_visual_info = raw_content_list
        
        print(f"--- 题目OCR文本: {question_ocr_text[:80].strip()}...")
        print(f"--- 题目视觉信息: {question_visual_info[:80].strip()}...")

        # --- 3. 对【答案图片】进行双路信息提取 ---
        print("\n--- 正在处理【答案】图片... ---")

        a_image_bytes = await answer_image.read()
        a_preprocessed = image_preprocess_v2(a_image_bytes)
        answer_ocr_text = process_ocr(a_preprocessed) # <<< 再次调用新函数


        with open(temp_a_image_path, "wb") as f:
            f.write(a_image_bytes)
            
        a_messages = [{'role': 'user', 'content': [{'text': vision_prompt}, {'image': f'file://{os.path.abspath(temp_a_image_path)}'}]}]
        a_vision_response = dashscope.MultiModalConversation.call(model='qwen-vl-max', messages=a_messages)
        
        answer_visual_info = ""
        if a_vision_response.status_code == 200:
            raw_content_list = a_vision_response.output.choices[0].message.content
            if isinstance(raw_content_list, list):
                for part in raw_content_list:
                    if part.get("text"):
                        answer_visual_info = part["text"]
                        break
            elif isinstance(raw_content_list, str):
                answer_visual_info = raw_content_list
        
        print(f"--- 学生答案OCR文本: {answer_ocr_text[:80].strip()}...")
        print(f"--- 学生答案视觉信息: {answer_visual_info[:80].strip()}...")

        # --- 4. 构造【批改模式】的终极Prompt ---
        print("\n--- 正在构造批改Prompt... ---")
        review_prompt = f"""
        **角色**: 你是一位极其专业、富有经验且鼓励性的批改老师。你的任务是仔细比对“标准题目”和“学生答案”，给出一份全面、有建设性的批改报告。

        **核心任务**:
        1.  **判断对错**: 首先，明确判断学生的最终答案是否正确。
        2.  **分析过程**: 逐一分析学生答案中的解题步骤。

        **【批改报告黄金法则】**:

        1.  **如果答案正确**:
            *   **明确表扬**: 首先要用积极、鼓励的语言肯定学生的成果，例如：“非常棒！你的答案是完全正确的，解题思路也很清晰！”
            *   **点出亮点**: 指出学生做得好的地方，例如：“特别欣赏你在这里使用了配方法，非常巧妙。”
            *   **提供优化建议**: 在肯定的基础上，提出可以优化的地方，例如：“如果这里能多一步关于定义域的讨论，那就更完美了。”或者“其实还有另一种更简洁的方法，你想了解一下吗？”

        2.  **如果答案错误**:
            *   **先肯定，后指正**: 不要直接否定。先找到学生做得对的部分并予以肯定，例如：“同学你好，你对正弦定理的理解和应用非常到位，这是一个很好的开始！”
            *   **精准定位错误**: 明确指出学生**第一个**出错的步骤，并解释**为什么**错了。例如：“问题出在第二步的化简上，这里应该同乘以`2a`而不是`a`，因为...”
            *   **给出正确示范**: 在指出错误后，给出从错误点开始的、正确的解题步骤和最终答案。
            *   **鼓励结尾**: 用鼓励的话语结束，例如：“这只是一个小的疏忽，下次注意就好。你已经很接近正确答案了，加油！”

        3.  **格式要求**:
            *   使用清晰的Markdown格式，可以用“✅ 亮点解析”、“❌ 错误分析”、“💡 优化建议”等标题来组织报告。
            *   所有数学公式必须使用标准的LaTeX语法。

        ---
        **【批改材料】**

        <QUESTION_DATA>
            <OCR_TEXT>{question_ocr_text}</OCR_TEXT>
            <VISUAL_INFO>{question_visual_info}</VISUAL_INFO>
        </QUESTION_DATA>

        <STUDENT_ANSWER_DATA>
            <OCR_TEXT>{answer_ocr_text}</OCR_TEXT>
            <VISUAL_INFO>{answer_visual_info}</VISUAL_INFO>
        </STUDENT_ANSWER_DATA>
        """

        # --- 5. 调用Kimi API并返回结果 ---
        print("\n--- 正在调用Kimi生成批改报告... ---")
        system_prompt_review = "你是一位负责批改作业、并提供高质量、鼓励性反馈的辅导老师。"
        
        solution_response = kimi_client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=[
                {"role": "system", "content": system_prompt_review},
                {"role": "user", "content": review_prompt}
            ],
            temperature=0.5,
            max_tokens=8192
        )
        final_markdown = solution_response.choices[0].message.content
        
        return {"solution": final_markdown}

    except Exception as e:
        print(f"!!! 发生严重错误 !!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        raise HTTPException(status_code=500, detail=f"处理时发生错误: {str(e)}")
    finally:
        if os.path.exists(temp_q_image_path): os.remove(temp_q_image_path)
        if os.path.exists(temp_a_image_path): os.remove(temp_a_image_path)