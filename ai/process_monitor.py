"""
AIプロセス監視システム

このモジュールは、AIの処理状況の可視化とステータス管理を行うための
監視システムを提供します。
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import uuid
import json

logger = logging.getLogger(__name__)

class ProcessStatus(str, Enum):
    """AIプロセスステータスの列挙型"""
    WAITING = "waiting"      # 実行待ち
    RUNNING = "running"      # 実行中
    COMPLETED = "completed"  # 正常完了
    FAILED = "failed"        # エラー発生
    CANCELED = "canceled"    # キャンセル済み
    TIMEOUT = "timeout"      # タイムアウト
    PAUSED = "paused"        # 一時停止


@dataclass
class ProcessInfo:
    """AIプロセス情報を格納するデータクラス"""
    process_id: str
    process_type: str  # 'llm_generation', 'rag_search', 'orchestration' など
    status: ProcessStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    progress: float = 0.0  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    parent_process_id: Optional[str] = None
    child_processes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "process_id": self.process_id,
            "process_type": self.process_type,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "progress": self.progress,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "parent_process_id": self.parent_process_id,
            "child_processes": self.child_processes,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessInfo':
        """辞書形式からオブジェクトを生成"""
        # 日時文字列をdatetimeに変換
        start_time = datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        
        return cls(
            process_id=data["process_id"],
            process_type=data["process_type"],
            status=ProcessStatus(data["status"]),
            start_time=start_time,
            end_time=end_time,
            progress=data.get("progress", 0.0),
            metadata=data.get("metadata", {}),
            error_message=data.get("error_message"),
            parent_process_id=data.get("parent_process_id"),
            child_processes=data.get("child_processes", [])
        )


class AIProcessMonitor:
    """
    AIプロセス監視システム
    - AIの処理状況をリアルタイムに追跡
    - 処理時間、ステータス、階層関係を管理
    - イベント通知によるステータス変更の監視
    - タイムアウト検出と自動クリーンアップ
    """
    
    def __init__(self, 
                 cleanup_interval_seconds: int = 300, 
                 process_timeout_seconds: int = 600,
                 max_history_count: int = 1000):
        """
        初期化
        
        Args:
            cleanup_interval_seconds: クリーンアップ間隔（秒）
            process_timeout_seconds: プロセスのタイムアウト時間（秒）
            max_history_count: 履歴に保持する最大プロセス数
        """
        # 現在監視中のプロセス
        self.active_processes: Dict[str, ProcessInfo] = {}
        
        # 完了したプロセスの履歴
        self.process_history: List[ProcessInfo] = []
        
        # 監視設定
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.process_timeout_seconds = process_timeout_seconds
        self.max_history_count = max_history_count
        
        # イベントハンドラー
        self.event_handlers: Dict[str, List[Callable[[ProcessInfo], None]]] = {
            "started": [],
            "progress": [],
            "completed": [],
            "failed": [],
            "timeout": [],
            "canceled": []
        }
          # 統計情報
        self.stats = {
            "total_processes": 0,
            "completed_processes": 0,
            "failed_processes": 0,
            "timed_out_processes": 0,
            "avg_process_time_seconds": 0,
            "active_processes": 0,
            
            # 拡張統計情報
            "max_process_time_seconds": 0,
            "min_process_time_seconds": float('inf'),
            "total_tokens_generated": 0,
            "total_tokens_input": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_24h_processes": 0,
            "last_24h_success_rate": 0.0
        }
        
        # パフォーマンス履歴
        self.performance_history = {
            "durations": [],  # 直近100件の処理時間
            "timestamps": [],  # 直近100件の処理完了時刻
            "process_types": {}  # プロセスタイプ別の統計
        }
        
        # ロック
        self._lock = asyncio.Lock()
        
        # クリーンアップタスク
        self._cleanup_task = None
        self._running = False
        
        logger.info(f"AIプロセス監視システムを初期化: クリーンアップ間隔={cleanup_interval_seconds}s, "
                   f"タイムアウト={process_timeout_seconds}s")

    async def start(self) -> None:
        """監視システムを開始"""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("AIプロセス監視システム開始")

    async def stop(self) -> None:
        """監視システムを停止"""
        if not self._running:
            return
            
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("AIプロセス監視システム停止")

    async def register_process(self, 
                              process_type: str, 
                              metadata: Dict[str, Any] = None,
                              parent_process_id: str = None) -> str:
        """
        新しいプロセスを登録
        
        Args:
            process_type: プロセスタイプ
            metadata: プロセスに関連するメタデータ
            parent_process_id: 親プロセスID
            
        Returns:
            str: 生成されたプロセスID
        """
        # プロセスIDの生成
        process_id = str(uuid.uuid4())
        
        # プロセス情報の作成
        process_info = ProcessInfo(
            process_id=process_id,
            process_type=process_type,
            status=ProcessStatus.WAITING,
            start_time=datetime.now(),
            metadata=metadata or {},
            parent_process_id=parent_process_id
        )
        
        # 親プロセスが指定されている場合は親に子プロセスとして登録
        if parent_process_id and parent_process_id in self.active_processes:
            async with self._lock:
                parent = self.active_processes[parent_process_id]
                parent.child_processes.append(process_id)
        
        # アクティブプロセスに追加
        async with self._lock:
            self.active_processes[process_id] = process_info
            self.stats["total_processes"] += 1
            self.stats["active_processes"] += 1
        
        logger.debug(f"プロセス登録: {process_id} ({process_type})")
        return process_id

    async def start_process(self, process_id: str) -> None:
        """プロセスの開始をマーク"""
        async with self._lock:
            if process_id not in self.active_processes:
                logger.warning(f"存在しないプロセスID: {process_id}")
                return
                
            process = self.active_processes[process_id]
            process.status = ProcessStatus.RUNNING
            process.start_time = datetime.now()
            
            # イベントを発行
            await self._emit_event("started", process)
            
        logger.debug(f"プロセス開始: {process_id}")

    async def update_progress(self, process_id: str, progress: float, 
                             metadata_update: Dict[str, Any] = None) -> None:
        """
        プロセスの進捗を更新
        
        Args:
            process_id: プロセスID
            progress: 進捗（0.0-1.0）
            metadata_update: 更新するメタデータ
        """
        async with self._lock:
            if process_id not in self.active_processes:
                logger.warning(f"存在しないプロセスID: {process_id}")
                return
                
            process = self.active_processes[process_id]
            
            # 進捗の更新
            process.progress = max(0.0, min(1.0, progress))
            
            # メタデータの更新
            if metadata_update:
                process.metadata.update(metadata_update)
                
            # イベントを発行
            await self._emit_event("progress", process)
            
        logger.debug(f"プロセス進捗更新: {process_id}, 進捗: {progress:.2f}")
        
    async def complete_process(self, process_id: str, 
                              metadata_update: Dict[str, Any] = None) -> None:
        """
        プロセスの完了をマーク
        
        Args:
            process_id: プロセスID
            metadata_update: 完了時に追加するメタデータ
        """
        async with self._lock:
            if process_id not in self.active_processes:
                logger.warning(f"存在しないプロセスID: {process_id}")
                return
                
            process = self.active_processes[process_id]
            
            # 状態の更新
            process.status = ProcessStatus.COMPLETED
            process.end_time = datetime.now()
            process.progress = 1.0
            
            # メタデータの更新
            if metadata_update:
                process.metadata.update(metadata_update)
                
                # キャッシュヒット統計の更新
                if metadata_update.get("cache_hit") is True:
                    self.stats["cache_hits"] += 1
                elif metadata_update.get("cache_hit") is False:
                    self.stats["cache_misses"] += 1
                
                # トークン統計の更新
                if "total_tokens" in metadata_update:
                    self.stats["total_tokens_generated"] += metadata_update.get("total_tokens", 0)
                if "input_tokens" in metadata_update:
                    self.stats["total_tokens_input"] += metadata_update.get("input_tokens", 0)
            
            # 処理時間の計算と記録
            if process.start_time:
                duration_seconds = (process.end_time - process.start_time).total_seconds()
                
                # パフォーマンス履歴に追加
                self.performance_history["durations"].append(duration_seconds)
                self.performance_history["timestamps"].append(process.end_time.timestamp())
                
                # 最大100件に制限
                if len(self.performance_history["durations"]) > 100:
                    self.performance_history["durations"].pop(0)
                    self.performance_history["timestamps"].pop(0)
                
                # プロセスタイプ別の統計
                process_type = process.process_type
                if process_type not in self.performance_history["process_types"]:
                    self.performance_history["process_types"][process_type] = {
                        "count": 0,
                        "total_time": 0,
                        "avg_time": 0,
                        "max_time": 0,
                        "min_time": float('inf')
                    }
                    
                type_stats = self.performance_history["process_types"][process_type]
                type_stats["count"] += 1
                type_stats["total_time"] += duration_seconds
                type_stats["avg_time"] = type_stats["total_time"] / type_stats["count"]
                type_stats["max_time"] = max(type_stats["max_time"], duration_seconds)
                type_stats["min_time"] = min(type_stats["min_time"], duration_seconds)
                
            # 統計情報の更新
            self.stats["completed_processes"] += 1
            self.stats["active_processes"] -= 1
            
            # 履歴に追加
            self._add_to_history(process)
            
            # アクティブリストから削除
            del self.active_processes[process_id]
            
            # イベントを発行
            await self._emit_event("completed", process)
            
            # 平均処理時間の更新と24時間統計の更新
            self._update_avg_process_time()
            self._update_24h_stats()
            
        logger.debug(f"プロセス完了: {process_id}")

    async def fail_process(self, process_id: str, error_message: str,
                          metadata_update: Dict[str, Any] = None) -> None:
        """
        プロセスの失敗をマーク
        
        Args:
            process_id: プロセスID
            error_message: エラーメッセージ
            metadata_update: 失敗時に追加するメタデータ
        """
        async with self._lock:
            if process_id not in self.active_processes:
                logger.warning(f"存在しないプロセスID: {process_id}")
                return
                
            process = self.active_processes[process_id]
            
            # 状態の更新
            process.status = ProcessStatus.FAILED
            process.end_time = datetime.now()
            process.error_message = error_message
            
            # メタデータの更新
            if metadata_update:
                process.metadata.update(metadata_update)
                
            # 統計情報の更新
            self.stats["failed_processes"] += 1
            self.stats["active_processes"] -= 1
            
            # 履歴に追加
            self._add_to_history(process)
            
            # アクティブリストから削除
            del self.active_processes[process_id]
            
            # イベントを発行
            await self._emit_event("failed", process)
            
        logger.debug(f"プロセス失敗: {process_id}, エラー: {error_message}")

    async def cancel_process(self, process_id: str) -> None:
        """プロセスのキャンセルをマーク"""
        async with self._lock:
            if process_id not in self.active_processes:
                logger.warning(f"存在しないプロセスID: {process_id}")
                return
                
            process = self.active_processes[process_id]
            
            # 状態の更新
            process.status = ProcessStatus.CANCELED
            process.end_time = datetime.now()
            
            # 統計情報の更新
            self.stats["active_processes"] -= 1
            
            # 履歴に追加
            self._add_to_history(process)
            
            # アクティブリストから削除
            del self.active_processes[process_id]
            
            # イベントを発行
            await self._emit_event("canceled", process)
            
        logger.debug(f"プロセスキャンセル: {process_id}")

    async def get_process_info(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        プロセス情報を取得
        
        Args:
            process_id: プロセスID
            
        Returns:
            Optional[Dict[str, Any]]: プロセス情報（辞書形式）または None
        """
        if process_id in self.active_processes:
            return self.active_processes[process_id].to_dict()
            
        # 履歴から検索
        for process in self.process_history:
            if process.process_id == process_id:
                return process.to_dict()
                
        return None

    async def get_active_processes(self) -> List[Dict[str, Any]]:
        """
        現在アクティブな全プロセス情報を取得
        
        Returns:
            List[Dict[str, Any]]: アクティブプロセスのリスト（辞書形式）
        """
        return [process.to_dict() for process in self.active_processes.values()]

    async def get_process_history(self, 
                                 limit: int = 100, 
                                 process_type: str = None,
                                 status: str = None) -> List[Dict[str, Any]]:
        """
        プロセス履歴を取得（フィルタ付き）
        
        Args:
            limit: 取得する最大件数
            process_type: フィルタするプロセスタイプ
            status: フィルタするステータス
            
        Returns:
            List[Dict[str, Any]]: プロセス履歴リスト（辞書形式）
        """
        filtered_history = self.process_history
        
        # プロセスタイプでフィルタ
        if process_type:
            filtered_history = [p for p in filtered_history if p.process_type == process_type]
            
        # ステータスでフィルタ
        if status:
            filtered_history = [p for p in filtered_history if p.status.value == status]
            
        # 最新順にソート
        filtered_history.sort(key=lambda p: p.end_time, reverse=True)
        
        # 指定された件数に制限
        filtered_history = filtered_history[:limit]
        
        return [process.to_dict() for process in filtered_history]

    async def get_stats(self) -> Dict[str, Any]:
        """
        監視システムの統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        async with self._lock:
            # 最新の統計を作成
            active_process_types = {}
            for process in self.active_processes.values():
                process_type = process.process_type
                active_process_types[process_type] = active_process_types.get(process_type, 0) + 1
            
            # 追加の統計計算
            success_rate = 0
            if self.stats["completed_processes"] + self.stats["failed_processes"] > 0:
                success_rate = self.stats["completed_processes"] / (
                    self.stats["completed_processes"] + self.stats["failed_processes"]
                )
            
            return {
                "total_processes": self.stats["total_processes"],
                "completed_processes": self.stats["completed_processes"],
                "failed_processes": self.stats["failed_processes"],
                "timed_out_processes": self.stats["timed_out_processes"],
                "active_processes": self.stats["active_processes"],
                "active_process_types": active_process_types,
                "avg_process_time_seconds": self.stats["avg_process_time_seconds"],
                "success_rate": success_rate,
                "history_size": len(self.process_history)
            }

    def add_event_handler(self, event_type: str, handler: Callable[[ProcessInfo], None]) -> None:
        """
        イベントハンドラを追加
        
        Args:
            event_type: イベントタイプ ("started", "progress", "completed", "failed", "timeout", "canceled")
            handler: イベントハンドラ関数
        """
        if event_type not in self.event_handlers:
            logger.warning(f"未知のイベントタイプ: {event_type}")
            return
            
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable[[ProcessInfo], None]) -> None:
        """イベントハンドラを削除"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)

    async def _emit_event(self, event_type: str, process: ProcessInfo) -> None:
        """イベントを発行"""
        if event_type not in self.event_handlers:
            return
            
        for handler in self.event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(process)
                else:
                    handler(process)
            except Exception as e:
                logger.error(f"イベントハンドラエラー ({event_type}): {e}")

    async def _cleanup_loop(self) -> None:
        """定期的なクリーンアップを行うループ"""
        while self._running:
            try:
                await self._cleanup_timed_out_processes()
                await self._trim_history()
                
                # 次のクリーンアップまで待機
                await asyncio.sleep(self.cleanup_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"クリーンアップエラー: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def _cleanup_timed_out_processes(self) -> None:
        """タイムアウトしたプロセスを検出して処理"""
        now = datetime.now()
        timed_out_processes = []
        
        async with self._lock:
            for process_id, process in list(self.active_processes.items()):
                # 実行中プロセスのみチェック
                if process.status != ProcessStatus.RUNNING:
                    continue
                    
                # タイムアウト判定
                elapsed_time = now - process.start_time
                if elapsed_time.total_seconds() > self.process_timeout_seconds:
                    # タイムアウト検出
                    process.status = ProcessStatus.TIMEOUT
                    process.end_time = now
                    process.error_message = f"プロセスがタイムアウトしました ({self.process_timeout_seconds}秒)"
                    
                    # 統計更新
                    self.stats["timed_out_processes"] += 1
                    self.stats["active_processes"] -= 1
                    
                    # 履歴に追加
                    self._add_to_history(process)
                    
                    # タイムアウト処理リストに追加
                    timed_out_processes.append(process)
                    
                    # アクティブプロセスから削除
                    del self.active_processes[process_id]
        
        # タイムアウトイベント発行（ロック外で実行）
        for process in timed_out_processes:
            logger.warning(f"プロセスタイムアウト: {process.process_id} ({process.process_type})")
            await self._emit_event("timeout", process)

    async def _trim_history(self) -> None:
        """履歴サイズを制限に合わせてトリミング"""
        if len(self.process_history) <= self.max_history_count:
            return
            
        async with self._lock:
            # 古い順にソート
            self.process_history.sort(key=lambda p: p.end_time)
            
            # 超過分を削除
            excess = len(self.process_history) - self.max_history_count
            if excess > 0:
                self.process_history = self.process_history[excess:]

    def _add_to_history(self, process: ProcessInfo) -> None:
        """履歴にプロセスを追加（コピーを作成）"""
        self.process_history.append(process)
        
        # サイズ制限チェック（即時トリミング）
        if len(self.process_history) > self.max_history_count * 1.1:  # 10%のバッファ
            # 古い順にソート
            self.process_history.sort(key=lambda p: p.end_time)
            
            # 超過分を削除            excess = len(self.process_history) - self.max_history_count
            if excess > 0:
                self.process_history = self.process_history[excess:]
                
    def _update_avg_process_time(self) -> None:
        """平均処理時間を更新"""
        if not self.process_history:
            return
            
        # 成功したプロセスの処理時間を計算
        completed_processes = [p for p in self.process_history 
                              if p.status == ProcessStatus.COMPLETED and p.end_time and p.start_time]
                              
        if not completed_processes:
            return
            
        # 処理時間を計算
        process_times = [(p.end_time - p.start_time).total_seconds() for p in completed_processes]
        
        if process_times:
            self.stats["avg_process_time_seconds"] = sum(process_times) / len(process_times)
            
            # 最大・最小処理時間も更新
            self.stats["max_process_time_seconds"] = max(process_times + [self.stats["max_process_time_seconds"]])
            self.stats["min_process_time_seconds"] = min([t for t in process_times if t > 0] + 
                                                        [self.stats["min_process_time_seconds"]] 
                                                        if self.stats["min_process_time_seconds"] < float('inf') 
                                                        else process_times)
    
    def _update_24h_stats(self) -> None:
        """24時間統計情報を更新"""
        try:
            # 現在時刻からの24時間前のタイムスタンプ
            now = datetime.now().timestamp()
            day_ago = now - (24 * 60 * 60)  # 24時間 = 86400秒
            
            # 直近24時間のプロセス数カウント
            recent_timestamps = [ts for ts in self.performance_history["timestamps"] if ts > day_ago]
            self.stats["last_24h_processes"] = len(recent_timestamps)
            
            # 直近24時間の履歴から成功率を計算
            if recent_timestamps:
                recent_processes = []
                
                # 24時間以内のプロセスを履歴から取得
                for process in self.process_history:
                    if process.end_time and process.end_time.timestamp() > day_ago:
                        recent_processes.append(process)
                
                # 成功と失敗をカウント
                success_count = len([p for p in recent_processes if p.status == ProcessStatus.COMPLETED])
                failed_count = len([p for p in recent_processes if p.status == ProcessStatus.FAILED])
                
                # 成功率を計算
                if success_count + failed_count > 0:
                    self.stats["last_24h_success_rate"] = success_count / (success_count + failed_count)
                else:
                    self.stats["last_24h_success_rate"] = 0.0
        
        except Exception as e:
            logger.error(f"24時間統計の更新エラー: {e}")


# デフォルトインスタンス
default_process_monitor = None

async def get_process_monitor(cleanup_interval_seconds: int = 300,
                             process_timeout_seconds: int = 600,
                             max_history_count: int = 1000) -> AIProcessMonitor:
    """
    デフォルトのプロセス監視システムを取得または初期化
    
    Args:
        cleanup_interval_seconds: クリーンアップ間隔（秒）
        process_timeout_seconds: プロセスのタイムアウト時間（秒）
        max_history_count: 履歴に保持する最大プロセス数
        
    Returns:
        AIProcessMonitor: プロセス監視システムインスタンス
    """
    global default_process_monitor
    
    if default_process_monitor is None:
        default_process_monitor = AIProcessMonitor(
            cleanup_interval_seconds=cleanup_interval_seconds,
            process_timeout_seconds=process_timeout_seconds,
            max_history_count=max_history_count
        )
        await default_process_monitor.start()
    
    return default_process_monitor
