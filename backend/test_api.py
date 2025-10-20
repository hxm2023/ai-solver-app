#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API接口测试脚本
使用方法：python test_api.py
"""

import requests
import base64
import json
from pathlib import Path

# 配置
API_BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    """打印分隔符"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_health_check():
    """测试1：健康检查"""
    print_section("测试1：健康检查")
    
    response = requests.get(f"{API_BASE_URL}/api/health")
    result = response.json()
    
    print("响应：")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("status") == "healthy":
        print("\n✅ 健康检查通过")
    else:
        print("\n❌ 健康检查失败")


def test_api_info():
    """测试2：API信息"""
    print_section("测试2：API信息")
    
    response = requests.get(f"{API_BASE_URL}/api/")
    result = response.json()
    
    print("响应：")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n✅ API信息获取成功")


def test_text_solve():
    """测试3：纯文本解题"""
    print_section("测试3：纯文本解题")
    
    data = {
        "mode": "solve",
        "input_type": "text",
        "content": {
            "text": "求函数 f(x) = x^2 + 2x + 1 的导数"
        },
        "options": {
            "detail_level": "detailed",
            "include_steps": True
        }
    }
    
    print("请求：")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    response = requests.post(
        f"{API_BASE_URL}/api/solve",
        json=data,
        timeout=30
    )
    
    result = response.json()
    
    print("\n响应：")
    if result.get("success"):
        print(f"✅ 解题成功！")
        print(f"Session ID: {result.get('session_id')}")
        print(f"处理时间: {result['metadata']['processing_time_ms']}ms")
        print("\nAI解答：")
        print(result['results'][0]['answer']['content'][:300] + "...")
    else:
        print(f"❌ 解题失败: {result.get('error')}")


def test_text_review():
    """测试4：纯文本批改"""
    print_section("测试4：纯文本批改")
    
    data = {
        "mode": "review",
        "input_type": "text",
        "content": {
            "text": """
            题目：计算 1 + 1 的值
            学生答案：2
            
            题目：计算 2 + 2 的值
            学生答案：5
            """
        },
        "options": {
            "include_analysis": True
        }
    }
    
    print("请求：批改两道题目")
    
    response = requests.post(
        f"{API_BASE_URL}/api/solve",
        json=data,
        timeout=30
    )
    
    result = response.json()
    
    if result.get("success"):
        print(f"\n✅ 批改成功！")
        print(f"处理时间: {result['metadata']['processing_time_ms']}ms")
        print("\nAI批改：")
        print(result['results'][0]['answer']['content'][:300] + "...")
    else:
        print(f"\n❌ 批改失败: {result.get('error')}")


def test_image_solve():
    """测试5：图片解题（如果有测试图片）"""
    print_section("测试5：图片解题")
    
    # 查找测试图片
    test_image_paths = [
        "test_image.png",
        "test_image.jpg",
        "../test_image.png",
        "../../test_image.png"
    ]
    
    test_image = None
    for path in test_image_paths:
        if Path(path).exists():
            test_image = path
            break
    
    if not test_image:
        print("⚠️ 未找到测试图片，跳过此测试")
        print("提示：在backend目录下放置 test_image.png 可测试图片功能")
        return
    
    # 读取图片并转Base64
    with open(test_image, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"测试图片: {test_image}")
    print(f"图片大小: {len(image_base64)} 字符")
    
    data = {
        "mode": "solve",
        "input_type": "image",
        "content": {
            "image_base64": image_base64
        },
        "options": {
            "detail_level": "detailed"
        }
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/solve",
        json=data,
        timeout=60
    )
    
    result = response.json()
    
    if result.get("success"):
        print(f"\n✅ 图片解题成功！")
        print(f"处理时间: {result['metadata']['processing_time_ms']}ms")
        print(f"OCR置信度: {result['metadata']['ocr_confidence']}")
        print("\n题目内容（OCR识别）：")
        print(result['results'][0]['question_text'][:200] + "...")
        print("\nAI解答：")
        print(result['results'][0]['answer']['content'][:300] + "...")
    else:
        print(f"\n❌ 图片解题失败: {result.get('error')}")


def test_question_bank():
    """测试6：题库检索"""
    print_section("测试6：题库检索")
    
    data = {
        "tags": ["函数", "导数"],
        "difficulty": "medium",
        "subject": "math",
        "limit": 5
    }
    
    print("请求：")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    response = requests.post(
        f"{API_BASE_URL}/api/question_bank",
        json=data,
        timeout=10
    )
    
    result = response.json()
    
    print("\n响应：")
    if result.get("success"):
        print(f"✅ 检索成功！")
        print(f"总计: {result['total']} 道题目")
        print(f"返回: {result['metadata']['returned']} 道题目")
        
        if result['questions']:
            print("\n示例题目：")
            q = result['questions'][0]
            print(f"题号: {q['id']}")
            print(f"标签: {q['tags']}")
            print(f"内容: {q['content']}")
    else:
        print(f"❌ 检索失败: {result.get('error')}")


def main():
    """主函数"""
    print("\n" + "█"*70)
    print("█" + " "*20 + "API接口测试脚本" + " "*23 + "█")
    print("█" + " "*20 + "沐梧AI解题系统 V22.1" + " "*19 + "█")
    print("█"*70)
    
    try:
        # 检查服务是否运行
        print("\n正在检查服务状态...")
        requests.get(f"{API_BASE_URL}/", timeout=5)
        print("✅ 后端服务正常运行")
        
        # 依次执行测试
        test_health_check()
        test_api_info()
        test_text_solve()
        test_text_review()
        test_image_solve()
        test_question_bank()
        
        print_section("测试完成")
        print("✅ 所有测试执行完毕！")
        print("\n提示：")
        print("- 访问 http://127.0.0.1:8000/docs 查看完整API文档")
        print("- 查看 API接口使用指南.md 了解更多用法")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到后端服务")
        print("请确保后端服务已启动：")
        print("  cd backend")
        print("  uvicorn main:app --reload")
    
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

