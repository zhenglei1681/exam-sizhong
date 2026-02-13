"""
AI 客户端模块

统一接口支持本地模型和商业 API 调用
"""
from typing import Dict, Any, List, Optional
import time

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AIClient:
    """AI 客户端，支持本地模型和 API 调用"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 AI 客户端

        Args:
            config: AI 配置字典
        """
        if OpenAI is None:
            raise ImportError("请先安装 openai 包: pip install openai")

        self.mode = config.get("mode", "api")
        self.timeout = config.get("timeout", 60)
        self.max_retries = config.get("max_retries", 3)
        self.temperature = config.get("temperature", 0.3)

        self.client = self._init_client(config)

    def _init_client(self, config: Dict[str, Any]):
        """初始化 OpenAI 客户端"""
        if self.mode == "local":
            # 本地模式：使用 Ollama、LM Studio 等
            local_config = config.get("local", {})
            self.model = local_config.get("model", "llama3.2")
            return OpenAI(
                base_url=local_config.get("base_url", "http://localhost:11434/v1"),
                api_key="dummy-key"  # 本地模式不需要真实 API key
            )
        else:
            # API 模式：使用商业 API
            api_config = config.get("api", {})
            self.model = api_config.get("model", "gpt-3.5-turbo")
            api_key = api_config.get("api_key", "")

            if not api_key:
                raise ValueError("API 模式需要提供 api_key")

            base_url = api_config.get("base_url")
            if base_url:
                # 使用自定义 endpoint（如 DeepSeek、通义千问等）
                return OpenAI(
                    base_url=base_url,
                    api_key=api_key
                )
            else:
                # 使用官方 OpenAI API
                return OpenAI(api_key=api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数

        Returns:
            AI 响应文本
        """
        # 合并默认参数
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "timeout": kwargs.get("timeout", self.timeout)
        }

        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content or ""

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"AI 调用失败（重试 {self.max_retries} 次后）: {e}")

                # 指数退避
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回 JSON 格式结果

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            解析后的 JSON 字典
        """
        import json

        response_text = self.chat(messages, **kwargs)

        # 尝试解析 JSON
        try:
            # 移除可能的 markdown 代码块标记
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())
        except json.JSONDecodeError:
            # JSON 解析失败，返回原始文本
            return {"raw": response_text}

    def get_model_info(self) -> Dict[str, str]:
        """
        获取当前模型信息

        Returns:
            包含模型信息的字典
        """
        return {
            "mode": self.mode,
            "model": self.model,
            "timeout": self.timeout,
            "temperature": self.temperature
        }
