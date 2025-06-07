"""
優先度ベースのキャッシュ機構をテストするスクリプト
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any

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

async def print_stats(rag_service):
    """統計情報の表示"""
    stats = await rag_service.get_stats()
    
    # 見やすく整形
    formatted_stats = json.dumps(stats, indent=2, ensure_ascii=False)
    logger.info(f"RAGサービス統計:\n{formatted_stats}")

async def test_priority_cache():
    """優先度キャッシュのテスト"""
    try:
        # 設定の準備
        config = {
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,  # 1時間
                "max_size_mb": 100,
                "use_priority": True  # 優先度キャッシュを有効化
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
        logger.info("優先度対応RAGサービスを初期化中...")
        rag_service = RAGAIService(config)
        initialized = await rag_service.initialize()
        
        if not initialized:
            logger.error("RAGサービス初期化失敗")
            return
            
        logger.info("RAGサービス初期化成功")
        
        # 初期状態の統計確認
        await print_stats(rag_service)
        
        # テスト1: 優先度の低いクエリを複数回実行
        logger.info("-" * 50)
        logger.info("テスト1: 優先度の低いクエリを実行")
        
        result1 = await rag_service.generate_with_rag(
            query="AIエージェントの最適化方法について教えてください",
            mode="interactive"
        )
        
        logger.info(f"テスト1結果: ステータス={result1.get('success')}, "
                    f"返答長={len(result1.get('response', ''))}")
        
        # テスト2: 優先度の高いクエリを複数回実行して優先度を上げる
        logger.info("-" * 50)
        logger.info("テスト2: 優先度の高いクエリを複数回実行")
        
        high_priority_query = "プロンプトエンジニアリングのベストプラクティス"
        
        for i in range(5):
            logger.info(f"実行 {i+1}/5: 優先度の高いクエリ")
            result_high = await rag_service.generate_with_rag(
                query=high_priority_query,
                mode="interactive"
            )
            logger.info(f"返答長={len(result_high.get('response', ''))}")
            
        # 中間統計情報
        logger.info("-" * 50)
        logger.info("中間統計情報:")
        await print_stats(rag_service)
        
        # テスト3: キャッシュクリーンアップをシミュレート（小さいキャッシュサイズで再初期化）
        logger.info("-" * 50)
        logger.info("テスト3: キャッシュクリーンアップテスト")
        
        # 小さいキャッシュサイズで新しいクエリを実行して、クリーンアップを引き起こす
        for i in range(10):
            unique_query = f"テストクエリ {i}: AI技術の応用例について教えてください"
            result = await rag_service.generate_with_rag(
                query=unique_query,
                mode="interactive"
            )
            logger.info(f"クエリ {i+1}/10: 応答長={len(result.get('response', ''))}")
            
        # 最終統計情報
        logger.info("-" * 50)
        logger.info("最終統計情報:")
        await print_stats(rag_service)
        
        # テスト4: 優先度の高いクエリがまだキャッシュに残っているか確認
        logger.info("-" * 50)
        logger.info("テスト4: 優先度の高いクエリがキャッシュに残っているかテスト")
        
        high_priority_result = await rag_service.generate_with_rag(
            query=high_priority_query,
            mode="interactive"
        )
        
        is_cached = high_priority_result.get("from_cache", False)
        logger.info(f"優先度の高いクエリはキャッシュから取得できた: {is_cached}")
        
        # テスト5: 優先度の低いクエリがキャッシュから削除されているか確認
        logger.info("-" * 50)
        logger.info("テスト5: 優先度の低いクエリがキャッシュから削除されているかテスト")
        
        low_priority_result = await rag_service.generate_with_rag(
            query="AIエージェントの最適化方法について教えてください",
            mode="interactive"
        )
        
        is_cached = low_priority_result.get("from_cache", False)
        logger.info(f"優先度の低いクエリはキャッシュから取得できた: {is_cached}")
        
    except Exception as e:
        logger.error(f"テスト実行中のエラー: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_priority_cache())
