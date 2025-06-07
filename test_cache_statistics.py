"""
RAGシステムのキャッシュ統計を確認する簡易テスト
"""

import asyncio
import json
import logging
import sys

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# RAG関連のインポート
from ai.rag.rag_ai_service import RAGAIService
from ai.cache_manager import get_cache_manager

async def test_cache_statistics():
    """キャッシュ統計の確認テスト"""
    try:
        # 設定の準備
        config = {
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,
                "max_size_mb": 100
            },
            "monitor": {
                "enabled": True,
                "cleanup_interval_seconds": 60,
                "process_timeout_seconds": 300,
                "max_history_count": 100
            },
            "rag": {
                "knowledge_base_path": "./ai/rag/test_knowledge_base",
                "vector_store_path": "./ai/rag/test_vector_store",
                "embedding_model": "local",
                "skip_reindex": True,
                "max_documents": 5
            }
        }
        
        # RAGサービスの初期化
        logger.info("RAGサービスを初期化中...")
        rag_service = RAGAIService(config)
        initialized = await rag_service.initialize()
        
        if not initialized:
            logger.error("RAGサービス初期化失敗")
            return
        
        # キャッシュ統計の確認
        cache_manager = await get_cache_manager()
        cache_stats = await cache_manager.get_stats()
        
        logger.info("現在のキャッシュ統計:")
        logger.info(f"- キャッシュ有効: {cache_stats.get('enabled', False)}")
        logger.info(f"- キャッシュサイズ: {cache_stats.get('size_mb', 0):.2f}MB")
        logger.info(f"- エントリ数: {cache_stats.get('entries', 0)}")
        logger.info(f"- ヒット数: {cache_stats.get('hits', 0)}")
        logger.info(f"- ミス数: {cache_stats.get('misses', 0)}")
        
        # RAG統計の確認
        rag_stats = await rag_service.get_stats()
        if "rag_system" in rag_stats:
            logger.info("\nRAGシステム統計:")
            if "index_status" in rag_stats["rag_system"]:
                index_status = rag_stats["rag_system"]["index_status"]
                logger.info(f"- 総チャンク数: {index_status.get('total_chunks', 0)}")
                logger.info(f"- インデックス済み: {index_status.get('indexed_chunks', 0)}")
                logger.info(f"- 再インデックス必要: {index_status.get('needs_reindex', False)}")
          # プロセス監視統計の確認
        from ai.process_monitor import get_process_monitor
        process_monitor = await get_process_monitor()
        process_stats = await process_monitor.get_stats()
        
        logger.info("\nプロセス監視統計:")
        logger.info(f"- アクティブプロセス: {process_stats.get('active_processes', 0)}")
        logger.info(f"- 完了プロセス: {process_stats.get('completed_processes', 0)}")
        logger.info(f"- 失敗プロセス: {process_stats.get('failed_processes', 0)}")
        logger.info(f"- タイムアウトプロセス: {process_stats.get('timed_out_processes', 0)}")
        
        logger.info("\nテスト完了")
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_cache_statistics())
