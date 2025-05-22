# OSSモデル用LLMクライアントの抽象実装例
from .agent_base import LLMClient

class OSSLLMClient(LLMClient):
    """OSS（無料）LLMモデル用のクライアント基盤。ここではダミー実装。"""
    def generate(self, prompt: str) -> str:
        # 実際はOllamaやローカルLLMサーバー等と連携する
        return f"[OSS LLM] {prompt}"
