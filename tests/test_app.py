"""
アプリケーション初期化とライフサイクルのテスト
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.app import Application
from core.exceptions import AppException
from core.events import EventBus
from .test_utils import EventCapture

@pytest.fixture
def app():
    """テスト用のアプリケーションインスタンス"""
    return Application()

@pytest.mark.unit
@pytest.mark.core
def test_application_initialization(app):
    """アプリケーション初期化のテスト"""
    assert app is not None
    assert hasattr(app, 'settings')
    assert hasattr(app, 'event_bus')

@pytest.mark.unit
@pytest.mark.core
def test_application_run_normal(app):
    """正常終了時のアプリケーション実行のテスト"""
    # イベントをキャプチャするためのセットアップ
    event_capture = EventCapture()
    event_capture.register(app.event_bus, 'APP_INITIALIZED')
    event_capture.register(app.event_bus, 'APP_SHUTDOWN')
    
    try:
        # アプリケーションを実行
        app.run()
        
        # 期待されるイベントが発生したか確認
        events = event_capture.get_events()
        event_types = [e.name for e in events]
        
        assert 'APP_INITIALIZED' in event_types
        assert 'APP_SHUTDOWN' in event_types
        
        # 順序も確認
        init_index = event_types.index('APP_INITIALIZED')
        shutdown_index = event_types.index('APP_SHUTDOWN')
        assert init_index < shutdown_index
        
    finally:
        # イベントキャプチャのクリーンアップ
        event_capture.unregister(app.event_bus)

@pytest.mark.unit
@pytest.mark.core
def test_application_run_with_exception():
    """例外発生時のアプリケーション実行のテスト"""
    with patch('core.app.Application') as MockApp:
        # モックのセットアップ
        mock_app = MagicMock()
        mock_app.event_bus = EventBus()
        MockApp.return_value = mock_app
        
        # 例外をスローするように設定
        def side_effect(*args, **kwargs):
            mock_app.event_bus.emit('APP_INITIALIZED')
            raise AppException("テスト例外")
        mock_app.run.side_effect = side_effect
        
        # イベントキャプチャをセットアップ
        event_capture = EventCapture()
        event_capture.register(mock_app.event_bus, 'APP_INITIALIZED')
        event_capture.register(mock_app.event_bus, 'ERROR_OCCURRED')
        event_capture.register(mock_app.event_bus, 'APP_SHUTDOWN')
        
        try:
            # テスト実行
            app = MockApp()
            with pytest.raises(AppException):
                app.run()
            
            # イベント発生の確認
            events = event_capture.get_events()
            event_types = [e.name for e in events]
            
            assert 'APP_INITIALIZED' in event_types
            assert 'ERROR_OCCURRED' in event_types
            assert 'APP_SHUTDOWN' in event_types
            
        finally:
            event_capture.unregister(mock_app.event_bus)

@pytest.mark.integration
@pytest.mark.core
def test_application_lifecycle(monkeypatch):
    """アプリケーション全体のライフサイクルテスト"""
    # 環境変数を設定
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    
    # アプリケーション初期化
    app = Application()
    
    # イベントキャプチャをセットアップ
    events = []
    def event_listener(event):
        events.append(event.name)
    
    app.event_bus.on('APP_INITIALIZED', event_listener)
    app.event_bus.on('APP_SHUTDOWN', event_listener)
    
    # テスト実行
    app.run()
    
    # 検証
    assert len(events) == 2
    assert events[0] == 'APP_INITIALIZED'
    assert events[1] == 'APP_SHUTDOWN'
