"""
テスト全体で共有される設定と fixture
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# プロジェクトルートへのパスを追加（テストモジュールからのインポートを簡素化）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト用ログ設定
@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """テスト実行中のログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("test")

# テスト実行時間計測
@pytest.fixture(autouse=True)
def timer(request):
    """各テストの実行時間を測定するフィクスチャ"""
    import time
    start = time.time()
    yield
    end = time.time()
    duration = end - start
    request.node.user_properties.append(("duration", duration))
    if duration > 1.0:  # 1秒以上かかるテストを識別
        logging.warning(f"Test {request.node.name} took {duration:.2f} seconds")

# 一時ファイル作成用ヘルパー
@pytest.fixture
def temp_file(tmp_path):
    """一時ファイルを作成して返す"""
    def _create_temp_file(content, filename="test_file.txt"):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path
    return _create_temp_file

# モック環境変数
@pytest.fixture
def mock_env_vars(monkeypatch):
    """テスト環境変数を一時的に設定する"""
    def _set_env_vars(env_vars):
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
    return _set_env_vars

# テスト設定オブジェクト（テスト間で共有される設定情報）
@pytest.fixture(scope="session")
def test_config():
    """テスト全体で共有される設定情報"""
    return {
        "base_url": "http://localhost:8000",
        "test_data_path": Path(__file__).parent / "test_data",
        "timeout": 5
    }

# 各サブシステムのスタブ/モックの設定
@pytest.fixture
def mock_db():
    """データベースのモック"""
    class MockDB:
        def __init__(self):
            self.data = {}
        
        def get(self, key, default=None):
            return self.data.get(key, default)
        
        def set(self, key, value):
            self.data[key] = value
            return True
        
        def delete(self, key):
            if key in self.data:
                del self.data[key]
                return True
            return False
    
    return MockDB()

@pytest.fixture
def mock_ai_service():
    """AIサービスのモック"""
    class MockAIService:
        def __init__(self):
            self.responses = {
                "default": "This is a mock AI response"
            }
        
        def set_response(self, query, response):
            self.responses[query] = response
        
        async def generate(self, prompt, **kwargs):
            for key, response in self.responses.items():
                if key in prompt:
                    return response
            return self.responses["default"]
    
    return MockAIService()
