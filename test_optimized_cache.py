"""
最適化された類似キャッシュ機能の統合テスト

このスクリプトでは、高速化されたAI処理キャッシュ機構の動作を検証します。
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 最適化された類似キャッシュ
from ai.optimized_cache_search import (
    OptimizedEmbeddingService, 
    OptimizedSimilarityCache,
    get_optimized_similarity_cache
)

# 既存のキャッシュマネージャー
from ai.cache_manager import AICacheManager
from ai.enhanced_cache_manager import EnhancedAICacheManager

async def test_optimized_embedding_service():
    """最適化されたエンベディングサービスのテスト"""
    logger.info("=== 最適化されたエンベディングサービステスト開始 ===")
    
    # サービスの初期化
    embedding_service = OptimizedEmbeddingService()
    
    # サンプルテキスト
    sample_texts = [
        "AIによるレポート自動生成機能について教えてください。",
        "機械学習モデルの学習方法を教えてください。",
        "深層学習の最新トレンドは何ですか？",
        "Python言語でデータ分析を行う方法は？"
    ]
    
    # パフォーマンス計測用の関数
    async def measure_time(func, *args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        return result, end - start
    
    # 連続エンベディング生成のパフォーマンステスト
    total_time = 0
    for text in sample_texts:
        _, elapsed = await measure_time(embedding_service.get_embedding, text)
        logger.info(f"テキスト「{text[:20]}...」のエンベディング生成: {elapsed:.4f}秒")
        total_time += elapsed
    
    # 連続エンベディング生成（2回目、キャッシュ利用）
    cached_total_time = 0
    for text in sample_texts:
        _, elapsed = await measure_time(embedding_service.get_embedding, text)
        logger.info(f"[キャッシュ利用] テキスト「{text[:20]}...」のエンベディング生成: {elapsed:.4f}秒")
        cached_total_time += elapsed
    
    logger.info(f"初回エンベディング生成合計時間: {total_time:.4f}秒")
    logger.info(f"キャッシュ利用時の合計時間: {cached_total_time:.4f}秒")
    logger.info(f"速度向上率: {total_time/cached_total_time:.2f}倍")
    
    logger.info("=== エンベディングサービステスト完了 ===\n")
    return embedding_service

async def test_optimized_similarity_cache(embedding_service):
    """最適化された類似度キャッシュのテスト"""
    logger.info("=== 最適化された類似度キャッシュテスト開始 ===")
    
    # テスト用キャッシュディレクトリ
    cache_dir = Path("./test_optimized_cache")
    
    # 類似度キャッシュの初期化
    similarity_cache = OptimizedSimilarityCache(
        embedding_service=embedding_service,
        cache_dir=cache_dir,
        similarity_threshold=0.7
    )
    
    # テストデータ
    test_data = {
        "query1": "AIによるドキュメント自動生成の方法を教えてください",
        "query2": "機械学習を使った文書の自動作成について知りたいです",
        "query3": "ディープラーニングの基礎概念について解説してください",
        "query4": "自然言語処理で文章要約を行う手法は？",
        "query5": "全く関係のない別のトピックについての質問です"
    }
    
    # キャッシュにテストデータを追加
    for key, query in test_data.items():
        success = await similarity_cache.add_query_embedding(key, query)
        logger.info(f"キャッシュ追加 ({key}): {'成功' if success else '失敗'}")
    
    # 類似クエリテスト
    similar_queries = [
        "AIを使って文書を自動生成したい",
        "機械学習でドキュメントを作成する方法",
        "ディープラーニングとは何ですか？基本を教えてください",
        "NLPを使った文章の要約方法について",
        "無関係な質問: 株価予測について教えてください"
    ]
    
    # パフォーマンス測定
    start_time = time.time()
    
    for i, query in enumerate(similar_queries):
        cache_key, similarity = await similarity_cache.find_similar_cache(query)
        expected_key = f"query{i+1}"
        match = "✓" if cache_key == expected_key else "✗"
        
        logger.info(f"クエリ: {query[:30]}...")
        logger.info(f"  類似キャッシュ: {cache_key}, 類似度: {similarity:.4f} {match}")
    
    # 複数回実行してキャッシュ効果を測定
    logger.info("キャッシュ効果測定（複数回検索）...")
    
    repeated_query = similar_queries[0]
    
    # 1回目（通常検索）
    start = time.time()
    cache_key1, _ = await similarity_cache.find_similar_cache(repeated_query)
    first_search_time = time.time() - start
    
    # 2回目（ハッシュキャッシュが効くはず）
    start = time.time()
    cache_key2, _ = await similarity_cache.find_similar_cache(repeated_query)
    second_search_time = time.time() - start
    
    logger.info(f"初回検索時間: {first_search_time:.4f}秒")
    logger.info(f"2回目検索時間: {second_search_time:.4f}秒")
    if second_search_time > 0:
        logger.info(f"速度向上率: {first_search_time/second_search_time:.2f}倍")
    
    logger.info("=== 類似度キャッシュテスト完了 ===\n")
    return similarity_cache

async def test_integrated_cache_usage():
    """キャッシュ機能の統合テスト"""
    logger.info("=== AI処理キャッシュ機構 統合テスト開始 ===")
    
    # シングルトンキャッシュインスタンスの取得
    optimized_cache = await get_optimized_similarity_cache(
        cache_dir="./integrated_cache",
        similarity_threshold=0.75
    )
    
    # テストデータ
    test_key_data = [
        {"query": "AIによる効率的な開発支援ツールについて教えてください", "model": "test_model"},
        {"query": "自然言語処理技術を活用したコード生成の最新動向", "model": "test_model"},
        {"query": "機械学習モデルのデプロイメントパイプライン構築方法", "model": "test_model"}
    ]
    
    test_results = [
        {"text": "AIによる開発支援ツールには、次のようなものがあります...", "tokens": 150},
        {"text": "自然言語処理を活用したコード生成技術は近年急速に発展しており...", "tokens": 180},
        {"text": "機械学習モデルのデプロイメントパイプラインを構築するには...", "tokens": 200}
    ]
    
    # データをキャッシュに追加
    for i, (key_data, result) in enumerate(zip(test_key_data, test_results)):
        # キャッシュキーの生成
        import hashlib
        import json
        key_str = json.dumps(key_data, sort_keys=True)
        cache_key = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
        # エンベディング追加
        await optimized_cache.add_query_embedding(cache_key, key_data["query"])
        logger.info(f"サンプルデータ {i+1} をキャッシュに追加しました")
    
    # 類似クエリテスト
    test_queries = [
        "AI開発支援ツールの最新情報を知りたいです",
        "NLPを使ったコード自動生成について教えてください",
        "機械学習モデルのデプロイパイプラインのベストプラクティス",
        "全く関係のない質問：天気予報APIについて教えてください"
    ]
    
    # 各クエリで類似キャッシュをテスト
    for i, query in enumerate(test_queries):
        logger.info(f"\nテストクエリ {i+1}: {query}")
        
        # 類似キャッシュを検索
        start_time = time.time()
        cache_key, similarity = await optimized_cache.find_similar_cache(query)
        search_time = time.time() - start_time
        
        if cache_key:
            logger.info(f"類似キャッシュヒット: キー={cache_key}, 類似度={similarity:.4f}, 検索時間={search_time:.4f}秒")
        else:
            logger.info(f"類似キャッシュミス: 検索時間={search_time:.4f}秒")
    
    logger.info("=== 統合テスト完了 ===")

async def test_cache_manager_comparison():
    """既存のキャッシュマネージャーと最適化版の比較テスト"""
    logger.info("=== キャッシュマネージャー比較テスト ===")
    
    # キャッシュディレクトリ
    cache_dir = Path("./comparison_cache")
    
    # 1. 基本キャッシュマネージャー
    basic_cache = AICacheManager(
        cache_dir=str(cache_dir / "basic"),
        ttl_seconds=3600,
        enable_cache=True
    )
    
    # 2. 拡張キャッシュマネージャー
    try:
        enhanced_cache = EnhancedAICacheManager(
            cache_dir=str(cache_dir / "enhanced"),
            ttl_seconds=3600,
            enable_cache=True,
            use_similarity=True
        )
    except Exception as e:
        logger.warning(f"拡張キャッシュマネージャーの初期化エラー: {e}")
        enhanced_cache = None
    
    # 3. 最適化キャッシュ
    optimized_cache = await get_optimized_similarity_cache(
        cache_dir=str(cache_dir / "optimized"),
        similarity_threshold=0.75
    )
    
    # テスト用キーデータと結果
    key_data = {"query": "AI開発におけるパフォーマンス最適化手法", "model": "test_model"}
    result_data = {"answer": "AI開発のパフォーマンス最適化には複数のアプローチがあります...", "tokens": 180}
    
    # 類似クエリのセット
    similar_queries = [
        "AI開発におけるパフォーマンス最適化手法",  # 完全一致
        "AIアプリケーションの実行速度を向上させるには？",  # 類似
        "機械学習モデルの最適化方法について教えてください",  # やや類似
        "ディープラーニングのパフォーマンスチューニング",  # やや類似
        "全く関係のない質問"  # 関連なし
    ]
    
    # 基本キャッシュにデータを設定
    logger.info("基本キャッシュにデータを設定")
    await basic_cache.set_cache(key_data, result_data)
    
    # 拡張キャッシュにデータを設定
    if enhanced_cache:
        logger.info("拡張キャッシュにデータを設定")
        await enhanced_cache.set_cache(key_data, result_data)
    
    # 最適化キャッシュにデータを設定
    logger.info("最適化キャッシュにデータを設定")
    import hashlib
    import json
    key_str = json.dumps(key_data, sort_keys=True)
    cache_key = hashlib.md5(key_str.encode('utf-8')).hexdigest()
    await optimized_cache.add_query_embedding(cache_key, key_data["query"])
    
    # 各クエリで検索時間を比較
    logger.info("\n検索時間比較:")
    
    for query in similar_queries:
        logger.info(f"\nクエリ: {query}")
        test_key = {"query": query, "model": "test_model"}
        
        # 基本キャッシュテスト
        start_time = time.time()
        basic_hit, _ = await basic_cache.get_cache(test_key)
        basic_time = time.time() - start_time
        logger.info(f"基本キャッシュ: ヒット={basic_hit}, 時間={basic_time:.6f}秒")
        
        # 拡張キャッシュテスト
        if enhanced_cache:
            start_time = time.time()
            enhanced_hit, _ = await enhanced_cache.get_cache(test_key)
            enhanced_time = time.time() - start_time
            logger.info(f"拡張キャッシュ: ヒット={enhanced_hit}, 時間={enhanced_time:.6f}秒")
        
        # 最適化キャッシュテスト
        # キー生成
        key_str = json.dumps(test_key, sort_keys=True)
        test_cache_key = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
        start_time = time.time()
        similar_key, similarity = await optimized_cache.find_similar_cache(query)
        optimized_time = time.time() - start_time
        optimized_hit = similar_key is not None
        logger.info(f"最適化キャッシュ: ヒット={optimized_hit}, 類似度={similarity if optimized_hit else 0:.4f}, 時間={optimized_time:.6f}秒")
    
    logger.info("=== 比較テスト完了 ===")

async def main():
    """メイン実行関数"""
    logger.info("AI処理キャッシュ機構 最適化テスト開始")
    
    try:
        # 最適化されたエンベディングサービスのテスト
        embedding_service = await test_optimized_embedding_service()
        
        # 最適化された類似度キャッシュのテスト
        await test_optimized_similarity_cache(embedding_service)
        
        # 統合テスト
        await test_integrated_cache_usage()
        
        # 比較テスト
        await test_cache_manager_comparison()
        
        logger.info("全てのテストが完了しました")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
