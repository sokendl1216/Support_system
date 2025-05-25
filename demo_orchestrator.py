# filepath: c:\Users\ss962\Desktop\仕事\Support_system\demo_orchestrator.py
"""
エージェントオーケストレーターのデモアプリケーション

このスクリプトはエージェントオーケストレーションシステムの
各機能をデモンストレーションします。
"""

import asyncio
import json
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 相対インポートの代わりに直接インポート
from ai.orchestrator_utils import (
    OrchestratorClient, 
    TaskTemplates, 
    quick_auto_execution,
    quick_interactive_execution,
    task
)
from ai.agent_orchestrator import ProgressMode


async def demo_basic_orchestrator():
    """基本的なオーケストレーター機能のデモ"""
    print("\n" + "="*60)
    print("🤖 エージェントオーケストレーター基本機能デモ")
    print("="*60)
    
    client = OrchestratorClient()
    
    try:
        # 初期化
        print("\n📋 オーケストレーターを初期化中...")
        success = await client.initialize()
        if not success:
            print("❌ 初期化に失敗しました")
            return
        print("✅ 初期化完了")
        
        # セッション開始
        print("\n🚀 セッションを開始...")
        session_id = await client.start_session("interactive")
        print(f"✅ セッション開始: {session_id}")
        
        # セッション状態確認
        status = client.get_session_status()
        print(f"\n📊 セッション状態:")
        print(f"  モード: {status['mode']}")
        print(f"  エージェント数: {len(status['agents'])}")
        print(f"  実行中: {status['is_running']}")
        
        print("\n👥 利用可能なエージェント:")
        for agent_id, agent_info in status['agents'].items():
            print(f"  - {agent_id}: {agent_info['role']} ({', '.join(agent_info['capabilities'])})")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        await client.shutdown()


async def demo_auto_mode():
    """全自動モードのデモ"""
    print("\n" + "="*60)
    print("🤖 全自動モード（Auto-GPT型）デモ")
    print("="*60)
    
    # タスク例: Pythonでのファイル処理スクリプト作成
    task_params = TaskTemplates.code_generation(
        language="Python",
        functionality="CSVファイル読み込み・データ分析スクリプト",
        requirements=[
            "pandasライブラリ使用",
            "基本統計の計算",
            "グラフ作成機能",
            "エラーハンドリング完備"
        ]
    )
    
    print(f"\n📝 タスク: {task_params['title']}")
    print(f"説明: {task_params['description']}")
    print(f"要件: {', '.join(task_params['requirements'])}")
    
    print("\n🔄 全自動実行中...")
    start_time = datetime.now()
    
    try:
        result = await quick_auto_execution(
            title=task_params['title'],
            description=task_params['description'],
            requirements=task_params['requirements']
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ 実行完了 (実行時間: {execution_time:.2f}秒)")
        print(f"タスクID: {result['task_id']}")
        
        # 結果の詳細表示
        task_result = result['result']
        
        if 'coordination' in task_result:
            print(f"\n📋 調整結果:")
            coord_result = task_result['coordination']
            if 'subtasks' in coord_result:
                print(f"  サブタスク数: {len(coord_result['subtasks'])}")
            if 'assignments' in coord_result:
                print(f"  割り当て数: {len(coord_result['assignments'])}")
        
        if 'analysis' in task_result:
            print(f"\n🔍 分析結果:")
            analysis = task_result['analysis']
            if 'analysis' in analysis:
                print(f"  複雑度: {analysis['analysis'].get('complexity', 'N/A')}")
            if 'risks' in analysis:
                print(f"  リスク数: {len(analysis['risks'])}")
        
        if 'execution' in task_result:
            print(f"\n⚡ 実行結果:")
            execution = task_result['execution']
            print(f"  タイプ: {execution.get('type', 'N/A')}")
            print(f"  ステータス: {execution.get('status', 'N/A')}")
            
            # 生成されたコンテンツの一部を表示
            content = execution.get('content', '')
            if content:
                print(f"\n📄 生成されたコンテンツ（抜粋）:")
                print("-" * 40)
                # 最初の500文字を表示
                print(content[:500] + ("..." if len(content) > 500 else ""))
                print("-" * 40)
        
        if 'review' in task_result:
            print(f"\n📝 レビュー結果:")
            review = task_result['review']
            print(f"  総合評価: {review.get('overall_score', 'N/A')}/10")
            print(f"  承認状態: {review.get('approval_status', 'N/A')}")
            
            strengths = review.get('strengths', [])
            if strengths:
                print(f"  良い点: {', '.join(strengths[:3])}")
            
            recommendations = review.get('recommendations', [])
            if recommendations:
                print(f"  推奨事項: {', '.join(recommendations[:3])}")
    
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()


async def demo_interactive_mode():
    """対話型モードのデモ"""
    print("\n" + "="*60)
    print("🤖 対話型モード（LangChain型）デモ")
    print("="*60)
    
    # タスク例: マーケティング戦略文書作成
    task_params = TaskTemplates.document_creation(
        doc_type="マーケティング戦略書",
        topic="新しいAIサービス",
        requirements=[
            "ターゲット市場分析",
            "競合分析",
            "価格戦略",
            "プロモーション計画",
            "実行スケジュール"
        ]
    )
    
    print(f"\n📝 タスク: {task_params['title']}")
    print(f"説明: {task_params['description']}")
    print(f"要件: {', '.join(task_params['requirements'])}")
    
    print("\n🔄 対話型実行中（分析・計画段階）...")
    
    try:
        result = await quick_interactive_execution(
            title=task_params['title'],
            description=task_params['description'],
            requirements=task_params['requirements']
        )
        
        print(f"\n✅ 分析・計画完了")
        print(f"タスクID: {result['task_id']}")
        
        task_result = result['result']
        
        if 'steps' in task_result:
            print(f"\n📋 実行ステップ:")
            for i, step in enumerate(task_result['steps']):
                print(f"\n  ステップ {i+1}: {step['step']}")
                print(f"    承認要求: {'Yes' if step.get('requires_approval', False) else 'No'}")
                print(f"    承認済み: {'Yes' if step.get('approved', False) else 'No'}")
                
                # ステップ結果の詳細
                step_result = step.get('result', {})
                if step['step'] == 'analysis' and 'analysis' in step_result:
                    analysis = step_result['analysis']
                    print(f"    複雑度: {analysis.get('complexity', 'N/A')}")
                    print(f"    推定時間: {analysis.get('estimated_time', 'N/A')}秒")
                
                elif step['step'] == 'planning' and 'subtasks' in step_result:
                    subtasks = step_result['subtasks']
                    print(f"    サブタスク数: {len(subtasks)}")
                    for j, subtask in enumerate(subtasks[:3]):  # 最初の3つのみ表示
                        print(f"      {j+1}. {subtask.title}")
        
        print(f"\n📊 現在の状態: {task_result.get('status', 'N/A')}")
        print("\n💡 対話型モードでは、各ステップを確認・承認してから次に進みます")
    
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()


async def demo_task_builder():
    """TaskBuilderのデモ"""
    print("\n" + "="*60)
    print("🔧 TaskBuilderデモ")
    print("="*60)
    
    # TaskBuilderを使用してタスクを構築
    task_params = (
        task()
        .set_title("レスポンシブWebサイト開発")
        .set_description("モダンなレスポンシブWebサイトを開発してください")
        .add_requirement("HTML5/CSS3/JavaScript使用")
        .add_requirement("モバイルファーストデザイン")
        .add_requirement("アクセシビリティ対応")
        .add_requirements([
            "SEO最適化",
            "パフォーマンス最適化",
            "クロスブラウザ対応"
        ])
        .build()
    )
    
    print(f"📝 構築されたタスク:")
    print(f"  タイトル: {task_params['title']}")
    print(f"  説明: {task_params['description']}")
    print(f"  要件数: {len(task_params['requirements'])}")
    print(f"  要件:")
    for i, req in enumerate(task_params['requirements'], 1):
        print(f"    {i}. {req}")
    
    # テンプレートとの比較
    print(f"\n🔄 Web開発テンプレートとの比較:")
    template_params = TaskTemplates.web_development(
        feature="レスポンシブWebサイト",
        technology="HTML5/CSS3/JavaScript"
    )
    
    print(f"  テンプレートタイトル: {template_params['title']}")
    print(f"  テンプレート要件数: {len(template_params['requirements'])}")


async def demo_complex_workflow():
    """複雑なワークフローのデモ"""
    print("\n" + "="*60)
    print("🔄 複雑なワークフローデモ")
    print("="*60)
    
    client = OrchestratorClient()
    
    try:
        # 初期化
        await client.initialize()
        
        # 複数のタスクを連続実行
        tasks = [
            {
                "title": "要件分析",
                "description": "プロジェクトの要件を分析してください",
                "requirements": ["詳細分析", "リスク評価"]
            },
            {
                "title": "アーキテクチャ設計",
                "description": "システムアーキテクチャを設計してください",
                "requirements": ["スケーラビリティ", "セキュリティ"]
            },
            {
                "title": "実装計画",
                "description": "実装計画を策定してください",
                "requirements": ["スケジュール", "リソース配分"]
            }
        ]
        
        # 対話型モードで各タスクを実行
        session_id = await client.start_session("interactive")
        print(f"セッション開始: {session_id}")
        
        for i, task_params in enumerate(tasks, 1):
            print(f"\n--- タスク {i}: {task_params['title']} ---")
            
            result = await client.add_and_execute_task(
                title=task_params['title'],
                description=task_params['description'],
                requirements=task_params['requirements']
            )
            
            print(f"✅ タスク {i} 完了: {result['task_id']}")
            
            # 短い休憩
            await asyncio.sleep(0.5)
        
        # 最終的なセッション状態
        final_status = client.get_session_status()
        print(f"\n📊 最終セッション状態:")
        print(f"  総タスク数: {final_status['total_tasks']}")
        print(f"  完了タスク数: {final_status['completed_tasks']}")
        print(f"  失敗タスク数: {final_status['failed_tasks']}")
    
    except Exception as e:
        print(f"❌ ワークフローエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.shutdown()


async def main():
    """メインデモ関数"""
    print("🎯 エージェントオーケストレーションシステム デモ")
    print("=" * 80)
    
    demos = [
        ("基本機能", demo_basic_orchestrator),
        ("全自動モード", demo_auto_mode),
        ("対話型モード", demo_interactive_mode),
        ("TaskBuilder", demo_task_builder),
        ("複雑なワークフロー", demo_complex_workflow)
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
            print(f"\n✅ {name}デモ完了")
        except Exception as e:
            print(f"\n❌ {name}デモでエラー: {e}")
        
        # デモ間の休憩
        await asyncio.sleep(1)
    
    print("\n" + "="*80)
    print("🎉 全デモ完了！")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
