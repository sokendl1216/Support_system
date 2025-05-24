#!/usr/bin/env python3
"""設定管理システムのデバッグ用テスト"""

from core.settings import SettingsManager, ConfigSource, ConfigFormat
import tempfile
import json
from pathlib import Path

def test_basic_config():
    """基本的な設定読み込みテスト"""
    test_data = {'test_key': 'test_value', 'nested': {'key': 'value'}}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / 'test.json'
        with open(config_file, 'w') as f:
            json.dump(test_data, f)
        
        manager = SettingsManager(base_path=Path(temp_dir))
        manager.config_sources.clear()
        manager.add_config_source(ConfigSource('test.json', ConfigFormat.JSON))
        
        print('Loading configs...')
        success = manager.load_configs()
        print(f'Load success: {success}')
        print(f'Config data keys: {list(manager.config_data.keys())}')
        print(f'Config data: {manager.config_data}')
        print(f'Get test_key: {manager.get("test_key")}')
        print(f'Get nested.key: {manager.get("nested.key")}')

if __name__ == '__main__':
    test_basic_config()
