# filepath: c:\Users\ss962\Desktop\仕事\Support_system\test_orchestrator.py
"""
エージェントオーケストレーターの簡単なテスト
"""

import asyncio
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)

async def test_basic_import():
    """基本的なインポートテスト"""
    print("🔍 基本インポートテスト開始...")
    
    try:
        from ai.agent_orchestrator import AgentOrchestrator, ProgressMode
        print("✅ AgentOrchestrator インポート成功")
        
        from ai.orchestrator_utils import OrchestratorClient
        print("✅ OrchestratorClient インポート成功")
        
        from ai.llm_initializer import LLMServiceInitializer
        print("✅ LLMServiceInitializer インポート成功")
        
        return True
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        return False

async def test_initialization():
    """初期化テスト"""
    print("\n🔧 初期化テスト開始...")
    
    try:
        from ai.orchestrator_utils import OrchestratorClient
        
        client = OrchestratorClient()
        success = await client.initialize()
        
        if success:
            print("✅ オーケストレーター初期化成功")
            
            # セッション開始テスト
            session_id = await client.start_session("interactive")
            print(f"✅ セッション開始成功: {session_id}")
            
            # 状態確認
            status = client.get_session_status()
            print(f"✅ セッション状態取得成功: {status['mode']}")
            
            await client.shutdown()
            print("✅ シャットダウン成功")
            
            return True
        else:
            print("❌ 初期化失敗")
            return False
            
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_task():
    """簡単なタスク実行テスト"""
    print("\n📝 簡単なタスク実行テスト開始...")
    
    try:
        from ai.orchestrator_utils import quick_interactive_execution
        
        result = await quick_interactive_execution(
            title="テストタスク",
            description="これは簡単なテストタスクです",
            requirements=["テスト要件1", "テスト要件2"]
        )
        
        print(f"✅ タスク実行成功: {result['task_id']}")
        print(f"  モード: {result['result'].get('mode', 'N/A')}")
        print(f"  ステータス: {result['result'].get('status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ タスク実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト関数"""
    print("🎯 エージェントオーケストレーター テスト")
    print("=" * 50)
    
    tests = [
        ("基本インポート", test_basic_import),
        ("初期化", test_initialization), 
        ("簡単なタスク実行", test_simple_task)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
            if result:
                print(f"✅ {name}テスト成功")
            else:
                print(f"❌ {name}テスト失敗")
        except Exception as e:
            print(f"❌ {name}テストでエラー: {e}")
            results.append((name, False))
        
        print("-" * 30)
    
    # 結果サマリー
    print("\n📊 テスト結果サマリー:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"  成功: {passed}/{total}")
    print(f"  失敗: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 全テスト成功！")
    else:
        print("⚠️  一部テストが失敗しました")

if __name__ == "__main__":
    asyncio.run(main())
