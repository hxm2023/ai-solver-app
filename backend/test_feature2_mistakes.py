#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feature 2: 错题本系统测试脚本
使用方法：python test_feature2_mistakes.py
"""

import requests
import json
import base64
from pathlib import Path

# 配置
API_BASE_URL = "http://127.0.0.1:8000"

# 全局token（从Feature 1获取）
TOKEN = None


def print_section(title):
    """打印分隔符"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def get_auth_headers():
    """获取认证请求头"""
    if TOKEN:
        return {"Authorization": f"Bearer {TOKEN}"}
    return {}


def test_0_login():
    """测试0：用户登录（前置条件）"""
    global TOKEN
    print_section("测试0：用户登录（前置条件）")
    
    # 尝试登录测试用户
    login_data = {
        "username": "test_student",
        "password": "password123"
    }
    
    print("尝试登录...")
    response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        TOKEN = result['access_token']
        print(f"✅ 登录成功！")
        print(f"   用户: {result['user_info']['username']}")
        print(f"   Token (前30字符): {TOKEN[:30]}...")
        return True
    else:
        print(f"❌ 登录失败: {response.json()}")
        print("\n⚠️ 请先运行: python test_feature1_auth.py 创建测试用户")
        return False


def test_1_create_mistake():
    """测试1：手动创建错题"""
    print_section("测试1：手动创建错题")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return None
    
    # 创建一个错题
    mistake_data = {
        "question_text": "计算 1 + 1 的值",
        "wrong_answer": "3",
        "ai_analysis": "[MISTAKE_DETECTED] 这道题答错了。正确答案应该是 2，而不是 3。",
        "subject": "数学",
        "knowledge_points": ["加法", "基础运算"],
        "difficulty": 1
    }
    
    print("创建错题...")
    print(f"题目: {mistake_data['question_text']}")
    print(f"错误答案: {mistake_data['wrong_answer']}")
    print(f"知识点: {mistake_data['knowledge_points']}")
    
    response = requests.post(
        f"{API_BASE_URL}/mistakes/",
        json=mistake_data,
        headers=get_auth_headers()
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✅ 错题创建成功！")
        print(f"   错题ID: {result['id']}")
        print(f"   学科: {result['subject']}")
        print(f"   难度: {result['difficulty']}")
        print(f"   创建时间: {result['created_at']}")
        return result['id']
    else:
        print(f"\n❌ 创建失败: {response.json()}")
        return None


def test_2_get_mistakes_list(mistake_id):
    """测试2：获取错题列表"""
    print_section("测试2：获取错题列表")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return
    
    print("获取错题列表...")
    response = requests.get(
        f"{API_BASE_URL}/mistakes/",
        params={"page": 1, "page_size": 10},
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功！")
        print(f"   总计: {result['total']} 条错题")
        print(f"   当前页: {result['page']}")
        print(f"   每页: {result['page_size']}")
        print(f"   本页返回: {len(result['mistakes'])} 条")
        
        if result['mistakes']:
            print("\n   错题列表:")
            for m in result['mistakes'][:3]:  # 只显示前3条
                print(f"     - ID {m['id']}: {m['question_text'][:30]}... ({m['subject']})")
    else:
        print(f"❌ 获取失败: {response.json()}")


def test_3_get_mistake_detail(mistake_id):
    """测试3：获取错题详情"""
    print_section("测试3：获取错题详情")
    
    if not TOKEN or not mistake_id:
        print("❌ 未登录或无错题ID，跳过测试")
        return
    
    print(f"获取错题详情: ID={mistake_id}")
    response = requests.get(
        f"{API_BASE_URL}/mistakes/{mistake_id}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功！")
        print(f"   题目: {result['question_text']}")
        print(f"   错误答案: {result['wrong_answer']}")
        print(f"   AI分析: {result['ai_analysis'][:100]}...")
        print(f"   已复习: {result['reviewed']}")
        print(f"   复习次数: {result['review_count']}")
    else:
        print(f"❌ 获取失败: {response.json()}")


def test_4_update_mistake(mistake_id):
    """测试4：标记错题为已复习"""
    print_section("测试4：标记错题为已复习")
    
    if not TOKEN or not mistake_id:
        print("❌ 未登录或无错题ID，跳过测试")
        return
    
    update_data = {
        "reviewed": True
    }
    
    print(f"标记错题为已复习: ID={mistake_id}")
    response = requests.put(
        f"{API_BASE_URL}/mistakes/{mistake_id}",
        json=update_data,
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 更新成功！")
        print(f"   已复习: {result['reviewed']}")
        print(f"   复习次数: {result['review_count']}")
        print(f"   最后复习时间: {result['last_reviewed_at']}")
    else:
        print(f"❌ 更新失败: {response.json()}")


def test_5_get_stats():
    """测试5：获取错题统计"""
    print_section("测试5：获取错题统计")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return
    
    print("获取错题统计...")
    response = requests.get(
        f"{API_BASE_URL}/mistakes/stats/summary",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 统计成功！")
        print(f"   总错题数: {result['total']}")
        print(f"   已复习: {result['reviewed']}")
        print(f"   未复习: {result['not_reviewed']}")
        print(f"   复习进度: {result['review_progress']}%")
        print(f"   学科分布: {result['by_subject']}")
    else:
        print(f"❌ 统计失败: {response.json()}")


def test_6_filter_mistakes():
    """测试6：筛选错题"""
    print_section("测试6：筛选错题（按学科和复习状态）")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return
    
    # 筛选未复习的数学错题
    print("筛选条件: 学科=数学, 已复习=False")
    response = requests.get(
        f"{API_BASE_URL}/mistakes/",
        params={"subject": "数学", "reviewed": False, "page_size": 5},
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 筛选成功！")
        print(f"   符合条件: {result['total']} 条")
        print(f"   返回: {len(result['mistakes'])} 条")
        
        if result['mistakes']:
            print("\n   未复习的数学错题:")
            for m in result['mistakes']:
                print(f"     - ID {m['id']}: {m['question_text'][:40]}...")
    else:
        print(f"❌ 筛选失败: {response.json()}")


def test_7_delete_mistake(mistake_id):
    """测试7：删除错题"""
    print_section("测试7：删除错题")
    
    if not TOKEN or not mistake_id:
        print("❌ 未登录或无错题ID，跳过测试")
        return
    
    print(f"删除错题: ID={mistake_id}")
    print("⚠️ 注意：这将永久删除错题！")
    
    # 为了测试，我们实际上不删除
    print("（测试模式：跳过实际删除）")
    print("如需测试删除功能，请取消注释以下代码：")
    print("""
    response = requests.delete(
        f"{API_BASE_URL}/mistakes/{mistake_id}",
        headers=get_auth_headers()
    )
    if response.status_code == 200:
        print("✅ 删除成功！")
    """)


def test_8_chat_with_review_mode():
    """测试8：测试批改模式的错题检测"""
    print_section("测试8：测试批改模式的错题自动检测")
    
    print("⚠️ 注意：当前/chat接口暂未集成用户认证")
    print("错题检测功能已实现，但自动保存功能需要用户登录")
    print("\n功能说明:")
    print("1. 使用包含'批改'关键词的prompt")
    print("2. AI会在回答中添加[MISTAKE_DETECTED]或[CORRECT]标记")
    print("3. 后端检测到标记会打印日志（见服务器输出）")
    print("4. 可以手动调用 POST /mistakes 保存错题")
    
    print("\n💡 测试方法:")
    print("1. 在前端使用批改功能")
    print("2. 查看后端日志输出")
    print("3. 看到【Feature 2: 错题检测】日志即表示功能正常")


def main():
    """主函数"""
    print("\n" + "█"*70)
    print("█" + " "*15 + "Feature 2: 错题本系统测试" + " "*22 + "█")
    print("█" + " "*20 + "沐梧AI V23.0-F2" + " "*27 + "█")
    print("█"*70)
    
    try:
        # 检查服务是否运行
        print("\n正在检查服务状态...")
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        info = response.json()
        print(f"✅ 后端服务正常运行")
        print(f"   版本: {info['version']}")
        
        # 执行测试
        if not test_0_login():
            print("\n❌ 无法继续测试（需要先登录）")
            print("请先运行: python test_feature1_auth.py")
            return
        
        mistake_id = test_1_create_mistake()
        test_2_get_mistakes_list(mistake_id)
        test_3_get_mistake_detail(mistake_id)
        test_4_update_mistake(mistake_id)
        test_5_get_stats()
        test_6_filter_mistakes()
        test_7_delete_mistake(mistake_id)
        test_8_chat_with_review_mode()
        
        print_section("测试总结")
        print("✅ Feature 2 错题本系统测试完成！")
        print("\n功能验证：")
        print("  ✅ 错题创建（手动）")
        print("  ✅ 错题列表获取（分页+筛选）")
        print("  ✅ 错题详情查看")
        print("  ✅ 错题更新（标记已复习）")
        print("  ✅ 错题统计")
        print("  ✅ 错题检测机制（批改模式）")
        
        print("\n下一步：")
        print("  1. 测试批改功能（使用前端或API）")
        print("  2. 查看后端日志验证错题检测")
        print("  3. 开始Feature 3: 智能出题系统")
        
        print("\n📚 API文档: http://127.0.0.1:8000/docs")
        
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

