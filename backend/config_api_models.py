"""
==============================================================================
沐梧AI解题系统 - 5大模型API配置中心
==============================================================================
功能：通过修改一行代码切换5个大模型
- qwen-vl-max
- qwen3-vl-32b-thinking  
- qwen3-vl-32b-instruct
- qwen3-vl-235b-a22b-thinking
- qwen3-vl-235b-a22b-instruct
==============================================================================
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 🔥 核心配置：只需修改这一行代码即可切换模型！
# ==============================================================================

ACTIVE_MODEL_KEY = "qwen-vl-max"  

# 切换到其他模型，只需取消下面某一行的注释：
# ACTIVE_MODEL_KEY = "qwen3-vl-32b-thinking"
# ACTIVE_MODEL_KEY = "qwen3-vl-32b-instruct"
# ACTIVE_MODEL_KEY = "qwen3-vl-235b-a22b-thinking"
# ACTIVE_MODEL_KEY = "qwen3-vl-235b-a22b-instruct"

# ==============================================================================
# 模型配置详情
# ==============================================================================

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    
    # ----------------------------------------------------------------------
    # 1. 通义千问VL Max（闭源基准模型）
    # ----------------------------------------------------------------------
    "qwen-vl-max": {
        "type": "dashscope_api",
        "model_name": "qwen-vl-max",
        "api_key_env": "DASHSCOPE_API_KEY",
        "description": "通义千问VL Max - 闭源旗舰版",
        "provider": "阿里云DashScope",
        "capabilities": ["multimodal", "streaming", "high_accuracy"],
        "cost_tier": "high",
        "pricing": "约0.008元/千tokens",
        "max_tokens": 8192,
        "temperature": 0.7,
    },
    
    # ----------------------------------------------------------------------
    # 2. Qwen3-VL-32B-Thinking（开源，带思考链）
    # ----------------------------------------------------------------------
    "qwen3-vl-32b-thinking": {
        "type": "openai_compatible",  # 使用OpenAI兼容API格式
        "model_name": "Qwen/Qwen3-VL-32B-Thinking",  # 实际模型名称
        "api_base": os.getenv("QWEN3_API_BASE", "https://api.siliconflow.cn/v1"),  # API服务地址
        "api_key": os.getenv("QWEN3_API_KEY", ""),  # API密钥
        "description": "Qwen3-VL 32B Thinking版 - 带思考链推理",
        "provider": "API服务商（SiliconFlow/Together AI/自建）",
        "capabilities": ["multimodal", "streaming", "chain_of_thought"],
        "cost_tier": "medium",
        "pricing": "约0.003元/千tokens（具体看服务商）",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": True,
    },
    
    # ----------------------------------------------------------------------
    # 3. Qwen3-VL-32B-Instruct（开源，直接指令）
    # ----------------------------------------------------------------------
    "qwen3-vl-32b-instruct": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen3-VL-32B-Instruct",
        "api_base": os.getenv("QWEN3_API_BASE", "https://api.siliconflow.cn/v1"),
        "api_key": os.getenv("QWEN3_API_KEY", ""),
        "description": "Qwen3-VL 32B Instruct版 - 直接指令执行",
        "provider": "API服务商（SiliconFlow/Together AI/自建）",
        "capabilities": ["multimodal", "streaming", "fast_response"],
        "cost_tier": "medium",
        "pricing": "约0.003元/千tokens",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": False,
    },
    
    # ----------------------------------------------------------------------
    # 4. Qwen3-VL-235B-A22B-Thinking（高性能，带思考链）
    # ----------------------------------------------------------------------
    "qwen3-vl-235b-a22b-thinking": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen3-VL-235B-A22B-Thinking",
        "api_base": os.getenv("QWEN235_API_BASE", "https://api.together.xyz/v1"),  # 大模型通常用Together AI
        "api_key": os.getenv("QWEN235_API_KEY", ""),
        "description": "Qwen3-VL 235B-A22B Thinking版 - 顶级性能推理",
        "provider": "API服务商（Together AI/自建GPU集群）",
        "capabilities": ["multimodal", "streaming", "advanced_reasoning", "high_ocr"],
        "cost_tier": "high",
        "pricing": "约0.006元/千tokens",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": True,
        "ocr_enhanced": True,
    },
    
    # ----------------------------------------------------------------------
    # 5. Qwen3-VL-235B-A22B-Instruct（高性能，直接指令）
    # ----------------------------------------------------------------------
    "qwen3-vl-235b-a22b-instruct": {
        "type": "openai_compatible",
        "model_name": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "api_base": os.getenv("QWEN235_API_BASE", "https://api.together.xyz/v1"),
        "api_key": os.getenv("QWEN235_API_KEY", ""),
        "description": "Qwen3-VL 235B-A22B Instruct版 - 顶级性能直接执行",
        "provider": "API服务商（Together AI/自建GPU集群）",
        "capabilities": ["multimodal", "streaming", "advanced_reasoning", "high_ocr"],
        "cost_tier": "high",
        "pricing": "约0.006元/千tokens",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": False,
        "ocr_enhanced": True,
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
            raise ValueError(f"❌ 环境变量 {config['api_key_env']} 未设置！请在.env文件中配置。")
        config["api_key"] = api_key
    
    # 如果是OpenAI兼容API，验证api_key
    elif config["type"] == "openai_compatible":
        if not config.get("api_key"):
            print(f"⚠️  警告: {ACTIVE_MODEL_KEY} 的API密钥未设置，请在.env文件中配置相应的环境变量。")
    
    return config


def get_model_info() -> str:
    """获取当前模型的详细信息"""
    config = get_active_model_config()
    
    info = [
        "=" * 70,
        f"[当前激活模型] {ACTIVE_MODEL_KEY}",
        "=" * 70,
        f"📝 描述: {config['description']}",
        f"🏢 提供商: {config.get('provider', '未知')}",
        f"🔧 API类型: {config['type']}",
        f"💰 成本等级: {config['cost_tier']}",
        f"💵 价格: {config.get('pricing', '价格未知')}",
        f"✨ 能力: {', '.join(config['capabilities'])}",
    ]
    
    if config['type'] == 'openai_compatible':
        info.append(f"🌐 API地址: {config['api_base']}")
    
    info.append("=" * 70)
    
    return "\n".join(info)


def list_all_models():
    """列出所有可用模型"""
    print("\n" + "=" * 70)
    print("可用的5大模型列表")
    print("=" * 70 + "\n")
    
    for i, (key, config) in enumerate(MODEL_CONFIGS.items(), 1):
        is_active = "✅ [当前使用]" if key == ACTIVE_MODEL_KEY else "  "
        print(f"{i}. {is_active} {key}")
        print(f"   {config['description']}")
        print(f"   提供商: {config.get('provider', '未知')} | 价格: {config.get('pricing', '未知')}")
        print()


def validate_api_keys():
    """验证所有模型的API密钥是否配置"""
    print("\n" + "=" * 70)
    print("API密钥配置检查")
    print("=" * 70 + "\n")
    
    for key, config in MODEL_CONFIGS.items():
        if config["type"] == "dashscope_api":
            api_key = os.getenv(config["api_key_env"])
            status = "✅ 已配置" if api_key else "❌ 未配置"
            print(f"{key}: {status} ({config['api_key_env']})")
        
        elif config["type"] == "openai_compatible":
            api_key = config.get("api_key")
            status = "✅ 已配置" if api_key else "❌ 未配置"
            
            # 从api_base推断环境变量名
            if "siliconflow" in config["api_base"]:
                env_var = "QWEN3_API_KEY (或 SILICONFLOW_API_KEY)"
            elif "together" in config["api_base"]:
                env_var = "QWEN235_API_KEY (或 TOGETHER_API_KEY)"
            else:
                env_var = "自定义API密钥"
            
            print(f"{key}: {status} ({env_var})")
    
    print()


# ==============================================================================
# 知识点提取模型配置
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
# 测试代码
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("沐梧AI解题系统 - 5大模型配置测试")
    print("=" * 70)
    
    # 显示所有模型
    list_all_models()
    
    # 显示当前激活的模型
    print(get_model_info())
    
    # 验证API密钥
    validate_api_keys()
    
    # 测试配置获取
    print("=" * 70)
    print("配置加载测试")
    print("=" * 70 + "\n")
    
    try:
        config = get_active_model_config()
        print(f"✅ 配置加载成功！")
        print(f"   模型名称: {config['model_name']}")
        print(f"   API类型: {config['type']}")
        if config['type'] == 'openai_compatible':
            print(f"   API地址: {config['api_base']}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
    
    print("\n" + "=" * 70)
    print("💡 提示: 修改 ACTIVE_MODEL_KEY 变量即可切换模型")
    print("=" * 70 + "\n")

