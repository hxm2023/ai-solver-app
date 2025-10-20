#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信小程序API接口测试脚本
测试 /process_image_for_miniapp 端点

功能：
1. 测试解题模式 (solve)
2. 测试批改模式 (review)
"""

import sys
import io
import requests
import base64
import json
from pathlib import Path

# 解决Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==============================================================================
# 配置区
# ==============================================================================

# API端点URL
API_URL = "http://127.0.0.1:8000/process_image_for_miniapp"

# 测试图片路径（请修改为实际的测试图片路径）
TEST_IMAGE_PATH = r"D:\360安全浏览器下载\题目\题目样本\wKhkGWXgOUqAC53qAAKgGBNBLLw024.jpg"

# 请求超时时间（秒）
TIMEOUT = 260


# ==============================================================================
# 工具函数
# ==============================================================================

def image_to_base64(image_path: str) -> str:
    """
    将图片文件转换为Base64编码字符串
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        Base64编码的字符串
    """
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return base64_string
    except FileNotFoundError:
        print(f"❌ 错误：找不到图片文件 {image_path}")
        print(f"💡 请修改 TEST_IMAGE_PATH 变量为有效的图片路径")
        raise
    except Exception as e:
        print(f"❌ 读取图片失败: {e}")
        raise


def send_request(image_base64: str, mode: str) -> dict:
    """
    向API发送请求
    
    Args:
        image_base64: Base64编码的图片
        mode: 操作模式 ('solve' 或 'review')
        
    Returns:
        API响应的JSON数据
    """
    payload = {
        "image_base_64": image_base64,
        "mode": mode
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"[请求] 正在发送请求到 {API_URL}")
    print(f"[请求] 模式: {mode}")
    print(f"[请求] 图片大小: {len(image_base64)} 字符")
    
    response = requests.post(
        API_URL,
        json=payload,
        headers=headers,
        timeout=TIMEOUT
    )
    
    return response


def print_separator(title: str = ""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'-'*70}\n")


def print_response(response: requests.Response, mode: str):
    """
    格式化打印API响应
    
    Args:
        response: requests响应对象
        mode: 请求的模式
    """
    print(f"[响应] HTTP状态码: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"[响应] 状态: {data.get('status', 'unknown')}")
            
            if data.get('status') == 'success':
                result = data.get('result', '')
                print(f"[响应] 结果长度: {len(result)} 字符")
                print(f"\n{'─'*70}")
                print(f"【AI生成内容预览】({mode}模式)")
                print(f"{'─'*70}")
                # 打印前500个字符作为预览
                preview = result[:500] if len(result) > 500 else result
                print(preview)
                if len(result) > 500:
                    print(f"\n... (还有 {len(result)-500} 个字符未显示)")
                print(f"{'─'*70}\n")
                
                print("✅ 测试成功！")
                
                # 可选：将完整结果保存到文件
                output_file = f"miniapp_test_result_{mode}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"💾 完整结果已保存到: {output_file}")
                
            elif data.get('status') == 'error':
                error_msg = data.get('message', '未知错误')
                print(f"[响应] 错误信息: {error_msg}")
                print("❌ 测试失败：API返回错误")
        
        except json.JSONDecodeError:
            print("❌ 测试失败：无法解析JSON响应")
            print(f"原始响应: {response.text[:200]}")
    else:
        print(f"❌ 测试失败：HTTP错误")
        print(f"响应内容: {response.text[:200]}")


# ==============================================================================
# 主测试流程
# ==============================================================================

def main():
    """主测试函数"""
    
    print_separator("微信小程序API接口测试")
    
    # 检查测试图片是否存在
    if not Path(TEST_IMAGE_PATH).exists():
        print(f"❌ 测试图片不存在: {TEST_IMAGE_PATH}")
        print(f"\n💡 请执行以下步骤：")
        print(f"   1. 准备一张题目图片")
        print(f"   2. 修改脚本中的 TEST_IMAGE_PATH 变量为该图片的路径")
        print(f"   3. 重新运行此测试脚本")
        return
    
    print(f"📷 测试图片: {TEST_IMAGE_PATH}")
    print(f"🔗 API地址: {API_URL}")
    print(f"⏱️ 超时设置: {TIMEOUT}秒")
    
    # 转换图片为Base64
    print("\n[准备] 正在读取并转换图片为Base64...")
    try:
        image_base64 = image_to_base64(TEST_IMAGE_PATH)
        print(f"[准备] ✓ Base64编码完成")
    except Exception:
        print("\n测试终止。")
        return
    
    # ==============================================================================
    # 测试1: 解题模式
    # ==============================================================================
    
    print_separator("测试 1/2: 解题模式 (solve)")
    
    try:
        response = send_request(image_base64, mode='solve')
        print_response(response, mode='solve')
    except requests.exceptions.Timeout:
        print(f"❌ 测试失败：请求超时（超过{TIMEOUT}秒）")
        print(f"💡 建议：增加 TIMEOUT 值或检查后端服务")
    except requests.exceptions.ConnectionError:
        print(f"❌ 测试失败：无法连接到服务器")
        print(f"💡 建议：")
        print(f"   1. 确认后端服务已启动")
        print(f"   2. 检查API地址是否正确: {API_URL}")
        print(f"   3. 尝试访问: http://127.0.0.1:8000/docs")
    except Exception as e:
        print(f"❌ 测试失败：{type(e).__name__}: {e}")
    
    print_separator()
    
    # 等待用户确认
    input("按回车键继续下一个测试...")
    
    # ==============================================================================
    # 测试2: 批改模式
    # ==============================================================================
    
    print_separator("测试 2/2: 批改模式 (review)")
    
    try:
        response = send_request(image_base64, mode='review')
        print_response(response, mode='review')
    except requests.exceptions.Timeout:
        print(f"❌ 测试失败：请求超时（超过{TIMEOUT}秒）")
        print(f"💡 建议：增加 TIMEOUT 值或检查后端服务")
    except requests.exceptions.ConnectionError:
        print(f"❌ 测试失败：无法连接到服务器")
        print(f"💡 建议：")
        print(f"   1. 确认后端服务已启动")
        print(f"   2. 检查API地址是否正确: {API_URL}")
        print(f"   3. 尝试访问: http://127.0.0.1:8000/docs")
    except Exception as e:
        print(f"❌ 测试失败：{type(e).__name__}: {e}")
    
    # ==============================================================================
    # 测试总结
    # ==============================================================================
    
    print_separator("测试完成")
    
    print("📊 测试总结:")
    print("   • 解题模式 (solve): 查看上方结果")
    print("   • 批改模式 (review): 查看上方结果")
    print("\n📁 生成的文件:")
    print("   • miniapp_test_result_solve.md  (解题结果)")
    print("   • miniapp_test_result_review.md (批改结果)")
    print("\n💡 建议:")
    print("   • 使用Markdown查看器打开生成的.md文件")
    print("   • 使用支持LaTeX的编辑器查看数学公式")
    print("   • 如果测试失败，检查后端服务日志")
    
    print(f"\n{'='*70}\n")


# ==============================================================================
# 快速测试函数（可单独调用）
# ==============================================================================

def quick_test_solve(image_path: str):
    """快速测试解题模式"""
    image_base64 = image_to_base64(image_path)
    response = send_request(image_base64, mode='solve')
    return response.json()


def quick_test_review(image_path: str):
    """快速测试批改模式"""
    image_base64 = image_to_base64(image_path)
    response = send_request(image_base64, mode='review')
    return response.json()


# ==============================================================================
# 脚本入口
# ==============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生未预期的错误:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

