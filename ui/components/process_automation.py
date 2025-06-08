"""
Task 4-7: 高度な統合機能 - Process Integration & Automation System
プロセス統合・自動化システムの実装

機能:
- 統合タスク実行エンジン
- インテリジェント監視システム
- 自動回復機能
- パフォーマンス最適化
"""

import asyncio
import json
import threading
import time
import subprocess
import psutil
import queue
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from enum import Enum
import concurrent.futures

class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    """タスク優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class MonitoringLevel(Enum):
    """監視レベル"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

@dataclass
class TaskDefinition:
    """タスク定義"""
    task_id: str
    name: str
    command: Union[str, List[str]]
    working_directory: str = ""
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: int = 300  # 5分
    retry_count: int = 3
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    cleanup_commands: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskExecution:
    """タスク実行状況"""
    task_id: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    process_id: Optional[int] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    retry_attempt: int = 0
    error_message: str = ""

@dataclass
class SystemMetrics:
    """システムメトリクス"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    process_count: int
    load_average: float

class ProcessMonitor:
    """プロセス監視システム"""
    
    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED):
        self.monitoring_level = monitoring_level
        self.monitored_processes: Dict[int, Dict] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage': 90.0
        }
        
        self.monitoring_active = True
        self.monitoring_interval = 5.0  # 5秒間隔
        
        # 監視スレッド
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # アラートコールバック
        self.alert_callback: Optional[Callable] = None
    
    def register_process(self, pid: int, task_id: str, metadata: Dict = None):
        """プロセス登録"""
        try:
            process = psutil.Process(pid)
            self.monitored_processes[pid] = {
                'task_id': task_id,
                'process': process,
                'start_time': datetime.now(),
                'metadata': metadata or {},
                'resource_history': []
            }
            logging.info(f"プロセス {pid} ({task_id}) を監視対象に追加")
        except psutil.NoSuchProcess:
            logging.error(f"プロセス {pid} が見つかりません")
    
    def unregister_process(self, pid: int):
        """プロセス登録解除"""
        if pid in self.monitored_processes:
            del self.monitored_processes[pid]
            logging.info(f"プロセス {pid} の監視を停止")
    
    def get_process_metrics(self, pid: int) -> Optional[Dict[str, Any]]:
        """プロセスメトリクス取得"""
        if pid not in self.monitored_processes:
            return None
        
        try:
            process_info = self.monitored_processes[pid]
            process = process_info['process']
            
            metrics = {
                'pid': pid,
                'task_id': process_info['task_id'],
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'memory_percent': process.memory_percent(),
                'status': process.status(),
                'create_time': process.create_time(),
                'num_threads': process.num_threads(),
                'timestamp': datetime.now()
            }
            
            if self.monitoring_level == MonitoringLevel.COMPREHENSIVE:
                metrics.update({
                    'io_counters': process.io_counters()._asdict() if hasattr(process, 'io_counters') else {},
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                    'connections': len(process.connections()) if hasattr(process, 'connections') else 0
                })
            
            return metrics
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logging.warning(f"プロセス {pid} のメトリクス取得失敗: {e}")
            return None
    
    def get_system_metrics(self) -> SystemMetrics:
        """システムメトリクス取得"""
        memory = psutil.virtual_memory()
        disk_usage = {}
        
        try:
            # ディスク使用量（主要なパーティションのみ）
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = (usage.used / usage.total) * 100
                except (PermissionError, OSError):
                    continue
        except Exception:
            disk_usage = {}
        
        try:
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            }
        except Exception:
            network_io = {}
        
        try:
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        except Exception:
            load_avg = 0.0
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=memory.percent,
            memory_available=memory.available,
            disk_usage=disk_usage,
            network_io=network_io,
            process_count=len(psutil.pids()),
            load_average=load_avg
        )
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # システムメトリクス収集
                system_metrics = self.get_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # 履歴の制限（直近1時間分のみ保持）
                cutoff_time = datetime.now() - timedelta(hours=1)
                self.system_metrics_history = [
                    m for m in self.system_metrics_history 
                    if m.timestamp > cutoff_time
                ]
                
                # プロセスメトリクス収集
                for pid in list(self.monitored_processes.keys()):
                    metrics = self.get_process_metrics(pid)
                    if metrics:
                        self.monitored_processes[pid]['resource_history'].append(metrics)
                    else:
                        # プロセスが終了した場合は監視から除外
                        self.unregister_process(pid)
                
                # アラートチェック
                self._check_alerts(system_metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logging.error(f"監視ループエラー: {e}")
                time.sleep(10)
    
    def _check_alerts(self, metrics: SystemMetrics):
        """アラートチェック"""
        alerts = []
        
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append(f"CPU使用率が高い: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append(f"メモリ使用率が高い: {metrics.memory_percent:.1f}%")
        
        for mount, usage in metrics.disk_usage.items():
            if usage > self.alert_thresholds['disk_usage']:
                alerts.append(f"ディスク使用率が高い ({mount}): {usage:.1f}%")
        
        if alerts and self.alert_callback:
            self.alert_callback(alerts)
    
    def set_alert_callback(self, callback: Callable):
        """アラートコールバック設定"""
        self.alert_callback = callback
    
    def shutdown(self):
        """監視停止"""
        self.monitoring_active = False
        logging.info("プロセス監視を停止しました")

class ErrorRecoverySystem:
    """エラー回復システム"""
    
    def __init__(self):
        self.recovery_strategies = self._load_recovery_strategies()
        self.recovery_history: List[Dict] = []
        
    def _load_recovery_strategies(self) -> Dict[str, Dict]:
        """回復戦略読み込み"""
        return {
            'timeout': {
                'action': 'terminate_and_retry',
                'max_retries': 3,
                'backoff_factor': 2.0
            },
            'resource_exhaustion': {
                'action': 'free_resources_and_retry',
                'max_retries': 2,
                'wait_time': 30
            },
            'dependency_failure': {
                'action': 'restart_dependencies',
                'max_retries': 2,
                'cascade_recovery': True
            },
            'permission_error': {
                'action': 'adjust_permissions',
                'max_retries': 1,
                'elevation_required': True
            },
            'network_error': {
                'action': 'retry_with_backoff',
                'max_retries': 5,
                'backoff_factor': 1.5
            }
        }
    
    def analyze_error(self, task_execution: TaskExecution) -> str:
        """エラー分析"""
        error_type = "unknown"
        
        if task_execution.exit_code == -15:  # SIGTERM
            error_type = "timeout"
        elif "Permission denied" in task_execution.stderr:
            error_type = "permission_error"
        elif "No space left on device" in task_execution.stderr:
            error_type = "resource_exhaustion"
        elif any(word in task_execution.stderr.lower() for word in ['network', 'connection', 'timeout']):
            error_type = "network_error"
        elif task_execution.exit_code != 0:
            error_type = "general_failure"
        
        return error_type
    
    def attempt_recovery(self, task_def: TaskDefinition, 
                        task_execution: TaskExecution,
                        error_type: str) -> bool:
        """回復試行"""
        if error_type not in self.recovery_strategies:
            logging.warning(f"未知のエラータイプ: {error_type}")
            return False
        
        strategy = self.recovery_strategies[error_type]
        
        # 回復試行記録
        recovery_record = {
            'task_id': task_def.task_id,
            'error_type': error_type,
            'strategy': strategy['action'],
            'timestamp': datetime.now(),
            'success': False
        }
        
        try:
            success = self._execute_recovery_action(
                strategy['action'], 
                task_def, 
                task_execution
            )
            
            recovery_record['success'] = success
            self.recovery_history.append(recovery_record)
            
            return success
            
        except Exception as e:
            logging.error(f"回復処理エラー: {e}")
            recovery_record['error'] = str(e)
            self.recovery_history.append(recovery_record)
            return False
    
    def _execute_recovery_action(self, action: str, 
                               task_def: TaskDefinition,
                               task_execution: TaskExecution) -> bool:
        """回復アクション実行"""
        if action == "terminate_and_retry":
            # プロセス強制終了
            if task_execution.process_id:
                try:
                    process = psutil.Process(task_execution.process_id)
                    process.terminate()
                    process.wait(timeout=10)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            return True
            
        elif action == "free_resources_and_retry":
            # リソース解放
            self._cleanup_resources()
            time.sleep(10)  # 少し待機
            return True
            
        elif action == "restart_dependencies":
            # 依存関係の再起動
            for dep in task_def.dependencies:
                logging.info(f"依存関係 {dep} の再起動を試行")
                # 実際の依存関係再起動ロジックは実装に依存
            return True
            
        elif action == "adjust_permissions":
            # 権限調整
            if task_def.working_directory:
                try:
                    # 作業ディレクトリの権限確認・調整
                    path = Path(task_def.working_directory)
                    if path.exists():
                        # 権限チェック
                        return path.is_dir() and os.access(path, os.R_OK | os.W_OK)
                except Exception:
                    pass
            return False
            
        elif action == "retry_with_backoff":
            # バックオフ付きリトライ
            wait_time = 2 ** task_execution.retry_attempt
            time.sleep(min(wait_time, 60))  # 最大60秒
            return True
        
        return False
    
    def _cleanup_resources(self):
        """リソースクリーンアップ"""
        try:
            # 一時ファイル削除
            import tempfile
            import shutil
            temp_dir = Path(tempfile.gettempdir())
            
            # 古い一時ファイルを削除（1日以上前）
            cutoff = time.time() - 86400  # 24時間
            for temp_file in temp_dir.glob("tmp*"):
                try:
                    if temp_file.stat().st_mtime < cutoff:
                        if temp_file.is_file():
                            temp_file.unlink()
                        elif temp_file.is_dir():
                            shutil.rmtree(temp_file)
                except Exception:
                    continue
                    
        except Exception as e:
            logging.warning(f"リソースクリーンアップエラー: {e}")

class TaskExecutor:
    """タスク実行エンジン"""
    
    def __init__(self, max_concurrent_tasks: int = 4):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: Dict[str, TaskExecution] = {}
        
        # コンポーネント
        self.monitor = ProcessMonitor()
        self.recovery_system = ErrorRecoverySystem()
        
        # 実行制御
        self.executor_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_tasks
        )
        self.execution_active = True
        
        # 実行スレッド
        self.execution_thread = threading.Thread(target=self._execution_loop)
        self.execution_thread.daemon = True
        self.execution_thread.start()
        
        # コールバック
        self.task_update_callback: Optional[Callable] = None
        self.voice_feedback_callback: Optional[Callable] = None
    
    def set_callbacks(self, task_update: Callable = None, voice_feedback: Callable = None):
        """コールバック設定"""
        self.task_update_callback = task_update
        self.voice_feedback_callback = voice_feedback
    
    def submit_task(self, task_def: TaskDefinition) -> str:
        """タスク提出"""
        # 優先度キューに追加（優先度が高いほど小さな数値）
        priority = 5 - task_def.priority.value  # HIGH=3 -> priority=2
        self.task_queue.put((priority, time.time(), task_def))
        
        # 実行状況初期化
        execution = TaskExecution(
            task_id=task_def.task_id,
            status=TaskStatus.PENDING
        )
        self.active_tasks[task_def.task_id] = execution
        
        logging.info(f"タスク {task_def.task_id} をキューに追加")
        
        if self.voice_feedback_callback:
            self.voice_feedback_callback(f"タスク {task_def.name} をキューに追加しました")
        
        return task_def.task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """タスクキャンセル"""
        if task_id in self.active_tasks:
            execution = self.active_tasks[task_id]
            
            if execution.status == TaskStatus.RUNNING:
                # 実行中のタスクを停止
                if execution.process_id:
                    try:
                        process = psutil.Process(execution.process_id)
                        process.terminate()
                        process.wait(timeout=10)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        try:
                            process.kill()
                        except psutil.NoSuchProcess:
                            pass
            
            execution.status = TaskStatus.CANCELLED
            execution.end_time = datetime.now()
            
            # 完了タスクに移動
            self.completed_tasks[task_id] = execution
            del self.active_tasks[task_id]
            
            logging.info(f"タスク {task_id} をキャンセルしました")
            return True
        
        return False
    
    def get_task_status(self, task_id: str) -> Optional[TaskExecution]:
        """タスクステータス取得"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        return None
    
    def get_active_tasks(self) -> List[TaskExecution]:
        """アクティブタスク一覧"""
        return list(self.active_tasks.values())
    
    def _execution_loop(self):
        """実行ループ"""
        while self.execution_active:
            try:
                # キューからタスク取得（1秒でタイムアウト）
                try:
                    priority, timestamp, task_def = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 並行実行数チェック
                running_count = sum(
                    1 for exec in self.active_tasks.values() 
                    if exec.status == TaskStatus.RUNNING
                )
                
                if running_count >= self.max_concurrent_tasks:
                    # キューに戻す
                    self.task_queue.put((priority, timestamp, task_def))
                    time.sleep(1)
                    continue
                
                # タスク実行
                future = self.executor_pool.submit(self._execute_task, task_def)
                
            except Exception as e:
                logging.error(f"実行ループエラー: {e}")
                time.sleep(5)
    
    def _execute_task(self, task_def: TaskDefinition):
        """タスク実行"""
        execution = self.active_tasks.get(task_def.task_id)
        if not execution:
            return
        
        execution.status = TaskStatus.RUNNING
        execution.start_time = datetime.now()
        
        if self.task_update_callback:
            self.task_update_callback(task_def.task_id, execution)
        
        try:
            # 依存関係チェック
            if not self._check_dependencies(task_def):
                execution.status = TaskStatus.FAILED
                execution.error_message = "依存関係が満たされていません"
                execution.end_time = datetime.now()
                return
            
            # コマンド実行
            self._run_command(task_def, execution)
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            logging.error(f"タスク {task_def.task_id} 実行エラー: {e}")
        
        finally:
            # 完了処理
            if execution.status == TaskStatus.RUNNING:
                execution.status = TaskStatus.COMPLETED
            
            execution.end_time = datetime.now()
            
            # 監視解除
            if execution.process_id:
                self.monitor.unregister_process(execution.process_id)
            
            # 完了タスクに移動
            self.completed_tasks[task_def.task_id] = execution
            if task_def.task_id in self.active_tasks:
                del self.active_tasks[task_def.task_id]
            
            if self.task_update_callback:
                self.task_update_callback(task_def.task_id, execution)
            
            # エラー回復処理
            if execution.status == TaskStatus.FAILED and execution.retry_attempt < task_def.retry_count:
                error_type = self.recovery_system.analyze_error(execution)
                if self.recovery_system.attempt_recovery(task_def, execution, error_type):
                    # リトライ
                    execution.retry_attempt += 1
                    self.submit_task(task_def)
    
    def _check_dependencies(self, task_def: TaskDefinition) -> bool:
        """依存関係チェック"""
        for dep_id in task_def.dependencies:
            if dep_id in self.completed_tasks:
                dep_execution = self.completed_tasks[dep_id]
                if dep_execution.status != TaskStatus.COMPLETED:
                    return False
            elif dep_id in self.active_tasks:
                # まだ完了していない
                return False
            else:
                # 存在しない依存関係
                return False
        return True
    
    def _run_command(self, task_def: TaskDefinition, execution: TaskExecution):
        """コマンド実行"""
        # 環境変数準備
        env = os.environ.copy()
        env.update(task_def.environment)
        
        # 作業ディレクトリ設定
        cwd = task_def.working_directory or None
        
        # コマンド実行
        if isinstance(task_def.command, str):
            cmd = task_def.command
            shell = True
        else:
            cmd = task_def.command
            shell = False
        
        process = subprocess.Popen(
            cmd,
            shell=shell,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        execution.process_id = process.pid
        
        # プロセス監視開始
        self.monitor.register_process(
            process.pid, 
            task_def.task_id,
            {'name': task_def.name}
        )
        
        try:
            # タイムアウト付き実行
            stdout, stderr = process.communicate(timeout=task_def.timeout)
            
            execution.exit_code = process.returncode
            execution.stdout = stdout
            execution.stderr = stderr
            
            # 成功基準チェック
            if task_def.success_criteria:
                if not self._check_success_criteria(task_def.success_criteria, execution):
                    execution.status = TaskStatus.FAILED
                    execution.error_message = "成功基準を満たしていません"
                    return
            
            if process.returncode == 0:
                execution.status = TaskStatus.COMPLETED
            else:
                execution.status = TaskStatus.FAILED
                execution.error_message = f"終了コード: {process.returncode}"
                
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            
            execution.exit_code = -15  # SIGTERM
            execution.stdout = stdout
            execution.stderr = stderr
            execution.status = TaskStatus.FAILED
            execution.error_message = "タイムアウト"
        
        finally:
            # クリーンアップコマンド実行
            for cleanup_cmd in task_def.cleanup_commands:
                try:
                    subprocess.run(cleanup_cmd, shell=True, cwd=cwd, timeout=30)
                except Exception as e:
                    logging.warning(f"クリーンアップエラー: {e}")
    
    def _check_success_criteria(self, criteria: Dict[str, Any], 
                              execution: TaskExecution) -> bool:
        """成功基準チェック"""
        if 'exit_code' in criteria:
            if execution.exit_code != criteria['exit_code']:
                return False
        
        if 'stdout_contains' in criteria:
            patterns = criteria['stdout_contains']
            if isinstance(patterns, str):
                patterns = [patterns]
            for pattern in patterns:
                if pattern not in execution.stdout:
                    return False
        
        if 'stderr_empty' in criteria and criteria['stderr_empty']:
            if execution.stderr.strip():
                return False
        
        return True
    
    def shutdown(self):
        """実行エンジン停止"""
        self.execution_active = False
        self.executor_pool.shutdown(wait=True)
        self.monitor.shutdown()
        logging.info("タスク実行エンジンを停止しました")

# テスト・デモ用関数
def demo_process_automation():
    """プロセス自動化デモ"""
    print("=== プロセス統合・自動化システム デモ ===")
    
    # システム初期化
    executor = TaskExecutor(max_concurrent_tasks=2)
    
    # コールバック設定
    def task_update(task_id, execution):
        print(f"📋 タスク更新: {task_id} -> {execution.status.value}")
    
    def voice_feedback(message):
        print(f"🔊 音声: {message}")
    
    executor.set_callbacks(task_update, voice_feedback)
    
    # サンプルタスク定義
    tasks = [
        TaskDefinition(
            task_id="task_1",
            name="Python環境チェック",
            command="python --version",
            timeout=10,
            priority=TaskPriority.HIGH
        ),
        TaskDefinition(
            task_id="task_2",
            name="ディスク容量チェック",
            command="df -h" if os.name != 'nt' else "dir",
            timeout=15,
            priority=TaskPriority.NORMAL,
            dependencies=["task_1"]
        ),
        TaskDefinition(
            task_id="task_3",
            name="長時間タスク（シミュレーション）",
            command="python -c \"import time; time.sleep(5); print('完了')\"",
            timeout=30,
            priority=TaskPriority.LOW
        )
    ]
    
    # タスク提出
    print("📤 タスクを提出中...")
    for task in tasks:
        task_id = executor.submit_task(task)
        print(f"  - {task.name} ({task_id})")
    
    # 実行監視
    print("\n⏳ 実行監視中...")
    start_time = time.time()
    
    while time.time() - start_time < 30:  # 30秒間監視
        active_tasks = executor.get_active_tasks()
        if not active_tasks:
            break
        
        print(f"  アクティブタスク数: {len(active_tasks)}")
        for task in active_tasks:
            if task.status == TaskStatus.RUNNING:
                print(f"    - {task.task_id}: 実行中 (PID: {task.process_id})")
        
        time.sleep(2)
    
    # 結果表示
    print("\n📊 実行結果:")
    for task_id in ["task_1", "task_2", "task_3"]:
        execution = executor.get_task_status(task_id)
        if execution:
            duration = ""
            if execution.start_time and execution.end_time:
                delta = execution.end_time - execution.start_time
                duration = f" ({delta.total_seconds():.1f}秒)"
            
            print(f"  - {task_id}: {execution.status.value}{duration}")
            if execution.exit_code is not None:
                print(f"    終了コード: {execution.exit_code}")
            if execution.error_message:
                print(f"    エラー: {execution.error_message}")
    
    executor.shutdown()

if __name__ == "__main__":
    import os
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # デモ実行
    demo_process_automation()
