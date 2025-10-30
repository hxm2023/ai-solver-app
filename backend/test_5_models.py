"""
快速测试5大模型API连接
运行方式：python test_5_models.py
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置
try:
    import config_api_models as config
except ImportError:
    print("❌ 错误：找不到 config_api_models.py")
    print("请确保该文件存在于 backend/ 目录下")
    sys.exit(1)

from model_adapter import get_multimodal_adapter, get_text_adapter


def test_model_connection(model_key: str):
    """测试指定模型的API连接"""
    print(f"\n{'='*70}")
    print(f"正在测试模型: {model_key}")
    print(f"{'='*70}")
    
    # 临时切换模型
    original_key = config.ACTIVE_MODEL_KEY
    config.ACTIVE_MODEL_KEY = model_key
    
    try:
        # 获取模型配置
        model_config = config.get_active_model_config()
        print(f"✅ 配置加载成功")
        print(f"   描述: {model_config['description']}")
        print(f"   类型: {model_config['type']}")
        print(f"   提供商: {model_config.get('provider', '未知')}")
        
        if model_config['type'] == 'openai_compatible':
            print(f"   API地址: {model_config['api_base']}")
        
        # 构造测试消息
        test_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "你好，请简短回答：1+1等于几？"}
                ]
            }
        ]
        
        print(f"\n🔄 正在调用API...")
        
        # 调用模型
        adapter = get_multimodal_adapter()
        full_response = ""
        
        for chunk in adapter.call(test_messages, stream=True):
            content = chunk.get('content', '')
            full_response += content
            # 打印前50个字符作为预览
            if len(full_response) <= 50:
                print(content, end='', flush=True)
        
        print(f"\n\n✅ API调用成功！")
        print(f"   响应长度: {len(full_response)} 字符")
        print(f"   响应预览: {full_response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        
        # 提供排查建议
        if "API" in str(e) or "key" in str(e).lower():
            print("\n💡 排查建议:")
            print("   1. 检查 .env 文件中的API密钥是否正确配置")
            print("   2. 确认API密钥有效且未过期")
            print("   3. 检查网络连接是否正常")
        
        return False
        
    finally:
        # 恢复原始配置
        config.ACTIVE_MODEL_KEY = original_key


def test_all_models():
    """测试所有5个模型"""
    print("\n" + "="*70)
    print("沐梧AI解题系统 - 5大模型API连接测试")
    print("="*70)
    
    models = [
        "qwen-vl-max",
        "qwen3-vl-32b-thinking",
        "qwen3-vl-32b-instruct",
        "qwen3-vl-235b-a22b-thinking",
        "qwen3-vl-235b-a22b-instruct",
    ]
    
    results = {}
    
    for model_key in models:
        success = test_model_connection(model_key)
        results[model_key] = success
    
    # 显示测试总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70 + "\n")
    
    for model_key, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} {model_key}")
    
    # 统计
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n总计: {success_count}/{total_count} 个模型连接成功")
    
    if success_count == total_count:
        print("\n🎉 恭喜！所有模型API都配置正确！")
        print("现在可以开始进行评测了。")
    elif success_count > 0:
        print("\n⚠️  部分模型配置成功，可以先测试已配置的模型。")
        print("未配置的模型可以稍后再补充API密钥。")
    else:
        print("\n❌ 没有任何模型配置成功，请检查 .env 文件配置。")
        print("参考 .env.example.api_models 文件进行配置。")


def test_single_model():
    """测试当前激活的单个模型"""
    print("\n" + "="*70)
    print("测试当前激活的模型")
    print("="*70)
    
    current_model = config.ACTIVE_MODEL_KEY
    test_model_connection(current_model)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试5大模型API连接")
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="测试所有5个模型"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        help="测试指定的模型"
    )
    
    args = parser.parse_args()
    
    if args.all:
        test_all_models()
    elif args.model:
        test_model_connection(args.model)
    else:
        # 默认测试当前激活的模型
        test_single_model()
        
        print("\n" + "="*70)
        print("💡 提示:")
        print("   - 测试所有模型: python test_5_models.py --all")
        print("   - 测试指定模型: python test_5_models.py --model qwen3-vl-32b-thinking")
        print("="*70 + "\n")

