"""
統合された最適化キャッシュマネージャー

基本のAICacheManagerを継承し、最適化された類似キャッシュ検索を統合した
高速キャッシュマネージャーを提供します。
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
from ai.optimized_cache_search import get_optimized_similarity_cache

logger = logging.getLogger(__name__)

class OptimizedAICacheManager(AICacheManager):
    """
    最適化された類似キャッシュ検索機能を持つAIキャッシュマネージャー
    
    特徴:
    - 高速エンベディング生成
    - バッチ処理による類似検索の最適化
    - 重複計算回避のためのメモリキャッシュ
    - クエリハッシュによる高速検索
    """
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 3600 * 24, 
                 max_cache_size_mb: int = 500, enable_cache: bool = True,
                 use_priority: bool = False, use_similarity: bool = True,
                 similarity_threshold: float = 0.75):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
            ttl_seconds: キャッシュの有効期限（秒）
            max_cache_size_mb: キャッシュの最大サイズ（MB）
            enable_cache: キャッシュ機能の有効化
            use_priority: 優先度ベースのキャッシュ管理を有効化
            use_similarity: 類似クエリ検出を有効化
            similarity_threshold: 類似度閾値 (0-1)
        """
        super().__init__(cache_dir, ttl_seconds, max_cache_size_mb, enable_cache, use_priority)
        
        self.use_similarity = use_similarity and enable_cache
        self.similarity_threshold = similarity_threshold
        self._similarity_cache = None
        self._initialization_task = None
        
        if self.use_similarity:
            self.stats["similarity_hits"] = 0
            self._initialization_task = asyncio.create_task(self._initialize_similarity_cache())
    
    async def _initialize_similarity_cache(self):
        """類似キャッシュの初期化（非同期）"""
        try:
            # 最適化された類似キャッシュを取得
            self._similarity_cache = await get_optimized_similarity_cache(
                cache_dir=str(self.cache_dir / "similarity"),
                similarity_threshold=self.similarity_threshold
            )
            logger.info("最適化された類似キャッシュの初期化が完了しました")
        except Exception as e:
            logger.error(f"類似キャッシュの初期化エラー: {e}")
            self._similarity_cache = None
    
    async def set_cache(self, key_data: Dict[str, Any], result: Any, ttl: int = None, 
                       priority: int = None) -> bool:
        """
        キャッシュにデータを保存し、類似検索用のエンベディングも追加
        
        Args:
            key_data: キャッシュキー情報
            result: キャッシュする結果データ
            ttl: キャッシュ有効期限（秒）
            priority: キャッシュ優先度
        
        Returns:
            bool: 成功したか
        """
        # 基本的なキャッシュ保存処理
        success = await super().set_cache(key_data, result, ttl, priority)
        
        # 類似検索が有効で、キャッシュ保存が成功した場合
        if success and self.use_similarity and "query" in key_data:
            try:
                # 初期化待機
                if self._initialization_task is not None and not self._initialization_task.done():
                    await self._initialization_task
                
                if self._similarity_cache is not None:
                    # キャッシュキーを生成
                    cache_key = self._generate_cache_key(key_data)
                    
                    # エンベディングを追加
                    await self._similarity_cache.add_query_embedding(
                        cache_key=cache_key,
                        query=key_data["query"]
                    )
            except Exception as e:
                logger.error(f"類似キャッシュへの追加エラー: {e}")
        
        return success
    
    async def get_cache(self, key_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        キャッシュからデータを取得（類似検索を含む）
        
        Args:
            key_data: キャッシュキー情報
        
        Returns:
            Tuple[bool, Any]: (ヒットしたか, キャッシュデータ)
        """
        # まず完全一致を試す（最も高速）
        hit, result = await super().get_cache(key_data)
        
        # 完全一致でヒットした場合はそのまま返す
        if hit:
            return hit, result
        
        # 類似検索が無効、または "query" キーがない場合は終了
        if not self.use_similarity or "query" not in key_data:
            return False, None
            
        try:
            # 初期化待機
            if self._initialization_task is not None and not self._initialization_task.done():
                await self._initialization_task
            
            # 類似キャッシュがない場合は終了
            if self._similarity_cache is None:
                return False, None
            
            # クエリの取得
            query = key_data["query"]
            start_time = time.time()
            
            # 類似キャッシュを検索
            similar_cache_key, similarity = await self._similarity_cache.find_similar_cache(
                query=query,
                threshold=self.similarity_threshold
            )
            
            search_time = time.time() - start_time
            
            # 類似キャッシュが見つからなかった場合
            if not similar_cache_key:
                return False, None
            
            # キャッシュファイルから結果を取得
            try:
                cache_path = self.cache_dir / f"{similar_cache_key}.json"
                if not cache_path.exists():
                    return False, None
                
                # キャッシュファイルを読み込む
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 有効期限をチェック
                if "expire_at" in cache_data and cache_data["expire_at"] < time.time():
                    # 期限切れ
                    return False, None
                
                # 統計情報の更新
                self.stats["total_requests"] += 1
                self.stats["similarity_hits"] = self.stats.get("similarity_hits", 0) + 1
                self.stats["response_time_ms"] += int(search_time * 1000)
                
                # メタデータ付きの結果を返す
                result_with_meta = cache_data.get("result", None)
                if isinstance(result_with_meta, dict):
                    result_with_meta["_similarity_info"] = {
                        "similarity": similarity,
                        "original_query": cache_data.get("key_data", {}).get("query", ""),
                        "search_time_ms": int(search_time * 1000)
                    }
                
                return True, result_with_meta
            except Exception as e:
                logger.error(f"類似キャッシュからの読み込みエラー: {e}")
                return False, None
                
        except Exception as e:
            logger.error(f"類似キャッシュ検索エラー: {e}")
            return False, None
    
    async def get_stats(self) -> Dict[str, Any]:
        """拡張された統計情報を取得"""
        # 基本統計を取得
        stats = await super().get_stats()
        
        # 類似検索の統計を追加
        if self.use_similarity:
            similarity_hits = self.stats.get("similarity_hits", 0)
            total_hits = stats.get("hits", 0) + similarity_hits
            total_requests = stats.get("total_requests", 0)
            
            stats["similarity_hits"] = similarity_hits
            stats["total_hits"] = total_hits
            
            # ヒット率の再計算
            if total_requests > 0:
                stats["hit_ratio"] = round(total_hits / total_requests, 4)
        
        return stats
    
    async def invalidate_cache(self, key_data: Dict[str, Any]) -> bool:
        """
        キャッシュの無効化（類似キャッシュも含む）
        
        Args:
            key_data: キャッシュキー情報
        
        Returns:
            bool: 成功したか
        """
        success = await super().invalidate_cache(key_data)
        
        # 類似キャッシュからも削除
        if success and self.use_similarity and self._similarity_cache is not None:
            try:
                cache_key = self._generate_cache_key(key_data)
                await self._similarity_cache.remove_embedding(cache_key)
            except Exception as e:
                logger.error(f"類似キャッシュの無効化エラー: {e}")
        
        return success

# シングルトンインスタンス
_optimized_cache_manager = None

def get_optimized_cache_manager() -> OptimizedAICacheManager:
    """
    最適化されたキャッシュマネージャーのシングルトンインスタンスを取得
    
    Returns:
        OptimizedAICacheManager: 最適化されたキャッシュマネージャー
    """
    global _optimized_cache_manager
    
    if _optimized_cache_manager is None:
        # 環境設定から構成を読み込み
        import os
        
        cache_dir = os.environ.get("AI_CACHE_DIR", None)
        ttl_seconds = int(os.environ.get("AI_CACHE_TTL", 86400))
        max_cache_size_mb = int(os.environ.get("AI_CACHE_MAX_SIZE", 500))
        enable_cache = os.environ.get("AI_CACHE_ENABLED", "true").lower() == "true"
        use_similarity = os.environ.get("AI_CACHE_SIMILARITY", "true").lower() == "true"
        similarity_threshold = float(os.environ.get("AI_CACHE_SIMILARITY_THRESHOLD", "0.75"))
        
        _optimized_cache_manager = OptimizedAICacheManager(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_cache_size_mb=max_cache_size_mb,
            enable_cache=enable_cache,
            use_similarity=use_similarity,
            similarity_threshold=similarity_threshold
        )
    
    return _optimized_cache_manager
