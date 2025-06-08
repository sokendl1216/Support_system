"""
キャッシュ機能テスト用スクリプト

このスクリプトは、類似クエリ検出を含む拡張されたキャッシュ機能をテストします。
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
import time
import random

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# AIキャッシュのインポート
from ai.cache_manager import AICacheManager
from ai.cache_similarity import EmbeddingService, SimilarityCache

async def test_basic_cache():
    """基本的なキャッシュ機能のテスト"""
    logger.info("基本的なキャッシュ機能のテスト開始")
    
    # キャッシュマネージャーを初期化
    cache_dir = Path("./test_cache")
    cache_mgr = AICacheManager(
        cache_dir=str(cache_dir),
        ttl_seconds=60,  # テスト用に短い時間
        max_cache_size_mb=10,
        enable_cache=True
    )
    
    # テストデータ
    key_data = {"query": "AIによるレポート自動生成方法を教えてください", "model": "test_model"}
    test_data = {"answer": "AIを使ったレポート自動生成には以下の手順があります...", "tokens": 150}
    
    # キャッシュに保存
    success = await cache_mgr.set_cache(key_data, test_data)
    logger.info(f"キャッシュ保存: {'成功' if success else '失敗'}")
    
    # キャッシュから取得
    hit, cached_data = await cache_mgr.get_cache(key_data)
    logger.info(f"キャッシュ取得: {'ヒット' if hit else 'ミス'}, データ一致: {cached_data == test_data}")
    
    # 別のクエリでは取得できないことを確認
    different_key = {"query": "全く別の質問", "model": "test_model"}
    hit, cached_data = await cache_mgr.get_cache(different_key)
    logger.info(f"異なるキーでの取得: {'ヒット' if hit else 'ミス（正常）'}")
    
    # 統計情報取得
    stats = await cache_mgr.get_stats()
    logger.info(f"キャッシュ統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
async def test_similarity_cache():
    """類似クエリ検出機能のテスト"""
    logger.info("類似クエリ検出機能のテスト開始")
    
    # エンベディングサービス初期化
    embedding_service = EmbeddingService()
    
    # 類似キャッシュ初期化
    cache_dir = Path("./test_cache")
    cache_dir.mkdir(exist_ok=True, parents=True)
    
    similarity_cache = SimilarityCache(
        embedding_service=embedding_service,
        cache_dir=cache_dir,
        similarity_threshold=0.85
    )
    
    # テストクエリ
    original_query = "AIを使って文書要約を行うベストプラクティスは何ですか？"
    cache_key = "test_key_1"
    
    # エンベディングを追加
    await similarity_cache.add_query_embedding(cache_key, original_query)
    logger.info(f"クエリのエンベディングを追加: {original_query}")
    
    # 類似クエリで検索
    similar_queries = [
        "AIによる文書要約の最良の方法を教えてください",
        "文書要約のためのAIテクニックのベストプラクティスとは？",
        "AIを活用した効果的な文書要約方法について",
        "全く関係のない別の質問です"
    ]
    
    for query in similar_queries:
        key, similarity = await similarity_cache.find_similar_cache(query)
        status = "類似" if key else "非類似"
        logger.info(f"クエリ: '{query}' -> {status} (類似度: {similarity:.4f})")
    
    # エンベディング削除のテスト
    removed = await similarity_cache.remove_embedding(cache_key)
    logger.info(f"エンベディング削除: {'成功' if removed else '失敗'}")
    
    # 削除後の検索
    key, similarity = await similarity_cache.find_similar_cache(similar_queries[0])
    logger.info(f"削除後の検索: キャッシュキー={key}, 類似度={similarity:.4f}")

async def test_integrated_similarity_cache():
    """類似クエリ検出とキャッシュ機能の統合テスト"""
    logger.info("統合シミュレーションテスト開始")
    
    cache_dir = Path("./test_integrated_cache")
    cache_dir.mkdir(exist_ok=True, parents=True)
    
    # エンベディングサービス
    embedding_service = EmbeddingService()
    
    # 類似キャッシュ
    similarity_cache = SimilarityCache(
        embedding_service=embedding_service,
        cache_dir=cache_dir,
        similarity_threshold=0.8  # テスト用に少し低めの閾値
    )
    
    # キャッシュマネージャー
    cache_mgr = AICacheManager(
        cache_dir=str(cache_dir),
        ttl_seconds=3600,
        max_cache_size_mb=10,
        enable_cache=True
    )
    
    # シミュレーション用のクエリベース
    base_queries = [
        "Pythonでウェブスクレイピングを行う方法",
        "機械学習モデルの評価指標について",
        "JavaScriptのプロミスとasync/await",
        "データベース正規化の重要性",
        "UIデザインの基本原則"
    ]
    
    # 回答シミュレーション関数
    async def simulate_ai_response(query):
        """AIからの回答をシミュレート"""
        # 実際のAI呼び出しの代わりに、クエリから疑似回答を生成
        await asyncio.sleep(0.2)  # 処理時間のシミュレーション
        return {
            "answer": f"{query}についての回答です。この内容はAIによって生成されました。",
            "tokens": random.randint(100, 500),
            "processing_time": random.uniform(0.5, 2.0)
        }
    
    # オリジナルクエリでキャッシュを作成
    logger.info("オリジナルクエリをキャッシュに保存中...")
    for i, query in enumerate(base_queries):
        key_data = {"query": query, "model": "test_model"}
        cache_key = cache_mgr._generate_cache_key(key_data)
        
        # AIからの回答をシミュレート
        response = await simulate_ai_response(query)
        
        # キャッシュに保存
        await cache_mgr.set_cache(key_data, response)
        
        # エンベディングも保存
        await similarity_cache.add_query_embedding(cache_key, query)
        
        logger.info(f"[{i+1}/{len(base_queries)}] キャッシュ保存: '{query[:30]}...'")
        
    # 類似クエリでテスト
    similar_queries = [
        "Pythonを使ったウェブスクレイピングのチュートリアル",
        "機械学習のモデル評価方法とメトリクス",
        "JavaScriptでのasync/awaitとPromiseの違い",
        "データベース設計における正規化の利点",
        "効果的なUIデザインのための5つの原則"
    ]
    
    logger.info("\n類似クエリのテスト開始...")
    for i, query in enumerate(similar_queries):
        start_time = time.time()
        
        # 通常のキャッシュチェック
        key_data = {"query": query, "model": "test_model"}
        hit, cached_data = await cache_mgr.get_cache(key_data)
        
        if hit:
            logger.info(f"[{i+1}/{len(similar_queries)}] 完全一致キャッシュヒット: '{query[:30]}...'")
        else:
            # 類似クエリ検索
            cache_key, similarity = await similarity_cache.find_similar_cache(query)
            
            if cache_key:
                # 類似度が十分なら、そのキャッシュを利用
                original_key_data = await cache_mgr._get_key_data_from_cache_key(cache_key)
                hit, cached_data = await cache_mgr.get_cache(original_key_data)
                
                if hit:
                    logger.info(f"[{i+1}/{len(similar_queries)}] 類似キャッシュヒット "
                              f"(類似度: {similarity:.4f}): '{query[:30]}...'")
                else:
                    logger.warning(f"類似キャッシュキー({cache_key})が存在するが、データが見つかりません")
                    
                    # AIからの回答をシミュレート
                    response = await simulate_ai_response(query)
                    await cache_mgr.set_cache(key_data, response)
                    new_cache_key = cache_mgr._generate_cache_key(key_data)
                    await similarity_cache.add_query_embedding(new_cache_key, query)
            else:
                logger.info(f"[{i+1}/{len(similar_queries)}] キャッシュミス: '{query[:30]}...'")
                
                # AIからの回答をシミュレート
                response = await simulate_ai_response(query)
                await cache_mgr.set_cache(key_data, response)
                new_cache_key = cache_mgr._generate_cache_key(key_data)
                await similarity_cache.add_query_embedding(new_cache_key, query)
        
        elapsed_time = time.time() - start_time
        logger.info(f"処理時間: {elapsed_time:.4f}秒\n")
    
    # 統計情報表示
    stats = await cache_mgr.get_stats()
    logger.info(f"キャッシュ統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")

async def main():
    """メイン実行関数"""
    try:
        # 基本的なキャッシュ機能テスト
        await test_basic_cache()
        
        logger.info("\n" + "-" * 50 + "\n")
        
        # 類似クエリ検出機能テスト
        await test_similarity_cache()
        
        logger.info("\n" + "-" * 50 + "\n")
        
        # 統合テスト
        await test_integrated_similarity_cache()
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}", exc_info=True)
    
if __name__ == "__main__":
    asyncio.run(main())
