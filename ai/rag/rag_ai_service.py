"""
RAG System - AI Service Integration
RAGシステムとAIサービスの統合
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path

from .rag_system import RAGSystem, RAGSearchResult
from ..llm_service import LLMServiceManager, GenerationRequest, GenerationResponse
from ..providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class RAGAIService:
    """
    RAG統合AIサービス
    知識ベースを活用した検索拡張生成システム
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            # デフォルト設定を読み込み
            from pathlib import Path
            import json
            
            config_path = Path(__file__).parent.parent.parent / "config" / "rag_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = {"rag": json.load(f)}
            else:
                config = {"rag": {}, "ai": {}}
                
        self.config = config
        self.rag_config = config.get("rag", {})
        self.ai_config = config.get("ai", {})
        
        # RAGシステム
        self.rag_system = RAGSystem(self.rag_config)
        
        # LLMサービス
        self.llm_service = None
        
        # 統合設定
        self.enable_rag = self.rag_config.get("enable", True)
        self.fallback_to_llm = self.rag_config.get("fallback_to_llm", True)
        self.context_template = self.rag_config.get("context_template", self._default_context_template())
        
        self.is_initialized = False
    
    def _default_context_template(self) -> str:
        """
        デフォルトのコンテキストテンプレート
        """
        return """以下の情報を参考にして、ユーザーの質問に回答してください。

参考情報:
{context}

質問: {query}

参考情報を基に、正確で有用な回答を提供してください。参考情報に答えがない場合は、その旨を明記してください。"""
    
    async def initialize(self) -> bool:
        """
        RAG統合AIサービスの初期化
        """
        try:
            logger.info("Initializing RAG AI Service...")
            
            # RAGシステムを初期化
            if self.enable_rag:
                rag_ok = await self.rag_system.initialize()
                if not rag_ok:
                    logger.error("Failed to initialize RAG system")
                    if not self.fallback_to_llm:
                        return False
                    logger.warning("Continuing without RAG (fallback enabled)")
                    self.enable_rag = False
            
            # LLMサービスを初期化
            try:
                # Ollamaプロバイダーを使用
                ollama_config = self.ai_config.get("ollama", {})
                ollama_provider = OllamaProvider(
                    base_url=ollama_config.get("base_url", "http://localhost:11434"),
                    timeout=ollama_config.get("timeout", 30)
                )
                
                # プロバイダーの健康状態をチェック
                if await ollama_provider.is_healthy():
                    self.llm_service = LLMServiceManager([ollama_provider])
                    logger.info("LLM service initialized with Ollama provider")
                else:
                    logger.error("Ollama provider is not healthy")
                    if not self.enable_rag:
                        return False
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                if not self.enable_rag:
                    return False
            
            self.is_initialized = True
            logger.info("RAG AI Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG AI Service: {e}")
            return False
    
    async def generate_with_rag(
        self,
        query: str,
        mode: str = "interactive",
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        context_length: int = None
    ) -> Dict[str, Any]:
        """
        RAGを使用した生成
        """
        if not self.is_initialized:
            raise RuntimeError("RAG AI Service not initialized")
        
        try:
            # RAGコンテキストを生成
            rag_context = None
            rag_sources = []
            
            if self.enable_rag:
                context_result = await self.rag_system.generate_context(
                    query=query,
                    mode=mode,
                    max_context_length=context_length
                )
                
                if context_result.get("context"):
                    rag_context = context_result["context"]
                    rag_sources = context_result.get("sources", [])
                    logger.info(f"Generated RAG context with {len(rag_sources)} sources")
                else:
                    logger.info("No relevant context found in knowledge base")
            
            # プロンプトを構築
            if rag_context:
                # RAGコンテキストを使用
                prompt = self.context_template.format(
                    context=rag_context,
                    query=query
                )
                generation_type = "rag_enhanced"
            else:
                # RAGコンテキストなしでLLMのみ使用
                prompt = query
                generation_type = "llm_only"
                if self.enable_rag:
                    logger.warning("No RAG context available, falling back to LLM only")
            
            # LLM生成を実行
            llm_response = None
            if self.llm_service:
                request = GenerationRequest(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens or 2048,
                    temperature=temperature or 0.7
                )
                
                llm_response = await self.llm_service.generate(request)
            
            # 結果を構築
            result = {
                "query": query,
                "response": llm_response.content if llm_response else "LLMサービスが利用できません",
                "generation_type": generation_type,
                "rag_enabled": self.enable_rag,
                "sources": rag_sources,
                "context_length": len(rag_context) if rag_context else 0,
                "model_used": llm_response.model if llm_response else None,
                "tokens_used": llm_response.usage.get("total_tokens") if llm_response and llm_response.usage else None
            }
            
            # メタデータを追加
            if llm_response:
                result.update({
                    "success": True,
                    "generation_time": llm_response.generation_time,
                    "finish_reason": llm_response.finish_reason
                })
            else:
                result.update({
                    "success": False,
                    "error": "LLM generation failed"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG generation: {e}")
            return {
                "query": query,
                "response": f"エラーが発生しました: {str(e)}",
                "success": False,
                "error": str(e),
                "generation_type": "error"
            }
    
    async def generate_stream_with_rag(
        self,
        query: str,
        mode: str = "interactive",
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        context_length: int = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        RAGを使用したストリーミング生成
        """
        if not self.is_initialized:
            yield {"error": "RAG AI Service not initialized"}
            return
        
        try:
            # RAGコンテキストを生成
            rag_context = None
            rag_sources = []
            
            if self.enable_rag:
                yield {"status": "searching", "message": "知識ベースを検索中..."}
                
                context_result = await self.rag_system.generate_context(
                    query=query,
                    mode=mode,
                    max_context_length=context_length
                )
                
                if context_result.get("context"):
                    rag_context = context_result["context"]
                    rag_sources = context_result.get("sources", [])
                    yield {
                        "status": "context_found",
                        "message": f"関連する情報を{len(rag_sources)}件見つけました",
                        "sources": rag_sources
                    }
                else:
                    yield {"status": "no_context", "message": "関連する情報が見つかりませんでした"}
            
            # プロンプトを構築
            if rag_context:
                prompt = self.context_template.format(
                    context=rag_context,
                    query=query
                )
                generation_type = "rag_enhanced"
            else:
                prompt = query
                generation_type = "llm_only"
            
            yield {"status": "generating", "message": "回答を生成中..."}
            
            # LLMストリーミング生成
            if self.llm_service:
                request = GenerationRequest(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens or 2048,
                    temperature=temperature or 0.7
                )
                
                async for chunk in self.llm_service.generate_stream(request):
                    # チャンクにRAG情報を追加
                    enhanced_chunk = {
                        **chunk,
                        "generation_type": generation_type,
                        "rag_enabled": self.enable_rag
                    }
                    
                    # 最初のチャンクにソース情報を追加
                    if rag_sources and chunk.get("is_first", False):
                        enhanced_chunk["sources"] = rag_sources
                    
                    yield enhanced_chunk
            else:
                yield {
                    "content": "LLMサービスが利用できません",
                    "finish_reason": "error",
                    "generation_type": generation_type,
                    "error": "LLM service unavailable"
                }
                
        except Exception as e:
            logger.error(f"Error in RAG streaming generation: {e}")
            yield {
                "content": f"エラーが発生しました: {str(e)}",
                "finish_reason": "error",
                "error": str(e)
            }
    
    async def search_knowledge_base(
        self,
        query: str,
        mode: str = "interactive",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        知識ベースの検索のみを実行
        """
        if not self.enable_rag:
            return []
        
        try:
            search_results = await self.rag_system.search(
                query=query,
                mode=mode,
                top_k=top_k
            )
            
            return [result.to_dict() for result in search_results]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    async def add_document_to_knowledge_base(
        self,
        content: str,
        file_name: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        知識ベースにドキュメントを追加
        """
        if not self.enable_rag:
            logger.warning("RAG is disabled, cannot add document")
            return False
        
        try:
            return await self.rag_system.add_document(content, file_name, metadata)
        except Exception as e:
            logger.error(f"Error adding document to knowledge base: {e}")
            return False
    
    async def reindex_knowledge_base(self, force: bool = False) -> Dict[str, Any]:
        """
        知識ベースの再インデックス
        """
        if not self.enable_rag:
            return {"status": "disabled", "message": "RAG is disabled"}
        
        try:
            return await self.rag_system.reindex_knowledge_base(force=force)
        except Exception as e:
            logger.error(f"Error reindexing knowledge base: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        RAG AI Serviceの統計情報を取得
        """
        try:
            stats = {
                "initialized": self.is_initialized,
                "rag_enabled": self.enable_rag,
                "llm_available": self.llm_service is not None
            }
            
            if self.enable_rag:
                rag_stats = await self.rag_system.get_stats()
                stats["rag_system"] = rag_stats
            
            if self.llm_service:
                # LLMサービスの統計（利用可能であれば）
                try:
                    providers_info = []
                    for provider in self.llm_service.providers:
                        if hasattr(provider, 'get_available_models'):
                            models = await provider.get_available_models()
                            providers_info.append({
                                "type": type(provider).__name__,
                                "healthy": await provider.is_healthy(),
                                "models": len(models),
                                "model_names": models
                            })
                    stats["llm_providers"] = providers_info
                except Exception as e:
                    stats["llm_providers"] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting RAG AI Service stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        RAG AI Serviceの健康状態をチェック
        """
        try:
            health = {
                "overall": "healthy",
                "components": {},
                "issues": []
            }
            
            # RAGシステムの健康状態
            if self.enable_rag:
                rag_health = await self.rag_system.health_check()
                health["components"]["rag"] = rag_health
                
                if rag_health.get("overall") != "healthy":
                    health["overall"] = "degraded"
                    health["issues"].extend(rag_health.get("issues", []))
            else:
                health["components"]["rag"] = {"status": "disabled"}
            
            # LLMサービスの健康状態
            if self.llm_service:
                llm_healthy = True
                llm_issues = []
                
                for provider in self.llm_service.providers:
                    try:
                        is_healthy = await provider.is_healthy()
                        if not is_healthy:
                            llm_healthy = False
                            llm_issues.append(f"{type(provider).__name__} unhealthy")
                    except Exception as e:
                        llm_healthy = False
                        llm_issues.append(f"{type(provider).__name__} error: {str(e)}")
                
                health["components"]["llm"] = {
                    "status": "healthy" if llm_healthy else "unhealthy",
                    "issues": llm_issues
                }
                
                if not llm_healthy:
                    health["overall"] = "degraded"
                    health["issues"].extend(llm_issues)
            else:
                health["components"]["llm"] = {"status": "unavailable"}
                health["overall"] = "warning"
                health["issues"].append("LLM service not available")
            
            return health
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return {
                "overall": "error",
                "error": str(e)
            }
