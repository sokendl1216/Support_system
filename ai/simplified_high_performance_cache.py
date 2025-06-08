"""
シンプルで高性能なAIキャッシュマネージャー

基本的なキャッシュ機能とメモリキャッシュを組み合わせた軽量・高速なキャッシュマネージャー。
"""

import logging
import os
import hashlib
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

from ai.cache_manager import AICacheManager

logger = logging.getLogger(__name__)

class SimplifiedHighPerformanceCache(AICacheManager):
    """
    高速化されたキャッシュ機能のシンプルな実装
    メモリキャッシュとディスクキャッシュを組み合わせ
    """
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 3600 * 24, 
                 max_cache_size_mb: int = 500, enable_cache: bool = True,
                 use_priority: bool = False):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
            ttl_seconds: キャッシュの有効期限（秒）
            max_cache_size_mb: キャッシュの最大サイズ（MB）
            enable_cache: キャッシュ機能の有効化
            use_priority: 優先度ベースのキャッシュ管理を有効化
        """
        super().__init__(cache_dir, ttl_seconds, max_cache_size_mb, enable_cache, use_priority)
        
        # メモリ内リクエストキャッシュ（最速）
        self._memory_cache = {}
        self._memory_cache_ttl = {}
        self._memory_cache_max_size = 100  # 最大エントリ数
        
        # 統計情報の初期化
        self.stats["memory_hits"] = 0
        self.stats["total_requests"] = 0  # 総リクエスト数も初期化
    
    async def set_cache(self, key_data: Dict[str, Any], data: Any) -> bool:
        """
        キャッシュにデータを保存
        
        Args:
            key_data: キャッシュキー情報
            data: キャッシュする結果データ
        
        Returns:
            bool: 成功したか
        """
        # 基本的なキャッシュ保存処理
        success = await super().set_cache(key_data, data)
        
        if success:
            # キャッシュキーを生成
            cache_key = self._generate_cache_key(key_data)
            
            # メモリキャッシュの管理（最大サイズを超えた場合）
            if len(self._memory_cache) >= self._memory_cache_max_size:
                # 最も古いか期限切れのエントリを削除
                oldest_key = None
                oldest_time = float('inf')
                current_time = time.time()
                
                for k, t in self._memory_cache_ttl.items():
                    if t < current_time or t < oldest_time:
                        oldest_key = k
                        oldest_time = t
                
                if oldest_key:
                    del self._memory_cache[oldest_key]
                    del self._memory_cache_ttl[oldest_key]
            
            # メモリキャッシュのTTLを設定（ディスクキャッシュの半分）
            mem_ttl = time.time() + (self.ttl_seconds / 2)
            
            # メモリキャッシュに保存
            self._memory_cache[cache_key] = data
            self._memory_cache_ttl[cache_key] = mem_ttl
        
        return success
    
    async def get_cache(self, key_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        キャッシュからデータを取得
        
        Args:
            key_data: キャッシュキー情報
        
        Returns:
            Tuple[bool, Any]: (ヒットしたか, キャッシュデータ)
        """
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(key_data)
        
        # メモリキャッシュを確認（最速）
        if cache_key in self._memory_cache:
            # TTLをチェック
            if time.time() < self._memory_cache_ttl[cache_key]:
                # メモリキャッシュヒット
                self.stats["memory_hits"] = self.stats.get("memory_hits", 0) + 1
                self.stats["total_requests"] += 1
                return True, self._memory_cache[cache_key]
            else:
                # 期限切れならメモリから削除
                del self._memory_cache[cache_key]
                del self._memory_cache_ttl[cache_key]
        
        # ディスクキャッシュを確認
        hit, result = await super().get_cache(key_data)
        
        # キャッシュヒットした場合はメモリにも保存
        if hit:
            # メモリキャッシュに保存（次回のアクセスを高速化）
            self._memory_cache[cache_key] = result
            self._memory_cache_ttl[cache_key] = time.time() + (self.ttl_seconds / 2)
        
        return hit, result
    
    async def get_stats(self) -> Dict[str, Any]:
        """拡張された統計情報を取得"""
        # 基本統計を取得
        stats = await super().get_stats()
        
        # メモリキャッシュの統計を追加
        memory_hits = self.stats.get("memory_hits", 0)
        stats["memory_hits"] = memory_hits
        
        # 総ヒット数と使用率の計算
        total_hits = stats.get("hits", 0) + memory_hits
        total_requests = stats.get("total_requests", 0)
        
        stats["total_hits"] = total_hits
        stats["memory_cache_entries"] = len(self._memory_cache)
        
        # ヒット率の再計算
        if total_requests > 0:
            stats["hit_ratio"] = round(total_hits / total_requests, 4)
        
        return stats
    
    async def invalidate_cache(self, key_data: Dict[str, Any]) -> bool:
        """
        キャッシュの無効化
        
        Args:
            key_data: キャッシュキー情報
        
        Returns:
            bool: 成功したか
        """
        # 基本的な無効化処理
        success = await super().invalidate_cache(key_data)
        
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(key_data)
        
        # メモリキャッシュからも削除
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            if cache_key in self._memory_cache_ttl:
                del self._memory_cache_ttl[cache_key]
        
        return success


# シングルトンインスタンス
_simplified_cache_manager = None

def get_simplified_high_performance_cache() -> SimplifiedHighPerformanceCache:
    """
    シンプルで高性能なキャッシュマネージャーのシングルトンを取得
    
    Returns:
        SimplifiedHighPerformanceCache: キャッシュマネージャーインスタンス
    """
    global _simplified_cache_manager
    
    if _simplified_cache_manager is None:
        # 環境設定から構成を読み込み
        import os
        
        cache_dir = os.environ.get("AI_CACHE_DIR", None)
        ttl_seconds = int(os.environ.get("AI_CACHE_TTL", 86400))
        max_cache_size_mb = int(os.environ.get("AI_CACHE_MAX_SIZE", 500))
        enable_cache = os.environ.get("AI_CACHE_ENABLED", "true").lower() == "true"
        
        _simplified_cache_manager = SimplifiedHighPerformanceCache(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_cache_size_mb=max_cache_size_mb,
            enable_cache=enable_cache
        )
    
    return _simplified_cache_manager
