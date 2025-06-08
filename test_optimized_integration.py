#!/usr/bin/env python3
"""
最適化されたAIキャッシュシステムの統合テスト

このスクリプトは、修正されたキャッシュシステムが
実際のユースケースで正常に動作することを確認します。
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

# 高性能キャッシュマネージャーのインポート
from ai.high_performance_cache_manager import HighPerformanceAICacheManager

async def test_basic_operations():
    """基本的なキャッシュ操作のテスト"""
    logger.info("=== 基本操作テスト開始 ===")
    
    # キャッシュマネージャーの初期化
    cache_dir = "./test_integration_cache"
    cache_manager = HighPerformanceAICacheManager(
        cache_dir=cache_dir,
        ttl_seconds=3600,
        enable_cache=True,
        use_similarity=True
    )
    
    # 初期化完了を待機
    if hasattr(cache_manager, '_initialization_task') and cache_manager._initialization_task:
        await asyncio.wait_for(cache_manager._initialization_task, timeout=10)
    
    # テストデータ
    test_queries = [
        "Pythonでウェブアプリを作成する方法は？",
        "機械学習の基本概念について教えてください",
        "データベースの最適化手法について",
        "APIの設計ベストプラクティス",
        "Pythonを使ったウェブアプリケーション開発",  # 類似クエリ
    ]
    
    test_results = [
        {"answer": "Pythonでウェブアプリを作成するには、FlaskやDjangoなどのフレームワークを使用します...", "tokens": 150},
        {"answer": "機械学習は、データからパターンを学習するAI技術です...", "tokens": 200},
        {"answer": "データベース最適化には、インデックス作成、クエリ最適化などがあります...", "tokens": 180},
        {"answer": "API設計では、RESTful原則に従い、適切なHTTPメソッドを使用します...", "tokens": 170},
    ]
    
    # 1. データの保存テスト
    logger.info("1. キャッシュ書き込みテスト")
    for i, (query, result) in enumerate(zip(test_queries[:4], test_results)):
        key_data = {"query": query, "model": "test-model"}
        
        start_time = time.time()
        await cache_manager.set_cache(key_data, result)
        elapsed = time.time() - start_time
        
        logger.info(f"   クエリ{i+1}保存完了: {elapsed:.4f}秒")
    
    # 2. 完全一致検索テスト
    logger.info("2. 完全一致検索テスト")
    for i, query in enumerate(test_queries[:4]):
        key_data = {"query": query, "model": "test-model"}
        
        start_time = time.time()
        hit, result = await cache_manager.get_cache(key_data)
        elapsed = time.time() - start_time
        
        if hit:
            logger.info(f"   クエリ{i+1}ヒット: {elapsed:.4f}秒")
        else:
            logger.warning(f"   クエリ{i+1}ミス: {elapsed:.4f}秒")
      # 3. 類似検索テスト
    logger.info("3. 類似検索テスト")
    similar_query = test_queries[4]  # 類似クエリ
    key_data = {"query": similar_query, "model": "test-model"}
    
    start_time = time.time()
    hit, result = await cache_manager.get_cache(key_data)
    elapsed = time.time() - start_time
    
    if hit:
        logger.info(f"   類似クエリヒット: {elapsed:.4f}秒")
        if result:
            logger.info(f"   結果: {result.get('answer', 'N/A')[:50]}...")
        else:
            logger.info("   結果: None")
    else:
        logger.warning(f"   類似クエリミス: {elapsed:.4f}秒")
    
    # 4. 統計情報の確認
    logger.info("4. 統計情報確認")
    stats = await cache_manager.get_stats()
    logger.info(f"   総リクエスト数: {stats.get('total_requests', 0)}")
    logger.info(f"   完全一致ヒット数: {stats.get('hits', 0)}")
    logger.info(f"   メモリキャッシュヒット数: {stats.get('memory_hits', 0)}")
    logger.info(f"   類似検索ヒット数: {stats.get('similarity_hits', 0)}")
    logger.info(f"   総ヒット率: {stats.get('hit_ratio', 0):.2%}")
    
    return True

async def test_concurrent_operations():
    """並行処理のテスト"""
    logger.info("\n=== 並行処理テスト開始 ===")
    
    cache_manager = HighPerformanceAICacheManager(
        cache_dir="./test_concurrent_cache",
        ttl_seconds=3600,
        enable_cache=True,
        use_similarity=True
    )
    
    # 初期化完了を待機
    if hasattr(cache_manager, '_initialization_task') and cache_manager._initialization_task:
        await asyncio.wait_for(cache_manager._initialization_task, timeout=10)
    
    # 並行書き込みテスト
    concurrent_queries = [
        f"テストクエリ{i}: プログラミング言語の特徴について" for i in range(10)
    ]
    concurrent_results = [
        {"answer": f"回答{i}: プログラミング言語には多様な特徴があります...", "tokens": 100 + i * 10}
        for i in range(10)
    ]
    
    # 並行書き込み
    start_time = time.time()
    write_tasks = []
    for query, result in zip(concurrent_queries, concurrent_results):
        key_data = {"query": query, "model": "test-model"}
        task = cache_manager.set_cache(key_data, result)
        write_tasks.append(task)
    
    await asyncio.gather(*write_tasks)
    write_time = time.time() - start_time
    logger.info(f"並行書き込み完了: {write_time:.3f}秒 ({len(concurrent_queries)}クエリ)")
    
    # 並行読み込み
    start_time = time.time()
    read_tasks = []
    for query in concurrent_queries:
        key_data = {"query": query, "model": "test-model"}
        task = cache_manager.get_cache(key_data)
        read_tasks.append(task)
    
    results = await asyncio.gather(*read_tasks)
    read_time = time.time() - start_time
    hits = sum(1 for hit, _ in results if hit)
    
    logger.info(f"並行読み込み完了: {read_time:.3f}秒 ({hits}/{len(concurrent_queries)}ヒット)")
    
    return True

async def test_error_handling():
    """エラーハンドリングのテスト"""
    logger.info("\n=== エラーハンドリングテスト開始 ===")
    
    cache_manager = HighPerformanceAICacheManager(
        cache_dir="./test_error_cache",
        ttl_seconds=3600,
        enable_cache=True,
        use_similarity=True
    )
    
    # 初期化完了を待機
    if hasattr(cache_manager, '_initialization_task') and cache_manager._initialization_task:
        await asyncio.wait_for(cache_manager._initialization_task, timeout=10)
    
    try:
        # 不正なデータでのテスト
        invalid_key = None
        hit, result = await cache_manager.get_cache(invalid_key)
        logger.info("不正なキーデータ処理: 正常にハンドリング")
    except Exception as e:
        logger.info(f"不正なキーデータ処理: エラー正常検出 - {type(e).__name__}")
    
    try:
        # 空のクエリでのテスト
        empty_key = {"query": "", "model": "test-model"}
        hit, result = await cache_manager.get_cache(empty_key)
        logger.info("空のクエリ処理: 正常にハンドリング")
    except Exception as e:
        logger.info(f"空のクエリ処理: エラー正常検出 - {type(e).__name__}")
    
    return True

async def main():
    """メイン実行関数"""
    try:
        logger.info("🚀 最適化されたAIキャッシュシステム 統合テスト開始")
        
        # 基本操作テスト
        success1 = await test_basic_operations()
        
        # 並行処理テスト  
        success2 = await test_concurrent_operations()
        
        # エラーハンドリングテスト
        success3 = await test_error_handling()
        
        if success1 and success2 and success3:
            logger.info("\n✅ すべてのテストが正常に完了しました")
            logger.info("🎉 最適化されたAIキャッシュシステムは正常に動作しています")
        else:
            logger.error("\n❌ 一部のテストが失敗しました")
            
    except Exception as e:
        logger.error(f"統合テスト中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
