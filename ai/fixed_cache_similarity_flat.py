"""
類似クエリ検出によるキャッシュ最適化モジュール（修正版）

このモジュールは、意味的に類似したクエリを検出し、既存のキャッシュを
効率的に再利用するための機能を提供します。
"""

import logging
import hashlib
import numpy as np
import json
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    文字列のエンベディングを生成するサービス
    """
    
    def __init__(self, model_path: str = None):
        """
        初期化
        
        Args:
            model_path: エンベディングモデルのパス（Noneの場合は適切なモデルを自動選択）
        """
        self.model = None
        self.model_loaded = False
        self._lock = asyncio.Lock()
        self.embedding_dim = 384  # デフォルトの埋め込み次元数
        self._embedding_memory_cache = {}  # メモリ内キャッシュ

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
                    
                    # 日本語対応の超軽量モデル
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
                    self.model = SentenceTransformer(model_name)
                    self.model_loaded = True
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
        self.model_loaded = True
        
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
            
            if self.model:
                # 正規のエンベディングモデルを使用
                vector = self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
                
                # メモリキャッシュに保存（次回のアクセスを高速化、最大100エントリまで）
                if len(self._embedding_memory_cache) > 100:
                    # 最も古いエントリを削除
                    self._embedding_memory_cache.pop(next(iter(self._embedding_memory_cache)))
                self._embedding_memory_cache[cache_key] = vector
                
                return vector
            else:
                # フォールバック手法を使用
                return self._fallback_embedding_fn(text)
                
        except Exception as e:
            logger.error(f"エンベディング生成エラー: {e}")
            # エラーの場合はゼロベクトルを返す
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        2つのエンベディング間のコサイン類似度を計算
        
        Args:
            embedding1: 1つ目のエンベディング
            embedding2: 2つ目のエンベディング
            
        Returns:
            float: コサイン類似度 (0-1)
        """
        # ゼロベクトルのチェック
        if np.all(embedding1 == 0) or np.all(embedding2 == 0):
            return 0.0
            
        # ノルム計算
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        # コサイン類似度
        cos_sim = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # 0-1の範囲に制限
        return max(0.0, min(1.0, cos_sim))


class SimilarityCache:
    """
    類似度ベースのキャッシュ検索を実現するクラス
    """
    
    def __init__(self, embedding_service: EmbeddingService, cache_dir: Path, 
                 similarity_threshold: float = 0.85):
        """
        初期化
        
        Args:
            embedding_service: エンベディングサービス
            cache_dir: キャッシュディレクトリのパス
            similarity_threshold: 類似と判断する閾値 (0-1)
        """
        self.embedding_service = embedding_service
        self.cache_dir = cache_dir
        self.similarity_threshold = similarity_threshold
        self.embedding_cache = {}  # キャッシュキー: エンベディング
        self._query_hash_cache = {}  # クエリハッシュ: キャッシュキー
        
        # キャッシュファイルパス
        self.embedding_cache_file = cache_dir / "embedding_cache.json"
        
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
                
        except Exception as e:
            logger.error(f"埋め込みキャッシュ読み込みエラー: {e}")
            self.embedding_cache = {}
            
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
            # クエリのエンベディングを取得
            embedding = await self.embedding_service.get_embedding(query)
            
            # キャッシュに追加
            self.embedding_cache[cache_key] = embedding.tolist()
            
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
        類似したキャッシュエントリを検索
        
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
            
        try:
            # 高速検索のためのキャッシュ
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
            
            # 埋め込みキャッシュで類似度検索
            for key, embedding in self.embedding_cache.items():
                # リスト形式なら配列に変換
                if isinstance(embedding, list):
                    embedding = np.array(embedding, dtype=np.float32)
                
                # 類似度を計算
                similarity = self.embedding_service.calculate_similarity(
                    query_embedding, embedding
                )
                
                # 閾値以上かつ最大の類似度を持つキーを記録
                if similarity > threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_key = key
            
            # 結果をキャッシュに保存（次回の高速化のため）
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
                
                # 削除後にキャッシュを保存
                await self._save_embedding_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"エンベディング削除エラー: {e}")
            return False


async def get_similarity_cache(cache_dir: str, similarity_threshold: float = 0.85) -> SimilarityCache:
    """
    類似キャッシュのインスタンスを取得
    
    Args:
        cache_dir: キャッシュディレクトリ
        similarity_threshold: 類似度閾値
        
    Returns:
        SimilarityCache: 類似キャッシュのインスタンス
    """
    # キャッシュディレクトリを作成
    cache_path = Path(cache_dir)
    os.makedirs(cache_path, exist_ok=True)
    
    # エンベディングサービスを初期化
    embedding_service = EmbeddingService()
    
    # 類似キャッシュを初期化
    similarity_cache = SimilarityCache(
        embedding_service=embedding_service,
        cache_dir=cache_path,
        similarity_threshold=similarity_threshold
    )
    
    return similarity_cache
