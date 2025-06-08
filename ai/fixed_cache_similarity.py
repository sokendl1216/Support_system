"""
類似クエリ検出によるキャッシュ最適化モジュール（修正版）

このモジュールは、意味的に類似したクエリを検出し、既存のキャッシュを
効率的に再利用するための機能を提供します。構文エラーを修正し、パフォーマンスを向上させました。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import json
from pathlib import Path
import asyncio
import os
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    文字列のエンベディングを生成するサービス（最適化版）
    """
    
    def __init__(self, model_path: str = None, memory_cache_size: int = 500):
        """
        初期化
        
        Args:
            model_path: エンベディングモデルのパス（Noneの場合は適切なモデルを自動選択）
            memory_cache_size: メモリ内エンベディングキャッシュの最大サイズ
        """
        self.model = None
        self.model_loaded = False
        self._lock = asyncio.Lock()
        self.embedding_dim = 384  # デフォルトの埋め込み次元数
        self._embedding_memory_cache = {}
        self._memory_cache_size = memory_cache_size
        self._executor = ThreadPoolExecutor(max_workers=2)  # モデル推論用のスレッドプール

        # 初期化後に非同期でモデルをロード
        asyncio.create_task(self._load_model(model_path))
        
    async def _load_model(self, model_path: str = None):
        """
        エンベディングモデルの非同期ロード
        """
        async with self._lock:
            if self.model_loaded:
                return
                
            try:
                # 軽量モデルを優先的に使用
                try:
                    from sentence_transformers import SentenceTransformer
                    
                    # 日本語対応の超軽量モデル (優先順)
                    model_options = [
                        "intfloat/multilingual-e5-small-q",  # 量子化されたバージョン（高速）
                        "sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2",  # より軽量なバージョン
                        "intfloat/multilingual-e5-small",  # 多言語対応の軽量モデル
                        "pkshatech/simcse-ja-bert-base-clcmlp"  # 日本語特化
                    ]
                    
                    model_name = model_options[0]  # 最も軽量なモデルをデフォルトに
                    
                    if model_path:
                        if os.path.exists(model_path):
                            model_name = model_path
                        else:
                            model_name = model_path
                    
                    logger.info(f"エンベディングモデルをロード中: {model_name}")
                    
                    # モデルロードを別スレッドで実行（UIブロッキング防止）
                    loop = asyncio.get_event_loop()
                    self.model = await loop.run_in_executor(
                        self._executor, 
                        lambda: SentenceTransformer(model_name)
                    )
                    
                    self.embedding_dim = self.model.get_sentence_embedding_dimension()
                    logger.info(f"エンベディングモデルのロード完了: 次元数 {self.embedding_dim}")
                    
                except ImportError:
                    logger.warning("SentenceTransformersが利用できないため、フォールバック方式を使用します")
                    self._setup_fallback_embedding()
                    
            except Exception as e:
                logger.error(f"エンベディングモデルのロードエラー: {e}")
                self._setup_fallback_embedding()
                
            self.model_loaded = True
    
    def _setup_fallback_embedding(self):
        """
        外部ライブラリが利用できない場合のフォールバック手法を設定
        """
        import hashlib
        
        logger.info("簡易エンベディング生成を使用")
        self.model = None
        
        # 擬似エンベディング生成用のハッシュ関数
        def generate_hash_embedding(text: str) -> np.ndarray:
            """
            ハッシュベースの簡易エンベディング生成
            """
            # テキストのハッシュ値を取得
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            # ハッシュ値からFloat32の配列を生成
            hash_array = np.frombuffer(hash_bytes, dtype=np.uint8)
            
            # 0-1の範囲に正規化
            normalized = hash_array.astype(np.float32) / 255.0
            
            # 次元数を調整
            if len(normalized) < self.embedding_dim:
                # 不足分をリピートで埋める
                repeat_count = int(np.ceil(self.embedding_dim / len(normalized)))
                normalized = np.tile(normalized, repeat_count)
                
            # 次元に切り詰め
            return normalized[:self.embedding_dim]
        
        # 重み付きn-gramベースでハッシュを生成する関数
        self._fallback_embedding_fn = generate_hash_embedding
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """
        テキストのエンベディングベクトルを取得
        
        Args:
            text: 埋め込みを生成するテキスト
            
        Returns:
            np.ndarray: 埋め込みベクトル
        """
        # モデルのロードを待機
        if not self.model_loaded:
            await self._load_model()
        
        try:
            # キャッシュキーの生成（同じテキストに対する再計算を避けるため）
            cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
            
            # メモリ内エンベディングキャッシュをチェック
            if cache_key in self._embedding_memory_cache:
                return self._embedding_memory_cache[cache_key]
            
            # エンベディング生成
            if self.model:
                # 別スレッドでモデル推論を実行（UIブロッキング防止）
                loop = asyncio.get_event_loop()
                vector = await loop.run_in_executor(
                    self._executor,
                    lambda: self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
                )
            else:
                # フォールバック手法を使用
                vector = self._fallback_embedding_fn(text)
            
            # メモリキャッシュ管理（LRUキャッシュ）
            if len(self._embedding_memory_cache) >= self._memory_cache_size:
                # 最も古いエントリを削除
                self._embedding_memory_cache.pop(next(iter(self._embedding_memory_cache)))
                
            # キャッシュに保存
            self._embedding_memory_cache[cache_key] = vector
            
            return vector
                
        except Exception as e:
            logger.error(f"エンベディング生成エラー: {e}")
            # エラーの場合はゼロベクトルを返す
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def batch_calculate_similarity(self, query_embedding: np.ndarray, stored_embeddings: np.ndarray) -> np.ndarray:
        """
        バッチ処理によるコサイン類似度計算
        
        Args:
            query_embedding: クエリのエンベディング
            stored_embeddings: 格納されたエンベディングの配列
            
        Returns:
            np.ndarray: 類似度スコアの配列
        """
        # ゼロ除算を防ぐための小さな値
        epsilon = 1e-10
        
        # クエリのノルム
        query_norm = np.linalg.norm(query_embedding) + epsilon
        
        # 全エンベディングのノルムを一度に計算
        norms = np.linalg.norm(stored_embeddings, axis=1) + epsilon
        
        # 全てのドット積を一度に計算
        dots = np.dot(stored_embeddings, query_embedding)
        
        # コサイン類似度を一度に計算
        similarities = dots / (norms * query_norm)
        
        # 0-1の範囲に制限
        return np.clip(similarities, 0.0, 1.0)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        2つのエンベディング間のコサイン類似度を計算
        
        Args:
            embedding1: 1つ目のエンベディング
            embedding2: 2つ目のエンベディング
            
        Returns:
            float: コサイン類似度 (0-1)
        """
        # バッチ処理を利用
        similarity = self.batch_calculate_similarity(embedding1, np.array([embedding2]))
        return float(similarity[0])


class SimilarityCache:
    """
    類似度ベースのキャッシュ検索を実現するクラス（最適化版）
    """
    
    def __init__(self, embedding_service: EmbeddingService, cache_dir: Path, 
                 similarity_threshold: float = 0.85, batch_size: int = 50):
        """
        初期化
        
        Args:
            embedding_service: エンベディングサービス
            cache_dir: キャッシュディレクトリのパス
            similarity_threshold: 類似と判断する閾値 (0-1)
            batch_size: 一度に処理するバッチのサイズ
        """
        self.embedding_service = embedding_service
        self.cache_dir = Path(cache_dir)
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        
        # キャッシュデータ
        self.embedding_cache = {}  # キャッシュキー: エンベディング
        self._query_hash_cache = {}  # クエリハッシュ: キャッシュキー
        
        # キャッシュディレクトリの作成
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # キャッシュファイルパス
        self.embedding_cache_file = self.cache_dir / "embedding_cache.json"
        self.hash_cache_file = self.cache_dir / "query_hash_cache.json"
        
        # 埋め込みキャッシュを読み込み
        self._load_embedding_cache()
        
    def _load_embedding_cache(self):
        """
        埋め込みキャッシュをファイルから読み込み
        """
        try:
            if self.embedding_cache_file.exists():
                with open(self.embedding_cache_file, 'r', encoding='utf-8') as f:
                    self.embedding_cache = json.load(f)
                logger.info(f"埋め込みキャッシュを読み込みました: {len(self.embedding_cache)}エントリ")
                
            if self.hash_cache_file.exists():
                with open(self.hash_cache_file, 'r', encoding='utf-8') as f:
                    self._query_hash_cache = json.load(f)
                logger.info(f"クエリハッシュキャッシュを読み込みました: {len(self._query_hash_cache)}エントリ")
                
        except Exception as e:
            logger.error(f"埋め込みキャッシュ読み込みエラー: {e}")
            self.embedding_cache = {}
            self._query_hash_cache = {}
            
    async def _save_embedding_cache(self):
        """
        埋め込みキャッシュをファイルに保存
        """
        try:
            # サイズ削減のため、保存前に埋め込みをリスト形式に変換
            serializable_cache = {}
            for key, embedding in self.embedding_cache.items():
                if isinstance(embedding, np.ndarray):
                    serializable_cache[key] = embedding.tolist()
                else:
                    serializable_cache[key] = embedding
                    
            with open(self.embedding_cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_cache, f)
                
            # ハッシュキャッシュの保存
            with open(self.hash_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._query_hash_cache, f)
                
            logger.debug(f"埋め込みキャッシュを保存しました: {len(serializable_cache)}エントリ")
            
        except Exception as e:
            logger.error(f"埋め込みキャッシュ保存エラー: {e}")
    
    async def add_query_embedding(self, cache_key: str, query: str) -> bool:
        """
        クエリのエンベディングをキャッシュに追加
        
        Args:
            cache_key: キャッシュキー
            query: クエリテキスト
            
        Returns:
            bool: 成功したか
        """
        try:
            # クエリハッシュの生成
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            
            # クエリのエンベディングを取得
            embedding = await self.embedding_service.get_embedding(query)
            
            # キャッシュに追加
            self.embedding_cache[cache_key] = embedding.tolist()
            self._query_hash_cache[query_hash] = cache_key
            
            # 定期的にキャッシュ保存
            if len(self.embedding_cache) % 10 == 0:
                await self._save_embedding_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"クエリエンベディング追加エラー: {e}")
            return False
    
    async def find_similar_cache(self, query: str,
                          threshold: Optional[float] = None) -> Tuple[Optional[str], float]:
        """
        類似したキャッシュエントリを検索（最適化版）
        
        Args:
            query: 検索クエリ
            threshold: 類似度閾値 (Noneの場合はデフォルト値を使用)
            
        Returns:
            Tuple[Optional[str], float]: (最も類似したキャッシュキー, 類似度)
                                         類似したものがない場合は (None, 0.0)
        """
        if not self.embedding_cache:
            return None, 0.0
            
        if threshold is None:
            threshold = self.similarity_threshold
            
        start_time = time.time()
            
        try:
            # 高速検索のためのハッシュキャッシュ
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            
            # 完全一致のキャッシュがあるか確認（高速ショートカット）
            if query_hash in self._query_hash_cache:
                cache_key = self._query_hash_cache[query_hash]
                if cache_key in self.embedding_cache:
                    return cache_key, 1.0
            
            # クエリのエンベディング
            query_embedding = await self.embedding_service.get_embedding(query)
            
            best_key = None
            best_similarity = 0.0
            
            # キャッシュサイズによる処理方法の最適化
            keys = list(self.embedding_cache.keys())
            
            # サイズが小さい場合は一括バッチ処理
            if len(keys) <= self.batch_size:
                batch_embeddings = []
                for key in keys:
                    stored_embedding = self.embedding_cache[key]
                    if isinstance(stored_embedding, list):
                        stored_embedding = np.array(stored_embedding, dtype=np.float32)
                    batch_embeddings.append(stored_embedding)
                
                if batch_embeddings:
                    # バッチ全体の類似度を一度に計算（高速）
                    batch_array = np.array(batch_embeddings)
                    similarities = self.embedding_service.batch_calculate_similarity(
                        query_embedding, batch_array)
                    
                    # 最良の一致を見つける
                    for i, sim in enumerate(similarities):
                        if sim > threshold and sim > best_similarity:
                            best_similarity = float(sim)
                            best_key = keys[i]
            
            # 大きなキャッシュはバッチ分割処理
            else:
                for i in range(0, len(keys), self.batch_size):
                    batch_keys = keys[i:i+self.batch_size]
                    batch_embeddings = []
                    
                    for key in batch_keys:
                        stored_embedding = self.embedding_cache[key]
                        if isinstance(stored_embedding, list):
                            stored_embedding = np.array(stored_embedding, dtype=np.float32)
                        batch_embeddings.append(stored_embedding)
                    
                    if batch_embeddings:
                        batch_array = np.array(batch_embeddings)
                        similarities = self.embedding_service.batch_calculate_similarity(
                            query_embedding, batch_array)
                        
                        for j, sim in enumerate(similarities):
                            if sim > threshold and sim > best_similarity:
                                best_similarity = float(sim)
                                best_key = batch_keys[j]
            
            # 計算速度の表示（デバッグ用）
            elapsed = time.time() - start_time
            logger.debug(f"類似検索完了: {elapsed:.4f}秒, キャッシュサイズ: {len(keys)}")
            
            # 高い類似度の場合はハッシュキャッシュに追加（次回の高速化）
            if best_key is not None and best_similarity > 0.95:
                self._query_hash_cache[query_hash] = best_key
            
            return best_key, best_similarity
            
        except Exception as e:
            logger.error(f"類似キャッシュ検索エラー: {e}")
            return None, 0.0
            
    async def update_embedding_for_key(self, cache_key: str, query: str) -> bool:
        """
        既存キャッシュキーのエンベディングを更新
        
        Args:
            cache_key: キャッシュキー
            query: 新しいクエリテキスト
            
        Returns:
            bool: 成功したか
        """
        return await self.add_query_embedding(cache_key, query)
        
    async def remove_embedding(self, cache_key: str) -> bool:
        """
        キャッシュキーのエンベディングを削除
        
        Args:
            cache_key: 削除するキャッシュキー
            
        Returns:
            bool: 成功したか
        """
        try:
            if cache_key in self.embedding_cache:
                del self.embedding_cache[cache_key]
                
                # ハッシュキャッシュからも関連するエントリを削除
                keys_to_remove = []
                for query_hash, key in self._query_hash_cache.items():
                    if key == cache_key:
                        keys_to_remove.append(query_hash)
                
                for query_hash in keys_to_remove:
                    del self._query_hash_cache[query_hash]
                
                # 削除後にキャッシュを保存
                await self._save_embedding_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"エンベディング削除エラー: {e}")
            return False

# シングルトンインスタンス管理
_cached_embedding_service = None
_cached_similarity_cache = None

async def get_similarity_cache(cache_dir: str = None, similarity_threshold: float = 0.85) -> SimilarityCache:
    """
    類似キャッシュインスタンスを取得（シングルトン）
    
    Args:
        cache_dir: キャッシュディレクトリ
        similarity_threshold: 類似度閾値
        
    Returns:
        SimilarityCache: 類似キャッシュインスタンス
    """
    global _cached_embedding_service, _cached_similarity_cache
    
    if _cached_similarity_cache is None:
        if cache_dir is None:
            # デフォルトのキャッシュディレクトリ
            cache_dir = Path.home() / ".ai_cache"
        
        # エンベディングサービスの初期化
        if _cached_embedding_service is None:
            _cached_embedding_service = EmbeddingService()
        
        # 類似キャッシュの初期化
        _cached_similarity_cache = SimilarityCache(
            embedding_service=_cached_embedding_service,
            cache_dir=cache_dir,
            similarity_threshold=similarity_threshold
        )
    
    return _cached_similarity_cache
