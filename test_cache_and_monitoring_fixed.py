"""
RAGシステムのキャッシュ機構とプロセス監視のテスト
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# RAG関連のインポート
from ai.rag.rag_ai_service import RAGAIService
from ai.process_monitor import get_process_monitor

async def process_event_handler(process_info):
    """プロセスイベントハンドラー"""
    logger.info(f"プロセスイベント: {process_info.process_id}, "
                f"タイプ: {process_info.process_type}, "
                f"状態: {process_info.status}, "
                f"進捗: {process_info.progress:.2f}")

async def print_stats(rag_service):
    """統計情報の表示"""
    stats = await rag_service.get_stats()
    
    # 見やすく整形
    formatted_stats = json.dumps(stats, indent=2, ensure_ascii=False)
    logger.info(f"RAGサービス統計:\n{formatted_stats}")

async def test_cache_and_monitoring():
    """キャッシュとモニタリングのテスト"""
    try:        # 設定の準備
        config = {
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,  # 1時間
                "max_size_mb": 100
            },
            "monitor": {
                "enabled": True,
                "cleanup_interval_seconds": 60,
                "process_timeout_seconds": 300,
                "max_history_count": 100
            },
            "rag": {
                "knowledge_base_path": "./ai/rag/test_knowledge_base",  # 小さいテスト用
                "vector_store_path": "./ai/rag/test_vector_store",      # テスト用
                "embedding_model": "local",
                "skip_reindex": True,                                   # 再インデックス防止
                "max_documents": 5                                      # 最大文書数制限
            }
        }
        
        # RAGサービスの初期化
        logger.info("RAGサービスを初期化中...")
        rag_service = RAGAIService(config)
        initialized = await rag_service.initialize()
        
        if not initialized:
            logger.error("RAGサービス初期化失敗")
            return
            
        logger.info("RAGサービス初期化成功")
        
        # プロセスモニターの取得とイベントハンドラー登録
        monitor = await get_process_monitor()
        monitor.add_event_handler("started", process_event_handler)
        monitor.add_event_handler("completed", process_event_handler)
        monitor.add_event_handler("failed", process_event_handler)
        
        # 初期状態の統計確認
        await print_stats(rag_service)
        
        # テスト1: 最初のクエリ（キャッシュミス）
        logger.info("-" * 50)
        logger.info("テスト1: 最初のクエリ実行（キャッシュミス期待）")
        
        result1 = await rag_service.generate_with_rag(
            query="AIエージェントの最適化方法について教えてください",
            mode="interactive"
        )
        
        logger.info(f"テスト1結果: ステータス={result1.get('success')}, "
                    f"返答長={len(result1.get('response', ''))}")
        
        # テスト2: 同一クエリ（キャッシュヒット）
        logger.info("-" * 50)
        logger.info("テスト2: 同一クエリ実行（キャッシュヒット期待）")
        
        result2 = await rag_service.generate_with_rag(
            query="AIエージェントの最適化方法について教えてください",
            mode="interactive"
        )
        
        logger.info(f"テスト2結果: ステータス={result2.get('success')}, "
                    f"返答長={len(result2.get('response', ''))}")
        
        # テスト3: 異なるクエリ（キャッシュミス）
        logger.info("-" * 50)
        logger.info("テスト3: 異なるクエリ実行（キャッシュミス期待）")
        
        result3 = await rag_service.generate_with_rag(
            query="プロンプトエンジニアリングのベストプラクティス",
            mode="autonomous"
        )
        
        logger.info(f"テスト3結果: ステータス={result3.get('success')}, "
                    f"返答長={len(result3.get('response', ''))}")
        
        # テスト4: ストリーミング生成のテスト（キャッシュミス）
        logger.info("-" * 50)
        logger.info("テスト4: ストリーミング生成テスト（キャッシュミス期待）")
        
        query = "ディープラーニングの最新トレンドについて教えてください"
        stream_chunks = []
        
        # ストリーミング生成（キャッシュミス）
        async for chunk in rag_service.generate_stream_with_rag(
            query=query,
            mode="interactive"
        ):
            if chunk.get("content"):
                # 長いコンテンツは省略して表示
                content_preview = chunk["content"][:30] + "..." if len(chunk.get("content", "")) > 30 else chunk.get("content", "")
                logger.info(f"ストリームチャンク: {content_preview}")
            elif "status" in chunk:
                logger.info(f"ストリームステータス: {chunk['status']}, メッセージ: {chunk.get('message', 'なし')}")
            
            stream_chunks.append(chunk)
        
        logger.info(f"ストリーミング生成: 合計{len(stream_chunks)}チャンク")
        
        # テスト5: 同一クエリでのストリーミング生成（キャッシュヒット）
        logger.info("-" * 50)
        logger.info("テスト5: 同一クエリでのストリーミング生成テスト（キャッシュヒット期待）")
        
        cached_stream_chunks = []
        async for chunk in rag_service.generate_stream_with_rag(
            query=query,
            mode="interactive"
        ):
            if "from_cache" in chunk:
                logger.info(f"キャッシュヒット: {chunk.get('status', '')}")
            elif chunk.get("content"):
                content_preview = chunk["content"][:30] + "..." if len(chunk.get("content", "")) > 30 else chunk.get("content", "")
                logger.info(f"キャッシュからのチャンク: {content_preview}")
            
            cached_stream_chunks.append(chunk)
        
        logger.info(f"キャッシュヒット: 合計{len(cached_stream_chunks)}チャンク")
        
        # 中間統計情報
        logger.info("-" * 50)
        logger.info("中間統計情報:")
        await print_stats(rag_service)
        
        # キャッシュと監視の連携テスト
        logger.info("-" * 50)
        logger.info("テスト6: 長時間処理のタイムアウト監視テスト")
        
        # 処理完了前に統計情報を確認
        process_stats = await monitor.get_statistics()
        logger.info(f"現在のアクティブプロセス数: {process_stats.get('active_processes', 0)}")
        logger.info(f"累積プロセス数: {process_stats.get('total_processes', 0)}")
        
        # 最終状態の統計確認
        logger.info("-" * 50)
        logger.info("最終統計情報:")
        await print_stats(rag_service)
        
        # プロセス履歴の確認
        logger.info("-" * 50)
        logger.info("プロセス履歴:")
        process_history = await monitor.get_process_history(limit=10)
        for idx, process in enumerate(process_history, 1):
            duration = "N/A"
            if process.get("start_time") and process.get("end_time"):
                start = datetime.fromisoformat(process["start_time"])
                end = datetime.fromisoformat(process["end_time"])
                duration = (end - start).total_seconds()
                
            logger.info(f"プロセス #{idx}: タイプ={process['process_type']}, "
                        f"状態={process['status']}, "
                        f"所要時間={duration}秒")
        
    except Exception as e:
        logger.error(f"テスト実行中のエラー: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_cache_and_monitoring())
