"""
ハイパフォーマンス統合キャッシュマネージャー

このモジュールは、基本のAICacheManagerを拡張し、パフォーマンスを大幅に向上させた
類似キャッシュ検索機能を統合した最適化版キャッシュマネージャーを提供します。
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
from ai.fixed_cache_similarity import get_similarity_cache, SimilarityCache

logger = logging.getLogger(__name__)

class HighPerformanceAICacheManager(AICacheManager):
    """
    高性能な類似キャッシュ検索機能を持つAIキャッシュマネージャー
    
    特徴:
    - 高速エンベディング生成（量子化モデル使用）
    - 並列処理による非同期検索
    - スレッドプールによるCPU最適化
    - 多層キャッシュ（メモリ、ハッシュ、類似検索）
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
          # メモリ内リクエストキャッシュ（最速）
        self._memory_cache = {}
        self._memory_cache_ttl = {}
        self._memory_cache_max_size = 100  # 最大エントリ数
        
        if self.use_similarity:
            self.stats["similarity_hits"] = 0
            self.stats["total_requests"] = 0  # 総リクエスト数も初期化
            self.stats["memory_hits"] = 0  # メモリヒット数も初期化
            self.stats["response_time_ms"] = 0  # レスポンス時間も初期化
            self._initialization_task = asyncio.create_task(self._initialize_similarity_cache())
    
    async def _initialize_similarity_cache(self):
        """類似キャッシュの初期化（非同期）"""
        try:
            # 最適化された類似キャッシュを取得
            sim_cache_dir = self.cache_dir / "similarity"
            os.makedirs(sim_cache_dir, exist_ok=True)
            
            self._similarity_cache = await get_similarity_cache(
                cache_dir=str(sim_cache_dir),
                similarity_threshold=self.similarity_threshold
            )
            logger.info("高性能類似キャッシュの初期化が完了しました")
        except Exception as e:
            logger.error(f"類似キャッシュの初期化エラー: {e}")
            self._similarity_cache = None
            
    async def set_cache(self, key_data: Dict[str, Any], data: Any) -> bool:
        """
        キャッシュにデータを保存し、類似検索用のエンベディングも追加
        
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
            
            # メモリ内キャッシュに保存（最も高速）
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
            
            # 類似検索が有効で、queryがある場合は類似キャッシュにも追加
            if self.use_similarity and "query" in key_data:
                try:
                    # 初期化待機
                    if self._initialization_task is not None and not self._initialization_task.done():
                        await self._initialization_task
                    
                    if self._similarity_cache is not None:
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
        キャッシュからデータを取得（多層キャッシュ）
        
        レイヤー1: メモリ内キャッシュ（最速）
        レイヤー2: 完全一致ディスクキャッシュ
        レイヤー3: 類似検索キャッシュ（高度な一致）
        
        Args:
            key_data: キャッシュキー情報
        
        Returns:
            Tuple[bool, Any]: (ヒットしたか, キャッシュデータ)
        """
        start_time = time.time()
        
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(key_data)
        
        # レイヤー1: メモリキャッシュを確認（最速）
        if cache_key in self._memory_cache:
            # TTLをチェック
            if time.time() < self._memory_cache_ttl[cache_key]:
                # メモリキャッシュヒット
                self.stats["memory_hits"] = self.stats.get("memory_hits", 0) + 1
                self.stats["total_requests"] += 1
                self.stats["response_time_ms"] += int((time.time() - start_time) * 1000)
                return True, self._memory_cache[cache_key]
            else:
                # 期限切れならメモリから削除
                del self._memory_cache[cache_key]
                del self._memory_cache_ttl[cache_key]
        
        # レイヤー2: 完全一致キャッシュを確認
        hit, result = await super().get_cache(key_data)
        
        # 完全一致でヒットした場合はメモリキャッシュに保存して返す
        if hit:
            # メモリキャッシュに保存（次回のアクセスを高速化）
            self._memory_cache[cache_key] = result
            self._memory_cache_ttl[cache_key] = time.time() + (self.ttl_seconds / 2)
            return hit, result
        
        # レイヤー3: 類似検索が無効か、"query"キーがない場合は終了
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
            
            # 類似キャッシュを検索
            similar_cache_key, similarity = await self._similarity_cache.find_similar_cache(
                query=query,
                threshold=self.similarity_threshold
            )
            
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
                
                # 結果を取得
                result_with_meta = cache_data.get("result", None)
                
                # メタデータを追加
                if isinstance(result_with_meta, dict):
                    result_with_meta["_similarity_info"] = {
                        "similarity": similarity,
                        "original_query": cache_data.get("key_data", {}).get("query", ""),
                        "search_time_ms": int((time.time() - start_time) * 1000)
                    }
                
                # メモリキャッシュにも保存（次回のアクセスを高速化）
                self._memory_cache[cache_key] = result_with_meta
                self._memory_cache_ttl[cache_key] = time.time() + (self.ttl_seconds / 2)
                
                # レスポンス時間を記録
                self.stats["response_time_ms"] += int((time.time() - start_time) * 1000)
                
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
        
        # メモリキャッシュの統計を追加
        memory_hits = self.stats.get("memory_hits", 0)
        stats["memory_hits"] = memory_hits
        
        # 類似検索の統計を追加
        if self.use_similarity:
            similarity_hits = self.stats.get("similarity_hits", 0)
            total_hits = stats.get("hits", 0) + similarity_hits + memory_hits
            total_requests = stats.get("total_requests", 0)
            
            stats["similarity_hits"] = similarity_hits
            stats["total_hits"] = total_hits
            
            # メモリ使用量の追加
            stats["memory_cache_entries"] = len(self._memory_cache)
            
            # ヒット率の再計算
            if total_requests > 0:
                stats["hit_ratio"] = round(total_hits / total_requests, 4)
        
        return stats
    
    async def invalidate_cache(self, key_data: Dict[str, Any]) -> bool:
        """
        キャッシュの無効化（全レイヤー）
        
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
            del self._memory_cache_ttl[cache_key]
          # 類似キャッシュからも削除        if success and self.use_similarity and self._similarity_cache is not None:
            try:
                await self._similarity_cache.remove_embedding(cache_key)
            except Exception as e:
                logger.error(f"類似キャッシュの無効化エラー: {e}")
        return success

# シングルトンインスタンス
_high_performance_cache_manager = None

def get_high_performance_cache_manager() -> HighPerformanceAICacheManager:
    """
    高性能キャッシュマネージャーのシングルトンインスタンスを取得
    
    Returns:
        HighPerformanceAICacheManager: 高性能キャッシュマネージャー
    """
    global _high_performance_cache_manager
    
    if _high_performance_cache_manager is None:
        # 環境設定から構成を読み込み
        import os
        
        cache_dir = os.environ.get("AI_CACHE_DIR", None)
        ttl_seconds = int(os.environ.get("AI_CACHE_TTL", 86400))
        max_cache_size_mb = int(os.environ.get("AI_CACHE_MAX_SIZE", 500))
        enable_cache = os.environ.get("AI_CACHE_ENABLED", "true").lower() == "true"
        use_similarity = os.environ.get("AI_CACHE_SIMILARITY", "true").lower() == "true"
        similarity_threshold = float(os.environ.get("AI_CACHE_SIMILARITY_THRESHOLD", "0.75"))
        
        _high_performance_cache_manager = HighPerformanceAICacheManager(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_cache_size_mb=max_cache_size_mb,
            enable_cache=enable_cache,
            use_similarity=use_similarity,
            similarity_threshold=similarity_threshold
        )
    
    return _high_performance_cache_manager
