#!/usr/bin/env python3
"""
RAGシステム統合テスト
Task 3-3完了の検証とTask 3-3a準備のためのテストスクリプト
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# RAGシステムのインポート
from ai.rag.rag_system import RAGSystem
from ai.rag.rag_ai_service import RAGAIService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_rag_system_initialization():
    """RAGシステムの初期化テスト"""
    logger.info("=== RAGシステム初期化テスト開始 ===")
    
    try:
        # デフォルト設定を読み込み
        import json
        from pathlib import Path
        
        config_path = Path(__file__).parent / "config" / "rag_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # 最小設定で初期化
            config = {
                "embedding": {"model_name": "nomic-embed-text"},
                "vector_store": {"dimension": 768},
                "knowledge_base": {"base_path": "ai/rag/knowledge_base"},
                "retrieval": {"top_k": 5},
                "mode_optimization": {
                    "interactive": {"top_k": 3, "similarity_threshold": 0.7},
                    "autonomous": {"top_k": 5, "similarity_threshold": 0.6}
                }
            }
        
        # RAGシステムの初期化
        rag_system = RAGSystem(config)
        await rag_system.initialize()
        
        # 健全性チェック
        health_status = await rag_system.health_check()
        logger.info(f"健全性チェック結果: {health_status}")
          # 統計情報取得
        stats = await rag_system.get_stats()
        logger.info(f"統計情報: {stats}")
        
        logger.info("✅ RAGシステム初期化テスト成功")
        return rag_system
        
    except Exception as e:
        logger.error(f"❌ RAGシステム初期化テスト失敗: {e}")
        raise

async def test_knowledge_base_ingestion(rag_system: RAGSystem):
    """知識ベースの文書取り込みテスト"""
    logger.info("=== 知識ベース取り込みテスト開始 ===")
    
    try:
        # 知識ベース再インデックス（強制更新）
        result = await rag_system.reindex_knowledge_base(force=True)
        logger.info(f"再インデックス結果: {result}")
        
        # 取り込み後の統計情報
        stats = await rag_system.get_stats()
        logger.info(f"取り込み後統計: {stats}")
        
        total_docs = stats.get('knowledge_base', {}).get('total_documents', 0)
        if total_docs > 0:
            logger.info("✅ 知識ベース取り込みテスト成功")
        else:
            logger.warning("⚠️ 文書が取り込まれていません")
            
    except Exception as e:        logger.error(f"❌ 知識ベース取り込みテスト失敗: {e}")
        raise

async def test_search_functionality(rag_system: RAGSystem):
    """検索機能テスト"""
    logger.info("=== 検索機能テスト開始 ===")
    
    test_queries = [
        "システムの概要について教えて",
        "プログラミングガイドの内容を知りたい",
        "RAGシステムの仕組みは？",
        "進行モードについて説明して"
    ]
    
    for query in test_queries:
        try:
            logger.info(f"検索クエリ: {query}")
            
            # 両方のモードでテスト
            for mode in ['interactive', 'autonomous']:
                results = await rag_system.search(query, mode=mode)
                logger.info(f"  {mode}モード結果数: {len(results)}")
                  if results:
                    top_result = results[0].to_dict()
                    logger.info(f"  トップ結果類似度: {top_result.get('similarity', 'N/A'):.3f}")
                    content_preview = top_result.get('content', '')[:100]
                    logger.info(f"  内容プレビュー: {content_preview}...")
                    
        except Exception as e:
            logger.error(f"❌ 検索テスト失敗 (クエリ: {query}): {e}")

async def test_rag_ai_service_integration():
    """RAG AIサービス統合テスト"""
    logger.info("=== RAG AIサービス統合テスト開始 ===")
    
    try:
        # RAG AIサービスの初期化
        rag_ai_service = RAGAIService()
        await rag_ai_service.initialize()
        
        # 統計情報取得テスト
        stats = await rag_ai_service.get_stats()
        logger.info(f"RAG AIサービス統計: {stats}")
        
        # 健康状態チェックテスト
        health = await rag_ai_service.health_check()
        logger.info(f"RAG AIサービス健康状態: {health}")
        
        # 知識ベース検索テスト
        test_query = "システムの主要機能について"
        search_results = await rag_ai_service.search_knowledge_base(test_query)
        logger.info(f"知識ベース検索結果数: {len(search_results)}")
        
        if search_results:
            logger.info(f"検索結果例: {search_results[0].get('content', '')[:100]}...")
        
        logger.info("✅ RAG AIサービス統合テスト成功")
            
    except Exception as e:
        logger.error(f"❌ RAG AIサービス統合テスト失敗: {e}")

async def test_mode_specific_optimization():
    """モード別最適化テスト（Task 3-3a準備）"""
    logger.info("=== モード別最適化テスト開始 ===")
    
    try:
        # デフォルト設定を読み込み
        import json
        from pathlib import Path
        
        config_path = Path(__file__).parent / "config" / "rag_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "embedding": {"model_name": "nomic-embed-text"},
                "vector_store": {"dimension": 768},
                "knowledge_base": {"base_path": "ai/rag/knowledge_base"},
                "retrieval": {"top_k": 5},
                "mode_optimization": {
                    "interactive": {"top_k": 3, "similarity_threshold": 0.7},
                    "autonomous": {"top_k": 5, "similarity_threshold": 0.6}
                }
            }
        
        rag_system = RAGSystem(config)
        await rag_system.initialize()
        
        test_query = "プログラミングのベストプラクティス"
        
        # 各モードでの検索パラメータ確認
        interactive_results = await rag_system.search(test_query, mode='interactive')
        autonomous_results = await rag_system.search(test_query, mode='autonomous')
        
        logger.info(f"対話型モード結果数: {len(interactive_results)}")
        logger.info(f"自律型モード結果数: {len(autonomous_results)}")
          # 結果の違いを分析
        if interactive_results and autonomous_results:
            interactive_scores = [r.similarity for r in interactive_results]
            autonomous_scores = [r.similarity for r in autonomous_results]
            
            logger.info(f"対話型平均スコア: {sum(interactive_scores)/len(interactive_scores):.3f}")
            logger.info(f"自律型平均スコア: {sum(autonomous_scores)/len(autonomous_scores):.3f}")
        
        logger.info("✅ モード別最適化テスト完了")
        
    except Exception as e:
        logger.error(f"❌ モード別最適化テスト失敗: {e}")

async def main():
    """メインテスト実行"""
    logger.info("🚀 RAGシステム統合テスト開始")
    
    try:
        # 1. システム初期化テスト
        rag_system = await test_rag_system_initialization()
        
        # 2. 知識ベース取り込みテスト
        await test_knowledge_base_ingestion(rag_system)
        
        # 3. 検索機能テスト
        await test_search_functionality(rag_system)
        
        # 4. AIサービス統合テスト
        await test_rag_ai_service_integration()
        
        # 5. モード別最適化テスト
        await test_mode_specific_optimization()
        
        logger.info("🎉 全てのテストが完了しました")
        
    except Exception as e:
        logger.error(f"💥 テスト実行中にエラーが発生: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
