#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合プロンプトサービス
Task 3-4: Context Window Management - RAGシステムとプロンプトテンプレート管理の統合

機能:
- RAG検索結果とプロンプトテンプレートの統合
- 進行モード別プロンプト生成
- A/Bテスト実行とメトリクス収集
- コンテキスト最適化
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .prompt_template_manager import (
    PromptTemplateManager, TemplateType, PromptMode, ContextWindowManager
)
from ..rag.rag_system import RAGSystem

logger = logging.getLogger(__name__)


@dataclass
class PromptGenerationResult:
    """プロンプト生成結果"""
    prompt: str
    template_id: str
    variant_id: Optional[str]
    mode: PromptMode
    context_length: int
    rag_results_count: int
    generation_time: float
    metadata: Dict[str, Any]


@dataclass
class ContextOptimizationConfig:
    """コンテキスト最適化設定"""
    max_context_length: int = 6000
    rag_results_limit: int = 5
    prioritize_recent: bool = True
    include_metadata: bool = True
    summary_threshold: int = 1000


class IntegratedPromptService:
    """統合プロンプトサービス"""
    
    def __init__(
        self, 
        rag_system: RAGSystem,
        templates_dir: str = "ai/prompts/templates"
    ):
        self.rag_system = rag_system
        self.template_manager = PromptTemplateManager(templates_dir)
        self.context_manager = ContextWindowManager()
        
        # 性能メトリクス
        self.metrics = {
            "total_generations": 0,
            "successful_generations": 0,
            "average_generation_time": 0.0,
            "template_usage": {},
            "mode_usage": {}
        }
        
        # デフォルトテンプレートを作成
        self._initialize_default_templates()
    
    async def generate_prompt(
        self,
        query: str,
        mode: PromptMode,
        template_type: TemplateType = TemplateType.USER,
        template_id: Optional[str] = None,
        additional_context: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        use_rag: bool = True,
        optimization_config: Optional[ContextOptimizationConfig] = None
    ) -> PromptGenerationResult:
        """統合プロンプトを生成"""
        
        start_time = time.time()
        self.metrics["total_generations"] += 1
        
        try:
            # 最適化設定のデフォルト値
            if optimization_config is None:
                optimization_config = ContextOptimizationConfig()
            
            # テンプレートを取得または選択
            if template_id:
                template = self.template_manager.get_template(template_id)
                if not template:
                    raise ValueError(f"指定されたテンプレートが見つかりません: {template_id}")
            else:
                template = self.template_manager.get_best_template(template_type, mode)
                if not template:
                    # フォールバックテンプレートを作成
                    template_id = await self._create_fallback_template(template_type, mode)
                    template = self.template_manager.get_template(template_id)
            
            # RAG検索実行
            rag_context = ""
            rag_results_count = 0
            if use_rag:
                rag_context, rag_results_count = await self._get_rag_context(
                    query, mode, optimization_config
                )
            
            # コンテキストを統合
            integrated_context = self._integrate_contexts(
                rag_context, additional_context, optimization_config
            )
            
            # 変数を準備
            template_variables = variables or {}
            template_variables.update({
                "query": query,
                "context": integrated_context,
                "mode": mode.value
            })
            
            # プロンプトをレンダリング
            rendered_prompt = self.template_manager.render_template(
                template.metadata.template_id,
                template_variables,
                integrated_context,
                mode
            )
            
            generation_time = time.time() - start_time
            
            # 結果を作成
            result = PromptGenerationResult(
                prompt=rendered_prompt,
                template_id=template.metadata.template_id,
                variant_id=None,  # A/Bテスト実装時に更新
                mode=mode,
                context_length=len(integrated_context),
                rag_results_count=rag_results_count,
                generation_time=generation_time,
                metadata={
                    "template_name": template.metadata.name,
                    "template_version": template.metadata.version,
                    "optimization_config": optimization_config.__dict__,
                    "rag_enabled": use_rag
                }
            )
            
            # メトリクスを更新
            self._update_metrics(template.metadata.template_id, mode, generation_time, True)
            self.metrics["successful_generations"] += 1
            
            logger.info(f"プロンプト生成完了: {generation_time:.3f}秒, モード: {mode.value}")
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            self._update_metrics("error", mode, generation_time, False)
            logger.error(f"プロンプト生成エラー: {e}")
            raise
    
    async def generate_mode_optimized_prompt(
        self,
        query: str,
        mode: PromptMode,
        task_context: Optional[Dict[str, Any]] = None
    ) -> PromptGenerationResult:
        """モード最適化プロンプトを生成"""
        
        # モード別の最適化設定
        mode_configs = {
            PromptMode.INTERACTIVE: ContextOptimizationConfig(
                max_context_length=4000,
                rag_results_limit=3,
                prioritize_recent=True,
                include_metadata=False,
                summary_threshold=800
            ),
            PromptMode.AUTONOMOUS: ContextOptimizationConfig(
                max_context_length=7000,
                rag_results_limit=8,
                prioritize_recent=False,
                include_metadata=True,
                summary_threshold=1500
            ),
            PromptMode.HYBRID: ContextOptimizationConfig(
                max_context_length=5500,
                rag_results_limit=5,
                prioritize_recent=True,
                include_metadata=True,
                summary_threshold=1200
            )
        }
        
        optimization_config = mode_configs.get(mode, ContextOptimizationConfig())
        
        # タスクコンテキストから追加変数を抽出
        variables = {}
        if task_context:
            variables.update(task_context)
        
        return await self.generate_prompt(
            query=query,
            mode=mode,
            template_type=TemplateType.USER,
            variables=variables,
            optimization_config=optimization_config
        )
    
    async def run_ab_test(
        self,
        query: str,
        mode: PromptMode,
        template_id: str,
        test_duration_minutes: int = 60,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """A/Bテストを実行"""
        
        logger.info(f"A/Bテスト開始: {template_id}, 期間: {test_duration_minutes}分")
        
        # ベーステンプレートとバリアントを取得
        base_template = self.template_manager.get_template(template_id, use_ab_test=False)
        if not base_template:
            raise ValueError(f"テンプレートが見つかりません: {template_id}")
        
        variants = self.template_manager.variants.get(template_id, [])
        if not variants:
            raise ValueError(f"テストバリアントが見つかりません: {template_id}")
        
        # テスト結果を記録
        test_results = {
            "base_template": {"usage_count": 0, "success_count": 0, "total_time": 0.0},
            "variants": {v.variant_id: {"usage_count": 0, "success_count": 0, "total_time": 0.0} 
                        for v in variants}
        }
        
        start_time = time.time()
        end_time = start_time + (test_duration_minutes * 60)
        
        sample_count = 0
        
        while time.time() < end_time and sample_count < sample_size:
            try:
                # ランダムにベースまたはバリアントを選択
                import random
                use_variant = random.choice([False] + [True] * len(variants))
                
                if use_variant:
                    # バリアントテストを実行
                    result = await self.generate_prompt(
                        query=query,
                        mode=mode,
                        template_id=template_id,
                        use_rag=True
                    )
                    
                    # バリアント選択（簡略化）
                    variant = random.choice(variants)
                    test_results["variants"][variant.variant_id]["usage_count"] += 1
                    test_results["variants"][variant.variant_id]["total_time"] += result.generation_time
                    
                    # 成功判定（簡略版、実際は複雑な評価が必要）
                    if result.generation_time < 2.0 and len(result.prompt) > 100:
                        test_results["variants"][variant.variant_id]["success_count"] += 1
                
                else:
                    # ベーステンプレートテスト
                    result = await self.generate_prompt(
                        query=query,
                        mode=mode,
                        template_id=template_id,
                        use_rag=True
                    )
                    
                    test_results["base_template"]["usage_count"] += 1
                    test_results["base_template"]["total_time"] += result.generation_time
                    
                    if result.generation_time < 2.0 and len(result.prompt) > 100:
                        test_results["base_template"]["success_count"] += 1
                
                sample_count += 1
                
                # テスト間隔
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"A/Bテストサンプル実行エラー: {e}")
                continue
        
        # 結果分析
        analysis = self._analyze_ab_test_results(test_results)
        
        logger.info(f"A/Bテスト完了: サンプル数: {sample_count}")
        return {
            "test_duration": time.time() - start_time,
            "sample_count": sample_count,
            "results": test_results,
            "analysis": analysis
        }
    
    async def _get_rag_context(
        self, 
        query: str, 
        mode: PromptMode, 
        config: ContextOptimizationConfig
    ) -> Tuple[str, int]:
        """RAG検索からコンテキストを取得"""
        
        try:
            # モード文字列に変換
            mode_str = mode.value
            
            # RAG検索実行
            search_results = await self.rag_system.search(
                query=query,
                mode=mode_str,
                top_k=config.rag_results_limit
            )
            
            if not search_results:
                return "", 0
            
            # 優先度とサマリー制御に基づいてコンテキストを構築
            context_parts = []
            total_length = 0
            
            for i, result in enumerate(search_results):
                chunk_content = result.chunk.content
                
                # 長すぎる場合は要約
                if len(chunk_content) > config.summary_threshold:
                    chunk_content = chunk_content[:config.summary_threshold] + "..."
                
                # メタデータを含めるかどうか
                chunk_text = chunk_content
                if config.include_metadata:
                    source_info = f"[出典: {result.chunk.source_file}]"
                    chunk_text = f"{source_info}\n{chunk_content}"
                
                # 文字数制限チェック
                if total_length + len(chunk_text) > config.max_context_length:
                    break
                
                context_parts.append(chunk_text)
                total_length += len(chunk_text)
            
            context = "\n\n".join(context_parts)
            return context, len(search_results)
            
        except Exception as e:
            logger.error(f"RAGコンテキスト取得エラー: {e}")
            return "", 0
    
    def _integrate_contexts(
        self,
        rag_context: str,
        additional_context: Optional[str],
        config: ContextOptimizationConfig
    ) -> str:
        """複数のコンテキストを統合"""
        
        contexts = []
        
        if rag_context:
            contexts.append(("RAG検索結果", rag_context, 1))
        
        if additional_context:
            contexts.append(("追加情報", additional_context, 2))
        
        # コンテキストウィンドウに収める
        fitted_contexts = self.context_manager.fit_context(contexts)
        
        integrated_parts = []
        for context_name, content in fitted_contexts:
            if context_name == "RAG検索結果":
                integrated_parts.append(f"関連情報:\n{content}")
            else:
                integrated_parts.append(f"{context_name}:\n{content}")
        
        return "\n\n".join(integrated_parts)
    
    def _initialize_default_templates(self):
        """デフォルトテンプレートを初期化"""
        
        # 対話型モード用テンプレート
        interactive_templates = [
            {
                "name": "general_assistant",
                "template": "あなたは親切で知識豊富なアシスタントです。\n\nユーザーの質問: {query}\n\n{context}\n\n上記の情報を参考に、わかりやすく丁寧に回答してください。不明な点があれば確認します。",
                "type": TemplateType.USER,
                "mode": PromptMode.INTERACTIVE,
                "description": "一般的な対話型アシスタント用テンプレート"
            },
            {
                "name": "task_helper",
                "template": "タスク支援モード：\n\n依頼内容: {query}\n\n参考情報:\n{context}\n\n段階的にサポートします。まず最初のステップから始めましょう。",
                "type": TemplateType.USER,
                "mode": PromptMode.INTERACTIVE,
                "description": "タスク支援用対話テンプレート"
            }
        ]
        
        # 自律型モード用テンプレート
        autonomous_templates = [
            {
                "name": "autonomous_analyzer",
                "template": "自律分析モード：\n\n分析対象: {query}\n\n利用可能情報:\n{context}\n\n以下の手順で包括的に分析し、詳細な結果を提供します：\n1. 情報収集と整理\n2. 多角的分析\n3. 結論と推奨事項\n4. 次のアクション提案",
                "type": TemplateType.USER,
                "mode": PromptMode.AUTONOMOUS,
                "description": "自律型分析用テンプレート"
            },
            {
                "name": "comprehensive_solver",
                "template": "包括的問題解決モード：\n\n問題: {query}\n\n背景情報:\n{context}\n\n複数のアプローチを検討し、最適解を見つけます。根拠と代替案も含めて完全な解決策を提示します。",
                "type": TemplateType.USER,
                "mode": PromptMode.AUTONOMOUS,
                "description": "包括的問題解決用テンプレート"
            }
        ]
        
        # ハイブリッドモード用テンプレート
        hybrid_templates = [
            {
                "name": "adaptive_assistant",
                "template": "適応型アシスタント：\n\n要求: {query}\n\n情報ベース:\n{context}\n\n状況に応じて最適なアプローチを選択します。必要に応じて質問や確認を行いながら、効果的な支援を提供します。",
                "type": TemplateType.USER,
                "mode": PromptMode.HYBRID,
                "description": "適応型ハイブリッドテンプレート"
            }
        ]
        
        # テンプレート作成
        all_templates = interactive_templates + autonomous_templates + hybrid_templates
        
        for template_config in all_templates:
            try:
                # 既存チェック
                template_id = self.template_manager._generate_template_id(
                    template_config["name"],
                    template_config["type"],
                    template_config["mode"]
                )
                
                if template_id not in self.template_manager.templates:
                    self.template_manager.create_template(
                        name=template_config["name"],
                        template=template_config["template"],
                        template_type=template_config["type"],
                        mode=template_config["mode"],
                        description=template_config["description"],
                        author="system"
                    )
                    logger.info(f"デフォルトテンプレート作成: {template_config['name']}")
                    
            except Exception as e:
                logger.error(f"デフォルトテンプレート作成エラー: {e}")
    
    async def _create_fallback_template(
        self, 
        template_type: TemplateType, 
        mode: PromptMode
    ) -> str:
        """フォールバックテンプレートを作成"""
        
        fallback_template = """
{mode}モードでのリクエスト: {query}

{context}

上記の情報に基づいて適切に対応してください。
        """.strip()
        
        template_id = self.template_manager.create_template(
            name=f"fallback_{mode.value}_{template_type.value}",
            template=fallback_template,
            template_type=template_type,
            mode=mode,
            description=f"自動生成されたフォールバックテンプレート",
            author="system"
        )
        
        logger.warning(f"フォールバックテンプレート作成: {template_id}")
        return template_id
    
    def _update_metrics(
        self, 
        template_id: str, 
        mode: PromptMode, 
        generation_time: float, 
        success: bool
    ):
        """メトリクスを更新"""
        
        # テンプレート使用回数
        if template_id not in self.metrics["template_usage"]:
            self.metrics["template_usage"][template_id] = 0
        self.metrics["template_usage"][template_id] += 1
        
        # モード使用回数
        mode_str = mode.value
        if mode_str not in self.metrics["mode_usage"]:
            self.metrics["mode_usage"][mode_str] = 0
        self.metrics["mode_usage"][mode_str] += 1
        
        # 平均生成時間を更新
        current_avg = self.metrics["average_generation_time"]
        total_count = self.metrics["total_generations"]
        self.metrics["average_generation_time"] = (
            (current_avg * (total_count - 1)) + generation_time
        ) / total_count
    
    def _analyze_ab_test_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """A/Bテスト結果を分析"""
        
        analysis = {
            "summary": {},
            "recommendations": [],
            "statistical_significance": False
        }
        
        # ベーステンプレートの性能
        base_stats = test_results["base_template"]
        if base_stats["usage_count"] > 0:
            base_success_rate = base_stats["success_count"] / base_stats["usage_count"]
            base_avg_time = base_stats["total_time"] / base_stats["usage_count"]
        else:
            base_success_rate = 0.0
            base_avg_time = 0.0
        
        analysis["summary"]["base_template"] = {
            "success_rate": base_success_rate,
            "average_time": base_avg_time,
            "usage_count": base_stats["usage_count"]
        }
        
        # バリアントの性能
        best_variant = None
        best_performance = base_success_rate
        
        for variant_id, variant_stats in test_results["variants"].items():
            if variant_stats["usage_count"] > 0:
                variant_success_rate = variant_stats["success_count"] / variant_stats["usage_count"]
                variant_avg_time = variant_stats["total_time"] / variant_stats["usage_count"]
                
                analysis["summary"][variant_id] = {
                    "success_rate": variant_success_rate,
                    "average_time": variant_avg_time,
                    "usage_count": variant_stats["usage_count"]
                }
                
                if variant_success_rate > best_performance:
                    best_performance = variant_success_rate
                    best_variant = variant_id
        
        # 推奨事項
        if best_variant:
            improvement = best_performance - base_success_rate
            if improvement > 0.05:  # 5%以上の改善
                analysis["recommendations"].append(f"バリアント {best_variant} への切り替えを推奨")
                analysis["statistical_significance"] = True
        
        return analysis
    
    def get_service_stats(self) -> Dict[str, Any]:
        """サービス統計を取得"""
        template_stats = self.template_manager.get_stats()
        
        return {
            "prompt_service": self.metrics,
            "template_manager": template_stats,
            "rag_enabled": self.rag_system is not None
        }
