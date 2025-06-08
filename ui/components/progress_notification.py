"""
進行状態通知システム - プログレスコンポーネント

長時間処理の進捗表示・通知機能を提供します。
アクセシビリティに配慮した実装となっています。
"""

import streamlit as st
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """通知タイプ"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"

class ProgressStatus(str, Enum):
    """進行ステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

@dataclass
class ProgressInfo:
    """進捗情報"""
    process_id: str
    title: str
    description: str
    progress: float  # 0.0 - 1.0
    status: ProgressStatus
    current_step: str
    total_steps: int
    current_step_number: int
    estimated_remaining_time: Optional[float] = None
    start_time: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Notification:
    """通知情報"""
    id: str
    type: NotificationType
    title: str
    message: str
    timestamp: float
    process_id: Optional[str] = None
    auto_dismiss: bool = True
    dismiss_after: float = 5.0  # seconds
    actions: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.actions is None:
            self.actions = []

class ProgressNotificationSystem:
    """進行状態通知システム"""
    
    def __init__(self):
        self.active_processes: Dict[str, ProgressInfo] = {}
        self.notifications: List[Notification] = []
        self.notification_handlers: List[Callable] = []
        
        # Streamlit session stateの初期化
        if 'progress_system' not in st.session_state:
            st.session_state.progress_system = self
        
    def start_process(self, 
                     process_id: str,
                     title: str,
                     description: str,
                     total_steps: int = 100) -> ProgressInfo:
        """プロセス開始"""
        progress_info = ProgressInfo(
            process_id=process_id,
            title=title,
            description=description,
            progress=0.0,
            status=ProgressStatus.PENDING,
            current_step="開始中...",
            total_steps=total_steps,
            current_step_number=0,
            start_time=time.time()
        )
        
        self.active_processes[process_id] = progress_info
        
        # 開始通知
        self._add_notification(
            type=NotificationType.INFO,
            title="処理開始",
            message=f"{title}を開始しました",
            process_id=process_id
        )
        
        logger.info(f"プロセス開始: {process_id} - {title}")
        return progress_info
    
    def update_progress(self,
                       process_id: str,
                       progress: float,
                       current_step: str,
                       step_number: Optional[int] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """進捗更新"""
        if process_id not in self.active_processes:
            logger.warning(f"存在しないプロセスID: {process_id}")
            return False
        
        process_info = self.active_processes[process_id]
        process_info.progress = max(0.0, min(1.0, progress))
        process_info.current_step = current_step
        process_info.status = ProgressStatus.RUNNING
        
        if step_number is not None:
            process_info.current_step_number = step_number
        
        if metadata:
            process_info.metadata.update(metadata)
        
        # 残り時間推定
        if process_info.start_time and progress > 0:
            elapsed = time.time() - process_info.start_time
            estimated_total = elapsed / progress
            process_info.estimated_remaining_time = estimated_total - elapsed
        
        logger.debug(f"進捗更新: {process_id} - {progress:.1%}")
        return True
    
    def complete_process(self,
                        process_id: str,
                        final_message: str = "完了しました",
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """プロセス完了"""
        if process_id not in self.active_processes:
            logger.warning(f"存在しないプロセスID: {process_id}")
            return False
        
        process_info = self.active_processes[process_id]
        process_info.progress = 1.0
        process_info.status = ProgressStatus.COMPLETED
        process_info.current_step = final_message
        
        if metadata:
            process_info.metadata.update(metadata)
        
        # 完了通知
        self._add_notification(
            type=NotificationType.SUCCESS,
            title="処理完了",
            message=f"{process_info.title}が完了しました",
            process_id=process_id
        )
        
        logger.info(f"プロセス完了: {process_id}")
        return True
    
    def fail_process(self,
                    process_id: str,
                    error_message: str,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """プロセスエラー"""
        if process_id not in self.active_processes:
            logger.warning(f"存在しないプロセスID: {process_id}")
            return False
        
        process_info = self.active_processes[process_id]
        process_info.status = ProgressStatus.ERROR
        process_info.current_step = f"エラー: {error_message}"
        
        if metadata:
            process_info.metadata.update(metadata)
        
        # エラー通知
        self._add_notification(
            type=NotificationType.ERROR,
            title="処理エラー",
            message=f"{process_info.title}でエラーが発生しました: {error_message}",
            process_id=process_id,
            auto_dismiss=False  # エラーは手動で閉じる
        )
        
        logger.error(f"プロセスエラー: {process_id} - {error_message}")
        return True
    
    def cancel_process(self, process_id: str) -> bool:
        """プロセスキャンセル"""
        if process_id not in self.active_processes:
            logger.warning(f"存在しないプロセスID: {process_id}")
            return False
        
        process_info = self.active_processes[process_id]
        process_info.status = ProgressStatus.CANCELLED
        process_info.current_step = "キャンセルされました"
        
        # キャンセル通知
        self._add_notification(
            type=NotificationType.WARNING,
            title="処理キャンセル",
            message=f"{process_info.title}がキャンセルされました",
            process_id=process_id
        )
        
        logger.info(f"プロセスキャンセル: {process_id}")
        return True
    
    def get_process_info(self, process_id: str) -> Optional[ProgressInfo]:
        """プロセス情報取得"""
        return self.active_processes.get(process_id)
    
    def get_active_processes(self) -> List[ProgressInfo]:
        """アクティブプロセス一覧取得"""
        return [
            process for process in self.active_processes.values()
            if process.status in [ProgressStatus.PENDING, ProgressStatus.RUNNING]
        ]
    
    def cleanup_completed_processes(self, max_age_seconds: float = 300):
        """完了プロセスのクリーンアップ"""
        current_time = time.time()
        to_remove = []
        
        for process_id, process_info in self.active_processes.items():
            if (process_info.status in [ProgressStatus.COMPLETED, ProgressStatus.ERROR, ProgressStatus.CANCELLED] and
                process_info.start_time and 
                current_time - process_info.start_time > max_age_seconds):
                to_remove.append(process_id)
        
        for process_id in to_remove:
            del self.active_processes[process_id]
            logger.debug(f"完了プロセスをクリーンアップ: {process_id}")
    
    def _add_notification(self,
                         type: NotificationType,
                         title: str,
                         message: str,
                         process_id: Optional[str] = None,
                         auto_dismiss: bool = True,
                         actions: Optional[List[Dict[str, Any]]] = None) -> str:
        """通知追加"""
        notification_id = f"notif_{int(time.time() * 1000)}"
        
        notification = Notification(
            id=notification_id,
            type=type,
            title=title,
            message=message,
            timestamp=time.time(),
            process_id=process_id,
            auto_dismiss=auto_dismiss,
            actions=actions or []
        )
        
        self.notifications.append(notification)
        
        # ハンドラーに通知
        for handler in self.notification_handlers:
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"通知ハンドラーエラー: {e}")
        
        return notification_id
    
    def dismiss_notification(self, notification_id: str) -> bool:
        """通知を削除"""
        for i, notification in enumerate(self.notifications):
            if notification.id == notification_id:
                del self.notifications[i]
                return True
        return False
    
    def get_recent_notifications(self, max_count: int = 10) -> List[Notification]:
        """最近の通知を取得"""
        return self.notifications[-max_count:]
    
    def cleanup_old_notifications(self, max_age_seconds: float = 60):
        """古い通知のクリーンアップ"""
        current_time = time.time()
        self.notifications = [
            notif for notif in self.notifications
            if current_time - notif.timestamp <= max_age_seconds
        ]
    
    def add_notification_handler(self, handler: Callable):
        """通知ハンドラー追加"""
        self.notification_handlers.append(handler)

# グローバルインスタンス
if 'global_progress_system' not in st.session_state:
    st.session_state.global_progress_system = ProgressNotificationSystem()

def get_progress_system() -> ProgressNotificationSystem:
    """進行状態通知システムのインスタンスを取得"""
    return st.session_state.global_progress_system
