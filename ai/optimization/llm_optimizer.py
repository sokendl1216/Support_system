"""
LLM最適化システム - 無料OSSモデルの性能最適化、量子化調整、メモリ効率化

Task 3-1b: LLM最適化の実装
- OSSモデルの性能最適化
- 量子化パラメータの調整
- メモリ効率化
- 動的パフォーマンス調整
"""

import asyncio
import logging
import psutil
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import statistics
from datetime import datetime, timedelta

from ai.llm_service import GenerationRequest, GenerationConfig, GenerationResponse

logger = logging.getLogger(__name__)

@dataclass
class ModelOptimizationProfile:
    """モデル最適化プロファイル"""
    model_name: str
    
    # 量子化設定
    quantization_level: str = "q4_0"  # q4_0, q5_0, q5_1, q8_0, f16, f32
    context_length: int = 2048
    
    # メモリ設定
    memory_limit_gb: float = 8.0
    cache_size_mb: int = 512
    
    # パフォーマンス設定
    num_threads: int = 4
    batch_size: int = 1
    use_gpu: bool = False
    
    # 動的調整設定
    auto_optimize: bool = True
    target_response_time: float = 5.0  # 目標応答時間（秒）
    target_memory_usage: float = 0.8   # 目標メモリ使用率
    
    # 統計情報
    performance_stats: Dict[str, Any] = field(default_factory=dict)
    last_optimized: Optional[datetime] = None

@dataclass
class OptimizationMetrics:
    """最適化メトリクス"""
    response_time: float
    memory_usage: float
    cpu_usage: float
    tokens_per_second: float
    error_rate: float
    timestamp: datetime = field(default_factory=datetime.now)

class LLMOptimizer:
    """LLM最適化マネージャー"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/optimization.json"
        self.profiles: Dict[str, ModelOptimizationProfile] = {}
        self.metrics_history: Dict[str, List[OptimizationMetrics]] = {}
        self.optimization_lock = asyncio.Lock()
        
        # 最適化設定
        self.optimization_config = {
            "auto_optimization_interval": 300,  # 5分間隔
            "metrics_retention_hours": 24,
            "min_samples_for_optimization": 10,
            "performance_degradation_threshold": 0.2,
            "memory_pressure_threshold": 0.9
        }
        
        self._load_profiles()
        
    def _load_profiles(self):
        """最適化プロファイルの読み込み"""
        try:
            config_path = Path(self.config_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for model_name, profile_data in data.get("profiles", {}).items():
                    profile = ModelOptimizationProfile(
                        model_name=model_name,
                        **profile_data
                    )
                    self.profiles[model_name] = profile
                    
                logger.info(f"最適化プロファイルを読み込みました: {len(self.profiles)}件")
            else:
                # デフォルトプロファイルを作成
                self._create_default_profiles()
                
        except Exception as e:
            logger.error(f"最適化プロファイル読み込みエラー: {e}")
            self._create_default_profiles()
    
    def _create_default_profiles(self):
        """デフォルト最適化プロファイルの作成"""
        default_models = {
            "deepseek-coder": {
                "quantization_level": "q4_0",
                "context_length": 4096,
                "memory_limit_gb": 8.0,
                "num_threads": 4,
                "target_response_time": 3.0
            },
            "llama2": {
                "quantization_level": "q5_0",
                "context_length": 2048,
                "memory_limit_gb": 6.0,
                "num_threads": 4,
                "target_response_time": 4.0
            },
            "mistral": {
                "quantization_level": "q4_0",
                "context_length": 4096,
                "memory_limit_gb": 6.0,
                "num_threads": 4,
                "target_response_time": 3.5
            },
            "codellama": {
                "quantization_level": "q4_0",
                "context_length": 8192,
                "memory_limit_gb": 8.0,
                "num_threads": 6,
                "target_response_time": 4.0
            }
        }
        
        for model_name, config in default_models.items():
            self.profiles[model_name] = ModelOptimizationProfile(
                model_name=model_name,
                **config
            )
        
        self._save_profiles()
        logger.info("デフォルト最適化プロファイルを作成しました")
    
    def _save_profiles(self):
        """最適化プロファイルの保存"""
        try:
            config_path = Path(self.config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "profiles": {},
                "optimization_config": self.optimization_config,
                "last_updated": datetime.now().isoformat()
            }
            
            for model_name, profile in self.profiles.items():
                data["profiles"][model_name] = {
                    "quantization_level": profile.quantization_level,
                    "context_length": profile.context_length,
                    "memory_limit_gb": profile.memory_limit_gb,
                    "cache_size_mb": profile.cache_size_mb,
                    "num_threads": profile.num_threads,
                    "batch_size": profile.batch_size,
                    "use_gpu": profile.use_gpu,
                    "auto_optimize": profile.auto_optimize,
                    "target_response_time": profile.target_response_time,
                    "target_memory_usage": profile.target_memory_usage,
                    "performance_stats": profile.performance_stats,
                    "last_optimized": profile.last_optimized.isoformat() if profile.last_optimized else None
                }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"最適化プロファイル保存エラー: {e}")
    
    async def get_optimization_config(self, model_name: str) -> Dict[str, Any]:
        """モデルの最適化設定を取得"""
        profile = self.profiles.get(model_name)
        if not profile:
            # 新しいモデルの場合、デフォルトプロファイルを作成
            profile = ModelOptimizationProfile(model_name=model_name)
            self.profiles[model_name] = profile
            self._save_profiles()
        
        return {
            "model": model_name,
            "options": {
                "num_ctx": profile.context_length,
                "num_thread": profile.num_threads,
                "low_vram": profile.use_gpu,
                "numa": False,
                "main_gpu": 0 if profile.use_gpu else -1,
                "mmap": True,
                "mlock": False,
                "f16_kv": profile.quantization_level in ["f16", "f32"],
                "logits_all": False,
                "vocab_only": False,
                "use_mmap": True,
                "use_mlock": False,
                "embedding_only": False,
                "n_keep": 0,
                "batch_size": profile.batch_size,
                "n_probs": 0,
                "top_k": 40,
                "top_p": 0.9,
                "tfs_z": 1.0,
                "typical_p": 1.0,
                "repeat_last_n": 64,
                "temperature": 0.8,
                "repeat_penalty": 1.1,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "mirostat": 0,
                "mirostat_lr": 0.1,
                "mirostat_ent": 5.0,
                "penalize_nl": True,
                "stop": [],
                "seed": -1,
                "ignore_eos": False
            }
        }
    
    async def record_performance_metrics(self, model_name: str, 
                                       response_time: float,
                                       token_count: int,
                                       success: bool):
        """パフォーマンスメトリクスの記録"""
        try:
            # システムメトリクスの取得
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            tokens_per_second = token_count / response_time if response_time > 0 else 0
            error_rate = 0.0 if success else 1.0
            
            metrics = OptimizationMetrics(
                response_time=response_time,
                memory_usage=memory_info.percent / 100.0,
                cpu_usage=cpu_percent / 100.0,
                tokens_per_second=tokens_per_second,
                error_rate=error_rate
            )
            
            # メトリクス履歴に追加
            if model_name not in self.metrics_history:
                self.metrics_history[model_name] = []
            
            self.metrics_history[model_name].append(metrics)
            
            # 古いメトリクスの削除（24時間以上古いもの）
            cutoff_time = datetime.now() - timedelta(
                hours=self.optimization_config["metrics_retention_hours"]
            )
            self.metrics_history[model_name] = [
                m for m in self.metrics_history[model_name] 
                if m.timestamp > cutoff_time
            ]
            
            # プロファイルの統計情報を更新
            await self._update_profile_stats(model_name)
            
            # 自動最適化の実行判定
            if self.profiles.get(model_name, {}).auto_optimize:
                await self._check_auto_optimization(model_name)
                
        except Exception as e:
            logger.error(f"パフォーマンスメトリクス記録エラー: {e}")
    
    async def _update_profile_stats(self, model_name: str):
        """プロファイル統計情報の更新"""
        profile = self.profiles.get(model_name)
        metrics = self.metrics_history.get(model_name, [])
        
        if not profile or not metrics:
            return
        
        recent_metrics = metrics[-100:]  # 最新100件
        
        if recent_metrics:
            profile.performance_stats = {
                "avg_response_time": statistics.mean(m.response_time for m in recent_metrics),
                "avg_memory_usage": statistics.mean(m.memory_usage for m in recent_metrics),
                "avg_cpu_usage": statistics.mean(m.cpu_usage for m in recent_metrics),
                "avg_tokens_per_second": statistics.mean(m.tokens_per_second for m in recent_metrics),
                "error_rate": statistics.mean(m.error_rate for m in recent_metrics),
                "total_requests": len(recent_metrics),
                "last_updated": datetime.now().isoformat()
            }
    
    async def _check_auto_optimization(self, model_name: str):
        """自動最適化の実行判定"""
        async with self.optimization_lock:
            profile = self.profiles.get(model_name)
            metrics = self.metrics_history.get(model_name, [])
            
            if not profile or len(metrics) < self.optimization_config["min_samples_for_optimization"]:
                return
            
            # 最後の最適化から十分時間が経過しているかチェック
            if profile.last_optimized:
                time_since_last = datetime.now() - profile.last_optimized
                if time_since_last.total_seconds() < self.optimization_config["auto_optimization_interval"]:
                    return
            
            recent_metrics = metrics[-20:]  # 最新20件で判定
            
            # パフォーマンス劣化の検出
            avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
            avg_memory_usage = statistics.mean(m.memory_usage for m in recent_metrics)
            error_rate = statistics.mean(m.error_rate for m in recent_metrics)
            
            needs_optimization = False
            optimization_reason = []
            
            # 応答時間が目標を上回っている
            if avg_response_time > profile.target_response_time * (1 + self.optimization_config["performance_degradation_threshold"]):
                needs_optimization = True
                optimization_reason.append(f"応答時間が目標を上回っています: {avg_response_time:.2f}s > {profile.target_response_time}s")
            
            # メモリ使用率が高すぎる
            if avg_memory_usage > self.optimization_config["memory_pressure_threshold"]:
                needs_optimization = True
                optimization_reason.append(f"メモリ使用率が高すぎます: {avg_memory_usage:.1%}")
            
            # エラー率が高い
            if error_rate > 0.1:  # 10%以上のエラー率
                needs_optimization = True
                optimization_reason.append(f"エラー率が高すぎます: {error_rate:.1%}")
            
            if needs_optimization:
                logger.info(f"自動最適化を実行します: {model_name} - {', '.join(optimization_reason)}")
                await self.optimize_model(model_name, auto=True)
    
    async def optimize_model(self, model_name: str, auto: bool = False) -> bool:
        """モデルの最適化実行"""
        try:
            profile = self.profiles.get(model_name)
            if not profile:
                logger.warning(f"最適化プロファイルが見つかりません: {model_name}")
                return False
            
            metrics = self.metrics_history.get(model_name, [])
            if len(metrics) < 5:
                logger.info(f"最適化に必要な十分なメトリクスがありません: {model_name}")
                return False
            
            recent_metrics = metrics[-20:]
            avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
            avg_memory_usage = statistics.mean(m.memory_usage for m in recent_metrics)
            
            optimizations_applied = []
            
            # 応答時間の最適化
            if avg_response_time > profile.target_response_time:
                if profile.context_length > 1024:
                    old_context = profile.context_length
                    profile.context_length = max(1024, int(profile.context_length * 0.8))
                    optimizations_applied.append(f"コンテキスト長: {old_context} -> {profile.context_length}")
                
                if profile.num_threads < 8:
                    old_threads = profile.num_threads
                    profile.num_threads = min(8, profile.num_threads + 1)
                    optimizations_applied.append(f"スレッド数: {old_threads} -> {profile.num_threads}")
            
            # メモリ使用率の最適化
            if avg_memory_usage > profile.target_memory_usage:
                # より激しい量子化を適用
                quantization_levels = ["f32", "f16", "q8_0", "q5_1", "q5_0", "q4_0"]
                current_index = quantization_levels.index(profile.quantization_level) if profile.quantization_level in quantization_levels else 0
                
                if current_index < len(quantization_levels) - 1:
                    old_quant = profile.quantization_level
                    profile.quantization_level = quantization_levels[current_index + 1]
                    optimizations_applied.append(f"量子化レベル: {old_quant} -> {profile.quantization_level}")
                
                # キャッシュサイズの削減
                if profile.cache_size_mb > 256:
                    old_cache = profile.cache_size_mb
                    profile.cache_size_mb = max(256, int(profile.cache_size_mb * 0.8))
                    optimizations_applied.append(f"キャッシュサイズ: {old_cache}MB -> {profile.cache_size_mb}MB")
            
            if optimizations_applied:
                profile.last_optimized = datetime.now()
                self._save_profiles()
                
                optimization_type = "自動" if auto else "手動"
                logger.info(f"{optimization_type}最適化を実行しました: {model_name} - {', '.join(optimizations_applied)}")
                return True
            else:
                logger.info(f"最適化の必要がありません: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"モデル最適化エラー: {e}")
            return False
    
    async def get_performance_report(self, model_name: str) -> Dict[str, Any]:
        """パフォーマンスレポートの生成"""
        profile = self.profiles.get(model_name)
        metrics = self.metrics_history.get(model_name, [])
        
        if not profile:
            return {"error": "プロファイルが見つかりません"}
        
        recent_metrics = metrics[-100:] if metrics else []
        
        report = {
            "model_name": model_name,
            "profile": {
                "quantization_level": profile.quantization_level,
                "context_length": profile.context_length,
                "memory_limit_gb": profile.memory_limit_gb,
                "num_threads": profile.num_threads,
                "auto_optimize": profile.auto_optimize,
                "last_optimized": profile.last_optimized.isoformat() if profile.last_optimized else None
            },
            "performance_stats": profile.performance_stats,
            "recent_performance": {},
            "optimization_recommendations": []
        }
        
        if recent_metrics:
            report["recent_performance"] = {
                "total_requests": len(recent_metrics),
                "avg_response_time": statistics.mean(m.response_time for m in recent_metrics),
                "min_response_time": min(m.response_time for m in recent_metrics),
                "max_response_time": max(m.response_time for m in recent_metrics),
                "avg_tokens_per_second": statistics.mean(m.tokens_per_second for m in recent_metrics),
                "avg_memory_usage": statistics.mean(m.memory_usage for m in recent_metrics),
                "error_rate": statistics.mean(m.error_rate for m in recent_metrics)
            }
            
            # 最適化推奨事項の生成
            avg_response_time = report["recent_performance"]["avg_response_time"]
            avg_memory_usage = report["recent_performance"]["avg_memory_usage"]
            error_rate = report["recent_performance"]["error_rate"]
            
            if avg_response_time > profile.target_response_time * 1.2:
                report["optimization_recommendations"].append({
                    "type": "performance",
                    "issue": "応答時間が目標を大幅に上回っています",
                    "current": f"{avg_response_time:.2f}秒",
                    "target": f"{profile.target_response_time:.2f}秒",
                    "suggestion": "コンテキスト長の削減またはスレッド数の増加を検討してください"
                })
            
            if avg_memory_usage > 0.85:
                report["optimization_recommendations"].append({
                    "type": "memory",
                    "issue": "メモリ使用率が高すぎます",
                    "current": f"{avg_memory_usage:.1%}",
                    "suggestion": "より激しい量子化レベルまたはキャッシュサイズの削減を検討してください"
                })
            
            if error_rate > 0.05:
                report["optimization_recommendations"].append({
                    "type": "reliability",
                    "issue": "エラー率が高すぎます",
                    "current": f"{error_rate:.1%}",
                    "suggestion": "モデル設定の見直しまたはリソース割り当ての増加を検討してください"
                })
        
        return report
    
    async def reset_model_optimization(self, model_name: str):
        """モデル最適化設定のリセット"""
        if model_name in self.profiles:
            # デフォルト設定に戻す
            self.profiles[model_name] = ModelOptimizationProfile(model_name=model_name)
            self._save_profiles()
            
            # メトリクス履歴をクリア
            if model_name in self.metrics_history:
                del self.metrics_history[model_name]
            
            logger.info(f"モデル最適化設定をリセットしました: {model_name}")
    
    async def get_system_resources(self) -> Dict[str, Any]:
        """システムリソース情報の取得"""
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        return {
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_percent": memory.percent,
                "free_percent": 100 - memory.percent
            },
            "cpu": {
                "logical_cores": cpu_count,
                "physical_cores": psutil.cpu_count(logical=False),
                "current_usage": psutil.cpu_percent(interval=1.0)
            },
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
