# イベントバスシステムのテスト
import pytest
import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.events import EventBus, Event, EventPriority, EventHandler

@pytest.fixture
def event_bus():
    """テスト用のイベントバスインスタンス"""
    return EventBus()

def test_event_bus_initialization(event_bus):
    """イベントバス初期化テスト"""
    assert isinstance(event_bus, EventBus)
    assert len(event_bus._handlers) == 0
    assert len(event_bus._event_history) == 0

def test_sync_handler_registration(event_bus):
    """同期ハンドラー登録テスト"""
    def test_handler(event):
        pass
    
    handler_id = event_bus.on("test_event", test_handler, EventPriority.HIGH)
    assert isinstance(handler_id, str)
    assert len(event_bus.get_handlers("test_event")) == 1
    
    handler_info = event_bus.get_handlers("test_event")[0]
    assert handler_info.priority == EventPriority.HIGH
    assert not handler_info.is_async

def test_async_handler_registration(event_bus):
    """非同期ハンドラー登録テスト"""
    async def async_test_handler(event):
        pass
    
    handler_id = event_bus.on("async_test_event", async_test_handler, EventPriority.NORMAL)
    assert isinstance(handler_id, str)
    
    handler_info = event_bus.get_handlers("async_test_event")[0]
    assert handler_info.is_async

def test_handler_priority_sorting(event_bus):
    """ハンドラー優先度ソートテスト"""
    def low_handler(event):
        pass
    
    def high_handler(event):
        pass
    
    def critical_handler(event):
        pass
    
    # 異なる優先度でハンドラーを登録
    event_bus.on("priority_test", low_handler, EventPriority.LOW)
    event_bus.on("priority_test", critical_handler, EventPriority.CRITICAL)
    event_bus.on("priority_test", high_handler, EventPriority.HIGH)
    
    handlers = event_bus.get_handlers("priority_test")
    # 優先度順にソートされているか確認
    assert handlers[0].priority == EventPriority.CRITICAL
    assert handlers[1].priority == EventPriority.HIGH
    assert handlers[2].priority == EventPriority.LOW

def test_sync_event_emission(event_bus):
    """同期イベント発火テスト"""
    results = []
    
    def test_handler(event):
        results.append(event.data)
    
    event_bus.on("sync_test", test_handler)
    
    emitted_event = event_bus.emit("sync_test", {"key": "value"})
    
    assert isinstance(emitted_event, Event)
    assert emitted_event.name == "sync_test"
    assert emitted_event.data["key"] == "value"
    assert len(results) == 1
    assert results[0]["key"] == "value"

@pytest.mark.asyncio
async def test_async_event_emission(event_bus):
    """非同期イベント発火テスト"""
    results = []
    
    async def async_test_handler(event):
        await asyncio.sleep(0.1)  # 非同期処理のシミュレーション
        results.append(event.data)
    
    def sync_test_handler(event):
        results.append("sync_handled")
    
    event_bus.on("async_test", async_test_handler)
    event_bus.on("async_test", sync_test_handler)
    
    emitted_event = await event_bus.emit_async("async_test", {"async_key": "async_value"})
    
    assert isinstance(emitted_event, Event)
    assert emitted_event.name == "async_test"
    assert len(results) == 2
    assert "sync_handled" in results
    assert {"async_key": "async_value"} in results

def test_handler_removal(event_bus):
    """ハンドラー削除テスト"""
    def test_handler(event):
        pass
    
    handler_id = event_bus.on("removal_test", test_handler)
    assert len(event_bus.get_handlers("removal_test")) == 1
    
    removed = event_bus.off("removal_test", handler_id)
    assert removed is True
    assert len(event_bus.get_handlers("removal_test")) == 0

def test_event_history(event_bus):
    """イベント履歴テスト"""
    event_bus.emit("history_test_1", {"data": "first"})
    event_bus.emit("history_test_2", {"data": "second"})
    
    history = event_bus.get_event_history()
    assert len(history) == 2
    assert history[0].name == "history_test_1"
    assert history[1].name == "history_test_2"
    
    # 制限付き履歴取得
    limited_history = event_bus.get_event_history(limit=1)
    assert len(limited_history) == 1
    assert limited_history[0].name == "history_test_2"

def test_middleware(event_bus):
    """ミドルウェアテスト"""
    middleware_calls = []
    
    def test_middleware(event):
        middleware_calls.append(event.name)
    
    event_bus.add_middleware(test_middleware)
    event_bus.emit("middleware_test", {"data": "test"})
    
    assert len(middleware_calls) == 1
    assert middleware_calls[0] == "middleware_test"

def test_error_handling(event_bus):
    """エラーハンドリングテスト"""
    def error_handler(event):
        raise ValueError("Test error")
    
    def normal_handler(event):
        event.data["handled"] = True
    
    event_bus.on("error_test", error_handler)
    event_bus.on("error_test", normal_handler)
    
    # エラーが発生してもイベント処理は継続される
    event = event_bus.emit("error_test", {})
    assert event.data.get("handled") is True

def test_event_creation():
    """イベントオブジェクト作成テスト"""
    event = Event(
        name="test_event",
        data={"key": "value"},
        timestamp=datetime.now(),
        event_id="test-id",
        priority=EventPriority.HIGH,
        source="test_source",
        target="test_target"
    )
    
    assert event.name == "test_event"
    assert event.data["key"] == "value"
    assert event.priority == EventPriority.HIGH
    assert event.source == "test_source"
    assert event.target == "test_target"

def test_handlers_clearing(event_bus):
    """ハンドラークリアテスト"""
    def handler1(event):
        pass
    
    def handler2(event):
        pass
    
    event_bus.on("clear_test", handler1)
    event_bus.on("other_event", handler2)
    
    # 特定イベントのハンドラーをクリア
    event_bus.clear_handlers("clear_test")
    assert len(event_bus.get_handlers("clear_test")) == 0
    assert len(event_bus.get_handlers("other_event")) == 1
    
    # 全ハンドラーをクリア
    event_bus.clear_handlers()
    assert len(event_bus.get_handlers("other_event")) == 0
