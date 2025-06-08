"""
最適化された類似キャッシュ検索モジュール

高速なエンベディングとバッチ処理による最適化されたキャッシュ検索機能を提供します。
"""

import logging
import hashlib
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

class OptimizedEmbeddingService:
    """
    効率的なエンベディング生成サービス
    """
    
    def __init__(self, model_path: str = None, memory_cache_size: int = 200):
        """
        初期化
        
        Args:
            model_path: エンベディングモデルのパス
            memory_cache_size: メモリキャッシュのサイズ
        """
        self.model = None
        self.model_loaded = False
        self._lock = asyncio.Lock()
        self.embedding_dim = 384  # デフォルト次元数
        self.memory_cache_size = memory_cache_size
        self._memory_cache = {}
        
        # 非同期でモデルをロード
        asyncio.create_task(self._load_model(model_path))
    
    async def _load_model(self, model_path: str = None):
        """
        エンベディングモデルを非同期でロード
        """
        async with self._lock:
            if self.model_loaded:
                return
                
            try:
                try:
                    # 軽量モデルを優先的に使用
                    from sentence_transformers import SentenceTransformer
                    
                    # 超軽量モデルオプション (優先順)
                    model_options = [
                        "intfloat/multilingual-e5-small-q",  # 量子化（高速）
                        "sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2",  # 軽量
                        "intfloat/multilingual-e5-small",  # 標準
                    ]
                    
                    model_name = model_path or model_options[0]
                    
                    logger.info(f"軽量エンベディングモデルをロード中: {model_name}")
                    self.model = SentenceTransformer(model_name)
                    self.embedding_dim = self.model.get_sentence_embedding_dimension()
                    logger.info(f"エンベディングモデルのロード完了: 次元数 {self.embedding_dim}")
                    
                except ImportError:
                    logger.warning("SentenceTransformers利用不可、フォールバック方式を使用")
                    self._setup_fallback_embedding()
                    
                self.model_loaded = True
                    
            except Exception as e:
                logger.error(f"モデルロードエラー: {e}")
                self._setup_fallback_embedding()
                self.model_loaded = True
    
    def _setup_fallback_embedding(self):
        """フォールバック手法の設定"""
        logger.info("ハッシュベースの簡易エンベディング使用")
        
        def generate_hash_embedding(text: str) -> np.ndarray:
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            hash_array = np.frombuffer(hash_bytes, dtype=np.uint8)
            normalized = hash_array.astype(np.float32) / 255.0
            
            if len(normalized) < self.embedding_dim:
                repeat_count = int(np.ceil(self.embedding_dim / len(normalized)))
                normalized = np.tile(normalized, repeat_count)
                
            return normalized[:self.embedding_dim]
        
        self.model = None
        self._fallback_fn = generate_hash_embedding
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """
        テキストのエンベディングベクトルを取得
        """
        if not self.model_loaded:
            await self._load_model()
            
        try:
            # キャッシュキーの生成
            cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
            
            # メモリキャッシュから取得
            if cache_key in self._memory_cache:
                return self._memory_cache[cache_key]
            
            # エンベディング生成
            if self.model:
                vector = self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
            else:
                vector = self._fallback_fn(text)
                
            # メモリキャッシュに格納
            if len(self._memory_cache) >= self.memory_cache_size:
                # 最も古いエントリを削除
                self._memory_cache.pop(next(iter(self._memory_cache)))
            self._memory_cache[cache_key] = vector
            
            return vector
            
        except Exception as e:
            logger.error(f"エンベディング生成エラー: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def batch_cosine_similarity(self, query_embedding: np.ndarray, 
                               stored_embeddings: np.ndarray) -> np.ndarray:
        """
        バッチ処理によるコサイン類似度計算（高速）
        
        Args:
            query_embedding: クエリのエンベディング
            stored_embeddings: 格納されたエンベディングの配列
            
        Returns:
            類似度のnumpy配列
        """
        # クエリのノルム
        query_norm = np.linalg.norm(query_embedding)
        
        # ゼロ除算回避
        if query_norm == 0:
            return np.zeros(len(stored_embeddings))
            
        # 各エンベディングのノルム計算
        norms = np.linalg.norm(stored_embeddings, axis=1)
        
        # ゼロ除算回避
        norms[norms == 0] = 1e-10
            
        # 内積計算
        dot_products = np.dot(stored_embeddings, query_embedding)
            
        # コサイン類似度計算
        similarities = dot_products / (norms * query_norm)
            
        # 0-1の範囲に制限
        return np.clip(similarities, 0.0, 1.0)


class OptimizedSimilarityCache:
    """
    最適化された類似度ベースのキャッシュ検索
    """
    
    def __init__(self, embedding_service: OptimizedEmbeddingService, 
                 cache_dir: Union[str, Path], similarity_threshold: float = 0.85,
                 batch_size: int = 50):
        """
        初期化
        
        Args:
            embedding_service: エンベディングサービス
            cache_dir: キャッシュディレクトリ
            similarity_threshold: 類似度閾値
            batch_size: 検索バッチサイズ
        """
        self.embedding_service = embedding_service
        self.cache_dir = Path(cache_dir)
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        
        # キャッシュデータ
        self.embedding_cache = {}  # キャッシュキー: エンベディング
        self._query_hash_cache = {}  # クエリハッシュ: キャッシュキー
        
        # キャッシュファイルパス
        os.makedirs(self.cache_dir, exist_ok=True)
        self.embedding_cache_file = self.cache_dir / "optimized_embedding_cache.json"
        
        # キャッシュロード
        self._load_embedding_cache()
    
    def _load_embedding_cache(self):
        """埋め込みキャッシュをファイルから読み込み"""
        try:
            if self.embedding_cache_file.exists():
                with open(self.embedding_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.embedding_cache = data.get('embeddings', {})
                    self._query_hash_cache = data.get('query_hashes', {})
                logger.info(f"埋め込みキャッシュをロード: {len(self.embedding_cache)}エントリ")
        except Exception as e:
            logger.error(f"キャッシュ読み込みエラー: {e}")
            self.embedding_cache = {}
            self._query_hash_cache = {}
    
    async def _save_embedding_cache(self):
        """埋め込みキャッシュをファイルに保存"""
        try:
            # シリアライズ可能なデータに変換
            serializable_cache = {}
            for key, embedding in self.embedding_cache.items():
                if isinstance(embedding, np.ndarray):
                    serializable_cache[key] = embedding.tolist()
                else:
                    serializable_cache[key] = embedding
            
            # キャッシュデータをまとめる
            cache_data = {
                'embeddings': serializable_cache,
                'query_hashes': self._query_hash_cache
            }
                
            # ファイルに保存
            with open(self.embedding_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
                
            logger.debug(f"埋め込みキャッシュを保存: {len(serializable_cache)}エントリ")
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")
    
    async def add_query_embedding(self, cache_key: str, query: str) -> bool:
        """クエリのエンベディングをキャッシュに追加"""
        try:
            # クエリハッシュの生成
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            
            # クエリのエンベディングを取得
            embedding = await self.embedding_service.get_embedding(query)
            
            # キャッシュに追加
            self.embedding_cache[cache_key] = embedding.tolist()
            self._query_hash_cache[query_hash] = cache_key
            
            # 定期的にキャッシュ保存
            if len(self.embedding_cache) % 20 == 0:
                await self._save_embedding_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"エンベディング追加エラー: {e}")
            return False
    
    async def find_similar_cache(self, query: str, 
                               threshold: Optional[float] = None) -> Tuple[Optional[str], float]:
        """類似したキャッシュエントリを検索（最適化版）"""
        if not self.embedding_cache:
            return None, 0.0
            
        threshold = threshold or self.similarity_threshold
            
        try:
            # 高速検索のためのハッシュキャッシュ
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            
            # ハッシュキャッシュで完全一致をチェック（最速）
            if query_hash in self._query_hash_cache:
                cache_key = self._query_hash_cache[query_hash]
                if cache_key in self.embedding_cache:
                    return cache_key, 1.0
            
            # クエリのエンベディング取得
            query_embedding = await self.embedding_service.get_embedding(query)
            
            best_key = None
            best_similarity = 0.0
            
            # キャッシュデータのバッチ処理
            keys = list(self.embedding_cache.keys())
            
            # キャッシュサイズが少ない場合は一括処理（最も効率的）
            if len(keys) <= self.batch_size:
                embeddings = []
                for key in keys:
                    embedding = self.embedding_cache[key]
                    if isinstance(embedding, list):
                        embedding = np.array(embedding, dtype=np.float32)
                    embeddings.append(embedding)
                
                if embeddings:
                    embeddings_array = np.array(embeddings)
                    similarities = self.embedding_service.batch_cosine_similarity(
                        query_embedding, embeddings_array)
                    
                    # 最良の一致を見つける
                    for i, sim in enumerate(similarities):
                        if sim > threshold and sim > best_similarity:
                            best_similarity = float(sim)
                            best_key = keys[i]
            
            # 大きなキャッシュはバッチ処理
            else:
                for i in range(0, len(keys), self.batch_size):
                    batch_keys = keys[i:i+self.batch_size]
                    batch_embeddings = []
                    
                    for key in batch_keys:
                        embedding = self.embedding_cache[key]
                        if isinstance(embedding, list):
                            embedding = np.array(embedding, dtype=np.float32)
                        batch_embeddings.append(embedding)
                    
                    if batch_embeddings:
                        batch_array = np.array(batch_embeddings)
                        similarities = self.embedding_service.batch_cosine_similarity(
                            query_embedding, batch_array)
                        
                        for j, sim in enumerate(similarities):
                            if sim > threshold and sim > best_similarity:
                                best_similarity = float(sim)
                                best_key = batch_keys[j]
            
            # 高い類似度の場合はハッシュキャッシュに追加
            if best_key is not None and best_similarity > 0.95:
                self._query_hash_cache[query_hash] = best_key
            
            return best_key, best_similarity
            
        except Exception as e:
            logger.error(f"類似キャッシュ検索エラー: {e}")
            return None, 0.0
    
    async def remove_embedding(self, cache_key: str) -> bool:
        """キャッシュキーのエンベディングを削除"""
        try:
            if cache_key in self.embedding_cache:
                # キャッシュから削除
                del self.embedding_cache[cache_key]
                
                # ハッシュキャッシュから逆引き削除
                keys_to_remove = []
                for query_hash, key in self._query_hash_cache.items():
                    if key == cache_key:
                        keys_to_remove.append(query_hash)
                
                for query_hash in keys_to_remove:
                    del self._query_hash_cache[query_hash]
                
                # キャッシュ保存
                await self._save_embedding_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"エンベディング削除エラー: {e}")
            return False


# シングルトンインスタンス
_cached_embedding_service = None
_cached_similarity_cache = None

async def get_optimized_similarity_cache(cache_dir: str = None, 
                                       similarity_threshold: float = 0.85) -> OptimizedSimilarityCache:
    """
    最適化された類似キャッシュインスタンスを取得（シングルトン）
    
    Args:
        cache_dir: キャッシュディレクトリ
        similarity_threshold: 類似度閾値
        
    Returns:
        OptimizedSimilarityCache: 類似キャッシュインスタンス
    """
    global _cached_embedding_service, _cached_similarity_cache
    
    if _cached_similarity_cache is None:
        if cache_dir is None:
            # デフォルトのキャッシュディレクトリ
            cache_dir = Path.home() / ".ai_cache"
        
        # キャッシュディレクトリを作成
        os.makedirs(cache_dir, exist_ok=True)
        
        # エンベディングサービス初期化
        if _cached_embedding_service is None:
            _cached_embedding_service = OptimizedEmbeddingService()
        
        # 類似キャッシュ初期化
        _cached_similarity_cache = OptimizedSimilarityCache(
            embedding_service=_cached_embedding_service,
            cache_dir=cache_dir,
            similarity_threshold=similarity_threshold
        )
    
    return _cached_similarity_cache
