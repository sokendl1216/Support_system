"""
AI処理キャッシュ機構

このモジュールは、AIの生成結果をローカルに保存・再利用することでレスポンスを向上させる
キャッシュ管理システムを提供します。
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class AICacheManager:
    """
    AI処理結果キャッシュマネージャー
    - クエリと設定に基づいたキャッシュキーの生成
    - 生成結果のキャッシュへの格納と取得
    - キャッシュの有効期限管理
    - キャッシュヒットとミスの統計
    """
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 3600 * 24, 
                 max_cache_size_mb: int = 500, enable_cache: bool = True,
                 use_priority: bool = False):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリパス。Noneの場合はデフォルトパスを使用
            ttl_seconds: キャッシュエントリの有効期限（秒）
            max_cache_size_mb: キャッシュの最大サイズ（MB）
            enable_cache: キャッシュ機能の有効化フラグ
            use_priority: 優先度ベースのキャッシュ管理を有効化
        """
        self.enable_cache = enable_cache
        
        if not enable_cache:
            logger.info("AIキャッシュ機構が無効化されています")
            return
            
        # キャッシュディレクトリの設定
        if cache_dir is None:
            base_dir = os.environ.get("AI_CACHE_DIR", os.path.join(os.path.expanduser("~"), ".ai_cache"))
            self.cache_dir = Path(base_dir)
        else:
            self.cache_dir = Path(cache_dir)
            
        # ディレクトリが存在しない場合は作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # キャッシュ設定
        self.ttl_seconds = ttl_seconds
        self.max_cache_size_mb = max_cache_size_mb
        self.use_priority = use_priority
        
        # 優先度管理用のインデックスファイル
        self.priority_index_file = self.cache_dir / "priority_index.json"
        self.priority_data = {
            "access_counts": {},  # キャッシュキー: アクセス回数
            "last_access": {},    # キャッシュキー: 最終アクセス時間
            "priorities": {}      # キャッシュキー: 優先度スコア
        }
        
        # 統計情報
        self.stats = {
            "hits": 0,
            "misses": 0,
            "entries": 0,
            "size_bytes": 0,
            "last_cleanup": datetime.now().timestamp(),
            "priority_hits": 0    # 優先度の高いキャッシュのヒット数
        }
        
        # ロック（スレッド/プロセス間の同期）
        self._lock = asyncio.Lock()
        
        logger.info(f"AIキャッシュ機構を初期化: {self.cache_dir}, TTL: {ttl_seconds}s, "
                   f"最大サイズ: {max_cache_size_mb}MB, 優先度管理: {use_priority}")
        
        # 優先度データの読み込み
        self._load_priority_data()
        
        # 初期統計情報を更新
        self._update_stats()
    
    def _load_priority_data(self):
        """優先度データの読み込み"""
        if not self.use_priority:
            return
            
        try:
            if self.priority_index_file.exists():
                with open(self.priority_index_file, 'r', encoding='utf-8') as f:
                    self.priority_data = json.load(f)
                logger.debug(f"優先度データを読み込みました: {len(self.priority_data.get('priorities', {}))}エントリ")
        except Exception as e:
            logger.error(f"優先度データの読み込みエラー: {e}")
            # デフォルト値にリセット
            self.priority_data = {
                "access_counts": {},
                "last_access": {},
                "priorities": {}
            }
    
    async def _save_priority_data(self):
        """優先度データの保存"""
        if not self.use_priority:
            return
            
        try:
            async with self._lock:
                with open(self.priority_index_file, 'w', encoding='utf-8') as f:
                    json.dump(self.priority_data, f, ensure_ascii=False)
                logger.debug(f"優先度データを保存しました: {len(self.priority_data.get('priorities', {}))}エントリ")
        except Exception as e:
            logger.error(f"優先度データの保存エラー: {e}")
    
    def _update_priority(self, cache_key: str):
        """キャッシュキーの優先度を更新"""
        if not self.use_priority:
            return
            
        # アクセスカウントの更新
        self.priority_data["access_counts"][cache_key] = self.priority_data["access_counts"].get(cache_key, 0) + 1
        
        # 最終アクセス時間の更新
        self.priority_data["last_access"][cache_key] = datetime.now().timestamp()
        
        # 優先度スコアの計算（アクセス回数と最終アクセス時間から算出）
        access_count = self.priority_data["access_counts"][cache_key]
        recency = datetime.now().timestamp() - self.priority_data["last_access"].get(cache_key, 0)
        recency_factor = max(0, 1 - (recency / (self.ttl_seconds * 2)))  # recencyを0-1の範囲に正規化
        
        # 基本的な優先度計算式: (アクセス回数の対数 * 0.7) + (近接度 * 0.3)
        priority_score = (min(10, max(1, (access_count ** 0.5))) * 0.7) + (recency_factor * 0.3)
        self.priority_data["priorities"][cache_key] = priority_score

    async def get_cache(self, key_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        キャッシュからデータを取得
        
        Args:
            key_data: キャッシュキーを生成するためのデータ
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (キャッシュヒットしたか, キャッシュデータ)
        """
        if not self.enable_cache:
            return False, None
            
        cache_key = self._generate_cache_key(key_data)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            if not cache_file.exists():
                self.stats["misses"] += 1
                return False, None
                
            # キャッシュファイルから読み込み
            async with self._lock:
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                
                # 優先度を更新
                if self.use_priority:
                    self._update_priority(cache_key)
                    # 一定回数の更新ごとに優先度データを保存
                    if self.stats["hits"] % 10 == 0:
                        await self._save_priority_data()
                
                # 有効期限をチェック
                if "timestamp" in cache_data:
                    elapsed_seconds = time.time() - cache_data["timestamp"]
                    if elapsed_seconds > self.ttl_seconds:
                        # 期限切れ: キャッシュミス
                        self.stats["misses"] += 1
                        return False, None
                        
                # キャッシュヒット
                self.stats["hits"] += 1
                
                # 優先度が高いエントリのヒットをカウント
                if self.use_priority and cache_key in self.priority_data["priorities"]:
                    if self.priority_data["priorities"][cache_key] > 5.0:  # 優先度高のしきい値
                        self.stats["priority_hits"] += 1
                
                return True, cache_data.get("data")
                
        except Exception as e:
            logger.error(f"キャッシュ取得エラー: {e}")
            self.stats["misses"] += 1
            return False, None

    async def set_cache(self, key_data: Dict[str, Any], data: Any) -> bool:
        """
        データをキャッシュに保存
        
        Args:
            key_data: キャッシュキーを生成するためのデータ
            data: 保存するデータ
            
        Returns:
            bool: 保存成功したか
        """
        if not self.enable_cache:
            return False
            
        # サイズチェック
        await self._check_cache_size()
            
        cache_key = self._generate_cache_key(key_data)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # キャッシュデータ構造
        cache_data = {
            "timestamp": time.time(),
            "key_data": key_data,
            "data": data
        }
        
        try:
            # JSONとして保存
            async with self._lock:
                cache_file.write_text(json.dumps(cache_data, ensure_ascii=False), encoding="utf-8")
                
            # 優先度の初期設定
            if self.use_priority:
                self._update_priority(cache_key)
                # 定期的に保存
                if len(self.priority_data["priorities"]) % 5 == 0:
                    await self._save_priority_data()
                
            logger.debug(f"キャッシュ保存: {cache_key}")
            self._update_stats()
            return True
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")
            return False
            
    def _generate_cache_key(self, key_data: Dict[str, Any]) -> str:
        """
        キャッシュキーを生成
        
        Args:
            key_data: キャッシュキーの元になるデータ
            
        Returns:
            str: 一意のキャッシュキー
        """
        # 安定したキー生成のためにソート
        if isinstance(key_data, dict):
            # 辞書データはキーでソートしてから文字列化
            serialized = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        else:
            # その他のデータはそのまま文字列化
            serialized = str(key_data)
            
        # SHA-256ハッシュ生成
        hash_obj = hashlib.sha256(serialized.encode("utf-8"))
        return hash_obj.hexdigest()
        
    async def _check_cache_size(self) -> None:
        """
        キャッシュサイズをチェックし、必要に応じてクリーンアップ
        """
        if not self.enable_cache:
            return
            
        # 定期チェック（前回から10分以上経過時）
        now = datetime.now().timestamp()
        if now - self.stats["last_cleanup"] < 600:  # 10分 = 600秒
            return
            
        # サイズ取得と統計更新
        self._update_stats()
        
        # サイズ制限チェック
        max_size_bytes = self.max_cache_size_mb * 1024 * 1024  # MBをバイトに変換
        if self.stats["size_bytes"] <= max_size_bytes:
            return
            
        logger.info(f"キャッシュサイズ制限超過: {self.stats['size_bytes'] / (1024*1024):.2f}MB > "
                   f"{self.max_cache_size_mb}MB、クリーンアップ開始")
        
        await self._cleanup_cache(max_size_bytes)
        
    async def _cleanup_cache(self, max_size_bytes: int) -> None:
        """
        古いキャッシュを削除して容量を確保
        
        Args:
            max_size_bytes: 目標最大サイズ（バイト）
        """
        try:
            # キャッシュファイル一覧取得
            cache_files = list(self.cache_dir.glob("*.json"))
            
            # メタデータファイルは除外
            cache_files = [f for f in cache_files if f.name != "priority_index.json"]
            
            if not cache_files:
                return
                
            # ファイルを更新日時でソート
            cache_files.sort(key=lambda f: f.stat().st_mtime)
            
            # 目標サイズまで古いファイルを削除
            current_size = self.stats["size_bytes"]
            files_deleted = 0
            
            for file in cache_files:
                if current_size <= max_size_bytes * 0.9:  # 10%マージン
                    break
                    
                # 優先度が高いファイルは保護する
                if self.use_priority:
                    cache_key = file.stem  # 拡張子なしのファイル名
                    if cache_key in self.priority_data["priorities"]:
                        priority = self.priority_data["priorities"][cache_key]
                        if priority > 7.0:  # 高優先度しきい値
                            continue
                
                # ファイルサイズを取得して削除
                file_size = file.stat().st_size
                await self._remove_cache_file(file)
                
                current_size -= file_size
                files_deleted += 1
            
            # 統計情報を更新
            self._update_stats()
            
            logger.info(f"キャッシュクリーンアップ完了: {files_deleted}ファイル削除、" 
                       f"現在のサイズ: {self.stats['size_bytes'] / (1024*1024):.2f}MB")
                       
        except Exception as e:
            logger.error(f"キャッシュクリーンアップエラー: {e}")
            
    async def _remove_cache_file(self, file_path: Path) -> None:
        """
        キャッシュファイルを安全に削除
        
        Args:
            file_path: 削除するファイルのパス
        """
        try:
            async with self._lock:
                file_path.unlink(missing_ok=True)
                
                # 優先度データからも削除
                if self.use_priority:
                    cache_key = file_path.stem
                    if cache_key in self.priority_data["access_counts"]:
                        del self.priority_data["access_counts"][cache_key]
                    if cache_key in self.priority_data["last_access"]:
                        del self.priority_data["last_access"][cache_key]
                    if cache_key in self.priority_data["priorities"]:
                        del self.priority_data["priorities"][cache_key]
                        
        except Exception as e:
            logger.error(f"キャッシュファイル削除エラー ({file_path}): {e}")
            
    def _update_stats(self) -> None:
        """キャッシュの統計情報を更新"""
        if not self.enable_cache:
            return
            
        try:
            # キャッシュファイル一覧取得（メタデータを除く）
            cache_files = list(self.cache_dir.glob("*.json"))
            cache_files = [f for f in cache_files if f.name != "priority_index.json"]
            
            # サイズ計算
            total_size = sum(f.stat().st_size for f in cache_files)
            
            self.stats.update({
                "entries": len(cache_files),
                "size_bytes": total_size,
                "last_cleanup": datetime.now().timestamp()
            })
            
        except Exception as e:
            logger.error(f"統計更新エラー: {e}")
            
    async def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        # 最新の統計に更新
        self._update_stats()
        
        # キャッシュ有効期限情報を追加
        stats_copy = self.stats.copy()
        stats_copy["ttl_seconds"] = self.ttl_seconds
        stats_copy["max_size_mb"] = self.max_cache_size_mb
        stats_copy["enabled"] = self.enable_cache
        
        # バイト数をMBに変換
        stats_copy["size_mb"] = stats_copy["size_bytes"] / (1024 * 1024)
        
        # ヒット率計算
        total_requests = stats_copy["hits"] + stats_copy["misses"]
        stats_copy["hit_ratio"] = stats_copy["hits"] / total_requests if total_requests > 0 else 0
        
        # 優先度情報を追加
        if self.use_priority:
            stats_copy["priority_enabled"] = True
            stats_copy["priority_entries"] = len(self.priority_data["priorities"])
            
            if "priority_hits" in stats_copy and stats_copy["hits"] > 0:
                stats_copy["priority_hit_ratio"] = stats_copy["priority_hits"] / stats_copy["hits"]
            
        return stats_copy
        
    async def invalidate_cache(self, key_data: Dict[str, Any]) -> bool:
        """
        特定のキャッシュエントリを無効化
        
        Args:
            key_data: 無効化するキャッシュキーを特定するデータ
            
        Returns:
            bool: 無効化成功したか
        """
        if not self.enable_cache:
            return False
            
        try:
            cache_key = self._generate_cache_key(key_data)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                await self._remove_cache_file(cache_file)
                logger.debug(f"キャッシュ無効化: {cache_key}")
                self._update_stats()
                return True
            return False
        except Exception as e:
            logger.error(f"キャッシュ無効化エラー: {e}")
            return False


# デフォルトインスタンス
default_cache_manager = None

async def get_cache_manager(cache_dir: str = None, ttl_seconds: int = 3600 * 24,
                     max_cache_size_mb: int = 500, enable_cache: bool = True,
                     use_priority: bool = False) -> AICacheManager:
    """
    デフォルトのキャッシュマネージャーを取得または初期化する
    
    Args:
        cache_dir: キャッシュディレクトリパス
        ttl_seconds: キャッシュエントリの有効期限（秒）
        max_cache_size_mb: キャッシュの最大サイズ（MB）
        enable_cache: キャッシュ機能の有効化フラグ
        use_priority: 優先度ベースのキャッシュ管理を有効化
        
    Returns:
        AICacheManager: キャッシュマネージャーインスタンス
    """
    global default_cache_manager
    
    if default_cache_manager is None:
        default_cache_manager = AICacheManager(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_cache_size_mb=max_cache_size_mb,
            enable_cache=enable_cache,
            use_priority=use_priority
        )
        
    return default_cache_manager
