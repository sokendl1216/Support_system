# エージェントオーケストレーション基盤
from .agent_base import BaseAgent

class AgentOrchestrator:
    """複数エージェントの連携・管理を行う基盤クラス"""
    def __init__(self, agents: list[BaseAgent]):
        self.agents = agents

    def run_all(self, input_data):
        results = []
        for agent in self.agents:
            results.append(agent.run(input_data))
        return results
