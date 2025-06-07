"""
優先度ベースのキャッシュ機構をシンプルにテストするスクリプト
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

# キャッシュ関連のインポート
from ai.cache_manager import get_cache_manager, AICacheManager

async def test_priority_cache():
    """優先度キャッシュのテスト"""
    try:
        # キャッシュマネージャーを初期化（優先度キャッシュを有効化）
        logger.info("優先度対応キャッシュマネージャーを初期化中...")
        
        cache_manager = await get_cache_manager(
            enable_cache=True, 
            ttl_seconds=3600,  # 1時間
            max_cache_size_mb=100,
            use_priority=True  # 優先度キャッシュを有効化
        )
        
        logger.info("キャッシュマネージャーを初期化しました")
        
        # テストデータ
        test_key1 = {"query": "AIエージェントの最適化方法について教えてください", "model": "test-model"}
        test_data1 = {"response": "AIエージェントの最適化には様々な方法があります。", "tokens": 150}
        
        test_key2 = {"query": "プロンプトエンジニアリングのベストプラクティス", "model": "test-model"}
        test_data2 = {"response": "プロンプトエンジニアリングのベストプラクティスには以下が含まれます。", "tokens": 200}
        
        # テスト1: 優先度の低いキャッシュ項目を作成
        logger.info("-" * 50)
        logger.info("テスト1: 優先度の低いキャッシュ項目を作成")
        
        await cache_manager.set_cache(test_key1, test_data1)
        logger.info("キャッシュ項目1を設定しました")
        
        # テスト2: 優先度の高いキャッシュ項目を作成して複数回アクセス
        logger.info("-" * 50)
        logger.info("テスト2: 優先度の高いキャッシュ項目を作成して複数回アクセス")
        
        await cache_manager.set_cache(test_key2, test_data2)
        logger.info("キャッシュ項目2を設定しました")
        
        # 複数回アクセスして優先度を上げる
        for i in range(5):
            logger.info(f"アクセス {i+1}/5: キャッシュ項目2")
            _, _ = await cache_manager.get_cache(test_key2)
        
        # 統計情報を表示
        logger.info("-" * 50)
        logger.info("キャッシュ統計:")
        stats = cache_manager.get_stats()
        formatted_stats = json.dumps(stats, indent=2, ensure_ascii=False)
        logger.info(f"\n{formatted_stats}")
        
        # 優先度データを表示
        logger.info("-" * 50)
        logger.info("優先度データ:")
        
        # 優先度データのハッシュキーを取得
        key1_hash = cache_manager._get_cache_key(test_key1)
        key2_hash = cache_manager._get_cache_key(test_key2)
        
        logger.info(f"キャッシュ項目1 キー: {key1_hash}")
        logger.info(f"キャッシュ項目1 アクセス回数: {cache_manager.priority_data['access_counts'].get(key1_hash, 0)}")
        logger.info(f"キャッシュ項目1 優先度: {cache_manager.priority_data['priorities'].get(key1_hash, 0)}")
        
        logger.info(f"キャッシュ項目2 キー: {key2_hash}")
        logger.info(f"キャッシュ項目2 アクセス回数: {cache_manager.priority_data['access_counts'].get(key2_hash, 0)}")
        logger.info(f"キャッシュ項目2 優先度: {cache_manager.priority_data['priorities'].get(key2_hash, 0)}")
        
        # クリーンアップをシミュレート
        logger.info("-" * 50)
        logger.info("キャッシュクリーンアップをシミュレート")
        
        # キャッシュサイズを強制的に制限する
        await cache_manager._cleanup_cache(1000)  # 小さいサイズを指定して強制的にクリーンアップ
        
        # クリーンアップ後に両方のキャッシュを確認
        key1_hit, _ = await cache_manager.get_cache(test_key1)
        key2_hit, _ = await cache_manager.get_cache(test_key2)
        
        logger.info(f"クリーンアップ後 キャッシュ項目1 存在: {key1_hit}")
        logger.info(f"クリーンアップ後 キャッシュ項目2 存在: {key2_hit}")
        
        if key2_hit and not key1_hit:
            logger.info("優先度ベースのキャッシュが正常に動作しています: 優先度の高い項目が保持されました")
        else:
            logger.warning("優先度ベースのキャッシュが期待通りに動作していません")
            
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        import traceback
        logger.error(traceback.format_exc())

# テストの実行
if __name__ == "__main__":
    asyncio.run(test_priority_cache())
