# ==============================================================================
# image_enhancer.py - 【V23.0 高级图像增强模块】
# 功能：对抗模糊、光照不均、污渍等问题，提升OCR识别精度
# ==============================================================================

import cv2
import numpy as np
from PIL import Image


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """将PIL Image对象转换为OpenCV格式 (BGR)"""
    # 确保是RGB模式
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv_img: np.ndarray) -> Image.Image:
    """将OpenCV格式 (BGR) 转换为PIL Image对象"""
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def sharpen_image(cv_img: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    使用反锐化掩模增强图片清晰度，对抗模糊。
    原理：原图 + (原图 - 模糊图) = 锐化效果
    
    【V24.1优化】添加强度参数，避免过度锐化
    
    参数:
        cv_img: 输入图像
        strength: 锐化强度 (0.0-2.0)，默认1.0为温和模式
    """
    print(f"[图像增强] → 应用锐化处理（强度: {strength}）...")
    blurred = cv2.GaussianBlur(cv_img, (0, 0), 3)
    # 降低默认锐化强度：从1.5降低到1.2
    alpha = 1.0 + (0.2 * strength)  # 1.0-1.4的范围
    beta = -0.2 * strength           # -0.0到-0.4的范围
    sharpened = cv2.addWeighted(cv_img, alpha, blurred, beta, 0)
    print("[图像增强] ✓ 锐化完成")
    return sharpened


def enhance_contrast_clahe(cv_img: np.ndarray) -> np.ndarray:
    """
    使用CLAHE (Contrast Limited Adaptive Histogram Equalization) 
    处理光照不均和对比度不足的问题。
    
    CLAHE的优势：
    - 局部自适应：不会像全局直方图均衡化那样导致过度增强
    - 对光照不均特别有效
    - 保留细节的同时提升对比度
    """
    print("[图像增强] → 应用CLAHE对比度增强...")
    
    # 将 BGR 图像转换为 LAB 色彩空间
    # LAB空间将亮度(L)和色彩(A,B)分离，便于单独处理亮度
    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # 对 L (亮度) 通道应用 CLAHE
    # clipLimit: 对比度限制，防止过度增强
    # tileGridSize: 分块大小，(8,8)适合文档图片
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # 合并通道并转换回 BGR
    limg = cv2.merge((cl, a, b))
    final_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    
    print("[图像增强] ✓ CLAHE增强完成")
    return final_img


def denoise_image(cv_img: np.ndarray, h: int = 6) -> np.ndarray:
    """
    使用非局部均值去噪算法去除噪声和轻微污渍。
    
    【V24.1优化】降低去噪强度，避免丢失细节
    
    fastNlMeansDenoisingColored的优势：
    - 保留边缘细节的同时去除噪声
    - 对彩色图像效果好
    - 可以去除轻微的污渍和斑点
    
    参数:
        cv_img: 输入图像
        h: 滤波强度 (3-15)，值越大去噪越强，默认6（温和）
    """
    print(f"[图像增强] → 应用去噪处理（强度: {h}）...")
    # 【V24.1】从h=10降低到h=6，更温和的去噪
    denoised = cv2.fastNlMeansDenoisingColored(cv_img, None, h, h, 7, 21)
    print("[图像增强] ✓ 去噪完成")
    return denoised


def adaptive_binarization(cv_img: np.ndarray) -> np.ndarray:
    """
    自适应二值化，对抗复杂背景和光照变化。
    可选的额外增强手段，适合极端情况。
    """
    print("[图像增强] → 应用自适应二值化...")
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 2
    )
    # 转回BGR以保持一致性
    binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    print("[图像增强] ✓ 二值化完成")
    return binary_bgr


def advanced_image_processing_pipeline(pil_img: Image.Image, mode: str = 'light') -> Image.Image:
    """
    一个集成了多种增强技术的高级图像预处理流水线。
    
    【V24.1重大优化】
    - 新增'light'和'none'模式，避免过度处理
    - 降低各级别的处理强度
    - 默认改为'light'轻量模式
    
    参数:
        pil_img: PIL格式的输入图像
        mode: 处理模式
            - 'none': 无处理，直接返回原图（推荐清晰图片）
            - 'light': 轻量模式，仅CLAHE对比度增强（新默认，推荐）
            - 'standard': 标准模式（温和锐化 + CLAHE）
            - 'aggressive': 激进模式（去噪 + 锐化 + CLAHE），适合严重模糊的图片
            - 'binary': 二值化模式，适合极端光照条件
    
    返回:
        PIL格式的增强后图像
    """
    print(f"\n{'='*60}")
    print(f"[图像增强] 🚀 启动图像预处理流水线 (模式: {mode})")
    print(f"{'='*60}")
    
    # 【V24.1新增】无处理模式
    if mode == 'none':
        print("[图像增强] ✓ 跳过处理，返回原图")
        print(f"{'='*60}\n")
        return pil_img
    
    # 1. 转换为OpenCV格式
    cv_img = pil_to_cv2(pil_img)
    original_shape = cv_img.shape
    print(f"[图像增强] ✓ 格式转换完成 | 原始尺寸: {original_shape[1]}x{original_shape[0]}")
    
    # 2. 根据模式选择处理流程
    if mode == 'binary':
        # 二值化模式：适合极端情况
        enhanced_img = adaptive_binarization(cv_img)
        
    elif mode == 'aggressive':
        # 激进模式：去噪 + 锐化 + CLAHE
        denoised_img = denoise_image(cv_img, h=8)  # 中等去噪
        sharpened_img = sharpen_image(denoised_img, strength=1.5)  # 较强锐化
        enhanced_img = enhance_contrast_clahe(sharpened_img)
        
    elif mode == 'standard':
        # 标准模式：温和锐化 + CLAHE
        sharpened_img = sharpen_image(cv_img, strength=1.0)  # 温和锐化
        enhanced_img = enhance_contrast_clahe(sharpened_img)
    
    else:  # 'light' 新默认模式
        # 【V24.1新增】轻量模式：仅CLAHE，不锐化不去噪
        print("[图像增强] → 轻量模式：仅对比度增强...")
        enhanced_img = enhance_contrast_clahe(cv_img)
    
    # 3. 转换回PIL格式并返回
    final_pil_img = cv2_to_pil(enhanced_img)
    
    print(f"{'='*60}")
    print(f"[图像增强] ✅ 预处理流水线完成！")
    print(f"{'='*60}\n")
    
    return final_pil_img


# 快捷函数：针对不同场景
def enhance_for_ocr_standard(pil_img: Image.Image) -> Image.Image:
    """标准增强：适合普通拍照题目"""
    return advanced_image_processing_pipeline(pil_img, mode='standard')


def enhance_for_ocr_aggressive(pil_img: Image.Image) -> Image.Image:
    """激进增强：适合模糊/污损严重的题目"""
    return advanced_image_processing_pipeline(pil_img, mode='aggressive')


def enhance_for_ocr_binary(pil_img: Image.Image) -> Image.Image:
    """二值化增强：适合极端光照条件"""
    return advanced_image_processing_pipeline(pil_img, mode='binary')

