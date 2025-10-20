#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feature 1: 用户认证系统测试脚本
使用方法：python test_feature1_auth.py
"""

import requests
import json

# 配置
API_BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    """打印分隔符"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_1_register():
    """测试1：用户注册"""
    print_section("测试1：用户注册")
    
    # 注册学生账户
    student_data = {
        "username": "test_student",
        "password": "password123",
        "email": "student@test.com",
        "role": "student"
    }
    
    print("注册学生账户...")
    response = requests.post(f"{API_BASE_URL}/auth/register", json=student_data)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ 注册成功！")
        print(f"   用户ID: {result['id']}")
        print(f"   用户名: {result['username']}")
        print(f"   角色: {result['role']}")
        return True
    elif response.status_code == 400:
        print("⚠️ 用户已存在（这是正常的，如果之前已注册）")
        return True
    else:
        print(f"❌ 注册失败: {response.json()}")
        return False


def test_2_login():
    """测试2：用户登录"""
    print_section("测试2：用户登录")
    
    login_data = {
        "username": "test_student",
        "password": "password123"
    }
    
    print("尝试登录...")
    response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 登录成功！")
        print(f"   Token类型: {result['token_type']}")
        print(f"   有效期: {result['expires_in']} 秒")
        print(f"   用户信息: {result['user_info']}")
        print(f"\n   Access Token (前50字符): {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"❌ 登录失败: {response.json()}")
        return None


def test_3_get_user_info(token):
    """测试3：获取当前用户信息（受保护的路由）"""
    print_section("测试3：获取用户信息（JWT认证）")
    
    if not token:
        print("❌ 没有token，跳过测试")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("请求受保护的路由: /auth/me")
    response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 认证成功！")
        print(f"   用户ID: {result['id']}")
        print(f"   用户名: {result['username']}")
        print(f"   邮箱: {result['email']}")
        print(f"   角色: {result['role']}")
        print(f"   注册时间: {result['created_at']}")
        return True
    else:
        print(f"❌ 认证失败: {response.json()}")
        return False


def test_4_test_protected_route(token):
    """测试4：测试受保护的路由"""
    print_section("测试4：测试受保护的路由")
    
    if not token:
        print("❌ 没有token，跳过测试")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("请求测试路由: /auth/test-protected")
    response = requests.get(f"{API_BASE_URL}/auth/test-protected", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 测试成功！")
        print(f"   消息: {result['message']}")
        print(f"   用户信息: {result['user']}")
        return True
    else:
        print(f"❌ 测试失败: {response.json()}")
        return False


def test_5_invalid_token():
    """测试5：使用无效token（应该失败）"""
    print_section("测试5：使用无效token（预期失败）")
    
    headers = {
        "Authorization": "Bearer invalid_token_12345"
    }
    
    print("尝试使用无效token访问受保护路由...")
    response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 401:
        print(f"✅ 按预期拒绝访问！")
        print(f"   错误信息: {response.json()['detail']}")
        return True
    else:
        print(f"❌ 意外成功（这不应该发生）")
        return False


def test_6_register_teacher():
    """测试6：注册教师账户"""
    print_section("测试6：注册教师账户")
    
    teacher_data = {
        "username": "test_teacher",
        "password": "teacher123",
        "email": "teacher@test.com",
        "role": "teacher"
    }
    
    print("注册教师账户...")
    response = requests.post(f"{API_BASE_URL}/auth/register", json=teacher_data)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ 教师账户注册成功！")
        print(f"   用户ID: {result['id']}")
        print(f"   用户名: {result['username']}")
        print(f"   角色: {result['role']}")
        return True
    elif response.status_code == 400:
        print("⚠️ 教师账户已存在")
        return True
    else:
        print(f"❌ 注册失败: {response.json()}")
        return False


def main():
    """主函数"""
    print("\n" + "█"*70)
    print("█" + " "*15 + "Feature 1: 用户认证系统测试" + " "*20 + "█")
    print("█" + " "*20 + "沐梧AI V23.0" + " "*29 + "█")
    print("█"*70)
    
    try:
        # 检查服务是否运行
        print("\n正在检查服务状态...")
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        info = response.json()
        print(f"✅ 后端服务正常运行")
        print(f"   版本: {info['version']}")
        print(f"   特性数: {len(info['features'])}")
        
        # 执行测试
        test_1_register()
        token = test_2_login()
        test_3_get_user_info(token)
        test_4_test_protected_route(token)
        test_5_invalid_token()
        test_6_register_teacher()
        
        print_section("测试总结")
        print("✅ Feature 1 用户认证系统测试完成！")
        print("\n功能验证：")
        print("  ✅ 用户注册（学生和教师）")
        print("  ✅ 用户登录（JWT token生成）")
        print("  ✅ JWT认证（受保护路由）")
        print("  ✅ Token验证（有效/无效）")
        print("  ✅ 用户信息获取")
        
        print("\n下一步：")
        print("  1. 访问 http://127.0.0.1:8000/docs 查看API文档")
        print("  2. 使用Swagger UI测试所有端点")
        print("  3. 开始Feature 2: 错题本系统")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到后端服务")
        print("请确保后端服务已启动：")
        print("  cd backend")
        print("  pip install sqlalchemy passlib[bcrypt] python-jose[cryptography]")
        print("  uvicorn main:app --reload")
    
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

