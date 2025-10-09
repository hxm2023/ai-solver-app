# ==============================================================================
# question_splitter.py - 【V24.2 结构化布局分析版】
# 核心策略：从"像素聚合"到"结构化布局分析"
# 三步走：强力聚合 → 题号检测 → 精细归属
# ==============================================================================

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple
import re


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """将PIL Image对象转换为OpenCV格式 (BGR)"""
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv_img: np.ndarray) -> Image.Image:
    """将OpenCV格式 (BGR) 转换为PIL Image对象"""
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


# ==============================================================================
# 第一步：强力区块聚合
# ==============================================================================

def coarse_graining(binary: np.ndarray, img_width: int, img_height: int, 
                    min_question_height: int = 50) -> List[Tuple[int, int, int, int]]:
    """
    【V24.2 - 步骤1】强力区块聚合 (Coarse Graining)
    
    策略：宁可错分到一起，也不要拆开
    - 使用大范围的水平膨胀，强制连接同一行的所有元素
    - 使用适度的垂直膨胀，连接垂直相邻的内容
    - 得到几个大的"候选区块"，每个可能包含1-N道题
    
    参数:
        binary: 二值化图像
        img_width, img_height: 图片尺寸
        min_question_height: 最小题目高度
    
    返回:
        粗粒度区块列表 [(x, y, w, h), ...]
    """
    print(f"\n[步骤1/3] 🔥 强力区块聚合...")
    
    # 1.1 强力水平膨胀 - 连接同一行的所有元素
    # 使用一个非常宽的水平核（100像素宽）
    horizontal_kernel = np.ones((1, 100), np.uint8)
    dilated_h = cv2.dilate(binary, horizontal_kernel, iterations=2)
    print(f"  ✓ 水平膨胀完成（核大小: 1x100, 迭代2次）")
    
    # 1.2 适度垂直膨胀 - 连接垂直相邻的段落
    # 使用一个较窄的垂直核（10像素高）
    vertical_kernel = np.ones((10, 1), np.uint8)
    dilated_full = cv2.dilate(dilated_h, vertical_kernel, iterations=3)
    print(f"  ✓ 垂直膨胀完成（核大小: 10x1, 迭代3次）")
    
    # 1.3 检测轮廓，得到大的候选区块
    contours, _ = cv2.findContours(dilated_full, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"  ✓ 检测到 {len(contours)} 个轮廓")
    
    # 1.4 过滤，保留有效的候选区块
    coarse_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # 宽松的过滤条件：宽度>20%，高度>最小值
        if w > img_width * 0.2 and h > min_question_height:
            coarse_boxes.append((x, y, w, h))
    
    coarse_boxes.sort(key=lambda b: b[1])  # 从上到下排序
    
    print(f"  ✓ 过滤后保留 {len(coarse_boxes)} 个粗粒度区块")
    print(f"[步骤1/3] ✅ 强力聚合完成\n")
    
    return coarse_boxes


# ==============================================================================
# 第二步：结构化分析与题号检测
# ==============================================================================

def find_all_text_blocks(binary: np.ndarray, min_area: int = 50) -> List[Tuple[int, int, int, int]]:
    """
    【V24.2 - 步骤2辅助】在原始二值图上找到所有细粒度的文本块
    
    这些文本块是最小的单元，后续会将它们聚类到题目中
    """
    # 使用小的膨胀连接单个单词内的字符
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 3))
    dilated = cv2.dilate(binary, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    blocks = []
    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            blocks.append(cv2.boundingRect(contour))
    
    return blocks


def detect_question_number_candidates(binary: np.ndarray, img_width: int, 
                                      coarse_boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int]]:
    """
    【V24.2 - 步骤2】检测题号候选位置
    
    策略：
    1. 在每个粗粒度区块的左侧区域寻找小的、类似题号的轮廓
    2. 使用启发式规则判断（位置、尺寸、形状）
    3. 不依赖OCR，仅用几何特征
    
    返回:
        题号候选位置列表 [(x, y), ...]，按y坐标排序
    """
    print(f"[步骤2/3] 🔍 检测题号锚点...")
    
    # 使用温和膨胀找到小的文本块
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 启发式规则1：位于页面左侧（左20%区域）
        if x > img_width * 0.2:
            continue
        
        # 启发式规则2：尺寸合理（题号通常不会太大）
        if w > 150 or h > 100 or w < 10 or h < 10:
            continue
        
        # 启发式规则3：宽高比合理（题号通常是小方块或略宽）
        aspect_ratio = w / h if h > 0 else 0
        if aspect_ratio > 5 or aspect_ratio < 0.2:
            continue
        
        # 启发式规则4：必须在某个粗粒度区块内
        is_in_coarse = any(
            cb[0] <= x < cb[0] + cb[2] and cb[1] <= y < cb[1] + cb[3]
            for cb in coarse_boxes
        )
        if not is_in_coarse:
            continue
        
        candidates.append((x, y))
    
    # 按y坐标排序，去重（相近的y坐标只保留一个）
    candidates.sort(key=lambda c: c[1])
    
    # 去重：如果两个候选位置的y坐标相差小于30像素，只保留第一个
    deduplicated = []
    for i, (x, y) in enumerate(candidates):
        if i == 0 or y - deduplicated[-1][1] > 30:
            deduplicated.append((x, y))
    
    print(f"  ✓ 检测到 {len(deduplicated)} 个题号锚点候选位置")
    print(f"[步骤2/3] ✅ 题号检测完成\n")
    
    return deduplicated


# ==============================================================================
# 第三步：基于锚点的精细化分割
# ==============================================================================

def segment_by_anchors(binary: np.ndarray, 
                      all_blocks: List[Tuple[int, int, int, int]],
                      anchor_points: List[Tuple[int, int]],
                      img_width: int, img_height: int) -> List[Tuple[int, int, int, int]]:
    """
    【V24.2 - 步骤3】基于题号锚点进行精细化分割
    
    策略：
    1. 以每个题号的y坐标为起点
    2. 到下一个题号的y坐标为终点（或图片底部）
    3. 在这个垂直范围内，找到所有内容的最小外接矩形
    
    参数:
        binary: 二值图
        all_blocks: 所有细粒度文本块
        anchor_points: 题号锚点位置
        img_width, img_height: 图片尺寸
    
    返回:
        精细化的题目框列表
    """
    print(f"[步骤3/3] ✂️ 基于锚点精细化分割...")
    
    if not anchor_points:
        print(f"  ⚠️ 无题号锚点，退化为全图单题")
        if not all_blocks:
            return [(0, 0, img_width, img_height)]
        
        # 计算所有文本块的联合边界框
        x_coords = [b[0] for b in all_blocks]
        y_coords = [b[1] for b in all_blocks]
        x2_coords = [b[0] + b[2] for b in all_blocks]
        y2_coords = [b[1] + b[3] for b in all_blocks]
        
        min_x = max(0, min(x_coords) - 20)
        min_y = max(0, min(y_coords) - 20)
        max_x = min(img_width, max(x2_coords) + 20)
        max_y = min(img_height, max(y2_coords) + 20)
        
        return [(min_x, min_y, max_x - min_x, max_y - min_y)]
    
    final_boxes = []
    
    for i, (anchor_x, anchor_y) in enumerate(anchor_points):
        # 确定当前题目的垂直范围
        y_start = anchor_y
        y_end = anchor_points[i + 1][1] if i + 1 < len(anchor_points) else img_height
        
        # 在垂直范围内裁剪图像
        strip = binary[y_start:y_end, :]
        
        # 找到这个条带内的所有内容
        strip_contours, _ = cv2.findContours(strip, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not strip_contours:
            continue
        
        # 计算所有轮廓的联合边界框
        min_x = img_width
        max_x = 0
        min_y_relative = strip.shape[0]
        max_y_relative = 0
        
        for contour in strip_contours:
            x, y, w, h = cv2.boundingRect(contour)
            min_x = min(min_x, x)
            max_x = max(max_x, x + w)
            min_y_relative = min(min_y_relative, y)
            max_y_relative = max(max_y_relative, y + h)
        
        # 转换为绝对坐标，添加padding
        padding = 20
        box_x = max(0, min_x - padding)
        box_y = max(0, y_start + min_y_relative - padding)
        box_w = min(img_width - box_x, max_x - min_x + 2 * padding)
        box_h = min(img_height - box_y, max_y_relative - min_y_relative + 2 * padding)
        
        final_boxes.append((box_x, box_y, box_w, box_h))
    
    print(f"  ✓ 基于 {len(anchor_points)} 个锚点生成了 {len(final_boxes)} 个题目框")
    print(f"[步骤3/3] ✅ 精细化分割完成\n")
    
    return final_boxes


# ==============================================================================
# 后处理：保守合并
# ==============================================================================

def conservative_merge(boxes: List[Tuple[int, int, int, int]], 
                       img_height: int, 
                       max_gap: int = None) -> List[Tuple[int, int, int, int]]:
    """
    【V24.2 - 后处理】保守的最终合并
    
    只合并那些垂直间距非常小（<2%图片高度）且有水平重叠的框
    """
    if not boxes or len(boxes) <= 1:
        return boxes
    
    if max_gap is None:
        max_gap = int(img_height * 0.02)  # 默认2%
    
    boxes.sort(key=lambda b: b[1])
    merged = []
    current = list(boxes[0])
    
    for next_box in boxes[1:]:
        gap = next_box[1] - (current[1] + current[3])
        
        # 计算水平重叠
        h_overlap = max(0, min(current[0] + current[2], next_box[0] + next_box[2]) - 
                       max(current[0], next_box[0]))
        
        if gap < max_gap and h_overlap > 0:
            # 合并
            new_x = min(current[0], next_box[0])
            new_y = min(current[1], next_box[1])
            new_x2 = max(current[0] + current[2], next_box[0] + next_box[2])
            new_y2 = max(current[1] + current[3], next_box[1] + next_box[3])
            
            current = [new_x, new_y, new_x2 - new_x, new_y2 - new_y]
        else:
            merged.append(tuple(current))
            current = list(next_box)
    
    merged.append(tuple(current))
    return merged


# ==============================================================================
# 主函数：整合三步走策略
# ==============================================================================

def find_question_boxes(image: Image.Image, 
                       min_question_height: int = 50,
                       use_anchor_based: bool = True) -> List[Tuple[int, int, int, int]]:
    """
    【V24.2 结构化布局分析版】
    
    核心策略：
    1. 强力区块聚合 - 宁可合错，不可拆散
    2. 题号锚点检测 - 找到题目的"重心"
    3. 精细化分割 - 基于锚点归属内容
    
    参数:
        image: PIL格式输入图像
        min_question_height: 最小题目高度
        use_anchor_based: 是否使用基于锚点的精细分割
    
    返回:
        题目边界框列表 [(x, y, w, h), ...]
    """
    print(f"\n{'='*80}")
    print(f"[题目分割器 V24.2] 🚀 结构化布局分析开始...")
    print(f"{'='*80}\n")
    
    # ===== 准备工作 =====
    cv_image = pil_to_cv2(image)
    img_height, img_width = cv_image.shape[:2]
    print(f"📐 图片尺寸: {img_width}x{img_height}")
    
    # 灰度化
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    
    # 自适应二值化
    binary = cv2.adaptiveThreshold(
        ~gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        15, -10
    )
    print(f"✓ 预处理完成（灰度化 + 二值化）\n")
    
    # ===== 步骤1: 强力区块聚合 =====
    coarse_boxes = coarse_graining(binary, img_width, img_height, min_question_height)
    
    # 如果没有找到粗粒度区块，整张图作为一题
    if not coarse_boxes:
        print(f"⚠️ 未检测到有效区块，返回全图")
        return [(0, 0, img_width, img_height)]
    
    # 如果只有一个粗粒度区块，可能就是一道题
    if len(coarse_boxes) == 1 and not use_anchor_based:
        print(f"ℹ️ 仅一个区块且未启用锚点分割，直接返回")
        return coarse_boxes
    
    # ===== 步骤2: 题号锚点检测 =====
    anchor_points = detect_question_number_candidates(binary, img_width, coarse_boxes)
    
    # ===== 步骤3: 基于锚点的精细化分割 =====
    if use_anchor_based and anchor_points:
        all_text_blocks = find_all_text_blocks(binary)
        print(f"📝 检测到 {len(all_text_blocks)} 个细粒度文本块\n")
        
        final_boxes = segment_by_anchors(binary, all_text_blocks, anchor_points, 
                                         img_width, img_height)
    else:
        print(f"ℹ️ 跳过锚点分割，使用粗粒度区块\n")
        final_boxes = coarse_boxes
    
    # ===== 后处理: 保守合并 =====
    if len(final_boxes) > 1:
        before_merge = len(final_boxes)
        final_boxes = conservative_merge(final_boxes, img_height)
        print(f"🔗 保守合并: {before_merge} → {len(final_boxes)} 个题目框\n")
    
    # ===== 排序并返回 =====
    final_boxes.sort(key=lambda b: b[1])
    
    print(f"{'='*80}")
    print(f"✅ [题目分割器 V24.2] 最终检测到 {len(final_boxes)} 个题目区域")
    print(f"{'='*80}\n")
    
    return final_boxes


# ==============================================================================
# 可视化调试
# ==============================================================================

def visualize_detected_boxes(image: Image.Image, 
                            boxes: List[Tuple[int, int, int, int]], 
                            output_path: str = "debug_boxes.png",
                            show_labels: bool = True):
    """
    【V24.2】可视化调试：绘制检测到的边界框
    """
    cv_image = pil_to_cv2(image)
    
    for i, (x, y, w, h) in enumerate(boxes):
        # 绘制矩形
        color = (0, 255, 0) if i % 2 == 0 else (0, 200, 255)  # 交替颜色
        cv2.rectangle(cv_image, (x, y), (x + w, y + h), color, 4)
        
        if show_labels:
            # 绘制题号标签
            label = f"Q{i+1}"
            font_scale = 1.2
            thickness = 3
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            
            # 白色背景
            cv2.rectangle(cv_image, (x + 10, y + 10), (x + tw + 30, y + th + 30), (255, 255, 255), -1)
            # 红色文字
            cv2.putText(cv_image, label, (x + 20, y + th + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
    
    # 添加标题
    title = f"V24.2: {len(boxes)} Questions Detected"
    cv2.putText(cv_image, title, (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
    cv2.putText(cv_image, title, (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    
    cv2.imwrite(output_path, cv_image)
    print(f"📸 [调试] 可视化图片已保存: {output_path}")

