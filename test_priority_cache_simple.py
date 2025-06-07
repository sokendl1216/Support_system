#!/usr/bin/env python3
"""
優先度ベースのキャッシュ機構の簡易テスト
"""

import asyncio
import sys
import os
import json
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(__name__)

async def test_priority_cache():
    """優先度キャッシュのシンプルテスト"""
    try:
        # パスを追加して相対インポートができるようにする
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # キャッシュマネージャーをインポート
        from ai.cache_manager import get_cache_manager
        
        # キャッシュマネージャーを優先度設定で初期化
        cache_manager = await get_cache_manager(
            enable_cache=True,
            ttl_seconds=3600,  # 1時間
            max_cache_size_mb=100,
            use_priority=True  # 優先度キャッシュを有効化
        )
        
        logger.info("優先度対応キャッシュマネージャーを初期化しました")
        
        # テスト1: 基本的なキャッシュの設定と取得
        logger.info("-" * 50)
        logger.info("テスト1: 基本的なキャッシュ操作")
        
        test_key_1 = {"query": "テスト用クエリ1", "operation": "test"}
        test_value_1 = {"answer": "テスト回答1", "metadata": {"source": "test"}}
        
        # キャッシュに保存
        await cache_manager.set_cache(test_key_1, test_value_1)
        logger.info("キャッシュに保存: %s", json.dumps(test_key_1, ensure_ascii=False))
        
        # キャッシュから取得
        hit, value = await cache_manager.get_cache(test_key_1)
        logger.info("キャッシュから取得: ヒット=%s, 値=%s", hit, json.dumps(value, ensure_ascii=False))
        
        # テスト2: 優先度の高いクエリを複数回実行
        logger.info("-" * 50)
        logger.info("テスト2: 優先度の高いクエリを複数回実行")
        
        high_priority_key = {"query": "高優先度クエリ", "operation": "test"}
        high_priority_value = {"answer": "高優先度回答", "metadata": {"priority": "high"}}
        
        # 最初に保存
        await cache_manager.set_cache(high_priority_key, high_priority_value)
        
        # 複数回アクセスして優先度を上げる
        for i in range(5):
            hit, value = await cache_manager.get_cache(high_priority_key)
            logger.info("高優先度キャッシュアクセス %d: ヒット=%s", i+1, hit)
        
        # テスト3: 複数のキャッシュエントリを作成してクリーンアップをトリガー
        logger.info("-" * 50)
        logger.info("テスト3: キャッシュクリーンアップのテスト")
        
        # 複数の低優先度エントリを作成
        for i in range(20):
            test_key = {"query": f"低優先度クエリ{i}", "operation": "test"}
            test_value = {"answer": f"低優先度回答{i}", "metadata": {"priority": "low"}}
            await cache_manager.set_cache(test_key, test_value)
        
        # 統計情報の確認
        stats = await cache_manager.get_stats()
        logger.info("キャッシュ統計情報: %s", json.dumps(stats, ensure_ascii=False))
        
        # クリーンアップを強制的に実行
        logger.info("クリーンアップを強制実行...")
        await cache_manager._cleanup_cache(1024)  # 小さなサイズ制限を指定してクリーンアップを強制
        
        # クリーンアップ後に高優先度エントリが残っているか確認
        hit, value = await cache_manager.get_cache(high_priority_key)
        logger.info("クリーンアップ後の高優先度キャッシュ: ヒット=%s", hit)
        
        # 最終統計情報
        stats = await cache_manager.get_stats()
        logger.info("最終キャッシュ統計情報: %s", json.dumps(stats, ensure_ascii=False))
        
        return True
    
    except Exception as e:
        logger.error("テスト中にエラーが発生: %s", str(e))
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """メイン関数"""
    success = await test_priority_cache()
    if success:
        logger.info("優先度キャッシュテスト成功!")
    else:
        logger.error("優先度キャッシュテスト失敗!")

if __name__ == "__main__":
    asyncio.run(main())
