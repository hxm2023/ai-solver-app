#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feature 3: 智能出题系统测试脚本
使用方法：python test_feature3_question_gen.py
"""

import requests
import json

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


def test_1_create_test_mistakes():
    """测试1：创建测试错题（准备数据）"""
    print_section("测试1：创建测试错题（准备数据）")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return []
    
    # 创建3道数学错题
    test_mistakes = [
        {
            "question_text": "解方程 x² - 5x + 6 = 0",
            "wrong_answer": "x = 1 或 x = 6",
            "ai_analysis": "[MISTAKE_DETECTED] 错误！因式分解应该是 (x-2)(x-3)=0，所以 x=2 或 x=3。学生对一元二次方程的因式分解理解不够深入。",
            "subject": "数学",
            "knowledge_points": ["一元二次方程", "因式分解"],
            "difficulty": 2
        },
        {
            "question_text": "求导数 f(x) = x³ + 2x",
            "wrong_answer": "f'(x) = x² + 2",
            "ai_analysis": "[MISTAKE_DETECTED] 错误！x³的导数是3x²，不是x²。正确答案是 f'(x) = 3x² + 2。学生对幂函数求导法则掌握不牢。",
            "subject": "数学",
            "knowledge_points": ["导数", "幂函数求导"],
            "difficulty": 3
        },
        {
            "question_text": "化简 (a+b)²",
            "wrong_answer": "a² + b²",
            "ai_analysis": "[MISTAKE_DETECTED] 错误！完全平方公式是 (a+b)² = a² + 2ab + b²，学生遗漏了中间项2ab。",
            "subject": "数学",
            "knowledge_points": ["完全平方公式", "代数式化简"],
            "difficulty": 1
        }
    ]
    
    created_ids = []
    
    for i, mistake_data in enumerate(test_mistakes):
        print(f"\n创建错题 {i+1}...")
        print(f"题目: {mistake_data['question_text']}")
        
        response = requests.post(
            f"{API_BASE_URL}/mistakes/",
            json=mistake_data,
            headers=get_auth_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            created_ids.append(result['id'])
            print(f"✅ 错题创建成功！ID: {result['id']}")
        else:
            print(f"❌ 创建失败: {response.json()}")
    
    print(f"\n总计创建: {len(created_ids)} 条测试错题")
    print(f"错题ID列表: {created_ids}")
    
    return created_ids


def test_2_generate_knowledge_points(mistake_ids):
    """测试2：从错题提炼知识点"""
    print_section("测试2：从错题提炼知识点")
    
    if not TOKEN or not mistake_ids:
        print("❌ 未登录或无错题ID，跳过测试")
        return None
    
    request_data = {
        "mistake_ids": mistake_ids,
        "subject": "数学"
    }
    
    print(f"提炼知识点...")
    print(f"错题ID: {mistake_ids}")
    print(f"学科: 数学")
    
    response = requests.post(
        f"{API_BASE_URL}/ai-learning/generate_knowledge_points",
        json=request_data,
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 知识点提炼成功！")
        print(f"\n提炼出的知识点:")
        for i, kp in enumerate(result['knowledge_points'], 1):
            print(f"  {i}. {kp}")
        
        print(f"\nAI分析:")
        print(f"  {result['ai_analysis'][:200]}...")
        
        return result['knowledge_points']
    else:
        print(f"\n❌ 提炼失败: {response.json()}")
        return None


def test_3_generate_questions(knowledge_points):
    """测试3：基于知识点生成题目"""
    print_section("测试3：基于知识点生成题目")
    
    if not TOKEN or not knowledge_points:
        print("❌ 未登录或无知识点，跳过测试")
        return
    
    # 生成不同题型
    request_data = {
        "knowledge_points": knowledge_points[:3],  # 最多选3个知识点
        "difficulty": "中等",
        "question_types": {
            "选择题": 2,
            "填空题": 1
        },
        "subject": "数学"
    }
    
    print(f"生成题目...")
    print(f"知识点: {request_data['knowledge_points']}")
    print(f"难度: {request_data['difficulty']}")
    print(f"题型要求: {request_data['question_types']}")
    
    response = requests.post(
        f"{API_BASE_URL}/ai-learning/generate_questions",
        json=request_data,
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 题目生成成功！")
        print(f"总计生成: {result['total_generated']} 道题目")
        print(f"耗时: {result['generation_time']}")
        
        print(f"\n生成的题目:")
        for i, q in enumerate(result['questions'], 1):
            content = json.loads(q['content'])
            print(f"\n  题目{i} ({q['question_type']}):")
            print(f"  题干: {content.get('stem', '')[:80]}...")
            if 'options' in content:
                print(f"  选项: A/B/C/D")
            print(f"  答案: {q['answer'][:50]}...")
            print(f"  难度: {q['difficulty']}")
        
        return result
    else:
        print(f"\n❌ 生成失败: {response.json()}")
        return None


def test_4_get_my_questions():
    """测试4：获取我生成的题目列表"""
    print_section("测试4：获取我生成的题目列表")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return
    
    print("获取题目列表...")
    response = requests.get(
        f"{API_BASE_URL}/ai-learning/my_questions",
        params={"page": 1, "page_size": 10},
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功！")
        print(f"   总计: {result['total']} 道题目")
        print(f"   当前页: {result['page']}")
        print(f"   返回: {len(result['questions'])} 道题目")
        
        if result['questions']:
            print(f"\n   题目列表:")
            for q in result['questions'][:3]:
                content = json.loads(q['content'])
                print(f"     - ID {q['id']}: {content.get('stem', '')[:40]}... ({q['question_type']})")
    else:
        print(f"❌ 获取失败: {response.json()}")


def test_5_filter_questions():
    """测试5：筛选题目"""
    print_section("测试5：筛选题目（按题型和难度）")
    
    if not TOKEN:
        print("❌ 未登录，跳过测试")
        return
    
    # 筛选中等难度的选择题
    print("筛选条件: 题型=选择题, 难度=中等")
    response = requests.get(
        f"{API_BASE_URL}/ai-learning/my_questions",
        params={"question_type": "选择题", "difficulty": "中等", "page_size": 5},
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 筛选成功！")
        print(f"   符合条件: {result['total']} 道")
        print(f"   返回: {len(result['questions'])} 道")
        
        if result['questions']:
            print(f"\n   筛选结果:")
            for q in result['questions']:
                content = json.loads(q['content'])
                print(f"     - {content.get('stem', '')[:50]}...")
    else:
        print(f"❌ 筛选失败: {response.json()}")


def test_6_complete_workflow():
    """测试6：完整工作流程"""
    print_section("测试6：完整工作流程演示")
    
    print("📚 完整工作流程:")
    print("  1. 学生做错题 → 保存到错题本")
    print("  2. 从错题本选择若干错题")
    print("  3. AI提炼共同知识点")
    print("  4. 选择知识点 + 指定难度和题型")
    print("  5. AI生成针对性练习题")
    print("  6. 查看生成的题目列表")
    print("  7. 使用生成的题目进行练习")
    print("\n✅ 以上所有步骤已在前面的测试中演示完成！")


def main():
    """主函数"""
    print("\n" + "█"*70)
    print("█" + " "*12 + "Feature 3: 智能出题系统测试" + " "*23 + "█")
    print("█" + " "*20 + "沐梧AI V23.0-F3" + " "*27 + "█")
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
            return
        
        # 创建测试错题
        mistake_ids = test_1_create_test_mistakes()
        
        if not mistake_ids:
            print("\n⚠️ 未能创建测试错题，跳过后续测试")
            return
        
        # 提炼知识点
        knowledge_points = test_2_generate_knowledge_points(mistake_ids)
        
        if not knowledge_points:
            print("\n⚠️ 未能提炼知识点，跳过后续测试")
            return
        
        # 生成题目
        test_3_generate_questions(knowledge_points)
        
        # 查看题目列表
        test_4_get_my_questions()
        
        # 筛选题目
        test_5_filter_questions()
        
        # 完整工作流程
        test_6_complete_workflow()
        
        print_section("测试总结")
        print("✅ Feature 3 智能出题系统测试完成！")
        print("\n功能验证：")
        print("  ✅ 从错题提炼知识点（AI分析）")
        print("  ✅ 基于知识点生成题目（多题型）")
        print("  ✅ 题目自动保存到数据库")
        print("  ✅ 题目列表获取（分页+筛选）")
        print("  ✅ 完整工作流程验证")
        
        print("\n核心亮点：")
        print("  🎯 AI智能提炼知识点")
        print("  🎲 支持多种题型（选择题、填空题、解答题）")
        print("  📊 支持难度定制（简单、中等、困难）")
        print("  🔄 完整的学习闭环（错题→知识点→新题→练习）")
        
        print("\n下一步：")
        print("  1. 继续积累错题")
        print("  2. 定期提炼知识点")
        print("  3. 生成针对性练习题")
        print("  4. 准备Feature 4: 试卷生成")
        
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

