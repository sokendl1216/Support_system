# filepath: c:\Users\ss962\Desktop\仕事\Support_system\ai\orchestrator_utils.py
"""
エージェントオーケストレーターのユーティリティ関数

このモジュールはエージェントオーケストレーターの初期化、設定、
便利な機能を提供します。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent_orchestrator import (
    AgentOrchestrator, ProgressMode, Task, TaskStatus
)
from .llm_service import LLMServiceManager
from .llm_initializer import LLMServiceInitializer

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """エージェントオーケストレーターの簡単なクライアント"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config.json"
        self.llm_service: Optional[LLMServiceManager] = None
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.current_session_id: Optional[str] = None
    
    async def initialize(self) -> bool:
        """オーケストレーターを初期化"""
        try:
            # LLMサービスを初期化
            initializer = LLMServiceInitializer(self.config_path)
            
            # 設定ファイルを読み込み
            if not initializer.load_config():
                logger.error("Failed to load config file")
                return False
            
            # LLMサービスを初期化
            if not await initializer.initialize_llm_service():
                logger.error("Failed to initialize LLM service")
                return False
            
            # グローバルのLLMサービスマネージャーを取得
            from .llm_service import llm_service
            self.llm_service = llm_service
            
            if not self.llm_service:
                logger.error("Failed to get LLM service manager")
                return False
            
            # オーケストレーターを初期化
            self.orchestrator = AgentOrchestrator(self.llm_service)
            
            logger.info("Orchestrator initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            return False
    
    async def start_session(self, mode: str = "interactive") -> str:
        """新しいセッションを開始"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        progress_mode = ProgressMode(mode.lower())
        self.current_session_id = await self.orchestrator.start_session(progress_mode)
        
        return self.current_session_id
    
    async def add_and_execute_task(
        self, 
        title: str, 
        description: str, 
        requirements: List[str] = None
    ) -> Dict[str, Any]:
        """タスクを追加して実行"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
          # タスクを追加
        task_id = await self.orchestrator.add_task(title, description, requirements)
        
        # タスクを実行
        result = await self.orchestrator.execute_task_by_id(task_id)
        
        return {
            "task_id": task_id,
            "result": result
        }
    
    async def execute_auto_task(
        self, 
        title: str, 
        description: str, 
        requirements: List[str] = None
    ) -> Dict[str, Any]:
        """全自動モードでタスクを実行"""
        if not self.current_session_id:
            await self.start_session("auto")
        elif self.orchestrator.state.mode != ProgressMode.AUTO:
            await self.start_session("auto")
        
        return await self.add_and_execute_task(title, description, requirements)
    
    async def execute_interactive_task(
        self, 
        title: str, 
        description: str, 
        requirements: List[str] = None
    ) -> Dict[str, Any]:
        """対話型モードでタスクを実行"""
        if not self.current_session_id:
            await self.start_session("interactive")
        elif self.orchestrator.state.mode != ProgressMode.INTERACTIVE:
            await self.start_session("interactive")
        
        return await self.add_and_execute_task(title, description, requirements)
    
    async def approve_task_step(
        self, 
        task_id: str, 
        step_index: int, 
        modifications: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """対話型モードでタスクのステップを承認"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        return await self.orchestrator.approve_step(task_id, step_index, modifications)
    
    def get_session_status(self) -> Dict[str, Any]:
        """現在のセッション状態を取得"""
        if not self.orchestrator:
            return {"status": "not_initialized"}
        
        return self.orchestrator.get_session_status()
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """特定のタスクの状態を取得"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        return self.orchestrator.get_task_status(task_id)
    
    async def shutdown(self):
        """オーケストレーターをシャットダウン"""
        if self.orchestrator:
            await self.orchestrator.stop_session()
        
        if self.llm_service:
            # LLMサービスのシャットダウン処理があれば実行
            pass


async def create_orchestrator_from_config(config_path: str = "config.json") -> AgentOrchestrator:
    """設定ファイルからオーケストレーターを作成"""
    initializer = LLMServiceInitializer(config_path)
    
    # 設定ファイルを読み込み
    if not initializer.load_config():
        raise RuntimeError("Failed to load config file")
    
    # LLMサービスを初期化
    if not await initializer.initialize_llm_service():
        raise RuntimeError("Failed to initialize LLM service")
    
    # グローバルのLLMサービスマネージャーを取得
    from .llm_service import llm_service
    
    if not llm_service:
        raise RuntimeError("Failed to get LLM service manager")
    
    return AgentOrchestrator(llm_service)


async def quick_auto_execution(
    title: str, 
    description: str, 
    requirements: List[str] = None,
    config_path: str = "config.json"
) -> Dict[str, Any]:
    """クイック全自動実行（一回限りの使用）"""
    client = OrchestratorClient(config_path)
    
    try:
        await client.initialize()
        result = await client.execute_auto_task(title, description, requirements)
        return result
    finally:
        await client.shutdown()


async def quick_interactive_execution(
    title: str, 
    description: str, 
    requirements: List[str] = None,
    config_path: str = "config.json"
) -> Dict[str, Any]:
    """クイック対話型実行（分析・計画段階まで）"""
    client = OrchestratorClient(config_path)
    
    try:
        await client.initialize()
        result = await client.execute_interactive_task(title, description, requirements)
        return result
    finally:
        await client.shutdown()


class TaskBuilder:
    """タスク構築のヘルパークラス"""
    
    def __init__(self):
        self.title = ""
        self.description = ""
        self.requirements = []
    
    def set_title(self, title: str) -> 'TaskBuilder':
        """タイトルを設定"""
        self.title = title
        return self
    
    def set_description(self, description: str) -> 'TaskBuilder':
        """説明を設定"""
        self.description = description
        return self
    
    def add_requirement(self, requirement: str) -> 'TaskBuilder':
        """要件を追加"""
        self.requirements.append(requirement)
        return self
    
    def add_requirements(self, requirements: List[str]) -> 'TaskBuilder':
        """複数の要件を追加"""
        self.requirements.extend(requirements)
        return self
    
    def build(self) -> Dict[str, Any]:
        """タスクパラメータを構築"""
        return {
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements
        }


# 便利な関数エイリアス
def task() -> TaskBuilder:
    """新しいTaskBuilderインスタンスを作成"""
    return TaskBuilder()


# よく使用されるタスクテンプレート
class TaskTemplates:
    """よく使用されるタスクのテンプレート"""
    
    @staticmethod
    def code_generation(language: str, functionality: str, requirements: List[str] = None) -> Dict[str, Any]:
        """コード生成タスクのテンプレート"""
        return {
            "title": f"{language}での{functionality}実装",
            "description": f"{language}を使用して{functionality}を実装してください。",
            "requirements": [
                f"プログラミング言語: {language}",
                "適切なコメント",
                "エラーハンドリング",
                "テストケース"
            ] + (requirements or [])
        }
    
    @staticmethod
    def document_creation(doc_type: str, topic: str, requirements: List[str] = None) -> Dict[str, Any]:
        """文書作成タスクのテンプレート"""
        return {
            "title": f"{topic}の{doc_type}作成",
            "description": f"{topic}について{doc_type}を作成してください。",
            "requirements": [
                "構造化された内容",
                "読みやすい形式",
                "適切な見出し",
                "必要に応じて例や図表"
            ] + (requirements or [])
        }
    
    @staticmethod
    def analysis_task(subject: str, analysis_type: str, requirements: List[str] = None) -> Dict[str, Any]:
        """分析タスクのテンプレート"""
        return {
            "title": f"{subject}の{analysis_type}",
            "description": f"{subject}について{analysis_type}を実行してください。",
            "requirements": [
                "詳細な分析",
                "根拠となるデータ",
                "結論と推奨事項",
                "視覚的な要素（必要に応じて）"
            ] + (requirements or [])
        }
    
    @staticmethod
    def web_development(feature: str, technology: str, requirements: List[str] = None) -> Dict[str, Any]:
        """Web開発タスクのテンプレート"""
        return {
            "title": f"{technology}を使用した{feature}の開発",
            "description": f"{technology}を使用して{feature}を開発してください。",
            "requirements": [
                f"技術スタック: {technology}",
                "レスポンシブデザイン",
                "アクセシビリティ対応",
                "パフォーマンス最適化",
                "セキュリティ考慮"
            ] + (requirements or [])
        }
