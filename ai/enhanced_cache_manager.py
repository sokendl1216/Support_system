"""
拡張AIキャッシュマネージャー

類似クエリ検出機能を統合したAIキャッシュマネージャーの拡張版
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ai.cache_manager import AICacheManager
from ai.cache_similarity import EmbeddingService, SimilarityCache

logger = logging.getLogger(__name__)

class EnhancedAICacheManager(AICacheManager):
    """
    類似クエリ検出機能を持つ拡張AIキャッシュマネージャー
    """
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 3600 * 24, 
                 max_cache_size_mb: int = 500, enable_cache: bool = True,
                 use_priority: bool = False, use_similarity: bool = True,
                 similarity_threshold: float = 0.85):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリパス
            ttl_seconds: キャッシュエントリの有効期限（秒）
            max_cache_size_mb: キャッシュの最大サイズ（MB）
            enable_cache: キャッシュ機能の有効化フラグ
            use_priority: 優先度ベースのキャッシュ管理を有効化
            use_similarity: 類似クエリ検出を有効化
            similarity_threshold: 類似と判断する閾値 (0-1)
        """
        super().__init__(cache_dir, ttl_seconds, max_cache_size_mb, enable_cache, use_priority)
        
        self.use_similarity = use_similarity and enable_cache
        self.similarity_threshold = similarity_threshold
        
        if self.use_similarity:
            self.stats["similarity_hits"] = 0
            self._initialize_similarity_cache()
            
    def _initialize_similarity_cache(self):
        """類似キャッシュ機能の初期化"""
        try:
            # エンベディングサービスを初期化
            self.embedding_service = EmbeddingService()
            
            # 類似キャッシュを初期化
            self.similarity_cache = SimilarityCache(
                embedding_service=self.embedding_service,
                cache_dir=self.cache_dir,
                similarity_threshold=self.similarity_threshold
            )
            
            logger.info("類似クエリ検出機能を初期化しました")
            
        except Exception as e:
            logger.error(f"類似クエリ検出機能の初期化エラー: {e}")
            self.use_similarity = False
            
    async def get_cache(self, key_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        キャッシュからデータを取得（完全一致＋類似検索）
        
        Args:
            key_data: キャッシュキーを生成するためのデータ
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (キャッシュヒットしたか, キャッシュデータ)
        """
        if not self.enable_cache:
            return False, None
            
        # 完全一致のキャッシュをチェック
        hit, data = await super().get_cache(key_data)
        
        # 完全一致でヒットした場合はそのまま返す
        if hit:
            return True, data
            
        # 完全一致でなく、類似検索が有効な場合
        if not hit and self.use_similarity and 'query' in key_data:
            query = key_data['query']
            
            try:
                # 類似キャッシュを検索
                cache_key, similarity = await self.similarity_cache.find_similar_cache(
                    query, self.similarity_threshold)
                
                if cache_key:
                    # キャッシュキーに対応するキーデータを取得
                    original_key_data = await self._get_key_data_from_cache_key(cache_key)
                    
                    if original_key_data:
                        # 元のキーデータでキャッシュを取得
                        hit, data = await super().get_cache(original_key_data)
                        
                        if hit:
                            # 類似キャッシュヒットの統計を更新
                            self.stats["similarity_hits"] = self.stats.get("similarity_hits", 0) + 1
                            
                            # データにメタ情報を追加
                            if isinstance(data, dict):
                                data["_similarity_info"] = {
                                    "original_query": original_key_data.get("query"),
                                    "similarity_score": similarity
                                }
                                
                            return True, data
            
            except Exception as e:
                logger.error(f"類似キャッシュ検索エラー: {e}")
        
        # 完全一致も類似もヒットしなかった場合
        return False, None
        
    async def set_cache(self, key_data: Dict[str, Any], data: Any) -> bool:
        """
        データをキャッシュに保存（エンベディングも登録）
        
        Args:
            key_data: キャッシュキーを生成するためのデータ
            data: 保存するデータ
            
        Returns:
            bool: 保存成功したか
        """
        # 標準のキャッシュ保存
        success = await super().set_cache(key_data, data)
        
        # 類似検索が有効で、クエリが含まれている場合、エンベディングも保存
        if success and self.use_similarity and 'query' in key_data:
            try:
                query = key_data['query']
                cache_key = self._generate_cache_key(key_data)
                
                # エンベディングを類似キャッシュに登録
                await self.similarity_cache.add_query_embedding(cache_key, query)
                
            except Exception as e:
                logger.error(f"エンベディング登録エラー: {e}")
                
        return success
        
    async def invalidate_cache(self, key_data: Dict[str, Any]) -> bool:
        """
        特定のキャッシュエントリを無効化（エンベディングも削除）
        
        Args:
            key_data: 無効化するキャッシュキーを特定するデータ
            
        Returns:
            bool: 無効化成功したか
        """
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(key_data)
        
        # 標準のキャッシュ無効化
        success = await super().invalidate_cache(key_data)
        
        # 類似検索が有効な場合、エンベディングも削除
        if success and self.use_similarity:
            try:
                await self.similarity_cache.remove_embedding(cache_key)
            except Exception as e:
                logger.error(f"エンベディング削除エラー: {e}")
                
        return success
        
    async def _remove_cache_file(self, file_path: Path) -> None:
        """
        キャッシュファイルを安全に削除（エンベディングも削除）
        
        Args:
            file_path: 削除するファイルのパス
        """
        # キャッシュキーを取得
        cache_key = file_path.stem
        
        # 標準の削除処理
        await super()._remove_cache_file(file_path)
        
        # 類似検索が有効な場合、エンベディングも削除
        if self.use_similarity:
            try:
                await self.similarity_cache.remove_embedding(cache_key)
            except Exception as e:
                logger.error(f"キャッシュファイル削除時のエンベディング削除エラー: {e}")
                
    async def _get_key_data_from_cache_key(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        キャッシュキーから元のキーデータを取得
        
        Args:
            cache_key: キャッシュキー
            
        Returns:
            Optional[Dict[str, Any]]: 元のキーデータ（見つからない場合はNone）
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
                
            async with self._lock:
                import json
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                return cache_data.get("key_data")
                
        except Exception as e:
            logger.error(f"キャッシュキーからのキーデータ取得エラー: {e}")
            return None
            
    async def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得（類似検索の統計を含む）
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        # 基本統計を取得
        stats = await super().get_stats()
        
        # 類似検索の統計を追加
        if self.use_similarity:
            stats["similarity_enabled"] = True
            stats["similarity_threshold"] = self.similarity_threshold
            stats["similarity_hits"] = self.stats.get("similarity_hits", 0)
            
            # 類似検索を含めた全ヒット数
            total_hits = stats["hits"] + stats.get("similarity_hits", 0)
            
            # ヒット率の再計算
            total_requests = total_hits + stats["misses"]
            if total_requests > 0:
                stats["total_hit_ratio"] = total_hits / total_requests
                stats["similarity_hit_ratio"] = stats.get("similarity_hits", 0) / total_requests
            
        return stats


# デフォルトインスタンス
default_enhanced_cache_manager = None

async def get_enhanced_cache_manager(cache_dir: str = None, ttl_seconds: int = 3600 * 24,
                     max_cache_size_mb: int = 500, enable_cache: bool = True,
                     use_priority: bool = False, use_similarity: bool = True,
                     similarity_threshold: float = 0.85) -> EnhancedAICacheManager:
    """
    拡張キャッシュマネージャーを取得または初期化する
    
    Args:
        cache_dir: キャッシュディレクトリパス
        ttl_seconds: キャッシュエントリの有効期限（秒）
        max_cache_size_mb: キャッシュの最大サイズ（MB）
        enable_cache: キャッシュ機能の有効化フラグ
        use_priority: 優先度ベースのキャッシュ管理を有効化
        use_similarity: 類似クエリ検出を有効化
        similarity_threshold: 類似と判断する閾値 (0-1)
        
    Returns:
        EnhancedAICacheManager: 拡張キャッシュマネージャーインスタンス
    """
    global default_enhanced_cache_manager
    
    if default_enhanced_cache_manager is None:
        default_enhanced_cache_manager = EnhancedAICacheManager(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_cache_size_mb=max_cache_size_mb,
            enable_cache=enable_cache,
            use_priority=use_priority,
            use_similarity=use_similarity,
            similarity_threshold=similarity_threshold
        )
        
    return default_enhanced_cache_manager
