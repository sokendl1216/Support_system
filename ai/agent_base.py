# AIエージェント基盤：ベースクラス・抽象化レイヤー
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """AIエージェントの抽象基底クラス"""
    @abstractmethod
    def run(self, input_data):
        pass

class LLMClient(ABC):
    """LLM（大規模言語モデル）クライアントの抽象基底クラス"""
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass
