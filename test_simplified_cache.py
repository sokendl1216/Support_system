"""
シンプルキャッシュマネージャーのテストスクリプト

このスクリプトは、高性能キャッシュマネージャーの簡略版をテストします。
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

# 基本キャッシュマネージャー
from ai.cache_manager import AICacheManager
from ai.simplified_high_performance_cache import SimplifiedHighPerformanceCache

async def test_cache_performance():
    """キャッシュのパフォーマンステスト"""
    logger.info("=== キャッシュパフォーマンステスト開始 ===")
    
    # テスト用キャッシュディレクトリ
    cache_dir = Path("./test_cache")
    
    # 基本キャッシュの初期化
    basic_cache = AICacheManager(
        cache_dir=str(cache_dir / "basic"),
        ttl_seconds=3600,
        max_cache_size_mb=100,
        enable_cache=True
    )
    
    # 高速キャッシュの初期化
    high_perf_cache = SimplifiedHighPerformanceCache(
        cache_dir=str(cache_dir / "high_perf"),
        ttl_seconds=3600,
        max_cache_size_mb=100,
        enable_cache=True
    )
    
    # テストデータ
    test_data = [
        {"query": f"テスト質問 {i}", "model": "test-model"} 
        for i in range(10)
    ]
    
    test_results = [
        {"answer": f"テスト回答 {i}", "tokens": 100 + i} 
        for i in range(10)
    ]
    
    # 書き込みパフォーマンス測定
    logger.info("書き込みパフォーマンステスト...")
    
    # 基本キャッシュへの書き込み
    basic_write_start = time.time()
    for i in range(len(test_data)):
        await basic_cache.set_cache(test_data[i], test_results[i])
    basic_write_time = time.time() - basic_write_start
    
    # 高速キャッシュへの書き込み
    high_perf_write_start = time.time()
    for i in range(len(test_data)):
        await high_perf_cache.set_cache(test_data[i], test_results[i])
    high_perf_write_time = time.time() - high_perf_write_start
    
    logger.info(f"基本キャッシュ書き込み時間: {basic_write_time:.6f}秒")
    logger.info(f"高速キャッシュ書き込み時間: {high_perf_write_time:.6f}秒")
    
    # 読み込みパフォーマンス測定
    logger.info("\n読み込みパフォーマンステスト (初回)...")
    
    # 基本キャッシュからの読み込み
    basic_read_start = time.time()
    for i in range(len(test_data)):
        hit, _ = await basic_cache.get_cache(test_data[i])
    basic_read_time = time.time() - basic_read_start
    
    # 高速キャッシュからの読み込み
    high_perf_read_start = time.time()
    for i in range(len(test_data)):
        hit, _ = await high_perf_cache.get_cache(test_data[i])
    high_perf_read_time = time.time() - high_perf_read_start
    
    logger.info(f"基本キャッシュ初回読み込み時間: {basic_read_time:.6f}秒")
    logger.info(f"高速キャッシュ初回読み込み時間: {high_perf_read_time:.6f}秒")
    
    # メモリキャッシュ効果の測定
    logger.info("\n読み込みパフォーマンステスト (2回目/メモリキャッシュ)...")
    
    # 基本キャッシュからの2回目の読み込み
    basic_read2_start = time.time()
    for i in range(len(test_data)):
        hit, _ = await basic_cache.get_cache(test_data[i])
    basic_read2_time = time.time() - basic_read2_start
    
    # 高速キャッシュからの2回目の読み込み
    high_perf_read2_start = time.time()
    for i in range(len(test_data)):
        hit, _ = await high_perf_cache.get_cache(test_data[i])
    high_perf_read2_time = time.time() - high_perf_read2_start
    
    logger.info(f"基本キャッシュ2回目読み込み時間: {basic_read2_time:.6f}秒")
    logger.info(f"高速キャッシュ2回目読み込み時間: {high_perf_read2_time:.6f}秒")
    
    # ゼロ除算を防止
    if high_perf_read2_time > 0:
        speedup = high_perf_read_time / high_perf_read2_time
        logger.info(f"メモリキャッシュによる高速化: {speedup:.2f}倍")
    else:
        logger.info("メモリキャッシュによる高速化: 計測不能（読み込み時間がゼロ）")
    
    # 統計情報の確認
    basic_stats = await basic_cache.get_stats()
    high_perf_stats = await high_perf_cache.get_stats()
    
    logger.info("\n基本キャッシュ統計:")
    logger.info(f"総リクエスト数: {basic_stats.get('total_requests', 0)}")
    logger.info(f"ヒット数: {basic_stats.get('hits', 0)}")
    logger.info(f"ヒット率: {basic_stats.get('hit_ratio', 0):.2%}")
    
    logger.info("\n高速キャッシュ統計:")
    logger.info(f"総リクエスト数: {high_perf_stats.get('total_requests', 0)}")
    logger.info(f"ディスクヒット数: {high_perf_stats.get('hits', 0)}")
    logger.info(f"メモリヒット数: {high_perf_stats.get('memory_hits', 0)}")
    logger.info(f"総ヒット率: {high_perf_stats.get('hit_ratio', 0):.2%}")
    
    logger.info("=== キャッシュパフォーマンステスト完了 ===")

async def main():
    """メイン関数"""
    try:
        logger.info("シンプル高性能キャッシュのテストを開始します")
        await test_cache_performance()
        logger.info("テスト完了")
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
