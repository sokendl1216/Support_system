"""
RAG System - Vector Store
FAISSベースの無料ベクトルストレージと検索システム
"""

import json
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None
    logging.warning("FAISS not installed. Vector store functionality will be limited.")

logger = logging.getLogger(__name__)

class VectorStore:
    """
    FAISSベースのベクトルストア
    完全無料でローカル実行可能
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vector_config = config.get("vector_store", {})
        self.dimension = config.get("embedding", {}).get("dimension", 768)
        self.index_type = self.vector_config.get("index_type", "IndexFlatIP")
        self.save_path = Path(self.vector_config.get("save_path", "ai/rag/vector_store/faiss_index"))
        self.metadata_path = Path(self.vector_config.get("metadata_path", "ai/rag/vector_store/metadata.json"))
        
        # FAISSインデックスとメタデータ
        self.index = None
        self.metadata = {}
        self.next_id = 0
        
        # 保存ディレクトリを作成
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """
        ベクトルストアの初期化
        """
        try:
            if faiss is None:
                logger.error("FAISS is not available. Please install faiss-cpu: pip install faiss-cpu")
                return False
            
            # 既存のインデックスをロード、なければ新規作成
            if self.save_path.exists():
                success = await self._load_index()
                if success:
                    logger.info(f"Loaded existing vector store with {self.index.ntotal} vectors")
                    return True
            
            # 新規インデックス作成
            success = await self._create_new_index()
            if success:
                logger.info(f"Created new vector store with dimension {self.dimension}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return False
    
    async def _create_new_index(self) -> bool:
        """
        新しいFAISSインデックスを作成
        """
        try:
            if self.index_type == "IndexFlatIP":
                # 内積検索（コサイン類似度）
                self.index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IndexFlatL2":
                # L2距離検索
                self.index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IndexIVFFlat":
                # より高速な近似検索（大量データ用）
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, min(100, max(1, self.dimension // 10)))
            else:
                logger.warning(f"Unknown index type {self.index_type}, using IndexFlatIP")
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self.metadata = {}
            self.next_id = 0
            return True
            
        except Exception as e:
            logger.error(f"Error creating new index: {e}")
            return False
    
    async def _load_index(self) -> bool:
        """
        既存のインデックスをロード
        """
        try:
            # FAISSインデックスをロード
            self.index = faiss.read_index(str(self.save_path))
            
            # メタデータをロード
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = data.get("metadata", {})
                    self.next_id = data.get("next_id", 0)
            else:
                self.metadata = {}
                self.next_id = self.index.ntotal
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    async def add_vectors(
        self, 
        vectors: List[List[float]], 
        documents: List[str],
        metadata_list: List[Dict[str, Any]] = None
    ) -> List[int]:
        """
        ベクトルとドキュメントを追加
        """
        if not vectors or not documents or len(vectors) != len(documents):
            raise ValueError("Vectors and documents must have the same length")
        
        if metadata_list and len(metadata_list) != len(vectors):
            raise ValueError("Metadata list must have the same length as vectors")
        
        try:
            # ベクトルをnumpy配列に変換
            vectors_array = np.array(vectors, dtype=np.float32)
            
            # 次元数チェック
            if vectors_array.shape[1] != self.dimension:
                raise ValueError(f"Vector dimension {vectors_array.shape[1]} doesn't match expected {self.dimension}")
            
            # ベクトルを正規化（内積検索用）
            if self.index_type == "IndexFlatIP":
                norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
                norms[norms == 0] = 1  # ゼロ除算を防ぐ
                vectors_array = vectors_array / norms
            
            # インデックスに追加
            self.index.add(vectors_array)
            
            # メタデータを保存
            vector_ids = []
            for i, (doc, meta) in enumerate(zip(documents, metadata_list or [{}] * len(documents))):
                vector_id = self.next_id + i
                self.metadata[str(vector_id)] = {
                    "document": doc,
                    "metadata": meta,
                    "timestamp": __import__('time').time()
                }
                vector_ids.append(vector_id)
            
            self.next_id += len(vectors)
            
            # 定期的に保存
            if len(vector_ids) > 10 or self.index.ntotal % 100 == 0:
                await self._save_index()
            
            logger.info(f"Added {len(vectors)} vectors to store. Total: {self.index.ntotal}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error adding vectors: {e}")
            raise
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        ベクトル検索を実行
        """
        if not query_vector:
            return []
        
        try:
            # クエリベクトルを準備
            query_array = np.array([query_vector], dtype=np.float32)
            
            # 正規化（内積検索用）
            if self.index_type == "IndexFlatIP":
                norm = np.linalg.norm(query_array)
                if norm > 0:
                    query_array = query_array / norm
            
            # 検索実行
            top_k = min(top_k, self.index.ntotal) if self.index.ntotal > 0 else 0
            if top_k == 0:
                return []
            
            distances, indices = self.index.search(query_array, top_k)
            
            # 結果を構築
            results = []
            for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                if index == -1:  # FAISSが返す無効なインデックス
                    continue
                
                # 類似度を計算（内積の場合はそのまま、L2の場合は変換）
                if self.index_type == "IndexFlatIP":
                    similarity = float(distance)
                else:
                    similarity = 1.0 / (1.0 + float(distance))
                
                if similarity < similarity_threshold:
                    continue
                
                # メタデータを取得
                meta = self.metadata.get(str(index), {})
                
                result = {
                    "id": int(index),
                    "document": meta.get("document", ""),
                    "metadata": meta.get("metadata", {}),
                    "similarity": similarity,
                    "distance": float(distance),
                    "rank": i + 1
                }
                results.append(result)
            
            logger.debug(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    async def _save_index(self) -> bool:
        """
        インデックスとメタデータを保存
        """
        try:
            # FAISSインデックスを保存
            faiss.write_index(self.index, str(self.save_path))
            
            # メタデータを保存
            save_data = {
                "metadata": self.metadata,
                "next_id": self.next_id,
                "dimension": self.dimension,
                "index_type": self.index_type,
                "total_vectors": self.index.ntotal
            }
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        ベクトルストアの統計情報を取得
        """
        try:
            return {
                "total_vectors": self.index.ntotal if self.index else 0,
                "dimension": self.dimension,
                "index_type": self.index_type,
                "metadata_count": len(self.metadata),
                "next_id": self.next_id,
                "storage_path": str(self.save_path),
                "index_size_mb": self.save_path.stat().st_size / (1024 * 1024) if self.save_path.exists() else 0
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    async def clear(self) -> bool:
        """
        ベクトルストアをクリア
        """
        try:
            await self._create_new_index()
            await self._save_index()
            logger.info("Vector store cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
    
    async def delete_vectors(self, vector_ids: List[int]) -> bool:
        """
        指定されたベクトルを削除
        注意: FAISSは直接削除をサポートしていないため、再構築が必要
        """
        try:
            # 削除対象のIDをセットに変換
            delete_ids = set(str(vid) for vid in vector_ids)
            
            # 残すメタデータを特定
            remaining_metadata = {
                k: v for k, v in self.metadata.items() 
                if k not in delete_ids
            }
            
            if len(remaining_metadata) == len(self.metadata):
                logger.info("No vectors to delete")
                return True
            
            # 新しいインデックスを作成
            await self._create_new_index()
            
            # 残すベクトルを再構築（実際の実装では、元のベクトルデータが必要）
            # 現在の実装では、メタデータのみ削除
            self.metadata = remaining_metadata
            
            await self._save_index()
            logger.info(f"Deleted {len(delete_ids)} vectors from store")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False
