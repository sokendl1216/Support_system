# エージェントオーケストレーション基盤
from typing import List, Optional
from .agent_base import BaseAgent

class AgentOrchestrator:
    """複数エージェントの連携・管理を行う基盤クラス"""
    
    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        self.agents = agents or []
        self.current_mode = "default"
        self.mode_styles = {
            "default": "",
            "creative": "[creative mode] ",
            "analytical": "[analytical mode] ",
            "technical": "[technical mode] "
        }

    def set_mode(self, mode: str):
        """処理モードを設定"""
        if mode in self.mode_styles:
            self.current_mode = mode
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def process_request(self, request: str) -> str:
        """リクエストを現在のモードで処理"""
        style_prefix = self.mode_styles.get(self.current_mode, "")
        return f"{style_prefix}{request}"

    def run_all(self, input_data):
        """すべてのエージェントを実行"""
        results = []
        for agent in self.agents:
            results.append(agent.run(input_data))
        return results
    
    def add_agent(self, agent: BaseAgent):
        """エージェントを追加"""
        self.agents.append(agent)
    
    def remove_agent(self, agent: BaseAgent):
        """エージェントを削除"""
        if agent in self.agents:
            self.agents.remove(agent)
