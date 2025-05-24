# 設定管理システムのテスト
import pytest
import json
import tempfile
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings import SettingsManager, ConfigSource, ConfigFormat, Settings, ConfigValidator

@pytest.fixture
def temp_config_dir():
    """テスト用の一時設定ディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_config_data():
    """サンプル設定データ"""
    return {
        "environment": "test",
        "debug": True,
        "api": {
            "host": "localhost",
            "port": 8080
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser"
        }
    }

def test_settings_manager_initialization():
    """SettingsManager初期化テスト"""
    manager = SettingsManager()
    assert isinstance(manager, SettingsManager)
    assert len(manager.config_sources) > 0  # デフォルトソースが追加される

def test_config_source_addition():
    """設定ソース追加テスト"""
    manager = SettingsManager()
    initial_count = len(manager.config_sources)
    
    new_source = ConfigSource("test.json", ConfigFormat.JSON, priority=10)
    manager.add_config_source(new_source)
    
    assert len(manager.config_sources) == initial_count + 1

def test_json_config_loading(temp_config_dir, sample_config_data):
    """JSON設定ファイル読み込みテスト"""
    # テスト用JSON設定ファイルを作成
    config_file = temp_config_dir / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config_data, f)
    
    # SettingsManagerで読み込み
    manager = SettingsManager(base_path=temp_config_dir)
    manager.config_sources.clear()  # デフォルトソースをクリア
    manager.add_config_source(ConfigSource("test_config.json", ConfigFormat.JSON))
    
    success = manager.load_configs()
    assert success is True
    assert manager.get("environment") == "test"
    assert manager.get("api.port") == 8080

def test_nested_config_access(temp_config_dir, sample_config_data):
    """ネストした設定値アクセステスト"""
    config_file = temp_config_dir / "nested_test.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config_data, f)
    
    manager = SettingsManager(base_path=temp_config_dir)
    manager.config_sources.clear()
    manager.add_config_source(ConfigSource("nested_test.json", ConfigFormat.JSON))
    manager.load_configs()
    
    # ネストしたキーでアクセス
    assert manager.get("api.host") == "localhost"
    assert manager.get("database.username") == "testuser"
    
    # セクションとしてアクセス
    api_config = manager.get_section("api")
    assert api_config["host"] == "localhost"
    assert api_config["port"] == 8080

def test_env_variable_loading():
    """環境変数読み込みテスト"""
    # テスト用環境変数を設定
    os.environ["APP_TEST_VALUE"] = "test_env_value"
    os.environ["APP_TEST_BOOL"] = "true"
    os.environ["APP_TEST_INT"] = "42"
    
    try:
        manager = SettingsManager()
        manager.config_sources.clear()
        manager.add_config_source(ConfigSource("ENV", ConfigFormat.ENV))
        manager.load_configs()
        
        assert manager.get("test.value") == "test_env_value"
        assert manager.get("test.bool") is True
        assert manager.get("test.int") == 42
        
    finally:
        # 環境変数をクリーンアップ
        for key in ["APP_TEST_VALUE", "APP_TEST_BOOL", "APP_TEST_INT"]:
            if key in os.environ:
                del os.environ[key]

def test_config_priority():
    """設定優先度テスト"""
    manager = SettingsManager()
    
    # 低優先度の設定を設定
    manager.set("test_priority", "low_priority", "source1")
    
    # 高優先度の設定でオーバーライド
    manager.set("test_priority", "high_priority", "source2")
    
    # 最後に設定された値が取得される
    assert manager.get("test_priority") == "high_priority"

def test_default_values():
    """デフォルト値テスト"""
    manager = SettingsManager()
    
    # 存在しないキーにデフォルト値
    assert manager.get("nonexistent_key", "default_value") == "default_value"
    assert manager.get("another_nonexistent_key") is None

def test_config_info():
    """設定値詳細情報テスト"""
    manager = SettingsManager()
    manager.set("info_test", "test_value", "test_source")
    
    info = manager.get_info("info_test")
    assert info is not None
    assert info.value == "test_value"
    assert info.source == "test_source"

def test_config_validator():
    """設定値検証テスト"""
    validator = ConfigValidator()
    
    # データベース設定検証
    valid_db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "username": "user"
    }
    assert validator.validate_database_config(valid_db_config) is True
    
    invalid_db_config = {"host": "localhost"}  # 必要なキーが不足
    assert validator.validate_database_config(invalid_db_config) is False
    
    # API設定検証
    valid_api_config = {"port": 8080}
    assert validator.validate_api_config(valid_api_config) is True
    
    invalid_api_config = {"port": "invalid_port"}
    assert validator.validate_api_config(invalid_api_config) is False
    
    # AI設定検証
    valid_ai_config = {
        "ollama": {
            "base_url": "http://localhost:11434"
        }
    }
    assert validator.validate_ai_config(valid_ai_config) is True
    
    invalid_ai_config = {
        "ollama": {
            "base_url": "invalid_url"
        }
    }
    assert validator.validate_ai_config(invalid_ai_config) is False

def test_legacy_settings_class():
    """レガシーSettingsクラステスト"""
    settings = Settings()
    
    # デフォルト値の確認
    assert isinstance(settings.env, str)
    assert isinstance(settings.debug, bool)
    assert isinstance(settings.api_port, int)
    assert settings.api_port > 0

def test_env_value_parsing():
    """環境変数値の型変換テスト"""
    manager = SettingsManager()
    
    # boolean解析
    assert manager._parse_env_value("true") is True
    assert manager._parse_env_value("false") is False
    assert manager._parse_env_value("True") is True
    
    # integer解析
    assert manager._parse_env_value("123") == 123
    assert manager._parse_env_value("-456") == -456
    
    # float解析
    assert manager._parse_env_value("3.14") == 3.14
    
    # JSON解析
    assert manager._parse_env_value('{"key": "value"}') == {"key": "value"}
    assert manager._parse_env_value('[1, 2, 3]') == [1, 2, 3]
    
    # string（デフォルト）
    assert manager._parse_env_value("plain_string") == "plain_string"

def test_config_reload(temp_config_dir):
    """設定再読み込みテスト"""
    config_file = temp_config_dir / "reload_test.json"
    
    # 初期設定
    initial_config = {"test_key": "initial_value"}
    with open(config_file, 'w') as f:
        json.dump(initial_config, f)
    
    manager = SettingsManager(base_path=temp_config_dir)
    manager.config_sources.clear()
    manager.add_config_source(ConfigSource("reload_test.json", ConfigFormat.JSON))
    manager.load_configs()
    
    assert manager.get("test_key") == "initial_value"
    
    # 設定ファイルを更新
    updated_config = {"test_key": "updated_value"}
    with open(config_file, 'w') as f:
        json.dump(updated_config, f)
    
    # 再読み込み
    manager.reload()
    assert manager.get("test_key") == "updated_value"
