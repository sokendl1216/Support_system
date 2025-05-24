#!/usr/bin/env python3
"""設定管理システムのデバッグテスト"""

from core.settings import SettingsManager, ConfigValidator, Settings

def test_basic_set_get():
    """基本的なset/getテスト"""
    print("=== 基本的なset/getテスト ===")
    manager = SettingsManager()
    
    # 設定値を設定
    manager.set("test_priority", "high_priority", "source2")
    
    # 設定値を取得
    value = manager.get("test_priority")
    print(f"設定値: {value}")
    print(f"設定データ: {manager.config_data}")
    
    # 詳細情報を取得
    info = manager.get_info("test_priority")
    print(f"詳細情報: {info}")

def test_database_validation():
    """データベース設定バリデーションテスト"""
    print("\n=== データベース設定バリデーションテスト ===")
    validator = ConfigValidator()
    
    valid_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "username": "user"
    }
    
    result = validator.validate_database_config(valid_config)
    print(f"バリデーション結果: {result}")

def test_legacy_settings():
    """レガシー設定クラステスト"""
    print("\n=== レガシー設定クラステスト ===")
    settings = Settings()
    
    print(f"env: {settings.env}")
    print(f"debug: {settings.debug}")
    print(f"api_port: {settings.api_port}")

if __name__ == "__main__":
    test_basic_set_get()
    test_database_validation()
    test_legacy_settings()
