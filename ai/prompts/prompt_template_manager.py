#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロンプトテンプレート管理システム
Task 3-4: Context Window Management - プロンプトエンジニアリング

機能:
- テンプレート管理とバージョニング
- 進行モード別テンプレート最適化
- A/Bテストフレームワーク
- コンテキストウィンドウ管理
"""

import json
import os
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

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


class ContextWindowManager:
    """コンテキストウィンドウ管理"""
    
    def __init__(self, max_tokens: int = 8192):
        self.max_tokens = max_tokens
        self.reserved_tokens = 1000  # レスポンス用予約トークン
        self.available_tokens = max_tokens - self.reserved_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """簡易的なトークン数推定"""
        # 大まかな推定: 1トークン ≈ 4文字（日本語と英語混在）
        return len(text) // 3
    
    def fit_context(self, components: List[Tuple[str, str, int]]) -> List[Tuple[str, str]]:
        """
        コンテキストウィンドウに収まるように文章を調整
        components: [(component_name, text, priority)]
        priority: 1=最高優先度、数字が大きいほど低優先度
        """
        # 優先度順にソート
        components.sort(key=lambda x: x[2])
        
        fitted_components = []
        used_tokens = 0
        
        for component_name, text, priority in components:
            text_tokens = self.estimate_tokens(text)
            
            if used_tokens + text_tokens <= self.available_tokens:
                fitted_components.append((component_name, text))
                used_tokens += text_tokens
            else:
                # 残りのトークン数で可能な範囲でテキストを切り詰め
                remaining_tokens = self.available_tokens - used_tokens
                if remaining_tokens > 100:  # 最低100トークンは確保
                    # 文字数ベースで切り詰め
                    max_chars = remaining_tokens * 3
                    truncated_text = text[:max_chars] + "..."
                    fitted_components.append((component_name, truncated_text))
                break
        
        return fitted_components


class PromptTemplateManager:
    """プロンプトテンプレート管理システム"""
    
    def __init__(self, templates_dir: str = "ai/prompts/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, PromptTemplate] = {}
        self.variants: Dict[str, List[TemplateVariant]] = {}
        self.ab_test_config: Dict[str, Any] = {}
        self.context_manager = ContextWindowManager()
        
        # メトリクス記録用
        self.metrics_file = self.templates_dir / "metrics.json"
        self.load_templates()
        self.load_ab_test_config()
    
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
    
    def save_templates(self):
        """テンプレートをファイルに保存"""
        try:
            templates_data = {
                "templates": [self._template_to_dict(template) for template in self.templates.values()],
                "last_updated": time.time()
            }
            
            templates_file = self.templates_dir / "templates.json"
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, ensure_ascii=False, indent=2)
            
            # バリアントも保存
            variants_data = {}
            for template_id, variants_list in self.variants.items():
                variants_data[template_id] = [asdict(variant) for variant in variants_list]
            
            variants_file = self.templates_dir / "variants.json"
            with open(variants_file, 'w', encoding='utf-8') as f:
                json.dump(variants_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"テンプレート保存エラー: {e}")
    
    def save_ab_test_config(self):
        """A/Bテスト設定を保存"""
        try:
            ab_config_file = self.templates_dir / "ab_test_config.json"
            with open(ab_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.ab_test_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"A/Bテスト設定保存エラー: {e}")
    
    def create_template(
        self,
        name: str,
        template: str,
        template_type: TemplateType,
        mode: PromptMode,
        description: str = "",
        variables: Optional[List[str]] = None,
        author: str = "system",
        tags: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        context_window_config: Optional[Dict[str, Any]] = None,
        optimization_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """新しいテンプレートを作成"""
        
        template_id = self._generate_template_id(name, template_type, mode)
        current_time = time.time()
        
        # 変数を自動抽出
        if variables is None:
            variables = self._extract_variables(template)
        
        # デフォルト設定
        if constraints is None:
            constraints = {"max_length": 2000, "required_variables": variables}
        
        if context_window_config is None:
            context_window_config = {
                "max_context_tokens": 6000,
                "preserve_priority": ["system", "instruction", "context"],
                "truncation_strategy": "end"
            }
        
        if optimization_params is None:
            optimization_params = self._get_default_optimization_params(mode)
        
        metadata = TemplateMetadata(
            template_id=template_id,
            name=name,
            version="1.0.0",
            template_type=template_type,
            mode=mode,
            description=description,
            created_at=current_time,
            updated_at=current_time,
            author=author,
            tags=tags or [],
            performance_metrics={},
            usage_count=0,
            success_rate=0.0,
            avg_response_time=0.0
        )
        
        prompt_template = PromptTemplate(
            metadata=metadata,
            template=template,
            variables=variables,
            constraints=constraints,
            context_window_config=context_window_config,
            optimization_params=optimization_params
        )
        
        self.templates[template_id] = prompt_template
        self.save_templates()
        
        logger.info(f"新しいテンプレート作成: {template_id}")
        return template_id
    
    def get_template(
        self, 
        template_id: str, 
        use_ab_test: bool = True
    ) -> Optional[PromptTemplate]:
        """テンプレートを取得（A/Bテスト考慮）"""
        
        if template_id not in self.templates:
            logger.warning(f"テンプレートが見つかりません: {template_id}")
            return None
        
        base_template = self.templates[template_id]
        
        # A/Bテストが有効で、バリアントが存在する場合
        if use_ab_test and self.ab_test_config.get("enabled", False):
            if template_id in self.variants:
                variant = self._select_ab_variant(template_id)
                if variant:
                    # バリアントテンプレートでベーステンプレートを更新
                    modified_template = PromptTemplate(
                        metadata=base_template.metadata,
                        template=variant.template,
                        variables=base_template.variables,
                        constraints=base_template.constraints,
                        context_window_config=base_template.context_window_config,
                        optimization_params=base_template.optimization_params
                    )
                    return modified_template
        
        return base_template
    
    def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        context: Optional[str] = None,
        mode: Optional[PromptMode] = None
    ) -> str:
        """テンプレートをレンダリング"""
        
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"テンプレートが見つかりません: {template_id}")
        
        # 使用回数を更新
        template.metadata.usage_count += 1
        
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
            
            return rendered
            
        except KeyError as e:
            logger.error(f"テンプレート変数エラー: {e}")
            raise ValueError(f"必要な変数が不足しています: {e}")
        except Exception as e:
            logger.error(f"テンプレートレンダリングエラー: {e}")
            raise
    
    def create_ab_variant(
        self,
        template_id: str,
        variant_template: str,
        weight: float = 0.5,
        variant_name: str = ""
    ) -> str:
        """A/Bテスト用バリアントを作成"""
        
        if template_id not in self.templates:
            raise ValueError(f"ベーステンプレートが存在しません: {template_id}")
        
        variant_id = f"{template_id}_variant_{len(self.variants.get(template_id, []))}"
        
        variant = TemplateVariant(
            variant_id=variant_id,
            template_id=template_id,
            template=variant_template,
            weight=weight,
            active=True,
            test_metrics={}
        )
        
        if template_id not in self.variants:
            self.variants[template_id] = []
        
        self.variants[template_id].append(variant)
        self.save_templates()
        
        logger.info(f"A/Bテストバリアント作成: {variant_id}")
        return variant_id
    
    def record_performance(
        self,
        template_id: str,
        variant_id: Optional[str],
        metrics: Dict[str, float],
        response_time: float
    ):
        """テンプレートの性能メトリクスを記録"""
        
        if template_id in self.templates:
            template = self.templates[template_id]
            
            # メトリクスを更新
            for metric_name, value in metrics.items():
                if metric_name in template.metadata.performance_metrics:
                    # 移動平均で更新
                    current = template.metadata.performance_metrics[metric_name]
                    template.metadata.performance_metrics[metric_name] = (current * 0.9) + (value * 0.1)
                else:
                    template.metadata.performance_metrics[metric_name] = value
            
            # レスポンス時間を更新
            current_avg = template.metadata.avg_response_time
            count = template.metadata.usage_count
            template.metadata.avg_response_time = ((current_avg * (count - 1)) + response_time) / count
        
        # バリアントのメトリクスも更新
        if variant_id and template_id in self.variants:
            for variant in self.variants[template_id]:
                if variant.variant_id == variant_id:
                    for metric_name, value in metrics.items():
                        if metric_name in variant.test_metrics:
                            current = variant.test_metrics[metric_name]
                            variant.test_metrics[metric_name] = (current * 0.9) + (value * 0.1)
                        else:
                            variant.test_metrics[metric_name] = value
                    break
        
        self.save_templates()
    
    def get_best_template(
        self,
        template_type: TemplateType,
        mode: PromptMode,
        metric: str = "success_rate"
    ) -> Optional[PromptTemplate]:
        """指定条件で最高性能のテンプレートを取得"""
        
        candidates = [
            template for template in self.templates.values()
            if template.metadata.template_type == template_type and template.metadata.mode == mode
        ]
        
        if not candidates:
            return None
        
        # メトリクス順にソート
        candidates.sort(
            key=lambda t: t.metadata.performance_metrics.get(metric, 0.0),
            reverse=True
        )
        
        return candidates[0]
    
    def _generate_template_id(self, name: str, template_type: TemplateType, mode: PromptMode) -> str:
        """テンプレートIDを生成"""
        base = f"{mode.value}_{template_type.value}_{name}"
        return hashlib.md5(base.encode()).hexdigest()[:12]
    
    def _extract_variables(self, template: str) -> List[str]:
        """テンプレートから変数を抽出"""
        import re
        pattern = r'\{([^}]+)\}'
        variables = re.findall(pattern, template)
        return list(set(variables))
    
    def _get_default_optimization_params(self, mode: PromptMode) -> Dict[str, Any]:
        """モード別デフォルト最適化パラメータ"""
        params = {
            PromptMode.INTERACTIVE: {
                "response_style": "conversational",
                "detail_level": "moderate",
                "examples_count": 2,
                "confirmation_requests": True
            },
            PromptMode.AUTONOMOUS: {
                "response_style": "systematic",
                "detail_level": "comprehensive",
                "examples_count": 3,
                "step_by_step": True
            },
            PromptMode.HYBRID: {
                "response_style": "balanced",
                "detail_level": "adaptive",
                "examples_count": 2,
                "context_sensitive": True
            }
        }
        return params.get(mode, {})
    
    def _select_ab_variant(self, template_id: str) -> Optional[TemplateVariant]:
        """A/Bテスト用バリアントを選択"""
        if template_id not in self.variants:
            return None
        
        active_variants = [v for v in self.variants[template_id] if v.active]
        if not active_variants:
            return None
        
        # 重み付き選択
        import random
        total_weight = sum(v.weight for v in active_variants)
        rand = random.uniform(0, total_weight)
        
        current_weight = 0
        for variant in active_variants:
            current_weight += variant.weight
            if rand <= current_weight:
                return variant
        
        return active_variants[0]  # フォールバック
    
    def _integrate_context(
        self, 
        rendered: str, 
        context: str, 
        template: PromptTemplate,
        mode: Optional[PromptMode]
    ) -> str:
        """コンテキストを統合"""
        context_config = template.context_window_config
        
        # コンテキストの優先度とトークン制限を考慮
        components = [
            ("main_prompt", rendered, 1),
            ("context", context, 2)
        ]
        
        fitted_components = self.context_manager.fit_context(components)
        
        # 統合されたプロンプトを生成
        result_parts = []
        for component_name, text in fitted_components:
            if component_name == "context":
                result_parts.append(f"以下の情報を参考にしてください：\n{text}\n")
            else:
                result_parts.append(text)
        
        return "\n".join(result_parts)
    
    def _apply_mode_optimization(
        self, 
        rendered: str, 
        mode: PromptMode, 
        template: PromptTemplate
    ) -> str:
        """モード別最適化を適用"""
        params = template.optimization_params
        
        if mode == PromptMode.INTERACTIVE:
            if params.get("confirmation_requests", False):
                rendered += "\n\n確認や質問があれば遠慮なくお聞かせください。"
        
        elif mode == PromptMode.AUTONOMOUS:
            if params.get("step_by_step", False):
                rendered = "以下の手順で段階的に作業を進めてください：\n\n" + rendered
        
        elif mode == PromptMode.HYBRID:
            if params.get("context_sensitive", False):
                rendered = "状況に応じて適切な方法を選択してください：\n\n" + rendered
        
        return rendered
    
    def _apply_context_window_limits(self, rendered: str, template: PromptTemplate) -> str:
        """コンテキストウィンドウ制限を適用"""
        max_tokens = template.context_window_config.get("max_context_tokens", 6000)
        estimated_tokens = self.context_manager.estimate_tokens(rendered)
        
        if estimated_tokens > max_tokens:
            # 切り詰め戦略に基づいて調整
            strategy = template.context_window_config.get("truncation_strategy", "end")
            max_chars = max_tokens * 3
            
            if strategy == "end":
                rendered = rendered[:max_chars] + "..."
            elif strategy == "middle":
                half = max_chars // 2
                rendered = rendered[:half] + "\n...(中略)...\n" + rendered[-half:]
            
        return rendered
    
    def _template_to_dict(self, template: PromptTemplate) -> Dict[str, Any]:
        """テンプレートを辞書に変換"""
        return {
            "metadata": asdict(template.metadata),
            "template": template.template,
            "variables": template.variables,
            "constraints": template.constraints,
            "context_window_config": template.context_window_config,
            "optimization_params": template.optimization_params
        }
    
    def _dict_to_template(self, data: Dict[str, Any]) -> PromptTemplate:
        """辞書からテンプレートを復元"""
        metadata_dict = data["metadata"]
        metadata_dict["template_type"] = TemplateType(metadata_dict["template_type"])
        metadata_dict["mode"] = PromptMode(metadata_dict["mode"])
        
        metadata = TemplateMetadata(**metadata_dict)
        
        return PromptTemplate(
            metadata=metadata,
            template=data["template"],
            variables=data["variables"],
            constraints=data["constraints"],
            context_window_config=data["context_window_config"],
            optimization_params=data["optimization_params"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_templates = len(self.templates)
        total_variants = sum(len(variants) for variants in self.variants.values())
        
        mode_counts = {}
        type_counts = {}
        
        for template in self.templates.values():
            mode = template.metadata.mode.value
            template_type = template.metadata.template_type.value
            
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            type_counts[template_type] = type_counts.get(template_type, 0) + 1
        
        return {
            "total_templates": total_templates,
            "total_variants": total_variants,
            "mode_distribution": mode_counts,
            "type_distribution": type_counts,
            "ab_test_enabled": self.ab_test_config.get("enabled", False),
            "context_window_max_tokens": self.context_manager.max_tokens
        }
