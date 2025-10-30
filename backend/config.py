"""
==============================================================================
沐梧AI解题系统 - 大模型配置中心
==============================================================================
功能：
- 统一管理所有大模型配置
- 一键切换不同模型（闭源/开源）
- 支持API调用和本地部署两种模式
==============================================================================
"""

import os
from typing import Dict, Any, Literal
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==============================================================================
# 核心配置：修改此变量以切换全局使用的模型
# ==============================================================================

# 当前激活的模型（修改此行即可切换模型）
#ACTIVE_MODEL_KEY = "qwen-vl-max"  # 默认使用闭源基准模型

# 可选模型列表（取消注释以切换）:
 ACTIVE_MODEL_KEY = "qwen3-vl-32b-thinking"
# ACTIVE_MODEL_KEY = "qwen3-vl-32b-instruct"
# ACTIVE_MODEL_KEY = "qwen3-vl-235b-a22b-thinking"
# ACTIVE_MODEL_KEY = "qwen3-vl-235b-a22b-instruct"

# ==============================================================================
# 模型配置字典
# ==============================================================================

ModelType = Literal["dashscope_api", "local_oss_api", "openai_compatible"]

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ----------------------------------------------------------------------
    # 闭源模型（阿里云Dashscope API）
    # ----------------------------------------------------------------------
    "qwen-vl-max": {
        "type": "dashscope_api",
        "model_name": "qwen-vl-max",
        "api_key_env": "DASHSCOPE_API_KEY",
        "description": "通义千问VL Max - 闭源基准模型",
        "capabilities": ["multimodal", "streaming", "high_accuracy"],
        "cost_tier": "high",  # 相对成本等级
        "max_tokens": 8192,
        "temperature": 0.7,
    },
    
    # ----------------------------------------------------------------------
    # 开源模型 - 32B系列（性价比优选）
    # ----------------------------------------------------------------------
    "qwen3-vl-32b-thinking": {
        "type": "local_oss_api",
        "model_name": "qwen3-vl-32b-thinking",
        "api_base": os.getenv("LOCAL_MODEL_API_BASE", "http://localhost:8001/v1"),
        "api_key": "EMPTY",  # 本地部署不需要真实key
        "description": "Qwen3-VL 32B Thinking版 - 带思考链推理",
        "capabilities": ["multimodal", "streaming", "chain_of_thought"],
        "cost_tier": "low",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": True,  # 启用思考链
        "instruction_following": "high",  # 指令遵循能力强
    },
    
    "qwen3-vl-32b-instruct": {
        "type": "local_oss_api",
        "model_name": "qwen3-vl-32b-instruct",
        "api_base": os.getenv("LOCAL_MODEL_API_BASE", "http://localhost:8001/v1"),
        "api_key": "EMPTY",
        "description": "Qwen3-VL 32B Instruct版 - 直接指令执行",
        "capabilities": ["multimodal", "streaming", "fast_response"],
        "cost_tier": "low",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": False,  # 直接回答模式
        "instruction_following": "very_high",  # SIFO评分最高
    },
    
    # ----------------------------------------------------------------------
    # 开源模型 - 235B-A22B系列（高性能）
    # ----------------------------------------------------------------------
    "qwen3-vl-235b-a22b-thinking": {
        "type": "local_oss_api",
        "model_name": "qwen3-vl-235b-a22b-thinking",
        "api_base": os.getenv("LOCAL_MODEL_API_BASE", "http://localhost:8002/v1"),
        "api_key": "EMPTY",
        "description": "Qwen3-VL 235B-A22B Thinking版 - 高性能推理",
        "capabilities": ["multimodal", "streaming", "advanced_reasoning", "high_ocr"],
        "cost_tier": "medium",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": True,
        "ocr_enhanced": True,  # OCR能力增强
        "reasoning_score": "highest",  # AIME25/LCB性能最佳
    },
    
    "qwen3-vl-235b-a22b-instruct": {
        "type": "local_oss_api",
        "model_name": "qwen3-vl-235b-a22b-instruct",
        "api_base": os.getenv("LOCAL_MODEL_API_BASE", "http://localhost:8002/v1"),
        "api_key": "EMPTY",
        "description": "Qwen3-VL 235B-A22B Instruct版 - 高性能直接执行",
        "capabilities": ["multimodal", "streaming", "advanced_reasoning", "high_ocr"],
        "cost_tier": "medium",
        "max_tokens": 8192,
        "temperature": 0.7,
        "thinking_mode": False,
        "ocr_enhanced": True,
        "reasoning_score": "very_high",
    },
}

# ==============================================================================
# 知识点提取模型配置（文本模型）
# ==============================================================================

# 知识点提取当前使用的模型
KNOWLEDGE_EXTRACTION_MODEL = "qwen-turbo"  # 可选：qwen-turbo, qwen-plus, qwen-max

KNOWLEDGE_EXTRACTION_CONFIGS = {
    "qwen-turbo": {
        "type": "dashscope_api",
        "model_name": "qwen-turbo",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
    "qwen-plus": {
        "type": "dashscope_api",
        "model_name": "qwen-plus",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
}

# ==============================================================================
# 配置获取函数
# ==============================================================================

def get_active_model_config() -> Dict[str, Any]:
    """
    获取当前激活的模型配置
    
    Returns:
        Dict: 包含模型所有配置信息的字典
    
    Raises:
        ValueError: 如果ACTIVE_MODEL_KEY不在配置中
    """
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
    
    return config


def get_knowledge_extraction_config() -> Dict[str, Any]:
    """获取知识点提取模型配置"""
    config = KNOWLEDGE_EXTRACTION_CONFIGS[KNOWLEDGE_EXTRACTION_MODEL].copy()
    
    if config["type"] == "dashscope_api":
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(f"环境变量 {config['api_key_env']} 未设置！")
        config["api_key"] = api_key
    
    return config


def get_model_info() -> str:
    """
    获取当前模型的友好描述信息
    
    Returns:
        str: 模型描述字符串
    """
    config = get_active_model_config()
    return (
        f"[当前模型] {ACTIVE_MODEL_KEY}\n"
        f"  描述: {config['description']}\n"
        f"  类型: {config['type']}\n"
        f"  成本等级: {config['cost_tier']}\n"
        f"  能力: {', '.join(config['capabilities'])}"
    )


def list_all_models() -> None:
    """打印所有可用模型的信息"""
    print("=" * 70)
    print("可用模型列表:")
    print("=" * 70)
    
    for key, config in MODEL_CONFIGS.items():
        is_active = "✓ [当前]" if key == ACTIVE_MODEL_KEY else "  "
        print(f"{is_active} {key}")
        print(f"    {config['description']}")
        print(f"    类型: {config['type']} | 成本: {config['cost_tier']}")
        print()


# ==============================================================================
# API兼容性配置
# ==============================================================================

# OpenAI API兼容格式的默认参数
OPENAI_COMPATIBLE_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 8192,
    "stream": True,
}

# Dashscope API默认参数
DASHSCOPE_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_length": 8192,
    "stream": True,
}

# ==============================================================================
# 运行时测试
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("沐梧AI解题系统 - 模型配置测试")
    print("=" * 70 + "\n")
    
    # 显示所有模型
    list_all_models()
    
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
        if config['type'] == 'local_oss_api':
            print(f"   API地址: {config['api_base']}")
    except Exception as e:
        print(f"\n❌ 配置加载失败: {e}")

