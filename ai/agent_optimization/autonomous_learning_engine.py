"""
AIエージェント自律学習エンジン

このモジュールは、AIエージェントが過去のタスク実行結果から自動的に学習し、
パフォーマンスを改善するための自律学習機能を提供します。
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import statistics

logger = logging.getLogger(__name__)

@dataclass
class LearningRecord:
    """学習記録データクラス"""
    agent_id: str
    task_type: str
    execution_time: float
    success: bool
    performance_score: float
    context: Dict[str, Any]
    feedback: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "execution_time": self.execution_time,
            "success": self.success,
            "performance_score": self.performance_score,
            "context": self.context,
            "feedback": self.feedback,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class LearningPattern:
    """学習パターンデータクラス"""
    pattern_id: str
    conditions: Dict[str, Any]
    success_rate: float
    avg_performance: float
    frequency: int
    confidence: float
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)

class AutonomousLearningEngine:
    """AIエージェント自律学習エンジン"""
    
    def __init__(self, data_dir: str = "ai/agent_optimization/data"):
        """
        自律学習エンジンの初期化
        
        Args:
            data_dir: 学習データの保存ディレクトリ
        """
        self.data_dir = data_dir
        self.learning_records: List[LearningRecord] = []
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self.agent_profiles: Dict[str, Dict[str, Any]] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
        # 学習パラメータ
        self.min_records_for_learning = 10
        self.pattern_confidence_threshold = 0.7
        self.learning_rate = 0.1
        self.decay_factor = 0.95
        
        # データディレクトリ作成
        os.makedirs(data_dir, exist_ok=True)
        
        # 既存データの読み込み
        self._load_learning_data()
        
        logger.info("自律学習エンジンが初期化されました")
    
    async def record_execution(self, record: LearningRecord) -> None:
        """
        タスク実行結果を記録
        
        Args:
            record: 学習記録
        """
        self.learning_records.append(record)
        
        # エージェントプロファイルを更新
        await self._update_agent_profile(record)
        
        # 記録数制限（メモリ管理）
        if len(self.learning_records) > 1000:
            self.learning_records = self.learning_records[-800:]
        
        # 定期的なパターン学習
        if len(self.learning_records) % 20 == 0:
            await self._trigger_pattern_learning()
        
        logger.debug(f"学習記録を追加: {record.agent_id} - {record.task_type}")
    
    async def _update_agent_profile(self, record: LearningRecord) -> None:
        """
        エージェントプロファイルを更新
        
        Args:
            record: 学習記録
        """
        agent_id = record.agent_id
        
        if agent_id not in self.agent_profiles:
            self.agent_profiles[agent_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "total_execution_time": 0.0,
                "avg_performance_score": 0.0,
                "task_type_performance": {},
                "strengths": [],
                "weaknesses": [],
                "last_updated": datetime.now()
            }
        
        profile = self.agent_profiles[agent_id]
        profile["total_executions"] += 1
        profile["total_execution_time"] += record.execution_time
        
        if record.success:
            profile["successful_executions"] += 1
        
        # 平均パフォーマンススコア更新
        current_avg = profile["avg_performance_score"]
        new_avg = (current_avg * (profile["total_executions"] - 1) + record.performance_score) / profile["total_executions"]
        profile["avg_performance_score"] = new_avg
        
        # タスクタイプ別パフォーマンス
        task_type = record.task_type
        if task_type not in profile["task_type_performance"]:
            profile["task_type_performance"][task_type] = {
                "count": 0,
                "success_rate": 0.0,
                "avg_score": 0.0,
                "avg_time": 0.0
            }
        
        task_perf = profile["task_type_performance"][task_type]
        task_perf["count"] += 1
        
        # 成功率更新
        if record.success:
            task_perf["success_rate"] = (task_perf["success_rate"] * (task_perf["count"] - 1) + 1.0) / task_perf["count"]
        else:
            task_perf["success_rate"] = (task_perf["success_rate"] * (task_perf["count"] - 1)) / task_perf["count"]
        
        # 平均スコア・時間更新
        task_perf["avg_score"] = (task_perf["avg_score"] * (task_perf["count"] - 1) + record.performance_score) / task_perf["count"]
        task_perf["avg_time"] = (task_perf["avg_time"] * (task_perf["count"] - 1) + record.execution_time) / task_perf["count"]
        
        profile["last_updated"] = datetime.now()
        
        # 強み・弱み分析
        await self._analyze_agent_strengths_weaknesses(agent_id)
    
    async def _analyze_agent_strengths_weaknesses(self, agent_id: str) -> None:
        """
        エージェントの強みと弱みを分析
        
        Args:
            agent_id: エージェントID
        """
        if agent_id not in self.agent_profiles:
            return
        
        profile = self.agent_profiles[agent_id]
        task_performances = profile["task_type_performance"]
        
        strengths = []
        weaknesses = []
        
        for task_type, perf in task_performances.items():
            if perf["count"] >= 5:  # 十分なデータがある場合のみ
                if perf["success_rate"] >= 0.8 and perf["avg_score"] >= 8.0:
                    strengths.append(f"高成功率タスク: {task_type}")
                elif perf["success_rate"] <= 0.5 or perf["avg_score"] <= 5.0:
                    weaknesses.append(f"低成功率タスク: {task_type}")
                
                if perf["avg_time"] <= profile["total_execution_time"] / profile["total_executions"] * 0.8:
                    strengths.append(f"高速実行タスク: {task_type}")
                elif perf["avg_time"] >= profile["total_execution_time"] / profile["total_executions"] * 1.5:
                    weaknesses.append(f"低速実行タスク: {task_type}")
        
        profile["strengths"] = strengths[:5]  # 最大5個
        profile["weaknesses"] = weaknesses[:5]  # 最大5個
    
    async def _trigger_pattern_learning(self) -> None:
        """パターン学習をトリガー"""
        try:
            await self._learn_success_patterns()
            await self._learn_failure_patterns()
            await self._optimize_agent_allocation()
            logger.info("パターン学習が完了しました")
        except Exception as e:
            logger.error(f"パターン学習中にエラーが発生: {e}")
    
    async def _learn_success_patterns(self) -> None:
        """成功パターンの学習"""
        successful_records = [r for r in self.learning_records if r.success and r.performance_score >= 7.0]
        
        if len(successful_records) < self.min_records_for_learning:
            return
        
        # タスクタイプ別にパターンを分析
        task_groups = {}
        for record in successful_records:
            if record.task_type not in task_groups:
                task_groups[record.task_type] = []
            task_groups[record.task_type].append(record)
        
        for task_type, records in task_groups.items():
            if len(records) < 5:
                continue
            
            # 共通の成功条件を抽出
            common_conditions = await self._extract_common_conditions(records)
            
            if common_conditions:
                pattern_id = f"success_{task_type}_{len(self.learned_patterns)}"
                success_rate = sum(1 for r in records if r.success) / len(records)
                avg_performance = sum(r.performance_score for r in records) / len(records)
                
                pattern = LearningPattern(
                    pattern_id=pattern_id,
                    conditions=common_conditions,
                    success_rate=success_rate,
                    avg_performance=avg_performance,
                    frequency=len(records),
                    confidence=min(success_rate, len(records) / 20.0),
                    recommendations=await self._generate_success_recommendations(common_conditions)
                )
                
                if pattern.confidence >= self.pattern_confidence_threshold:
                    self.learned_patterns[pattern_id] = pattern
                    logger.info(f"成功パターンを学習: {pattern_id}")
    
    async def _learn_failure_patterns(self) -> None:
        """失敗パターンの学習"""
        failed_records = [r for r in self.learning_records if not r.success or r.performance_score < 5.0]
        
        if len(failed_records) < self.min_records_for_learning:
            return
        
        # 失敗の共通要因を分析
        failure_groups = {}
        for record in failed_records:
            key = f"{record.agent_id}_{record.task_type}"
            if key not in failure_groups:
                failure_groups[key] = []
            failure_groups[key].append(record)
        
        for group_key, records in failure_groups.items():
            if len(records) < 3:
                continue
            
            common_failure_conditions = await self._extract_failure_conditions(records)
            
            if common_failure_conditions:
                pattern_id = f"failure_{group_key}_{len(self.learned_patterns)}"
                failure_rate = sum(1 for r in records if not r.success) / len(records)
                
                pattern = LearningPattern(
                    pattern_id=pattern_id,
                    conditions=common_failure_conditions,
                    success_rate=1.0 - failure_rate,
                    avg_performance=sum(r.performance_score for r in records) / len(records),
                    frequency=len(records),
                    confidence=min(failure_rate, len(records) / 15.0),
                    recommendations=await self._generate_failure_avoidance_recommendations(common_failure_conditions)
                )
                
                if pattern.confidence >= self.pattern_confidence_threshold:
                    self.learned_patterns[pattern_id] = pattern
                    logger.info(f"失敗パターンを学習: {pattern_id}")
    
    async def _extract_common_conditions(self, records: List[LearningRecord]) -> Dict[str, Any]:
        """成功記録から共通条件を抽出"""
        if not records:
            return {}
        
        common_conditions = {}
        
        # 実行時間の範囲
        execution_times = [r.execution_time for r in records]
        if execution_times:
            common_conditions["optimal_execution_time_range"] = {
                "min": min(execution_times),
                "max": max(execution_times),
                "avg": statistics.mean(execution_times)
            }
        
        # コンテキストの共通要素
        context_keys = set()
        for record in records:
            context_keys.update(record.context.keys())
        
        for key in context_keys:
            values = [r.context.get(key) for r in records if key in r.context]
            if values and len(set(str(v) for v in values)) <= len(values) * 0.7:  # 70%以上が共通
                common_conditions[f"context_{key}"] = max(set(values), key=values.count)
        
        return common_conditions
    
    async def _extract_failure_conditions(self, records: List[LearningRecord]) -> Dict[str, Any]:
        """失敗記録から失敗条件を抽出"""
        if not records:
            return {}
        
        failure_conditions = {}
        
        # 実行時間の異常値検出
        execution_times = [r.execution_time for r in records]
        if execution_times:
            avg_time = statistics.mean(execution_times)
            max_time = max(execution_times)
            if max_time > avg_time * 2:  # 平均の2倍以上
                failure_conditions["excessive_execution_time"] = max_time
        
        # 低パフォーマンススコアの条件
        low_score_records = [r for r in records if r.performance_score < 5.0]
        if low_score_records:
            failure_conditions["low_performance_indicators"] = await self._analyze_low_performance_context(low_score_records)
        
        return failure_conditions
    
    async def _analyze_low_performance_context(self, records: List[LearningRecord]) -> Dict[str, Any]:
        """低パフォーマンス記録のコンテキスト分析"""
        if not records:
            return {}
        
        indicators = {}
        
        # 共通のコンテキスト要素
        context_analysis = {}
        for record in records:
            for key, value in record.context.items():
                if key not in context_analysis:
                    context_analysis[key] = []
                context_analysis[key].append(value)
        
        for key, values in context_analysis.items():
            if len(values) >= len(records) * 0.6:  # 60%以上で共通
                indicators[f"common_{key}"] = max(set(str(v) for v in values), key=values.count)
        
        return indicators
    
    async def _generate_success_recommendations(self, conditions: Dict[str, Any]) -> List[str]:
        """成功条件から推奨事項を生成"""
        recommendations = []
        
        if "optimal_execution_time_range" in conditions:
            time_range = conditions["optimal_execution_time_range"]
            recommendations.append(f"実行時間を{time_range['min']:.1f}-{time_range['max']:.1f}秒の範囲に保つ")
        
        for key, value in conditions.items():
            if key.startswith("context_"):
                context_key = key.replace("context_", "")
                recommendations.append(f"コンテキスト「{context_key}」を「{value}」に設定")
        
        if not recommendations:
            recommendations.append("現在の設定を維持")
        
        return recommendations
    
    async def _generate_failure_avoidance_recommendations(self, conditions: Dict[str, Any]) -> List[str]:
        """失敗条件から回避推奨事項を生成"""
        recommendations = []
        
        if "excessive_execution_time" in conditions:
            max_time = conditions["excessive_execution_time"]
            recommendations.append(f"実行時間が{max_time:.1f}秒を超えないよう注意")
        
        if "low_performance_indicators" in conditions:
            indicators = conditions["low_performance_indicators"]
            for key, value in indicators.items():
                if key.startswith("common_"):
                    context_key = key.replace("common_", "")
                    recommendations.append(f"コンテキスト「{context_key}」が「{value}」の場合は代替手法を検討")
        
        if not recommendations:
            recommendations.append("失敗パターンの詳細分析が必要")
        
        return recommendations
    
    async def _optimize_agent_allocation(self) -> None:
        """エージェント割り当ての最適化"""
        optimization_record = {
            "timestamp": datetime.now().isoformat(),
            "agent_performances": {},
            "task_type_recommendations": {},
            "allocation_changes": []
        }
        
        # エージェント別パフォーマンス分析
        for agent_id, profile in self.agent_profiles.items():
            if profile["total_executions"] >= 10:
                success_rate = profile["successful_executions"] / profile["total_executions"]
                avg_performance = profile["avg_performance_score"]
                avg_time = profile["total_execution_time"] / profile["total_executions"]
                
                optimization_record["agent_performances"][agent_id] = {
                    "success_rate": success_rate,
                    "avg_performance": avg_performance,
                    "avg_execution_time": avg_time,
                    "efficiency_score": (success_rate * avg_performance) / (avg_time + 1)
                }
        
        # タスクタイプ別推奨エージェント
        task_type_agents = {}
        for agent_id, profile in self.agent_profiles.items():
            for task_type, perf in profile["task_type_performance"].items():
                if perf["count"] >= 5:
                    if task_type not in task_type_agents:
                        task_type_agents[task_type] = []
                    
                    efficiency = (perf["success_rate"] * perf["avg_score"]) / (perf["avg_time"] + 1)
                    task_type_agents[task_type].append((agent_id, efficiency))
        
        for task_type, agents in task_type_agents.items():
            # 効率順にソート
            agents.sort(key=lambda x: x[1], reverse=True)
            optimization_record["task_type_recommendations"][task_type] = {
                "primary_agent": agents[0][0] if agents else None,
                "backup_agents": [agent[0] for agent in agents[1:3]],
                "efficiency_scores": {agent[0]: agent[1] for agent in agents}
            }
        
        self.optimization_history.append(optimization_record)
        
        # 履歴制限
        if len(self.optimization_history) > 50:
            self.optimization_history = self.optimization_history[-30:]
    
    async def get_agent_recommendations(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスクに対するエージェント推奨事項を取得
        
        Args:
            task_type: タスクタイプ
            context: タスクコンテキスト
            
        Returns:
            推奨事項の辞書
        """
        recommendations = {
            "recommended_agent": None,
            "confidence": 0.0,
            "reasoning": [],
            "optimization_tips": [],
            "risk_warnings": []
        }
        
        # 最新の最適化履歴から推奨エージェントを取得
        if self.optimization_history:
            latest_optimization = self.optimization_history[-1]
            task_recommendations = latest_optimization.get("task_type_recommendations", {})
            
            if task_type in task_recommendations:
                task_rec = task_recommendations[task_type]
                recommendations["recommended_agent"] = task_rec["primary_agent"]
                recommendations["confidence"] = 0.8
                recommendations["reasoning"].append(f"エージェント「{task_rec['primary_agent']}」がタスクタイプ「{task_type}」で最高効率を記録")
        
        # 学習パターンからの推奨事項
        relevant_patterns = []
        for pattern in self.learned_patterns.values():
            if self._pattern_matches_context(pattern, task_type, context):
                relevant_patterns.append(pattern)
        
        # 信頼度順にソート
        relevant_patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        for pattern in relevant_patterns[:3]:  # 上位3パターン
            if pattern.pattern_id.startswith("success_"):
                recommendations["optimization_tips"].extend(pattern.recommendations)
            elif pattern.pattern_id.startswith("failure_"):
                recommendations["risk_warnings"].extend(pattern.recommendations)
        
        return recommendations
    
    def _pattern_matches_context(self, pattern: LearningPattern, task_type: str, context: Dict[str, Any]) -> bool:
        """パターンがコンテキストにマッチするかチェック"""
        # タスクタイプマッチ
        if task_type in pattern.pattern_id:
            return True
        
        # コンテキスト条件マッチ
        context_matches = 0
        context_conditions = 0
        
        for key, value in pattern.conditions.items():
            if key.startswith("context_"):
                context_conditions += 1
                context_key = key.replace("context_", "")
                if context_key in context and str(context[context_key]) == str(value):
                    context_matches += 1
        
        if context_conditions > 0:
            return context_matches / context_conditions >= 0.7
        
        return False
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """学習による洞察を取得"""
        insights = {
            "total_records": len(self.learning_records),
            "total_patterns": len(self.learned_patterns),
            "agent_count": len(self.agent_profiles),
            "top_performing_agents": [],
            "common_success_factors": [],
            "common_failure_factors": [],
            "optimization_trends": []
        }
        
        # トップパフォーミングエージェント
        if self.agent_profiles:
            sorted_agents = sorted(
                self.agent_profiles.items(),
                key=lambda x: x[1].get("avg_performance_score", 0),
                reverse=True
            )
            insights["top_performing_agents"] = [
                {
                    "agent_id": agent_id,
                    "avg_score": profile["avg_performance_score"],
                    "success_rate": profile["successful_executions"] / max(profile["total_executions"], 1),
                    "strengths": profile.get("strengths", [])
                }
                for agent_id, profile in sorted_agents[:5]
            ]
        
        # 成功・失敗要因
        success_patterns = [p for p in self.learned_patterns.values() if p.pattern_id.startswith("success_")]
        failure_patterns = [p for p in self.learned_patterns.values() if p.pattern_id.startswith("failure_")]
        
        if success_patterns:
            all_success_recommendations = []
            for pattern in success_patterns:
                all_success_recommendations.extend(pattern.recommendations)
            insights["common_success_factors"] = list(set(all_success_recommendations))[:10]
        
        if failure_patterns:
            all_failure_recommendations = []
            for pattern in failure_patterns:
                all_failure_recommendations.extend(pattern.recommendations)
            insights["common_failure_factors"] = list(set(all_failure_recommendations))[:10]
        
        return insights
    
    def _load_learning_data(self) -> None:
        """学習データを読み込み"""
        try:
            # 学習記録の読み込み
            records_file = os.path.join(self.data_dir, "learning_records.json")
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    records_data = json.load(f)
                
                for record_data in records_data:
                    record = LearningRecord(
                        agent_id=record_data["agent_id"],
                        task_type=record_data["task_type"],
                        execution_time=record_data["execution_time"],
                        success=record_data["success"],
                        performance_score=record_data["performance_score"],
                        context=record_data["context"],
                        feedback=record_data.get("feedback"),
                        timestamp=datetime.fromisoformat(record_data["timestamp"])
                    )
                    self.learning_records.append(record)
            
            # エージェントプロファイルの読み込み
            profiles_file = os.path.join(self.data_dir, "agent_profiles.json")
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    self.agent_profiles = json.load(f)
                
                # 日時の復元
                for profile in self.agent_profiles.values():
                    if "last_updated" in profile:
                        profile["last_updated"] = datetime.fromisoformat(profile["last_updated"])
            
            logger.info(f"学習データを読み込みました: {len(self.learning_records)}件の記録")
            
        except Exception as e:
            logger.error(f"学習データの読み込みエラー: {e}")
    
    async def save_learning_data(self) -> bool:
        """学習データを保存"""
        try:
            # 学習記録の保存
            records_file = os.path.join(self.data_dir, "learning_records.json")
            records_data = [record.to_dict() for record in self.learning_records]
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records_data, f, ensure_ascii=False, indent=2)
            
            # エージェントプロファイルの保存
            profiles_file = os.path.join(self.data_dir, "agent_profiles.json")
            profiles_data = {}
            for agent_id, profile in self.agent_profiles.items():
                profile_copy = profile.copy()
                if "last_updated" in profile_copy:
                    profile_copy["last_updated"] = profile_copy["last_updated"].isoformat()
                profiles_data[agent_id] = profile_copy
            
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, ensure_ascii=False, indent=2)
            
            # 学習パターンの保存
            patterns_file = os.path.join(self.data_dir, "learned_patterns.json")
            patterns_data = {}
            for pattern_id, pattern in self.learned_patterns.items():
                patterns_data[pattern_id] = {
                    "pattern_id": pattern.pattern_id,
                    "conditions": pattern.conditions,
                    "success_rate": pattern.success_rate,
                    "avg_performance": pattern.avg_performance,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "recommendations": pattern.recommendations,
                    "created_at": pattern.created_at.isoformat()
                }
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)
            
            logger.info("学習データを保存しました")
            return True
            
        except Exception as e:
            logger.error(f"学習データの保存エラー: {e}")
            return False
