# ==============================================================================
# question_splitter.py - 【V24.0 题目自动分割模块】
# 功能：使用OpenCV计算机视觉技术检测图片中的多个题目区域并分割
# ==============================================================================

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """将PIL Image对象转换为OpenCV格式 (BGR)"""
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def find_question_boxes(image: Image.Image, min_question_height: int = 50, use_projection: bool = True) -> List[Tuple[int, int, int, int]]:
    """
    在图片中检测并返回每道题目的边界框 (bounding boxes)。
    
    【V24.1优化】改进紧密排列题目的识别能力
    
    算法流程：
    1. 图像预处理（灰度化、二值化）
    2. 【新增】水平投影分割法（针对紧密排列）
    3. 形态学操作（膨胀）连接文本区域
    4. 轮廓检测找到独立区块
    5. 智能过滤和合并
    6. 从上到下排序
    
    参数:
        image: PIL格式的输入图像
        min_question_height: 最小题目高度（像素），用于过滤噪点
        use_projection: 是否使用水平投影辅助分割（针对紧密题目）
    
    返回:
        一个元组列表，每个元组代表一个题目的 (x, y, w, h) 坐标。
        列表按从上到下的顺序排序。
    """
    print(f"\n{'='*70}")
    print(f"[题目分割器] 🔍 开始智能检测题目区域...")
    print(f"{'='*70}")
    
    cv_image = pil_to_cv2(image)
    img_height, img_width = cv_image.shape[:2]
    print(f"[题目分割器] 图片尺寸: {img_width}x{img_height}")
    
    # 1. 图像预处理 - 转灰度
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    print("[题目分割器] ✓ 灰度化完成")
    
    # 2. 自适应二值化 - 对抗光照不均
    binary = cv2.adaptiveThreshold(
        ~gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        15,
        -10
    )
    print("[题目分割器] ✓ 自适应二值化完成")
    
    # 【V24.1新增】3. 水平投影分割法 - 针对紧密排列题目
    projection_split_lines = []
    if use_projection:
        projection_split_lines = find_split_lines_by_projection(binary, img_height, min_gap=20)
        print(f"[题目分割器] ✓ 水平投影检测到 {len(projection_split_lines)} 个潜在分割线")
    
    # 4. 形态学膨胀操作 - 减少膨胀强度，避免过度连接
    # 【V24.1优化】降低膨胀迭代次数
    kernel_horizontal = np.ones((2, 10), np.uint8)  # 从(3,15)降低到(2,10)
    kernel_vertical = np.ones((3, 2), np.uint8)     # 从(5,3)降低到(3,2)
    
    dilated = cv2.dilate(binary, kernel_horizontal, iterations=1)  # 从2降低到1
    dilated = cv2.dilate(dilated, kernel_vertical, iterations=2)    # 从3降低到2
    print("[题目分割器] ✓ 形态学膨胀完成（温和模式）")
    
    # 5. 寻找轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"[题目分割器] ✓ 检测到 {len(contours)} 个原始轮廓")
    
    # 6. 过滤轮廓，提取有效的题目框
    raw_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 【V24.1优化】放宽过滤条件，避免遗漏
        # 宽度：从20%降低到15%，捕获更多题目
        # 高度：从固定值改为动态（图片高度的3%）
        min_h = max(min_question_height, int(img_height * 0.03))
        if (img_width * 0.15 < w < img_width * 0.98) and (min_h < h < img_height * 0.85):
            raw_boxes.append((x, y, w, h))
    
    print(f"[题目分割器] ✓ 初步过滤后保留 {len(raw_boxes)} 个候选区域")
    
    # 7. 【V24.1新增】使用投影分割线辅助分割大框
    if projection_split_lines and len(raw_boxes) > 0:
        raw_boxes = split_boxes_by_projection(raw_boxes, projection_split_lines, img_width)
        print(f"[题目分割器] ✓ 投影辅助分割后: {len(raw_boxes)} 个区域")
    
    # 8. 智能合并（更保守，避免过度合并）
    if len(raw_boxes) > 0:
        merged_boxes = merge_overlapping_boxes(raw_boxes, img_height, merge_threshold=0.5)  # 提高合并阈值
        print(f"[题目分割器] ✓ 合并后剩余 {len(merged_boxes)} 个题目区域")
    else:
        merged_boxes = []
    
    # 9. 【V24.1+新增】全覆盖检查 - 确保不遗漏任何信息
    if len(merged_boxes) > 0:
        final_boxes = ensure_full_coverage(binary, merged_boxes, img_width, img_height)
        print(f"[题目分割器] ✓ 全覆盖检查完成，最终: {len(final_boxes)} 个题目区域")
    else:
        final_boxes = merged_boxes
    
    # 10. 从上到下排序
    final_boxes.sort(key=lambda box: box[1])
    
    print(f"\n{'='*70}")
    print(f"[题目分割器] ✅ 最终检测到 {len(final_boxes)} 个题目区域")
    print(f"{'='*70}\n")
    
    return final_boxes


def find_split_lines_by_projection(binary: np.ndarray, img_height: int, min_gap: int = 20) -> List[int]:
    """
    【V24.1新增】使用水平投影法找到题目之间的分割线
    
    原理：题目之间通常有空白行，这些行的像素投影值会很低
    
    参数:
        binary: 二值化图像
        img_height: 图片高度
        min_gap: 最小空白行高度（像素）
    
    返回:
        分割线的y坐标列表
    """
    # 计算每一行的水平投影（白色像素数量）
    h_projection = np.sum(binary == 255, axis=1)
    
    # 找到投影值很低的行（空白区域）
    threshold = np.max(h_projection) * 0.1  # 低于最大值10%视为空白
    is_blank = h_projection < threshold
    
    # 找到连续的空白区域
    split_lines = []
    in_gap = False
    gap_start = 0
    
    for i, blank in enumerate(is_blank):
        if blank and not in_gap:
            gap_start = i
            in_gap = True
        elif not blank and in_gap:
            gap_height = i - gap_start
            if gap_height >= min_gap:
                # 选择空白区域的中间作为分割线
                split_line = (gap_start + i) // 2
                split_lines.append(split_line)
            in_gap = False
    
    return split_lines


def split_boxes_by_projection(boxes: List[Tuple[int, int, int, int]], 
                               split_lines: List[int], 
                               img_width: int) -> List[Tuple[int, int, int, int]]:
    """
    【V24.1新增】使用投影分割线将大框分割成小框
    
    参数:
        boxes: 原始边界框列表
        split_lines: 分割线y坐标列表
        img_width: 图片宽度
    
    返回:
        分割后的边界框列表
    """
    new_boxes = []
    
    for x, y, w, h in boxes:
        box_bottom = y + h
        
        # 找到穿过此框的分割线
        internal_splits = [line for line in split_lines if y < line < box_bottom]
        
        if not internal_splits:
            # 没有分割线穿过，保留原框
            new_boxes.append((x, y, w, h))
        else:
            # 有分割线，进行分割
            internal_splits = [y] + sorted(internal_splits) + [box_bottom]
            
            for i in range(len(internal_splits) - 1):
                sub_y = internal_splits[i]
                sub_h = internal_splits[i + 1] - sub_y
                
                # 过滤掉太小的子框
                if sub_h > 30:  # 至少30像素高
                    new_boxes.append((x, sub_y, w, sub_h))
    
    return new_boxes


def ensure_full_coverage(binary: np.ndarray, 
                         boxes: List[Tuple[int, int, int, int]], 
                         img_width: int, 
                         img_height: int,
                         min_uncovered_area: int = 500) -> List[Tuple[int, int, int, int]]:
    """
    【V24.1+新增】确保所有有意义的区域都被至少一个框覆盖
    
    策略：
    1. 创建一个覆盖掩码，标记已被覆盖的区域
    2. 检测未被覆盖的文字区域
    3. 为这些区域创建补充框
    4. 允许框之间有适当重叠（10-20%）
    
    参数:
        binary: 二值化图像
        boxes: 现有的边界框列表
        img_width: 图片宽度
        img_height: 图片高度
        min_uncovered_area: 最小未覆盖区域面积（像素），小于此值忽略
    
    返回:
        包含补充框的完整边界框列表
    """
    print(f"\n[全覆盖检查] 🔍 开始检查覆盖完整性...")
    
    # 1. 创建覆盖掩码（所有像素初始为未覆盖）
    coverage_mask = np.zeros((img_height, img_width), dtype=np.uint8)
    
    # 2. 标记已被覆盖的区域（给予一定的扩展padding）
    padding = 15  # 覆盖检测时的padding
    for x, y, w, h in boxes:
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(img_width, x + w + padding)
        y2 = min(img_height, y + h + padding)
        coverage_mask[y1:y2, x1:x2] = 255
    
    # 3. 找到未被覆盖的文字区域（在二值图中有内容，但在覆盖掩码中未覆盖）
    uncovered = cv2.bitwise_and(binary, cv2.bitwise_not(coverage_mask))
    
    # 4. 检测未覆盖区域的轮廓
    uncovered_contours, _ = cv2.findContours(uncovered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 5. 为未覆盖区域创建补充框
    supplementary_boxes = []
    for contour in uncovered_contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        
        # 只处理足够大的未覆盖区域
        if area >= min_uncovered_area:
            # 创建补充框，带有较大的padding确保覆盖
            supplement_padding = 30
            supp_x = max(0, x - supplement_padding)
            supp_y = max(0, y - supplement_padding)
            supp_w = min(img_width - supp_x, w + 2 * supplement_padding)
            supp_h = min(img_height - supp_y, h + 2 * supplement_padding)
            
            supplementary_boxes.append((supp_x, supp_y, supp_w, supp_h))
            print(f"[全覆盖检查] → 发现未覆盖区域 ({x},{y},{w}x{h})，创建补充框")
    
    # 6. 合并原始框和补充框
    all_boxes = boxes + supplementary_boxes
    
    if supplementary_boxes:
        print(f"[全覆盖检查] ✓ 创建了 {len(supplementary_boxes)} 个补充框")
    else:
        print(f"[全覆盖检查] ✓ 无需补充，所有区域已覆盖")
    
    # 7. 计算覆盖率统计
    total_text_pixels = np.sum(binary == 255)
    final_coverage_mask = np.zeros((img_height, img_width), dtype=np.uint8)
    for x, y, w, h in all_boxes:
        final_coverage_mask[y:min(img_height, y+h), x:min(img_width, x+w)] = 255
    
    covered_text_pixels = np.sum(cv2.bitwise_and(binary, final_coverage_mask) == 255)
    coverage_rate = (covered_text_pixels / total_text_pixels * 100) if total_text_pixels > 0 else 100
    
    print(f"[全覆盖检查] 📊 覆盖率: {coverage_rate:.1f}% ({covered_text_pixels}/{total_text_pixels} 像素)")
    
    return all_boxes


def merge_overlapping_boxes(boxes: List[Tuple[int, int, int, int]], img_height: int, merge_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
    """
    合并重叠或垂直距离过近的边界框。
    
    【V24.1优化】更保守的合并策略，避免过度合并紧密题目
    
    策略：
    - 如果两个框的垂直重叠超过merge_threshold（默认30%），合并
    - 如果两个框的垂直间距小于图片高度的2%（从3%降低），合并
    """
    if len(boxes) <= 1:
        return boxes
    
    # 按y坐标排序
    sorted_boxes = sorted(boxes, key=lambda b: b[1])
    merged = [sorted_boxes[0]]
    
    for current in sorted_boxes[1:]:
        last_merged = merged[-1]
        
        # 计算垂直重叠和间距
        last_bottom = last_merged[1] + last_merged[3]
        current_top = current[1]
        current_bottom = current[1] + current[3]
        
        # 计算重叠高度
        overlap = max(0, min(last_bottom, current_bottom) - max(last_merged[1], current_top))
        
        # 计算间距
        gap = current_top - last_bottom
        
        # 判断是否需要合并
        should_merge = False
        
        # 条件1: 有显著重叠（超过较小框高度的merge_threshold）
        if overlap > min(last_merged[3], current[3]) * merge_threshold:
            should_merge = True
        
        # 条件2: 间距很小（小于图片高度的2%）- 从3%降低到2%，更保守
        if gap >= 0 and gap < img_height * 0.02:
            should_merge = True
        
        if should_merge:
            # 合并两个框：取最小的x和y，最大的右下角
            new_x = min(last_merged[0], current[0])
            new_y = min(last_merged[1], current[1])
            new_right = max(last_merged[0] + last_merged[2], current[0] + current[2])
            new_bottom = max(last_merged[1] + last_merged[3], current[1] + current[3])
            
            merged[-1] = (new_x, new_y, new_right - new_x, new_bottom - new_y)
            print(f"[题目分割器] → 合并了两个接近的区域（gap={gap}px）")
        else:
            merged.append(current)
    
    return merged


def visualize_detected_boxes(image: Image.Image, 
                            boxes: List[Tuple[int, int, int, int]], 
                            output_path: str = "debug_boxes.png",
                            show_overlap: bool = True):
    """
    【V24.1增强】调试用：在图片上绘制检测到的边界框并保存
    
    参数:
        image: 原始图片
        boxes: 检测到的边界框列表
        output_path: 输出文件路径
        show_overlap: 是否用不同颜色标识重叠区域
    """
    cv_image = pil_to_cv2(image)
    img_height, img_width = cv_image.shape[:2]
    
    # 如果要显示重叠，先创建覆盖掩码
    if show_overlap:
        overlap_mask = np.zeros((img_height, img_width), dtype=np.uint8)
        for x, y, w, h in boxes:
            overlap_mask[y:y+h, x:x+w] += 1
        
        # 用半透明颜色显示重叠区域
        overlay = cv_image.copy()
        # 重叠2次及以上的区域用黄色标识
        overlap_2x = (overlap_mask >= 2)
        overlay[overlap_2x] = [0, 255, 255]  # 黄色
        
        # 混合
        cv_image = cv2.addWeighted(cv_image, 0.7, overlay, 0.3, 0)
    
    # 绘制所有边界框
    for i, (x, y, w, h) in enumerate(boxes):
        # 绘制矩形（绿色边框）
        cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        # 绘制题号（红色文字，白色背景）
        label = f"Q{i+1}"
        font_scale = 1.0
        thickness = 2
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # 绘制白色背景
        cv2.rectangle(cv_image, (x + 5, y + 5), (x + text_width + 15, y + text_height + 15), (255, 255, 255), -1)
        # 绘制文字
        cv2.putText(cv_image, label, (x + 10, y + text_height + 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
    
    # 添加图例
    legend_y = 30
    cv2.putText(cv_image, f"Total: {len(boxes)} boxes", (10, legend_y), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if show_overlap:
        cv2.putText(cv_image, "Yellow = Overlap", (10, legend_y + 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # 保存
    cv2.imwrite(output_path, cv_image)
    print(f"[题目分割器] 📸 调试图片已保存到: {output_path}")
    
    # 统计重叠信息
    if show_overlap:
        overlap_pixels = np.sum(overlap_mask >= 2)
        total_covered = np.sum(overlap_mask >= 1)
        overlap_rate = (overlap_pixels / total_covered * 100) if total_covered > 0 else 0
        print(f"[题目分割器] 📊 重叠率: {overlap_rate:.1f}%")

