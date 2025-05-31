"""
動的パフォーマンス最適化エンジン
AIエージェントのリアルタイムパフォーマンス最適化を行う
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    agent_id: str
    task_type: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success_rate: float
    error_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0
    throughput: float = 0.0


@dataclass
class LoadBalanceConfig:
    """負荷分散設定"""
    max_concurrent_tasks: int = 5
    memory_threshold: float = 80.0  # メモリ使用率閾値（%）
    cpu_threshold: float = 70.0     # CPU使用率閾値（%）
    response_time_threshold: float = 30.0  # 応答時間閾値（秒）
    enable_dynamic_allocation: bool = True
    enable_agent_scaling: bool = True


@dataclass
class OptimizationStrategy:
    """最適化戦略"""
    strategy_type: str
    priority: int
    conditions: Dict[str, Any]
    actions: List[str]
    effectiveness_score: float = 0.0
    usage_count: int = 0


class PerformanceOptimizer:
    """動的パフォーマンス最適化エンジン"""
    
    def __init__(self, config: Optional[LoadBalanceConfig] = None):
        self.config = config or LoadBalanceConfig()
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.agent_load: Dict[str, Dict[str, Any]] = {}
        self.optimization_strategies: List[OptimizationStrategy] = []
        self.active_optimizations: Dict[str, Any] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # パフォーマンス統計
        self.performance_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "avg_improvement": 0.0,
            "last_optimization": None
        }
        
        # 最適化戦略を初期化
        self._initialize_optimization_strategies()
        
        logger.info("Performance Optimizer initialized")
    
    def _initialize_optimization_strategies(self):
        """最適化戦略を初期化"""
        strategies = [
            OptimizationStrategy(
                strategy_type="load_redistribution",
                priority=1,
                conditions={"cpu_usage": ">70", "memory_usage": ">80"},
                actions=["redistribute_tasks", "scale_agents"]
            ),
            OptimizationStrategy(
                strategy_type="response_time_optimization",
                priority=2,
                conditions={"avg_response_time": ">30"},
                actions=["optimize_task_allocation", "enable_parallel_processing"]
            ),
            OptimizationStrategy(
                strategy_type="memory_optimization",
                priority=3,
                conditions={"memory_usage": ">75"},
                actions=["clear_caches", "optimize_memory_usage"]
            ),
            OptimizationStrategy(
                strategy_type="task_priority_adjustment",
                priority=4,
                conditions={"queue_length": ">10"},
                actions=["adjust_task_priorities", "enable_batch_processing"]
            ),
            OptimizationStrategy(
                strategy_type="agent_specialization",
                priority=5,
                conditions={"success_rate": "<0.8"},
                actions=["specialize_agents", "reassign_tasks"]
            )
        ]
        
        self.optimization_strategies = strategies
        logger.info(f"Initialized {len(strategies)} optimization strategies")
    
    def start_monitoring(self):
        """パフォーマンス監視を開始"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """パフォーマンス監視を停止"""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.is_monitoring:
            try:
                self._collect_system_metrics()
                self._evaluate_optimization_needs()
                time.sleep(10)  # 10秒間隔で監視
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """システムメトリクスを収集"""
        try:
            # システムリソース取得
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # 各エージェントの負荷情報を更新
            current_time = datetime.now()
            for agent_id in self.agent_load:
                if agent_id not in self.agent_load:
                    continue
                
                self.agent_load[agent_id].update({
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "last_updated": current_time
                })
                
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
    
    def record_performance(self, metrics: PerformanceMetrics):
        """パフォーマンスメトリクスを記録"""
        agent_id = metrics.agent_id
        
        # 履歴に追加
        self.performance_history[agent_id].append(metrics)
        
        # エージェント負荷情報を更新
        if agent_id not in self.agent_load:
            self.agent_load[agent_id] = {
                "active_tasks": 0,
                "total_tasks": 0,
                "avg_response_time": 0.0,
                "success_rate": 1.0,
                "last_updated": datetime.now()
            }
        
        load_info = self.agent_load[agent_id]
        load_info["total_tasks"] += 1
        load_info["last_updated"] = metrics.timestamp
        
        # 成功率の更新
        if metrics.error_count == 0:
            load_info["success_rate"] = (
                (load_info["success_rate"] * (load_info["total_tasks"] - 1) + 1.0) /
                load_info["total_tasks"]
            )
        else:
            load_info["success_rate"] = (
                (load_info["success_rate"] * (load_info["total_tasks"] - 1)) /
                load_info["total_tasks"]
            )
        
        # 平均応答時間の更新
        load_info["avg_response_time"] = (
            (load_info["avg_response_time"] * (load_info["total_tasks"] - 1) + metrics.execution_time) /
            load_info["total_tasks"]
        )
        
        logger.debug(f"Recorded performance for agent {agent_id}: {metrics.execution_time:.2f}s")
    
    def _evaluate_optimization_needs(self):
        """最適化の必要性を評価"""
        for strategy in self.optimization_strategies:
            if self._should_apply_strategy(strategy):
                asyncio.create_task(self._apply_optimization_strategy(strategy))
    
    def _should_apply_strategy(self, strategy: OptimizationStrategy) -> bool:
        """戦略を適用すべきかどうかを判定"""
        conditions = strategy.conditions
        
        for condition, threshold_str in conditions.items():
            if not self._evaluate_condition(condition, threshold_str):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: str, threshold_str: str) -> bool:
        """条件を評価"""
        try:
            # 閾値の解析
            operator = threshold_str[0] if threshold_str[0] in ['>', '<', '='] else '='
            threshold_value = float(threshold_str[1:] if operator in ['>', '<'] else threshold_str)
            
            # 現在値の取得
            current_value = self._get_current_metric_value(condition)
            if current_value is None:
                return False
            
            # 比較
            if operator == '>':
                return current_value > threshold_value
            elif operator == '<':
                return current_value < threshold_value
            else:
                return abs(current_value - threshold_value) < 0.1
                
        except (ValueError, IndexError):
            logger.warning(f"Invalid condition format: {condition}={threshold_str}")
            return False
    
    def _get_current_metric_value(self, metric_name: str) -> Optional[float]:
        """現在のメトリクス値を取得"""
        if metric_name == "cpu_usage":
            try:
                return psutil.cpu_percent()
            except:
                return None
        elif metric_name == "memory_usage":
            try:
                return psutil.virtual_memory().percent
            except:
                return None
        elif metric_name == "avg_response_time":
            if not self.agent_load:
                return None
            response_times = [info["avg_response_time"] for info in self.agent_load.values()]
            return mean(response_times) if response_times else None
        elif metric_name == "success_rate":
            if not self.agent_load:
                return None
            success_rates = [info["success_rate"] for info in self.agent_load.values()]
            return mean(success_rates) if success_rates else None
        elif metric_name == "queue_length":
            # 仮想的なキュー長（実装に応じて調整）
            return sum(info["active_tasks"] for info in self.agent_load.values())
        
        return None
    
    async def _apply_optimization_strategy(self, strategy: OptimizationStrategy):
        """最適化戦略を適用"""
        strategy_id = f"{strategy.strategy_type}_{int(time.time())}"
        
        if strategy_id in self.active_optimizations:
            return
        
        self.active_optimizations[strategy_id] = {
            "strategy": strategy,
            "start_time": datetime.now(),
            "status": "running"
        }
        
        logger.info(f"Applying optimization strategy: {strategy.strategy_type}")
        
        try:
            # 戦略に応じた最適化アクションを実行
            for action in strategy.actions:
                await self._execute_optimization_action(action, strategy)
            
            # 戦略の使用回数を増加
            strategy.usage_count += 1
            
            # 最適化の完了
            self.active_optimizations[strategy_id]["status"] = "completed"
            self.performance_stats["total_optimizations"] += 1
            self.performance_stats["successful_optimizations"] += 1
            self.performance_stats["last_optimization"] = datetime.now()
            
            logger.info(f"Successfully applied optimization strategy: {strategy.strategy_type}")
            
        except Exception as e:
            logger.error(f"Failed to apply optimization strategy {strategy.strategy_type}: {e}")
            self.active_optimizations[strategy_id]["status"] = "failed"
        finally:
            # アクティブな最適化から削除（一定時間後）
            await asyncio.sleep(60)
            self.active_optimizations.pop(strategy_id, None)
    
    async def _execute_optimization_action(self, action: str, strategy: OptimizationStrategy):
        """最適化アクションを実行"""
        if action == "redistribute_tasks":
            await self._redistribute_tasks()
        elif action == "scale_agents":
            await self._scale_agents()
        elif action == "optimize_task_allocation":
            await self._optimize_task_allocation()
        elif action == "enable_parallel_processing":
            await self._enable_parallel_processing()
        elif action == "clear_caches":
            await self._clear_caches()
        elif action == "optimize_memory_usage":
            await self._optimize_memory_usage()
        elif action == "adjust_task_priorities":
            await self._adjust_task_priorities()
        elif action == "enable_batch_processing":
            await self._enable_batch_processing()
        elif action == "specialize_agents":
            await self._specialize_agents()
        elif action == "reassign_tasks":
            await self._reassign_tasks()
        else:
            logger.warning(f"Unknown optimization action: {action}")
    
    async def _redistribute_tasks(self):
        """タスクを再分散"""
        logger.info("Redistributing tasks among agents")
        # 実装：負荷の高いエージェントから低いエージェントへタスクを移動
        
        # 負荷の高いエージェントを特定
        high_load_agents = []
        low_load_agents = []
        
        for agent_id, load_info in self.agent_load.items():
            avg_time = load_info.get("avg_response_time", 0)
            active_tasks = load_info.get("active_tasks", 0)
            
            if avg_time > self.config.response_time_threshold or active_tasks > self.config.max_concurrent_tasks:
                high_load_agents.append(agent_id)
            elif active_tasks < self.config.max_concurrent_tasks // 2:
                low_load_agents.append(agent_id)
        
        # 再分散の実行（仮想的な実装）
        if high_load_agents and low_load_agents:
            logger.info(f"Redistributing from {len(high_load_agents)} high-load agents to {len(low_load_agents)} low-load agents")
            # 実際の実装では、タスクキューの管理が必要
    
    async def _scale_agents(self):
        """エージェントのスケーリング"""
        logger.info("Scaling agents based on load")
        # 実装：必要に応じてエージェントの数を調整
    
    async def _optimize_task_allocation(self):
        """タスク割り当ての最適化"""
        logger.info("Optimizing task allocation")
        # 実装：エージェントの特性に基づいた最適な割り当て
    
    async def _enable_parallel_processing(self):
        """並列処理の有効化"""
        logger.info("Enabling parallel processing")
        # 実装：並列実行可能なタスクの特定と実行
    
    async def _clear_caches(self):
        """キャッシュのクリア"""
        logger.info("Clearing caches to free memory")
        # 実装：不要なキャッシュデータの削除
    
    async def _optimize_memory_usage(self):
        """メモリ使用量の最適化"""
        logger.info("Optimizing memory usage")
        # 実装：メモリ効率的なアルゴリズムの適用
    
    async def _adjust_task_priorities(self):
        """タスク優先度の調整"""
        logger.info("Adjusting task priorities")
        # 実装：重要度に基づく優先度の再設定
    
    async def _enable_batch_processing(self):
        """バッチ処理の有効化"""
        logger.info("Enabling batch processing")
        # 実装：類似タスクのバッチ化
    
    async def _specialize_agents(self):
        """エージェントの専門化"""
        logger.info("Specializing agents for specific tasks")
        # 実装：エージェントの得意分野への特化
    
    async def _reassign_tasks(self):
        """タスクの再割り当て"""
        logger.info("Reassigning tasks to more suitable agents")
        # 実装：より適切なエージェントへのタスク移動
    
    def get_optimal_agent_for_task(self, task_type: str, task_complexity: float = 1.0) -> Optional[str]:
        """タスクに最適なエージェントを取得"""
        if not self.agent_load:
            return None
        
        candidate_agents = []
        
        for agent_id, load_info in self.agent_load.items():
            if load_info["active_tasks"] >= self.config.max_concurrent_tasks:
                continue
            
            # パフォーマンス履歴から適性を判定
            agent_history = list(self.performance_history[agent_id])
            if not agent_history:
                score = 0.5  # デフォルトスコア
            else:
                # タスクタイプが一致する履歴のみを考慮
                relevant_history = [m for m in agent_history if m.task_type == task_type]
                if relevant_history:
                    avg_time = mean([m.execution_time for m in relevant_history])
                    avg_success = mean([1.0 if m.error_count == 0 else 0.0 for m in relevant_history])
                    avg_quality = mean([m.quality_score for m in relevant_history])
                    
                    # スコア計算（時間は逆数、成功率と品質は正の値）
                    score = (avg_success * 0.4 + avg_quality * 0.3 + (1.0 / (avg_time + 1)) * 0.3)
                else:
                    score = 0.5
            
            # 現在の負荷を考慮
            load_factor = 1.0 - (load_info["active_tasks"] / self.config.max_concurrent_tasks)
            final_score = score * load_factor
            
            candidate_agents.append((agent_id, final_score))
        
        if not candidate_agents:
            return None
        
        # 最高スコアのエージェントを選択
        candidate_agents.sort(key=lambda x: x[1], reverse=True)
        selected_agent = candidate_agents[0][0]
        
        logger.debug(f"Selected agent {selected_agent} for task type {task_type}")
        return selected_agent
    
    def predict_performance(self, agent_id: str, task_type: str) -> Dict[str, float]:
        """パフォーマンスを予測"""
        if agent_id not in self.performance_history:
            return {"execution_time": 30.0, "success_probability": 0.8, "quality_score": 0.7}
        
        agent_history = list(self.performance_history[agent_id])
        relevant_history = [m for m in agent_history if m.task_type == task_type]
        
        if not relevant_history:
            # 他のタスクタイプからの推定
            if agent_history:
                avg_time = mean([m.execution_time for m in agent_history[-10:]])
                avg_success = mean([1.0 if m.error_count == 0 else 0.0 for m in agent_history[-10:]])
                avg_quality = mean([m.quality_score for m in agent_history[-10:]])
            else:
                avg_time, avg_success, avg_quality = 30.0, 0.8, 0.7
        else:
            recent_history = relevant_history[-5:]  # 最近5件
            avg_time = mean([m.execution_time for m in recent_history])
            avg_success = mean([1.0 if m.error_count == 0 else 0.0 for m in recent_history])
            avg_quality = mean([m.quality_score for m in recent_history])
        
        return {
            "execution_time": avg_time,
            "success_probability": avg_success,
            "quality_score": avg_quality
        }
    
    def get_load_balancing_recommendations(self) -> List[Dict[str, Any]]:
        """負荷分散の推奨事項を取得"""
        recommendations = []
        
        if not self.agent_load:
            return recommendations
        
        # 負荷の不均衡をチェック
        load_values = [info["active_tasks"] for info in self.agent_load.values()]
        if len(load_values) > 1:
            max_load = max(load_values)
            min_load = min(load_values)
            
            if max_load - min_load > 2:  # 負荷差が2以上
                recommendations.append({
                    "type": "load_imbalance",
                    "severity": "medium",
                    "description": f"Load imbalance detected: max={max_load}, min={min_load}",
                    "action": "redistribute_tasks"
                })
        
        # 高負荷エージェントのチェック
        for agent_id, load_info in self.agent_load.items():
            if load_info["active_tasks"] > self.config.max_concurrent_tasks * 0.8:
                recommendations.append({
                    "type": "high_load",
                    "severity": "high",
                    "description": f"Agent {agent_id} is heavily loaded",
                    "action": "scale_or_redistribute"
                })
        
        # 応答時間の問題
        slow_agents = [
            agent_id for agent_id, load_info in self.agent_load.items()
            if load_info["avg_response_time"] > self.config.response_time_threshold
        ]
        
        if slow_agents:
            recommendations.append({
                "type": "slow_response",
                "severity": "medium",
                "description": f"Slow response detected in agents: {', '.join(slow_agents)}",
                "action": "optimize_or_reassign"
            })
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        total_agents = len(self.agent_load)
        total_tasks = sum(info["total_tasks"] for info in self.agent_load.values())
        
        if total_tasks > 0:
            avg_success_rate = mean([info["success_rate"] for info in self.agent_load.values()])
            avg_response_time = mean([info["avg_response_time"] for info in self.agent_load.values()])
        else:
            avg_success_rate = 0.0
            avg_response_time = 0.0
        
        return {
            "total_agents": total_agents,
            "total_tasks_processed": total_tasks,
            "average_success_rate": avg_success_rate,
            "average_response_time": avg_response_time,
            "optimization_stats": self.performance_stats.copy(),
            "active_optimizations": len(self.active_optimizations),
            "system_metrics": {
                "cpu_usage": self._get_current_metric_value("cpu_usage"),
                "memory_usage": self._get_current_metric_value("memory_usage")
            }
        }
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.stop_monitoring()
        self.executor.shutdown(wait=True)
        logger.info("Performance Optimizer cleaned up")
