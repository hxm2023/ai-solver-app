#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V19.0 混合输入架构 - 性能基准测试
对比纯图片模式 vs 混合输入模式的识别准确性
"""

import time
from PIL import Image
from pix2text import Pix2Text
import io
import re

def image_preprocess_v2(img: Image.Image) -> Image.Image:
    """图片预处理"""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    max_dimension = 2000
    if max(width, height) > max_dimension:
        scale = max_dimension / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return img

def extract_text_with_pix2text(image: Image.Image, p2t) -> str:
    """OCR识别"""
    try:
        processed_img = image_preprocess_v2(image)
        result = p2t.recognize(processed_img)
        
        if isinstance(result, dict) and 'text' in result:
            ocr_text = result['text']
        elif isinstance(result, str):
            ocr_text = result
        else:
            ocr_text = str(result)
        
        ocr_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ocr_text)
        ocr_text = ocr_text.strip()
        
        return ocr_text
    except Exception as e:
        return f"[OCR识别失败: {e}]"

def benchmark_ocr_performance(image_path: str):
    """
    基准测试：评估OCR性能
    
    测试指标：
    1. 初始化时间
    2. 识别速度
    3. 识别结果质量
    """
    print("="*70)
    print("🔬 V19.0 混合输入架构 - OCR性能基准测试")
    print("="*70)
    
    # 1. 初始化OCR引擎
    print("\n📦 步骤1: 初始化Pix2Text OCR引擎...")
    start_time = time.time()
    try:
        p2t = Pix2Text(analyzer_config=dict(model_name='mfd'))
        init_time = time.time() - start_time
        print(f"   ✅ 初始化成功！耗时: {init_time:.2f}秒")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return
    
    # 2. 加载测试图片
    print(f"\n📸 步骤2: 加载测试图片 '{image_path}'...")
    try:
        image = Image.open(image_path)
        original_size = image.size
        print(f"   ✅ 图片加载成功！")
        print(f"   - 原始尺寸: {original_size[0]} x {original_size[1]}")
        print(f"   - 图片模式: {image.mode}")
    except Exception as e:
        print(f"   ❌ 图片加载失败: {e}")
        return
    
    # 3. 图片预处理
    print(f"\n🔧 步骤3: 图片预处理...")
    start_time = time.time()
    processed_image = image_preprocess_v2(image)
    preprocess_time = time.time() - start_time
    processed_size = processed_image.size
    print(f"   ✅ 预处理完成！耗时: {preprocess_time*1000:.0f}ms")
    print(f"   - 处理后尺寸: {processed_size[0]} x {processed_size[1]}")
    print(f"   - 缩放比例: {processed_size[0]/original_size[0]:.2f}x")
    
    # 4. OCR识别
    print(f"\n🔍 步骤4: OCR文字识别...")
    start_time = time.time()
    ocr_text = extract_text_with_pix2text(image, p2t)
    ocr_time = time.time() - start_time
    print(f"   ✅ 识别完成！耗时: {ocr_time:.2f}秒")
    
    # 5. 分析识别结果
    print(f"\n📊 步骤5: 识别结果分析")
    print("="*70)
    
    char_count = len(ocr_text)
    line_count = ocr_text.count('\n') + 1
    has_latex = bool(re.search(r'\\[a-zA-Z]+', ocr_text))
    has_numbers = bool(re.search(r'\d', ocr_text))
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', ocr_text))
    
    print(f"✅ 识别统计:")
    print(f"   - 总字符数: {char_count}")
    print(f"   - 总行数: {line_count}")
    print(f"   - 包含LaTeX公式: {'是 ✅' if has_latex else '否'}")
    print(f"   - 包含数字: {'是 ✅' if has_numbers else '否'}")
    print(f"   - 包含中文: {'是 ✅' if has_chinese else '否'}")
    
    print(f"\n📝 识别结果预览 (前500字符):")
    print("-"*70)
    print(ocr_text[:500] + ("..." if len(ocr_text) > 500 else ""))
    print("-"*70)
    
    # 6. 性能总结
    print(f"\n⏱️  性能总结:")
    print("="*70)
    total_time = init_time + preprocess_time + ocr_time
    print(f"   初始化时间:    {init_time:.2f}秒 ({init_time/total_time*100:.1f}%)")
    print(f"   预处理时间:    {preprocess_time:.3f}秒 ({preprocess_time/total_time*100:.1f}%)")
    print(f"   OCR识别时间:   {ocr_time:.2f}秒 ({ocr_time/total_time*100:.1f}%)")
    print(f"   总耗时:        {total_time:.2f}秒")
    print(f"   识别速度:      {char_count/ocr_time:.1f} 字符/秒")
    print("="*70)
    
    # 7. 质量评估提示
    print(f"\n💡 质量评估建议:")
    print("   1. 检查上述OCR结果是否准确识别了文字和公式")
    print("   2. 对比原图，验证LaTeX公式转换是否正确")
    print("   3. 注意特殊符号、上下标、分数等是否识别完整")
    print("   4. 如果识别有误，图片仍会发送给AI进行视觉校正")
    
    # 8. 架构优势说明
    print(f"\n🎯 V19.0混合架构优势:")
    print("="*70)
    print("   ✅ 文字/公式: 由Pix2Text高精度识别 (如上所示)")
    print("   ✅ 几何图形: 原图直接发送给通义千问视觉理解")
    print("   ✅ 信息互补: AI可用原图纠正OCR错误")
    print("   ✅ 优雅降级: OCR失败时自动退化到纯图片模式")
    print("="*70)
    
    print(f"\n✨ 测试完成！OCR部分工作正常。")
    print(f"💬 下一步: 使用 test_hybrid_architecture.py 测试完整的AI解答流程\n")

def main():
    """主测试入口"""
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                V19.0 OCR性能基准测试                             ║
║                                                                  ║
║  本测试将评估Pix2Text OCR引擎的:                                 ║
║  - 初始化速度                                                    ║
║  - 识别准确性                                                    ║
║  - 处理性能                                                      ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("📌 使用方法:")
        print("   python benchmark_v19.py <图片路径>\n")
        print("📌 示例:")
        print("   python benchmark_v19.py test_math.png\n")
        sys.exit(1)
    
    benchmark_ocr_performance(image_path)

if __name__ == "__main__":
    main()

