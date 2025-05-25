# filepath: c:\Users\ss962\Desktop\仕事\Support_system\ai\agent_orchestrator.py
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
    requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1が最高優先度
    estimated_duration: Optional[int] = None  # 推定時間（秒）


@dataclass
class AgentContext:
    """エージェントのコンテキスト"""
    agent_id: str
    role: AgentRole
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    is_busy: bool = False


@dataclass
class OrchestratorState:
    """オーケストレーターの状態"""
    mode: ProgressMode = ProgressMode.INTERACTIVE
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tasks: Dict[str, Task] = field(default_factory=dict)
    agents: Dict[str, AgentContext] = field(default_factory=dict)
    global_context: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    is_running: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """エージェントの基底クラス"""
    
    def __init__(self, agent_id: str, role: AgentRole, llm_service: LLMServiceManager):
        self.agent_id = agent_id
        self.role = role
        self.llm_service = llm_service
        self.context = AgentContext(agent_id=agent_id, role=role)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    @abstractmethod
    async def execute_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """タスクを実行"""
        pass
    
    async def analyze_task(self, task: Task) -> Dict[str, Any]:
        """タスクを分析して実行計画を立てる"""
        prompt = f"""
        タスク分析を行ってください：
        
        タイトル: {task.title}
        説明: {task.description}
        要件: {', '.join(task.requirements)}
        
        以下の観点で分析してください：
        1. タスクの複雑度
        2. 必要な技術・知識
        3. 推定実行時間
        4. 潜在的な困難点
        5. 成功の条件
          JSON形式で回答してください。
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
            analysis = json.loads(response.text)
        except json.JSONDecodeError:
            # JSONパースに失敗した場合のフォールバック
            analysis = {
                "complexity": "medium",
                "required_skills": ["general"],
                "estimated_time": 300,
                "challenges": ["unknown"],
                "success_criteria": ["completion"]
            }
        
        return analysis
    
    def update_performance(self, task: Task, execution_time: float, success: bool):
        """パフォーマンス指標を更新"""
        if "total_tasks" not in self.context.performance_metrics:
            self.context.performance_metrics["total_tasks"] = 0
            self.context.performance_metrics["successful_tasks"] = 0
            self.context.performance_metrics["average_time"] = 0
        
        self.context.performance_metrics["total_tasks"] += 1
        if success:
            self.context.performance_metrics["successful_tasks"] += 1
        
        # 平均実行時間を更新
        total_tasks = self.context.performance_metrics["total_tasks"]
        current_avg = self.context.performance_metrics["average_time"]
        new_avg = (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        self.context.performance_metrics["average_time"] = new_avg
        
        # 成功率を計算
        success_rate = self.context.performance_metrics["successful_tasks"] / total_tasks
        self.context.performance_metrics["success_rate"] = success_rate


class CoordinatorAgent(BaseAgent):
    """調整役エージェント"""
    
    def __init__(self, llm_service: LLMServiceManager):
        super().__init__("coordinator", AgentRole.COORDINATOR, llm_service)
        self.context.capabilities = ["task_decomposition", "agent_coordination", "progress_monitoring"]
    
    async def execute_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """調整タスクを実行"""
        self.logger.info(f"Coordinating task: {task.title}")
        
        # タスクの分解
        subtasks = await self.decompose_task(task, context)
        
        # エージェントへの割り当て
        assignments = await self.assign_tasks(subtasks, context)
        
        return {
            "subtasks": subtasks,
            "assignments": assignments,
            "coordination_plan": "Sequential execution with checkpoints"
        }
    
    async def decompose_task(self, task: Task, context: Dict[str, Any]) -> List[Task]:
        """タスクを小さなサブタスクに分解"""
        prompt = f"""
        以下のタスクを実行可能な小さなサブタスクに分解してください：
        
        メインタスク: {task.title}
        説明: {task.description}
        要件: {', '.join(task.requirements)}
        
        各サブタスクについて以下を含むJSON配列で回答してください：
        - title: サブタスクのタイトル
        - description: 詳細説明
        - requirements: 要件リスト
        - estimated_duration: 推定時間（秒）        - dependencies: 依存関係（他のサブタスクのタイトル）
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
            subtask_data = json.loads(response.text)
            subtasks = []
            
            for data in subtask_data:
                subtask = Task(
                    title=data.get("title", "Untitled subtask"),
                    description=data.get("description", ""),
                    requirements=data.get("requirements", []),
                    estimated_duration=data.get("estimated_duration", 300),
                    dependencies=data.get("dependencies", [])
                )
                subtasks.append(subtask)
            
            return subtasks
        
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse subtasks: {e}")
            # フォールバック: 元のタスクをそのまま返す
            return [task]
    
    async def assign_tasks(self, tasks: List[Task], context: Dict[str, Any]) -> Dict[str, str]:
        """タスクをエージェントに割り当て"""
        assignments = {}
        available_agents = context.get("available_agents", [])
        
        for task in tasks:
            # 簡単なラウンドロビン割り当て（実際はより高度なロジックが必要）
            if available_agents:
                assigned_agent = available_agents[len(assignments) % len(available_agents)]
                assignments[task.id] = assigned_agent
            
        return assignments


class AnalyzerAgent(BaseAgent):
    """分析役エージェント"""
    
    def __init__(self, llm_service: LLMServiceManager):
        super().__init__("analyzer", AgentRole.ANALYZER, llm_service)
        self.context.capabilities = ["data_analysis", "requirement_analysis", "risk_assessment"]
    
    async def execute_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """分析タスクを実行"""
        self.logger.info(f"Analyzing task: {task.title}")
        
        analysis = await self.analyze_task(task)
        
        # リスク評価
        risks = await self.assess_risks(task, context)
        
        # 推奨事項
        recommendations = await self.generate_recommendations(task, analysis, risks)
        
        return {
            "analysis": analysis,
            "risks": risks,
            "recommendations": recommendations
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
        - impact: 影響度 (1-5)        - mitigation: 軽減策
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
    """実行役エージェント"""
    
    def __init__(self, llm_service: LLMServiceManager):
        super().__init__("executor", AgentRole.EXECUTOR, llm_service)
        self.context.capabilities = ["code_generation", "content_creation", "task_execution"]
    
    async def execute_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """実行タスクを実行"""
        self.logger.info(f"Executing task: {task.title}")
        
        # タスクの種類を判定
        task_type = await self.determine_task_type(task)
        
        # 適切な実行メソッドを選択
        if task_type == "code_generation":
            return await self.generate_code(task, context)
        elif task_type == "content_creation":
            return await self.create_content(task, context)
        else:
            return await self.execute_general_task(task, context)
    
    async def determine_task_type(self, task: Task) -> str:
        """タスクの種類を判定"""
        code_keywords = ["コード", "プログラム", "スクリプト", "実装", "開発"]
        content_keywords = ["文書", "レポート", "説明", "マニュアル", "記事"]
        
        description_lower = task.description.lower()
        title_lower = task.title.lower()
        
        if any(keyword in description_lower or keyword in title_lower for keyword in code_keywords):
            return "code_generation"
        elif any(keyword in description_lower or keyword in title_lower for keyword in content_keywords):
            return "content_creation"
        else:
            return "general"
    
    async def generate_code(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """コード生成タスク"""
        prompt = f"""
        以下の要件に基づいてコードを生成してください：
        
        タスク: {task.title}
        要件: {task.description}
        追加要件: {', '.join(task.requirements)}
        
        以下の形式でコードを生成してください：
        1. 使用する言語の選択理由
        2. アーキテクチャの説明
        3. 実装コード
        4. 使用方法の例
        5. テストケース
        """
          request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=2000,
                temperature=0.3  # コード生成では低い温度を使用
            )
        )
        
        response = await self.llm_service.generate(request)
        
        return {
            "type": "code_generation",
            "content": response.text,
            "language": "auto-detected",
            "status": "generated"
        }
    
    async def create_content(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツ作成タスク"""
        prompt = f"""
        以下の要件に基づいてコンテンツを作成してください：
        
        タスク: {task.title}
        内容: {task.description}
        要件: {', '.join(task.requirements)}
        
        構造化された読みやすいコンテンツを作成してください。
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
            "type": "content_creation",
            "content": response.text,
            "format": "markdown",
            "status": "created"
        }
    
    async def execute_general_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """一般的なタスク実行"""
        prompt = f"""
        以下のタスクを実行してください：
        
        タスク: {task.title}
        説明: {task.description}
        要件: {', '.join(task.requirements)}
        
        段階的に実行し、結果を報告してください。
        """
          request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=1200,
                temperature=0.7
            )
        )
        
        response = await self.llm_service.generate(request)
        
        return {
            "type": "general_execution",
            "result": response.text,
            "status": "completed"
        }


class ReviewerAgent(BaseAgent):
    """レビュー役エージェント"""
    
    def __init__(self, llm_service: LLMServiceManager):
        super().__init__("reviewer", AgentRole.REVIEWER, llm_service)
        self.context.capabilities = ["quality_assessment", "code_review", "content_review"]
    
    async def execute_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """レビュータスクを実行"""
        self.logger.info(f"Reviewing task: {task.title}")
        
        # レビュー対象を取得
        target_content = context.get("review_target", "")
        
        if not target_content:
            return {"status": "error", "message": "No content to review"}
        
        # レビューを実行
        review_result = await self.perform_review(target_content, task)
        
        return review_result
    
    async def perform_review(self, content: str, task: Task) -> Dict[str, Any]:
        """レビューを実行"""
        prompt = f"""
        以下のコンテンツをレビューしてください：
        
        レビュー対象:
        {content}
        
        レビュー観点:
        - 品質
        - 完全性
        - 正確性
        - 改善点
        
        以下の形式でレビュー結果をJSON形式で回答してください：
        {{
            "overall_score": 1-10の評価,
            "strengths": ["良い点のリスト"],
            "weaknesses": ["改善点のリスト"],
            "recommendations": ["具体的な推奨事項"],
            "approval_status": "approved/needs_revision/rejected"
        }}
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
            review_result = json.loads(response.text)
        except json.JSONDecodeError:
            review_result = {
                "overall_score": 5,
                "strengths": ["Review completed"],
                "weaknesses": ["Unable to parse detailed review"],
                "recommendations": ["Manual review recommended"],
                "approval_status": "needs_revision"
            }
        
        return review_result


class AgentOrchestrator:
    """エージェントオーケストレーター"""
    
    def __init__(self, llm_service: LLMServiceManager):
        self.llm_service = llm_service
        self.state = OrchestratorState()
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger(__name__)
        
        # デフォルトエージェントを初期化
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """デフォルトエージェントを初期化"""
        self.agents["coordinator"] = CoordinatorAgent(self.llm_service)
        self.agents["analyzer"] = AnalyzerAgent(self.llm_service)
        self.agents["executor"] = ExecutorAgent(self.llm_service)
        self.agents["reviewer"] = ReviewerAgent(self.llm_service)
        
        # エージェントコンテキストを状態に追加
        for agent_id, agent in self.agents.items():
            self.state.agents[agent_id] = agent.context
    
    async def start_session(self, mode: ProgressMode = ProgressMode.INTERACTIVE) -> str:
        """新しいセッションを開始"""
        self.state.mode = mode
        self.state.session_id = str(uuid.uuid4())
        self.state.is_running = True
        self.state.created_at = datetime.now()
        
        self.logger.info(f"Started new session: {self.state.session_id} in {mode.value} mode")
        return self.state.session_id
    
    async def add_task(self, title: str, description: str, requirements: List[str] = None) -> str:
        """新しいタスクを追加"""
        task = Task(
            title=title,
            description=description,
            requirements=requirements or []
        )
        
        self.state.tasks[task.id] = task
        self.logger.info(f"Added task: {task.title} (ID: {task.id})")
        
        return task.id
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """タスクを実行"""
        if task_id not in self.state.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.state.tasks[task_id]
        
        if self.state.mode == ProgressMode.AUTO:
            return await self._execute_auto_mode(task)
        elif self.state.mode == ProgressMode.INTERACTIVE:
            return await self._execute_interactive_mode(task)
        else:
            return await self._execute_hybrid_mode(task)
    
    async def _execute_auto_mode(self, task: Task) -> Dict[str, Any]:
        """全自動モードでタスクを実行"""
        self.logger.info(f"Executing task in AUTO mode: {task.title}")
        
        task.status = TaskStatus.RUNNING
        start_time = datetime.now()
        
        try:
            # 1. 調整エージェントがタスクを分解
            coordinator = self.agents["coordinator"]
            coordination_result = await coordinator.execute_task(task, {
                "available_agents": list(self.agents.keys()),
                "mode": "auto"
            })
            
            # 2. 分析エージェントが分析
            analyzer = self.agents["analyzer"]
            analysis_result = await analyzer.execute_task(task, {})
            
            # 3. 実行エージェントが実行
            executor = self.agents["executor"]
            execution_result = await executor.execute_task(task, {
                "analysis": analysis_result,
                "coordination": coordination_result
            })
            
            # 4. レビューエージェントがレビュー
            reviewer = self.agents["reviewer"]
            review_result = await reviewer.execute_task(task, {
                "review_target": str(execution_result.get("content", ""))
            })
            
            task.status = TaskStatus.COMPLETED
            task.result = {
                "coordination": coordination_result,
                "analysis": analysis_result,
                "execution": execution_result,
                "review": review_result
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # パフォーマンス更新
            for agent in self.agents.values():
                agent.update_performance(task, execution_time, True)
            
            return task.result
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.logger.error(f"Task execution failed: {e}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            for agent in self.agents.values():
                agent.update_performance(task, execution_time, False)
            
            raise
    
    async def _execute_interactive_mode(self, task: Task) -> Dict[str, Any]:
        """対話型モードでタスクを実行"""
        self.logger.info(f"Executing task in INTERACTIVE mode: {task.title}")
        
        task.status = TaskStatus.RUNNING
        
        # 対話型モードでは段階的に実行し、各ステップで確認を求める
        steps = []
        
        # ステップ1: 分析
        analyzer = self.agents["analyzer"]
        analysis_result = await analyzer.execute_task(task, {})
        steps.append({
            "step": "analysis",
            "result": analysis_result,
            "requires_approval": True
        })
        
        # ステップ2: 計画
        coordinator = self.agents["coordinator"]
        coordination_result = await coordinator.execute_task(task, {
            "available_agents": list(self.agents.keys()),
            "mode": "interactive"
        })
        steps.append({
            "step": "planning",
            "result": coordination_result,
            "requires_approval": True
        })
        
        # インタラクティブモードでは、実際の実行は承認後に行う
        task.result = {
            "mode": "interactive",
            "steps": steps,
            "status": "awaiting_approval"
        }
        
        return task.result
    
    async def _execute_hybrid_mode(self, task: Task) -> Dict[str, Any]:
        """ハイブリッドモードでタスクを実行"""
        # ハイブリッドモードは自動と対話の組み合わせ
        # 重要な決定は対話的に、ルーチン作業は自動的に
        return await self._execute_interactive_mode(task)
    
    async def approve_step(self, task_id: str, step_index: int, modifications: Dict[str, Any] = None) -> Dict[str, Any]:
        """対話型モードでステップを承認"""
        if task_id not in self.state.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.state.tasks[task_id]
        
        if task.result and "steps" in task.result:
            steps = task.result["steps"]
            if 0 <= step_index < len(steps):
                step = steps[step_index]
                step["approved"] = True
                step["modifications"] = modifications or {}
                
                # 全ステップが承認されたら実行を継続
                if all(s.get("approved", False) for s in steps if s.get("requires_approval", False)):
                    return await self._continue_interactive_execution(task)
        
        return {"status": "step_approved", "next_action": "awaiting_more_approvals"}
    
    async def _continue_interactive_execution(self, task: Task) -> Dict[str, Any]:
        """対話型モードで承認後の実行を継続"""
        executor = self.agents["executor"]
        execution_result = await executor.execute_task(task, task.result)
        
        reviewer = self.agents["reviewer"]
        review_result = await reviewer.execute_task(task, {
            "review_target": str(execution_result.get("content", ""))
        })
        
        task.status = TaskStatus.COMPLETED
        task.result.update({
            "execution": execution_result,
            "review": review_result,
            "status": "completed"
        })
        
        return task.result
    
    def get_session_status(self) -> Dict[str, Any]:
        """セッションの状態を取得"""
        return {
            "session_id": self.state.session_id,
            "mode": self.state.mode.value,
            "is_running": self.state.is_running,
            "total_tasks": len(self.state.tasks),
            "completed_tasks": len([t for t in self.state.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.state.tasks.values() if t.status == TaskStatus.FAILED]),
            "agents": {
                agent_id: {
                    "role": ctx.role.value,
                    "capabilities": ctx.capabilities,
                    "is_busy": ctx.is_busy,
                    "performance": ctx.performance_metrics
                }
                for agent_id, ctx in self.state.agents.items()
            }
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """特定のタスクの状態を取得"""
        if task_id not in self.state.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.state.tasks[task_id]
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "assigned_agent": task.assigned_agent,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "result": task.result,
            "error": task.error
        }
    
    async def stop_session(self):
        """セッションを停止"""
        self.state.is_running = False
        self.logger.info(f"Stopped session: {self.state.session_id}")
