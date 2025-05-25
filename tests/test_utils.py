"""
テスト用ユーティリティと共通関数
"""
import asyncio
import functools
import os
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from unittest.mock import MagicMock

def async_test(coro):
    """非同期テスト関数のデコレータ"""
    @functools.wraps(coro)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

@dataclass
class MockResponse:
    """HTTPレスポンスのモック"""
    status_code: int
    text: str
    json_data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    
    def json(self) -> Dict[str, Any]:
        if self.json_data is not None:
            return self.json_data
        return json.loads(self.text)
    
    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise Exception(f"HTTP Error {self.status_code}")

class EventCapture:
    """イベントをキャプチャするためのユーティリティ"""
    def __init__(self):
        self.events = []
        self.handler_id = None
    
    def handler(self, event):
        """キャプチャされたイベントを記録"""
        self.events.append(event)
    
    def register(self, event_bus, event_type):
        """イベントバスにハンドラを登録"""
        from core.events import EventPriority
        self.handler_id = event_bus.on(event_type, self.handler, EventPriority.LOW)
    
    def unregister(self, event_bus):
        """イベントバスからハンドラを解除"""
        if self.handler_id:
            event_bus.off(self.handler_id)
            self.handler_id = None
    
    def clear(self):
        """キャプチャしたイベントをクリア"""
        self.events.clear()
    
    def get_events(self):
        """キャプチャしたイベントのリストを返す"""
        return self.events.copy()

class ConfigBuilder:
    """テスト用設定ビルダー"""
    def __init__(self):
        self.config = {}
    
    def add_database_config(self, host="localhost", port=5432, name="test_db"):
        """データベース設定を追加"""
        self.config["database"] = {
            "host": host,
            "port": port,
            "name": name,
            "user": "test_user",
            "password": "test_password"
        }
        return self
    
    def add_api_config(self, base_url="http://localhost:8000", timeout=30):
        """API設定を追加"""
        self.config["api"] = {
            "base_url": base_url,
            "timeout": timeout,
            "retry_attempts": 3
        }
        return self
    
    def add_ai_config(self, model="test-model", temperature=0.7):
        """AI設定を追加"""
        self.config["ai"] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": 1000
        }
        return self
    
    def add_custom_section(self, section_name: str, section_data: Dict[str, Any]):
        """カスタムセクションを追加"""
        self.config[section_name] = section_data
        return self
    
    def build(self) -> Dict[str, Any]:
        """設定ディクショナリを構築して返す"""
        return self.config.copy()
    
    def save_to_file(self, file_path: str) -> str:
        """設定をファイルに保存"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        return file_path
    
    def create_temp_file(self) -> str:
        """一時ファイルを作成して設定を保存"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', 
                                       delete=False, encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
            return f.name

def create_mock_database():
    """モックデータベースを作成"""
    mock_db = MagicMock()
    mock_db.connect.return_value = True
    mock_db.execute.return_value = True
    mock_db.fetch_all.return_value = []
    mock_db.close.return_value = True
    return mock_db

def create_mock_ai_service():
    """モックAIサービスを作成"""
    mock_ai = MagicMock()
    mock_ai.generate_response.return_value = "テスト応答"
    mock_ai.analyze_text.return_value = {"sentiment": "positive", "score": 0.8}
    mock_ai.is_available.return_value = True
    return mock_ai

def create_test_config_file(content: Dict[str, Any], suffix: str = '.json') -> str:
    """テスト用設定ファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, 
                                   delete=False, encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
        return f.name

def cleanup_test_files(*file_paths: str):
    """テストファイルをクリーンアップ"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass

def assert_config_equals(actual: Dict[str, Any], expected: Dict[str, Any], 
                        ignore_keys: Optional[List[str]] = None):
    """設定の深い比較を行う"""
    ignore_keys = ignore_keys or []
    
    def filter_dict(d, keys_to_ignore):
        return {k: v for k, v in d.items() if k not in keys_to_ignore}
    
    filtered_actual = filter_dict(actual, ignore_keys)
    filtered_expected = filter_dict(expected, ignore_keys)
    
    assert filtered_actual == filtered_expected

def create_test_directory_structure(base_path: str, structure: Dict[str, Any]) -> str:
    """テスト用ディレクトリ構造を作成"""
    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)
    
    for name, content in structure.items():
        path = base / name
        if isinstance(content, dict):
            create_test_directory_structure(str(path), content)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                if isinstance(content, (dict, list)):
                    json.dump(content, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(content))
    
    return str(base)
