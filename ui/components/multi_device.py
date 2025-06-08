"""
Task 4-7: 高度な統合機能 - Multi-device Support System
マルチデバイス対応システムの実装

機能:
- デバイス間連携
- 設定・状態同期
- 継続作業機能
- クロスプラットフォーム対応
"""

import asyncio
import json
import threading
import time
import socket
import platform
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from enum import Enum
import hashlib
import zeroconf
from cryptography.fernet import Fernet
import qrcode
from io import BytesIO
import base64

class DeviceType(Enum):
    """デバイスタイプ"""
    DESKTOP = "desktop"
    LAPTOP = "laptop"
    TABLET = "tablet"
    MOBILE = "mobile"
    SERVER = "server"

class ConnectionStatus(Enum):
    """接続ステータス"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"

class SyncScope(Enum):
    """同期範囲"""
    SETTINGS = "settings"
    WORKSPACE = "workspace"
    HISTORY = "history"
    PREFERENCES = "preferences"
    FILES = "files"
    ALL = "all"

@dataclass
class DeviceInfo:
    """デバイス情報"""
    device_id: str
    device_name: str
    device_type: DeviceType
    platform: str
    version: str
    ip_address: str
    port: int
    capabilities: List[str] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)
    trust_level: int = 0  # 0=未知, 1=認識済み, 2=信頼済み
    encryption_key: Optional[str] = None

@dataclass
class WorkSession:
    """作業セッション"""
    session_id: str
    device_id: str
    application: str
    context: Dict[str, Any]
    start_time: datetime
    last_activity: datetime
    files: List[str] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

@dataclass
class SyncRequest:
    """同期リクエスト"""
    request_id: str
    source_device: str
    target_device: str
    scope: SyncScope
    data: Dict[str, Any]
    timestamp: datetime
    encrypted: bool = False

class DeviceDiscovery:
    """デバイス発見システム"""
    
    def __init__(self, device_info: DeviceInfo):
        self.device_info = device_info
        self.discovered_devices: Dict[str, DeviceInfo] = {}
        self.discovery_active = True
        
        # Zeroconf設定
        self.zeroconf = zeroconf.Zeroconf()
        self.service_type = "_supportdevice._tcp.local."
        
        # サービス登録
        self._register_service()
        
        # 発見スレッド
        self.discovery_thread = threading.Thread(target=self._discovery_loop)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        
        # コールバック
        self.device_found_callback: Optional[Callable] = None
        self.device_lost_callback: Optional[Callable] = None
    
    def _register_service(self):
        """サービス登録"""
        try:
            service_info = zeroconf.ServiceInfo(
                self.service_type,
                f"{self.device_info.device_name}.{self.service_type}",
                addresses=[socket.inet_aton(self.device_info.ip_address)],
                port=self.device_info.port,
                properties={
                    'device_id': self.device_info.device_id,
                    'device_type': self.device_info.device_type.value,
                    'platform': self.device_info.platform,
                    'version': self.device_info.version,
                    'capabilities': ','.join(self.device_info.capabilities)
                }
            )
            
            self.zeroconf.register_service(service_info)
            logging.info(f"デバイスサービスを登録: {self.device_info.device_name}")
            
        except Exception as e:
            logging.error(f"サービス登録エラー: {e}")
    
    def _discovery_loop(self):
        """発見ループ"""
        browser = zeroconf.ServiceBrowser(
            self.zeroconf, 
            self.service_type, 
            handlers=[self._on_service_state_change]
        )
        
        while self.discovery_active:
            try:
                # 定期的に古いデバイスをクリーンアップ
                self._cleanup_old_devices()
                time.sleep(30)
                
            except Exception as e:
                logging.error(f"発見ループエラー: {e}")
                time.sleep(5)
    
    def _on_service_state_change(self, zeroconf_instance, service_type, name, state_change):
        """サービス状態変更ハンドラ"""
        if state_change == zeroconf.ServiceStateChange.Added:
            self._on_service_added(zeroconf_instance, service_type, name)
        elif state_change == zeroconf.ServiceStateChange.Removed:
            self._on_service_removed(name)
    
    def _on_service_added(self, zeroconf_instance, service_type, name):
        """サービス追加ハンドラ"""
        try:
            info = zeroconf_instance.get_service_info(service_type, name)
            if info and info.properties:
                props = {k.decode(): v.decode() for k, v in info.properties.items()}
                
                device_id = props.get('device_id', '')
                
                # 自分自身は除外
                if device_id == self.device_info.device_id:
                    return
                
                device = DeviceInfo(
                    device_id=device_id,
                    device_name=name.split('.')[0],
                    device_type=DeviceType(props.get('device_type', 'desktop')),
                    platform=props.get('platform', 'unknown'),
                    version=props.get('version', '1.0'),
                    ip_address=socket.inet_ntoa(info.addresses[0]),
                    port=info.port,
                    capabilities=props.get('capabilities', '').split(',') if props.get('capabilities') else []
                )
                
                self.discovered_devices[device_id] = device
                logging.info(f"デバイス発見: {device.device_name} ({device.ip_address})")
                
                if self.device_found_callback:
                    self.device_found_callback(device)
                    
        except Exception as e:
            logging.error(f"サービス追加処理エラー: {e}")
    
    def _on_service_removed(self, name):
        """サービス削除ハンドラ"""
        device_name = name.split('.')[0]
        
        # 該当デバイスを検索
        device_to_remove = None
        for device_id, device in self.discovered_devices.items():
            if device.device_name == device_name:
                device_to_remove = device_id
                break
        
        if device_to_remove:
            device = self.discovered_devices.pop(device_to_remove)
            logging.info(f"デバイス削除: {device.device_name}")
            
            if self.device_lost_callback:
                self.device_lost_callback(device)
    
    def _cleanup_old_devices(self):
        """古いデバイスクリーンアップ"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        devices_to_remove = []
        
        for device_id, device in self.discovered_devices.items():
            if device.last_seen < cutoff_time:
                devices_to_remove.append(device_id)
        
        for device_id in devices_to_remove:
            device = self.discovered_devices.pop(device_id)
            if self.device_lost_callback:
                self.device_lost_callback(device)
    
    def get_discovered_devices(self) -> List[DeviceInfo]:
        """発見されたデバイス一覧"""
        return list(self.discovered_devices.values())
    
    def shutdown(self):
        """発見システム停止"""
        self.discovery_active = False
        self.zeroconf.close()

class DeviceConnection:
    """デバイス接続管理"""
    
    def __init__(self, device_info: DeviceInfo):
        self.device_info = device_info
        self.connections: Dict[str, Dict] = {}
        self.server_socket: Optional[socket.socket] = None
        
        # 暗号化
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # サーバー開始
        self._start_server()
    
    def _start_server(self):
        """サーバー開始"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.device_info.ip_address, self.device_info.port))
            self.server_socket.listen(5)
            
            # 接続受付スレッド
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            logging.info(f"デバイスサーバー開始: {self.device_info.ip_address}:{self.device_info.port}")
            
        except Exception as e:
            logging.error(f"サーバー開始エラー: {e}")
    
    def _accept_connections(self):
        """接続受付"""
        while self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                
                # 接続処理スレッド
                handler_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address)
                )
                handler_thread.daemon = True
                handler_thread.start()
                
            except Exception as e:
                if self.server_socket:  # ソケットが閉じられていない場合のみエラー
                    logging.error(f"接続受付エラー: {e}")
    
    def _handle_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """接続処理"""
        try:
            # ハンドシェイク
            handshake_data = self._receive_data(client_socket)
            if not self._verify_handshake(handshake_data):
                client_socket.close()
                return
            
            device_id = handshake_data.get('device_id', '')
            
            # 接続記録
            self.connections[device_id] = {
                'socket': client_socket,
                'address': address,
                'connected_at': datetime.now(),
                'last_activity': datetime.now()
            }
            
            logging.info(f"デバイス接続: {device_id} from {address[0]}")
            
            # メッセージ処理ループ
            while True:
                data = self._receive_data(client_socket)
                if not data:
                    break
                
                self._process_message(device_id, data)
                self.connections[device_id]['last_activity'] = datetime.now()
                
        except Exception as e:
            logging.error(f"接続処理エラー: {e}")
        finally:
            if device_id in self.connections:
                del self.connections[device_id]
            client_socket.close()
    
    def connect_to_device(self, target_device: DeviceInfo) -> bool:
        """デバイスに接続"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((target_device.ip_address, target_device.port))
            
            # ハンドシェイク送信
            handshake = {
                'device_id': self.device_info.device_id,
                'device_name': self.device_info.device_name,
                'timestamp': datetime.now().isoformat(),
                'encryption_key': base64.b64encode(self.encryption_key).decode()
            }
            
            self._send_data(client_socket, handshake)
            
            # 接続記録
            self.connections[target_device.device_id] = {
                'socket': client_socket,
                'address': (target_device.ip_address, target_device.port),
                'connected_at': datetime.now(),
                'last_activity': datetime.now()
            }
            
            logging.info(f"デバイス接続成功: {target_device.device_name}")
            return True
            
        except Exception as e:
            logging.error(f"デバイス接続エラー: {e}")
            return False
    
    def send_message(self, target_device_id: str, message: Dict[str, Any]) -> bool:
        """メッセージ送信"""
        if target_device_id not in self.connections:
            return False
        
        try:
            connection = self.connections[target_device_id]
            self._send_data(connection['socket'], message)
            connection['last_activity'] = datetime.now()
            return True
            
        except Exception as e:
            logging.error(f"メッセージ送信エラー: {e}")
            # 接続削除
            if target_device_id in self.connections:
                del self.connections[target_device_id]
            return False
    
    def _send_data(self, socket_obj: socket.socket, data: Dict[str, Any]):
        """データ送信"""
        json_data = json.dumps(data, default=str)
        encrypted_data = self.cipher_suite.encrypt(json_data.encode())
        
        # データ長を先に送信
        data_length = len(encrypted_data)
        socket_obj.sendall(data_length.to_bytes(4, byteorder='big'))
        socket_obj.sendall(encrypted_data)
    
    def _receive_data(self, socket_obj: socket.socket) -> Optional[Dict[str, Any]]:
        """データ受信"""
        try:
            # データ長受信
            length_bytes = socket_obj.recv(4)
            if len(length_bytes) != 4:
                return None
            
            data_length = int.from_bytes(length_bytes, byteorder='big')
            
            # データ受信
            encrypted_data = b''
            while len(encrypted_data) < data_length:
                chunk = socket_obj.recv(data_length - len(encrypted_data))
                if not chunk:
                    return None
                encrypted_data += chunk
            
            # 復号化
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logging.error(f"データ受信エラー: {e}")
            return None
    
    def _verify_handshake(self, handshake: Dict[str, Any]) -> bool:
        """ハンドシェイク検証"""
        required_fields = ['device_id', 'device_name', 'timestamp']
        return all(field in handshake for field in required_fields)
    
    def _process_message(self, device_id: str, message: Dict[str, Any]):
        """メッセージ処理"""
        message_type = message.get('type', '')
        
        if message_type == 'sync_request':
            self._handle_sync_request(device_id, message)
        elif message_type == 'ping':
            self._handle_ping(device_id, message)
        else:
            logging.warning(f"未知のメッセージタイプ: {message_type}")
    
    def _handle_sync_request(self, device_id: str, message: Dict[str, Any]):
        """同期リクエスト処理"""
        # 同期処理は後で実装
        response = {
            'type': 'sync_response',
            'request_id': message.get('request_id'),
            'status': 'received'
        }
        self.send_message(device_id, response)
    
    def _handle_ping(self, device_id: str, message: Dict[str, Any]):
        """Ping処理"""
        response = {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }
        self.send_message(device_id, response)
    
    def get_connected_devices(self) -> List[str]:
        """接続済みデバイス一覧"""
        return list(self.connections.keys())
    
    def disconnect_device(self, device_id: str):
        """デバイス切断"""
        if device_id in self.connections:
            connection = self.connections[device_id]
            connection['socket'].close()
            del self.connections[device_id]
            logging.info(f"デバイス切断: {device_id}")
    
    def shutdown(self):
        """接続管理停止"""
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        for device_id in list(self.connections.keys()):
            self.disconnect_device(device_id)

class SessionManager:
    """セッション管理システム"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.active_sessions: Dict[str, WorkSession] = {}
        self.session_history: List[WorkSession] = []
        
        # データベース
        self.db_path = "device_sessions.db"
        self._init_database()
        
        # セッション監視
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS work_sessions (
                    session_id TEXT PRIMARY KEY,
                    device_id TEXT,
                    application TEXT,
                    context TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    last_activity TIMESTAMP,
                    files TEXT,
                    state TEXT,
                    is_active BOOLEAN
                )
            ''')
    
    def start_session(self, application: str, context: Dict[str, Any] = None,
                     files: List[str] = None) -> str:
        """セッション開始"""
        session_id = str(uuid.uuid4())
        
        session = WorkSession(
            session_id=session_id,
            device_id=self.device_id,
            application=application,
            context=context or {},
            start_time=datetime.now(),
            last_activity=datetime.now(),
            files=files or [],
            state={}
        )
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        logging.info(f"セッション開始: {application} ({session_id})")
        return session_id
    
    def update_session(self, session_id: str, state: Dict[str, Any] = None,
                      files: List[str] = None):
        """セッション更新"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        
        if state:
            session.state.update(state)
        
        if files:
            session.files = files
        
        self._save_session(session)
        return True
    
    def end_session(self, session_id: str):
        """セッション終了"""
        if session_id in self.active_sessions:
            session = self.active_sessions.pop(session_id)
            session.is_active = False
            
            self.session_history.append(session)
            self._save_session(session)
            
            logging.info(f"セッション終了: {session.application} ({session_id})")
    
    def get_session(self, session_id: str) -> Optional[WorkSession]:
        """セッション取得"""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[WorkSession]:
        """アクティブセッション一覧"""
        return list(self.active_sessions.values())
    
    def get_transferable_sessions(self) -> List[WorkSession]:
        """転送可能セッション一覧"""
        # ファイルパスが存在し、状態が保存されているセッション
        transferable = []
        
        for session in self.active_sessions.values():
            if session.files and session.state:
                transferable.append(session)
        
        return transferable
    
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションエクスポート"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_data': asdict(session),
            'export_time': datetime.now().isoformat(),
            'device_id': self.device_id
        }
    
    def import_session(self, session_data: Dict[str, Any]) -> str:
        """セッションインポート"""
        session_dict = session_data['session_data']
        
        # 新しいセッションIDを生成
        new_session_id = str(uuid.uuid4())
        session_dict['session_id'] = new_session_id
        session_dict['device_id'] = self.device_id
        
        # 時刻フィールドを変換
        session_dict['start_time'] = datetime.fromisoformat(session_dict['start_time'])
        session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
        
        session = WorkSession(**session_dict)
        self.active_sessions[new_session_id] = session
        self._save_session(session)
        
        logging.info(f"セッションインポート: {session.application} ({new_session_id})")
        return new_session_id
    
    def _save_session(self, session: WorkSession):
        """セッション保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO work_sessions
                (session_id, device_id, application, context, start_time, end_time,
                 last_activity, files, state, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.device_id,
                session.application,
                json.dumps(session.context),
                session.start_time,
                None,  # end_time
                session.last_activity,
                json.dumps(session.files),
                json.dumps(session.state),
                session.is_active
            ))
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # 非アクティブセッションの検出
                cutoff_time = datetime.now() - timedelta(hours=1)
                inactive_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if session.last_activity < cutoff_time:
                        inactive_sessions.append(session_id)
                
                # 非アクティブセッションを履歴に移動
                for session_id in inactive_sessions:
                    self.end_session(session_id)
                
                time.sleep(300)  # 5分間隔
                
            except Exception as e:
                logging.error(f"セッション監視エラー: {e}")
                time.sleep(60)
    
    def shutdown(self):
        """セッション管理停止"""
        self.monitoring_active = False
        
        # アクティブセッションを終了
        for session_id in list(self.active_sessions.keys()):
            self.end_session(session_id)

class MultiDeviceSupport:
    """マルチデバイス対応 メインクラス"""
    
    def __init__(self):
        # デバイス情報初期化
        self.device_info = self._create_device_info()
        
        # コンポーネント初期化
        self.discovery = DeviceDiscovery(self.device_info)
        self.connection = DeviceConnection(self.device_info)
        self.session_manager = SessionManager(self.device_info.device_id)
        
        # 設定
        self.auto_discovery = True
        self.auto_sync = True
        self.trust_new_devices = False
        
        # コールバック設定
        self.discovery.device_found_callback = self._on_device_found
        self.discovery.device_lost_callback = self._on_device_lost
        
        # 同期データ
        self.sync_data: Dict[SyncScope, Dict] = {
            SyncScope.SETTINGS: {},
            SyncScope.WORKSPACE: {},
            SyncScope.HISTORY: {},
            SyncScope.PREFERENCES: {}
        }
        
        # イベントコールバック
        self.device_event_callback: Optional[Callable] = None
        self.sync_event_callback: Optional[Callable] = None
    
    def _create_device_info(self) -> DeviceInfo:
        """デバイス情報作成"""
        # デバイスID生成（MACアドレスベース）
        device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node()))
        
        # プラットフォーム判定
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            device_type = DeviceType.DESKTOP if "desktop" in platform.platform().lower() else DeviceType.LAPTOP
        elif system == "darwin":
            device_type = DeviceType.LAPTOP  # Mac
        elif system == "linux":
            device_type = DeviceType.DESKTOP
        else:
            device_type = DeviceType.DESKTOP
        
        # IP アドレス取得
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except Exception:
            ip_address = "127.0.0.1"
        
        return DeviceInfo(
            device_id=device_id,
            device_name=platform.node(),
            device_type=device_type,
            platform=f"{system} {platform.release()}",
            version="1.0.0",
            ip_address=ip_address,
            port=55555,
            capabilities=["sync", "voice", "accessibility", "automation"]
        )
    
    def _on_device_found(self, device: DeviceInfo):
        """デバイス発見ハンドラ"""
        logging.info(f"新しいデバイス: {device.device_name}")
        
        if self.device_event_callback:
            self.device_event_callback('device_found', device)
        
        # 自動接続（信頼済みデバイスのみ）
        if device.trust_level >= 2:
            self.connect_to_device(device.device_id)
    
    def _on_device_lost(self, device: DeviceInfo):
        """デバイス消失ハンドラ"""
        logging.info(f"デバイス消失: {device.device_name}")
        
        if self.device_event_callback:
            self.device_event_callback('device_lost', device)
    
    def get_discovered_devices(self) -> List[DeviceInfo]:
        """発見されたデバイス一覧"""
        return self.discovery.get_discovered_devices()
    
    def connect_to_device(self, device_id: str) -> bool:
        """デバイス接続"""
        devices = {d.device_id: d for d in self.get_discovered_devices()}
        
        if device_id not in devices:
            return False
        
        device = devices[device_id]
        return self.connection.connect_to_device(device)
    
    def disconnect_device(self, device_id: str):
        """デバイス切断"""
        self.connection.disconnect_device(device_id)
    
    def trust_device(self, device_id: str, trust_level: int = 2):
        """デバイス信頼設定"""
        devices = {d.device_id: d for d in self.get_discovered_devices()}
        
        if device_id in devices:
            devices[device_id].trust_level = trust_level
            logging.info(f"デバイス信頼レベル設定: {devices[device_id].device_name} -> {trust_level}")
    
    def start_work_session(self, application: str, context: Dict[str, Any] = None,
                          files: List[str] = None) -> str:
        """作業セッション開始"""
        return self.session_manager.start_session(application, context, files)
    
    def transfer_session(self, session_id: str, target_device_id: str) -> bool:
        """セッション転送"""
        session_data = self.session_manager.export_session(session_id)
        if not session_data:
            return False
        
        message = {
            'type': 'session_transfer',
            'session_data': session_data
        }
        
        return self.connection.send_message(target_device_id, message)
    
    def generate_pairing_qr(self) -> str:
        """ペアリングQRコード生成"""
        pairing_data = {
            'device_id': self.device_info.device_id,
            'device_name': self.device_info.device_name,
            'ip_address': self.device_info.ip_address,
            'port': self.device_info.port,
            'timestamp': datetime.now().isoformat()
        }
        
        # QRコード生成
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(pairing_data))
        qr.make(fit=True)
        
        # 画像をBase64エンコード
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def sync_with_device(self, target_device_id: str, scope: SyncScope = SyncScope.ALL) -> bool:
        """デバイス間同期"""
        sync_request = SyncRequest(
            request_id=str(uuid.uuid4()),
            source_device=self.device_info.device_id,
            target_device=target_device_id,
            scope=scope,
            data=self.sync_data.get(scope, {}),
            timestamp=datetime.now()
        )
        
        message = {
            'type': 'sync_request',
            'request_id': sync_request.request_id,
            'scope': scope.value,
            'data': sync_request.data
        }
        
        success = self.connection.send_message(target_device_id, message)
        
        if self.sync_event_callback:
            self.sync_event_callback('sync_requested', sync_request)
        
        return success
    
    def update_sync_data(self, scope: SyncScope, data: Dict[str, Any]):
        """同期データ更新"""
        self.sync_data[scope].update(data)
        
        # 自動同期
        if self.auto_sync:
            for device_id in self.connection.get_connected_devices():
                self.sync_with_device(device_id, scope)
    
    def get_device_status(self) -> Dict[str, Any]:
        """デバイスステータス取得"""
        return {
            'device_info': asdict(self.device_info),
            'discovered_devices': len(self.get_discovered_devices()),
            'connected_devices': len(self.connection.get_connected_devices()),
            'active_sessions': len(self.session_manager.get_active_sessions()),
            'auto_discovery': self.auto_discovery,
            'auto_sync': self.auto_sync
        }
    
    def shutdown(self):
        """マルチデバイス対応停止"""
        self.discovery.shutdown()
        self.connection.shutdown()
        self.session_manager.shutdown()
        logging.info("マルチデバイス対応を停止しました")

# テスト・デモ用関数
def demo_multi_device():
    """マルチデバイス対応デモ"""
    print("=== マルチデバイス対応システム デモ ===")
    
    # システム初期化
    multi_device = MultiDeviceSupport()
    
    # デバイス情報表示
    print(f"📱 デバイス情報:")
    print(f"  - ID: {multi_device.device_info.device_id}")
    print(f"  - 名前: {multi_device.device_info.device_name}")
    print(f"  - タイプ: {multi_device.device_info.device_type.value}")
    print(f"  - プラットフォーム: {multi_device.device_info.platform}")
    print(f"  - IPアドレス: {multi_device.device_info.ip_address}")
    
    # 作業セッション開始
    print("\n💼 作業セッション開始:")
    session_id = multi_device.start_work_session(
        "text_editor",
        {"file": "demo.py", "line": 42},
        ["demo.py", "config.json"]
    )
    print(f"  - セッションID: {session_id}")
    
    # セッション更新
    multi_device.session_manager.update_session(
        session_id,
        {"line": 45, "modified": True}
    )
    
    # QRコード生成
    print("\n🔗 ペアリングQRコード生成:")
    qr_data = multi_device.generate_pairing_qr()
    print(f"  - QRコードデータサイズ: {len(qr_data)} bytes")
    
    # 同期データ更新
    print("\n🔄 同期データ更新:")
    multi_device.update_sync_data(SyncScope.SETTINGS, {
        "theme": "dark",
        "font_size": 12,
        "auto_save": True
    })
    print("  - 設定データを更新しました")
    
    # ステータス表示
    print("\n📊 デバイスステータス:")
    status = multi_device.get_device_status()
    for key, value in status.items():
        if key != 'device_info':
            print(f"  - {key}: {value}")
    
    # 発見デバイス表示
    devices = multi_device.get_discovered_devices()
    print(f"\n🔍 発見されたデバイス: {len(devices)}台")
    for device in devices:
        print(f"  - {device.device_name} ({device.device_type.value})")
    
    # セッション一覧
    sessions = multi_device.session_manager.get_active_sessions()
    print(f"\n📋 アクティブセッション: {len(sessions)}個")
    for session in sessions:
        print(f"  - {session.application}: {len(session.files)}ファイル")
    
    # 短時間待機（発見システムのテスト）
    print("\n⏳ デバイス発見を5秒間テスト...")
    time.sleep(5)
    
    multi_device.shutdown()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # デモ実行
    demo_multi_device()
