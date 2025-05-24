# Enhanced event bus implementation with async support

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """イベント優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    """イベントデータクラス"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    event_id: str
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None
    target: Optional[str] = None

@dataclass
class EventHandler:
    """イベントハンドラー情報"""
    handler: Callable
    priority: EventPriority
    is_async: bool
    handler_id: str

class EventBus:
    """Enhanced event bus with async support and priority handling"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._middleware: List[Callable] = []
        
    def on(self, event_name: str, handler: Callable, priority: EventPriority = EventPriority.NORMAL) -> str:
        """イベントハンドラーを登録"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        handler_id = str(uuid.uuid4())
        is_async = asyncio.iscoroutinefunction(handler)
        
        event_handler = EventHandler(
            handler=handler,
            priority=priority,
            is_async=is_async,
            handler_id=handler_id
        )
        
        self._handlers[event_name].append(event_handler)
        # 優先度順にソート（高い優先度が先）
        self._handlers[event_name].sort(key=lambda h: h.priority.value, reverse=True)
        
        logger.debug(f"Handler registered for event '{event_name}' with priority {priority.name}")
        return handler_id
    
    def off(self, event_name: str, handler_id: str) -> bool:
        """イベントハンドラーを削除"""
        if event_name not in self._handlers:
            return False
        
        original_count = len(self._handlers[event_name])
        self._handlers[event_name] = [h for h in self._handlers[event_name] if h.handler_id != handler_id]
        
        return len(self._handlers[event_name]) < original_count
    
    def emit(self, event_name: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Event:
        """同期イベント発火"""
        event = self._create_event(event_name, data, **kwargs)
        self._add_to_history(event)
        
        # ミドルウェア実行
        for middleware in self._middleware:
            try:
                middleware(event)
            except Exception as e:
                logger.error(f"Middleware error: {e}")
        
        # ハンドラー実行
        handlers = self._handlers.get(event_name, [])
        for handler_info in handlers:
            try:
                if handler_info.is_async:
                    # 非同期ハンドラーは同期的に実行しない
                    logger.warning(f"Async handler skipped in sync emit: {handler_info.handler_id}")
                else:
                    handler_info.handler(event)
            except Exception as e:
                logger.error(f"Handler error in '{event_name}': {e}")
        
        return event
    
    async def emit_async(self, event_name: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Event:
        """非同期イベント発火"""
        event = self._create_event(event_name, data, **kwargs)
        self._add_to_history(event)
        
        # ミドルウェア実行
        for middleware in self._middleware:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    await middleware(event)
                else:
                    middleware(event)
            except Exception as e:
                logger.error(f"Middleware error: {e}")
        
        # ハンドラー実行
        handlers = self._handlers.get(event_name, [])
        tasks = []
        
        for handler_info in handlers:
            try:
                if handler_info.is_async:
                    tasks.append(handler_info.handler(event))
                else:
                    handler_info.handler(event)
            except Exception as e:
                logger.error(f"Handler error in '{event_name}': {e}")
        
        # 非同期タスクを並行実行
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return event
    
    def _create_event(self, event_name: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Event:
        """イベントオブジェクトを作成"""
        event_data = data or {}
        event_data.update(kwargs)
        
        return Event(
            name=event_name,
            data=event_data,
            timestamp=datetime.now(),
            event_id=str(uuid.uuid4()),
            priority=event_data.get('priority', EventPriority.NORMAL),
            source=event_data.get('source'),
            target=event_data.get('target')
        )
    
    def _add_to_history(self, event: Event):
        """イベント履歴に追加"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def add_middleware(self, middleware: Callable):
        """ミドルウェアを追加"""
        self._middleware.append(middleware)
    
    def get_event_history(self, limit: Optional[int] = None) -> List[Event]:
        """イベント履歴を取得"""
        if limit:
            return self._event_history[-limit:]
        return self._event_history.copy()
    
    def get_handlers(self, event_name: str) -> List[EventHandler]:
        """イベントのハンドラー一覧を取得"""
        return self._handlers.get(event_name, []).copy()
    
    def clear_handlers(self, event_name: Optional[str] = None):
        """ハンドラーをクリア"""
        if event_name:
            self._handlers[event_name] = []
        else:
            self._handlers.clear()

# グローバルイベントバスインスタンス
event_bus = EventBus()
