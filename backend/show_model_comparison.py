"""
5大模型对比查看工具
快速查看模型配置、价格、能力对比
"""

import os
from config_api_models import MODEL_CONFIGS, ACTIVE_MODEL_KEY

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def show_price_comparison():
    """显示价格对比"""
    print_header("💰 价格对比")
    
    print("模型名称".ljust(35) + "价格".ljust(20) + "相对成本".ljust(15) + "节省")
    print("-" * 80)
    
    base_price = 0.008  # qwen-vl-max的价格作为基准
    
    for key, config in MODEL_CONFIGS.items():
        is_active = "✅" if key == ACTIVE_MODEL_KEY else "  "
        name = f"{is_active} {key}"
        
        pricing = config.get('pricing', '未知')
        
        # 提取价格数字进行计算
        if '0.008' in pricing:
            price_val = 0.008
        elif '0.003' in pricing:
            price_val = 0.003
        elif '0.006' in pricing:
            price_val = 0.006
        else:
            price_val = 0
        
        relative_cost = (price_val / base_price * 100) if price_val > 0 else 0
        savings = 100 - relative_cost if price_val > 0 else 0
        
        relative_str = f"{relative_cost:.1f}%" if price_val > 0 else "N/A"
        savings_str = f"节省{savings:.1f}%" if savings > 0 else "基准"
        
        print(
            name.ljust(35) + 
            pricing.ljust(20) + 
            relative_str.ljust(15) + 
            savings_str
        )


def show_capability_comparison():
    """显示能力对比"""
    print_header("✨ 能力对比")
    
    print("模型名称".ljust(35) + "核心能力")
    print("-" * 80)
    
    for key, config in MODEL_CONFIGS.items():
        is_active = "✅" if key == ACTIVE_MODEL_KEY else "  "
        name = f"{is_active} {key}"
        capabilities = ', '.join(config.get('capabilities', []))
        
        print(f"{name.ljust(35)} {capabilities}")
        
        # 显示特殊标记
        if config.get('thinking_mode'):
            print(" " * 35 + "  🧠 思考链模式")
        if config.get('ocr_enhanced'):
            print(" " * 35 + "  📷 OCR增强")


def show_provider_comparison():
    """显示服务商对比"""
    print_header("🏢 服务商对比")
    
    providers = {}
    for key, config in MODEL_CONFIGS.items():
        provider = config.get('provider', '未知')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append((key, config))
    
    for provider, models in providers.items():
        print(f"\n📌 {provider}")
        print("-" * 80)
        
        for key, config in models:
            is_active = "✅" if key == ACTIVE_MODEL_KEY else "  "
            name = f"{is_active} {key}"
            desc = config.get('description', '')
            cost = config.get('cost_tier', '未知')
            
            print(f"{name.ljust(35)} {desc}")
            print(" " * 35 + f"成本等级: {cost}")


def show_recommendation():
    """显示使用推荐"""
    print_header("💡 使用场景推荐")
    
    recommendations = [
        ("🎯 日常批改作业（高频）", "qwen3-vl-32b-instruct", "成本最低，响应快"),
        ("🧮 复杂题目解答（中频）", "qwen3-vl-235b-a22b-thinking", "推理能力强，准确率高"),
        ("📝 生成试卷（低频）", "qwen-vl-max", "质量最优，可靠性高"),
        ("💰 极致成本优化", "qwen3-vl-32b-thinking", "节省62.5%成本"),
        ("🚀 高性能追求", "qwen3-vl-235b-a22b-instruct", "性能最强"),
    ]
    
    for scenario, model, reason in recommendations:
        print(f"{scenario}")
        print(f"  推荐模型: {model}")
        print(f"  原因: {reason}\n")


def show_current_model():
    """显示当前激活的模型"""
    print_header("🎯 当前激活的模型")
    
    config = MODEL_CONFIGS[ACTIVE_MODEL_KEY]
    
    print(f"模型名称: {ACTIVE_MODEL_KEY}")
    print(f"描述: {config.get('description', '无')}")
    print(f"提供商: {config.get('provider', '未知')}")
    print(f"API类型: {config.get('type', '未知')}")
    print(f"成本等级: {config.get('cost_tier', '未知')}")
    print(f"价格: {config.get('pricing', '未知')}")
    print(f"能力: {', '.join(config.get('capabilities', []))}")
    
    if config.get('type') == 'openai_compatible':
        print(f"API地址: {config.get('api_base', '未知')}")
    
    if config.get('thinking_mode'):
        print("🧠 思考链模式: 启用")
    if config.get('ocr_enhanced'):
        print("📷 OCR增强: 启用")


def show_quick_switch_guide():
    """显示快速切换指南"""
    print_header("🔄 快速切换指南")
    
    print("方法1：手动修改配置文件")
    print("-" * 80)
    print("1. 打开 backend/config_api_models.py")
    print("2. 找到第23行：ACTIVE_MODEL_KEY = \"qwen-vl-max\"")
    print("3. 修改为以下任意一个：")
    for i, key in enumerate(MODEL_CONFIGS.keys(), 1):
        print(f"   {i}. ACTIVE_MODEL_KEY = \"{key}\"")
    print("4. 保存文件")
    print("5. 重启后端：python main_db.py")
    
    print("\n方法2：使用一键切换脚本（Windows）")
    print("-" * 80)
    print("运行：【一键切换】模型切换脚本.bat")
    
    print("\n方法3：使用命令行")
    print("-" * 80)
    print("运行：python show_model_comparison.py --switch <模型编号>")


def show_api_key_status():
    """显示API密钥配置状态"""
    print_header("🔑 API密钥配置状态")
    
    print("模型".ljust(35) + "API密钥状态".ljust(20) + "环境变量")
    print("-" * 80)
    
    for key, config in MODEL_CONFIGS.items():
        is_active = "✅" if key == ACTIVE_MODEL_KEY else "  "
        name = f"{is_active} {key}"
        
        if config["type"] == "dashscope_api":
            env_var = config["api_key_env"]
            api_key = os.getenv(env_var)
            status = "✅ 已配置" if api_key else "❌ 未配置"
        elif config["type"] == "openai_compatible":
            api_key = config.get("api_key")
            status = "✅ 已配置" if api_key else "❌ 未配置"
            env_var = "见.env文件"
        else:
            status = "❓ 未知"
            env_var = "N/A"
        
        print(name.ljust(35) + status.ljust(20) + env_var)
    
    print("\n提示：")
    print("  - 如果显示 ❌ 未配置，请在 .env 文件中添加相应的API密钥")
    print("  - 参考 .env.example.api_models 文件进行配置")


def show_all():
    """显示所有信息"""
    show_current_model()
    show_price_comparison()
    show_capability_comparison()
    show_provider_comparison()
    show_recommendation()
    show_quick_switch_guide()
    show_api_key_status()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="5大模型对比查看工具")
    parser.add_argument("--price", action="store_true", help="显示价格对比")
    parser.add_argument("--capability", action="store_true", help="显示能力对比")
    parser.add_argument("--provider", action="store_true", help="显示服务商对比")
    parser.add_argument("--recommend", action="store_true", help="显示使用推荐")
    parser.add_argument("--current", action="store_true", help="显示当前激活的模型")
    parser.add_argument("--guide", action="store_true", help="显示快速切换指南")
    parser.add_argument("--apikey", action="store_true", help="显示API密钥配置状态")
    parser.add_argument("--all", action="store_true", help="显示所有信息")
    
    args = parser.parse_args()
    
    # 如果没有任何参数，显示当前模型和快速帮助
    if not any(vars(args).values()):
        show_current_model()
        print("\n提示：使用 --help 查看所有选项")
        print("  或使用 --all 查看完整对比信息")
    else:
        if args.all:
            show_all()
        else:
            if args.current:
                show_current_model()
            if args.price:
                show_price_comparison()
            if args.capability:
                show_capability_comparison()
            if args.provider:
                show_provider_comparison()
            if args.recommend:
                show_recommendation()
            if args.guide:
                show_quick_switch_guide()
            if args.apikey:
                show_api_key_status()

