"""
RAG System - Embedding Service
Ollamaベースの無料ベクトル埋め込みサービス
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
import aiohttp
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Ollamaを使用したベクトル埋め込みサービス
    完全無料のnomic-embed-textモデルを使用
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embedding_config = config.get("embedding", {})
        self.base_url = self.embedding_config.get("base_url", "http://localhost:11434")
        self.model = self.embedding_config.get("model", "nomic-embed-text")
        self.dimension = self.embedding_config.get("dimension", 768)
        self.batch_size = self.embedding_config.get("batch_size", 32)
        self.timeout = self.embedding_config.get("timeout", 30)
        
    async def initialize(self) -> bool:
        """
        埋め込みモデルの初期化と確認
        """
        try:
            # モデルが利用可能かチェック
            if not await self._check_model_availability():
                logger.warning(f"Embedding model {self.model} not available, attempting to pull...")
                if not await self._pull_model():
                    logger.error(f"Failed to pull embedding model {self.model}")
                    return False
            
            # テスト埋め込みを実行
            test_embedding = await self.embed_text("test")
            if test_embedding is not None:
                logger.info(f"Embedding service initialized successfully with dimension {len(test_embedding)}")
                return True
            else:
                logger.error("Failed to generate test embedding")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            return False
    
    async def _check_model_availability(self) -> bool:
        """
        モデルの利用可能性をチェック
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        models_data = await response.json()
                        available_models = [model["name"] for model in models_data.get("models", [])]
                        return any(self.model in model_name for model_name in available_models)
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def _pull_model(self) -> bool:
        """
        埋め込みモデルをプル
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                pull_data = {"name": self.model}
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=pull_data
                ) as response:
                    if response.status == 200:
                        # プル進行状況を監視
                        async for line in response.content:
                            if line:
                                try:
                                    progress = json.loads(line.decode())
                                    if progress.get("status") == "success":
                                        logger.info(f"Successfully pulled embedding model {self.model}")
                                        return True
                                except json.JSONDecodeError:
                                    continue
            return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        単一テキストの埋め込みを生成
        """
        if not text or not text.strip():
            return None
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                embed_data = {
                    "model": self.model,
                    "prompt": text.strip()
                }
                
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json=embed_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        embedding = result.get("embedding")
                        if embedding and len(embedding) > 0:
                            return embedding
                    else:
                        logger.error(f"Embedding request failed: {response.status}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        複数テキストの埋め込みを生成（バッチ処理）
        """
        if not texts:
            return []
        
        # 空のテキストをフィルタリング
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
        if not valid_texts:
            return [None] * len(texts)
        
        results = [None] * len(texts)
        
        # バッチサイズで分割して処理
        for i in range(0, len(valid_texts), self.batch_size):
            batch = valid_texts[i:i + self.batch_size]
            batch_tasks = []
            
            for original_idx, text in batch:
                task = asyncio.create_task(self.embed_text(text))
                batch_tasks.append((original_idx, task))
            
            # バッチ内の並列処理
            for original_idx, task in batch_tasks:
                try:
                    embedding = await task
                    results[original_idx] = embedding
                except Exception as e:
                    logger.error(f"Error in batch embedding for index {original_idx}: {e}")
                    results[original_idx] = None
        
        return results
    
    async def embed_query(self, query: str) -> Optional[List[float]]:
        """
        クエリの埋め込みを生成（検索用に最適化）
        """
        if not query or not query.strip():
            return None
        
        # クエリを検索に適した形式に前処理
        processed_query = self._preprocess_query(query)
        return await self.embed_text(processed_query)
    
    def _preprocess_query(self, query: str) -> str:
        """
        検索クエリの前処理
        """
        # 基本的な前処理
        query = query.strip()
        
        # 検索に適した形式に変換
        if not query.endswith("?") and not query.endswith("."):
            query += "."
        
        return query
    
    def get_dimension(self) -> int:
        """
        埋め込みベクトルの次元数を取得
        """
        return self.dimension
    
    async def health_check(self) -> Dict[str, Any]:
        """
        埋め込みサービスの健康状態をチェック
        """
        try:
            # モデル利用可能性チェック
            model_available = await self._check_model_availability()
            
            # テスト埋め込み生成
            test_embedding = None
            if model_available:
                test_embedding = await self.embed_text("health check test")
            
            return {
                "status": "healthy" if model_available and test_embedding else "unhealthy",
                "model": self.model,
                "model_available": model_available,
                "embedding_dimension": len(test_embedding) if test_embedding else 0,
                "base_url": self.base_url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model,
                "base_url": self.base_url
            }
