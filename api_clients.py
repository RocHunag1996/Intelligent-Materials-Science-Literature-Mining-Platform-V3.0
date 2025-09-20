# 2_api_clients.py
"""
This module handles all interactions with external Large Language Model (LLM) APIs.
It uses a factory pattern with a base class and specific implementations for each provider.
This design makes it easy to add support for new LLMs in the future by simply adding
a new client class.
"""
import requests
import json
import time
import re
from abc import ABC, abstractmethod
from queue import Queue
from typing import Dict, Any

# Import from other project modules
from config import MAX_RETRIES, API_REQUEST_TIMEOUT

# --- Abstract Base Class for API Clients ---
class BaseAPIClient(ABC):
    """
    Abstract Base Class for all API clients.
    It defines a common interface ('analyze_text') that all concrete clients must implement,
    and provides shared functionality like request retries and JSON cleaning.
    """
    def __init__(self, api_key: str, model: str, endpoint: str, queue: Queue):
        """
        Initializes the base client.

        Args:
            api_key (str): The API key for the provider.
            model (str): The specific model to use.
            endpoint (str): The API endpoint URL.
            queue (Queue): The queue for logging messages back to the GUI.

        Raises:
            ValueError: If the API key is not provided.
        """
        if not api_key:
            raise ValueError(f"错误: {self.__class__.__name__} 的 API 密钥不能为空。")
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.queue = queue

    @abstractmethod
    def analyze_text(self, prompt: str, temperature: float = 0.1, top_p: float = 0.9) -> Dict[str, Any]:
        """
        Analyzes the given text using the specific LLM API.
        This method must be implemented by all subclasses.
        """
        pass

    def _make_request_with_retries(self, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        A helper method to perform HTTP POST requests with exponential backoff retries.
        This handles transient network errors and server-side issues gracefully.
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    data=json.dumps(data),
                    timeout=API_REQUEST_TIMEOUT
                )
                response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except requests.exceptions.HTTPError as e:
                self.queue.put(f"API HTTP错误 (尝试 {attempt + 1}/{MAX_RETRIES}): {e.response.status_code} {e.response.text}")
            except requests.exceptions.RequestException as e:
                self.queue.put(f"API 请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
            
            if attempt < MAX_RETRIES - 1:
                sleep_time = 2 ** (attempt + 1)
                self.queue.put(f"将在 {sleep_time} 秒后重试...")
                time.sleep(sleep_time)
        
        self.queue.put(f"错误: API 请求在 {MAX_RETRIES} 次尝试后最终失败。")
        return None

    def _clean_json_response(self, text_content: str) -> Dict[str, Any]:
        """
        Cleans and parses a JSON object from a string that might be wrapped in markdown code blocks
        or have other text around it. This is a common issue with LLM responses.
        """
        # Use regex to find the first occurrence of a JSON object
        match = re.search(r'\{.*\}', text_content, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.queue.put(f"警告: 无法解码API返回的JSON。错误: {e}")
                self.queue.put(f"原始文本内容 (前500字符): {text_content[:500]}")
                return {"error": "JSON Decode Error", "raw_content": text_content}
        else:
            self.queue.put(f"警告: 在API响应中未找到有效的JSON对象。")
            self.queue.put(f"原始文本内容 (前500字符): {text_content[:500]}")
            return {"error": "No JSON found in response", "raw_content": text_content}


# --- Specific Client Implementations ---

class OpenAIClient(BaseAPIClient):
    """API Client for OpenAI (GPT models)."""
    def analyze_text(self, prompt, temperature=0.1, top_p=0.9):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p,
            "response_format": {"type": "json_object"}
        }
        response_json = self._make_request_with_retries(headers, data)
        if response_json:
            try:
                content = response_json["choices"][0]["message"]["content"]
                return self._clean_json_response(content)
            except (KeyError, IndexError) as e:
                self.queue.put(f"错误: 意外的 OpenAI 响应格式 - {e}")
                return {"error": "API Format Error"}
        return {"error": "API Failure"}

class AnthropicClient(BaseAPIClient):
    """API Client for Anthropic (Claude models)."""
    def analyze_text(self, prompt, temperature=0.1, top_p=0.9):
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
        system_prompt, user_prompt = prompt.split("--- TEXT TO ANALYZE ---", 1)
        data = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "top_p": top_p,
            "system": system_prompt.strip(),
            "messages": [{"role": "user", "content": "--- TEXT TO ANALYZE ---" + user_prompt}]
        }
        response_json = self._make_request_with_retries(headers, data)
        if response_json:
            try:
                content = response_json["content"][0]["text"]
                return self._clean_json_response(content)
            except (KeyError, IndexError) as e:
                self.queue.put(f"错误: 意外的 Anthropic 响应格式 - {e}")
                return {"error": "API Format Error"}
        return {"error": "API Failure"}

class DeepSeekClient(BaseAPIClient):
    """API Client for DeepSeek models."""
    def analyze_text(self, prompt, temperature=0.1, top_p=0.9):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p
        }
        response_json = self._make_request_with_retries(headers, data)
        if response_json:
            try:
                content = response_json["choices"][0]["message"]["content"]
                return self._clean_json_response(content)
            except (KeyError, IndexError) as e:
                self.queue.put(f"错误: 意外的 DeepSeek 响应格式 - {e}")
                return {"error": "API Format Error"}
        return {"error": "API Failure"}

class MoonshotClient(BaseAPIClient):
    """API Client for Moonshot (Kimi) models."""
    def analyze_text(self, prompt, temperature=0.1, top_p=0.9):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p,
            "response_format": {"type": "json_object"}
        }
        response_json = self._make_request_with_retries(headers, data)
        if response_json:
            try:
                content = response_json["choices"][0]["message"]["content"]
                return self._clean_json_response(content)
            except (KeyError, IndexError) as e:
                self.queue.put(f"错误: 意外的 Moonshot 响应格式 - {e}")
                return {"error": "API Format Error"}
        return {"error": "API Failure"}


class InternAIClient(BaseAPIClient):
    """API Client for the internal Intern-AI service."""
    def analyze_text(self, prompt, temperature=0.1, top_p=0.9):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model, "messages": [{"role": "user", "content": prompt}],
            "n": 1, "temperature": temperature, "top_p": top_p, "thinking_mode": False
        }
        response_json = self._make_request_with_retries(headers, data)
        if response_json:
            try:
                content = response_json["choices"][0]['message']["content"]
                return self._clean_json_response(content)
            except (KeyError, IndexError) as e:
                self.queue.put(f"错误: 意外的 Intern-AI 响应格式 - {e}")
                return {"error": "API Format Error"}
        return {"error": "API Failure"}

# --- Factory Function ---
def get_api_client(provider_name: str, api_key: str, model: str, endpoint: str, queue: Queue) -> BaseAPIClient:
    """
    Factory function to create an instance of the correct API client based on the provider name.
    This is the single point of entry for creating clients, making the main code cleaner.
    """
    client_map = {
        "OpenAI": OpenAIClient,
        "Anthropic": AnthropicClient,
        "DeepSeek": DeepSeekClient,
        "Moonshot": MoonshotClient,
        "Intern-AI (Internal)": InternAIClient,
    }
    client_class = client_map.get(provider_name)
    if not client_class:
        raise ValueError(f"错误: 未知的 API provider: {provider_name}")
    return client_class(api_key, model, endpoint, queue)
