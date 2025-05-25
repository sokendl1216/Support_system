"""
AIエージェントオーケストレーションシステム

このモジュールは複数のAIエージェントを連携・調整するシステムを提供します。
- 全自動型進行モード（Auto-GPT型）
- 対話型進行モード（LangChain型）
- エージェント間の通信とコンテキスト管理
- タスクの分解と並列実行
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# LLMサービスをインポート
from .llm_service import LLMServiceManager, GenerationRequest, GenerationResponse, GenerationConfig

logger = logging.getLogger(__name__)


class ProgressMode(Enum):
    """進行モード"""
    AUTO = "auto"           # 全自動型（Auto-GPT型）
    INTERACTIVE = "interactive"  # 対話型（LangChain型）
    HYBRID = "hybrid"       # ハイブリッド型


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentRole(Enum):
    """エージェントの役割"""
    COORDINATOR = "coordinator"    # 調整役
    ANALYZER = "analyzer"          # 分析役
    EXECUTOR = "executor"          # 実行役
    REVIEWER = "reviewer"          # レビュー役
    SPECIALIST = "specialist"      # 専門家


@dataclass
class Task:
    """タスク定義"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    priority: int = 1  # 1-5
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class AgentContext:
    """エージェントコンテキスト"""
    agent_id: str
    role: AgentRole
    session_id: str
    current_task: Optional[Task] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_action: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrchestratorState:
    """オーケストレーターの状態"""
    session_id: str
    mode: ProgressMode
    active_tasks: List[Task] = field(default_factory=list)
    completed_tasks: List[Task] = field(default_factory=list)
    agent_contexts: Dict[str, AgentContext] = field(default_factory=dict)
    global_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_checkpoint: Optional[datetime] = None


class BaseAgent(ABC):
    """基本エージェントクラス"""
    
    def __init__(self, agent_id: str, role: AgentRole, llm_service: LLMServiceManager):
        self.agent_id = agent_id
        self.role = role
        self.llm_service = llm_service
        self.context: Optional[AgentContext] = None
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_execution_time": 0.0,
            "last_activity": None
        }
    
    def set_context(self, context: AgentContext):
        """コンテキストを設定"""
        self.context = context
    
    @abstractmethod
    async def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """タスクを実行"""
        pass
    
    async def pre_execute(self, task: Task, context: Dict[str, Any]) -> bool:
        """実行前処理"""
        logger.info(f"Agent {self.agent_id} starting task: {task.title}")
        return True
    
    async def post_execute(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """実行後処理"""
        logger.info(f"Agent {self.agent_id} completed task: {task.title}")
        self.performance_metrics["tasks_completed"] += 1
        self.performance_metrics["last_activity"] = datetime.now()
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクスを取得"""
        return self.performance_metrics.copy()


class CoordinatorAgent(BaseAgent):
    """コーディネーターエージェント - タスクの分解と調整を担当"""
    
    def __init__(self, agent_id: str, llm_service: LLMServiceManager):
        super().__init__(agent_id, AgentRole.COORDINATOR, llm_service)
    
    async def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """タスクの分解と調整を実行"""
        subtasks = await self.decompose_task(task, context)
        coordination_plan = await self.create_coordination_plan(task, subtasks, context)
        
        return {
            "type": "coordination",
            "subtasks": subtasks,
            "coordination_plan": coordination_plan,
            "status": "coordinated",
            "agent_id": self.agent_id
        }
    
    async def decompose_task(self, task: Task, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """タスクを小さなサブタスクに分解"""
        prompt = f"""
        以下のタスクを実行可能な小さなサブタスクに分解してください：
        
        タスク: {task.title}
        説明: {task.description}
        コンテキスト: {json.dumps(context, ensure_ascii=False, default=str)}
        
        各サブタスクについて以下の情報を含むJSON配列で回答してください：
        - title: サブタスクのタイトル
        - description: サブタスクの詳細説明
        - priority: 優先度 (1-5)
        - estimated_duration: 推定実行時間（分）
        - required_skills: 必要なスキル
        - dependencies: 依存関係
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1500,
                temperature=0.7
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            subtasks = json.loads(response.text)
            return subtasks if isinstance(subtasks, list) else []
        except json.JSONDecodeError:
            # フォールバック: シンプルなサブタスクを作成
            return [
                {
                    "title": f"Sub-task for: {task.title}",
                    "description": f"Execute: {task.description}",
                    "priority": task.priority,
                    "estimated_duration": 30,
                    "required_skills": ["general"],
                    "dependencies": []
                }
            ]
    
    async def create_coordination_plan(self, main_task: Task, subtasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """調整計画を作成"""
        prompt = f"""
        以下のメインタスクとサブタスクについて実行計画を作成してください：
        
        メインタスク: {main_task.title}
        サブタスク: {json.dumps(subtasks, ensure_ascii=False)}
        
        以下を含む実行計画をJSONで回答してください：
        - execution_order: 実行順序
        - parallel_groups: 並列実行可能なグループ
        - resource_allocation: リソース配分
        - timeline: タイムライン
        - checkpoints: チェックポイント
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1000,
                temperature=0.5
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "execution_order": "sequential",
                "parallel_groups": [],
                "resource_allocation": "balanced",
                "timeline": "flexible",
                "checkpoints": ["start", "middle", "end"]
            }


class AnalyzerAgent(BaseAgent):
    """アナライザーエージェント - 分析と評価を担当"""
    
    def __init__(self, agent_id: str, llm_service: LLMServiceManager):
        super().__init__(agent_id, AgentRole.ANALYZER, llm_service)
    
    async def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析タスクを実行"""
        analysis = await self.analyze_requirements(task, context)
        risks = await self.assess_risks(task, context)
        recommendations = await self.generate_recommendations(task, analysis, risks)
        
        return {
            "type": "analysis",
            "analysis": analysis,
            "risks": risks,
            "recommendations": recommendations,
            "agent_id": self.agent_id
        }
    
    async def analyze_requirements(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """要件分析を実行"""
        prompt = f"""
        以下のタスクについて要件分析を行ってください：
        
        タスク: {task.title}
        説明: {task.description}
        コンテキスト: {json.dumps(context, ensure_ascii=False, default=str)}
        
        以下の観点で分析し、JSONで回答してください：
        - functional_requirements: 機能要件
        - non_functional_requirements: 非機能要件
        - constraints: 制約条件
        - assumptions: 前提条件
        - success_criteria: 成功基準
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1200,
                temperature=0.6
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "functional_requirements": ["Basic task execution"],
                "non_functional_requirements": ["Reliability", "Performance"],
                "constraints": ["Time", "Resources"],
                "assumptions": ["Standard environment"],
                "success_criteria": ["Task completion"]
            }
    
    async def assess_risks(self, task: Task, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """リスク評価を実行"""
        prompt = f"""
        以下のタスクについてリスク評価を行ってください：
        
        タスク: {task.title}
        説明: {task.description}
        
        以下の観点でリスクを評価し、JSON配列で回答してください：
        - type: リスクの種類
        - description: リスクの説明
        - probability: 発生確率 (0.0-1.0)
        - impact: 影響度 (1-5)
        - mitigation: 軽減策
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1000,
                temperature=0.7
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return [{"type": "unknown", "description": "Risk assessment failed", "probability": 0.5, "impact": 3, "mitigation": "Monitor closely"}]
    
    async def generate_recommendations(self, task: Task, analysis: Dict[str, Any], risks: List[Dict[str, Any]]) -> List[str]:
        """推奨事項を生成"""
        prompt = f"""
        タスク分析とリスク評価に基づいて推奨事項を生成してください：
        
        タスク: {task.title}
        分析結果: {json.dumps(analysis, ensure_ascii=False)}
        リスク: {json.dumps(risks, ensure_ascii=False)}
        
        具体的で実行可能な推奨事項のリストを生成してください。
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=800,
                temperature=0.7
            )
        )
        
        response = await self.llm_service.generate(request)
        
        # シンプルな改行分割で推奨事項を抽出
        recommendations = [line.strip() for line in response.text.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        return recommendations[:10]  # 最大10個の推奨事項


class ExecutorAgent(BaseAgent):
    """エグゼキューターエージェント - 実際のタスク実行を担当"""
    
    def __init__(self, agent_id: str, llm_service: LLMServiceManager):
        super().__init__(agent_id, AgentRole.EXECUTOR, llm_service)
    
    async def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """実行タスクを実行"""
        task_type = context.get("task_type", "general")
        
        if task_type == "code_generation":
            result = await self.generate_code(task, context)
        elif task_type == "content_creation":
            result = await self.create_content(task, context)
        else:
            result = await self.execute_general_task(task, context)
        
        return {
            "type": "execution",
            "task_type": task_type,
            "result": result,
            "agent_id": self.agent_id
        }
    
    async def generate_code(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """コード生成タスク"""
        language = context.get("language", "python")
        requirements = context.get("requirements", task.description)
        
        prompt = f"""
        以下の要件に基づいて{language}のコードを生成してください：
        
        要件: {requirements}
        言語: {language}
        
        以下の形式で回答してください：
        - コードブロック
        - 説明とコメント
        - 使用方法の例
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=2000,
                temperature=0.3
            )
        )
        
        response = await self.llm_service.generate(request)
        
        return {
            "code": response.text,
            "language": language,
            "status": "generated"
        }
    
    async def create_content(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツ作成タスク"""
        content_type = context.get("content_type", "document")
        style = context.get("style", "professional")
        
        prompt = f"""
        以下の仕様で{content_type}を作成してください：
        
        タイトル: {task.title}
        内容: {task.description}
        スタイル: {style}
        
        高品質で読みやすいコンテンツを作成してください。
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1500,
                temperature=0.7
            )
        )
        
        response = await self.llm_service.generate(request)
        
        return {
            "content": response.text,
            "content_type": content_type,
            "style": style,
            "status": "created"
        }
    
    async def execute_general_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """一般的なタスク実行"""
        prompt = f"""
        以下のタスクを実行してください：
        
        タスク: {task.title}
        説明: {task.description}
        コンテキスト: {json.dumps(context, ensure_ascii=False, default=str)}
        
        タスクを分析し、適切な方法で実行し、結果を報告してください。
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1000,
                temperature=0.6
            )
        )
        
        response = await self.llm_service.generate(request)
        
        return {
            "output": response.text,
            "status": "executed"
        }


class ReviewerAgent(BaseAgent):
    """レビューワーエージェント - 品質評価とレビューを担当"""
    
    def __init__(self, agent_id: str, llm_service: LLMServiceManager):
        super().__init__(agent_id, AgentRole.REVIEWER, llm_service)
    
    async def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """レビュータスクを実行"""
        target_result = context.get("target_result", {})
        review_type = context.get("review_type", "quality")
        
        if review_type == "code":
            review = await self.review_code(target_result, context)
        elif review_type == "content":
            review = await self.review_content(target_result, context)
        else:
            review = await self.review_quality(target_result, context)
        
        return {
            "type": "review",
            "review_type": review_type,
            "review": review,
            "agent_id": self.agent_id
        }
    
    async def review_code(self, code_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """コードレビュー"""
        code = code_result.get("code", "")
        language = code_result.get("language", "python")
        
        prompt = f"""
        以下の{language}コードをレビューしてください：
        
        ```{language}
        {code}
        ```
        
        以下の観点でレビューし、JSONで回答してください：
        - code_quality: コード品質 (1-10)
        - readability: 可読性 (1-10)
        - security: セキュリティ (1-10)
        - performance: パフォーマンス (1-10)
        - issues: 問題点のリスト
        - suggestions: 改善提案のリスト
        - overall_score: 総合評価 (1-10)
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1200,
                temperature=0.4
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "code_quality": 7,
                "readability": 7,
                "security": 7,
                "performance": 7,
                "issues": ["Review parsing failed"],
                "suggestions": ["Manual review recommended"],
                "overall_score": 7
            }
    
    async def review_content(self, content_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツレビュー"""
        content = content_result.get("content", "")
        content_type = content_result.get("content_type", "document")
        
        prompt = f"""
        以下の{content_type}をレビューしてください：
        
        {content}
        
        以下の観点でレビューし、JSONで回答してください：
        - clarity: 明確性 (1-10)
        - accuracy: 正確性 (1-10)
        - completeness: 完全性 (1-10)
        - engagement: 魅力度 (1-10)
        - issues: 問題点のリスト
        - suggestions: 改善提案のリスト
        - overall_score: 総合評価 (1-10)
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1000,
                temperature=0.5
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "clarity": 7,
                "accuracy": 7,
                "completeness": 7,
                "engagement": 7,
                "issues": ["Review parsing failed"],
                "suggestions": ["Manual review recommended"],
                "overall_score": 7
            }
    
    async def review_quality(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """品質レビュー"""
        prompt = f"""
        以下の作業結果を品質の観点でレビューしてください：
        
        結果: {json.dumps(result, ensure_ascii=False, default=str)}
        コンテキスト: {json.dumps(context, ensure_ascii=False, default=str)}
        
        以下の観点でレビューし、JSONで回答してください：
        - completeness: 完成度 (1-10)
        - accuracy: 正確性 (1-10)
        - efficiency: 効率性 (1-10)
        - reliability: 信頼性 (1-10)
        - issues: 問題点のリスト
        - suggestions: 改善提案のリスト
        - overall_score: 総合評価 (1-10)
        """
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1000,
                temperature=0.5
            )
        )
        
        response = await self.llm_service.generate(request)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "completeness": 7,
                "accuracy": 7,
                "efficiency": 7,
                "reliability": 7,
                "issues": ["Review parsing failed"],
                "suggestions": ["Manual review recommended"],
                "overall_score": 7
            }


class AgentOrchestrator:
    """エージェントオーケストレーター - 複数エージェントの調整管理"""
    
    def __init__(self, llm_service: LLMServiceManager):
        self.llm_service = llm_service
        self.sessions: Dict[str, OrchestratorState] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # デフォルトエージェントを初期化
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """デフォルトエージェントを初期化"""
        agents_config = [
            ("coordinator_1", CoordinatorAgent),
            ("analyzer_1", AnalyzerAgent),
            ("executor_1", ExecutorAgent),
            ("reviewer_1", ReviewerAgent)
        ]
        
        for agent_id, agent_class in agents_config:
            agent = agent_class(agent_id, self.llm_service)
            self.agents[agent_id] = agent
            logger.info(f"Initialized agent: {agent_id} ({agent.role.value})")
    
    def create_session(self, mode: ProgressMode = ProgressMode.AUTO) -> str:
        """新しいセッションを作成"""
        session_id = str(uuid.uuid4())
        state = OrchestratorState(session_id=session_id, mode=mode)
        
        # エージェントコンテキストを初期化
        for agent_id, agent in self.agents.items():
            context = AgentContext(
                agent_id=agent_id,
                role=agent.role,
                session_id=session_id
            )
            state.agent_contexts[agent_id] = context
            agent.set_context(context)
        
        self.sessions[session_id] = state
        logger.info(f"Created session: {session_id} with mode: {mode.value}")
        
        return session_id
    
    async def start_session(self, mode: Union[str, ProgressMode] = ProgressMode.AUTO) -> str:
        """新しいセッションを開始（非同期バージョン）"""
        if isinstance(mode, str):
            mode = ProgressMode(mode)
        return self.create_session(mode)
    
    async def stop_session(self, session_id: Optional[str] = None):
        """セッションを停止"""
        if session_id is None:
            # 全セッションをクリア
            self.sessions.clear()
            logger.info("All sessions stopped")
        elif session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} stopped")
        else:
            logger.warning(f"Session {session_id} not found")
    
    def get_session_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """セッションのステータスを取得"""
        if session_id is None and hasattr(self, 'current_session_id'):
            session_id = self.current_session_id
        
        if session_id and session_id in self.sessions:
            summary = self.get_session_summary(session_id)
            return summary if summary else {
                "session_id": session_id,
                "mode": "unknown",
                "status": "not_found"
            }
        else:
            return {
                "active_sessions": len(self.sessions),
                "session_ids": list(self.sessions.keys()),
                "mode": "multi-session" if len(self.sessions) > 1 else "no-session"
            }
    
    async def add_task(self, title: str, description: str, requirements: Optional[Dict[str, Any]] = None) -> str:
        """タスクを追加"""
        # タスクを作成
        task = Task(
            title=title,
            description=description,
            context=requirements or {}
        )
        
        return task.id
    
    async def execute_task_by_id(self, task_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """タスクIDでタスクを実行"""
        # デフォルトセッションがない場合は作成
        if not self.sessions:
            session_id = self.create_session()
        elif session_id is None:
            session_id = list(self.sessions.keys())[0]  # 最初のセッションを使用
        
        # タスクを再作成（実際の実装では永続化されたタスクを取得）
        # 簡単な実装のため、デモタスクを作成
        task = Task(
            id=task_id,
            title="デモタスク",
            description="テスト用のデモタスク",
            context={}
        )
        
        # タスクを実行
        return await self.execute_task(session_id, task)
    
    async def execute_task(self, session_id: str, task: Task, 
                          approval_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """タスクを実行"""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        state = self.sessions[session_id]
        state.active_tasks.append(task)
        task.status = TaskStatus.RUNNING
        
        try:
            if state.mode == ProgressMode.AUTO:
                result = await self._execute_auto_mode(session_id, task)
            elif state.mode == ProgressMode.INTERACTIVE:
                result = await self._execute_interactive_mode(session_id, task, approval_callback)
            else:  # HYBRID
                result = await self._execute_hybrid_mode(session_id, task, approval_callback)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            state.completed_tasks.append(task)
            state.active_tasks.remove(task)
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task execution failed: {e}")
            raise
    
    async def _execute_auto_mode(self, session_id: str, task: Task) -> Dict[str, Any]:
        """全自動モードでタスクを実行"""
        logger.info(f"Executing task in AUTO mode: {task.title}")
        
        # 1. コーディネーター：タスク分解
        coordinator = self.agents["coordinator_1"]
        coordination_result = await coordinator.execute(task, {"mode": "auto"})
        
        # 2. アナライザー：分析
        analyzer = self.agents["analyzer_1"]
        analysis_result = await analyzer.execute(task, {"mode": "auto"})
        
        # 3. エグゼキューター：実行
        executor = self.agents["executor_1"]
        execution_result = await executor.execute(task, {
            "mode": "auto",
            "coordination": coordination_result,
            "analysis": analysis_result
        })
        
        # 4. レビューワー：レビュー
        reviewer = self.agents["reviewer_1"]
        review_result = await reviewer.execute(task, {
            "mode": "auto",
            "target_result": execution_result
        })
        
        return {
            "mode": "auto",
            "coordination": coordination_result,
            "analysis": analysis_result,
            "execution": execution_result,
            "review": review_result,
            "status": "completed"
        }
    
    async def _execute_interactive_mode(self, session_id: str, task: Task, 
                                      approval_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """対話モードでタスクを実行"""
        logger.info(f"Executing task in INTERACTIVE mode: {task.title}")
        
        results = {"mode": "interactive", "steps": []}
        
        # ステップ1: コーディネーション
        if approval_callback is None or await approval_callback("coordination", task):
            coordinator = self.agents["coordinator_1"]
            coordination_result = await coordinator.execute(task, {"mode": "interactive"})
            results["coordination"] = coordination_result
            results["steps"].append("coordination")
        
        # ステップ2: 分析
        if approval_callback is None or await approval_callback("analysis", task):
            analyzer = self.agents["analyzer_1"]
            analysis_result = await analyzer.execute(task, {"mode": "interactive"})
            results["analysis"] = analysis_result
            results["steps"].append("analysis")
        
        # ステップ3: 実行
        if approval_callback is None or await approval_callback("execution", task):
            executor = self.agents["executor_1"]
            execution_result = await executor.execute(task, {
                "mode": "interactive",
                "coordination": results.get("coordination"),
                "analysis": results.get("analysis")
            })
            results["execution"] = execution_result
            results["steps"].append("execution")
        
        # ステップ4: レビュー
        if approval_callback is None or await approval_callback("review", task):
            reviewer = self.agents["reviewer_1"]
            review_result = await reviewer.execute(task, {
                "mode": "interactive",
                "target_result": results.get("execution")
            })
            results["review"] = review_result
            results["steps"].append("review")
        
        results["status"] = "completed"
        return results
    
    async def _execute_hybrid_mode(self, session_id: str, task: Task, 
                                 approval_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """ハイブリッドモードでタスクを実行"""
        logger.info(f"Executing task in HYBRID mode: {task.title}")
        
        # 重要なステップのみ承認を求める
        critical_steps = ["execution", "review"]
        
        results = {"mode": "hybrid", "steps": []}
        
        # コーディネーション（自動）
        coordinator = self.agents["coordinator_1"]
        coordination_result = await coordinator.execute(task, {"mode": "hybrid"})
        results["coordination"] = coordination_result
        results["steps"].append("coordination")
        
        # 分析（自動）
        analyzer = self.agents["analyzer_1"]
        analysis_result = await analyzer.execute(task, {"mode": "hybrid"})
        results["analysis"] = analysis_result
        results["steps"].append("analysis")
        
        # 実行（承認必要）
        if approval_callback is None or await approval_callback("execution", task):
            executor = self.agents["executor_1"]
            execution_result = await executor.execute(task, {
                "mode": "hybrid",
                "coordination": coordination_result,
                "analysis": analysis_result
            })
            results["execution"] = execution_result
            results["steps"].append("execution")
        
        # レビュー（承認必要）
        if approval_callback is None or await approval_callback("review", task):
            reviewer = self.agents["reviewer_1"]
            review_result = await reviewer.execute(task, {
                "mode": "hybrid",
                "target_result": results.get("execution")
            })
            results["review"] = review_result
            results["steps"].append("review")
        
        results["status"] = "completed"
        return results
    
    def get_session_state(self, session_id: str) -> Optional[OrchestratorState]:
        """セッション状態を取得"""
        return self.sessions.get(session_id)
    
    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """全エージェントのメトリクスを取得"""
        return {agent_id: agent.get_metrics() for agent_id, agent in self.agents.items()}
    
    def switch_mode(self, session_id: str, new_mode: ProgressMode):
        """進行モードを切り替え"""
        if session_id in self.sessions:
            self.sessions[session_id].mode = new_mode
            logger.info(f"Switched session {session_id} to mode: {new_mode.value}")
        else:
            raise ValueError(f"Session not found: {session_id}")
    
    def list_sessions(self) -> List[str]:
        """アクティブなセッション一覧を取得"""
        return list(self.sessions.keys())
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションのサマリーを取得"""
        if session_id not in self.sessions:
            return None
        
        state = self.sessions[session_id]
        return {
            "session_id": session_id,
            "mode": state.mode.value,
            "created_at": state.created_at.isoformat(),
            "active_tasks_count": len(state.active_tasks),
            "completed_tasks_count": len(state.completed_tasks),
            "agents_count": len(state.agent_contexts)
        }
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """イベントハンドラーを追加"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def emit_event(self, event_type: str, data: Any):
        """イベントを発行"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
