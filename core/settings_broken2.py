"""
設定管理システム

マルチソース設定読み込み、バリデーション、優先度処理を提供します。
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigFormat(Enum):
    """設定ファイル形式"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"

@dataclass
class ConfigSource:
    """設定ソース定義"""
    path: str
    format: ConfigFormat
    priority: int = 1
    required: bool = False

@dataclass
class ConfigValue:
    """設定値とメタデータ"""
    value: Any
    source: str

class ConfigValidator:
    """設定値の検証"""
    
    def validate_database_config(self, config: Dict[str, Any]) -> bool:
        """データベース設定の検証"""
        required_fields = ["url"]
        # urlがない場合は、host, port, database, usernameで構成されるかチェック
        if "url" not in config:
            alt_required = ["host", "database", "username"]
            return all(field in config for field in alt_required)
        return all(field in config for field in required_fields)
    
    def validate_api_config(self, config: Dict[str, Any]) -> bool:
        """API設定の検証"""
        if "port" in config:
            port = config["port"]            if not isinstance(port, int) or port < 1 or port > 65535:
                return False
        return True
    
    def validate_ai_config(self, config: Dict[str, Any]) -> bool:
        """AI設定の検証"""
        if "ollama" in config:
            ollama_config = config["ollama"]
            if "base_url" in ollama_config:
                url = ollama_config["base_url"]
                # 基本的なURL形式の検証
                if not (url.startswith("http://") or url.startswith("https://")):
                    return False
        return True

class SettingsManager:
    """設定管理マネージャー"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.config_sources: List[ConfigSource] = []
        self.config_data: Dict[str, ConfigValue] = {}
        self.validator = ConfigValidator()
        self._loaded = False
        
        # デフォルトの設定ソースを追加
        self._add_default_sources()
    
    def _add_default_sources(self):
        """デフォルトの設定ソースを追加"""
        default_sources = [
            ConfigSource("config.json", ConfigFormat.JSON, priority=1),
            ConfigSource("config.yaml", ConfigFormat.YAML, priority=2),
            ConfigSource("local.json", ConfigFormat.JSON, priority=3),
            ConfigSource("ENV", ConfigFormat.ENV, priority=4)
        ]
        
        for source in default_sources:
            self.add_config_source(source)
    
    def add_config_source(self, source: ConfigSource):
        """設定ソースを追加"""
        self.config_sources.append(source)
        # 優先度順にソート
        self.config_sources.sort(key=lambda s: s.priority)
    
    def load_configs(self) -> bool:
        """すべての設定ファイルを読み込み"""
        try:
            # 既存の設定をクリア
            self.config_data.clear()
            
            for source in self.config_sources:
                self._load_single_source(source)
            
            # 設定値の検証
            self._validate_configs()
            
            self._loaded = True
            logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _load_single_source(self, source: ConfigSource):
        """単一の設定ソースを読み込み"""
        try:
            if source.format == ConfigFormat.ENV:
                self._load_env_config(source)
            else:
                file_path = self.base_path / source.path
                if not file_path.exists():
                    if source.required:
                        raise FileNotFoundError(f"Required config file not found: {source.path}")
                    return
                
                if source.format == ConfigFormat.JSON:
                    self._load_json_config(file_path, source)
                elif source.format == ConfigFormat.YAML:
                    self._load_yaml_config(file_path, source)
                    
        except Exception as e:
            logger.error(f"Error loading config source {source.path}: {e}")
            if source.required:
                raise
    
    def _load_json_config(self, file_path: Path, source: ConfigSource):
        """JSON設定ファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # コメント行を除去（#で始まる行）
                lines = content.split('\n')
                filtered_lines = [
                    line for line in lines 
                    if not line.strip().startswith('#') and line.strip()
                ]
                clean_content = '\n'.join(filtered_lines)
                
                if not clean_content.strip():
                    logger.warning(f"Empty JSON file: {file_path}")
                    return
                    
                data = json.loads(clean_content)
                if data:
                    self._merge_config_data(data, source.path)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            if source.required:
                raise
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            if source.required:
                raise
    
    def _load_yaml_config(self, file_path: Path, source: ConfigSource):
        """YAML設定ファイルを読み込み"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data:
                    self._merge_config_data(data, source.path)
        except ImportError:
            logger.warning("PyYAML not installed, skipping YAML config files")
        except Exception as e:
            logger.error(f"Error reading YAML file {file_path}: {e}")
            if source.required:
                raise
    
    def _load_env_config(self, source: ConfigSource):
        """環境変数から設定を読み込み"""
        env_prefix = "APP_"  # アプリケーション固有のプレフィックス
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                # ネストした設定キーをサポート（例：APP_DB_HOST -> db.host）
                nested_key = config_key.replace('_', '.')
                self._set_nested_value(nested_key, value, source.path)
    
    def _merge_config_data(self, data: Dict[str, Any], source_name: str):
        """設定データをマージ"""
        if isinstance(data, dict):
            self._flatten_and_store(data, source_name)
        else:
            logger.warning(f"Invalid config data format from {source_name}, expected dict, got {type(data)}")
    
    def _flatten_and_store(self, data: Dict[str, Any], source_name: str, prefix: str = "", max_depth: int = 10):
        """ネストした設定データを平坦化して保存"""
        if max_depth <= 0:
            logger.warning(f"Maximum nesting depth reached for {prefix}, skipping further nesting")
            return
            
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and value:  # 空の辞書はスキップ
                self._flatten_and_store(value, source_name, full_key, max_depth - 1)
            else:
                self.config_data[full_key] = ConfigValue(
                    value=value,
                    source=source_name
                )
    
    def _set_nested_value(self, key: str, value: str, source_name: str):
        """ネストしたキーの値を設定"""
        # 型推論を試行
        parsed_value = self._parse_env_value(value)
        self.config_data[key] = ConfigValue(
            value=parsed_value,
            source=source_name
        )
    
    def _parse_env_value(self, value: str) -> Any:
        """環境変数の値を適切な型に変換"""
        # boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # float
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON
        if value.startswith(('{', '[')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
          # string（デフォルト）
        return value
    
    def _validate_configs(self):
        """設定値の検証"""
        # バリデーションは既にロードされた設定に対してのみ実行
        # データベース設定の検証
        db_config = self._get_section_data("database")
        if db_config and not self.validator.validate_database_config(db_config):
            logger.warning("Invalid database configuration")
        
        # API設定の検証
        api_config = self._get_section_data("api")
        if api_config and not self.validator.validate_api_config(api_config):
            logger.warning("Invalid API configuration")
        
        # AI設定の検証
        ai_config = self._get_section_data("ai")
        if ai_config and not self.validator.validate_ai_config(ai_config):
            logger.warning("Invalid AI configuration")
    
    def _get_section_data(self, section: str) -> Dict[str, Any]:
        """設定セクションを取得（内部用、再帰を避ける）"""
        section_data = {}
        prefix = f"{section}."
        
        for key, config_value in self.config_data.items():
            if key.startswith(prefix):
                # セクションプレフィックスを除去
                sub_key = key[len(prefix):]
                section_data[sub_key] = config_value.value
            elif key == section:
                # セクション自体が値の場合
                if isinstance(config_value.value, dict):
                    section_data.update(config_value.value)
                else:
                    section_data[section] = config_value.value
        
        return section_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        if not self._loaded:
            try:
                self.load_configs()
            except Exception as e:
                logger.error(f"Failed to load configs on first access: {e}")
                return default
        
        if key in self.config_data:
            return self.config_data[key].value
        return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """設定セクションを取得"""
        if not self._loaded:
            try:
                self.load_configs()
            except Exception as e:
                logger.error(f"Failed to load configs on section access: {e}")
                return {}
        
        section_data = {}
        prefix = f"{section}."
        
        for key, config_value in self.config_data.items():
            if key.startswith(prefix):
                # セクションプレフィックスを除去
                sub_key = key[len(prefix):]
                section_data[sub_key] = config_value.value
            elif key == section:
                # セクション自体が値の場合
                if isinstance(config_value.value, dict):
                    section_data.update(config_value.value)
                else:
                    section_data[section] = config_value.value
        
        return section_data
    
    def get_info(self, key: str) -> Optional[ConfigValue]:
        """設定値の詳細情報を取得"""
        if not self._loaded:
            try:
                self.load_configs()
            except Exception as e:
                logger.error(f"Failed to load configs on info access: {e}")
                return None
        
        if key in self.config_data:
            return self.config_data[key]
        return None
    
    def set(self, key: str, value: Any, source: str = "manual"):
        """設定値を手動で設定"""
        self.config_data[key] = ConfigValue(value=value, source=source)
    
    def reload(self) -> bool:
        """設定を再読み込み"""
        self._loaded = False
        return self.load_configs()
    
    def get_config_info(self) -> Dict[str, Any]:
        """設定情報を取得"""
        if not self._loaded:
            self.load_configs()
        
        info = {
            "sources": [
                {
                    "path": source.path,
                    "format": source.format.value,
                    "priority": source.priority,
                    "required": source.required
                }
                for source in self.config_sources
            ],
            "loaded_values": len(self.config_data),
            "config_keys": list(self.config_data.keys())
        }
        
        return info

# レガシークラスとの互換性のため
class Settings:
    """レガシー設定クラス（互換性のため）"""
    def __init__(self):
        self._manager = SettingsManager()
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._manager.get(key, default)
    
    @property
    def env(self) -> str:
        return self._manager.get("environment", "development")
    
    @property
    def debug(self) -> bool:
        return self._manager.get("debug", False)
    
    @property
    def api_port(self) -> int:
        return self._manager.get("api.port", 8000)

class AppSettings(Settings):
    """アプリケーション設定クラス（互換性のため）"""
    pass

class DatabaseSettings(Settings):
    """データベース設定クラス（互換性のため）"""
    def __init__(self):
        super().__init__()
    
    @property
    def url(self) -> str:
        return self._manager.get("database.url", "sqlite:///app.db")
    
    @property
    def echo(self) -> bool:
        return self._manager.get("database.echo", False)

class AISettings(Settings):
    """AI設定クラス（互換性のため）"""
    def __init__(self):
        super().__init__()
    
    @property
    def default_model(self) -> str:
        return self._manager.get("ai.default_model", "gpt-3.5-turbo")
    
    @property
    def timeout(self) -> int:
        return self._manager.get("ai.timeout", 30)

# グローバル設定マネージャーインスタンス
settings_manager = SettingsManager()
