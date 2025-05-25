#!/usr/bin/env python3
"""
RAGシステム簡易テスト - Task 3-3a実装用
"""

import asyncio
import logging
import json
from pathlib import Path
import sys

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai.rag.rag_system import RAGSystem

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_test.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_rag_search():
    """RAG検索の簡易テスト"""
    
    # 設定読み込み
    config_path = Path(__file__).parent / "config" / "rag_config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "embedding": {"model_name": "nomic-embed-text"},
            "vector_store": {"dimension": 768},
            "knowledge_base": {"base_path": "ai/rag/knowledge_base"},
            "retrieval": {"top_k": 5, "similarity_threshold": 0.5},
            "mode_optimization": {
                "interactive": {"top_k": 3, "similarity_threshold": 0.5},
                "autonomous": {"top_k": 5, "similarity_threshold": 0.4}
            }
        }
    
    # RAGシステム初期化
    rag_system = RAGSystem(config)
    await rag_system.initialize()
    
    # 簡単な検索テスト
    query = "システムの機能"
    
    print(f"\n=== 検索テスト: '{query}' ===")
    
    # 対話型モード
    interactive_results = await rag_system.search(query, mode='interactive')
    print(f"対話型モード結果数: {len(interactive_results)}")
    
    # 自律型モード
    autonomous_results = await rag_system.search(query, mode='autonomous')
    print(f"自律型モード結果数: {len(autonomous_results)}")
    
    # 結果表示
    if interactive_results:
        print(f"対話型トップ結果類似度: {interactive_results[0].similarity:.3f}")
        print(f"内容: {interactive_results[0].chunk.content[:100]}...")
    
    if autonomous_results:
        print(f"自律型トップ結果類似度: {autonomous_results[0].similarity:.3f}")
        print(f"内容: {autonomous_results[0].chunk.content[:100]}...")
    
    # 統計情報
    stats = await rag_system.get_stats()
    kb_stats = stats.get('knowledge_base', {})
    print(f"\n知識ベース統計:")
    print(f"  文書数: {kb_stats.get('total_documents', 0)}")
    print(f"  チャンク数: {kb_stats.get('total_chunks', 0)}")
    
    return len(interactive_results) > 0 or len(autonomous_results) > 0

if __name__ == "__main__":
    success = asyncio.run(test_rag_search())
    if success:
        print("\n✅ RAGシステムは正常に動作しています")
    else:
        print("\n❌ RAGシステムに問題があります")
