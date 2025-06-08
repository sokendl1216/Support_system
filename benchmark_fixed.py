"""
高性能キャッシュシステムのベンチマークテスト（修正版）

このスクリプトは、既存のキャッシュシステムと高性能キャッシュシステムを
パフォーマンス面で比較評価します。
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
import json
import random
import os
import shutil

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# キャッシュマネージャーのインポート
from ai.cache_manager import AICacheManager
from ai.simplified_high_performance_cache import SimplifiedHighPerformanceCache
from ai.fixed_high_performance_cache_manager import HighPerformanceAICacheManager

# テスト用データの生成関数
def generate_test_queries(count=50):
    """テスト用のクエリデータを生成"""
    templates = [
        "AIモデルの{aspect}を{action}する方法は？",
        "{domain}における{technology}の活用例について教えてください。",
        "{task}のための最適な{tool}は何ですか？",
        "{language}で{feature}を実装するコードを書いてください。",
        "{product}の{component}に関する問題を解決したい。"
    ]
    
    aspects = ["パフォーマンス", "精度", "応答性", "メモリ使用量", "推論速度", "バッチ処理"]
    actions = ["最適化", "改善", "向上", "分析", "監視", "デバッグ"]
    domains = ["機械学習", "自然言語処理", "コンピュータビジョン", "データサイエンス", "ロボティクス"]
    technologies = ["ディープラーニング", "強化学習", "転移学習", "アンサンブル学習", "オートエンコーダ"]
    tasks = ["データ分析", "画像認識", "テキスト分類", "音声認識", "異常検出"]
    tools = ["TensorFlow", "PyTorch", "scikit-learn", "BERT", "GPT"]
    languages = ["Python", "JavaScript", "Java", "C++", "Go"]
    features = ["並列処理", "非同期処理", "メモリキャッシング", "分散計算", "エラーハンドリング"]
    products = ["ウェブアプリ", "モバイルアプリ", "APIサービス", "バックエンドシステム", "データベース"]
    components = ["認証機能", "キャッシュ層", "APIインターフェース", "クエリエンジン", "UI要素"]
    
    queries = []
    for _ in range(count):
        template = random.choice(templates)
        
        if "{aspect}" in template and "{action}" in template:
            query = template.format(
                aspect=random.choice(aspects),
                action=random.choice(actions)
            )
        elif "{domain}" in template and "{technology}" in template:
            query = template.format(
                domain=random.choice(domains),
                technology=random.choice(technologies)
            )
        elif "{task}" in template and "{tool}" in template:
            query = template.format(
                task=random.choice(tasks),
                tool=random.choice(tools)
            )
        elif "{language}" in template and "{feature}" in template:
            query = template.format(
                language=random.choice(languages),
                feature=random.choice(features)
            )
        elif "{product}" in template and "{component}" in template:
            query = template.format(
                product=random.choice(products),
                component=random.choice(components)
            )
        
        queries.append(query)
    
    return queries

def generate_test_results(count=50):
    """テスト用の結果データを生成"""
    results = []
    for i in range(count):
        result = {
            "answer": f"テスト回答 {i+1}。ここには長文の回答が入ります。" + "." * random.randint(100, 500),
            "tokens": random.randint(100, 500),
            "model": "test-model",
            "processing_time": random.uniform(0.5, 2.0)
        }
        results.append(result)
    
    return results

async def prepare_cache_folders():
    """テスト用キャッシュディレクトリを準備"""
    # ベースディレクトリ
    base_dir = Path("./benchmark_cache")
    
    # 古いキャッシュを削除
    if base_dir.exists():
        shutil.rmtree(base_dir)
    
    # キャッシュディレクトリを作成
    cache_dirs = {
        "basic": base_dir / "basic",
        "simplified": base_dir / "simplified", 
        "high_performance": base_dir / "high_performance"
    }
    
    for d in cache_dirs.values():
        os.makedirs(d, exist_ok=True)
    
    return cache_dirs

async def initialize_cache_managers(cache_dirs):
    """各種キャッシュマネージャーを初期化"""
    logger.info("=== キャッシュマネージャー初期化 ===")
    
    # 基本キャッシュの初期化時間
    start_time = time.time()
    basic_cache = AICacheManager(
        cache_dir=str(cache_dirs["basic"]),
        ttl_seconds=3600,
        enable_cache=True
    )
    basic_init_time = time.time() - start_time
    logger.info(f"基本キャッシュ初期化時間: {basic_init_time:.6f}秒")
    
    # シンプル高性能キャッシュの初期化時間
    start_time = time.time()
    simplified_cache = SimplifiedHighPerformanceCache(
        cache_dir=str(cache_dirs["simplified"]),
        ttl_seconds=3600,
        enable_cache=True
    )
    simplified_init_time = time.time() - start_time
    logger.info(f"シンプル高性能キャッシュ初期化時間: {simplified_init_time:.6f}秒")
    
    # 高性能キャッシュの初期化時間
    start_time = time.time()
    high_performance_cache = HighPerformanceAICacheManager(
        cache_dir=str(cache_dirs["high_performance"]),
        ttl_seconds=3600,
        enable_cache=True,
        use_similarity=True
    )
    high_performance_init_time = time.time() - start_time
    logger.info(f"高性能キャッシュ初期化時間: {high_performance_init_time:.6f}秒")
    
    # 初期化の待機（非同期処理）
    if hasattr(high_performance_cache, '_initialization_task') and high_performance_cache._initialization_task:
        try:
            await asyncio.wait_for(high_performance_cache._initialization_task, timeout=5)
        except asyncio.TimeoutError:
            logger.warning("高性能キャッシュの初期化完了を待機中にタイムアウト")
    
    return {
        "basic": basic_cache,
        "basic_time": basic_init_time,
        "simplified": simplified_cache,
        "simplified_time": simplified_init_time,
        "high_performance": high_performance_cache,
        "high_performance_time": high_performance_init_time
    }

async def benchmark_cache_writes(cache_managers, test_count=20):
    """各キャッシュマネージャーの書き込み性能をベンチマーク"""
    logger.info("\n=== キャッシュ書き込み性能の比較 ===")
    
    # テストデータの生成
    queries = generate_test_queries(test_count)
    results = generate_test_results(test_count)
    
    # 基本キャッシュの書き込み時間
    basic_cache = cache_managers["basic"]
    basic_write_times = []
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        result = results[i]
        
        start_time = time.time()
        await basic_cache.set_cache(key_data, result)
        basic_write_times.append(time.time() - start_time)
    
    # シンプル高性能キャッシュの書き込み時間
    simplified_cache = cache_managers["simplified"]
    simplified_write_times = []
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        result = results[i]
        
        start_time = time.time()
        await simplified_cache.set_cache(key_data, result)
        simplified_write_times.append(time.time() - start_time)
    
    # 高性能キャッシュの書き込み時間
    high_performance_cache = cache_managers["high_performance"]
    high_performance_write_times = []
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        result = results[i]
        
        start_time = time.time()
        await high_performance_cache.set_cache(key_data, result)
        high_performance_write_times.append(time.time() - start_time)
    
    # 結果集計
    basic_avg = sum(basic_write_times) / len(basic_write_times)
    simplified_avg = sum(simplified_write_times) / len(simplified_write_times)
    high_perf_avg = sum(high_performance_write_times) / len(high_performance_write_times)
    
    logger.info(f"基本キャッシュ平均書き込み時間: {basic_avg:.6f}秒")
    logger.info(f"シンプル高性能キャッシュ平均書き込み時間: {simplified_avg:.6f}秒")
    logger.info(f"高性能キャッシュ平均書き込み時間: {high_perf_avg:.6f}秒")
    
    # 性能向上率
    if basic_avg > 0:
        logger.info(f"シンプル高性能キャッシュの書き込み速度向上: {basic_avg / simplified_avg:.2f}倍")
        logger.info(f"高性能キャッシュの書き込み速度向上: {basic_avg / high_perf_avg:.2f}倍")
    
    return {
        "basic_times": basic_write_times,
        "basic_avg": basic_avg,
        "simplified_times": simplified_write_times,
        "simplified_avg": simplified_avg,
        "high_performance_times": high_performance_write_times,
        "high_performance_avg": high_perf_avg
    }

async def benchmark_cache_reads(cache_managers, test_count=20):
    """各キャッシュマネージャーの読み込み性能をベンチマーク（初回）"""
    logger.info("\n=== キャッシュ読み込み性能の比較（初回） ===")
    
    # テストデータの生成
    queries = generate_test_queries(test_count)
    
    # 基本キャッシュの読み込み時間
    basic_cache = cache_managers["basic"]
    basic_read_times = []
    basic_hit_count = 0
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await basic_cache.get_cache(key_data)
        basic_read_times.append(time.time() - start_time)
        if hit:
            basic_hit_count += 1
    
    # シンプル高性能キャッシュの読み込み時間
    simplified_cache = cache_managers["simplified"]
    simplified_read_times = []
    simplified_hit_count = 0
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await simplified_cache.get_cache(key_data)
        simplified_read_times.append(time.time() - start_time)
        if hit:
            simplified_hit_count += 1
    
    # 高性能キャッシュの読み込み時間
    high_performance_cache = cache_managers["high_performance"]
    high_performance_read_times = []
    high_performance_hit_count = 0
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await high_performance_cache.get_cache(key_data)
        high_performance_read_times.append(time.time() - start_time)
        if hit:
            high_performance_hit_count += 1
    
    # 結果集計
    basic_avg = sum(basic_read_times) / len(basic_read_times) if basic_read_times else 0
    simplified_avg = sum(simplified_read_times) / len(simplified_read_times) if simplified_read_times else 0
    high_perf_avg = sum(high_performance_read_times) / len(high_performance_read_times) if high_performance_read_times else 0
    
    logger.info(f"基本キャッシュ平均読み込み時間: {basic_avg:.6f}秒 (ヒット率: {basic_hit_count/test_count:.1%})")
    logger.info(f"シンプル高性能キャッシュ平均読み込み時間: {simplified_avg:.6f}秒 (ヒット率: {simplified_hit_count/test_count:.1%})")
    logger.info(f"高性能キャッシュ平均読み込み時間: {high_perf_avg:.6f}秒 (ヒット率: {high_performance_hit_count/test_count:.1%})")
    
    # 性能向上率
    if basic_avg > 0:
        if simplified_avg > 0:
            logger.info(f"シンプル高性能キャッシュの読み込み速度向上: {basic_avg / simplified_avg:.2f}倍")
        if high_perf_avg > 0:
            logger.info(f"高性能キャッシュの読み込み速度向上: {basic_avg / high_perf_avg:.2f}倍")
    
    # 二回目の読み込み（メモリキャッシュ効果確認）
    logger.info("\n=== キャッシュ読み込み性能の比較（2回目/メモリキャッシュ効果） ===")
    
    # 基本キャッシュの2回目読み込み
    basic_read2_times = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await basic_cache.get_cache(key_data)
        basic_read2_times.append(time.time() - start_time)
    
    # シンプル高性能キャッシュの2回目読み込み
    simplified_read2_times = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await simplified_cache.get_cache(key_data)
        simplified_read2_times.append(time.time() - start_time)
    
    # 高性能キャッシュの2回目読み込み
    high_performance_read2_times = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await high_performance_cache.get_cache(key_data)
        high_performance_read2_times.append(time.time() - start_time)
    
    # 結果集計
    basic_avg2 = sum(basic_read2_times) / len(basic_read2_times) if basic_read2_times else 0
    simplified_avg2 = sum(simplified_read2_times) / len(simplified_read2_times) if simplified_read2_times else 0
    high_perf_avg2 = sum(high_performance_read2_times) / len(high_performance_read2_times) if high_performance_read2_times else 0
    
    logger.info(f"基本キャッシュ平均読み込み時間(2回目): {basic_avg2:.6f}秒")
    logger.info(f"シンプル高性能キャッシュ平均読み込み時間(2回目): {simplified_avg2:.6f}秒")
    logger.info(f"高性能キャッシュ平均読み込み時間(2回目): {high_perf_avg2:.6f}秒")
    
    # メモリキャッシュによる速度向上
    if basic_avg > 0 and basic_avg2 > 0:
        logger.info(f"基本キャッシュのメモリキャッシュ効果: {basic_avg / basic_avg2:.2f}倍")
    if simplified_avg > 0 and simplified_avg2 > 0:
        logger.info(f"シンプル高性能キャッシュのメモリキャッシュ効果: {simplified_avg / simplified_avg2:.2f}倍")
    if high_perf_avg > 0 and high_perf_avg2 > 0:
        logger.info(f"高性能キャッシュのメモリキャッシュ効果: {high_perf_avg / high_perf_avg2:.2f}倍")
    
    return {
        "first_read": {
            "basic_times": basic_read_times,
            "basic_avg": basic_avg,
            "basic_hits": basic_hit_count,
            "simplified_times": simplified_read_times,
            "simplified_avg": simplified_avg,
            "simplified_hits": simplified_hit_count,
            "high_performance_times": high_performance_read_times,
            "high_performance_avg": high_perf_avg,
            "high_performance_hits": high_performance_hit_count
        },
        "second_read": {
            "basic_times": basic_read2_times,
            "basic_avg": basic_avg2,
            "simplified_times": simplified_read2_times,
            "simplified_avg": simplified_avg2,
            "high_performance_times": high_performance_read2_times,
            "high_performance_avg": high_perf_avg2
        }
    }

async def benchmark_bulk_operations(cache_managers, test_count=50):
    """一括処理性能のベンチマーク"""
    logger.info("\n=== バルク操作パフォーマンスの比較 ===")
    
    # テストデータの生成 (より大量)
    queries = generate_test_queries(test_count)
    results = generate_test_results(test_count)
    
    # 各キャッシュマネージャー
    basic_cache = cache_managers["basic"]
    simplified_cache = cache_managers["simplified"]
    high_performance_cache = cache_managers["high_performance"]
    
    # 基本キャッシュの一括書き込み
    start_time = time.time()
    basic_tasks = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        task = basic_cache.set_cache(key_data, results[i])
        basic_tasks.append(task)
    
    await asyncio.gather(*basic_tasks)
    basic_bulk_write_time = time.time() - start_time
    
    # シンプル高性能キャッシュの一括書き込み
    start_time = time.time()
    simplified_tasks = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        task = simplified_cache.set_cache(key_data, results[i])
        simplified_tasks.append(task)
    
    await asyncio.gather(*simplified_tasks)
    simplified_bulk_write_time = time.time() - start_time
    
    # 高性能キャッシュの一括書き込み
    start_time = time.time()
    high_perf_tasks = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        task = high_performance_cache.set_cache(key_data, results[i])
        high_perf_tasks.append(task)
    
    await asyncio.gather(*high_perf_tasks)
    high_perf_bulk_write_time = time.time() - start_time
    
    # 結果表示
    logger.info(f"基本キャッシュ一括書き込み時間: {basic_bulk_write_time:.6f}秒 ({test_count}個, {basic_bulk_write_time/test_count:.6f}秒/項目)")
    logger.info(f"シンプル高性能キャッシュ一括書き込み時間: {simplified_bulk_write_time:.6f}秒 ({test_count}個, {simplified_bulk_write_time/test_count:.6f}秒/項目)")
    logger.info(f"高性能キャッシュ一括書き込み時間: {high_perf_bulk_write_time:.6f}秒 ({test_count}個, {high_perf_bulk_write_time/test_count:.6f}秒/項目)")
    
    # 一括読み込みテスト
    logger.info("\n--- 一括読み込みテスト ---")
    
    # 基本キャッシュの一括読み込み
    start_time = time.time()
    basic_read_tasks = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        task = basic_cache.get_cache(key_data)
        basic_read_tasks.append(task)
    
    await asyncio.gather(*basic_read_tasks)
    basic_bulk_read_time = time.time() - start_time
    
    # シンプル高性能キャッシュの一括読み込み
    start_time = time.time()
    simplified_read_tasks = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        task = simplified_cache.get_cache(key_data)
        simplified_read_tasks.append(task)
    
    await asyncio.gather(*simplified_read_tasks)
    simplified_bulk_read_time = time.time() - start_time
    
    # 高性能キャッシュの一括読み込み
    start_time = time.time()
    high_perf_read_tasks = []
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        task = high_performance_cache.get_cache(key_data)
        high_perf_read_tasks.append(task)
    
    await asyncio.gather(*high_perf_read_tasks)
    high_perf_bulk_read_time = time.time() - start_time
    
    # 結果表示
    logger.info(f"基本キャッシュ一括読み込み時間: {basic_bulk_read_time:.6f}秒 ({test_count}個, {basic_bulk_read_time/test_count:.6f}秒/項目)")
    logger.info(f"シンプル高性能キャッシュ一括読み込み時間: {simplified_bulk_read_time:.6f}秒 ({test_count}個, {simplified_bulk_read_time/test_count:.6f}秒/項目)")
    logger.info(f"高性能キャッシュ一括読み込み時間: {high_perf_bulk_read_time:.6f}秒 ({test_count}個, {high_perf_bulk_read_time/test_count:.6f}秒/項目)")
    
    return {
        "bulk_write": {
            "basic_time": basic_bulk_write_time,
            "simplified_time": simplified_bulk_write_time,
            "high_performance_time": high_perf_bulk_write_time,
        },
        "bulk_read": {
            "basic_time": basic_bulk_read_time,
            "simplified_time": simplified_bulk_read_time,
            "high_performance_time": high_perf_bulk_read_time,
        }
    }

async def collect_statistics(cache_managers):
    """各キャッシュマネージャーの統計情報を収集"""
    logger.info("\n=== キャッシュ統計情報 ===")
    
    # 基本キャッシュの統計
    basic_stats = await cache_managers["basic"].get_stats()
    logger.info("\n基本キャッシュ統計:")
    logger.info(f"総リクエスト数: {basic_stats.get('total_requests', 0)}")
    logger.info(f"ヒット数: {basic_stats.get('hits', 0)}")
    logger.info(f"ヒット率: {basic_stats.get('hit_ratio', 0):.2%}")
    
    # シンプル高性能キャッシュの統計
    simplified_stats = await cache_managers["simplified"].get_stats()
    logger.info("\nシンプル高性能キャッシュ統計:")
    logger.info(f"総リクエスト数: {simplified_stats.get('total_requests', 0)}")
    logger.info(f"ディスクヒット数: {simplified_stats.get('hits', 0)}")
    logger.info(f"メモリヒット数: {simplified_stats.get('memory_hits', 0)}")
    logger.info(f"総ヒット率: {simplified_stats.get('hit_ratio', 0):.2%}")
    logger.info(f"メモリキャッシュエントリ数: {simplified_stats.get('memory_cache_entries', 0)}")
    
    # 高性能キャッシュの統計
    high_performance_stats = await cache_managers["high_performance"].get_stats()
    logger.info("\n高性能キャッシュ統計:")
    logger.info(f"総リクエスト数: {high_performance_stats.get('total_requests', 0)}")
    logger.info(f"ディスクヒット数: {high_performance_stats.get('hits', 0)}")
    logger.info(f"メモリヒット数: {high_performance_stats.get('memory_hits', 0)}")
    
    if "similarity_hits" in high_performance_stats:
        logger.info(f"類似検索ヒット数: {high_performance_stats.get('similarity_hits', 0)}")
    
    logger.info(f"総ヒット率: {high_performance_stats.get('hit_ratio', 0):.2%}")
    logger.info(f"メモリキャッシュエントリ数: {high_performance_stats.get('memory_cache_entries', 0)}")
    
    return {
        "basic": basic_stats,
        "simplified": simplified_stats,
        "high_performance": high_performance_stats
    }

async def export_benchmark_results(results, test_name="benchmark_results"):
    """ベンチマークの結果をJSONファイルとしてエクスポート"""
    # 結果をJSONにエクスポート
    filename = f"{test_name}_{int(time.time())}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n結果を {filename} に保存しました")
    
    return filename

async def run_benchmark():
    """ベンチマークテストを実行"""
    logger.info("=== AIキャッシュシステム ベンチマークテスト開始 ===")
    
    # テスト結果格納用
    results = {}
    
    try:
        # キャッシュディレクトリの準備
        cache_dirs = await prepare_cache_folders()
        
        # キャッシュマネージャーの初期化
        cache_managers = await initialize_cache_managers(cache_dirs)
        results["initialization"] = {
            "basic_time": cache_managers["basic_time"],
            "simplified_time": cache_managers["simplified_time"],
            "high_performance_time": cache_managers["high_performance_time"]
        }
        
        # 書き込みパフォーマンスの測定
        write_results = await benchmark_cache_writes(cache_managers, test_count=20)
        results["write_performance"] = write_results
        
        # 読み込みパフォーマンスの測定
        read_results = await benchmark_cache_reads(cache_managers, test_count=20)
        results["read_performance"] = read_results
        
        # 一括処理パフォーマンスの測定
        bulk_results = await benchmark_bulk_operations(cache_managers, test_count=50)
        results["bulk_operations"] = bulk_results
        
        # 統計情報の収集
        stats = await collect_statistics(cache_managers)
        results["statistics"] = stats
        
        # 結果をエクスポート
        await export_benchmark_results(results)
        
        logger.info("\n=== ベンチマークテスト完了 ===")
        
    except Exception as e:
        logger.error(f"ベンチマークテスト中にエラーが発生しました: {e}", exc_info=True)
        results["error"] = str(e)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_benchmark())
