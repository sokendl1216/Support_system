"""
高度なコンテキスト管理システム
エージェント間の長期記憶、コンテキスト継承、セッション永続化を管理
"""

import asyncio
import json
import sqlite3
import pickle
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """コンテキストエントリ"""
    entry_id: str
    session_id: str
    agent_id: str
    task_id: Optional[str]
    context_type: str  # "task", "agent_state", "user_preference", "learning"
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    importance_score: float = 1.0


@dataclass
class SessionContext:
    """セッションコンテキスト"""
    session_id: str
    user_id: Optional[str]
    mode: str
    created_at: datetime
    last_accessed: datetime
    context_entries: Dict[str, ContextEntry] = field(default_factory=dict)
    agent_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LongTermMemory:
    """長期記憶"""
    memory_id: str
    memory_type: str  # "pattern", "knowledge", "preference", "skill"
    content: Dict[str, Any]
    related_contexts: List[str] = field(default_factory=list)
    strength: float = 1.0  # 記憶の強度
    frequency: int = 1     # アクセス頻度
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


class AdvancedContextManager:
    """高度なコンテキスト管理システム"""
    
    def __init__(self, db_path: str = "context_db.sqlite", memory_limit_mb: int = 500):
        self.db_path = Path(db_path)
        self.memory_limit_mb = memory_limit_mb
        self.active_sessions: Dict[str, SessionContext] = {}
        self.long_term_memory: Dict[str, LongTermMemory] = {}
        self.context_cache: Dict[str, Any] = {}
        self.lock = threading.RLock()
        
        # 統計情報
        self.stats = {
            "total_contexts": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "memory_consolidations": 0,
            "contexts_persisted": 0
        }
        
        # 初期化
        self._initialize_database()
        self._load_long_term_memory()
        
        logger.info(f"Advanced Context Manager initialized with DB: {self.db_path}")
    
    def _initialize_database(self):
        """データベースを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_entries (
                    entry_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    task_id TEXT,
                    context_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    importance_score REAL DEFAULT 1.0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_contexts (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    mode TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    agent_states TEXT,
                    task_history TEXT,
                    preferences TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    related_contexts TEXT,
                    strength REAL DEFAULT 1.0,
                    frequency INTEGER DEFAULT 1,
                    last_accessed TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_session ON context_entries(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_agent ON context_entries(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_type ON context_entries(context_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON long_term_memory(memory_type)")
            
            conn.commit()
        
        logger.info("Database initialized successfully")
    
    def _load_long_term_memory(self):
        """長期記憶をロード"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM long_term_memory")
                for row in cursor.fetchall():
                    memory = LongTermMemory(
                        memory_id=row[0],
                        memory_type=row[1],
                        content=json.loads(row[2]),
                        related_contexts=json.loads(row[3]) if row[3] else [],
                        strength=row[4],
                        frequency=row[5],
                        last_accessed=datetime.fromisoformat(row[6]),
                        created_at=datetime.fromisoformat(row[7])
                    )
                    self.long_term_memory[memory.memory_id] = memory
            
            logger.info(f"Loaded {len(self.long_term_memory)} long-term memories")
        except Exception as e:
            logger.error(f"Failed to load long-term memory: {e}")
    
    @contextmanager
    def _get_db_connection(self):
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def create_session_context(self, session_id: str, user_id: Optional[str] = None, 
                             mode: str = "default") -> SessionContext:
        """セッションコンテキストを作成"""
        with self.lock:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            session_context = SessionContext(
                session_id=session_id,
                user_id=user_id,
                mode=mode,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            
            self.active_sessions[session_id] = session_context
            
            # ユーザーの過去のセッションから学習した設定を適用
            if user_id:
                self._apply_user_preferences(session_context)
            
            logger.info(f"Created session context: {session_id}")
            return session_context
    
    def _apply_user_preferences(self, session_context: SessionContext):
        """ユーザー設定を適用"""
        user_id = session_context.user_id
        if not user_id:
            return
        
        # 長期記憶からユーザー設定を取得
        user_preferences = self._get_user_preferences(user_id)
        if user_preferences:
            session_context.preferences.update(user_preferences)
            logger.debug(f"Applied user preferences for {user_id}")
    
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """ユーザー設定を取得"""
        preferences = {}
        
        for memory in self.long_term_memory.values():
            if (memory.memory_type == "preference" and 
                memory.content.get("user_id") == user_id):
                preferences.update(memory.content.get("preferences", {}))
        
        return preferences
    
    def store_context(self, session_id: str, agent_id: str, context_type: str, 
                     content: Dict[str, Any], task_id: Optional[str] = None,
                     importance_score: float = 1.0, expires_in_hours: Optional[int] = None) -> str:
        """コンテキストを保存"""
        with self.lock:
            # エントリIDを生成
            content_str = json.dumps(content, sort_keys=True, default=str)
            entry_id = hashlib.md5(f"{session_id}_{agent_id}_{context_type}_{content_str}".encode()).hexdigest()
            
            # 有効期限を設定
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            # コンテキストエントリを作成
            entry = ContextEntry(
                entry_id=entry_id,
                session_id=session_id,
                agent_id=agent_id,
                task_id=task_id,
                context_type=context_type,
                content=content,
                importance_score=importance_score,
                expires_at=expires_at
            )
            
            # セッションコンテキストに追加
            if session_id in self.active_sessions:
                self.active_sessions[session_id].context_entries[entry_id] = entry
                self.active_sessions[session_id].last_accessed = datetime.now()
            
            # キャッシュに追加
            cache_key = f"{session_id}_{context_type}_{agent_id}"
            self.context_cache[cache_key] = entry
            
            self.stats["total_contexts"] += 1
            
            logger.debug(f"Stored context: {entry_id} for agent {agent_id}")
            return entry_id
    
    def retrieve_context(self, session_id: str, context_type: str, 
                        agent_id: Optional[str] = None, limit: int = 10) -> List[ContextEntry]:
        """コンテキストを取得"""
        with self.lock:
            # キャッシュから検索
            cache_key = f"{session_id}_{context_type}_{agent_id or '*'}"
            if cache_key in self.context_cache:
                self.stats["cache_hits"] += 1
                entry = self.context_cache[cache_key]
                entry.access_count += 1
                return [entry]
            
            self.stats["cache_misses"] += 1
            
            # セッションから検索
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                matching_entries = []
                
                for entry in session.context_entries.values():
                    # 有効期限チェック
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        continue
                    
                    # フィルタリング
                    if entry.context_type == context_type:
                        if agent_id is None or entry.agent_id == agent_id:
                            entry.access_count += 1
                            matching_entries.append(entry)
                
                # 重要度とアクセス回数でソート
                matching_entries.sort(
                    key=lambda x: (x.importance_score, x.access_count),
                    reverse=True
                )
                
                session.last_accessed = datetime.now()
                return matching_entries[:limit]
            
            # データベースから検索（フォールバック）
            return self._retrieve_context_from_db(session_id, context_type, agent_id, limit)
    
    def _retrieve_context_from_db(self, session_id: str, context_type: str,
                                 agent_id: Optional[str], limit: int) -> List[ContextEntry]:
        """データベースからコンテキストを取得"""
        entries = []
        
        try:
            with self._get_db_connection() as conn:
                query = """
                    SELECT * FROM context_entries 
                    WHERE session_id = ? AND context_type = ?
                """
                params = [session_id, context_type]
                
                if agent_id:
                    query += " AND agent_id = ?"
                    params.append(agent_id)
                
                query += " ORDER BY importance_score DESC, access_count DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    entry = ContextEntry(
                        entry_id=row[0],
                        session_id=row[1],
                        agent_id=row[2],
                        task_id=row[3],
                        context_type=row[4],
                        content=json.loads(row[5]),
                        metadata=json.loads(row[6]) if row[6] else {},
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        expires_at=datetime.fromisoformat(row[9]) if row[9] else None,
                        access_count=row[10],
                        importance_score=row[11]
                    )
                    entries.append(entry)
        except Exception as e:
            logger.error(f"Failed to retrieve context from DB: {e}")
        
        return entries
    
    def inherit_context(self, source_session_id: str, target_session_id: str,
                       context_types: Optional[List[str]] = None,
                       agent_filter: Optional[str] = None) -> int:
        """コンテキストを継承"""
        if source_session_id not in self.active_sessions:
            logger.warning(f"Source session not found: {source_session_id}")
            return 0
        
        if target_session_id not in self.active_sessions:
            self.create_session_context(target_session_id)
        
        source_session = self.active_sessions[source_session_id]
        target_session = self.active_sessions[target_session_id]
        
        inherited_count = 0
        
        for entry in source_session.context_entries.values():
            # フィルタリング
            if context_types and entry.context_type not in context_types:
                continue
            if agent_filter and entry.agent_id != agent_filter:
                continue
            
            # 有効期限チェック
            if entry.expires_at and datetime.now() > entry.expires_at:
                continue
            
            # 継承されたエントリを作成
            new_entry_id = f"inherited_{entry.entry_id}_{target_session_id}"
            inherited_entry = ContextEntry(
                entry_id=new_entry_id,
                session_id=target_session_id,
                agent_id=entry.agent_id,
                task_id=entry.task_id,
                context_type=entry.context_type,
                content=entry.content.copy(),
                metadata={**entry.metadata, "inherited_from": source_session_id},
                importance_score=entry.importance_score * 0.8  # 継承時に重要度を減衰
            )
            
            target_session.context_entries[new_entry_id] = inherited_entry
            inherited_count += 1
        
        logger.info(f"Inherited {inherited_count} contexts from {source_session_id} to {target_session_id}")
        return inherited_count
    
    def consolidate_memory(self, session_id: str):
        """メモリを統合して長期記憶に保存"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        consolidated_memories = []
        
        # 重要なコンテキストを選出
        important_contexts = [
            entry for entry in session.context_entries.values()
            if entry.importance_score > 1.5 or entry.access_count > 3
        ]
        
        # パターンを抽出
        patterns = self._extract_patterns(important_contexts)
        for pattern in patterns:
            memory = LongTermMemory(
                memory_id=f"pattern_{hashlib.md5(str(pattern).encode()).hexdigest()}",
                memory_type="pattern",
                content=pattern,
                related_contexts=[ctx.entry_id for ctx in important_contexts]
            )
            consolidated_memories.append(memory)
        
        # 知識を抽出
        knowledge_items = self._extract_knowledge(important_contexts)
        for knowledge in knowledge_items:
            memory = LongTermMemory(
                memory_id=f"knowledge_{hashlib.md5(str(knowledge).encode()).hexdigest()}",
                memory_type="knowledge",
                content=knowledge
            )
            consolidated_memories.append(memory)
        
        # 長期記憶に保存
        for memory in consolidated_memories:
            self.long_term_memory[memory.memory_id] = memory
        
        # データベースに永続化
        self._persist_long_term_memories(consolidated_memories)
        
        self.stats["memory_consolidations"] += 1
        logger.info(f"Consolidated {len(consolidated_memories)} memories from session {session_id}")
    
    def _extract_patterns(self, contexts: List[ContextEntry]) -> List[Dict[str, Any]]:
        """コンテキストからパターンを抽出"""
        patterns = []
        
        # タスクタイプとエージェントの組み合わせパターン
        task_agent_pairs = defaultdict(int)
        for context in contexts:
            if context.task_id and context.agent_id:
                task_type = context.content.get("task_type", "unknown")
                task_agent_pairs[(task_type, context.agent_id)] += 1
        
        for (task_type, agent_id), count in task_agent_pairs.items():
            if count > 2:  # 3回以上の組み合わせをパターンとして認識
                patterns.append({
                    "type": "task_agent_preference",
                    "task_type": task_type,
                    "preferred_agent": agent_id,
                    "frequency": count
                })
        
        # 成功パターンの抽出
        success_patterns = []
        for context in contexts:
            if context.content.get("success", False):
                success_patterns.append({
                    "agent_id": context.agent_id,
                    "task_type": context.content.get("task_type"),
                    "execution_method": context.content.get("method"),
                    "parameters": context.content.get("parameters", {})
                })
        
        if success_patterns:
            patterns.append({
                "type": "success_patterns",
                "patterns": success_patterns
            })
        
        return patterns
    
    def _extract_knowledge(self, contexts: List[ContextEntry]) -> List[Dict[str, Any]]:
        """コンテキストから知識を抽出"""
        knowledge_items = []
        
        # エージェントの能力情報
        agent_capabilities = defaultdict(set)
        for context in contexts:
            if "capabilities" in context.content:
                agent_capabilities[context.agent_id].update(context.content["capabilities"])
        
        for agent_id, capabilities in agent_capabilities.items():
            knowledge_items.append({
                "type": "agent_capabilities",
                "agent_id": agent_id,
                "capabilities": list(capabilities)
            })
        
        # タスク完了時間の統計
        task_times = defaultdict(list)
        for context in contexts:
            if "execution_time" in context.content:
                task_type = context.content.get("task_type", "unknown")
                task_times[task_type].append(context.content["execution_time"])
        
        for task_type, times in task_times.items():
            if len(times) >= 3:
                knowledge_items.append({
                    "type": "execution_time_stats",
                    "task_type": task_type,
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "sample_size": len(times)
                })
        
        return knowledge_items
    
    def _persist_long_term_memories(self, memories: List[LongTermMemory]):
        """長期記憶をデータベースに永続化"""
        try:
            with self._get_db_connection() as conn:
                for memory in memories:
                    conn.execute("""
                        INSERT OR REPLACE INTO long_term_memory 
                        (memory_id, memory_type, content, related_contexts, 
                         strength, frequency, last_accessed, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        memory.memory_id,
                        memory.memory_type,
                        json.dumps(memory.content, default=str),
                        json.dumps(memory.related_contexts),
                        memory.strength,
                        memory.frequency,
                        memory.last_accessed.isoformat(),
                        memory.created_at.isoformat()
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist long-term memories: {e}")
    
    def persist_session(self, session_id: str):
        """セッションをデータベースに永続化"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        try:
            with self._get_db_connection() as conn:
                # セッション情報を保存
                conn.execute("""
                    INSERT OR REPLACE INTO session_contexts
                    (session_id, user_id, mode, created_at, last_accessed, 
                     agent_states, task_history, preferences, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.user_id,
                    session.mode,
                    session.created_at.isoformat(),
                    session.last_accessed.isoformat(),
                    json.dumps(session.agent_states, default=str),
                    json.dumps(session.task_history, default=str),
                    json.dumps(session.preferences, default=str),
                    json.dumps(session.metadata, default=str)
                ))
                
                # コンテキストエントリを保存
                for entry in session.context_entries.values():
                    conn.execute("""
                        INSERT OR REPLACE INTO context_entries
                        (entry_id, session_id, agent_id, task_id, context_type,
                         content, metadata, created_at, updated_at, expires_at,
                         access_count, importance_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.entry_id,
                        entry.session_id,
                        entry.agent_id,
                        entry.task_id,
                        entry.context_type,
                        json.dumps(entry.content, default=str),
                        json.dumps(entry.metadata, default=str),
                        entry.created_at.isoformat(),
                        entry.updated_at.isoformat(),
                        entry.expires_at.isoformat() if entry.expires_at else None,
                        entry.access_count,
                        entry.importance_score
                    ))
                
                conn.commit()
                self.stats["contexts_persisted"] += len(session.context_entries)
                logger.info(f"Persisted session {session_id} with {len(session.context_entries)} contexts")
                
        except Exception as e:
            logger.error(f"Failed to persist session {session_id}: {e}")
    
    def load_session(self, session_id: str) -> Optional[SessionContext]:
        """セッションをデータベースから読み込み"""
        try:
            with self._get_db_connection() as conn:
                # セッション情報を取得
                cursor = conn.execute(
                    "SELECT * FROM session_contexts WHERE session_id = ?",
                    (session_id,)
                )
                session_row = cursor.fetchone()
                
                if not session_row:
                    return None
                
                # セッションオブジェクトを作成
                session = SessionContext(
                    session_id=session_row[0],
                    user_id=session_row[1],
                    mode=session_row[2],
                    created_at=datetime.fromisoformat(session_row[3]),
                    last_accessed=datetime.fromisoformat(session_row[4]),
                    agent_states=json.loads(session_row[5]) if session_row[5] else {},
                    task_history=json.loads(session_row[6]) if session_row[6] else [],
                    preferences=json.loads(session_row[7]) if session_row[7] else {},
                    metadata=json.loads(session_row[8]) if session_row[8] else {}
                )
                
                # コンテキストエントリを取得
                cursor = conn.execute(
                    "SELECT * FROM context_entries WHERE session_id = ?",
                    (session_id,)
                )
                
                for row in cursor.fetchall():
                    entry = ContextEntry(
                        entry_id=row[0],
                        session_id=row[1],
                        agent_id=row[2],
                        task_id=row[3],
                        context_type=row[4],
                        content=json.loads(row[5]),
                        metadata=json.loads(row[6]) if row[6] else {},
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        expires_at=datetime.fromisoformat(row[9]) if row[9] else None,
                        access_count=row[10],
                        importance_score=row[11]
                    )
                    session.context_entries[entry.entry_id] = entry
                
                self.active_sessions[session_id] = session
                logger.info(f"Loaded session {session_id} with {len(session.context_entries)} contexts")
                return session
                
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def cleanup_expired_contexts(self):
        """期限切れのコンテキストを削除"""
        now = datetime.now()
        cleaned_count = 0
        
        with self.lock:
            # アクティブセッションから削除
            for session in self.active_sessions.values():
                expired_entries = [
                    entry_id for entry_id, entry in session.context_entries.items()
                    if entry.expires_at and now > entry.expires_at
                ]
                
                for entry_id in expired_entries:
                    del session.context_entries[entry_id]
                    cleaned_count += 1
            
            # キャッシュから削除
            expired_cache_keys = []
            for key, entry in self.context_cache.items():
                if hasattr(entry, 'expires_at') and entry.expires_at and now > entry.expires_at:
                    expired_cache_keys.append(key)
            
            for key in expired_cache_keys:
                del self.context_cache[key]
                cleaned_count += 1
        
        # データベースから削除
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM context_entries WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (now.isoformat(),)
                )
                cleaned_count += cursor.rowcount
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to cleanup expired contexts from DB: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired contexts")
        
        return cleaned_count
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """コンテキスト統計を取得"""
        with self.lock:
            active_contexts = sum(
                len(session.context_entries) for session in self.active_sessions.values()
            )
            
            context_types = defaultdict(int)
            for session in self.active_sessions.values():
                for entry in session.context_entries.values():
                    context_types[entry.context_type] += 1
            
            return {
                "active_sessions": len(self.active_sessions),
                "active_contexts": active_contexts,
                "long_term_memories": len(self.long_term_memory),
                "cache_size": len(self.context_cache),
                "context_types": dict(context_types),
                "stats": self.stats.copy()
            }
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        with self.lock:
            # すべてのアクティブセッションを永続化
            for session_id in list(self.active_sessions.keys()):
                self.persist_session(session_id)
            
            # 期限切れコンテキストを削除
            self.cleanup_expired_contexts()
            
            # メモリをクリア
            self.active_sessions.clear()
            self.context_cache.clear()
            
        logger.info("Advanced Context Manager cleaned up")
