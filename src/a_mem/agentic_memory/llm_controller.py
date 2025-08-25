from typing import Dict, Optional, Literal, Any
import os
import json
from abc import ABC, abstractmethod
from litellm import completion

class BaseLLMController(ABC):
    @abstractmethod
    def get_completion(self, prompt: str) -> str:
        """Get completion from LLM"""
        pass

class OpenAIController(BaseLLMController):
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
        if api_key is None:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        # 设置环境变量供 litellm 使用
        os.environ['OPENAI_API_KEY'] = api_key
    
    def get_completion(self, prompt: str, response_format: dict, temperature: float = 0.7) -> str:
        response = completion(
            model=self.model,
            messages=[
                {"role": "system", "content": "You must respond with a JSON object."},
                {"role": "user", "content": prompt}
            ],
            response_format=response_format,
            temperature=temperature,
            max_tokens=1000
        )
        return response.choices[0].message.content
from litellm import completion
import re

class GLMController(BaseLLMController):
    def __init__(self, model: str = "glm-4", api_key: Optional[str] = None):
        self.model = model
        if api_key is None:
            api_key = os.getenv('GLM_API_KEY')
        if api_key is None:
            raise ValueError("GLM API key not found. Set GLM_API_KEY environment variable.")
        self.api_key = api_key
        self.url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    def get_completion(self, prompt: str, response_format: dict, temperature: float = 0.7) -> str:
        import requests
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You must respond with a ***only*** JSON object. Do not swap by anything!"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        response = requests.post(self.url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        # 原始文本
        raw_content = result["choices"][0]["message"]["content"]
        # print(f"raw_content:\{raw_content}")
        # 去掉 ```json ``` 或 ``` 包裹
        clean_content = re.sub(r"```json|```", "", raw_content).strip()
        clean_content = clean_content.replace("True", "true").replace("False", "false").replace("None", "null")
        # print(f"clean_content:\{clean_content}")
        return clean_content
        # response = requests.post(self.url, headers=headers, json=payload, timeout=60)
        # response.raise_for_status()
        # result = response.json()
        # print(result)
        # return result["choices"][0]["message"]["content"]


class OllamaController(BaseLLMController):
    def __init__(self, model: str = "llama2"):
        self.model = model
    
    def _generate_empty_value(self, schema_type: str, schema_items: dict = None) -> Any:
        if schema_type == "array":
            return []
        elif schema_type == "string":
            return ""
        elif schema_type == "object":
            return {}
        elif schema_type == "number":
            return 0
        elif schema_type == "boolean":
            return False
        return None

    def _generate_empty_response(self, response_format: dict) -> dict:
        if "json_schema" not in response_format:
            return {}
            
        schema = response_format["json_schema"]["schema"]
        result = {}
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                result[prop_name] = self._generate_empty_value(prop_schema["type"], 
                                                            prop_schema.get("items"))
        
        return result

    def get_completion(self, prompt: str, response_format: dict, temperature: float = 0.7) -> str:
        try:
            response = completion(
                model=f"ollama_chat/{self.model}",
                messages=[
                    {"role": "system", "content": "You must respond with a JSON object."},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_format,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            empty_response = self._generate_empty_response(response_format)
            return json.dumps(empty_response)

class LLMController:
    """LLM-based controller for memory metadata generation"""
    def __init__(self, 
                 backend: Literal["openai", "ollama", "glm"] = "openai",
                 model: str = "gpt-4", 
                 api_key: Optional[str] = None):
        if backend == "openai":
            self.llm = OpenAIController(model, api_key)
        elif backend == "ollama":
            self.llm = OllamaController(model)
        elif backend == "glm":
            self.llm = GLMController(model, api_key)
        else:
            raise ValueError("Backend must be one of: 'openai', 'ollama', 'glm'")
            
    def get_completion(self, prompt: str, response_format: dict = None, temperature: float = 0.7) -> str:
        return self.llm.get_completion(prompt, response_format, temperature)
