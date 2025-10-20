# ==============================================================================
# image_enhancer.py - 专业级图像增强模块
# 功能：对上传的图片进行智能画质优化，提升OCR识别准确率
# 技术：反锐化掩模 (Unsharp Masking) + CLAHE对比度增强
# 版本：V1.0
# ==============================================================================

import cv2
import numpy as np
from PIL import Image
from typing import Optional


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """
    将Pillow Image对象转换为OpenCV的numpy ndarray格式（BGR色彩空间）
    
    Args:
        pil_img: PIL.Image对象
        
    Returns:
        cv_img: OpenCV格式的numpy数组（BGR色彩空间）
    """
    # 确保图像是RGB模式
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    
    # PIL使用RGB，OpenCV使用BGR，需要转换
    # 先转为numpy数组（RGB）
    img_array = np.array(pil_img)
    
    # RGB → BGR（OpenCV格式）
    cv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    return cv_img


def cv2_to_pil(cv_img: np.ndarray) -> Image.Image:
    """
    将OpenCV的numpy数组转换回Pillow Image对象
    
    Args:
        cv_img: OpenCV格式的numpy数组（BGR色彩空间）
        
    Returns:
        pil_img: PIL.Image对象
    """
    # BGR → RGB
    rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    
    # numpy数组 → PIL Image
    pil_img = Image.fromarray(rgb_img)
    
    return pil_img


def sharpen_image(cv_img: np.ndarray, kernel_size: int = 5, sigma: float = 1.0, 
                  amount: float = 1.5, threshold: int = 0) -> np.ndarray:
    """
    使用反锐化掩模（Unsharp Masking）算法对图像进行锐化处理
    
    原理：
    1. 对原图进行高斯模糊得到模糊版本
    2. 原图减去模糊版本得到高频细节（边缘）
    3. 将高频细节按比例叠加回原图，增强边缘
    
    Args:
        cv_img: 输入图像（BGR格式）
        kernel_size: 高斯模糊核大小（奇数），越大模糊越强
        sigma: 高斯核标准差，控制模糊程度
        amount: 锐化强度，1.0-2.0为佳，越大越锐
        threshold: 阈值，只锐化差异超过此值的像素（降噪用）
        
    Returns:
        sharpened: 锐化后的图像
    """
    print(f"[图像增强] 正在进行锐化处理... (kernel_size={kernel_size}, amount={amount})")
    
    # 步骤1：创建模糊版本
    blurred = cv2.GaussianBlur(cv_img, (kernel_size, kernel_size), sigma)
    
    # 步骤2：计算高频细节（原图 - 模糊图）
    # 使用float类型避免溢出
    high_freq = cv_img.astype(np.float32) - blurred.astype(np.float32)
    
    # 步骤3：将高频细节按比例叠加回原图
    # sharpened = original + amount * high_freq
    sharpened = cv_img.astype(np.float32) + amount * high_freq
    
    # 步骤4：应用阈值（可选，用于降噪）
    if threshold > 0:
        # 只保留差异超过阈值的增强
        mask = np.abs(high_freq) > threshold
        sharpened = np.where(mask, sharpened, cv_img.astype(np.float32))
    
    # 步骤5：裁剪到有效范围[0, 255]并转换回uint8
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    
    print("[图像增强] ✓ 锐化处理完成")
    return sharpened


def enhance_contrast_clahe(cv_img: np.ndarray, clip_limit: float = 2.0, 
                           tile_grid_size: tuple = (8, 8)) -> np.ndarray:
    """
    使用CLAHE（对比度受限自适应直方图均衡化）增强图像对比度
    
    原理：
    CLAHE是传统直方图均衡化的改进版本，它将图像分成小块（tiles），
    在每个小块内独立进行对比度增强，并使用双线性插值平滑边界。
    对比度限制（clip_limit）防止过度增强导致噪声放大。
    
    为什么用LAB色彩空间？
    - L通道：亮度信息，独立于颜色
    - A/B通道：色彩信息
    - 只对L通道增强，保持色彩不失真
    
    Args:
        cv_img: 输入图像（BGR格式）
        clip_limit: 对比度限制因子，1.0-4.0为佳，越大对比度越强
        tile_grid_size: 分块大小，如(8,8)表示将图像分成8x8个小块
        
    Returns:
        enhanced: 对比度增强后的图像（BGR格式）
    """
    print(f"[图像增强] 正在进行CLAHE对比度增强... (clip_limit={clip_limit}, tile_grid={tile_grid_size})")
    
    # 步骤1：BGR → LAB色彩空间
    # LAB空间中L通道表示亮度，与色彩信息解耦
    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    
    # 步骤2：分离LAB三个通道
    l_channel, a_channel, b_channel = cv2.split(lab)
    
    # 步骤3：创建CLAHE对象
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    
    # 步骤4：只对L（亮度）通道应用CLAHE
    l_channel_clahe = clahe.apply(l_channel)
    
    # 步骤5：合并增强后的L通道与原始的A、B通道
    lab_enhanced = cv2.merge([l_channel_clahe, a_channel, b_channel])
    
    # 步骤6：LAB → BGR，转换回原始色彩空间
    enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    
    print("[图像增强] ✓ CLAHE对比度增强完成")
    return enhanced


def advanced_image_processing_pipeline(pil_img: Image.Image, 
                                      sharpen_amount: float = 1.5,
                                      clahe_clip_limit: float = 2.0) -> Image.Image:
    """
    高级图像处理流水线（总入口函数）
    
    处理流程：
    1. Pillow Image → OpenCV numpy数组
    2. 反锐化掩模锐化（增强边缘和文字清晰度）
    3. CLAHE对比度增强（改善光照不均和对比度不足）
    4. OpenCV numpy数组 → Pillow Image
    
    Args:
        pil_img: 输入的Pillow Image对象
        sharpen_amount: 锐化强度（1.0-2.0），默认1.5
        clahe_clip_limit: CLAHE对比度限制（1.0-4.0），默认2.0
        
    Returns:
        enhanced_pil_img: 增强后的Pillow Image对象
    """
    print("\n" + "="*70)
    print("【图像增强流水线】开始处理")
    print("="*70)
    
    try:
        # 步骤1：格式转换 PIL → OpenCV
        print("[图像增强] 步骤1: 转换图像格式 (PIL → OpenCV)")
        cv_img = pil_to_cv2(pil_img)
        print(f"[图像增强] ✓ 图像尺寸: {cv_img.shape[1]}x{cv_img.shape[0]}, 色彩通道: {cv_img.shape[2]}")
        
        # 步骤2：锐化处理
        print("[图像增强] 步骤2: 应用反锐化掩模")
        sharpened_img = sharpen_image(cv_img, amount=sharpen_amount)
        
        # 步骤3：对比度增强
        print("[图像增强] 步骤3: 应用CLAHE对比度增强")
        enhanced_img = enhance_contrast_clahe(sharpened_img, clip_limit=clahe_clip_limit)
        
        # 步骤4：格式转换 OpenCV → PIL
        print("[图像增强] 步骤4: 转换图像格式 (OpenCV → PIL)")
        enhanced_pil_img = cv2_to_pil(enhanced_img)
        
        print("="*70)
        print("【图像增强流水线】✅ 处理完成！")
        print("="*70 + "\n")
        
        return enhanced_pil_img
        
    except Exception as e:
        print(f"!!! [图像增强] 处理过程中发生错误: {e}")
        print(f"!!! [图像增强] 返回原始图像作为降级方案")
        print("="*70 + "\n")
        return pil_img


# ==============================================================================
# 可选：独立测试函数（开发调试用）
# ==============================================================================
def test_enhancer(image_path: str, output_path: str = "enhanced_output.png"):
    """
    独立测试函数，用于开发时验证图像增强效果
    
    使用方法：
    python image_enhancer.py
    
    Args:
        image_path: 输入图像路径
        output_path: 输出图像路径
    """
    print(f"🔍 测试模式：读取图像 {image_path}")
    
    # 读取图像
    pil_img = Image.open(image_path)
    print(f"原始图像尺寸: {pil_img.size}, 模式: {pil_img.mode}")
    
    # 应用增强流水线
    enhanced_img = advanced_image_processing_pipeline(pil_img)
    
    # 保存结果
    enhanced_img.save(output_path)
    print(f"✅ 增强后的图像已保存到: {output_path}")
    
    # 显示对比（可选，需要matplotlib）
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        ax1.imshow(pil_img)
        ax1.set_title("原始图像")
        ax1.axis('off')
        
        ax2.imshow(enhanced_img)
        ax2.set_title("增强后图像")
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig("comparison.png")
        print("✅ 对比图已保存到: comparison.png")
        
    except ImportError:
        print("ℹ️ 未安装matplotlib，跳过对比图生成")


if __name__ == "__main__":
    # 如果直接运行此文件，执行测试
    import sys
    
    if len(sys.argv) > 1:
        test_image_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "enhanced_output.png"
        test_enhancer(test_image_path, output_path)
    else:
        print("📖 使用方法:")
        print("  python image_enhancer.py <输入图像路径> [输出图像路径]")
        print("\n示例:")
        print("  python image_enhancer.py test_image.png enhanced_test.png")

