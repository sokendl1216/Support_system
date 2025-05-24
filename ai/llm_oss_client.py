# OSSモデル用LLMクライアントの実装（Ollama API統合）
import requests
import json
from typing import Optional
from .agent_base import LLMClient

class OSSLLMClient(LLMClient):
    """OSS（無料）LLMモデル用のクライアント - Ollama API統合"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        """
        Args:
            base_url: OllamaサーバーのベースURL
            model: 使用するモデル名（例: llama2, codellama, mistral等）
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    def generate(self, prompt: str) -> str:
        """Ollama APIを使用してテキスト生成"""
        try:
            # Ollamaサーバーの稼働状況をチェック
            if not self._is_ollama_available():
                return f"[Ollama Unavailable] {prompt} (サーバーが起動していません)"
            
            # モデルが利用可能かチェック
            if not self._is_model_available():
                return f"[Model Unavailable] {prompt} (モデル '{self.model}' が見つかりません)"
            
            # API呼び出し
            url = f"{self.base_url}/api/generate"
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", f"[No Response] {prompt}")
            
        except requests.exceptions.ConnectionError:
            return f"[Connection Error] {prompt} (Ollamaサーバーに接続できません)"
        except requests.exceptions.Timeout:
            return f"[Timeout] {prompt} (応答がタイムアウトしました)"
        except Exception as e:
            return f"[Error] {prompt} (エラー: {str(e)})"
    
    def _is_ollama_available(self) -> bool:
        """Ollamaサーバーが利用可能かチェック"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _is_model_available(self) -> bool:
        """指定されたモデルが利用可能かチェック"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            tags = response.json()
            models = [model["name"] for model in tags.get("models", [])]
            return any(self.model in model for model in models)
        except:
            return False
    
    def list_available_models(self) -> list:
        """利用可能なモデル一覧を取得"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return []
            
            tags = response.json()
            return [model["name"] for model in tags.get("models", [])]
        except:
            return []
