"""
AIエージェント最適化システム設定

設定のテンプレートと管理機能を提供
"""

import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import timedelta

from .optimization_system import OptimizationConfig


class ConfigurationManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "config/ai_optimization_config.yaml"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_config(self, config: OptimizationConfig) -> bool:
        """設定をファイルに保存"""
        try:
            config_dict = asdict(config)
            
            if self.config_path.suffix.lower() == '.json':
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:  # YAML
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            return True
            
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def load_config(self) -> Optional[OptimizationConfig]:
        """設定をファイルから読み込み"""
        try:
            if not self.config_path.exists():
                return None
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    config_dict = json.load(f)
                else:  # YAML
                    config_dict = yaml.safe_load(f)
            
            return OptimizationConfig(**config_dict)
            
        except Exception as e:
            print(f"Failed to load config: {e}")
            return None
    
    def create_default_config(self) -> OptimizationConfig:
        """デフォルト設定を作成して保存"""
        config = OptimizationConfig()
        self.save_config(config)
        return config


# プリセット設定

def get_development_config() -> OptimizationConfig:
    """開発環境用設定"""
    return OptimizationConfig(
        learning_enabled=True,
        learning_rate=0.2,  # 高い学習率
        pattern_analysis_interval=60,  # 短い間隔
        min_samples_for_learning=3,  # 少ないサンプル数
        
        performance_monitoring_enabled=True,
        performance_check_interval=30,  # 短い間隔
        load_balancing_enabled=True,
        auto_scaling_enabled=False,
        
        context_retention_days=1,  # 短い保持期間
        max_context_entries=1000,
        auto_context_cleanup=True,
        context_consolidation_interval=300,
        
        health_monitoring_enabled=True,
        health_check_interval=30,  # 短い間隔
        auto_recovery_enabled=True,
        alert_threshold=0.5,  # 低い閾値
        
        data_persistence_enabled=True,
        database_path="dev_ai_optimization.db",
        backup_interval=3600,  # 1時間
        
        experimental_features_enabled=True,
        a_b_testing_enabled=True,
        feature_flags={
            "advanced_learning": True,
            "predictive_optimization": True,
            "debug_mode": True
        }
    )


def get_production_config() -> OptimizationConfig:
    """本番環境用設定"""
    return OptimizationConfig(
        learning_enabled=True,
        learning_rate=0.05,  # 保守的な学習率
        pattern_analysis_interval=600,  # 10分間隔
        min_samples_for_learning=50,  # 十分なサンプル数
        
        performance_monitoring_enabled=True,
        performance_check_interval=120,  # 2分間隔
        load_balancing_enabled=True,
        auto_scaling_enabled=True,
        
        context_retention_days=30,  # 長い保持期間
        max_context_entries=100000,
        auto_context_cleanup=True,
        context_consolidation_interval=3600,  # 1時間
        
        health_monitoring_enabled=True,
        health_check_interval=300,  # 5分間隔
        auto_recovery_enabled=True,
        alert_threshold=0.8,  # 高い閾値
        
        data_persistence_enabled=True,
        database_path="prod_ai_optimization.db",
        backup_interval=86400,  # 24時間
        
        experimental_features_enabled=False,
        a_b_testing_enabled=False,
        feature_flags={
            "advanced_learning": True,
            "predictive_optimization": False,
            "debug_mode": False
        }
    )


def get_testing_config() -> OptimizationConfig:
    """テスト環境用設定"""
    return OptimizationConfig(
        learning_enabled=False,  # テスト中は学習無効
        learning_rate=0.1,
        pattern_analysis_interval=300,
        min_samples_for_learning=5,
        
        performance_monitoring_enabled=True,
        performance_check_interval=10,  # 非常に短い間隔
        load_balancing_enabled=False,
        auto_scaling_enabled=False,
        
        context_retention_days=1,
        max_context_entries=100,
        auto_context_cleanup=True,
        context_consolidation_interval=60,
        
        health_monitoring_enabled=True,
        health_check_interval=10,
        auto_recovery_enabled=False,  # テスト中は自動回復無効
        alert_threshold=0.3,
        
        data_persistence_enabled=False,  # テスト中は永続化無効
        database_path=":memory:",
        backup_interval=3600,
        
        experimental_features_enabled=True,
        a_b_testing_enabled=True,
        feature_flags={
            "advanced_learning": True,
            "predictive_optimization": True,
            "debug_mode": True,
            "test_mode": True
        }
    )


def get_lightweight_config() -> OptimizationConfig:
    """軽量設定（リソース制限環境用）"""
    return OptimizationConfig(
        learning_enabled=True,
        learning_rate=0.1,
        pattern_analysis_interval=1800,  # 30分間隔
        min_samples_for_learning=20,
        
        performance_monitoring_enabled=True,
        performance_check_interval=300,  # 5分間隔
        load_balancing_enabled=False,  # 負荷分散無効
        auto_scaling_enabled=False,
        
        context_retention_days=3,
        max_context_entries=5000,
        auto_context_cleanup=True,
        context_consolidation_interval=7200,  # 2時間
        
        health_monitoring_enabled=True,
        health_check_interval=600,  # 10分間隔
        auto_recovery_enabled=True,
        alert_threshold=0.7,
        
        data_persistence_enabled=True,
        database_path="lite_ai_optimization.db",
        backup_interval=172800,  # 48時間
        
        experimental_features_enabled=False,
        a_b_testing_enabled=False,
        feature_flags={
            "advanced_learning": False,
            "predictive_optimization": False,
            "debug_mode": False
        }
    )


# 設定テンプレート生成

def generate_config_template() -> str:
    """設定テンプレートを生成"""
    template = """
# AIエージェント最適化システム設定

# 学習設定
learning_enabled: true              # 学習機能の有効化
learning_rate: 0.1                  # 学習率 (0.0-1.0)
pattern_analysis_interval: 300      # パターン分析間隔 (秒)
min_samples_for_learning: 10        # 学習に必要な最小サンプル数

# パフォーマンス最適化設定
performance_monitoring_enabled: true # パフォーマンス監視の有効化
performance_check_interval: 60       # パフォーマンスチェック間隔 (秒)
load_balancing_enabled: true         # 負荷分散の有効化
auto_scaling_enabled: false          # 自動スケーリングの有効化

# コンテキスト管理設定
context_retention_days: 7            # コンテキスト保持日数
max_context_entries: 10000           # 最大コンテキストエントリ数
auto_context_cleanup: true           # 自動クリーンアップの有効化
context_consolidation_interval: 3600 # コンテキスト統合間隔 (秒)

# 診断設定
health_monitoring_enabled: true      # ヘルス監視の有効化
health_check_interval: 120           # ヘルスチェック間隔 (秒)
auto_recovery_enabled: true          # 自動回復の有効化
alert_threshold: 0.7                 # アラート閾値 (0.0-1.0)

# データ永続化設定
data_persistence_enabled: true       # データ永続化の有効化
database_path: "ai_optimization.db"  # データベースファイルパス
backup_interval: 86400               # バックアップ間隔 (秒)

# 実験設定
experimental_features_enabled: false # 実験的機能の有効化
a_b_testing_enabled: false          # A/Bテストの有効化

# 機能フラグ
feature_flags:
  advanced_learning: true            # 高度学習機能
  predictive_optimization: false     # 予測最適化
  debug_mode: false                  # デバッグモード
"""
    return template.strip()


def validate_config(config: OptimizationConfig) -> tuple[bool, list[str]]:
    """設定の妥当性を検証"""
    errors = []
    
    # 学習設定検証
    if config.learning_rate < 0 or config.learning_rate > 1:
        errors.append("learning_rate must be between 0.0 and 1.0")
    
    if config.pattern_analysis_interval < 10:
        errors.append("pattern_analysis_interval must be at least 10 seconds")
    
    if config.min_samples_for_learning < 1:
        errors.append("min_samples_for_learning must be at least 1")
    
    # パフォーマンス設定検証
    if config.performance_check_interval < 5:
        errors.append("performance_check_interval must be at least 5 seconds")
    
    # コンテキスト設定検証
    if config.context_retention_days < 1:
        errors.append("context_retention_days must be at least 1")
    
    if config.max_context_entries < 100:
        errors.append("max_context_entries must be at least 100")
    
    if config.context_consolidation_interval < 60:
        errors.append("context_consolidation_interval must be at least 60 seconds")
    
    # 診断設定検証
    if config.health_check_interval < 10:
        errors.append("health_check_interval must be at least 10 seconds")
    
    if config.alert_threshold < 0 or config.alert_threshold > 1:
        errors.append("alert_threshold must be between 0.0 and 1.0")
    
    # データベース設定検証
    if config.data_persistence_enabled and not config.database_path:
        errors.append("database_path is required when data_persistence_enabled is true")
    
    if config.backup_interval < 600:  # 10分
        errors.append("backup_interval must be at least 600 seconds")
    
    return len(errors) == 0, errors


# 設定比較ユーティリティ

def compare_configs(config1: OptimizationConfig, config2: OptimizationConfig) -> Dict[str, Any]:
    """2つの設定を比較"""
    dict1 = asdict(config1)
    dict2 = asdict(config2)
    
    differences = {}
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        val1 = dict1.get(key)
        val2 = dict2.get(key)
        
        if val1 != val2:
            differences[key] = {
                "config1": val1,
                "config2": val2
            }
    
    return differences


def merge_configs(base_config: OptimizationConfig, override_config: Dict[str, Any]) -> OptimizationConfig:
    """設定をマージ"""
    base_dict = asdict(base_config)
    base_dict.update(override_config)
    return OptimizationConfig(**base_dict)


# 環境変数からの設定読み込み

def load_config_from_env() -> Dict[str, Any]:
    """環境変数から設定を読み込み"""
    import os
    
    env_mapping = {
        "AI_OPT_LEARNING_ENABLED": ("learning_enabled", bool),
        "AI_OPT_LEARNING_RATE": ("learning_rate", float),
        "AI_OPT_PATTERN_INTERVAL": ("pattern_analysis_interval", int),
        "AI_OPT_MIN_SAMPLES": ("min_samples_for_learning", int),
        "AI_OPT_PERF_MONITORING": ("performance_monitoring_enabled", bool),
        "AI_OPT_PERF_INTERVAL": ("performance_check_interval", int),
        "AI_OPT_LOAD_BALANCING": ("load_balancing_enabled", bool),
        "AI_OPT_AUTO_SCALING": ("auto_scaling_enabled", bool),
        "AI_OPT_CONTEXT_DAYS": ("context_retention_days", int),
        "AI_OPT_MAX_CONTEXTS": ("max_context_entries", int),
        "AI_OPT_AUTO_CLEANUP": ("auto_context_cleanup", bool),
        "AI_OPT_CONSOLIDATION_INTERVAL": ("context_consolidation_interval", int),
        "AI_OPT_HEALTH_MONITORING": ("health_monitoring_enabled", bool),
        "AI_OPT_HEALTH_INTERVAL": ("health_check_interval", int),
        "AI_OPT_AUTO_RECOVERY": ("auto_recovery_enabled", bool),
        "AI_OPT_ALERT_THRESHOLD": ("alert_threshold", float),
        "AI_OPT_DATA_PERSISTENCE": ("data_persistence_enabled", bool),
        "AI_OPT_DATABASE_PATH": ("database_path", str),
        "AI_OPT_BACKUP_INTERVAL": ("backup_interval", int),
        "AI_OPT_EXPERIMENTAL": ("experimental_features_enabled", bool),
        "AI_OPT_AB_TESTING": ("a_b_testing_enabled", bool),
    }
    
    config_overrides = {}
    
    for env_key, (config_key, value_type) in env_mapping.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            try:
                if value_type == bool:
                    config_overrides[config_key] = env_value.lower() in ("true", "1", "yes", "on")
                elif value_type == int:
                    config_overrides[config_key] = int(env_value)
                elif value_type == float:
                    config_overrides[config_key] = float(env_value)
                else:  # str
                    config_overrides[config_key] = env_value
            except ValueError:
                print(f"Warning: Invalid value for {env_key}: {env_value}")
    
    return config_overrides
