"""
高性能キャッシュシステムのベンチマークテスト

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
# from ai.enhanced_cache_manager import EnhancedAICacheManager
# 構文エラーのあるファイルを回避
from ai.optimized_cache_manager import OptimizedAICacheManager
from ai.high_performance_cache_manager import HighPerformanceAICacheManager

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

# キャッシュディレクトリを準備
def prepare_cache_dirs():
    """テスト用のキャッシュディレクトリを準備"""
    cache_base = Path("./benchmark_cache")
    
    # 既存のキャッシュを削除
    if cache_base.exists():
        shutil.rmtree(cache_base)
    
    # 各キャッシュタイプのディレクトリを作成
    dirs = {
        "basic": cache_base / "basic",
        "enhanced": cache_base / "enhanced",
        "optimized": cache_base / "optimized",
        "high_performance": cache_base / "high_performance"
    }
    
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    
    return dirs

async def benchmark_cache_initialization(cache_dirs):
    """各キャッシュマネージャーの初期化時間をベンチマーク"""
    logger.info("=== キャッシュマネージャー初期化時間の比較 ===")
    
    # 基本キャッシュの初期化時間
    start_time = time.time()
    basic_cache = AICacheManager(
        cache_dir=str(cache_dirs["basic"]),
        ttl_seconds=3600,
        enable_cache=True
    )
    basic_init_time = time.time() - start_time
    logger.info(f"基本キャッシュ初期化時間: {basic_init_time:.6f}秒")
      # 拡張キャッシュはエラーがあるため無効化
    enhanced_cache = None
    enhanced_init_time = float('inf')
    logger.info("拡張キャッシュ: 構文エラーのため無効化")
      # 既存の最適化キャッシュのテスト
    start_time = time.time()
    try:
        # OptimizedAICacheManagerも依存関係の問題があるため省略
        optimized_cache = None
        optimized_init_time = float('inf')
        logger.info("最適化キャッシュ: 依存関係の問題で無効化")
    except Exception as e:
        logger.warning(f"最適化キャッシュ初期化エラー: {e}")
        optimized_cache = None
        optimized_init_time = float('inf')
    
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
    if enhanced_cache:
        await asyncio.sleep(1)  # 初期化完了を待機
        
    if optimized_cache:
        if hasattr(optimized_cache, '_initialization_task') and optimized_cache._initialization_task:
            try:
                await asyncio.wait_for(optimized_cache._initialization_task, timeout=5)
            except asyncio.TimeoutError:
                logger.warning("最適化キャッシュの初期化完了を待機中にタイムアウト")
    
    if hasattr(high_performance_cache, '_initialization_task') and high_performance_cache._initialization_task:
        try:
            await asyncio.wait_for(high_performance_cache._initialization_task, timeout=5)
        except asyncio.TimeoutError:
            logger.warning("高性能キャッシュの初期化完了を待機中にタイムアウト")
    
    return {
        "basic": basic_cache,
        "basic_time": basic_init_time,
        "enhanced": enhanced_cache,
        "enhanced_time": enhanced_init_time,
        "optimized": optimized_cache,
        "optimized_time": optimized_init_time,
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
    
    # 拡張キャッシュの書き込み時間
    enhanced_write_times = []
    if cache_managers["enhanced"]:
        enhanced_cache = cache_managers["enhanced"]
        
        for i in range(test_count):
            key_data = {"query": queries[i], "model": "test-model"}
            result = results[i]
            
            start_time = time.time()
            await enhanced_cache.set_cache(key_data, result)
            enhanced_write_times.append(time.time() - start_time)
    
    # 最適化キャッシュの書き込み時間
    optimized_write_times = []
    if cache_managers["optimized"]:
        optimized_cache = cache_managers["optimized"]
        
        for i in range(test_count):
            key_data = {"query": queries[i], "model": "test-model"}
            result = results[i]
            
            start_time = time.time()
            await optimized_cache.set_cache(key_data, result)
            optimized_write_times.append(time.time() - start_time)
    
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
    logger.info(f"基本キャッシュ平均書き込み時間: {basic_avg:.6f}秒")
    
    if enhanced_write_times:
        enhanced_avg = sum(enhanced_write_times) / len(enhanced_write_times)
        logger.info(f"拡張キャッシュ平均書き込み時間: {enhanced_avg:.6f}秒")
    else:
        enhanced_avg = float('inf')
        logger.info("拡張キャッシュ: 利用不可")
    
    if optimized_write_times:
        optimized_avg = sum(optimized_write_times) / len(optimized_write_times)
        logger.info(f"最適化キャッシュ平均書き込み時間: {optimized_avg:.6f}秒")
    else:
        optimized_avg = float('inf')
        logger.info("最適化キャッシュ: 利用不可")
    
    high_performance_avg = sum(high_performance_write_times) / len(high_performance_write_times)
    logger.info(f"高性能キャッシュ平均書き込み時間: {high_performance_avg:.6f}秒")
    
    logger.info(f"基本キャッシュに対する高性能キャッシュの書き込み速度向上: {basic_avg/high_performance_avg:.2f}倍")
    
    return {
        "queries": queries,
        "basic_write_avg": basic_avg,
        "enhanced_write_avg": enhanced_avg,
        "optimized_write_avg": optimized_avg,
        "high_performance_write_avg": high_performance_avg
    }

async def benchmark_cache_reads(cache_managers, test_data, test_count=20):
    """各キャッシュマネージャーの読み込み性能をベンチマーク"""
    logger.info("\n=== キャッシュ読み込み性能の比較 ===")
    
    # クエリの取得
    queries = test_data["queries"]
    
    # 完全一致読み込みのテスト
    logger.info("完全一致読み込みテスト:")
    
    # 基本キャッシュの読み込み時間
    basic_cache = cache_managers["basic"]
    basic_exact_times = []
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await basic_cache.get_cache(key_data)
        basic_exact_times.append(time.time() - start_time)
    
    # 拡張キャッシュの読み込み時間
    enhanced_exact_times = []
    if cache_managers["enhanced"]:
        enhanced_cache = cache_managers["enhanced"]
        
        for i in range(test_count):
            key_data = {"query": queries[i], "model": "test-model"}
            
            start_time = time.time()
            hit, _ = await enhanced_cache.get_cache(key_data)
            enhanced_exact_times.append(time.time() - start_time)
    
    # 最適化キャッシュの読み込み時間
    optimized_exact_times = []
    if cache_managers["optimized"]:
        optimized_cache = cache_managers["optimized"]
        
        for i in range(test_count):
            key_data = {"query": queries[i], "model": "test-model"}
            
            start_time = time.time()
            hit, _ = await optimized_cache.get_cache(key_data)
            optimized_exact_times.append(time.time() - start_time)
    
    # 高性能キャッシュの読み込み時間
    high_performance_cache = cache_managers["high_performance"]
    high_performance_exact_times = []
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await high_performance_cache.get_cache(key_data)
        high_performance_exact_times.append(time.time() - start_time)
    
    # 結果集計
    basic_exact_avg = sum(basic_exact_times) / len(basic_exact_times)
    logger.info(f"基本キャッシュ平均読み込み時間: {basic_exact_avg:.6f}秒")
    
    if enhanced_exact_times:
        enhanced_exact_avg = sum(enhanced_exact_times) / len(enhanced_exact_times)
        logger.info(f"拡張キャッシュ平均読み込み時間: {enhanced_exact_avg:.6f}秒")
    else:
        enhanced_exact_avg = float('inf')
        logger.info("拡張キャッシュ: 利用不可")
    
    if optimized_exact_times:
        optimized_exact_avg = sum(optimized_exact_times) / len(optimized_exact_times)
        logger.info(f"最適化キャッシュ平均読み込み時間: {optimized_exact_avg:.6f}秒")
    else:
        optimized_exact_avg = float('inf')
        logger.info("最適化キャッシュ: 利用不可")
    
    high_performance_exact_avg = sum(high_performance_exact_times) / len(high_performance_exact_times)
    logger.info(f"高性能キャッシュ平均読み込み時間: {high_performance_exact_avg:.6f}秒")
    
    # ゼロ除算を防止
    if high_performance_exact_avg > 0:
        speed_improvement = basic_exact_avg / high_performance_exact_avg
        logger.info(f"基本キャッシュに対する高性能キャッシュの読み込み速度向上: {speed_improvement:.2f}倍")
    else:
        logger.info("基本キャッシュに対する高性能キャッシュの読み込み速度向上: 計測不能（読み込み時間がゼロ）")
    
    # 2回目の読み込み（メモリキャッシュ効果の測定）
    logger.info("\nメモリキャッシュ効果測定（2回目の読み込み）:")
    
    # 高性能キャッシュの2回目の読み込み時間
    high_performance_second_times = []
    
    for i in range(test_count):
        key_data = {"query": queries[i], "model": "test-model"}
        
        start_time = time.time()
        hit, _ = await high_performance_cache.get_cache(key_data)
        high_performance_second_times.append(time.time() - start_time)
    
    high_performance_second_avg = sum(high_performance_second_times) / len(high_performance_second_times)
    logger.info(f"高性能キャッシュ2回目平均読み込み時間: {high_performance_second_avg:.6f}秒")
    
    # ゼロ除算を防止
    if high_performance_second_avg > 0:
        memory_speedup = high_performance_exact_avg / high_performance_second_avg
        logger.info(f"メモリキャッシュによる速度向上: {memory_speedup:.2f}倍")
    else:
        logger.info("メモリキャッシュによる速度向上: 計測不能（読み込み時間がゼロ）")
    
    return {
        "basic_exact_avg": basic_exact_avg,
        "enhanced_exact_avg": enhanced_exact_avg,
        "optimized_exact_avg": optimized_exact_avg,
        "high_performance_exact_avg": high_performance_exact_avg,
        "high_performance_second_avg": high_performance_second_avg
    }

async def benchmark_similarity_search(cache_managers, test_count=10):
    """各キャッシュマネージャーの類似検索性能をベンチマーク"""
    logger.info("\n=== 類似検索性能の比較 ===")
    
    # 類似クエリの生成
    original_queries = [
        "AIによるレポート自動生成機能について教えてください。",
        "機械学習モデルの学習方法を教えてください。",
        "深層学習の最新トレンドは何ですか？",
        "Python言語でデータ分析を行う方法は？",
        "自然言語処理技術の応用例を教えてください。"
    ]
    
    similar_queries = [
        "AIを使ったレポート作成機能はありますか？",
        "機械学習モデルをトレーニングする手順を教えて。",
        "ディープラーニングの最新の研究動向を知りたいです。",
        "Pythonを使ってデータ分析するにはどうすればいい？",
        "NLPテクノロジーの実際の使用例を教えてください。"
    ]
    
    # テスト用データの準備
    for i in range(len(original_queries)):
        key_data = {"query": original_queries[i], "model": "test-model"}
        result = {"answer": f"オリジナルクエリ{i+1}に対する回答", "tokens": 200 + i * 10}
        
        # 各キャッシュに保存
        if cache_managers["enhanced"]:
            await cache_managers["enhanced"].set_cache(key_data, result)
        
        if cache_managers["optimized"]:
            await cache_managers["optimized"].set_cache(key_data, result)
        
        await cache_managers["high_performance"].set_cache(key_data, result)
    
    # 類似検索のベンチマーク
    logger.info("類似クエリ検索テスト:")
    
    # 拡張キャッシュの類似検索時間
    enhanced_similarity_times = []
    enhanced_hits = 0
    
    if cache_managers["enhanced"]:
        enhanced_cache = cache_managers["enhanced"]
        
        for query in similar_queries:
            key_data = {"query": query, "model": "test-model"}
            
            start_time = time.time()
            hit, result = await enhanced_cache.get_cache(key_data)
            enhanced_similarity_times.append(time.time() - start_time)
            
            if hit:
                enhanced_hits += 1
    
    # 最適化キャッシュの類似検索時間
    optimized_similarity_times = []
    optimized_hits = 0
    
    if cache_managers["optimized"]:
        optimized_cache = cache_managers["optimized"]
        
        for query in similar_queries:
            key_data = {"query": query, "model": "test-model"}
            
            start_time = time.time()
            hit, result = await optimized_cache.get_cache(key_data)
            optimized_similarity_times.append(time.time() - start_time)
            
            if hit:
                optimized_hits += 1
    
    # 高性能キャッシュの類似検索時間
    high_performance_cache = cache_managers["high_performance"]
    high_performance_similarity_times = []
    high_performance_hits = 0
    
    for query in similar_queries:
        key_data = {"query": query, "model": "test-model"}
        
        start_time = time.time()
        hit, result = await high_performance_cache.get_cache(key_data)
        high_performance_similarity_times.append(time.time() - start_time)
        
        if hit:
            high_performance_hits += 1
    
    # 結果集計
    if enhanced_similarity_times:
        enhanced_similarity_avg = sum(enhanced_similarity_times) / len(enhanced_similarity_times)
        logger.info(f"拡張キャッシュ平均類似検索時間: {enhanced_similarity_avg:.6f}秒 (ヒット率: {enhanced_hits/len(similar_queries):.2%})")
    else:
        enhanced_similarity_avg = float('inf')
        logger.info("拡張キャッシュ: 利用不可")
    
    if optimized_similarity_times:
        optimized_similarity_avg = sum(optimized_similarity_times) / len(optimized_similarity_times)
        logger.info(f"最適化キャッシュ平均類似検索時間: {optimized_similarity_avg:.6f}秒 (ヒット率: {optimized_hits/len(similar_queries):.2%})")
    else:
        optimized_similarity_avg = float('inf')
        logger.info("最適化キャッシュ: 利用不可")
    
    high_performance_similarity_avg = sum(high_performance_similarity_times) / len(high_performance_similarity_times)
    logger.info(f"高性能キャッシュ平均類似検索時間: {high_performance_similarity_avg:.6f}秒 (ヒット率: {high_performance_hits/len(similar_queries):.2%})")
    
    if enhanced_similarity_avg != float('inf'):
        logger.info(f"拡張キャッシュに対する高性能キャッシュの類似検索速度向上: {enhanced_similarity_avg/high_performance_similarity_avg:.2f}倍")
    
    return {
        "enhanced_similarity_avg": enhanced_similarity_avg,
        "enhanced_hits": enhanced_hits,
        "optimized_similarity_avg": optimized_similarity_avg,
        "optimized_hits": optimized_hits,
        "high_performance_similarity_avg": high_performance_similarity_avg,
        "high_performance_hits": high_performance_hits
    }

async def benchmark_stress_test(cache_managers, batch_size=100):
    """ストレステスト: 大量のクエリ処理を高速に行う"""
    logger.info(f"\n=== ストレステスト (バッチサイズ: {batch_size}) ===")
    
    # 大量のクエリの生成
    queries = generate_test_queries(batch_size)
    results = generate_test_results(batch_size)
    
    # 高性能キャッシュでの一括書き込み
    high_performance_cache = cache_managers["high_performance"]
    
    start_time = time.time()
    
    # 非同期タスクのリスト
    write_tasks = []
    
    for i in range(batch_size):
        key_data = {"query": queries[i], "model": "test-model"}
        result = results[i]
        
        # 書き込みタスクを作成
        task = high_performance_cache.set_cache(key_data, result)
        write_tasks.append(task)
    
    # 全ての書き込みタスクを並列実行
    await asyncio.gather(*write_tasks)
    
    write_time = time.time() - start_time
    logger.info(f"高性能キャッシュ一括書き込み時間: {write_time:.3f}秒 (平均: {write_time/batch_size:.6f}秒/クエリ)")
      # 類似クエリの生成
    similar_queries = []
    for query in queries[:10]:  # 最初の10個のクエリに対する類似クエリ
        words = query.split()
        if len(words) > 2:  # 条件を緩和（3単語以上 → 2単語以上）
            # 単語の一部を置き換えて類似クエリを作成
            modified_words = words.copy()
            replacement_count = max(1, min(2, len(words) // 3))  # 最低1個は置換
            for _ in range(replacement_count):
                idx = random.randint(0, len(words) - 1)
                modified_words[idx] = random.choice(["方法", "テクニック", "手法", "アプローチ", "技術"])
            similar_queries.append(" ".join(modified_words))
        else:
            # 短い場合は基本的な修正を行う
            similar_queries.append(query + "について")
    
    # 類似検索の一括処理
    start_time = time.time()
    
    # 非同期タスクのリスト
    search_tasks = []
    
    for query in similar_queries:
        key_data = {"query": query, "model": "test-model"}
        
        # 検索タスクを作成
        task = high_performance_cache.get_cache(key_data)
        search_tasks.append(task)
      # 全ての検索タスクを並列実行
    search_results = await asyncio.gather(*search_tasks)
    
    search_time = time.time() - start_time
    hits = sum(1 for hit, _ in search_results if hit)
    
    # ゼロ除算を防止
    if len(similar_queries) > 0:
        avg_search_time = search_time / len(similar_queries)
        hit_ratio = hits / len(similar_queries)
        logger.info(f"高性能キャッシュ一括類似検索時間: {search_time:.3f}秒 (平均: {avg_search_time:.6f}秒/クエリ)")
        logger.info(f"類似検索ヒット率: {hit_ratio:.2%}")
    else:
        avg_search_time = 0
        hit_ratio = 0
        logger.info("類似クエリが生成されませんでした")
      # 統計情報の取得
    stats = await high_performance_cache.get_stats()
    logger.info("\n高性能キャッシュの統計情報:")
    logger.info(f"総リクエスト数: {stats.get('total_requests', 0)}")
    logger.info(f"完全一致ヒット数: {stats.get('hits', 0)}")
    logger.info(f"メモリキャッシュヒット数: {stats.get('memory_hits', 0)}")
    logger.info(f"類似検索ヒット数: {stats.get('similarity_hits', 0)}")
    logger.info(f"総ヒット率: {stats.get('hit_ratio', 0):.2%}")
    
    return {
        "batch_size": batch_size,
        "write_time": write_time,
        "write_avg": write_time / batch_size,
        "search_time": search_time,
        "search_avg": avg_search_time,
        "hits": hits,
        "hit_ratio": hit_ratio,
        "stats": stats
    }

async def main():
    """メイン実行関数"""
    try:
        logger.info("高性能AIキャッシュシステム ベンチマークテスト開始")
        
        # キャッシュディレクトリを準備
        cache_dirs = prepare_cache_dirs()
        
        # 各キャッシュマネージャーの初期化
        cache_managers = await benchmark_cache_initialization(cache_dirs)
        
        # 書き込み性能の比較
        write_results = await benchmark_cache_writes(cache_managers)
        
        # 読み込み性能の比較
        read_results = await benchmark_cache_reads(cache_managers, write_results)
        
        # 類似検索性能の比較
        similarity_results = await benchmark_similarity_search(cache_managers)
        
        # ストレステスト
        stress_results = await benchmark_stress_test(cache_managers)
        
        # 総合結果レポート
        logger.info("\n=== AIキャッシュシステム最適化 総合評価 ===")
        
        # 基本キャッシュとの比較
        basic_write = write_results["basic_write_avg"]
        hp_write = write_results["high_performance_write_avg"]
        write_speedup = basic_write / hp_write if hp_write > 0 else 0
        
        basic_read = read_results["basic_exact_avg"]
        hp_read = read_results["high_performance_exact_avg"]
        read_speedup = basic_read / hp_read if hp_read > 0 else 0
        
        hp_memory_read = read_results["high_performance_second_avg"]
        memory_speedup = hp_read / hp_memory_read if hp_memory_read > 0 else 0
        
        logger.info("基本のキャッシュシステムと比較した性能向上:")
        logger.info(f"1. 書き込み速度: {write_speedup:.2f}倍高速")
        logger.info(f"2. 読み込み速度: {read_speedup:.2f}倍高速")
        logger.info(f"3. メモリキャッシュ効果: {memory_speedup:.2f}倍高速")
        
        # 類似検索の性能比較
        enhanced_sim = similarity_results["enhanced_similarity_avg"]
        hp_sim = similarity_results["high_performance_similarity_avg"]
        
        if enhanced_sim != float('inf'):
            sim_speedup = enhanced_sim / hp_sim if hp_sim > 0 else 0
            logger.info(f"4. 類似検索速度: {sim_speedup:.2f}倍高速")
        
        # ストレステスト結果
        logger.info(f"\n大規模処理性能 ({stress_results['batch_size']}クエリの一括処理):")
        logger.info(f"- 一括書き込み: {stress_results['write_time']:.3f}秒 ({stress_results['write_avg']*1000:.2f}ms/クエリ)")
        logger.info(f"- 一括検索: {stress_results['search_time']:.3f}秒 ({stress_results['search_avg']*1000:.2f}ms/クエリ)")
        logger.info(f"- 類似検索ヒット率: {stress_results['hit_ratio']:.2%}")
        
        logger.info("\nベンチマークテスト完了")
        
    except Exception as e:
        logger.error(f"ベンチマーク中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
