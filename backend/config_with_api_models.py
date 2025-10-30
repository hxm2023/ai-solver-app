"""
==============================================================================
沐梧AI解题系统 - 大模型配置中心（API版本）
==============================================================================
功能：
- 支持通过API调用开源模型
- 无需本地GPU部署
- 多种API服务商可选
==============================================================================
"""

import os
from typing import Dict, Any, Literal
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 核心配置：修改此变量以切换全局使用的模型
# ==============================================================================

# 当前激活的模型
ACTIVE_MODEL_KEY = "qwen-vl-max"  # 默认使用闭源基准模型

# 可选模型（通过API调用，无需本地部署）:
# ACTIVE_MODEL_KEY = "qwen-vl-plus"              # 阿里云开源版API
# ACTIVE_MODEL_KEY = "qwen2-vl-72b"              # 阿里云72B版本
# ACTIVE_MODEL_KEY = "qwen-vl-7b-siliconflow"    # SiliconFlow提供
# ACTIVE_MODEL_KEY = "qwen-vl-72b-together"      # Together AI提供

# ==============================================================================
# 模型配置字典
# ==============================================================================

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ----------------------------------------------------------------------
    # 阿里云DashScope API（闭源和开源都支持）
    # ----------------------------------------------------------------------
    "qwen-vl-max": {
        "type": "dashscope_api",
        "model_name": "qwen-vl-max",
        "api_key_env": "DASHSCOPE_API_KEY",
        "description": "通义千问VL Max - 闭源旗舰版",
        "capabilities": ["multimodal", "streaming", "high_accuracy"],
        "cost_tier": "high",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "阿里云DashScope",
    },
    
    "qwen-vl-plus": {
        "type": "dashscope_api",
        "model_name": "qwen-vl-plus",
        "api_key_env": "DASHSCOPE_API_KEY",
        "description": "通义千问VL Plus - 性价比开源版（API）",
        "capabilities": ["multimodal", "streaming", "cost_effective"],
        "cost_tier": "medium",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "阿里云DashScope",
        "pricing": "约0.002元/千tokens（比Max便宜70%）",
    },
    
    "qwen2-vl-72b": {
        "type": "dashscope_api",
        "model_name": "qwen2-vl-72b-instruct",
        "api_key_env": "DASHSCOPE_API_KEY",
        "description": "Qwen2-VL 72B Instruct - 高性能开源（API）",
        "capabilities": ["multimodal", "streaming", "high_performance"],
        "cost_tier": "medium",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "阿里云DashScope",
        "pricing": "约0.004元/千tokens",
    },
    
    # ----------------------------------------------------------------------
    # SiliconFlow API（超便宜，推荐）
    # ----------------------------------------------------------------------
    "qwen-vl-7b-siliconflow": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen2-VL-7B-Instruct",
        "api_base": "https://api.siliconflow.cn/v1",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "description": "Qwen2-VL 7B - SiliconFlow超低价API",
        "capabilities": ["multimodal", "streaming", "ultra_low_cost"],
        "cost_tier": "very_low",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "SiliconFlow",
        "pricing": "约0.0007元/千tokens（超便宜！）",
        "signup_url": "https://cloud.siliconflow.cn/",
    },
    
    "qwen-vl-72b-siliconflow": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen2-VL-72B-Instruct",
        "api_base": "https://api.siliconflow.cn/v1",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "description": "Qwen2-VL 72B - SiliconFlow低价API",
        "capabilities": ["multimodal", "streaming", "low_cost"],
        "cost_tier": "low",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "SiliconFlow",
        "pricing": "约0.0035元/千tokens",
    },
    
    # ----------------------------------------------------------------------
    # Together AI（国际化，稳定）
    # ----------------------------------------------------------------------
    "qwen-vl-72b-together": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen2-VL-72B-Instruct",
        "api_base": "https://api.together.xyz/v1",
        "api_key": os.getenv("TOGETHER_API_KEY", ""),
        "description": "Qwen2-VL 72B - Together AI国际服务",
        "capabilities": ["multimodal", "streaming", "international"],
        "cost_tier": "medium",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "Together AI",
        "pricing": "$0.001/千tokens",
        "signup_url": "https://www.together.ai/",
    },
    
    # ----------------------------------------------------------------------
    # DeepInfra（备选方案）
    # ----------------------------------------------------------------------
    "qwen-vl-7b-deepinfra": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen2-VL-7B-Instruct",
        "api_base": "https://api.deepinfra.com/v1/openai",
        "api_key": os.getenv("DEEPINFRA_API_KEY", ""),
        "description": "Qwen2-VL 7B - DeepInfra稳定服务",
        "capabilities": ["multimodal", "streaming", "stable"],
        "cost_tier": "low",
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "DeepInfra",
        "pricing": "$0.0006/千tokens",
        "signup_url": "https://deepinfra.com/",
    },
    
    # ----------------------------------------------------------------------
    # 本地/远程vLLM部署（可选）
    # ----------------------------------------------------------------------
    "qwen3-vl-32b-local": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen3-VL-32B-Instruct",
        "api_base": os.getenv("LOCAL_MODEL_API_BASE", "http://localhost:8001/v1"),
        "api_key": "EMPTY",
        "description": "Qwen3-VL 32B - 本地/远程vLLM部署",
        "capabilities": ["multimodal", "streaming", "self_hosted"],
        "cost_tier": "zero",  # 自己部署，只有硬件成本
        "max_tokens": 8192,
        "temperature": 0.7,
        "provider": "自部署vLLM",
        "note": "需要GPU服务器，适合大规模使用",
    },
}

# ==============================================================================
# 配置获取函数
# ==============================================================================

def get_active_model_config() -> Dict[str, Any]:
    """获取当前激活的模型配置"""
    if ACTIVE_MODEL_KEY not in MODEL_CONFIGS:
        raise ValueError(
            f"未知的模型KEY: {ACTIVE_MODEL_KEY}. "
            f"可用的模型: {list(MODEL_CONFIGS.keys())}"
        )
    
    config = MODEL_CONFIGS[ACTIVE_MODEL_KEY].copy()
    
    # 如果是Dashscope API，加载API Key
    if config["type"] == "dashscope_api":
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(f"环境变量 {config['api_key_env']} 未设置！")
        config["api_key"] = api_key
    
    # 如果是OpenAI兼容API，验证api_key
    elif config["type"] == "openai_compatible":
        if not config.get("api_key"):
            print(f"⚠️  警告: {ACTIVE_MODEL_KEY} 的API密钥未设置")
    
    return config


def get_model_info() -> str:
    """获取当前模型的友好描述信息"""
    config = get_active_model_config()
    
    info = [
        f"[当前模型] {ACTIVE_MODEL_KEY}",
        f"  描述: {config['description']}",
        f"  提供商: {config.get('provider', '未知')}",
        f"  类型: {config['type']}",
        f"  成本等级: {config['cost_tier']}",
    ]
    
    if 'pricing' in config:
        info.append(f"  价格: {config['pricing']}")
    
    if 'signup_url' in config:
        info.append(f"  注册地址: {config['signup_url']}")
    
    info.append(f"  能力: {', '.join(config['capabilities'])}")
    
    return "\n".join(info)


def list_api_models_by_provider():
    """按服务商列出所有API模型"""
    print("=" * 70)
    print("可用的API模型（按服务商分类）")
    print("=" * 70 + "\n")
    
    providers = {}
    for key, config in MODEL_CONFIGS.items():
        provider = config.get('provider', '未知')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append((key, config))
    
    for provider, models in providers.items():
        print(f"🏢 {provider}")
        print("-" * 70)
        for key, config in models:
            is_active = "✓ [当前]" if key == ACTIVE_MODEL_KEY else "  "
            pricing = config.get('pricing', '价格未知')
            print(f"{is_active} {key}")
            print(f"    {config['description']}")
            print(f"    价格: {pricing}")
            if 'signup_url' in config:
                print(f"    注册: {config['signup_url']}")
            print()
        print()


def recommend_model_by_scenario():
    """根据使用场景推荐模型"""
    print("=" * 70)
    print("使用场景推荐")
    print("=" * 70 + "\n")
    
    recommendations = {
        "💰 极致成本优化": "qwen-vl-7b-siliconflow（0.0007元/千tokens）",
        "⚖️  性价比平衡": "qwen-vl-plus（阿里云，稳定可靠）",
        "🚀 高性能需求": "qwen2-vl-72b（72B参数，推理能力强）",
        "🌍 国际化部署": "qwen-vl-72b-together（Together AI）",
        "🔒 数据安全/大规模": "qwen3-vl-32b-local（自部署）",
        "🧪 开发测试": "qwen-vl-7b-siliconflow（便宜快速）",
    }
    
    for scenario, model in recommendations.items():
        print(f"{scenario}")
        print(f"  推荐: {model}\n")


# ==============================================================================
# 知识点提取模型配置（保持不变）
# ==============================================================================

KNOWLEDGE_EXTRACTION_MODEL = "qwen-turbo"

KNOWLEDGE_EXTRACTION_CONFIGS = {
    "qwen-turbo": {
        "type": "dashscope_api",
        "model_name": "qwen-turbo",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
}

def get_knowledge_extraction_config() -> Dict[str, Any]:
    """获取知识点提取模型配置"""
    config = KNOWLEDGE_EXTRACTION_CONFIGS[KNOWLEDGE_EXTRACTION_MODEL].copy()
    if config["type"] == "dashscope_api":
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(f"环境变量 {config['api_key_env']} 未设置！")
        config["api_key"] = api_key
    return config


# ==============================================================================
# 运行时测试
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("沐梧AI解题系统 - 模型配置测试（API版本）")
    print("=" * 70 + "\n")
    
    # 显示所有API模型
    list_api_models_by_provider()
    
    # 显示使用场景推荐
    recommend_model_by_scenario()
    
    # 显示当前激活的模型
    print("=" * 70)
    print(get_model_info())
    print("=" * 70)
    
    # 测试配置获取
    try:
        config = get_active_model_config()
        print("\n✅ 配置加载成功！")
        print(f"   模型名称: {config['model_name']}")
        print(f"   API类型: {config['type']}")
        if config['type'] == 'openai_compatible':
            print(f"   API地址: {config['api_base']}")
    except Exception as e:
        print(f"\n❌ 配置加载失败: {e}")

