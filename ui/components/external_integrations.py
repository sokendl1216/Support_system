"""
Task 4-7: 高度な統合機能 - External System Integrations
外部システム統合機能の実装

機能:
- API連携管理
- データ同期システム
- 認証統合
- 通知統合
- クラウド・オフライン対応
"""

import asyncio
import json
import threading
import time
import requests
import sqlite3
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from enum import Enum
from urllib.parse import urljoin, urlparse
import base64
import jwt

class IntegrationType(Enum):
    """統合タイプ"""
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    DATABASE = "database"
    FILE_SYNC = "file_sync"
    CLOUD_STORAGE = "cloud_storage"
    NOTIFICATION = "notification"

class AuthType(Enum):
    """認証タイプ"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    JWT = "jwt"

class SyncStatus(Enum):
    """同期ステータス"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    CONFLICT = "conflict"

@dataclass
class ExternalSystem:
    """外部システム定義"""
    system_id: str
    name: str
    integration_type: IntegrationType
    endpoint_url: str
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit: int = 100  # リクエスト/分
    timeout: int = 30
    retry_count: int = 3
    enabled: bool = True

@dataclass
class SyncConfiguration:
    """同期設定"""
    sync_id: str
    system_id: str
    sync_type: str  # "pull", "push", "bidirectional"
    schedule: str  # cron形式
    source_path: str
    destination_path: str
    filters: List[str] = field(default_factory=list)
    conflict_resolution: str = "newer_wins"  # "newer_wins", "manual", "source_wins"
    enabled: bool = True

@dataclass
class SyncRecord:
    """同期記録"""
    sync_id: str
    timestamp: datetime
    status: SyncStatus
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

class APIClient:
    """API連携クライアント"""
    
    def __init__(self, system: ExternalSystem):
        self.system = system
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(system.rate_limit)
        self._setup_authentication()
        self._setup_headers()
    
    def _setup_authentication(self):
        """認証設定"""
        if self.system.auth_type == AuthType.API_KEY:
            # APIキー認証
            if 'header_name' in self.system.auth_config:
                header_name = self.system.auth_config['header_name']
                api_key = self.system.auth_config['api_key']
                self.session.headers[header_name] = api_key
            else:
                self.session.params['api_key'] = self.system.auth_config['api_key']
                
        elif self.system.auth_type == AuthType.BEARER_TOKEN:
            # Bearer Token認証
            token = self.system.auth_config['token']
            self.session.headers['Authorization'] = f'Bearer {token}'
            
        elif self.system.auth_type == AuthType.BASIC_AUTH:
            # Basic認証
            username = self.system.auth_config['username']
            password = self.system.auth_config['password']
            self.session.auth = (username, password)
            
        elif self.system.auth_type == AuthType.JWT:
            # JWT認証
            self._setup_jwt_auth()
    
    def _setup_jwt_auth(self):
        """JWT認証設定"""
        try:
            secret = self.system.auth_config['secret']
            payload = {
                'iss': self.system.auth_config.get('issuer', 'support_system'),
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            
            if 'user_id' in self.system.auth_config:
                payload['sub'] = self.system.auth_config['user_id']
            
            token = jwt.encode(payload, secret, algorithm='HS256')
            self.session.headers['Authorization'] = f'Bearer {token}'
            
        except Exception as e:
            logging.error(f"JWT認証設定エラー: {e}")
    
    def _setup_headers(self):
        """ヘッダー設定"""
        self.session.headers.update(self.system.headers)
        if 'User-Agent' not in self.session.headers:
            self.session.headers['User-Agent'] = 'SupportSystem/1.0'
    
    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """API リクエスト"""
        await self.rate_limiter.acquire()
        
        url = urljoin(self.system.endpoint_url, endpoint)
        
        for attempt in range(self.system.retry_count + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.system.timeout,
                    **kwargs
                )
                
                if response.status_code == 429:  # Rate Limited
                    wait_time = int(response.headers.get('Retry-After', 60))
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                if response.headers.get('content-type', '').startswith('application/json'):
                    return response.json()
                else:
                    return {'content': response.text, 'status_code': response.status_code}
                    
            except requests.exceptions.RequestException as e:
                if attempt == self.system.retry_count:
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
        
        raise Exception("最大リトライ回数に達しました")
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET リクエスト"""
        return await self.request('GET', endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST リクエスト"""
        return await self.request('POST', endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PUT リクエスト"""
        return await self.request('PUT', endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE リクエスト"""
        return await self.request('DELETE', endpoint, **kwargs)

class RateLimiter:
    """レート制限器"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """リクエスト許可取得"""
        async with self.lock:
            now = datetime.now()
            # 1分前より古いリクエストを削除
            cutoff = now - timedelta(minutes=1)
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            if len(self.requests) >= self.requests_per_minute:
                # 待機時間計算
                oldest_request = min(self.requests)
                wait_time = 60 - (now - oldest_request).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self.requests.append(now)

class DataSynchronizer:
    """データ同期システム"""
    
    def __init__(self, db_path: str = "sync_data.db"):
        self.db_path = db_path
        self.sync_records: List[SyncRecord] = []
        self._init_database()
        
        # 同期スケジューラ
        self.scheduler_active = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # コールバック
        self.sync_callback: Optional[Callable] = None
    
    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_items (
                    item_id TEXT PRIMARY KEY,
                    sync_id TEXT,
                    source_path TEXT,
                    destination_path TEXT,
                    content_hash TEXT,
                    last_modified TIMESTAMP,
                    sync_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    sync_id TEXT,
                    item_id TEXT,
                    source_version TEXT,
                    destination_version TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
    
    def add_sync_configuration(self, config: SyncConfiguration):
        """同期設定追加"""
        # 設定をデータベースに保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO sync_configurations 
                (sync_id, system_id, sync_type, schedule, source_path, destination_path, filters, conflict_resolution, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.sync_id, config.system_id, config.sync_type,
                config.schedule, config.source_path, config.destination_path,
                json.dumps(config.filters), config.conflict_resolution, config.enabled
            ))
    
    async def sync_data(self, sync_config: SyncConfiguration, 
                       api_client: APIClient) -> SyncRecord:
        """データ同期実行"""
        record = SyncRecord(
            sync_id=sync_config.sync_id,
            timestamp=datetime.now(),
            status=SyncStatus.SYNCING
        )
        
        try:
            if sync_config.sync_type == "pull":
                await self._pull_data(sync_config, api_client, record)
            elif sync_config.sync_type == "push":
                await self._push_data(sync_config, api_client, record)
            elif sync_config.sync_type == "bidirectional":
                await self._bidirectional_sync(sync_config, api_client, record)
            
            record.status = SyncStatus.SUCCESS
            
        except Exception as e:
            record.status = SyncStatus.ERROR
            record.error_message = str(e)
            logging.error(f"同期エラー ({sync_config.sync_id}): {e}")
        
        # 記録保存
        self.sync_records.append(record)
        if self.sync_callback:
            self.sync_callback(record)
        
        return record
    
    async def _pull_data(self, config: SyncConfiguration, 
                        api_client: APIClient, record: SyncRecord):
        """データプル"""
        # リモートデータ取得
        remote_data = await api_client.get(config.source_path)
        
        if isinstance(remote_data, dict) and 'items' in remote_data:
            items = remote_data['items']
        elif isinstance(remote_data, list):
            items = remote_data
        else:
            items = [remote_data]
        
        record.items_processed = len(items)
        
        for item in items:
            try:
                # フィルター適用
                if self._apply_filters(item, config.filters):
                    await self._save_local_item(item, config, record)
                    record.items_successful += 1
                
            except Exception as e:
                record.items_failed += 1
                logging.warning(f"アイテム同期失敗: {e}")
    
    async def _push_data(self, config: SyncConfiguration,
                        api_client: APIClient, record: SyncRecord):
        """データプッシュ"""
        # ローカルデータ取得
        local_items = self._get_local_items(config)
        record.items_processed = len(local_items)
        
        for item in local_items:
            try:
                # リモートに送信
                await api_client.post(config.destination_path, json=item)
                record.items_successful += 1
                
            except Exception as e:
                record.items_failed += 1
                logging.warning(f"アイテムプッシュ失敗: {e}")
    
    async def _bidirectional_sync(self, config: SyncConfiguration,
                                 api_client: APIClient, record: SyncRecord):
        """双方向同期"""
        # リモートとローカルのデータを比較
        remote_data = await api_client.get(config.source_path)
        local_items = self._get_local_items(config)
        
        # コンフリクト検出・解決
        conflicts = self._detect_conflicts(remote_data, local_items, config)
        
        for conflict in conflicts:
            resolved_item = self._resolve_conflict(conflict, config.conflict_resolution)
            if resolved_item:
                await self._save_local_item(resolved_item, config, record)
    
    def _apply_filters(self, item: Dict, filters: List[str]) -> bool:
        """フィルター適用"""
        if not filters:
            return True
        
        # 簡単なフィルター実装（実際はより複雑になる）
        for filter_expr in filters:
            if '=' in filter_expr:
                key, value = filter_expr.split('=', 1)
                if item.get(key) != value:
                    return False
            elif filter_expr.startswith('!'):
                # 否定フィルター
                key = filter_expr[1:]
                if key in item:
                    return False
        
        return True
    
    def _get_local_items(self, config: SyncConfiguration) -> List[Dict]:
        """ローカルアイテム取得"""
        items = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT item_id, source_path, content_hash, last_modified
                FROM sync_items
                WHERE sync_id = ?
            ''', (config.sync_id,))
            
            for row in cursor.fetchall():
                items.append({
                    'id': row[0],
                    'path': row[1],
                    'hash': row[2],
                    'modified': row[3]
                })
        
        return items
    
    def _detect_conflicts(self, remote_data: Any, local_items: List[Dict],
                         config: SyncConfiguration) -> List[Dict]:
        """コンフリクト検出"""
        conflicts = []
        
        # 実装は具体的なデータ構造に依存
        # ここでは簡単な例を示す
        
        return conflicts
    
    def _resolve_conflict(self, conflict: Dict, resolution_strategy: str) -> Optional[Dict]:
        """コンフリクト解決"""
        if resolution_strategy == "newer_wins":
            # より新しいバージョンを選択
            source_time = conflict.get('source_modified', datetime.min)
            dest_time = conflict.get('destination_modified', datetime.min)
            
            if source_time > dest_time:
                return conflict['source_version']
            else:
                return conflict['destination_version']
        
        elif resolution_strategy == "source_wins":
            return conflict['source_version']
        
        elif resolution_strategy == "manual":
            # 手動解決が必要
            return None
        
        return None
    
    async def _save_local_item(self, item: Dict, config: SyncConfiguration,
                              record: SyncRecord):
        """ローカルアイテム保存"""
        # アイテムの内容ハッシュ計算
        content_str = json.dumps(item, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO sync_items
                (item_id, sync_id, source_path, destination_path, content_hash, last_modified, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('id', f"item_{int(time.time())}"),
                config.sync_id,
                config.source_path,
                config.destination_path,
                content_hash,
                datetime.now(),
                'synced'
            ))
    
    def _scheduler_loop(self):
        """スケジューラループ"""
        while self.scheduler_active:
            try:
                # 定期的に同期設定をチェック
                # 実際のcronスケジュール実装は省略
                time.sleep(60)  # 1分間隔でチェック
                
            except Exception as e:
                logging.error(f"スケジューラエラー: {e}")
                time.sleep(60)
    
    def shutdown(self):
        """同期システム停止"""
        self.scheduler_active = False

class NotificationIntegrator:
    """通知統合システム"""
    
    def __init__(self):
        self.notification_channels: Dict[str, ExternalSystem] = {}
        self.notification_queue: List[Dict] = []
        
        # 通知送信スレッド
        self.sender_active = True
        self.sender_thread = threading.Thread(target=self._sender_loop)
        self.sender_thread.daemon = True
        self.sender_thread.start()
    
    def add_channel(self, channel_id: str, system: ExternalSystem):
        """通知チャンネル追加"""
        self.notification_channels[channel_id] = system
        logging.info(f"通知チャンネル {channel_id} を追加")
    
    def send_notification(self, channel_id: str, title: str, message: str,
                         priority: str = "normal", metadata: Dict = None):
        """通知送信"""
        notification = {
            'channel_id': channel_id,
            'title': title,
            'message': message,
            'priority': priority,
            'metadata': metadata or {},
            'timestamp': datetime.now(),
            'retry_count': 0
        }
        
        self.notification_queue.append(notification)
    
    def _sender_loop(self):
        """通知送信ループ"""
        while self.sender_active:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    asyncio.run(self._send_single_notification(notification))
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"通知送信エラー: {e}")
                time.sleep(5)
    
    async def _send_single_notification(self, notification: Dict):
        """単一通知送信"""
        channel_id = notification['channel_id']
        
        if channel_id not in self.notification_channels:
            logging.error(f"通知チャンネル {channel_id} が見つかりません")
            return
        
        system = self.notification_channels[channel_id]
        client = APIClient(system)
        
        try:
            # 通知ペイロード作成
            payload = {
                'title': notification['title'],
                'message': notification['message'],
                'priority': notification['priority'],
                'timestamp': notification['timestamp'].isoformat()
            }
            payload.update(notification['metadata'])
            
            # 送信
            response = await client.post('/notifications', json=payload)
            logging.info(f"通知送信成功: {channel_id}")
            
        except Exception as e:
            notification['retry_count'] += 1
            
            if notification['retry_count'] < 3:
                # リトライキューに戻す
                self.notification_queue.append(notification)
            
            logging.error(f"通知送信失敗 ({channel_id}): {e}")
    
    def shutdown(self):
        """通知システム停止"""
        self.sender_active = False

class ExternalSystemIntegrator:
    """外部システム統合 メインクラス"""
    
    def __init__(self):
        self.systems: Dict[str, ExternalSystem] = {}
        self.api_clients: Dict[str, APIClient] = {}
        self.synchronizer = DataSynchronizer()
        self.notifier = NotificationIntegrator()
        
        # オフライン対応
        self.offline_mode = False
        self.offline_queue: List[Dict] = []
        
        # データファイル
        self.config_file = Path("external_systems.json")
        self._load_configuration()
        
        # ヘルスチェック
        self.health_check_active = True
        self.health_thread = threading.Thread(target=self._health_check_loop)
        self.health_thread.daemon = True
        self.health_thread.start()
        
        # コールバック
        self.status_callback: Optional[Callable] = None
    
    def register_system(self, system: ExternalSystem):
        """外部システム登録"""
        self.systems[system.system_id] = system
        
        if system.enabled:
            self.api_clients[system.system_id] = APIClient(system)
        
        logging.info(f"外部システム {system.name} を登録")
    
    def get_system(self, system_id: str) -> Optional[ExternalSystem]:
        """システム取得"""
        return self.systems.get(system_id)
    
    def enable_system(self, system_id: str):
        """システム有効化"""
        if system_id in self.systems:
            system = self.systems[system_id]
            system.enabled = True
            self.api_clients[system_id] = APIClient(system)
            logging.info(f"システム {system.name} を有効化")
    
    def disable_system(self, system_id: str):
        """システム無効化"""
        if system_id in self.systems:
            system = self.systems[system_id]
            system.enabled = False
            if system_id in self.api_clients:
                del self.api_clients[system_id]
            logging.info(f"システム {system.name} を無効化")
    
    async def api_call(self, system_id: str, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """API呼び出し"""
        if self.offline_mode:
            # オフラインキューに追加
            self.offline_queue.append({
                'system_id': system_id,
                'method': method,
                'endpoint': endpoint,
                'kwargs': kwargs,
                'timestamp': datetime.now()
            })
            raise Exception("オフラインモードです")
        
        if system_id not in self.api_clients:
            raise Exception(f"システム {system_id} が利用できません")
        
        client = self.api_clients[system_id]
        return await client.request(method, endpoint, **kwargs)
    
    def setup_sync(self, config: SyncConfiguration):
        """同期設定"""
        self.synchronizer.add_sync_configuration(config)
    
    async def sync_system(self, system_id: str, sync_id: str) -> SyncRecord:
        """システム同期"""
        if system_id not in self.api_clients:
            raise Exception(f"システム {system_id} が利用できません")
        
        # 同期設定取得（実装は省略）
        sync_config = SyncConfiguration(
            sync_id=sync_id,
            system_id=system_id,
            sync_type="pull",
            schedule="0 */1 * * *",  # 1時間毎
            source_path="/data",
            destination_path="local_data"
        )
        
        client = self.api_clients[system_id]
        return await self.synchronizer.sync_data(sync_config, client)
    
    def send_notification(self, channel_id: str, title: str, message: str,
                         priority: str = "normal"):
        """通知送信"""
        self.notifier.send_notification(channel_id, title, message, priority)
    
    def set_offline_mode(self, offline: bool):
        """オフラインモード設定"""
        self.offline_mode = offline
        logging.info(f"オフラインモード: {offline}")
        
        if not offline and self.offline_queue:
            # オンライン復帰時にキューを処理
            asyncio.create_task(self._process_offline_queue())
    
    async def _process_offline_queue(self):
        """オフラインキュー処理"""
        while self.offline_queue:
            item = self.offline_queue.pop(0)
            try:
                await self.api_call(
                    item['system_id'],
                    item['method'],
                    item['endpoint'],
                    **item['kwargs']
                )
            except Exception as e:
                logging.error(f"オフラインキュー処理エラー: {e}")
    
    def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.health_check_active:
            try:
                for system_id, client in self.api_clients.items():
                    # 簡単なヘルスチェック
                    try:
                        # 通常は専用のヘルスチェックエンドポイントを使用
                        asyncio.run(client.get('/health'))
                        
                        if self.status_callback:
                            self.status_callback(system_id, 'healthy')
                            
                    except Exception:
                        if self.status_callback:
                            self.status_callback(system_id, 'unhealthy')
                
                time.sleep(300)  # 5分間隔
                
            except Exception as e:
                logging.error(f"ヘルスチェックエラー: {e}")
                time.sleep(60)
    
    def _load_configuration(self):
        """設定読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for system_data in data.get('systems', []):
                    system = ExternalSystem(**system_data)
                    self.register_system(system)
                    
        except Exception as e:
            logging.error(f"設定読み込みエラー: {e}")
    
    def save_configuration(self):
        """設定保存"""
        try:
            data = {
                'systems': [asdict(system) for system in self.systems.values()],
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"設定保存エラー: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """統合ステータス取得"""
        return {
            'systems_count': len(self.systems),
            'active_systems': len(self.api_clients),
            'offline_mode': self.offline_mode,
            'offline_queue_size': len(self.offline_queue),
            'sync_records': len(self.synchronizer.sync_records),
            'notification_queue': len(self.notifier.notification_queue)
        }
    
    def shutdown(self):
        """統合システム停止"""
        self.health_check_active = False
        self.synchronizer.shutdown()
        self.notifier.shutdown()
        self.save_configuration()
        logging.info("外部システム統合を停止しました")

# テスト・デモ用関数
def demo_external_integrations():
    """外部システム統合デモ"""
    print("=== 外部システム統合 デモ ===")
    
    # システム初期化
    integrator = ExternalSystemIntegrator()
    
    # サンプルシステム登録
    github_system = ExternalSystem(
        system_id="github",
        name="GitHub API",
        integration_type=IntegrationType.REST_API,
        endpoint_url="https://api.github.com",
        auth_type=AuthType.BEARER_TOKEN,
        auth_config={'token': 'your_github_token'},
        rate_limit=60
    )
    
    slack_system = ExternalSystem(
        system_id="slack",
        name="Slack Webhook",
        integration_type=IntegrationType.WEBHOOK,
        endpoint_url="https://hooks.slack.com/services",
        auth_type=AuthType.NONE,
        rate_limit=1
    )
    
    integrator.register_system(github_system)
    integrator.register_system(slack_system)
    
    # 通知チャンネル設定
    integrator.notifier.add_channel("slack_general", slack_system)
    
    # 同期設定
    sync_config = SyncConfiguration(
        sync_id="github_repos",
        system_id="github",
        sync_type="pull",
        schedule="0 */6 * * *",  # 6時間毎
        source_path="/user/repos",
        destination_path="local_repos"
    )
    
    integrator.setup_sync(sync_config)
    
    # ステータス表示
    status = integrator.get_integration_status()
    print(f"📊 統合ステータス:")
    for key, value in status.items():
        print(f"  - {key}: {value}")
    
    # 通知送信テスト
    print("\n📢 通知送信テスト:")
    integrator.send_notification(
        "slack_general",
        "統合テスト",
        "外部システム統合が正常に動作しています",
        "normal"
    )
    print("  - Slack通知を送信しました")
    
    # オフラインモードテスト
    print("\n🔌 オフラインモードテスト:")
    integrator.set_offline_mode(True)
    print("  - オフラインモードに切り替えました")
    
    integrator.set_offline_mode(False)
    print("  - オンラインモードに復帰しました")
    
    integrator.shutdown()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # デモ実行
    demo_external_integrations()
