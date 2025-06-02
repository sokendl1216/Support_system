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
                 max_cache_size_mb: int = 500, enable_cache: bool = True):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリパス。Noneの場合はデフォルトパスを使用
            ttl_seconds: キャッシュエントリの有効期限（秒）
            max_cache_size_mb: キャッシュの最大サイズ（MB）
            enable_cache: キャッシュ機能の有効化フラグ
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
        
        # 統計情報
        self.stats = {
            "hits": 0,
            "misses": 0,
            "entries": 0,
            "size_bytes": 0,
            "last_cleanup": datetime.now().timestamp()
        }
        
        # ロック（スレッド/プロセス間の同期）
        self._lock = asyncio.Lock()
        
        logger.info(f"AIキャッシュ機構を初期化: {self.cache_dir}, TTL: {ttl_seconds}s, "
                   f"最大サイズ: {max_cache_size_mb}MB")
        
        # 初期統計情報を更新
        self._update_stats()

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
                
                # 有効期限チェック
                timestamp = cache_data.get("timestamp", 0)
                if timestamp + self.ttl_seconds < time.time():
                    # 期限切れ: キャッシュミス
                    logger.debug(f"キャッシュ期限切れ: {cache_key}")
                    self.stats["misses"] += 1
                    # 古いファイルは非同期で削除
                    asyncio.create_task(self._remove_cache_file(cache_file))
                    return False, None
                
                # キャッシュヒット
                logger.debug(f"キャッシュヒット: {cache_key}")
                self.stats["hits"] += 1
                # 最終アクセス時間を更新
                cache_file.touch()
                return True, cache_data.get("data")
                
        except Exception as e:
            logger.error(f"キャッシュ取得エラー: {e}")
            self.stats["misses"] += 1
            return False, None

    async def set_cache(self, key_data: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        データをキャッシュに格納
        
        Args:
            key_data: キャッシュキーを生成するためのデータ
            data: キャッシュするデータ
            
        Returns:
            bool: 保存に成功したか
        """
        if not self.enable_cache:
            return False
            
        cache_key = self._generate_cache_key(key_data)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # キャッシュサイズ管理
            await self._manage_cache_size()
            
            # キャッシュデータの構築
            cache_data = {
                "timestamp": time.time(),
                "key_data": key_data,
                "data": data
            }
            
            # キャッシュファイルに保存
            async with self._lock:
                cache_file.write_text(json.dumps(cache_data, ensure_ascii=False), encoding="utf-8")
                
            logger.debug(f"キャッシュ保存: {cache_key}")
            
            # 統計更新
            self._update_stats()
            return True
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")
            return False

    async def clear_cache(self) -> bool:
        """
        キャッシュをクリア
        
        Returns:
            bool: クリア成功したか
        """
        if not self.enable_cache:
            return False
            
        try:
            async with self._lock:
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.error(f"キャッシュファイル削除エラー: {e}")
            
            self._reset_stats()
            logger.info("キャッシュをクリア")
            return True
            
        except Exception as e:
            logger.error(f"キャッシュクリアエラー: {e}")
            return False

    async def cleanup_expired(self) -> int:
        """
        期限切れキャッシュエントリを削除
        
        Returns:
            int: 削除されたキャッシュエントリ数
        """
        if not self.enable_cache:
            return 0
            
        try:
            removed_count = 0
            current_time = time.time()
            
            async with self._lock:
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        # キャッシュデータを読み取り
                        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                        timestamp = cache_data.get("timestamp", 0)
                        
                        # 期限切れチェック
                        if timestamp + self.ttl_seconds < current_time:
                            cache_file.unlink()
                            removed_count += 1
                    except Exception as e:
                        logger.error(f"期限切れキャッシュクリーンアップエラー: {e}")
            
            self.stats["last_cleanup"] = datetime.now().timestamp()
            self._update_stats()
            
            logger.info(f"{removed_count}件の期限切れキャッシュを削除")
            return removed_count
            
        except Exception as e:
            logger.error(f"キャッシュクリーンアップエラー: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得
        
        Returns:
            Dict[str, Any]: キャッシュ統計
        """
        if not self.enable_cache:
            return {"enabled": False}
            
        # 最新の統計情報を取得
        self._update_stats()
        
        # キャッシュヒット率を計算
        total_accesses = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / total_accesses if total_accesses > 0 else 0
        
        return {
            "enabled": True,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_ratio": hit_ratio,
            "entries": self.stats["entries"],
            "size_bytes": self.stats["size_bytes"],
            "size_mb": self.stats["size_bytes"] / (1024 * 1024),
            "max_size_mb": self.max_cache_size_mb,
            "ttl_seconds": self.ttl_seconds,
            "last_cleanup": datetime.fromtimestamp(self.stats["last_cleanup"]).isoformat(),
            "cache_dir": str(self.cache_dir)
        }

    def _generate_cache_key(self, key_data: Dict[str, Any]) -> str:
        """
        キャッシュキーを生成
        
        Args:
            key_data: キャッシュキーを生成するためのデータ
            
        Returns:
            str: 生成されたキャッシュキー
        """
        # 辞書をソートしてキー生成を一貫性のあるものにする
        serialized = json.dumps(key_data, sort_keys=True)
        
        # SHA-256ハッシュを計算
        hash_obj = hashlib.sha256(serialized.encode())
        return hash_obj.hexdigest()

    async def _manage_cache_size(self) -> None:
        """キャッシュサイズを管理"""
        # 現在のキャッシュサイズを確認
        self._update_stats()
        current_size_mb = self.stats["size_bytes"] / (1024 * 1024)
        
        # サイズ制限を超えていない場合は何もしない
        if current_size_mb < self.max_cache_size_mb:
            return
            
        # サイズ制限を超えている場合、古いキャッシュから削除
        logger.info(f"キャッシュサイズ管理: 現在 {current_size_mb:.2f}MB / {self.max_cache_size_mb}MB")
        
        try:
            # アクセス時間でソートしたファイル一覧を取得
            cache_files = []
            for cache_file in self.cache_dir.glob("*.json"):
                cache_files.append((cache_file, cache_file.stat().st_atime))
            
            # 古い順にソート
            cache_files.sort(key=lambda x: x[1])
            
            # 目標サイズに達するまで削除
            target_size_mb = self.max_cache_size_mb * 0.8  # 20%の余裕を持たせる
            removed = 0
            
            async with self._lock:
                for cache_file, _ in cache_files:
                    if current_size_mb <= target_size_mb:
                        break
                    
                    file_size_mb = cache_file.stat().st_size / (1024 * 1024)
                    try:
                        cache_file.unlink()
                        current_size_mb -= file_size_mb
                        removed += 1
                    except Exception as e:
                        logger.error(f"キャッシュファイル削除エラー: {e}")
            
            logger.info(f"キャッシュサイズ管理: {removed}件のキャッシュを削除, 新しいサイズ: {current_size_mb:.2f}MB")
            
        except Exception as e:
            logger.error(f"キャッシュサイズ管理エラー: {e}")
        
        finally:
            # 統計を更新
            self._update_stats()

    async def _remove_cache_file(self, file_path: Path) -> None:
        """キャッシュファイルを削除"""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"キャッシュファイル削除エラー: {e}")

    def _update_stats(self) -> None:
        """キャッシュ統計を更新"""
        if not self.enable_cache:
            return
            
        try:
            # エントリ数を計算
            entries = list(self.cache_dir.glob("*.json"))
            self.stats["entries"] = len(entries)
            
            # サイズを計算
            size_bytes = sum(f.stat().st_size for f in entries)
            self.stats["size_bytes"] = size_bytes
            
        except Exception as e:
            logger.error(f"統計情報更新エラー: {e}")

    def _reset_stats(self) -> None:
        """統計情報をリセット"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "entries": 0,
            "size_bytes": 0,
            "last_cleanup": datetime.now().timestamp()
        }

    async def invalidate_cache_for_key(self, key_data: Dict[str, Any]) -> bool:
        """特定のキーのキャッシュを無効化"""
        if not self.enable_cache:
            return False
            
        cache_key = self._generate_cache_key(key_data)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
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

def get_cache_manager(cache_dir: str = None, ttl_seconds: int = 3600 * 24,
                     max_cache_size_mb: int = 500, enable_cache: bool = True) -> AICacheManager:
    """
    デフォルトのキャッシュマネージャーを取得または初期化する
    
    Args:
        cache_dir: キャッシュディレクトリパス
        ttl_seconds: キャッシュエントリの有効期限（秒）
        max_cache_size_mb: キャッシュの最大サイズ（MB）
        enable_cache: キャッシュ機能の有効化フラグ
        
    Returns:
        AICacheManager: キャッシュマネージャーインスタンス
    """
    global default_cache_manager
    
    if default_cache_manager is None:
        default_cache_manager = AICacheManager(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_cache_size_mb=max_cache_size_mb,
            enable_cache=enable_cache
        )
    
    return default_cache_manager
