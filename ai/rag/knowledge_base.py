"""
RAG System - Knowledge Base Manager
ドキュメントの読み込み、分割、インデクシングを管理
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import mimetypes

logger = logging.getLogger(__name__)

class DocumentChunk:
    """
    ドキュメントチャンク（分割されたテキスト断片）
    """
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_id: str = None,
        source_file: str = None,
        chunk_index: int = 0
    ):
        self.content = content
        self.metadata = metadata or {}
        self.chunk_id = chunk_id or self._generate_chunk_id(content, source_file, chunk_index)
        self.source_file = source_file
        self.chunk_index = chunk_index
        self.created_at = time.time()
    
    def _generate_chunk_id(self, content: str, source_file: str, chunk_index: int) -> str:
        """チャンクIDを生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        source_hash = hashlib.md5((source_file or "").encode()).hexdigest()[:8]
        return f"{source_hash}_{chunk_index}_{content_hash}"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunk':
        """辞書から復元"""
        chunk = cls(
            content=data["content"],
            metadata=data.get("metadata", {}),
            chunk_id=data["chunk_id"],
            source_file=data.get("source_file"),
            chunk_index=data.get("chunk_index", 0)
        )
        chunk.created_at = data.get("created_at", time.time())
        return chunk

class KnowledgeBaseManager:
    """
    知識ベース管理システム
    ドキュメントの読み込み、分割、メタデータ管理を行う
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kb_config = config.get("knowledge_base", {})
        self.retrieval_config = config.get("retrieval", {})
        
        self.data_directory = Path(self.kb_config.get("data_directory", "ai/rag/knowledge_base"))
        self.supported_formats = set(self.kb_config.get("supported_formats", [".txt", ".md", ".json", ".py"]))
        self.auto_refresh = self.kb_config.get("auto_refresh", True)
        self.refresh_interval = self.kb_config.get("refresh_interval_minutes", 60)
        
        self.chunk_size = self.retrieval_config.get("chunk_size", 512)
        self.chunk_overlap = self.retrieval_config.get("chunk_overlap", 50)
        
        # ドキュメント管理
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: Dict[str, DocumentChunk] = {}
        self.file_hashes: Dict[str, str] = {}
        self.last_refresh = 0
        
        # データディレクトリを作成
        self.data_directory.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """
        知識ベースマネージャーの初期化
        """
        try:
            # 既存のメタデータをロード
            await self._load_metadata()
            
            # 初回スキャン
            await self.refresh_knowledge_base()
            
            logger.info(f"Knowledge base initialized with {len(self.documents)} documents and {len(self.chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            return False
    
    async def refresh_knowledge_base(self, force: bool = False) -> Dict[str, Any]:
        """
        知識ベースを更新
        """
        current_time = time.time()
        
        # 自動更新チェック
        if not force and not self.auto_refresh:
            return {"status": "skipped", "reason": "auto_refresh disabled"}
        
        if not force and (current_time - self.last_refresh) < (self.refresh_interval * 60):
            return {"status": "skipped", "reason": "refresh_interval not reached"}
        
        try:
            scan_results = await self._scan_directory()
            self.last_refresh = current_time
            
            # メタデータを保存
            await self._save_metadata()
            
            logger.info(f"Knowledge base refreshed: {scan_results}")
            return scan_results
            
        except Exception as e:
            logger.error(f"Error refreshing knowledge base: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _scan_directory(self) -> Dict[str, Any]:
        """
        ディレクトリをスキャンして新規・更新・削除されたファイルを検出
        """
        current_files = set()
        new_files = []
        updated_files = []
        errors = []
        
        # ファイルスキャン
        for file_path in self.data_directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                try:
                    file_str = str(file_path.relative_to(self.data_directory))
                    current_files.add(file_str)
                    
                    # ファイルハッシュを計算
                    file_hash = await self._calculate_file_hash(file_path)
                    
                    if file_str not in self.file_hashes:
                        # 新規ファイル
                        await self._process_file(file_path, file_str)
                        new_files.append(file_str)
                    elif self.file_hashes[file_str] != file_hash:
                        # 更新されたファイル
                        await self._process_file(file_path, file_str)
                        updated_files.append(file_str)
                    
                    self.file_hashes[file_str] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    errors.append({"file": str(file_path), "error": str(e)})
        
        # 削除されたファイルを検出
        deleted_files = []
        for file_str in list(self.file_hashes.keys()):
            if file_str not in current_files:
                await self._remove_file(file_str)
                deleted_files.append(file_str)
        
        return {
            "status": "completed",
            "new_files": len(new_files),
            "updated_files": len(updated_files),
            "deleted_files": len(deleted_files),
            "errors": len(errors),
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "details": {
                "new": new_files,
                "updated": updated_files,
                "deleted": deleted_files,
                "errors": errors
            }
        }
    
    async def _process_file(self, file_path: Path, file_str: str) -> bool:
        """
        ファイルを処理してチャンクを生成
        """
        try:
            # 既存のチャンクを削除
            await self._remove_file(file_str)
            
            # ファイル内容を読み込み
            content = await self._read_file(file_path)
            if not content:
                return False
            
            # ドキュメントメタデータを作成
            doc_metadata = {
                "file_path": file_str,
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "file_type": file_path.suffix.lower(),
                "modified_time": file_path.stat().st_mtime,
                "processed_time": time.time()
            }
            
            # ドキュメントを登録
            self.documents[file_str] = {
                "content": content,
                "metadata": doc_metadata,
                "chunk_count": 0
            }
            
            # チャンクに分割
            chunks = await self._split_into_chunks(content, file_str, doc_metadata)
            
            # チャンクを登録
            for chunk in chunks:
                self.chunks[chunk.chunk_id] = chunk
            
            self.documents[file_str]["chunk_count"] = len(chunks)
            
            logger.debug(f"Processed file {file_str}: {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False
    
    async def _read_file(self, file_path: Path) -> Optional[str]:
        """
        ファイル内容を読み込み
        """
        try:
            # エンコーディングを推定
            encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'euc-jp', 'iso-2022-jp']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return content.strip()
                except UnicodeDecodeError:
                    continue
            
            # バイナリファイルの場合
            logger.warning(f"Could not decode file {file_path} as text")
            return None
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    async def _split_into_chunks(
        self, 
        content: str, 
        source_file: str, 
        doc_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        テキストをチャンクに分割
        """
        if not content.strip():
            return []
        
        chunks = []
        
        # 基本的なテキスト分割
        if len(content) <= self.chunk_size:
            # 短いテキストはそのまま1チャンクに
            chunk = DocumentChunk(
                content=content,
                metadata={**doc_metadata, "chunk_type": "full_document"},
                source_file=source_file,
                chunk_index=0
            )
            chunks.append(chunk)
        else:
            # 長いテキストは分割
            chunks.extend(await self._split_long_text(content, source_file, doc_metadata))
        
        return chunks
    
    async def _split_long_text(
        self, 
        text: str, 
        source_file: str, 
        doc_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        長いテキストを意味的に分割
        """
        chunks = []
        
        # 段落で分割を試行
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 現在のチャンクに追加できるかチェック
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # 現在のチャンクを保存
                if current_chunk:
                    chunk = DocumentChunk(
                        content=current_chunk,
                        metadata={**doc_metadata, "chunk_type": "paragraph_group"},
                        source_file=source_file,
                        chunk_index=chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # 段落が長すぎる場合は文で分割
                if len(paragraph) > self.chunk_size:
                    sentence_chunks = await self._split_by_sentences(
                        paragraph, source_file, doc_metadata, chunk_index
                    )
                    chunks.extend(sentence_chunks)
                    chunk_index += len(sentence_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # 最後のチャンクを保存
        if current_chunk:
            chunk = DocumentChunk(
                content=current_chunk,
                metadata={**doc_metadata, "chunk_type": "final_chunk"},
                source_file=source_file,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _split_by_sentences(
        self, 
        text: str, 
        source_file: str, 
        doc_metadata: Dict[str, Any], 
        start_index: int
    ) -> List[DocumentChunk]:
        """
        文単位でテキストを分割
        """
        chunks = []
        
        # 文で分割
        sentences = re.split(r'[.!?。！？]\s*', text)
        
        current_chunk = ""
        chunk_index = start_index
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            potential_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunk = DocumentChunk(
                        content=current_chunk,
                        metadata={**doc_metadata, "chunk_type": "sentence_group"},
                        source_file=source_file,
                        chunk_index=chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # オーバーラップを考慮して次のチャンクを開始
                if len(sentence) > self.chunk_size:
                    # 文が長すぎる場合は強制分割
                    for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                        chunk_text = sentence[i:i + self.chunk_size]
                        if chunk_text.strip():
                            chunk = DocumentChunk(
                                content=chunk_text,
                                metadata={**doc_metadata, "chunk_type": "forced_split"},
                                source_file=source_file,
                                chunk_index=chunk_index
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunk = DocumentChunk(
                content=current_chunk,
                metadata={**doc_metadata, "chunk_type": "sentence_final"},
                source_file=source_file,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _remove_file(self, file_str: str) -> None:
        """
        ファイルと関連チャンクを削除
        """
        # ドキュメントを削除
        if file_str in self.documents:
            del self.documents[file_str]
        
        # 関連チャンクを削除
        chunks_to_remove = [
            chunk_id for chunk_id, chunk in self.chunks.items()
            if chunk.source_file == file_str
        ]
        
        for chunk_id in chunks_to_remove:
            del self.chunks[chunk_id]
        
        # ファイルハッシュを削除
        if file_str in self.file_hashes:
            del self.file_hashes[file_str]
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """
        ファイルのハッシュを計算
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    async def _load_metadata(self) -> bool:
        """
        メタデータファイルをロード
        """
        metadata_file = self.data_directory / "metadata.json"
        try:
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # ドキュメントメタデータを復元
                    self.documents = data.get("documents", {})
                    self.file_hashes = data.get("file_hashes", {})
                    self.last_refresh = data.get("last_refresh", 0)
                    
                    # チャンクを復元
                    chunks_data = data.get("chunks", {})
                    self.chunks = {
                        chunk_id: DocumentChunk.from_dict(chunk_data)
                        for chunk_id, chunk_data in chunks_data.items()
                    }
                    
                    logger.info(f"Loaded metadata: {len(self.documents)} documents, {len(self.chunks)} chunks")
                    return True
            return True
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return False
    
    async def _save_metadata(self) -> bool:
        """
        メタデータファイルを保存
        """
        metadata_file = self.data_directory / "metadata.json"
        try:
            # チャンクを辞書形式に変換
            chunks_data = {
                chunk_id: chunk.to_dict()
                for chunk_id, chunk in self.chunks.items()
            }
            
            data = {
                "documents": self.documents,
                "chunks": chunks_data,
                "file_hashes": self.file_hashes,
                "last_refresh": self.last_refresh,
                "config": self.kb_config,
                "stats": {
                    "total_documents": len(self.documents),
                    "total_chunks": len(self.chunks),
                    "supported_formats": list(self.supported_formats)
                }
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            return False
    
    async def get_chunks(self, filter_func=None) -> List[DocumentChunk]:
        """
        チャンクを取得（フィルタ機能付き）
        """
        if filter_func is None:
            return list(self.chunks.values())
        
        return [chunk for chunk in self.chunks.values() if filter_func(chunk)]
    
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """
        IDでチャンクを取得
        """
        return self.chunks.get(chunk_id)
    
    async def add_document(
        self, 
        content: str, 
        file_name: str, 
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """
        ドキュメントを直接追加
        """
        try:
            doc_metadata = {
                "file_path": file_name,
                "file_name": file_name,
                "file_size": len(content.encode()),
                "file_type": "manual",
                "processed_time": time.time(),
                **(metadata or {})
            }
            
            # ドキュメントを登録
            self.documents[file_name] = {
                "content": content,
                "metadata": doc_metadata,
                "chunk_count": 0
            }
            
            # チャンクに分割
            chunks = await self._split_into_chunks(content, file_name, doc_metadata)
            
            # チャンクを登録
            chunk_ids = []
            for chunk in chunks:
                self.chunks[chunk.chunk_id] = chunk
                chunk_ids.append(chunk.chunk_id)
            
            self.documents[file_name]["chunk_count"] = len(chunks)
            
            # メタデータを保存
            await self._save_metadata()
            
            logger.info(f"Added document {file_name}: {len(chunks)} chunks")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error adding document {file_name}: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        知識ベースの統計情報を取得
        """
        try:
            total_content_size = sum(
                len(doc["content"]) for doc in self.documents.values()
            )
            
            chunk_sizes = [len(chunk.content) for chunk in self.chunks.values()]
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            
            file_types = {}
            for doc in self.documents.values():
                file_type = doc["metadata"].get("file_type", "unknown")
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                "total_documents": len(self.documents),
                "total_chunks": len(self.chunks),
                "total_content_size": total_content_size,
                "average_chunk_size": round(avg_chunk_size, 2),
                "file_types": file_types,
                "data_directory": str(self.data_directory),
                "supported_formats": list(self.supported_formats),
                "last_refresh": self.last_refresh,
                "auto_refresh": self.auto_refresh
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
