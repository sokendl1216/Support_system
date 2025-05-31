"""
自己診断・修復システム
AIエージェントのヘルスモニタリング、自動エラー回復、パフォーマンス劣化検出
"""

import asyncio
import logging
import traceback
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import threading
import json
from statistics import mean, stdev
import warnings

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """ヘルス状態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    RECOVERING = "recovering"


class IssueType(Enum):
    """問題タイプ"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HIGH_ERROR_RATE = "high_error_rate"
    MEMORY_LEAK = "memory_leak"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMEOUT_ISSUES = "timeout_issues"
    CONNECTIVITY_ISSUES = "connectivity_issues"
    LLM_API_ISSUES = "llm_api_issues"
    TASK_QUEUE_OVERFLOW = "task_queue_overflow"


@dataclass
class HealthMetric:
    """ヘルスメトリクス"""
    metric_name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = field(default_factory=datetime.now)
    status: HealthStatus = HealthStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticIssue:
    """診断された問題"""
    issue_id: str
    issue_type: IssueType
    severity: HealthStatus
    description: str
    affected_components: List[str]
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    recovery_actions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    auto_recovery_attempted: bool = False
    recovery_success: bool = False


@dataclass
class RecoveryAction:
    """回復アクション"""
    action_id: str
    action_type: str
    description: str
    target_component: str
    execution_func: Callable
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    success_rate: float = 0.0
    execution_count: int = 0


class SelfDiagnosticSystem:
    """自己診断・修復システム"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.active_issues: Dict[str, DiagnosticIssue] = {}
        self.resolved_issues: List[DiagnosticIssue] = []
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.agent_health: Dict[str, HealthStatus] = {}
        self.system_health: HealthStatus = HealthStatus.UNKNOWN
        
        # 監視スレッド
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        
        # 統計情報
        self.diagnostic_stats = {
            "total_checks": 0,
            "issues_detected": 0,
            "auto_recoveries_attempted": 0,
            "successful_recoveries": 0,
            "false_positives": 0,
            "last_check": None
        }
        
        # 回復アクションを初期化
        self._initialize_recovery_actions()
        
        logger.info("Self-Diagnostic System initialized")
    
    def _initialize_recovery_actions(self):
        """回復アクションを初期化"""
        actions = [
            RecoveryAction(
                action_id="restart_agent",
                action_type="restart",
                description="エージェントを再起動",
                target_component="agent",
                execution_func=self._restart_agent,
                priority=3
            ),
            RecoveryAction(
                action_id="clear_task_queue",
                action_type="queue_management",
                description="タスクキューをクリア",
                target_component="task_queue",
                execution_func=self._clear_task_queue,
                priority=2
            ),
            RecoveryAction(
                action_id="reduce_concurrent_tasks",
                action_type="load_reduction",
                description="同時実行タスク数を削減",
                target_component="orchestrator",
                execution_func=self._reduce_concurrent_tasks,
                priority=1
            ),
            RecoveryAction(
                action_id="garbage_collection",
                action_type="memory_management",
                description="ガベージコレクション実行",
                target_component="system",
                execution_func=self._force_garbage_collection,
                priority=1
            ),
            RecoveryAction(
                action_id="reconnect_llm",
                action_type="connectivity",
                description="LLMプロバイダーに再接続",
                target_component="llm_provider",
                execution_func=self._reconnect_llm_provider,
                priority=2
            ),
            RecoveryAction(
                action_id="reset_agent_context",
                action_type="context_management",
                description="エージェントコンテキストをリセット",
                target_component="agent",
                execution_func=self._reset_agent_context,
                priority=2
            )
        ]
        
        for action in actions:
            self.recovery_actions[action.action_id] = action
        
        logger.info(f"Initialized {len(actions)} recovery actions")
    
    def start_monitoring(self):
        """監視を開始"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Self-diagnostic monitoring started")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        logger.info("Self-diagnostic monitoring stopped")
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.is_monitoring:
            try:
                asyncio.run(self._perform_health_check())
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in diagnostic monitoring loop: {e}")
                time.sleep(5)
    
    async def _perform_health_check(self):
        """ヘルスチェックを実行"""
        self.diagnostic_stats["total_checks"] += 1
        self.diagnostic_stats["last_check"] = datetime.now()
        
        try:
            # システムメトリクスを収集
            system_metrics = await self._collect_system_metrics()
            
            # エージェントメトリクスを収集
            agent_metrics = await self._collect_agent_metrics()
            
            # 問題を診断
            issues = await self._diagnose_issues(system_metrics, agent_metrics)
            
            # 新しい問題を処理
            for issue in issues:
                await self._handle_new_issue(issue)
            
            # システム全体のヘルス状態を更新
            self._update_system_health()
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            traceback.print_exc()
    
    async def _collect_system_metrics(self) -> Dict[str, HealthMetric]:
        """システムメトリクスを収集"""
        metrics = {}
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics["cpu_usage"] = HealthMetric(
                metric_name="cpu_usage",
                value=cpu_percent,
                threshold_warning=70.0,
                threshold_critical=90.0
            )
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            metrics["memory_usage"] = HealthMetric(
                metric_name="memory_usage",
                value=memory.percent,
                threshold_warning=80.0,
                threshold_critical=95.0
            )
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            metrics["disk_usage"] = HealthMetric(
                metric_name="disk_usage",
                value=disk.percent,
                threshold_warning=85.0,
                threshold_critical=95.0
            )
            
            # プロセス数
            process_count = len(psutil.pids())
            metrics["process_count"] = HealthMetric(
                metric_name="process_count",
                value=process_count,
                threshold_warning=1000,
                threshold_critical=1500
            )
            
            # メトリクスのステータスを評価
            for metric in metrics.values():
                if metric.value >= metric.threshold_critical:
                    metric.status = HealthStatus.CRITICAL
                elif metric.value >= metric.threshold_warning:
                    metric.status = HealthStatus.WARNING
                else:
                    metric.status = HealthStatus.HEALTHY
                
                # 履歴に追加
                self.health_metrics[metric.metric_name].append(metric)
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
        
        return metrics
    
    async def _collect_agent_metrics(self) -> Dict[str, Dict[str, HealthMetric]]:
        """エージェントメトリクスを収集"""
        agent_metrics = {}
        
        # この実装では、エージェントオーケストレーターからメトリクスを取得する想定
        # 実際の統合時に具体的な実装が必要
        
        return agent_metrics
    
    async def _diagnose_issues(self, system_metrics: Dict[str, HealthMetric],
                             agent_metrics: Dict[str, Dict[str, HealthMetric]]) -> List[DiagnosticIssue]:
        """問題を診断"""
        issues = []
        
        # システムレベルの問題診断
        issues.extend(await self._diagnose_system_issues(system_metrics))
        
        # エージェントレベルの問題診断
        issues.extend(await self._diagnose_agent_issues(agent_metrics))
        
        # トレンド分析による問題検出
        issues.extend(await self._diagnose_trend_issues())
        
        return issues
    
    async def _diagnose_system_issues(self, metrics: Dict[str, HealthMetric]) -> List[DiagnosticIssue]:
        """システムレベルの問題を診断"""
        issues = []
        
        # CPU使用率の問題
        if "cpu_usage" in metrics:
            cpu_metric = metrics["cpu_usage"]
            if cpu_metric.status == HealthStatus.CRITICAL:
                issues.append(DiagnosticIssue(
                    issue_id=f"cpu_critical_{int(time.time())}",
                    issue_type=IssueType.RESOURCE_EXHAUSTION,
                    severity=HealthStatus.CRITICAL,
                    description=f"CPU使用率が危険レベル: {cpu_metric.value:.1f}%",
                    affected_components=["system"],
                    detected_at=datetime.now(),
                    metrics={"cpu_usage": cpu_metric.value}
                ))
        
        # メモリ使用率の問題
        if "memory_usage" in metrics:
            memory_metric = metrics["memory_usage"]
            if memory_metric.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                # メモリリークの可能性をチェック
                memory_history = list(self.health_metrics["memory_usage"])
                if len(memory_history) >= 10:
                    recent_memory = [m.value for m in memory_history[-10:]]
                    if self._is_increasing_trend(recent_memory):
                        issues.append(DiagnosticIssue(
                            issue_id=f"memory_leak_{int(time.time())}",
                            issue_type=IssueType.MEMORY_LEAK,
                            severity=memory_metric.status,
                            description=f"メモリリークの可能性: {memory_metric.value:.1f}% (上昇トレンド)",
                            affected_components=["system"],
                            detected_at=datetime.now(),
                            metrics={"memory_usage": memory_metric.value, "trend": "increasing"}
                        ))
        
        return issues
    
    async def _diagnose_agent_issues(self, agent_metrics: Dict[str, Dict[str, HealthMetric]]) -> List[DiagnosticIssue]:
        """エージェントレベルの問題を診断"""
        issues = []
        
        for agent_id, metrics in agent_metrics.items():
            # 応答時間の問題
            if "response_time" in metrics:
                response_metric = metrics["response_time"]
                if response_metric.value > 30.0:  # 30秒以上の応答時間
                    issues.append(DiagnosticIssue(
                        issue_id=f"slow_response_{agent_id}_{int(time.time())}",
                        issue_type=IssueType.PERFORMANCE_DEGRADATION,
                        severity=HealthStatus.WARNING,
                        description=f"エージェント {agent_id} の応答時間が遅延: {response_metric.value:.1f}秒",
                        affected_components=[agent_id],
                        detected_at=datetime.now(),
                        metrics={"response_time": response_metric.value}
                    ))
            
            # エラー率の問題
            if "error_rate" in metrics:
                error_metric = metrics["error_rate"]
                if error_metric.value > 0.2:  # 20%以上のエラー率
                    issues.append(DiagnosticIssue(
                        issue_id=f"high_error_rate_{agent_id}_{int(time.time())}",
                        issue_type=IssueType.HIGH_ERROR_RATE,
                        severity=HealthStatus.CRITICAL if error_metric.value > 0.5 else HealthStatus.WARNING,
                        description=f"エージェント {agent_id} のエラー率が高い: {error_metric.value:.1%}",
                        affected_components=[agent_id],
                        detected_at=datetime.now(),
                        metrics={"error_rate": error_metric.value}
                    ))
        
        return issues
    
    async def _diagnose_trend_issues(self) -> List[DiagnosticIssue]:
        """トレンド分析による問題診断"""
        issues = []
        
        # 各メトリクスのトレンドを分析
        for metric_name, history in self.health_metrics.items():
            if len(history) >= 20:  # 十分なデータがある場合
                recent_values = [m.value for m in list(history)[-20:]]
                
                # 性能劣化のトレンド検出
                if metric_name in ["response_time", "error_rate"]:
                    if self._is_increasing_trend(recent_values):
                        trend_rate = self._calculate_trend_rate(recent_values)
                        if trend_rate > 0.1:  # 10%以上の増加トレンド
                            issues.append(DiagnosticIssue(
                                issue_id=f"trend_degradation_{metric_name}_{int(time.time())}",
                                issue_type=IssueType.PERFORMANCE_DEGRADATION,
                                severity=HealthStatus.WARNING,
                                description=f"{metric_name} に性能劣化のトレンドを検出 (増加率: {trend_rate:.1%})",
                                affected_components=["system"],
                                detected_at=datetime.now(),
                                metrics={"metric": metric_name, "trend_rate": trend_rate}
                            ))
        
        return issues
    
    def _is_increasing_trend(self, values: List[float]) -> bool:
        """増加トレンドかどうかを判定"""
        if len(values) < 5:
            return False
        
        # 線形回帰の傾きを計算
        n = len(values)
        x = list(range(n))
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        return slope > 0
    
    def _calculate_trend_rate(self, values: List[float]) -> float:
        """トレンド率を計算"""
        if len(values) < 2:
            return 0.0
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = mean(first_half)
        avg_second = mean(second_half)
        
        if avg_first == 0:
            return 0.0
        
        return (avg_second - avg_first) / avg_first
    
    async def _handle_new_issue(self, issue: DiagnosticIssue):
        """新しい問題を処理"""
        # 重複チェック
        existing_issue = self._find_similar_issue(issue)
        if existing_issue:
            logger.debug(f"Similar issue already exists: {existing_issue.issue_id}")
            return
        
        # 問題を登録
        self.active_issues[issue.issue_id] = issue
        self.diagnostic_stats["issues_detected"] += 1
        
        logger.warning(f"New issue detected: {issue.description}")
        
        # 自動回復を試行
        if self._should_attempt_auto_recovery(issue):
            await self._attempt_auto_recovery(issue)
    
    def _find_similar_issue(self, issue: DiagnosticIssue) -> Optional[DiagnosticIssue]:
        """類似の問題を検索"""
        for existing_issue in self.active_issues.values():
            if (existing_issue.issue_type == issue.issue_type and
                existing_issue.affected_components == issue.affected_components and
                (datetime.now() - existing_issue.detected_at).total_seconds() < 300):  # 5分以内
                return existing_issue
        return None
    
    def _should_attempt_auto_recovery(self, issue: DiagnosticIssue) -> bool:
        """自動回復を試行すべきかどうかを判定"""
        # 重要度が高すぎる場合は手動介入を待つ
        if issue.severity == HealthStatus.CRITICAL and issue.issue_type in [
            IssueType.RESOURCE_EXHAUSTION, IssueType.CONNECTIVITY_ISSUES
        ]:
            return False
        
        # 自動回復の試行回数制限
        if issue.auto_recovery_attempted:
            return False
        
        return True
    
    async def _attempt_auto_recovery(self, issue: DiagnosticIssue):
        """自動回復を試行"""
        issue.auto_recovery_attempted = True
        self.diagnostic_stats["auto_recoveries_attempted"] += 1
        
        logger.info(f"Attempting auto-recovery for issue: {issue.issue_id}")
        
        # 問題タイプに応じた回復アクションを選択
        recovery_actions = self._select_recovery_actions(issue)
        
        recovery_success = False
        executed_actions = []
        
        for action in recovery_actions:
            try:
                logger.info(f"Executing recovery action: {action.description}")
                
                # 回復アクションを実行
                success = await action.execution_func(issue)
                
                action.execution_count += 1
                executed_actions.append(action.action_id)
                
                if success:
                    recovery_success = True
                    action.success_rate = (action.success_rate * (action.execution_count - 1) + 1.0) / action.execution_count
                    logger.info(f"Recovery action successful: {action.description}")
                    break
                else:
                    action.success_rate = (action.success_rate * (action.execution_count - 1)) / action.execution_count
                    logger.warning(f"Recovery action failed: {action.description}")
                
            except Exception as e:
                logger.error(f"Error executing recovery action {action.action_id}: {e}")
                action.execution_count += 1
                action.success_rate = (action.success_rate * (action.execution_count - 1)) / action.execution_count
        
        # 回復結果を記録
        issue.recovery_actions = executed_actions
        issue.recovery_success = recovery_success
        
        if recovery_success:
            issue.resolved_at = datetime.now()
            self.resolved_issues.append(issue)
            del self.active_issues[issue.issue_id]
            self.diagnostic_stats["successful_recoveries"] += 1
            logger.info(f"Issue resolved through auto-recovery: {issue.issue_id}")
        else:
            logger.warning(f"Auto-recovery failed for issue: {issue.issue_id}")
    
    def _select_recovery_actions(self, issue: DiagnosticIssue) -> List[RecoveryAction]:
        """問題に対する回復アクションを選択"""
        actions = []
        
        # 問題タイプに応じたアクション選択
        if issue.issue_type == IssueType.MEMORY_LEAK:
            actions.extend([
                self.recovery_actions["garbage_collection"],
                self.recovery_actions["restart_agent"]
            ])
        elif issue.issue_type == IssueType.HIGH_ERROR_RATE:
            actions.extend([
                self.recovery_actions["reset_agent_context"],
                self.recovery_actions["reconnect_llm"],
                self.recovery_actions["restart_agent"]
            ])
        elif issue.issue_type == IssueType.PERFORMANCE_DEGRADATION:
            actions.extend([
                self.recovery_actions["reduce_concurrent_tasks"],
                self.recovery_actions["clear_task_queue"],
                self.recovery_actions["garbage_collection"]
            ])
        elif issue.issue_type == IssueType.RESOURCE_EXHAUSTION:
            actions.extend([
                self.recovery_actions["reduce_concurrent_tasks"],
                self.recovery_actions["garbage_collection"]
            ])
        elif issue.issue_type == IssueType.TASK_QUEUE_OVERFLOW:
            actions.extend([
                self.recovery_actions["clear_task_queue"],
                self.recovery_actions["reduce_concurrent_tasks"]
            ])
        
        # 優先度と成功率でソート
        actions.sort(key=lambda x: (x.priority, -x.success_rate))
        
        return actions
    
    # 回復アクション実装
    async def _restart_agent(self, issue: DiagnosticIssue) -> bool:
        """エージェントを再起動"""
        try:
            logger.info("Simulating agent restart")
            # 実際の実装では、エージェントの再初期化を行う
            await asyncio.sleep(2)  # シミュレーション
            return True
        except Exception as e:
            logger.error(f"Failed to restart agent: {e}")
            return False
    
    async def _clear_task_queue(self, issue: DiagnosticIssue) -> bool:
        """タスクキューをクリア"""
        try:
            logger.info("Simulating task queue clear")
            # 実際の実装では、待機中のタスクをクリアする
            await asyncio.sleep(1)  # シミュレーション
            return True
        except Exception as e:
            logger.error(f"Failed to clear task queue: {e}")
            return False
    
    async def _reduce_concurrent_tasks(self, issue: DiagnosticIssue) -> bool:
        """同時実行タスク数を削減"""
        try:
            logger.info("Simulating concurrent task reduction")
            # 実際の実装では、max_concurrent_tasksを調整する
            await asyncio.sleep(1)  # シミュレーション
            return True
        except Exception as e:
            logger.error(f"Failed to reduce concurrent tasks: {e}")
            return False
    
    async def _force_garbage_collection(self, issue: DiagnosticIssue) -> bool:
        """ガベージコレクションを強制実行"""
        try:
            import gc
            before_count = len(gc.get_objects())
            gc.collect()
            after_count = len(gc.get_objects())
            
            freed_objects = before_count - after_count
            logger.info(f"Garbage collection freed {freed_objects} objects")
            return freed_objects > 0
        except Exception as e:
            logger.error(f"Failed to perform garbage collection: {e}")
            return False
    
    async def _reconnect_llm_provider(self, issue: DiagnosticIssue) -> bool:
        """LLMプロバイダーに再接続"""
        try:
            logger.info("Simulating LLM provider reconnection")
            # 実際の実装では、LLMサービスの再接続を行う
            await asyncio.sleep(3)  # シミュレーション
            return True
        except Exception as e:
            logger.error(f"Failed to reconnect LLM provider: {e}")
            return False
    
    async def _reset_agent_context(self, issue: DiagnosticIssue) -> bool:
        """エージェントコンテキストをリセット"""
        try:
            logger.info("Simulating agent context reset")
            # 実際の実装では、エージェントのコンテキストをクリアする
            await asyncio.sleep(1)  # シミュレーション
            return True
        except Exception as e:
            logger.error(f"Failed to reset agent context: {e}")
            return False
    
    def _update_system_health(self):
        """システム全体のヘルス状態を更新"""
        if not self.active_issues:
            self.system_health = HealthStatus.HEALTHY
        else:
            severities = [issue.severity for issue in self.active_issues.values()]
            if HealthStatus.CRITICAL in severities:
                self.system_health = HealthStatus.CRITICAL
            elif HealthStatus.WARNING in severities:
                self.system_health = HealthStatus.WARNING
            else:
                self.system_health = HealthStatus.HEALTHY
    
    def get_health_status(self) -> Dict[str, Any]:
        """ヘルス状態を取得"""
        return {
            "system_health": self.system_health.value,
            "active_issues": len(self.active_issues),
            "resolved_issues": len(self.resolved_issues),
            "agent_health": {agent_id: status.value for agent_id, status in self.agent_health.items()},
            "diagnostic_stats": self.diagnostic_stats.copy(),
            "last_check": self.diagnostic_stats.get("last_check"),
            "monitoring_active": self.is_monitoring
        }
    
    def get_active_issues(self) -> List[Dict[str, Any]]:
        """アクティブな問題一覧を取得"""
        return [
            {
                "issue_id": issue.issue_id,
                "type": issue.issue_type.value,
                "severity": issue.severity.value,
                "description": issue.description,
                "affected_components": issue.affected_components,
                "detected_at": issue.detected_at.isoformat(),
                "auto_recovery_attempted": issue.auto_recovery_attempted,
                "recovery_success": issue.recovery_success
            }
            for issue in self.active_issues.values()
        ]
    
    def get_recovery_recommendations(self) -> List[Dict[str, Any]]:
        """回復推奨事項を取得"""
        recommendations = []
        
        for issue in self.active_issues.values():
            if not issue.auto_recovery_attempted or not issue.recovery_success:
                recovery_actions = self._select_recovery_actions(issue)
                
                recommendations.append({
                    "issue_id": issue.issue_id,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "recommended_actions": [
                        {
                            "action_id": action.action_id,
                            "description": action.description,
                            "success_rate": action.success_rate
                        }
                        for action in recovery_actions[:3]  # 上位3つの推奨アクション
                    ]
                })
        
        return recommendations
    
    def manual_recovery(self, issue_id: str, action_id: str) -> bool:
        """手動回復を実行"""
        if issue_id not in self.active_issues:
            logger.warning(f"Issue not found: {issue_id}")
            return False
        
        if action_id not in self.recovery_actions:
            logger.warning(f"Recovery action not found: {action_id}")
            return False
        
        issue = self.active_issues[issue_id]
        action = self.recovery_actions[action_id]
        
        try:
            # 非同期実行
            future = asyncio.run_coroutine_threadsafe(
                action.execution_func(issue),
                asyncio.get_event_loop()
            )
            success = future.result(timeout=30)
            
            if success:
                issue.resolved_at = datetime.now()
                issue.recovery_success = True
                issue.recovery_actions.append(action_id)
                
                self.resolved_issues.append(issue)
                del self.active_issues[issue_id]
                
                logger.info(f"Manual recovery successful for issue: {issue_id}")
                return True
            else:
                logger.warning(f"Manual recovery failed for issue: {issue_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error during manual recovery: {e}")
            return False
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.stop_monitoring()
        logger.info("Self-Diagnostic System cleaned up")
