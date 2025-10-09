#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V19.0 混合输入架构 - 快速测试脚本
用于验证 OCR + 原图混合输入是否正常工作
"""

import requests
import base64
import json
import sys
from pathlib import Path

def test_hybrid_chat(image_path: str, prompt: str = "请详细解答这道题目。"):
    """
    测试混合输入架构
    
    Args:
        image_path: 图片文件路径
        prompt: 用户提示
    """
    # 1. 读取图片并转为base64
    print(f"\n{'='*60}")
    print(f"📸 正在读取图片: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        print(f"✅ 图片读取成功，大小: {len(image_bytes)} 字节")
    except Exception as e:
        print(f"❌ 读取图片失败: {e}")
        return
    
    # 2. 构建请求
    url = "http://127.0.0.1:8000/chat"
    payload = {
        "prompt": prompt,
        "image_base_64": image_base64
    }
    
    print(f"\n🚀 正在发送请求到后端...")
    print(f"   Prompt: {prompt}")
    print(f"   图片Base64长度: {len(image_base64)} 字符")
    
    # 3. 发送请求
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n{'='*60}")
            print(f"✅ 请求成功！")
            print(f"{'='*60}")
            print(f"📝 会话ID: {result.get('session_id')}")
            print(f"📋 标题: {result.get('title')}")
            print(f"🔄 是否截断: {result.get('is_truncated')}")
            print(f"\n{'='*60}")
            print(f"🤖 AI回答:")
            print(f"{'='*60}")
            print(result.get('response', ''))
            print(f"{'='*60}\n")
            
            # 返回session_id供后续追问使用
            return result.get('session_id')
        else:
            print(f"\n❌ 请求失败！")
            print(f"   状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时！请检查：")
        print(f"   1. 后端服务是否正在运行")
        print(f"   2. OCR识别是否耗时过长")
        return None
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None

def test_follow_up(session_id: str, question: str):
    """
    测试追问功能
    
    Args:
        session_id: 会话ID
        question: 追问问题
    """
    url = "http://127.0.0.1:8000/chat"
    payload = {
        "session_id": session_id,
        "prompt": question
    }
    
    print(f"\n{'='*60}")
    print(f"💬 发送追问...")
    print(f"   会话ID: {session_id}")
    print(f"   问题: {question}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 追问成功！")
            print(f"{'='*60}")
            print(f"🤖 AI回答:")
            print(f"{'='*60}")
            print(result.get('response', ''))
            print(f"{'='*60}\n")
        else:
            print(f"\n❌ 追问失败: {response.text}")
    except Exception as e:
        print(f"\n❌ 追问异常: {e}")

def main():
    """主测试流程"""
    print("""
╔══════════════════════════════════════════════════════════╗
║     V19.0 混合输入架构 - 测试脚本                       ║
║     OCR增强 + 原图视觉 = 终极识别能力                   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 检查后端服务
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"✅ 后端服务状态: {response.json()['message']}\n")
    except:
        print("❌ 后端服务未启动！请先运行: uvicorn main:app --reload\n")
        sys.exit(1)
    
    # 获取图片路径
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("📌 使用方法:")
        print("   python test_hybrid_architecture.py <图片路径> [提示词]\n")
        print("📌 示例:")
        print("   python test_hybrid_architecture.py test_math.png")
        print("   python test_hybrid_architecture.py test_math.png \"请详细解答第1题\"\n")
        
        # 尝试使用默认测试图片
        default_images = ["test.png", "test.jpg", "example.png"]
        for img in default_images:
            if Path(img).exists():
                image_path = img
                print(f"🔍 找到默认测试图片: {image_path}")
                break
        else:
            print("❌ 未找到测试图片，请提供图片路径")
            sys.exit(1)
    
    # 获取提示词
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细解答这道题目。"
    
    # 测试首轮对话
    session_id = test_hybrid_chat(image_path, prompt)
    
    if session_id:
        # 询问是否要追问
        print("\n" + "="*60)
        print("💡 提示：你可以继续追问（输入问题）或按Enter退出")
        print("="*60)
        
        while True:
            try:
                question = input("\n❓ 追问 (Enter退出): ").strip()
                if not question:
                    break
                test_follow_up(session_id, question)
            except KeyboardInterrupt:
                print("\n\n👋 测试结束！")
                break
    
    print("\n✨ 测试完成！\n")

if __name__ == "__main__":
    main()

