#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGシステムのモード別最適化テスト
Task 3-3a: 進行モード別知識ベース最適化の検証
"""

import asyncio
import sys
import os
import logging
import json

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ai.rag.rag_system import RAGSystem
from ai.rag.rag_ai_service import RAGAIService

def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"設定ファイルの読み込みに失敗: {e}")
        return {}

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mode_optimization():
    """モード別最適化のテスト"""
    try:
        logger.info("=== RAGシステム モード別最適化テスト開始 ===")        # RAGシステム初期化
        logger.info("RAGシステムを初期化中...")
        config_path = os.path.join(project_root, "config", "rag_config.json")
        config = load_config(config_path)
        if not config:
            logger.error("設定ファイルの読み込みに失敗")
            return False
        
        rag_system = RAGSystem(config)
        
        # 初期化の確認
        if not await rag_system.initialize():
            logger.error("RAGシステムの初期化に失敗")
            return False
        
        logger.info("RAGシステムの初期化完了")
        
        # システム統計を表示
        stats = await rag_system.get_stats()
        logger.info(f"システム統計: {stats}")
        
        # テストクエリ
        test_query = "プログラミングのベストプラクティス"
        
        # 各モードでの検索テスト
        modes = ["interactive", "autonomous", "hybrid"]
        
        for mode in modes:
            logger.info(f"\n--- {mode.upper()}モードでの検索テスト ---")
            
            try:
                # 検索実行
                search_results = await rag_system.search(test_query, mode=mode)
                
                logger.info(f"{mode}モード検索結果: {len(search_results)}件")
                
                # 結果を表示
                for i, result in enumerate(search_results[:3]):  # 上位3件
                    logger.info(f"  結果 {i+1}:")
                    logger.info(f"    類似度: {result.similarity:.4f}")
                    logger.info(f"    ソース: {result.chunk.source_file}")
                    logger.info(f"    内容: {result.chunk.content[:100]}...")
                    logger.info(f"    ランク: {result.rank}")
                
                # コンテキスト生成テスト
                context_data = await rag_system.generate_context(test_query, mode=mode)
                logger.info(f"  コンテキスト長: {context_data['context_length']} 文字")
                logger.info(f"  ソース数: {len(context_data['sources'])}")
                
            except Exception as e:
                logger.error(f"{mode}モードでエラー: {e}")
        
        # RAGAIService統合テスト
        logger.info("\n--- RAGAIService統合テスト ---")
        try:
            rag_ai_service = RAGAIService()
            await rag_ai_service.initialize()
            
            # 各モードでRAG検索付きLLM応答テスト
            for mode in modes:
                logger.info(f"\n{mode}モードでのRAG検索付きLLM応答テスト:")
                
                context_data = await rag_ai_service.search_and_generate_context(
                    test_query, mode=mode
                )
                
                logger.info(f"  検索結果: {context_data['total_results']}件")
                logger.info(f"  コンテキスト長: {context_data['context_length']} 文字")
                
        except Exception as e:
            logger.error(f"RAGAIService統合テストでエラー: {e}")
        
        # ヘルスチェック
        logger.info("\n--- システムヘルスチェック ---")
        health = await rag_system.health_check()
        logger.info(f"システム状態: {health['overall']}")
        
        if health.get("issues"):
            logger.warning(f"検出された問題: {health['issues']}")
        
        logger.info("=== モード別最適化テスト完了 ===")
        return True
        
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生: {e}")
        return False

def main():
    """メイン関数"""
    try:
        success = asyncio.run(test_mode_optimization())
        if success:
            print("\n✅ モード別最適化テストが正常に完了しました")
            sys.exit(0)
        else:
            print("\n❌ モード別最適化テストが失敗しました")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
