"""
RAG System - Main RAG Implementation
統合RAGシステム：検索拡張生成システム
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .embedding_service import EmbeddingService
from .vector_store import VectorStore
from .knowledge_base import KnowledgeBaseManager, DocumentChunk
from ..cache_manager import get_cache_manager, AICacheManager
from ..process_monitor import get_process_monitor, AIProcessMonitor, ProcessStatus

logger = logging.getLogger(__name__)

class RAGSearchResult:
    """
    RAG検索結果
    """
    def __init__(
        self,
        chunk: DocumentChunk,
        similarity: float,
        distance: float,
        rank: int,
        vector_id: int = None
    ):
        self.chunk = chunk
        self.similarity = similarity
        self.distance = distance
        self.rank = rank
        self.vector_id = vector_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "content": self.chunk.content,
            "metadata": self.chunk.metadata,
            "similarity": self.similarity,
            "distance": self.distance,
            "rank": self.rank,
            "vector_id": self.vector_id
        }

class RAGSystem:
    """
    統合RAGシステム
    知識ベース検索・適用システム
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.retrieval_config = config.get("retrieval", {})
        self.mode_config = config.get("mode_optimization", {})
        self.cache_config = config.get("cache", {})
        self.monitor_config = config.get("monitor", {})
        
        # コンポーネント初期化
        self.embedding_service = EmbeddingService(config)
        self.vector_store = VectorStore(config)
        self.knowledge_base = KnowledgeBaseManager(config)
        
        # キャッシュシステムとプロセス監視（後で初期化）
        self.cache_manager = None
        self.process_monitor = None
        
        # 状態管理
        self.is_initialized = False
        self.index_status = {
            "total_chunks": 0,
            "indexed_chunks": 0,
            "last_update": 0,
            "needs_reindex": False
        }
        
    async def initialize(self) -> bool:
        """
        RAGシステム全体の初期化
        """
        try:
            logger.info("Initializing RAG system...")
            
            # 各コンポーネントを初期化
            embedding_ok = await self.embedding_service.initialize()
            if not embedding_ok:
                logger.error("Failed to initialize embedding service")
                return False
            
            vector_store_ok = await self.vector_store.initialize()
            if not vector_store_ok:
                logger.error("Failed to initialize vector store")
                return False
            
            knowledge_base_ok = await self.knowledge_base.initialize()
            if not knowledge_base_ok:
                logger.error("Failed to initialize knowledge base")
                return False
                
            # キャッシュシステムの初期化
            try:
                cache_enabled = self.cache_config.get("enabled", True)
                cache_ttl = self.cache_config.get("ttl_seconds", 3600 * 24)  # デフォルト24時間
                cache_max_size = self.cache_config.get("max_size_mb", 500)  # デフォルト500MB
                cache_dir = self.cache_config.get("cache_dir")
                
                self.cache_manager = await get_cache_manager(
                    cache_dir=cache_dir,
                    ttl_seconds=cache_ttl,
                    max_cache_size_mb=cache_max_size,
                    enable_cache=cache_enabled
                )
                logger.info(f"RAG cache system initialized: enabled={cache_enabled}")
            except Exception as cache_error:
                logger.warning(f"Failed to initialize cache system: {cache_error}, proceeding without cache")
                
            # プロセス監視システムの初期化
            try:
                monitor_enabled = self.monitor_config.get("enabled", True)
                if monitor_enabled:
                    cleanup_interval = self.monitor_config.get("cleanup_interval_seconds", 300)
                    process_timeout = self.monitor_config.get("process_timeout_seconds", 600)
                    max_history = self.monitor_config.get("max_history_count", 1000)
                    
                    self.process_monitor = await get_process_monitor(
                        cleanup_interval_seconds=cleanup_interval,
                        process_timeout_seconds=process_timeout,
                        max_history_count=max_history
                    )
                    logger.info("RAG process monitor initialized")
            except Exception as monitor_error:
                logger.warning(f"Failed to initialize process monitor: {monitor_error}, proceeding without monitoring")
            
            # インデックス状態をチェック
            await self._check_index_status()
            
            # 必要に応じて再インデックス
            if self.index_status["needs_reindex"]:
                logger.info("Reindexing required, starting reindex process...")
                await self.reindex_knowledge_base()            
            self.is_initialized = True
            logger.info("RAG system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            return False
            
    async def _check_index_status(self) -> None:
        """
        インデックス状態をチェック
        """
        try:
            # 知識ベースのチャンク数
            chunks = await self.knowledge_base.get_chunks()
            total_chunks = len(chunks)
            
            # ベクトルストアのベクトル数
            vector_stats = await self.vector_store.get_stats()
            indexed_vectors = vector_stats.get("total_vectors", 0)
            
            self.index_status.update({
                "total_chunks": total_chunks,
                "indexed_chunks": indexed_vectors,
                "needs_reindex": total_chunks != indexed_vectors
            })
            
            logger.info(f"Index status: {total_chunks} chunks, {indexed_vectors} vectors indexed")
        except Exception as e:
            logger.error(f"Error checking index status: {e}")
            self.index_status["needs_reindex"] = True
            
    async def search(
        self,
        query: str,
        mode: str = "interactive",
        top_k: int = None,
        similarity_threshold: float = None
    ) -> List[RAGSearchResult]:
        """
        知識ベースを検索
        """
        process_id = None
        
        if not self.is_initialized:
            logger.error("RAG system not initialized")
            return []
        
        if not query or not query.strip():
            return []
        
        try:
            # プロセス監視開始 (利用可能な場合)
            if self.process_monitor:
                process_id = await self.process_monitor.register_process(
                    process_type="rag_search",
                    metadata={"query": query, "mode": mode, "top_k": top_k}
                )
                await self.process_monitor.start_process(process_id)
            
            # キャッシュチェック (利用可能な場合)
            if self.cache_manager:
                cache_key = {
                    "operation": "rag_search",
                    "query": query,
                    "mode": mode,
                    "top_k": top_k,
                    "similarity_threshold": similarity_threshold
                }
                
                cache_hit, cached_results = await self.cache_manager.get_cache(cache_key)
                if cache_hit and cached_results:
                    logger.debug(f"Cache hit for RAG search: {query[:30]}...")
                    
                    # キャッシュから結果を再構築
                    results = []
                    for item in cached_results:
                        chunk = DocumentChunk(
                            chunk_id=item["chunk_id"],
                            content=item["content"],
                            metadata=item["metadata"]
                        )
                        results.append(RAGSearchResult(
                            chunk=chunk,
                            similarity=item["similarity"],
                            distance=item["distance"],
                            rank=item["rank"],
                            vector_id=item["vector_id"]
                        ))
                    
                    # プロセス完了報告
                    if self.process_monitor and process_id:
                        await self.process_monitor.complete_process(
                            process_id,
                            metadata_update={"cache_hit": True, "results_count": len(results)}
                        )
                    
                    return results
            
            # モード別設定を適用
            search_config = self._get_mode_config(mode)
            if top_k is None:
                top_k = search_config.get("top_k", self.retrieval_config.get("top_k", 5))
            if similarity_threshold is None:
                similarity_threshold = search_config.get(
                    "similarity_threshold", 
                    self.retrieval_config.get("similarity_threshold", 0.7)
                )
            
            # 進捗更新
            if self.process_monitor and process_id:
                await self.process_monitor.update_progress(
                    process_id, 0.2, 
                    {"stage": "embedding_query"}
                )
                
            # クエリを埋め込み
            query_embedding = await self.embedding_service.embed_query(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                if self.process_monitor and process_id:
                    await self.process_monitor.fail_process(
                        process_id,
                        error_message="Failed to generate query embedding"
                    )
                return []
            
            # 進捗更新
            if self.process_monitor and process_id:
                await self.process_monitor.update_progress(
                    process_id, 0.4, 
                    {"stage": "vector_search"}
                )
                
            # ベクトル検索を実行
            vector_results = await self.vector_store.search(
                query_vector=query_embedding,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            if not vector_results:
                logger.info("No relevant documents found")
                return []
              # 結果をRAGSearchResultに変換
            search_results = []
            
            # 進捗更新
            if self.process_monitor and process_id:
                await self.process_monitor.update_progress(
                    process_id, 0.6, 
                    {"stage": "process_results", "result_count": len(vector_results)}
                )
                
            for result in vector_results:
                # チャンクを取得
                chunk = await self.knowledge_base.get_chunk_by_id(str(result["id"]))
                if chunk:
                    rag_result = RAGSearchResult(
                        chunk=chunk,
                        similarity=result["similarity"],
                        distance=result["distance"],
                        rank=result["rank"],
                        vector_id=result["id"]
                    )
                    search_results.append(rag_result)
            
            logger.info(f"Found {len(search_results)} relevant documents for query")
            
            # 進捗更新
            if self.process_monitor and process_id:
                await self.process_monitor.update_progress(
                    process_id, 0.8, 
                    {"stage": "applying_optimization", "pre_opt_count": len(search_results)}
                )
                
            # モード別最適化を適用
            optimized_results = await self._apply_mode_optimization(search_results, mode, query)
            
            # キャッシュに結果を保存（利用可能な場合）
            if self.cache_manager:
                # 辞書形式に変換
                cacheable_results = []
                for result in optimized_results:
                    cacheable_results.append({
                        "chunk_id": result.chunk.chunk_id,
                        "content": result.chunk.content,
                        "metadata": result.chunk.metadata,
                        "similarity": result.similarity,
                        "distance": result.distance,
                        "rank": result.rank,
                        "vector_id": result.vector_id
                    })
                
                # キャッシュキー
                cache_key = {
                    "operation": "rag_search",
                    "query": query,
                    "mode": mode,
                    "top_k": top_k,
                    "similarity_threshold": similarity_threshold
                }
                
                # 非同期でキャッシュに保存
                asyncio.create_task(self.cache_manager.set_cache(cache_key, cacheable_results))
            
            # プロセス完了報告
            if self.process_monitor and process_id:
                await self.process_monitor.complete_process(
                    process_id,
                    metadata_update={
                        "results_count": len(optimized_results),
                        "optimization_applied": True,
                        "mode": mode
                    }
                )
            
            return optimized_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            
            # プロセスエラー報告
            if self.process_monitor and process_id:
                await self.process_monitor.fail_process(
                    process_id,
                    error_message=f"Search failed: {str(e)}"
                )
                
            return []
    
    def _get_mode_config(self, mode: str) -> Dict[str, Any]:
        """
        指定されたモードの設定を取得
        """
        mode_configs = self.mode_config
        
        # モード名の正規化
        normalized_mode = mode.lower()
        if normalized_mode in ["dialog", "chat"]:
            normalized_mode = "interactive"
        elif normalized_mode in ["auto", "autonomous"]:
            normalized_mode = "autonomous"
        
        # 指定されたモードの設定を取得、なければgeneral設定を使用
        config = mode_configs.get(normalized_mode, mode_configs.get("general", {}))
        
        # デフォルト値とマージ
        default_config = {
            "similarity_threshold": 0.3,
            "boost_user_context": 1.0,
            "exploration_factor": 1.0,
            "cross_reference_boost": 1.0,
            "prefer_recent": False,
            "multi_perspective_retrieval": False,
            "balanced_approach": True,
            "adaptive_threshold": False,
            "context_awareness": 0.5,
            "personalization_weight": 0.0,
            "response_speed_priority": False,
            "depth_search_enabled": False
        }
        
        # 設定をマージ
        merged_config = {**default_config, **config}
        return merged_config

    async def _apply_mode_optimization(
        self,
        search_results: List[RAGSearchResult],
        mode: str,
        query: str
    ) -> List[RAGSearchResult]:
        """
        モード別の最適化を検索結果に適用
        """
        if not search_results:
            return search_results
        
        mode_config = self._get_mode_config(mode)
        
        try:
            # 結果をコピーして操作
            optimized_results = search_results.copy()
            
            # interactiveモードの最適化
            if mode in ["interactive", "dialog"]:
                optimized_results = await self._optimize_for_interactive(
                    optimized_results, mode_config, query
                )
            
            # autonomousモードの最適化
            elif mode in ["autonomous", "auto"]:
                optimized_results = await self._optimize_for_autonomous(
                    optimized_results, mode_config, query
                )
            
            # hybridモードの最適化
            elif mode == "hybrid":
                optimized_results = await self._optimize_for_hybrid(
                    optimized_results, mode_config, query
                )
            
            return optimized_results
            
        except Exception as e:
            logger.error(f"Error applying mode optimization: {e}")
            return search_results
    
    async def _optimize_for_interactive(
        self,
        results: List[RAGSearchResult],
        config: Dict[str, Any],
        query: str
    ) -> List[RAGSearchResult]:
        """
        対話型モード向けの最適化
        - 最近の文書を優先
        - 個人化重み適用
        - レスポンス速度重視
        """
        try:
            boost_user_context = config.get("boost_user_context", 1.0)
            personalization_weight = config.get("personalization_weight", 0.0)
            prefer_recent = config.get("prefer_recent", False)
            
            # 最近の文書にブーストを適用
            if prefer_recent:
                current_time = time.time()
                for result in results:
                    # メタデータから作成時間を取得（存在する場合）
                    created_time = result.chunk.metadata.get("created_time", current_time)
                    time_diff = current_time - created_time
                    
                    # 最近の文書ほど高いスコア（24時間以内は1.5倍、1週間以内は1.2倍）
                    if time_diff < 86400:  # 24時間
                        result.similarity *= 1.5
                    elif time_diff < 604800:  # 1週間
                        result.similarity *= 1.2
            
            # コンテキストブーストを適用
            if boost_user_context > 1.0:
                for result in results:
                    # ユーザーコンテキストに関連するキーワードがある場合のブースト
                    content_lower = result.chunk.content.lower()
                    query_lower = query.lower()
                    
                    # 簡単な関連度計算
                    query_words = set(query_lower.split())
                    content_words = set(content_lower.split())
                    overlap = len(query_words & content_words)
                    
                    if overlap > 0:
                        boost_factor = min(boost_user_context, 1.0 + (overlap * 0.1))
                        result.similarity *= boost_factor
            
            # 類似度でソート
            results.sort(key=lambda x: x.similarity, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in interactive optimization: {e}")
            return results
    
    async def _optimize_for_autonomous(
        self,
        results: List[RAGSearchResult],
        config: Dict[str, Any],
        query: str
    ) -> List[RAGSearchResult]:
        """
        自律型モード向けの最適化
        - 包括的な情報収集
        - 探索性重視
        - 多角的視点
        """
        try:
            exploration_factor = config.get("exploration_factor", 1.0)
            cross_reference_boost = config.get("cross_reference_boost", 1.0)
            multi_perspective = config.get("multi_perspective_retrieval", False)
            
            # 探索因子を適用（多様性を重視）
            if exploration_factor > 1.0:
                # 類似性の分散を計算
                similarities = [r.similarity for r in results]
                if len(similarities) > 1:
                    import statistics
                    std_dev = statistics.stdev(similarities)
                    
                    # 分散が小さい（似たような結果ばかり）場合、下位結果にブーストを適用
                    if std_dev < 0.1:
                        for i, result in enumerate(results):
                            if i >= len(results) // 2:  # 下位半分
                                diversity_boost = 1.0 + (exploration_factor - 1.0) * 0.5
                                result.similarity *= diversity_boost
            
            # 相互参照ブーストを適用
            if cross_reference_boost > 1.0:
                # 同一ソースファイルからの複数チャンクにブーストを適用
                source_counts = {}
                for result in results:
                    source = result.chunk.source_file
                    source_counts[source] = source_counts.get(source, 0) + 1
                
                for result in results:
                    source = result.chunk.source_file
                    if source_counts[source] > 1:
                        result.similarity *= cross_reference_boost
            
            # 多角的視点の検索
            if multi_perspective:
                # 異なるタイプの文書からバランス良く結果を選択
                doc_types = {}
                for result in results:
                    doc_type = result.chunk.metadata.get("document_type", "unknown")
                    if doc_type not in doc_types:
                        doc_types[doc_type] = []
                    doc_types[doc_type].append(result)
                
                # 各タイプから最低1つは選択
                balanced_results = []
                for doc_type, type_results in doc_types.items():
                    # 各タイプから最高スコアのものを追加
                    type_results.sort(key=lambda x: x.similarity, reverse=True)
                    balanced_results.extend(type_results[:2])  # 各タイプから最大2つ
                
                # 重複を除去し、元の結果とマージ
                seen_chunks = set(r.chunk.chunk_id for r in balanced_results)
                for result in results:
                    if result.chunk.chunk_id not in seen_chunks:
                        balanced_results.append(result)
                
                results = balanced_results
            
            # 類似度でソート
            results.sort(key=lambda x: x.similarity, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in autonomous optimization: {e}")
            return results
    
    async def _optimize_for_hybrid(
        self,
        results: List[RAGSearchResult],
        config: Dict[str, Any],
        query: str
    ) -> List[RAGSearchResult]:
        """
        ハイブリッドモード向けの最適化
        - バランス重視
        - アダプティブ閾値
        - コンテキスト認識
        """
        try:
            balanced_approach = config.get("balanced_approach", True)
            adaptive_threshold = config.get("adaptive_threshold", False)
            context_awareness = config.get("context_awareness", 0.5)
            
            if balanced_approach:
                # interactiveとautonomousの中間的なアプローチ
                interactive_results = await self._optimize_for_interactive(
                    results.copy(), 
                    {"boost_user_context": 1.1, "prefer_recent": True},
                    query
                )
                autonomous_results = await self._optimize_for_autonomous(
                    results.copy(),
                    {"exploration_factor": 1.2, "cross_reference_boost": 1.1},
                    query
                )
                
                # 両方の結果を重み付きで組み合わせ
                combined_scores = {}
                for result in interactive_results:
                    combined_scores[result.chunk.chunk_id] = {
                        "interactive": result.similarity,
                        "autonomous": 0.0
                    }
                
                for result in autonomous_results:
                    chunk_id = result.chunk.chunk_id
                    if chunk_id in combined_scores:
                        combined_scores[chunk_id]["autonomous"] = result.similarity
                    else:
                        combined_scores[chunk_id] = {
                            "interactive": 0.0,
                            "autonomous": result.similarity
                        }
                
                # 重み付き平均を計算
                for result in results:
                    chunk_id = result.chunk.chunk_id
                    if chunk_id in combined_scores:
                        scores = combined_scores[chunk_id]
                        result.similarity = (
                            scores["interactive"] * context_awareness +
                            scores["autonomous"] * (1.0 - context_awareness)
                        )
            
            # アダプティブ閾値調整
            if adaptive_threshold and results:
                # 結果の分布に基づいて動的に閾値を調整
                similarities = [r.similarity for r in results]
                if len(similarities) > 2:
                    import statistics
                    mean_sim = statistics.mean(similarities)
                    std_sim = statistics.stdev(similarities) if len(similarities) > 1 else 0
                    
                    # 動的閾値 = 平均 - 0.5 * 標準偏差
                    dynamic_threshold = max(0.1, mean_sim - (0.5 * std_sim))
                    
                    # 閾値未満の結果を除外
                    results = [r for r in results if r.similarity >= dynamic_threshold]
            
            # 類似度でソート
            results.sort(key=lambda x: x.similarity, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid optimization: {e}")
            return results

    async def generate_context(
        self,
        query: str,
        mode: str = "interactive",
        max_context_length: int = None
    ) -> Dict[str, Any]:
        """
        クエリに基づいてコンテキストを生成
        """
        if max_context_length is None:
            max_context_length = self.retrieval_config.get("max_context_length", 4096)
        
        # 検索実行
        search_results = await self.search(query, mode)
        
        if not search_results:
            return {
                "context": "",
                "sources": [],
                "total_results": 0,
                "context_length": 0
            }
        
        # コンテキストを構築
        context_parts = []
        sources = []
        current_length = 0
        
        for result in search_results:
            chunk_text = f"[文書 {result.rank}] {result.chunk.content}"
            
            # 長さ制限をチェック
            if current_length + len(chunk_text) > max_context_length:
                # 残りスペースがあれば部分的に追加
                remaining_space = max_context_length - current_length
                if remaining_space > 100:  # 最小限の有用な長さ
                    chunk_text = chunk_text[:remaining_space] + "..."
                    context_parts.append(chunk_text)
                    current_length += len(chunk_text)
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
            
            # ソース情報を追加
            source_info = {
                "chunk_id": result.chunk.chunk_id,
                "source_file": result.chunk.source_file,
                "similarity": result.similarity,
                "rank": result.rank
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        return {
            "context": context,
            "sources": sources,
            "total_results": len(search_results),
            "context_length": len(context),
            "query": query,
            "mode": mode
        }
    
    async def add_document(
        self,
        content: str,
        file_name: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        新しいドキュメントを追加してインデックス
        """
        try:
            # 知識ベースに追加
            chunk_ids = await self.knowledge_base.add_document(content, file_name, metadata)
            if not chunk_ids:
                logger.error(f"Failed to add document to knowledge base: {file_name}")
                return False
            
            # チャンクを取得して埋め込み生成
            chunks = []
            for chunk_id in chunk_ids:
                chunk = await self.knowledge_base.get_chunk_by_id(chunk_id)
                if chunk:
                    chunks.append(chunk)
            
            if not chunks:
                logger.error(f"No chunks found for document: {file_name}")
                return False
            
            # 埋め込みを生成
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed_texts(texts)
            
            # ベクトルストアに追加
            valid_embeddings = []
            valid_texts = []
            valid_metadata = []
            
            for chunk, embedding in zip(chunks, embeddings):
                if embedding:
                    valid_embeddings.append(embedding)
                    valid_texts.append(chunk.content)
                    valid_metadata.append({
                        "chunk_id": chunk.chunk_id,
                        "source_file": chunk.source_file,
                        "chunk_index": chunk.chunk_index,
                        **chunk.metadata
                    })
            
            if valid_embeddings:
                vector_ids = await self.vector_store.add_vectors(
                    vectors=valid_embeddings,
                    documents=valid_texts,
                    metadata_list=valid_metadata
                )
                
                logger.info(f"Added document {file_name}: {len(vector_ids)} vectors indexed")
                
                # インデックス状態を更新
                await self._check_index_status()
                return True
            else:
                logger.error(f"No valid embeddings generated for document: {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding document {file_name}: {e}")
            return False
    
    async def reindex_knowledge_base(self, force: bool = False) -> Dict[str, Any]:
        """
        知識ベース全体を再インデックス
        """
        try:
            logger.info("Starting knowledge base reindexing...")
            start_time = time.time()
            
            # 知識ベースを更新
            refresh_result = await self.knowledge_base.refresh_knowledge_base(force=force)
            
            # 全チャンクを取得
            chunks = await self.knowledge_base.get_chunks()
            if not chunks:
                logger.info("No chunks to index")
                return {"status": "completed", "indexed_chunks": 0}
            
            # ベクトルストアをクリア（強制再インデックスの場合）
            if force:
                await self.vector_store.clear()
            
            # バッチで埋め込み生成とインデックス
            batch_size = self.embedding_service.batch_size
            total_indexed = 0
            errors = 0
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                try:
                    # 埋め込み生成
                    texts = [chunk.content for chunk in batch_chunks]
                    embeddings = await self.embedding_service.embed_texts(texts)
                    
                    # 有効な埋め込みのみを処理
                    valid_data = []
                    for chunk, embedding in zip(batch_chunks, embeddings):
                        if embedding:
                            valid_data.append((chunk, embedding))
                    
                    if valid_data:
                        valid_chunks, valid_embeddings = zip(*valid_data)
                        
                        # メタデータ準備
                        metadata_list = []
                        documents = []
                        
                        for chunk in valid_chunks:
                            documents.append(chunk.content)
                            metadata_list.append({
                                "chunk_id": chunk.chunk_id,
                                "source_file": chunk.source_file,
                                "chunk_index": chunk.chunk_index,
                                **chunk.metadata
                            })
                        
                        # ベクトルストアに追加
                        vector_ids = await self.vector_store.add_vectors(
                            vectors=list(valid_embeddings),
                            documents=documents,
                            metadata_list=metadata_list
                        )
                        
                        total_indexed += len(vector_ids)
                        logger.debug(f"Indexed batch {i//batch_size + 1}: {len(vector_ids)} chunks")
                    else:
                        errors += len(batch_chunks)
                        logger.warning(f"No valid embeddings in batch {i//batch_size + 1}")
                        
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    errors += len(batch_chunks)
            
            # インデックス状態を更新
            await self._check_index_status()
            
            elapsed_time = time.time() - start_time
            result = {
                "status": "completed",
                "total_chunks": len(chunks),
                "indexed_chunks": total_indexed,
                "errors": errors,                "elapsed_time": round(elapsed_time, 2),
                "refresh_result": refresh_result
            }
            logger.info(f"Reindexing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during reindexing: {e}")
            return {"status": "error", "error": str(e)}
            
    async def get_stats(self) -> Dict[str, Any]:
        """
        RAGシステムの統計情報を取得
        """
        try:
            # 各コンポーネントの統計を取得
            kb_stats = await self.knowledge_base.get_stats()
            vector_stats = await self.vector_store.get_stats()
            embedding_health = await self.embedding_service.health_check()
            
            stats = {
                "system_status": "initialized" if self.is_initialized else "not_initialized",
                "knowledge_base": kb_stats,
                "vector_store": vector_stats,
                "embedding_service": embedding_health,
                "index_status": self.index_status,
                "configuration": {
                    "retrieval": self.retrieval_config,
                    "mode_optimization": self.mode_config
                }
            }
            
            # キャッシュ統計を追加
            if self.cache_manager:
                cache_stats = await self.cache_manager.get_stats()
                stats["cache"] = cache_stats
            
            # プロセス監視統計を追加
            if self.process_monitor:
                monitor_stats = await self.process_monitor.get_stats()
                # アクティブなRAG検索プロセスを追加
                active_rag_processes = await self.process_monitor.get_active_processes()
                rag_processes = [p for p in active_rag_processes 
                               if p.get("process_type") == "rag_search"]
                
                stats["process_monitor"] = {
                    **monitor_stats,
                    "active_rag_searches": len(rag_processes)
                }
                
            return stats
            
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        RAGシステムの健康状態をチェック
        """
        try:
            health_status = {
                "overall": "healthy",
                "components": {},
                "issues": []
            }
            
            # 各コンポーネントの健康状態をチェック
            embedding_health = await self.embedding_service.health_check()
            health_status["components"]["embedding"] = embedding_health
            
            if embedding_health.get("status") != "healthy":
                health_status["overall"] = "degraded"
                health_status["issues"].append("Embedding service issue")
            
            vector_stats = await self.vector_store.get_stats()
            health_status["components"]["vector_store"] = {
                "status": "healthy" if vector_stats.get("total_vectors", 0) > 0 else "warning",
                "total_vectors": vector_stats.get("total_vectors", 0)
            }
            
            if vector_stats.get("total_vectors", 0) == 0:
                health_status["overall"] = "warning"
                health_status["issues"].append("No vectors in store")
            
            kb_stats = await self.knowledge_base.get_stats()
            health_status["components"]["knowledge_base"] = {
                "status": "healthy" if kb_stats.get("total_documents", 0) > 0 else "warning",
                "total_documents": kb_stats.get("total_documents", 0),
                "total_chunks": kb_stats.get("total_chunks", 0)
            }
            
            if kb_stats.get("total_documents", 0) == 0:
                health_status["overall"] = "warning"
                health_status["issues"].append("No documents in knowledge base")
            
            # インデックス同期チェック
            if self.index_status.get("needs_reindex", False):
                health_status["overall"] = "warning"
                health_status["issues"].append("Index needs reindexing")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return {
                "overall": "error",
                "error": str(e)
            }
