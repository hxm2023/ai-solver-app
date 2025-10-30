"""
==============================================================================
沐梧AI解题系统 - 大模型适配器
==============================================================================
功能：
- 统一不同模型的调用接口
- 支持Dashscope API和OpenAI兼容API
- 自动处理格式转换和流式响应
==============================================================================
"""

import os
import json
import httpx
import dashscope
from typing import List, Dict, Any, Generator, Optional
from config import get_active_model_config, get_knowledge_extraction_config


# ==============================================================================
# 消息格式转换
# ==============================================================================

def convert_messages_to_openai_format(messages: List[Dict]) -> List[Dict]:
    """
    将Dashscope格式的消息转换为OpenAI兼容格式
    
    Dashscope格式:
    {
        "role": "user",
        "content": [
            {"image": "data:image/jpeg;base64,..."},
            {"text": "问题文本"}
        ]
    }
    
    OpenAI格式:
    {
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
            {"type": "text", "text": "问题文本"}
        ]
    }
    """
    converted = []
    
    for msg in messages:
        new_msg = {"role": msg["role"]}
        
        # 如果content是字符串，直接使用
        if isinstance(msg["content"], str):
            new_msg["content"] = msg["content"]
        
        # 如果content是列表，需要转换格式
        elif isinstance(msg["content"], list):
            new_content = []
            for item in msg["content"]:
                if "text" in item:
                    new_content.append({
                        "type": "text",
                        "text": item["text"]
                    })
                elif "image" in item:
                    new_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": item["image"]
                        }
                    })
            new_msg["content"] = new_content
        
        converted.append(new_msg)
    
    return converted


def convert_messages_to_dashscope_format(messages: List[Dict]) -> List[Dict]:
    """
    将OpenAI格式转换回Dashscope格式（如果需要）
    """
    converted = []
    
    for msg in messages:
        new_msg = {"role": msg["role"]}
        
        if isinstance(msg["content"], str):
            new_msg["content"] = msg["content"]
        elif isinstance(msg["content"], list):
            new_content = []
            for item in msg["content"]:
                if item.get("type") == "text":
                    new_content.append({"text": item["text"]})
                elif item.get("type") == "image_url":
                    new_content.append({"image": item["image_url"]["url"]})
            new_msg["content"] = new_content
        
        converted.append(new_msg)
    
    return converted


# ==============================================================================
# 核心适配器类
# ==============================================================================

class MultiModalModelAdapter:
    """
    多模态模型统一适配器
    
    支持:
    - Dashscope API (阿里云通义千问)
    - OpenAI兼容API (本地部署的开源模型)
    """
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """
        初始化适配器
        
        Args:
            model_config: 模型配置字典，如果为None则使用get_active_model_config()
        """
        self.config = model_config or get_active_model_config()
        self.model_type = self.config["type"]
        self.model_name = self.config["model_name"]
        
        print(f"✅ [模型适配器] 初始化: {self.model_name} (类型: {self.model_type})")
    
    def call(
        self,
        messages: List[Dict],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        统一的模型调用接口
        
        Args:
            messages: 对话消息列表
            stream: 是否使用流式响应
            temperature: 温度参数
            max_tokens: 最大生成token数
        
        Yields:
            Dict: 响应chunk，格式统一为 {"content": str, "finish_reason": str}
        """
        if self.model_type == "dashscope_api":
            yield from self._call_dashscope(messages, stream, temperature, max_tokens)
        
        elif self.model_type in ["local_oss_api", "openai_compatible"]:
            yield from self._call_openai_compatible(messages, stream, temperature, max_tokens)
        
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
    
    def _call_dashscope(
        self,
        messages: List[Dict],
        stream: bool,
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> Generator[Dict, None, None]:
        """
        调用Dashscope API
        """
        # 设置API Key
        dashscope.api_key = self.config["api_key"]
        
        # 构建参数
        params = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_length"] = max_tokens
        
        # 调用API
        try:
            response = dashscope.MultiModalConversation.call(**params)
            
            if stream:
                # 流式响应
                for chunk in response:
                    if chunk.status_code == 200:
                        content = chunk.output.choices[0].message.content[0]["text"]
                        finish_reason = chunk.output.choices[0].finish_reason
                        
                        yield {
                            "content": content,
                            "finish_reason": finish_reason,
                            "usage": chunk.usage if hasattr(chunk, 'usage') else None
                        }
                    else:
                        error_msg = f"Dashscope API错误: {chunk.code} - {chunk.message}"
                        print(f"❌ {error_msg}")
                        yield {
                            "content": "",
                            "finish_reason": "error",
                            "error": error_msg
                        }
                        break
            else:
                # 非流式响应
                if response.status_code == 200:
                    content = response.output.choices[0].message.content[0]["text"]
                    yield {
                        "content": content,
                        "finish_reason": "stop",
                        "usage": response.usage
                    }
                else:
                    error_msg = f"Dashscope API错误: {response.code} - {response.message}"
                    print(f"❌ {error_msg}")
                    yield {
                        "content": "",
                        "finish_reason": "error",
                        "error": error_msg
                    }
        
        except Exception as e:
            error_msg = f"Dashscope调用异常: {str(e)}"
            print(f"❌ {error_msg}")
            yield {
                "content": "",
                "finish_reason": "error",
                "error": error_msg
            }
    
    def _call_openai_compatible(
        self,
        messages: List[Dict],
        stream: bool,
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> Generator[Dict, None, None]:
        """
        调用OpenAI兼容API（用于本地部署的开源模型）
        """
        # 转换消息格式
        converted_messages = convert_messages_to_openai_format(messages)
        
        # 构建请求参数
        api_base = self.config["api_base"]
        api_key = self.config.get("api_key", "EMPTY")
        
        params = {
            "model": self.model_name,
            "messages": converted_messages,
            "stream": stream,
            "temperature": temperature or self.config.get("temperature", 0.7),
            "max_tokens": max_tokens or self.config.get("max_tokens", 8192)
        }
        
        # 如果是thinking模式，添加特殊参数
        if self.config.get("thinking_mode"):
            params["extra_body"] = {"enable_thinking": True}
        
        try:
            # 使用httpx发送请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client(timeout=300.0) as client:
                if stream:
                    # 流式请求
                    with client.stream(
                        "POST",
                        f"{api_base}/chat/completions",
                        json=params,
                        headers=headers
                    ) as response:
                        response.raise_for_status()
                        
                        for line in response.iter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]  # 去掉 "data: " 前缀
                                
                                if data_str.strip() == "[DONE]":
                                    break
                                
                                try:
                                    data = json.loads(data_str)
                                    delta = data["choices"][0]["delta"]
                                    content = delta.get("content", "")
                                    finish_reason = data["choices"][0].get("finish_reason")
                                    
                                    yield {
                                        "content": content,
                                        "finish_reason": finish_reason,
                                        "usage": data.get("usage")
                                    }
                                except json.JSONDecodeError:
                                    continue
                
                else:
                    # 非流式请求
                    response = client.post(
                        f"{api_base}/chat/completions",
                        json=params,
                        headers=headers
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    yield {
                        "content": content,
                        "finish_reason": "stop",
                        "usage": data.get("usage")
                    }
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            print(f"❌ [OpenAI兼容API] {error_msg}")
            yield {
                "content": "",
                "finish_reason": "error",
                "error": error_msg
            }
        
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            print(f"❌ [OpenAI兼容API] {error_msg}")
            yield {
                "content": "",
                "finish_reason": "error",
                "error": error_msg
            }


# ==============================================================================
# 文本模型适配器（用于知识点提取等）
# ==============================================================================

class TextModelAdapter:
    """
    纯文本模型适配器（用于知识点提取、续答生成等）
    """
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """初始化文本模型适配器"""
        self.config = model_config or get_knowledge_extraction_config()
        self.model_type = self.config["type"]
        self.model_name = self.config["model_name"]
        
        if self.model_type == "dashscope_api":
            dashscope.api_key = self.config["api_key"]
    
    def call(self, prompt: str, temperature: float = 0.3) -> str:
        """
        调用文本模型
        
        Args:
            prompt: 输入提示
            temperature: 温度参数
        
        Returns:
            str: 模型输出文本
        """
        if self.model_type == "dashscope_api":
            try:
                response = dashscope.Generation.call(
                    model=self.model_name,
                    prompt=prompt,
                    temperature=temperature
                )
                
                if response.status_code == 200:
                    return response.output.text
                else:
                    print(f"❌ Dashscope文本模型错误: {response.code} - {response.message}")
                    return ""
            
            except Exception as e:
                print(f"❌ 文本模型调用异常: {e}")
                return ""
        
        else:
            # TODO: 添加OpenAI兼容API的文本模型调用
            print(f"⚠️  暂不支持 {self.model_type} 类型的文本模型")
            return ""


# ==============================================================================
# 便捷函数
# ==============================================================================

def get_multimodal_adapter() -> MultiModalModelAdapter:
    """获取多模态模型适配器实例（使用当前激活的模型）"""
    return MultiModalModelAdapter()


def get_text_adapter() -> TextModelAdapter:
    """获取文本模型适配器实例"""
    return TextModelAdapter()


# ==============================================================================
# 测试代码
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("模型适配器测试")
    print("=" * 70 + "\n")
    
    # 测试多模态适配器
    try:
        adapter = get_multimodal_adapter()
        
        # 构建测试消息
        test_messages = [
            {
                "role": "user",
                "content": [
                    {"text": "你好，请介绍一下你自己。"}
                ]
            }
        ]
        
        print("📤 发送测试消息...")
        print("💬 回复:")
        
        full_response = ""
        for chunk in adapter.call(test_messages, stream=True):
            if chunk["finish_reason"] != "error":
                content = chunk["content"]
                full_response += content
                print(content, end="", flush=True)
            else:
                print(f"\n❌ 错误: {chunk.get('error')}")
                break
        
        print("\n\n✅ 测试完成！")
        print(f"📊 完整回复长度: {len(full_response)} 字符")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")

