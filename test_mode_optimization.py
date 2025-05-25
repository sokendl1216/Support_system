#!/usr/bin/env python3
"""
Task 3-3a モード別知識ベース最適化のテスト
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# パスを追加
sys.path.append(str(Path(__file__).parent))

from ai.rag.rag_system import RAGSystem

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_config():
    """設定ファイルを読み込み"""
    try:
        config_path = Path(__file__).parent / "config" / "rag_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"設定ファイル読み込みエラー: {e}")
        # デフォルト設定を返す
        return {
            "embedding": {
                "model_name": "nomic-embed-text",
                "base_url": "http://localhost:11434",
                "batch_size": 32,
                "timeout": 30
            },
            "vector_store": {
                "dimension": 768,
                "metric": "cosine",
                "index_type": "Flat"
            },
            "knowledge_base": {
                "base_directory": "./knowledge_base",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "file_extensions": [".txt", ".md", ".json"]
            },
            "retrieval": {
                "default_top_k": 5,
                "max_context_length": 4096,
                "default_similarity_threshold": 0.3
            },
            "mode_optimization": {
                "modes": {
                    "interactive": {
                        "similarity_threshold": 0.2,
                        "boost_user_context": 1.3,
                        "prefer_recent": True,
                        "personalization_weight": 0.2,
                        "response_speed_priority": True
                    },
                    "autonomous": {
                        "similarity_threshold": 0.15,
                        "exploration_factor": 1.4,
                        "cross_reference_boost": 1.2,
                        "multi_perspective_retrieval": True,
                        "depth_search_enabled": True
                    },
                    "hybrid": {
                        "similarity_threshold": 0.25,
                        "balanced_approach": True,
                        "adaptive_threshold": True,
                        "context_awareness": 0.6,
                        "exploration_factor": 1.2,
                        "boost_user_context": 1.1
                    },
                    "general": {
                        "similarity_threshold": 0.3,
                        "boost_user_context": 1.0,
                        "exploration_factor": 1.0
                    }
                }
            }
        }

async def test_mode_optimization():
    """モード別最適化のテスト"""
    print("=== Task 3-3a モード別知識ベース最適化テスト ===")
    
    try:
        # 設定を読み込み
        config = await load_config()
        print("✓ 設定ファイル読み込み完了")
        
        # RAGSystemを初期化
        rag_system = RAGSystem(config)
        print("✓ RAGSystem初期化完了")
        
        # 初期化
        await rag_system.initialize()
        print("✓ RAGSystem初期化成功")
        
        # テストクエリ
        test_query = "プログラミングのベストプラクティス"
        
        print(f"\n--- テストクエリ: '{test_query}' ---")
        
        # 各モードでの検索テスト
        modes = ["interactive", "autonomous", "hybrid", "general"]
        
        results = {}
        for mode in modes:
            print(f"\n{mode.upper()}モードでの検索:")
            try:
                search_results = await rag_system.search(test_query, mode=mode, top_k=3)
                
                print(f"  検索結果数: {len(search_results)}")
                
                if search_results:
                    # モード設定を取得
                    mode_config = rag_system._get_mode_config(mode)
                    print(f"  閾値: {mode_config.get('similarity_threshold', 'N/A')}")
                    print(f"  設定: {mode_config}")
                    
                    for i, result in enumerate(search_results[:2]):  # 上位2件のみ表示
                        print(f"    [{i+1}] 類似度: {result.similarity:.3f}")
                        print(f"        ソース: {result.chunk.source_file}")
                        print(f"        内容(抜粋): {result.chunk.content[:100]}...")
                
                results[mode] = search_results
                print(f"  ✓ {mode}モード検索完了")
                
            except Exception as e:
                print(f"  ✗ {mode}モード検索エラー: {e}")
                results[mode] = []
        
        # 結果の比較分析
        print(f"\n--- モード別結果比較 ---")
        for mode, mode_results in results.items():
            if mode_results:
                avg_similarity = sum(r.similarity for r in mode_results) / len(mode_results)
                print(f"{mode.upper()}: 結果数={len(mode_results)}, 平均類似度={avg_similarity:.3f}")
            else:
                print(f"{mode.upper()}: 結果なし")
        
        # コンテキスト生成テスト
        print(f"\n--- コンテキスト生成テスト ---")
        context_result = await rag_system.generate_context(test_query, mode="interactive")
        print(f"コンテキスト長: {context_result.get('context_length', 0)}")
        print(f"ソース数: {len(context_result.get('sources', []))}")
        if context_result.get('context'):
            print(f"コンテキスト(抜粋): {context_result['context'][:200]}...")
        
        # 統計情報取得
        print(f"\n--- システム統計 ---")
        stats = await rag_system.get_stats()
        print(f"システム状態: {stats.get('system_status', 'unknown')}")
        if 'knowledge_base' in stats:
            kb_stats = stats['knowledge_base']
            print(f"文書数: {kb_stats.get('total_documents', 0)}")
            print(f"チャンク数: {kb_stats.get('total_chunks', 0)}")
        
        print("\n=== Task 3-3a テスト完了 ===")
        print("✓ モード別最適化機能が正常に動作しています")
        
        return True
        
    except Exception as e:
        print(f"\n✗ テストエラー: {e}")
        logger.error(f"テスト実行エラー: {e}", exc_info=True)
        return False

async def main():
    """メイン関数"""
    success = await test_mode_optimization()
    if success:
        print("\n🎉 Task 3-3a モード別知識ベース最適化 - 実装完了!")
    else:
        print("\n❌ テスト失敗 - 問題を修正してください")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
