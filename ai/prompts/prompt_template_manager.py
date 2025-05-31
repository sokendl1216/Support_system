#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロンプトテンプレート管理システム
Task 3-4: プロンプトエンジニアリング (テンプレート管理、バージョニング、A/Bテスト基盤)

機能:
- テンプレート管理とバージョニング
- 進行モード別テンプレート最適化
- A/Bテストフレームワーク
- コンテキストウィンドウ管理
- 高度なメトリクス分析
- 自動プロンプト最適化
- リアルタイム統計とダッシュボード
"""

import json
import os
import logging
import time
import hashlib
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """テンプレートタイプ"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    CONTEXT = "context"
    INSTRUCTION = "instruction"


class PromptMode(Enum):
    """プロンプトモード（進行モード別）"""
    INTERACTIVE = "interactive"
    AUTONOMOUS = "autonomous"
    HYBRID = "hybrid"


@dataclass
class TemplateMetadata:
    """テンプレートメタデータ"""
    template_id: str
    name: str
    version: str
    template_type: TemplateType
    mode: PromptMode
    description: str
    created_at: float
    updated_at: float
    author: str
    tags: List[str]
    performance_metrics: Dict[str, float]
    usage_count: int
    success_rate: float
    avg_response_time: float


@dataclass
class PromptTemplate:
    """プロンプトテンプレート"""
    metadata: TemplateMetadata
    template: str
    variables: List[str]
    constraints: Dict[str, Any]
    context_window_config: Dict[str, Any]
    optimization_params: Dict[str, Any]


@dataclass
class TemplateVariant:
    """A/Bテスト用テンプレートバリアント"""
    variant_id: str
    template_id: str
    template: str
    weight: float
    active: bool
    test_metrics: Dict[str, float]
    sample_size: int = 0
    conversion_rate: float = 0.0
    confidence_score: float = 0.0


@dataclass
class TestResult:
    """A/Bテスト結果"""
    test_id: str
    template_id: str
    variant_id: str
    start_time: float
    end_time: Optional[float]
    sample_size: int
    metrics: Dict[str, float]
    statistical_significance: bool
    confidence_level: float
    improvement_percentage: float


class ContextWindowManager:
    """コンテキストウィンドウ管理"""
    
    def __init__(self, default_max_tokens: int = 4096):
        self.default_max_tokens = default_max_tokens
        self.token_estimation_ratio = 4  # 1トークン ≈ 4文字（日本語）
    
    def estimate_tokens(self, text: str) -> int:
        """トークン数を推定"""
        return len(text) // self.token_estimation_ratio
    
    def fit_content(
        self, 
        components: List[Tuple[str, str]], 
        max_tokens: int = None
    ) -> List[Tuple[str, str]]:
        """コンテンツをトークン制限内に収める"""
        if max_tokens is None:
            max_tokens = self.default_max_tokens
        
        max_chars = max_tokens * self.token_estimation_ratio
        current_chars = 0
        fitted_components = []
        
        for component_name, text in components:
            if current_chars + len(text) <= max_chars:
                fitted_components.append((component_name, text))
                current_chars += len(text)
            else:
                # 残りの容量に合わせて切り詰め
                remaining_chars = max_chars - current_chars
                if remaining_chars > 100:  # 最低限の長さを確保
                    truncated_text = text[:remaining_chars - 3] + "..."
                    fitted_components.append((component_name, truncated_text))
                break
        
        return fitted_components


class PromptAnalytics:
    """プロンプト分析・統計システム"""
    
    def __init__(self):
        self.session_data: Dict[str, List[Dict[str, Any]]] = {}
        self.hourly_stats: Dict[str, Dict[str, float]] = {}
        
    def record_usage(
        self, 
        template_id: str, 
        variant_id: Optional[str],
        metrics: Dict[str, float],
        user_feedback: Optional[Dict[str, Any]] = None
    ):
        """使用状況を記録"""
        timestamp = time.time()
        
        record = {
            "timestamp": timestamp,
            "template_id": template_id,
            "variant_id": variant_id,
            "metrics": metrics,
            "user_feedback": user_feedback
        }
        
        if template_id not in self.session_data:
            self.session_data[template_id] = []
        
        self.session_data[template_id].append(record)
        self._update_hourly_stats(template_id, metrics)
    
    def _update_hourly_stats(self, template_id: str, metrics: Dict[str, float]):
        """時間別統計を更新"""
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        
        if hour_key not in self.hourly_stats:
            self.hourly_stats[hour_key] = {}
        
        if template_id not in self.hourly_stats[hour_key]:
            self.hourly_stats[hour_key][template_id] = {
                "usage_count": 0,
                "avg_response_time": 0.0,
                "success_rate": 0.0,
                "user_satisfaction": 0.0
            }
        
        stats = self.hourly_stats[hour_key][template_id]
        stats["usage_count"] += 1
        
        # 移動平均で更新
        for metric_name, value in metrics.items():
            if metric_name in stats:
                current = stats[metric_name]
                stats[metric_name] = (current * 0.9) + (value * 0.1)
    
    def get_template_analytics(
        self, 
        template_id: str,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """テンプレートの分析結果を取得"""
        cutoff_time = time.time() - (time_range_hours * 3600)
        
        if template_id not in self.session_data:
            return {"error": "No data available"}
        
        recent_data = [
            record for record in self.session_data[template_id]
            if record["timestamp"] > cutoff_time
        ]
        
        if not recent_data:
            return {"error": "No recent data"}
        
        # 統計計算
        response_times = [r["metrics"].get("response_time", 0) for r in recent_data]
        success_rates = [r["metrics"].get("success_rate", 0) for r in recent_data]
        satisfaction_scores = [
            r["user_feedback"].get("satisfaction", 0) 
            for r in recent_data 
            if r["user_feedback"]
        ]
        
        return {
            "template_id": template_id,
            "time_range_hours": time_range_hours,
            "total_usage": len(recent_data),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "success_rate": statistics.mean(success_rates) if success_rates else 0,
            "user_satisfaction": statistics.mean(satisfaction_scores) if satisfaction_scores else 0,
            "response_time_trend": self._calculate_trend(response_times),
            "usage_pattern": self._analyze_usage_pattern(recent_data),
            "top_error_types": self._analyze_errors(recent_data)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """値の傾向を計算"""
        if len(values) < 2:
            return "insufficient_data"
        
        recent_avg = statistics.mean(values[-len(values)//3:])
        overall_avg = statistics.mean(values)
        
        if recent_avg > overall_avg * 1.1:
            return "improving"
        elif recent_avg < overall_avg * 0.9:
            return "degrading"
        else:
            return "stable"
    
    def _analyze_usage_pattern(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """使用パターンを分析"""
        pattern = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        
        for record in data:
            hour = datetime.fromtimestamp(record["timestamp"]).hour
            if 6 <= hour < 12:
                pattern["morning"] += 1
            elif 12 <= hour < 18:
                pattern["afternoon"] += 1
            elif 18 <= hour < 22:
                pattern["evening"] += 1
            else:
                pattern["night"] += 1
        
        return pattern
    
    def _analyze_errors(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """エラーパターンを分析"""
        errors = {}
        
        for record in data:
            if record["metrics"].get("success_rate", 1.0) < 0.8:
                error_type = record["metrics"].get("error_type", "unknown")
                errors[error_type] = errors.get(error_type, 0) + 1
        
        return dict(sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5])


class AutoOptimizer:
    """自動プロンプト最適化システム"""
    
    def __init__(self, analytics: PromptAnalytics):
        self.analytics = analytics
        self.optimization_rules = {
            "response_time": {
                "threshold": 5.0,  # 5秒以上は遅い
                "actions": ["shorten_prompt", "simplify_instructions"]
            },
            "success_rate": {
                "threshold": 0.8,  # 80%未満は改善が必要
                "actions": ["add_examples", "clarify_instructions", "adjust_parameters"]
            },
            "user_satisfaction": {
                "threshold": 3.5,  # 5点満点で3.5未満
                "actions": ["personalize_tone", "add_context", "improve_formatting"]
            }
        }
    
    def analyze_and_suggest_optimizations(
        self, 
        template_id: str
    ) -> Dict[str, Any]:
        """最適化の提案を生成"""
        analytics = self.analytics.get_template_analytics(template_id)
        
        if "error" in analytics:
            return {"error": analytics["error"]}
        
        suggestions = {
            "template_id": template_id,
            "optimization_suggestions": [],
            "priority_level": "low",
            "estimated_improvement": 0.0
        }
        
        # 各メトリクスをチェック
        for metric, config in self.optimization_rules.items():
            value = analytics.get(metric, 0)
            threshold = config["threshold"]
            
            if (metric == "response_time" and value > threshold) or \
               (metric in ["success_rate", "user_satisfaction"] and value < threshold):
                
                suggestions["optimization_suggestions"].extend([
                    {
                        "metric": metric,
                        "current_value": value,
                        "target_value": threshold,
                        "actions": config["actions"],
                        "priority": self._calculate_priority(metric, value, threshold)
                    }
                ])
        
        # 全体的な優先度を決定
        if suggestions["optimization_suggestions"]:
            priorities = [s["priority"] for s in suggestions["optimization_suggestions"]]
            max_priority = max(priorities)
            suggestions["priority_level"] = "high" if max_priority > 0.7 else "medium"
            suggestions["estimated_improvement"] = max_priority * 100
        
        return suggestions
    
    def _calculate_priority(self, metric: str, current: float, threshold: float) -> float:
        """優先度を計算"""
        if metric == "response_time":
            return min(1.0, (current - threshold) / threshold)
        else:
            return min(1.0, (threshold - current) / threshold)
    
    def apply_automatic_optimizations(
        self, 
        template: PromptTemplate,
        suggestions: Dict[str, Any]
    ) -> PromptTemplate:
        """自動最適化を適用"""
        optimized_template = template
        
        for suggestion in suggestions.get("optimization_suggestions", []):
            for action in suggestion["actions"]:
                optimized_template = self._apply_optimization_action(
                    optimized_template, action, suggestion["metric"]
                )
        
        return optimized_template
    
    def _apply_optimization_action(
        self, 
        template: PromptTemplate, 
        action: str, 
        metric: str
    ) -> PromptTemplate:
        """最適化アクションを適用"""
        # この部分は実際のプロンプト内容に基づいてより詳細に実装
        if action == "shorten_prompt":
            # プロンプトを短縮
            lines = template.template.split('\n')
            if len(lines) > 3:
                template.template = '\n'.join(lines[:len(lines)//2])
        
        elif action == "add_examples":
            # 例を追加
            if "例:" not in template.template:
                template.template += "\n\n例:\n- 具体例1\n- 具体例2"
        
        elif action == "clarify_instructions":
            # 指示を明確化
            if template.template and not template.template.endswith("。"):
                template.template += "\n\n明確な指示に従って回答してください。"
        
        return template


class PromptTemplateManager:
    """プロンプトテンプレート管理システム"""
    
    def __init__(self, templates_dir: str = "ai/prompts/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, PromptTemplate] = {}
        self.variants: Dict[str, List[TemplateVariant]] = {}
        self.ab_test_config: Dict[str, Any] = {}
        self.active_tests: Dict[str, TestResult] = {}
        
        # 新機能
        self.context_manager = ContextWindowManager()
        self.analytics = PromptAnalytics()
        self.auto_optimizer = AutoOptimizer(self.analytics)
        
        # メトリクス記録用
        self.metrics_file = self.templates_dir / "metrics.json"
        self.analytics_file = self.templates_dir / "analytics.json"
        
        self.load_templates()
        self.load_ab_test_config()
        self.load_analytics_data()
    
    def load_templates(self):
        """テンプレートファイルを読み込み"""
        try:
            templates_file = self.templates_dir / "templates.json"
            if templates_file.exists():
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for template_data in data.get("templates", []):
                    template = self._dict_to_template(template_data)
                    self.templates[template.metadata.template_id] = template
                    
            # バリアントファイルを読み込み
            variants_file = self.templates_dir / "variants.json"
            if variants_file.exists():
                with open(variants_file, 'r', encoding='utf-8') as f:
                    variants_data = json.load(f)
                    
                for template_id, variants_list in variants_data.items():
                    self.variants[template_id] = [
                        TemplateVariant(**variant) for variant in variants_list
                    ]
                    
            logger.info(f"読み込んだテンプレート数: {len(self.templates)}")
            logger.info(f"読み込んだバリアント数: {sum(len(v) for v in self.variants.values())}")
            
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {e}")
    
    def load_ab_test_config(self):
        """A/Bテスト設定を読み込み"""
        try:
            ab_config_file = self.templates_dir / "ab_test_config.json"
            if ab_config_file.exists():
                with open(ab_config_file, 'r', encoding='utf-8') as f:
                    self.ab_test_config = json.load(f)
            else:
                # デフォルト設定
                self.ab_test_config = {
                    "enabled": True,
                    "sample_size_threshold": 100,
                    "confidence_level": 0.95,
                    "success_metrics": ["response_quality", "task_completion", "user_satisfaction"],
                    "auto_promote_threshold": 0.05  # 5%改善で自動昇格
                }
                self.save_ab_test_config()
                
        except Exception as e:
            logger.error(f"A/Bテスト設定読み込みエラー: {e}")
    
    def load_analytics_data(self):
        """分析データを読み込み"""
        try:
            if self.analytics_file.exists():
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.analytics.session_data = data.get("session_data", {})
                    self.analytics.hourly_stats = data.get("hourly_stats", {})
        except Exception as e:
            logger.error(f"分析データ読み込みエラー: {e}")
    
    def save_analytics_data(self):
        """分析データを保存"""
        try:
            data = {
                "session_data": self.analytics.session_data,
                "hourly_stats": self.analytics.hourly_stats,
                "last_updated": time.time()
            }
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"分析データ保存エラー: {e}")
    
    def enhanced_render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        context: Optional[str] = None,
        mode: Optional[PromptMode] = None,
        track_metrics: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """拡張テンプレートレンダリング（メトリクス追跡付き）"""
        start_time = time.time()
        
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"テンプレートが見つかりません: {template_id}")
        
        # A/Bテスト用バリアント選択
        variant_id = None
        if self.ab_test_config.get("enabled", False):
            selected_variant = self._select_ab_variant(template_id)
            if selected_variant:
                variant_id = selected_variant.variant_id
                # バリアントのテンプレートを使用
                template.template = selected_variant.template
        
        try:
            # 変数置換
            rendered = template.template.format(**variables)
            
            # コンテキストがある場合は追加
            if context:
                rendered = self._integrate_context(rendered, context, template, mode)
            
            # モード別最適化
            if mode:
                rendered = self._apply_mode_optimization(rendered, mode, template)
            
            # コンテキストウィンドウチェック
            rendered = self._apply_context_window_limits(rendered, template)
            
            # メトリクス記録
            end_time = time.time()
            response_time = end_time - start_time
            
            metrics = {
                "response_time": response_time,
                "template_length": len(rendered),
                "variable_count": len(variables),
                "success_rate": 1.0  # 成功した場合
            }
            
            if track_metrics:
                # 使用回数を更新
                template.metadata.usage_count += 1
                
                # 分析データに記録
                self.analytics.record_usage(template_id, variant_id, metrics)
                
                # パフォーマンスメトリクスを更新
                self.record_performance(template_id, variant_id, metrics, response_time)
            
            return rendered, metrics
            
        except Exception as e:
            # エラー時のメトリクス記録
            error_metrics = {
                "response_time": time.time() - start_time,
                "success_rate": 0.0,
                "error_type": type(e).__name__
            }
            
            if track_metrics:
                self.analytics.record_usage(template_id, variant_id, error_metrics)
            
            logger.error(f"テンプレートレンダリングエラー: {e}")
            raise
    
    def start_ab_test(
        self,
        template_id: str,
        variant_template: str,
        test_name: str = "",
        target_metric: str = "success_rate",
        test_duration_hours: int = 168  # 1週間
    ) -> str:
        """A/Bテストを開始"""
        if template_id not in self.templates:
            raise ValueError(f"ベーステンプレートが存在しません: {template_id}")
        
        # バリアント作成
        variant_id = self.create_ab_variant(template_id, variant_template, weight=0.5)
        
        # テスト結果オブジェクト作成
        test_id = f"test_{template_id}_{int(time.time())}"
        test_result = TestResult(
            test_id=test_id,
            template_id=template_id,
            variant_id=variant_id,
            start_time=time.time(),
            end_time=None,
            sample_size=0,
            metrics={target_metric: 0.0},
            statistical_significance=False,
            confidence_level=0.0,
            improvement_percentage=0.0
        )
        
        self.active_tests[test_id] = test_result
        
        # テスト設定を保存
        self.save_templates()
        
        logger.info(f"A/Bテスト開始: {test_id} (期間: {test_duration_hours}時間)")
        return test_id
    
    def end_ab_test(self, test_id: str) -> Dict[str, Any]:
        """A/Bテストを終了して結果を分析"""
        if test_id not in self.active_tests:
            raise ValueError(f"アクティブなテストが見つかりません: {test_id}")
        
        test_result = self.active_tests[test_id]
        test_result.end_time = time.time()
        
        # 統計的有意性を計算
        base_analytics = self.analytics.get_template_analytics(test_result.template_id)
        variant_analytics = self.analytics.get_template_analytics(test_result.variant_id)
        
        if not base_analytics.get("error") and not variant_analytics.get("error"):
            # 改善率を計算
            base_metric = base_analytics.get("success_rate", 0)
            variant_metric = variant_analytics.get("success_rate", 0)
            
            if base_metric > 0:
                improvement = ((variant_metric - base_metric) / base_metric) * 100
                test_result.improvement_percentage = improvement
                
                # 統計的有意性の簡易計算
                base_sample = base_analytics.get("total_usage", 0)
                variant_sample = variant_analytics.get("total_usage", 0)
                
                if base_sample >= 30 and variant_sample >= 30:
                    # 十分なサンプルサイズがある場合
                    test_result.statistical_significance = abs(improvement) > 5.0
                    test_result.confidence_level = 0.95 if test_result.statistical_significance else 0.5
        
        # テスト結果を記録
        results = {
            "test_id": test_id,
            "template_id": test_result.template_id,
            "variant_id": test_result.variant_id,
            "duration_hours": (test_result.end_time - test_result.start_time) / 3600,
            "improvement_percentage": test_result.improvement_percentage,
            "statistical_significance": test_result.statistical_significance,
            "confidence_level": test_result.confidence_level,
            "recommendation": self._generate_test_recommendation(test_result)
        }
        
        # アクティブテストから除去
        del self.active_tests[test_id]
        
        logger.info(f"A/Bテスト終了: {test_id}, 改善率: {test_result.improvement_percentage:.2f}%")
        return results
    
    def _generate_test_recommendation(self, test_result: TestResult) -> str:
        """テスト結果に基づく推奨アクションを生成"""
        if test_result.statistical_significance:
            if test_result.improvement_percentage > 5.0:
                return "バリアントを本採用することを推奨します"
            elif test_result.improvement_percentage < -5.0:
                return "元のテンプレートを継続使用することを推奨します"
        
        return "追加データが必要です。テスト期間を延長するか、サンプルサイズを増やしてください"
    
    def get_optimization_dashboard(self) -> Dict[str, Any]:
        """最適化ダッシュボード用データを取得"""
        dashboard_data = {
            "timestamp": time.time(),
            "total_templates": len(self.templates),
            "active_tests": len(self.active_tests),
            "template_performance": {},
            "optimization_opportunities": [],
            "recent_trends": {}
        }
        
        # 各テンプレートの性能分析
        for template_id, template in self.templates.items():
            analytics = self.analytics.get_template_analytics(template_id)
            if not analytics.get("error"):
                dashboard_data["template_performance"][template_id] = {
                    "usage_count": analytics.get("total_usage", 0),
                    "success_rate": analytics.get("success_rate", 0),
                    "avg_response_time": analytics.get("avg_response_time", 0),
                    "user_satisfaction": analytics.get("user_satisfaction", 0),
                    "trend": analytics.get("response_time_trend", "unknown")
                }
                
                # 最適化機会を特定
                optimization_suggestions = self.auto_optimizer.analyze_and_suggest_optimizations(template_id)
                if optimization_suggestions.get("optimization_suggestions"):
                    dashboard_data["optimization_opportunities"].append({
                        "template_id": template_id,
                        "template_name": template.metadata.name,
                        "priority": optimization_suggestions["priority_level"],
                        "potential_improvement": optimization_suggestions["estimated_improvement"],
                        "suggestions": optimization_suggestions["optimization_suggestions"]
                    })
        
        # 最適化機会を優先度順にソート
        dashboard_data["optimization_opportunities"].sort(
            key=lambda x: x["potential_improvement"], reverse=True
        )
        
        return dashboard_data
    
    def auto_optimize_template(self, template_id: str) -> Dict[str, Any]:
        """テンプレートの自動最適化を実行"""
        if template_id not in self.templates:
            raise ValueError(f"テンプレートが見つかりません: {template_id}")
        
        template = self.templates[template_id]
        
        # 最適化提案を取得
        suggestions = self.auto_optimizer.analyze_and_suggest_optimizations(template_id)
        
        if not suggestions.get("optimization_suggestions"):
            return {"status": "no_optimization_needed", "template_id": template_id}
        
        # 最適化を適用
        optimized_template = self.auto_optimizer.apply_automatic_optimizations(template, suggestions)
        
        # 新しいバージョンとして保存
        new_version = self._increment_version(template.metadata.version)
        optimized_template.metadata.version = new_version
        optimized_template.metadata.updated_at = time.time()
        
        # A/Bテストとして設定
        test_id = self.start_ab_test(
            template_id=template_id,
            variant_template=optimized_template.template,
            test_name=f"auto_optimization_v{new_version}",
            target_metric="success_rate"
        )
        
        return {
            "status": "optimization_applied",
            "template_id": template_id,
            "new_version": new_version,
            "ab_test_id": test_id,
            "applied_optimizations": suggestions["optimization_suggestions"],
            "estimated_improvement": suggestions["estimated_improvement"]
        }
    
    def _increment_version(self, current_version: str) -> str:
        """バージョン番号をインクリメント"""
        try:
            parts = current_version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            return '.'.join(parts)
        except:
            return f"{current_version}.1"
    
    def export_analytics_report(self, days: int = 30) -> Dict[str, Any]:
        """分析レポートをエクスポート"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        report = {
            "report_period_days": days,
            "generated_at": time.time(),
            "summary": {
                "total_templates": len(self.templates),
                "total_usage": 0,
                "avg_success_rate": 0,
                "avg_response_time": 0
            },
            "template_details": {},
            "recommendations": []
        }
        
        success_rates = []
        response_times = []
        total_usage = 0
        
        for template_id, template in self.templates.items():
            analytics = self.analytics.get_template_analytics(template_id, time_range_hours=days*24)
            
            if not analytics.get("error"):
                usage = analytics.get("total_usage", 0)
                success_rate = analytics.get("success_rate", 0)
                response_time = analytics.get("avg_response_time", 0)
                
                total_usage += usage
                if success_rate > 0:
                    success_rates.append(success_rate)
                if response_time > 0:
                    response_times.append(response_time)
                
                report["template_details"][template_id] = {
                    "name": template.metadata.name,
                    "usage": usage,
                    "success_rate": success_rate,
                    "response_time": response_time,
                    "user_satisfaction": analytics.get("user_satisfaction", 0),
                    "trend": analytics.get("response_time_trend", "unknown")
                }
        
        # サマリー計算
        report["summary"]["total_usage"] = total_usage
        report["summary"]["avg_success_rate"] = statistics.mean(success_rates) if success_rates else 0
        report["summary"]["avg_response_time"] = statistics.mean(response_times) if response_times else 0
        
        # 推奨事項生成
        for template_id in self.templates:
            optimization = self.auto_optimizer.analyze_and_suggest_optimizations(template_id)
            if optimization.get("optimization_suggestions"):
                report["recommendations"].append({
                    "template_id": template_id,
                    "priority": optimization["priority_level"],
                    "suggestions": optimization["optimization_suggestions"]
                })
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """システム統計情報を取得"""
        stats = {
            "templates": {
                "total": len(self.templates),
                "by_type": {},
                "by_mode": {},
                "total_usage": sum(t.metadata.usage_count for t in self.templates.values())
            },
            "ab_tests": {
                "active": len(self.active_tests),
                "total_variants": sum(len(variants) for variants in self.variants.values())
            },
            "performance": {
                "avg_success_rate": 0,
                "avg_response_time": 0,
                "top_performing_templates": []
            },
            "system_health": {
                "analytics_status": "active" if self.analytics.session_data else "inactive",
                "optimization_status": "enabled",
                "last_optimization": time.time()
            }
        }
        
        # テンプレートタイプ・モード別集計
        for template in self.templates.values():
            template_type = template.metadata.template_type.value
            mode = template.metadata.mode.value
            
            stats["templates"]["by_type"][template_type] = \
                stats["templates"]["by_type"].get(template_type, 0) + 1
            stats["templates"]["by_mode"][mode] = \
                stats["templates"]["by_mode"].get(mode, 0) + 1
        
        # パフォーマンス統計
        success_rates = []
        response_times = []
        template_performance = []
        
        for template_id, template in self.templates.items():
            success_rate = template.metadata.success_rate
            response_time = template.metadata.avg_response_time
            
            if success_rate > 0:
                success_rates.append(success_rate)
            if response_time > 0:
                response_times.append(response_time)
            
            template_performance.append({
                "id": template_id,
                "name": template.metadata.name,
                "success_rate": success_rate,
                "usage_count": template.metadata.usage_count
            })
        
        if success_rates:
            stats["performance"]["avg_success_rate"] = statistics.mean(success_rates)
        if response_times:
            stats["performance"]["avg_response_time"] = statistics.mean(response_times)
        
        # トップパフォーマンステンプレート
        template_performance.sort(key=lambda x: x["success_rate"] * x["usage_count"], reverse=True)
        stats["performance"]["top_performing_templates"] = template_performance[:5]
        
        return stats
