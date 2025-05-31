"""
RAG System Stub - テスト用の簡易実装
"""

from typing import List, Dict, Any, Optional
from .rag_system import RAGSearchResult
from .knowledge_base import DocumentChunk


class StubRAGSystem:
    """テスト用のRAGシステムスタブ"""
    
    def __init__(self):
        self.initialized = True
        
    async def search(
        self, 
        query: str, 
        top_k: int = 5, 
        mode: str = "hybrid",
        **kwargs
    ) -> List[RAGSearchResult]:
        """スタブの検索メソッド - 空の結果を返す"""
        return []
    
    async def add_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """スタブのドキュメント追加メソッド"""
        return "stub_doc_id"
    
    def is_initialized(self) -> bool:
        """初期化状態を返す"""
        return self.initialized
