"""
拡張エージェントオーケストレーター

既存のAgentOrchestratorに最適化機能を統合した拡張版。
以下の最適化機能を提供：
- 自律学習エンジン
- 動的パフォーマンス最適化
- 高度なコンテキスト管理
- 自己診断・修復システム
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import uuid

# 既存のエージェントシステムからインポート
from ..agent_orchestrator import (
    AgentOrchestrator, BaseAgent, Task, AgentContext, OrchestratorState,
    ProgressMode, TaskStatus, AgentRole
)
from ..llm_service import LLMServiceManager

# 最適化コンポーネントをインポート
from .autonomous_learning_engine import AutonomousLearningEngine, LearningRecord
from .performance_optimizer import PerformanceOptimizer, PerformanceMetrics
from .context_manager import AdvancedContextManager, ContextEntry
from .self_diagnostic import SelfDiagnosticSystem, HealthMetric

logger = logging.getLogger(__name__)


@dataclass
class EnhancedAgentMetrics:
    """拡張エージェントメトリクス"""
    agent_id: str
    role: AgentRole
    # 基本メトリクス
    tasks_completed: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    # 品質メトリクス
    quality_scores: List[float] = field(default_factory=list)
    error_count: int = 0
    recovery_count: int = 0
    # 学習メトリクス
    learning_rate: float = 0.0
    adaptation_count: int = 0
    specialization_score: float = 0.0
    # パフォーマンスメトリクス
    memory_usage: float = 0.0
    cpu_utilization: float = 0.0
    response_time_percentiles: Dict[str, float] = field(default_factory=dict)
    # タイムスタンプ
    last_activity: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


class EnhancedBaseAgent(BaseAgent):
    """拡張基本エージェントクラス - 最適化機能付き"""
    
    def __init__(self, agent_id: str, role: AgentRole, llm_service: LLMServiceManager,
                 learning_engine: Optional[AutonomousLearningEngine] = None,
                 performance_optimizer: Optional[PerformanceOptimizer] = None,
                 context_manager: Optional[AdvancedContextManager] = None):
        super().__init__(agent_id, role, llm_service)
        
        # 最適化コンポーネント
        self.learning_engine = learning_engine
        self.performance_optimizer = performance_optimizer
        self.context_manager = context_manager
        
        # 拡張メトリクス
        self.enhanced_metrics = EnhancedAgentMetrics(agent_id=agent_id, role=role)
        
        # 実行履歴
        self.execution_history: List[Dict[str, Any]] = []
        self.error_history: List[Dict[str, Any]] = []
        
        # 最適化設定
        self.optimization_enabled = True
        self.learning_enabled = True
        self.auto_recovery_enabled = True
    
    async def execute_with_optimization(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """最適化機能付きでタスクを実行"""
        start_time = datetime.now()
        execution_id = str(uuid.uuid4())
        
        try:
            # 事前最適化
            optimized_context = await self._pre_optimize(task, context)
            
            # コンテキスト継承
            if self.context_manager:
                inherited_context = await self.context_manager.inherit_context(
                    self.agent_id, task.id, optimized_context
                )
                optimized_context.update(inherited_context)
            
            # タスク実行
            result = await self.execute(task, optimized_context)
            
            # 実行後最適化
            enhanced_result = await self._post_optimize(task, result, start_time)
            
            # 学習記録
            await self._record_learning(task, optimized_context, enhanced_result, True)
            
            # メトリクス更新
            self._update_metrics(start_time, True, enhanced_result)
            
            return enhanced_result
            
        except Exception as e:
            # エラー記録と学習
            await self._record_learning(task, context, {"error": str(e)}, False)
            self._update_metrics(start_time, False, {"error": str(e)})
            
            # 自動回復試行
            if self.auto_recovery_enabled:
                recovery_result = await self._attempt_recovery(task, context, e)
                if recovery_result:
                    return recovery_result
            
            raise e
    
    async def _pre_optimize(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """事前最適化処理"""
        optimized_context = context.copy()
        
        # パフォーマンス最適化による推奨設定適用
        if self.performance_optimizer:
            try:
                recommendations = await self.performance_optimizer.get_optimal_agent_for_task(
                    task.description, [self.agent_id]
                )
                if recommendations and recommendations[0] == self.agent_id:
                    # 最適化推奨設定を適用
                    optimized_context["optimized"] = True
                    optimized_context["optimization_hints"] = {
                        "agent_selected": True,
                        "performance_score": getattr(recommendations, 'score', 0.8)
                    }
            except Exception as e:
                logger.warning(f"Performance optimization failed: {e}")
        
        # 学習エンジンによる推奨設定適用
        if self.learning_engine:
            try:
                agent_recommendations = await self.learning_engine.get_agent_recommendations(
                    task.description
                )
                if self.agent_id in agent_recommendations:
                    optimized_context["learning_hints"] = agent_recommendations[self.agent_id]
            except Exception as e:
                logger.warning(f"Learning optimization failed: {e}")
        
        return optimized_context
    
    async def _post_optimize(self, task: Task, result: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """事後最適化処理"""
        enhanced_result = result.copy()
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 結果メタデータ追加
        enhanced_result["execution_metadata"] = {
            "agent_id": self.agent_id,
            "execution_time": execution_time,
            "optimization_applied": self.optimization_enabled,
            "learning_applied": self.learning_enabled,
            "timestamp": datetime.now().isoformat()
        }
        
        # コンテキスト保存
        if self.context_manager:
            try:
                context_entry = ContextEntry(
                    context_id=str(uuid.uuid4()),
                    session_id=getattr(self.context, 'session_id', 'unknown'),
                    agent_id=self.agent_id,
                    task_id=task.id,
                    context_data={
                        "task": task.__dict__,
                        "result": enhanced_result,
                        "execution_time": execution_time
                    },
                    relevance_score=0.8,
                    timestamp=datetime.now()
                )
                await self.context_manager.store_context(context_entry)
            except Exception as e:
                logger.warning(f"Context storage failed: {e}")
        
        return enhanced_result
    
    async def _record_learning(self, task: Task, context: Dict[str, Any], result: Dict[str, Any], success: bool):
        """学習記録の保存"""
        if not self.learning_engine or not self.learning_enabled:
            return
        
        try:
            learning_record = LearningRecord(
                task_id=task.id,
                agent_id=self.agent_id,
                task_type=context.get("task_type", "general"),
                task_description=task.description,
                context_data=context,
                result_data=result,
                success=success,
                execution_time=(datetime.now() - task.created_at).total_seconds() if hasattr(task, 'created_at') else 0.0,
                quality_score=self._extract_quality_score(result),
                timestamp=datetime.now()
            )
            
            await self.learning_engine.record_execution(learning_record)
            
        except Exception as e:
            logger.warning(f"Learning record failed: {e}")
    
    def _extract_quality_score(self, result: Dict[str, Any]) -> float:
        """結果から品質スコアを抽出"""
        if "review" in result and isinstance(result["review"], dict):
            return result["review"].get("overall_score", 7.0) / 10.0
        elif "quality_score" in result:
            return float(result["quality_score"])
        else:
            return 0.7  # デフォルト品質スコア
    
    def _update_metrics(self, start_time: datetime, success: bool, result: Dict[str, Any]):
        """メトリクス更新"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 基本メトリクス更新
        self.enhanced_metrics.tasks_completed += 1
        self.enhanced_metrics.total_execution_time += execution_time
        self.enhanced_metrics.average_execution_time = (
            self.enhanced_metrics.total_execution_time / self.enhanced_metrics.tasks_completed
        )
        
        # 成功率更新
        if success:
            current_successes = self.enhanced_metrics.success_rate * (self.enhanced_metrics.tasks_completed - 1)
            self.enhanced_metrics.success_rate = (current_successes + 1) / self.enhanced_metrics.tasks_completed
        else:
            current_successes = self.enhanced_metrics.success_rate * (self.enhanced_metrics.tasks_completed - 1)
            self.enhanced_metrics.success_rate = current_successes / self.enhanced_metrics.tasks_completed
            self.enhanced_metrics.error_count += 1
        
        # 品質スコア更新
        quality_score = self._extract_quality_score(result)
        self.enhanced_metrics.quality_scores.append(quality_score)
        
        # アクティビティ更新
        self.enhanced_metrics.last_activity = datetime.now()
        
        # 実行履歴追加
        self.execution_history.append({
            "timestamp": datetime.now(),
            "execution_time": execution_time,
            "success": success,
            "quality_score": quality_score,
            "result_type": result.get("type", "unknown")
        })
        
        # 古い履歴を削除（最新100件のみ保持）
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    async def _attempt_recovery(self, task: Task, context: Dict[str, Any], error: Exception) -> Optional[Dict[str, Any]]:
        """自動回復試行"""
        try:
            # エラー記録
            self.error_history.append({
                "timestamp": datetime.now(),
                "task_id": task.id,
                "error": str(error),
                "context": context
            })
            
            # 簡単な回復試行（実際の実装ではより複雑な回復ロジック）
            if "timeout" in str(error).lower():
                # タイムアウトエラーの場合は再試行
                logger.info(f"Attempting recovery for timeout error in agent {self.agent_id}")
                await asyncio.sleep(1)  # 短い待機
                return await self.execute(task, context)
            
            elif "memory" in str(error).lower():
                # メモリエラーの場合はコンテキストを削減
                logger.info(f"Attempting recovery for memory error in agent {self.agent_id}")
                reduced_context = {k: v for k, v in context.items() if k in ["task_type", "priority"]}
                return await self.execute(task, reduced_context)
            
            self.enhanced_metrics.recovery_count += 1
            return None
            
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
            return None
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """拡張メトリクスを取得"""
        base_metrics = self.get_metrics()
        
        enhanced_data = {
            "agent_id": self.enhanced_metrics.agent_id,
            "role": self.enhanced_metrics.role.value,
            "tasks_completed": self.enhanced_metrics.tasks_completed,
            "success_rate": self.enhanced_metrics.success_rate,
            "average_execution_time": self.enhanced_metrics.average_execution_time,
            "total_execution_time": self.enhanced_metrics.total_execution_time,
            "error_count": self.enhanced_metrics.error_count,
            "recovery_count": self.enhanced_metrics.recovery_count,
            "learning_rate": self.enhanced_metrics.learning_rate,
            "adaptation_count": self.enhanced_metrics.adaptation_count,
            "specialization_score": self.enhanced_metrics.specialization_score,
            "quality_average": sum(self.enhanced_metrics.quality_scores) / len(self.enhanced_metrics.quality_scores) if self.enhanced_metrics.quality_scores else 0.0,
            "quality_trend": self._calculate_quality_trend(),
            "last_activity": self.enhanced_metrics.last_activity.isoformat() if self.enhanced_metrics.last_activity else None,
            "optimization_enabled": self.optimization_enabled,
            "learning_enabled": self.learning_enabled,
            "auto_recovery_enabled": self.auto_recovery_enabled
        }
        
        return {**base_metrics, **enhanced_data}
    
    def _calculate_quality_trend(self) -> str:
        """品質トレンドを計算"""
        if len(self.enhanced_metrics.quality_scores) < 2:
            return "insufficient_data"
        
        recent_scores = self.enhanced_metrics.quality_scores[-10:]  # 最近10件
        early_scores = self.enhanced_metrics.quality_scores[-20:-10] if len(self.enhanced_metrics.quality_scores) >= 20 else self.enhanced_metrics.quality_scores[:-10]
        
        if not early_scores:
            return "insufficient_data"
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        early_avg = sum(early_scores) / len(early_scores)
        
        if recent_avg > early_avg + 0.1:
            return "improving"
        elif recent_avg < early_avg - 0.1:
            return "declining"
        else:
            return "stable"


class EnhancedAgentOrchestrator(AgentOrchestrator):
    """拡張エージェントオーケストレーター - 最適化機能統合"""
    
    def __init__(self, llm_service: LLMServiceManager, 
                 optimization_config: Optional[Dict[str, Any]] = None):
        super().__init__(llm_service)
        
        # 最適化設定
        self.optimization_config = optimization_config or {}
        
        # 最適化コンポーネント初期化
        self.learning_engine = AutonomousLearningEngine()
        self.performance_optimizer = PerformanceOptimizer()
        self.context_manager = AdvancedContextManager()
        self.diagnostic_system = SelfDiagnosticSystem()
        
        # 拡張エージェント再初期化
        self._initialize_enhanced_agents()
        
        # 最適化タスク
        self._optimization_tasks: List[asyncio.Task] = []
        self._monitoring_active = False
        
        logger.info("Enhanced Agent Orchestrator initialized with optimization components")
    
    def _initialize_enhanced_agents(self):
        """拡張エージェントを初期化"""
        # 既存エージェントをクリア
        self.agents.clear()
        
        # 拡張エージェントを作成
        from ..agent_orchestrator import CoordinatorAgent, AnalyzerAgent, ExecutorAgent, ReviewerAgent
        
        enhanced_agents_config = [
            ("coordinator_1", CoordinatorAgent, AgentRole.COORDINATOR),
            ("analyzer_1", AnalyzerAgent, AgentRole.ANALYZER),
            ("executor_1", ExecutorAgent, AgentRole.EXECUTOR),
            ("reviewer_1", ReviewerAgent, AgentRole.REVIEWER)
        ]
        
        for agent_id, base_class, role in enhanced_agents_config:
            # 基本エージェントを作成
            base_agent = base_class(agent_id, self.llm_service)
            
            # 拡張エージェントでラップ
            enhanced_agent = EnhancedBaseAgent(
                agent_id=agent_id,
                role=role,
                llm_service=self.llm_service,
                learning_engine=self.learning_engine,
                performance_optimizer=self.performance_optimizer,
                context_manager=self.context_manager
            )
            
            # 元の実行メソッドを保持
            enhanced_agent._original_execute = base_agent.execute
            enhanced_agent.execute = enhanced_agent._original_execute
            
            self.agents[agent_id] = enhanced_agent
            logger.info(f"Initialized enhanced agent: {agent_id} ({role.value})")
    
    async def start_optimization_monitoring(self):
        """最適化監視を開始"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        # 各種監視タスクを開始
        monitoring_tasks = [
            self._performance_monitoring_loop(),
            self._learning_optimization_loop(),
            self._health_monitoring_loop(),
            self._context_cleanup_loop()
        ]
        
        self._optimization_tasks = [
            asyncio.create_task(task) for task in monitoring_tasks
        ]
        
        logger.info("Optimization monitoring started")
    
    async def stop_optimization_monitoring(self):
        """最適化監視を停止"""
        self._monitoring_active = False
        
        # 全監視タスクをキャンセル
        for task in self._optimization_tasks:
            task.cancel()
        
        # タスク完了を待機
        if self._optimization_tasks:
            await asyncio.gather(*self._optimization_tasks, return_exceptions=True)
        
        self._optimization_tasks.clear()
        logger.info("Optimization monitoring stopped")
    
    async def _performance_monitoring_loop(self):
        """パフォーマンス監視ループ"""
        while self._monitoring_active:
            try:
                # エージェントメトリクス収集
                agent_metrics = {}
                for agent_id, agent in self.agents.items():
                    if isinstance(agent, EnhancedBaseAgent):
                        metrics = agent.get_enhanced_metrics()
                        agent_metrics[agent_id] = PerformanceMetrics(
                            agent_id=agent_id,
                            response_time=metrics["average_execution_time"],
                            success_rate=metrics["success_rate"],
                            error_rate=metrics["error_count"] / max(metrics["tasks_completed"], 1),
                            throughput=metrics["tasks_completed"] / 3600,  # 1時間あたり
                            memory_usage=metrics.get("memory_usage", 0.0),
                            cpu_utilization=metrics.get("cpu_utilization", 0.0)
                        )
                
                # パフォーマンス最適化
                if agent_metrics:
                    await self.performance_optimizer.optimize_performance(list(agent_metrics.values()))
                
                await asyncio.sleep(60)  # 1分間隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _learning_optimization_loop(self):
        """学習最適化ループ"""
        while self._monitoring_active:
            try:
                # 学習パターン分析と最適化
                await self.learning_engine.analyze_patterns()
                
                # エージェント最適化適用
                for agent_id, agent in self.agents.items():
                    if isinstance(agent, EnhancedBaseAgent):
                        recommendations = await self.learning_engine.get_agent_recommendations("general")
                        if agent_id in recommendations:
                            # 最適化推奨を適用
                            agent.enhanced_metrics.learning_rate = recommendations[agent_id].get("learning_rate", 0.5)
                            agent.enhanced_metrics.adaptation_count += 1
                
                await asyncio.sleep(300)  # 5分間隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Learning optimization error: {e}")
                await asyncio.sleep(300)
    
    async def _health_monitoring_loop(self):
        """ヘルス監視ループ"""
        while self._monitoring_active:
            try:
                # システムヘルスチェック
                health_metrics = []
                for agent_id, agent in self.agents.items():
                    if isinstance(agent, EnhancedBaseAgent):
                        metrics = agent.get_enhanced_metrics()
                        health_metric = HealthMetric(
                            metric_name=f"agent_{agent_id}_health",
                            value=metrics["success_rate"],
                            threshold=0.8,
                            status="healthy" if metrics["success_rate"] >= 0.8 else "warning",
                            timestamp=datetime.now()
                        )
                        health_metrics.append(health_metric)
                
                # 診断と自動回復
                if health_metrics:
                    await self.diagnostic_system.run_diagnostics(health_metrics)
                
                await asyncio.sleep(120)  # 2分間隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(120)
    
    async def _context_cleanup_loop(self):
        """コンテキストクリーンアップループ"""
        while self._monitoring_active:
            try:
                # 古いコンテキストをクリーンアップ
                cutoff_time = datetime.now() - timedelta(hours=24)
                await self.context_manager.cleanup_old_contexts(cutoff_time)
                
                # メモリ統合
                await self.context_manager.consolidate_memory()
                
                await asyncio.sleep(3600)  # 1時間間隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Context cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def execute_task_with_optimization(self, session_id: str, task: Task, 
                                           approval_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """最適化機能付きでタスクを実行"""
        # 最適なエージェント選択
        optimal_agent_id = await self._select_optimal_agent(task)
        
        if optimal_agent_id and optimal_agent_id in self.agents:
            agent = self.agents[optimal_agent_id]
            if isinstance(agent, EnhancedBaseAgent):
                # 拡張実行
                return await agent.execute_with_optimization(task, {"session_id": session_id})
        
        # フォールバック：通常実行
        return await self.execute_task(session_id, task, approval_callback)
    
    async def _select_optimal_agent(self, task: Task) -> Optional[str]:
        """タスクに最適なエージェントを選択"""
        try:
            agent_ids = list(self.agents.keys())
            recommendations = await self.performance_optimizer.get_optimal_agent_for_task(
                task.description, agent_ids
            )
            
            if recommendations:
                return recommendations[0]
            
            # 学習エンジンからの推奨
            learning_recommendations = await self.learning_engine.get_agent_recommendations(
                task.description
            )
            
            if learning_recommendations:
                # 最高スコアのエージェントを選択
                best_agent = max(learning_recommendations.items(), key=lambda x: x[1].get("confidence", 0.0))
                return best_agent[0]
            
        except Exception as e:
            logger.warning(f"Optimal agent selection failed: {e}")
        
        return None
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """最適化システムのステータスを取得"""
        return {
            "monitoring_active": self._monitoring_active,
            "optimization_tasks": len(self._optimization_tasks),
            "learning_engine_status": "active" if self.learning_engine else "inactive",
            "performance_optimizer_status": "active" if self.performance_optimizer else "inactive",
            "context_manager_status": "active" if self.context_manager else "inactive",
            "diagnostic_system_status": "active" if self.diagnostic_system else "inactive",
            "enhanced_agents_count": sum(1 for agent in self.agents.values() if isinstance(agent, EnhancedBaseAgent)),
            "last_health_check": self.diagnostic_system.last_check_time.isoformat() if hasattr(self.diagnostic_system, 'last_check_time') else None
        }
    
    async def force_optimization(self):
        """手動で最適化を実行"""
        logger.info("Forcing manual optimization...")
        
        try:
            # パフォーマンス最適化
            agent_metrics = []
            for agent_id, agent in self.agents.items():
                if isinstance(agent, EnhancedBaseAgent):
                    metrics = agent.get_enhanced_metrics()
                    agent_metrics.append(PerformanceMetrics(
                        agent_id=agent_id,
                        response_time=metrics["average_execution_time"],
                        success_rate=metrics["success_rate"],
                        error_rate=metrics["error_count"] / max(metrics["tasks_completed"], 1),
                        throughput=metrics["tasks_completed"],
                        memory_usage=metrics.get("memory_usage", 0.0),
                        cpu_utilization=metrics.get("cpu_utilization", 0.0)
                    ))
            
            if agent_metrics:
                await self.performance_optimizer.optimize_performance(agent_metrics)
            
            # 学習最適化
            await self.learning_engine.analyze_patterns()
            
            # ヘルスチェック
            health_metrics = []
            for agent_id, agent in self.agents.items():
                if isinstance(agent, EnhancedBaseAgent):
                    metrics = agent.get_enhanced_metrics()
                    health_metrics.append(HealthMetric(
                        metric_name=f"agent_{agent_id}_health",
                        value=metrics["success_rate"],
                        threshold=0.8,
                        status="healthy" if metrics["success_rate"] >= 0.8 else "warning",
                        timestamp=datetime.now()
                    ))
            
            if health_metrics:
                await self.diagnostic_system.run_diagnostics(health_metrics)
            
            # コンテキスト統合
            await self.context_manager.consolidate_memory()
            
            logger.info("Manual optimization completed successfully")
            
        except Exception as e:
            logger.error(f"Manual optimization failed: {e}")
            raise
    
    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """包括的なメトリクスを取得"""
        base_metrics = self.get_agent_metrics()
        
        # 拡張メトリクス
        enhanced_metrics = {}
        for agent_id, agent in self.agents.items():
            if isinstance(agent, EnhancedBaseAgent):
                enhanced_metrics[agent_id] = agent.get_enhanced_metrics()
        
        # システム全体メトリクス
        system_metrics = {
            "total_tasks_completed": sum(m.get("tasks_completed", 0) for m in enhanced_metrics.values()),
            "average_success_rate": sum(m.get("success_rate", 0) for m in enhanced_metrics.values()) / len(enhanced_metrics) if enhanced_metrics else 0,
            "total_errors": sum(m.get("error_count", 0) for m in enhanced_metrics.values()),
            "total_recoveries": sum(m.get("recovery_count", 0) for m in enhanced_metrics.values()),
            "optimization_status": self.get_optimization_status()
        }
        
        return {
            "base_metrics": base_metrics,
            "enhanced_metrics": enhanced_metrics,
            "system_metrics": system_metrics,
            "timestamp": datetime.now().isoformat()
        }
