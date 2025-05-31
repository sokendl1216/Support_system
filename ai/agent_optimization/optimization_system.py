"""
AIエージェント最適化システム統合ファサード

すべての最適化コンポーネントを統合管理するメインファサードクラス。
外部からの簡単なインターフェースでAIエージェントシステムの最適化機能を提供。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import os
from pathlib import Path

# 既存システムからインポート
from ..llm_service import LLMServiceManager
from ..agent_orchestrator import ProgressMode, Task, TaskStatus

# 最適化コンポーネントからインポート
from .enhanced_agent_orchestrator import EnhancedAgentOrchestrator
from .autonomous_learning_engine import AutonomousLearningEngine
from .performance_optimizer import PerformanceOptimizer
from .context_manager import AdvancedContextManager
from .self_diagnostic import SelfDiagnosticSystem

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """最適化システム設定"""
    # 学習設定
    learning_enabled: bool = True
    learning_rate: float = 0.1
    pattern_analysis_interval: int = 300  # 秒
    min_samples_for_learning: int = 10
    
    # パフォーマンス最適化設定
    performance_monitoring_enabled: bool = True
    performance_check_interval: int = 60  # 秒
    load_balancing_enabled: bool = True
    auto_scaling_enabled: bool = False
    
    # コンテキスト管理設定
    context_retention_days: int = 7
    max_context_entries: int = 10000
    auto_context_cleanup: bool = True
    context_consolidation_interval: int = 3600  # 秒
    
    # 診断設定
    health_monitoring_enabled: bool = True
    health_check_interval: int = 120  # 秒
    auto_recovery_enabled: bool = True
    alert_threshold: float = 0.7
    
    # データ永続化設定
    data_persistence_enabled: bool = True
    database_path: str = "ai_optimization.db"
    backup_interval: int = 86400  # 秒（1日）
    
    # 実験設定
    experimental_features_enabled: bool = False
    a_b_testing_enabled: bool = False
    feature_flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class SystemStatus:
    """システム全体のステータス"""
    status: str  # "healthy", "warning", "error", "initializing"
    uptime: timedelta
    total_tasks_processed: int
    active_sessions: int
    optimization_score: float
    last_optimization: Optional[datetime]
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class AIAgentOptimizationSystem:
    """AIエージェント最適化システム統合ファサード"""
    
    def __init__(self, llm_service: LLMServiceManager, config: Optional[OptimizationConfig] = None):
        """
        システム初期化
        
        Args:
            llm_service: LLMサービスマネージャー
            config: 最適化設定（Noneの場合はデフォルト設定を使用）
        """
        self.llm_service = llm_service
        self.config = config or OptimizationConfig()
        
        # システム状態
        self.start_time = datetime.now()
        self.is_initialized = False
        self.is_running = False
        
        # コアコンポーネント
        self.orchestrator: Optional[EnhancedAgentOrchestrator] = None
        self.learning_engine: Optional[AutonomousLearningEngine] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        self.context_manager: Optional[AdvancedContextManager] = None
        self.diagnostic_system: Optional[SelfDiagnosticSystem] = None
        
        # 統計情報
        self.stats = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "optimizations_applied": 0,
            "recoveries_performed": 0,
            "learning_iterations": 0
        }
        
        # イベントハンドラー
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        logger.info("AI Agent Optimization System initialized")
    
    async def initialize(self) -> bool:
        """
        システム全体を初期化
        
        Returns:
            bool: 初期化成功の可否
        """
        try:
            logger.info("Initializing AI Agent Optimization System...")
            
            # データベース初期化
            if self.config.data_persistence_enabled:
                await self._initialize_database()
            
            # コアコンポーネント初期化
            await self._initialize_components()
            
            # 設定検証
            if not await self._validate_configuration():
                logger.error("Configuration validation failed")
                return False
            
            # システム状態設定
            self.is_initialized = True
            
            # 初期化完了イベント発行
            await self._emit_event("system_initialized", {
                "timestamp": datetime.now(),
                "config": self.config.__dict__
            })
            
            logger.info("AI Agent Optimization System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    async def _initialize_database(self):
        """データベース初期化"""
        try:
            # データベースディレクトリ作成
            db_path = Path(self.config.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Database initialized at: {db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _initialize_components(self):
        """コアコンポーネント初期化"""
        try:
            # 学習エンジン
            if self.config.learning_enabled:
                self.learning_engine = AutonomousLearningEngine()
                logger.info("Learning engine initialized")
            
            # パフォーマンス最適化
            if self.config.performance_monitoring_enabled:
                self.performance_optimizer = PerformanceOptimizer()
                logger.info("Performance optimizer initialized")
            
            # コンテキスト管理
            self.context_manager = AdvancedContextManager(
                database_path=self.config.database_path
            )
            await self.context_manager.initialize()
            logger.info("Context manager initialized")
            
            # 診断システム
            if self.config.health_monitoring_enabled:
                self.diagnostic_system = SelfDiagnosticSystem()
                logger.info("Diagnostic system initialized")
            
            # 拡張オーケストレーター
            self.orchestrator = EnhancedAgentOrchestrator(
                llm_service=self.llm_service,
                optimization_config=self.config.__dict__
            )
            logger.info("Enhanced orchestrator initialized")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    async def _validate_configuration(self) -> bool:
        """設定検証"""
        try:
            # 必須コンポーネントの存在確認
            if not self.orchestrator:
                logger.error("Orchestrator not initialized")
                return False
            
            # 設定値の妥当性チェック
            if self.config.learning_rate <= 0 or self.config.learning_rate > 1:
                logger.error("Invalid learning rate")
                return False
            
            if self.config.performance_check_interval <= 0:
                logger.error("Invalid performance check interval")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    async def start(self) -> bool:
        """
        システムを開始
        
        Returns:
            bool: 開始成功の可否
        """
        if not self.is_initialized:
            logger.error("System not initialized. Call initialize() first.")
            return False
        
        try:
            logger.info("Starting AI Agent Optimization System...")
            
            # 最適化監視開始
            if self.orchestrator:
                await self.orchestrator.start_optimization_monitoring()
            
            # システム状態設定
            self.is_running = True
            
            # 開始イベント発行
            await self._emit_event("system_started", {
                "timestamp": datetime.now(),
                "uptime": datetime.now() - self.start_time
            })
            
            logger.info("AI Agent Optimization System started successfully")
            return True
            
        except Exception as e:
            logger.error(f"System start failed: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        システムを停止
        
        Returns:
            bool: 停止成功の可否
        """
        try:
            logger.info("Stopping AI Agent Optimization System...")
            
            # 最適化監視停止
            if self.orchestrator:
                await self.orchestrator.stop_optimization_monitoring()
            
            # システム状態設定
            self.is_running = False
            
            # 停止イベント発行
            await self._emit_event("system_stopped", {
                "timestamp": datetime.now(),
                "uptime": datetime.now() - self.start_time,
                "final_stats": self.stats.copy()
            })
            
            logger.info("AI Agent Optimization System stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"System stop failed: {e}")
            return False
    
    async def create_session(self, mode: Union[str, ProgressMode] = ProgressMode.AUTO) -> str:
        """
        新しいセッションを作成
        
        Args:
            mode: 進行モード
            
        Returns:
            str: セッションID
        """
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")
        
        if isinstance(mode, str):
            mode = ProgressMode(mode)
        
        session_id = await self.orchestrator.start_session(mode)
        
        # セッション作成イベント発行
        await self._emit_event("session_created", {
            "session_id": session_id,
            "mode": mode.value,
            "timestamp": datetime.now()
        })
        
        return session_id
    
    async def execute_task(self, session_id: str, title: str, description: str, 
                          requirements: Optional[Dict[str, Any]] = None,
                          use_optimization: bool = True) -> Dict[str, Any]:
        """
        タスクを実行
        
        Args:
            session_id: セッションID
            title: タスクタイトル
            description: タスク説明
            requirements: 追加要件
            use_optimization: 最適化機能使用フラグ
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")
        
        # タスク作成
        task = Task(
            title=title,
            description=description,
            context=requirements or {}
        )
        
        try:
            # タスク実行開始イベント
            await self._emit_event("task_started", {
                "task_id": task.id,
                "session_id": session_id,
                "title": title,
                "timestamp": datetime.now()
            })
            
            # 最適化機能付き実行 or 通常実行
            if use_optimization and self.orchestrator:
                result = await self.orchestrator.execute_task_with_optimization(session_id, task)
            else:
                result = await self.orchestrator.execute_task(session_id, task)
            
            # 統計更新
            self.stats["total_tasks_processed"] += 1
            self.stats["successful_tasks"] += 1
            
            # タスク完了イベント
            await self._emit_event("task_completed", {
                "task_id": task.id,
                "session_id": session_id,
                "success": True,
                "timestamp": datetime.now(),
                "result_summary": self._summarize_result(result)
            })
            
            return result
            
        except Exception as e:
            # 統計更新
            self.stats["total_tasks_processed"] += 1
            self.stats["failed_tasks"] += 1
            
            # タスク失敗イベント
            await self._emit_event("task_failed", {
                "task_id": task.id,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now()
            })
            
            raise
    
    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """結果要約を作成"""
        return {
            "type": result.get("type", "unknown"),
            "agent_id": result.get("agent_id", "unknown"),
            "success": "error" not in result,
            "has_optimization": "execution_metadata" in result
        }
    
    async def get_system_status(self) -> SystemStatus:
        """
        システム全体のステータスを取得
        
        Returns:
            SystemStatus: システムステータス
        """
        try:
            # 基本情報
            uptime = datetime.now() - self.start_time
            active_sessions = len(self.orchestrator.sessions) if self.orchestrator else 0
            
            # 最適化スコア計算
            optimization_score = await self._calculate_optimization_score()
            
            # 問題と推奨事項の収集
            issues, recommendations = await self._collect_issues_and_recommendations()
            
            # ステータス判定
            status = self._determine_system_status(optimization_score, issues)
            
            return SystemStatus(
                status=status,
                uptime=uptime,
                total_tasks_processed=self.stats["total_tasks_processed"],
                active_sessions=active_sessions,
                optimization_score=optimization_score,
                last_optimization=datetime.now(),  # 簡易実装
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return SystemStatus(
                status="error",
                uptime=datetime.now() - self.start_time,
                total_tasks_processed=0,
                active_sessions=0,
                optimization_score=0.0,
                last_optimization=None,
                issues=[f"Status collection failed: {str(e)}"]
            )
    
    async def _calculate_optimization_score(self) -> float:
        """最適化スコアを計算"""
        try:
            if not self.orchestrator:
                return 0.0
            
            # エージェントメトリクス取得
            metrics = await self.orchestrator.get_comprehensive_metrics()
            enhanced_metrics = metrics.get("enhanced_metrics", {})
            
            if not enhanced_metrics:
                return 0.5  # デフォルトスコア
            
            # 各エージェントの成功率の平均
            success_rates = [m.get("success_rate", 0.0) for m in enhanced_metrics.values()]
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
            
            # 品質スコア平均
            quality_scores = [m.get("quality_average", 0.0) for m in enhanced_metrics.values()]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # 最適化スコア = (成功率 * 0.6) + (品質 * 0.4)
            optimization_score = (avg_success_rate * 0.6) + (avg_quality * 0.4)
            
            return min(1.0, max(0.0, optimization_score))
            
        except Exception as e:
            logger.error(f"Optimization score calculation failed: {e}")
            return 0.0
    
    async def _collect_issues_and_recommendations(self) -> tuple[List[str], List[str]]:
        """問題と推奨事項を収集"""
        issues = []
        recommendations = []
        
        try:
            if not self.orchestrator:
                issues.append("Orchestrator not available")
                return issues, recommendations
            
            # エージェントメトリクス分析
            metrics = await self.orchestrator.get_comprehensive_metrics()
            enhanced_metrics = metrics.get("enhanced_metrics", {})
            
            for agent_id, agent_metrics in enhanced_metrics.items():
                success_rate = agent_metrics.get("success_rate", 0.0)
                error_count = agent_metrics.get("error_count", 0)
                quality_trend = agent_metrics.get("quality_trend", "stable")
                
                # 問題検出
                if success_rate < 0.7:
                    issues.append(f"Agent {agent_id} has low success rate: {success_rate:.2f}")
                
                if error_count > 10:
                    issues.append(f"Agent {agent_id} has high error count: {error_count}")
                
                if quality_trend == "declining":
                    issues.append(f"Agent {agent_id} shows declining quality trend")
                
                # 推奨事項生成
                if success_rate < 0.8:
                    recommendations.append(f"Consider retraining agent {agent_id}")
                
                if error_count > 5:
                    recommendations.append(f"Review error patterns for agent {agent_id}")
            
            # システム全体の推奨事項
            total_tasks = self.stats["total_tasks_processed"]
            if total_tasks > 0:
                error_rate = self.stats["failed_tasks"] / total_tasks
                if error_rate > 0.1:
                    recommendations.append("System error rate is high - consider global optimization")
            
        except Exception as e:
            issues.append(f"Issue collection failed: {str(e)}")
        
        return issues, recommendations
    
    def _determine_system_status(self, optimization_score: float, issues: List[str]) -> str:
        """システムステータスを判定"""
        if not self.is_running:
            return "stopped"
        
        if not self.is_initialized:
            return "initializing"
        
        critical_issues = [issue for issue in issues if "critical" in issue.lower() or "failed" in issue.lower()]
        
        if critical_issues:
            return "error"
        elif optimization_score < 0.5 or len(issues) > 5:
            return "warning"
        else:
            return "healthy"
    
    async def force_optimization(self):
        """手動で最適化を実行"""
        if not self.is_running:
            raise RuntimeError("System not running")
        
        if self.orchestrator:
            await self.orchestrator.force_optimization()
            self.stats["optimizations_applied"] += 1
            
            await self._emit_event("optimization_forced", {
                "timestamp": datetime.now(),
                "optimization_count": self.stats["optimizations_applied"]
            })
    
    async def get_comprehensive_report(self) -> Dict[str, Any]:
        """包括的なシステムレポートを取得"""
        try:
            status = await self.get_system_status()
            
            # メトリクス取得
            metrics = {}
            if self.orchestrator:
                metrics = await self.orchestrator.get_comprehensive_metrics()
            
            # 最適化情報
            optimization_info = {}
            if self.orchestrator:
                optimization_info = self.orchestrator.get_optimization_status()
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": status.__dict__,
                "statistics": self.stats.copy(),
                "configuration": self.config.__dict__,
                "optimization_info": optimization_info,
                "agent_metrics": metrics,
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "is_healthy": status.status == "healthy"
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "system_status": "report_generation_failed"
            }
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """イベントハンドラーを追加"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Any):
        """イベントを発行"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Event handler error for {event_type}: {e}")
    
    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            logger.info("Cleaning up AI Agent Optimization System...")
            
            # システム停止
            if self.is_running:
                await self.stop()
            
            # コンポーネントクリーンアップ
            if self.context_manager:
                await self.context_manager.cleanup_old_contexts(
                    datetime.now() - timedelta(days=self.config.context_retention_days)
                )
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# 便利な関数群

async def create_optimized_ai_system(llm_service: LLMServiceManager, 
                                   config: Optional[OptimizationConfig] = None) -> AIAgentOptimizationSystem:
    """
    最適化されたAIシステムを作成し初期化
    
    Args:
        llm_service: LLMサービスマネージャー
        config: 最適化設定
        
    Returns:
        AIAgentOptimizationSystem: 初期化済みシステム
    """
    system = AIAgentOptimizationSystem(llm_service, config)
    
    if await system.initialize():
        return system
    else:
        raise RuntimeError("Failed to initialize AI Agent Optimization System")


def create_default_optimization_config() -> OptimizationConfig:
    """デフォルト最適化設定を作成"""
    return OptimizationConfig(
        learning_enabled=True,
        performance_monitoring_enabled=True,
        health_monitoring_enabled=True,
        data_persistence_enabled=True,
        auto_recovery_enabled=True
    )
