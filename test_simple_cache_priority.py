"""
優先度ベースのキャッシュ機構をシンプルにテストするスクリプト
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# キャッシュマネージャのインポート
from ai.cache_manager import get_cache_manager

async def test_simple_priority_cache():
    """優先度キャッシュ機能のシンプルテスト"""
    try:
        # キャッシュマネージャーを優先度機能有効で初期化
        cache_manager = await get_cache_manager(
            enable_cache=True,
            ttl_seconds=3600,  # 1時間
            max_cache_size_mb=10,  # 小さいサイズに設定
            use_priority=True  # 優先度キャッシュを有効化
        )
        
        logger.info("キャッシュマネージャーを優先度機能有効で初期化しました")
        
        # 初期状態の統計確認
        stats = await cache_manager.get_stats()
        logger.info(f"初期統計: {json.dumps(stats, ensure_ascii=False)}")
        
        # テスト1: 優先度の低いデータをキャッシュに格納
        logger.info("-" * 50)
        logger.info("テスト1: 優先度の低いデータをキャッシュに格納")
        
        low_priority_keys = []
        for i in range(5):
            key = {
                "operation": "test",
                "query": f"低優先度クエリ_{i}",
                "timestamp": datetime.now().isoformat()
            }
            low_priority_keys.append(key)
            
            result = {"answer": f"これは低優先度クエリ_{i}の回答です。" * 100}  # 大きめのデータ
            await cache_manager.set_cache(key, result)
            logger.info(f"低優先度データ_{i}をキャッシュに格納")
            
            # 少し待つ
            await asyncio.sleep(0.1)
        
        # テスト2: 優先度の高いデータをキャッシュに格納して複数回アクセス
        logger.info("-" * 50)
        logger.info("テスト2: 優先度の高いデータをキャッシュに格納して複数回アクセス")
        
        high_priority_key = {
            "operation": "test",
            "query": "高優先度クエリ",
            "timestamp": datetime.now().isoformat()
        }
        
        high_priority_result = {"answer": "これは高優先度クエリの回答です。" * 50}
        await cache_manager.set_cache(high_priority_key, high_priority_result)
        logger.info("高優先度データをキャッシュに格納")
        
        # 複数回アクセスして優先度を上げる
        for i in range(10):
            _, result = await cache_manager.get_cache(high_priority_key)
            logger.info(f"高優先度データにアクセス ({i+1}/10)")
            await asyncio.sleep(0.1)
        
        # キャッシュ統計の確認
        stats = await cache_manager.get_stats()
        logger.info(f"アクセス後の統計: {json.dumps(stats, ensure_ascii=False)}")
        
        # テスト3: さらに多くのデータを格納してキャッシュクリーンアップを発生させる
        logger.info("-" * 50)
        logger.info("テスト3: クリーンアップを発生させるためのデータ追加")
        
        # 多数のデータを追加して最大キャッシュサイズを超えさせる
        for i in range(20):
            key = {
                "operation": "test",
                "query": f"追加クエリ_{i}",
                "timestamp": datetime.now().isoformat()
            }
            
            # 大きめのデータを格納
            large_result = {"answer": f"これは追加クエリ_{i}の回答です。" * 200}
            await cache_manager.set_cache(key, large_result)
            logger.info(f"追加データ_{i}をキャッシュに格納")
            
            # 少し待つ
            await asyncio.sleep(0.1)
        
        # キャッシュクリーンアップが発生したか確認
        stats = await cache_manager.get_stats()
        logger.info(f"クリーンアップ後の統計: {json.dumps(stats, ensure_ascii=False)}")
        
        # テスト4: 優先度の高いデータがまだキャッシュに残っているか確認
        logger.info("-" * 50)
        logger.info("テスト4: 優先度の高いデータがまだキャッシュに残っているか確認")
        
        cache_hit, result = await cache_manager.get_cache(high_priority_key)
        logger.info(f"高優先度データがキャッシュに残っている: {cache_hit}")
        
        # テスト5: 優先度の低いデータがキャッシュから削除されているか確認
        logger.info("-" * 50)
        logger.info("テスト5: 優先度の低いデータがキャッシュから削除されているか確認")
        
        low_priority_hits = 0
        for i, key in enumerate(low_priority_keys):
            cache_hit, _ = await cache_manager.get_cache(key)
            if cache_hit:
                low_priority_hits += 1
            logger.info(f"低優先度データ_{i}がキャッシュに残っている: {cache_hit}")
        
        logger.info(f"低優先度データの残存率: {low_priority_hits}/{len(low_priority_keys)}")
        
        logger.info("-" * 50)
        logger.info("テスト完了")
        logger.info(f"優先度ベースのキャッシュ機能のテスト結果: {'成功' if cache_hit and low_priority_hits < len(low_priority_keys) else '失敗'}")
        
    except Exception as e:
        logger.error(f"テスト実行中のエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_priority_cache())
