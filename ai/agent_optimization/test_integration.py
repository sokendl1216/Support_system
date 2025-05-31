"""
AIエージェント最適化システム統合テスト

全体システムの動作確認とパフォーマンステストを実行
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pytest

# テスト対象のモジュールをインポート
from ..llm_service import LLMServiceManager
from .optimization_system import AIAgentOptimizationSystem, create_optimized_ai_system
from .config import get_testing_config, get_development_config
from ..agent_orchestrator import ProgressMode, Task

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestAIAgentOptimizationSystem:
    """AIエージェント最適化システムの統合テスト"""
    
    @pytest.fixture
    async def llm_service(self):
        """LLMサービスのモックフィクスチャ"""
        # テスト用のLLMサービス（実際の実装では設定ファイルから読み込み）
        config = {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "timeout": 30
        }
        return LLMServiceManager(config)
    
    @pytest.fixture
    async def optimization_system(self, llm_service):
        """最適化システムのフィクスチャ"""
        config = get_testing_config()
        system = AIAgentOptimizationSystem(llm_service, config)
        await system.initialize()
        await system.start()
        yield system
        await system.stop()
        await system.cleanup()
    
    async def test_system_initialization(self, llm_service):
        """システム初期化テスト"""
        config = get_testing_config()
        system = AIAgentOptimizationSystem(llm_service, config)
        
        # 初期化前の状態確認
        assert not system.is_initialized
        assert not system.is_running
        
        # 初期化実行
        result = await system.initialize()
        assert result is True
        assert system.is_initialized
        
        # コンポーネント初期化確認
        assert system.orchestrator is not None
        assert system.context_manager is not None
        
        await system.cleanup()
    
    async def test_session_creation_and_management(self, optimization_system):
        """セッション作成・管理テスト"""
        # セッション作成
        session_id = await optimization_system.create_session(ProgressMode.AUTO)
        assert session_id is not None
        assert len(session_id) > 0
        
        # セッション状態確認
        status = await optimization_system.get_system_status()
        assert status.active_sessions == 1
        
        # 複数セッション作成
        session_id2 = await optimization_system.create_session(ProgressMode.INTERACTIVE)
        assert session_id2 != session_id
        
        status = await optimization_system.get_system_status()
        assert status.active_sessions == 2
    
    async def test_task_execution_without_optimization(self, optimization_system):
        """最適化なしでのタスク実行テスト"""
        session_id = await optimization_system.create_session()
        
        # シンプルなタスク実行
        result = await optimization_system.execute_task(
            session_id=session_id,
            title="テストタスク",
            description="これはテスト用のシンプルなタスクです",
            requirements={"task_type": "general"},
            use_optimization=False
        )
        
        assert result is not None
        assert "type" in result
        
        # 統計確認
        assert optimization_system.stats["total_tasks_processed"] == 1
        assert optimization_system.stats["successful_tasks"] == 1
    
    async def test_task_execution_with_optimization(self, optimization_system):
        """最適化ありでのタスク実行テスト"""
        session_id = await optimization_system.create_session()
        
        # 最適化機能付きタスク実行
        result = await optimization_system.execute_task(
            session_id=session_id,
            title="最適化テストタスク",
            description="最適化機能をテストするためのタスクです",
            requirements={"task_type": "analysis"},
            use_optimization=True
        )
        
        assert result is not None
        
        # 最適化メタデータの確認
        if "execution_metadata" in result:
            metadata = result["execution_metadata"]
            assert "optimization_applied" in metadata
            assert "learning_applied" in metadata
    
    async def test_error_handling_and_recovery(self, optimization_system):
        """エラーハンドリング・回復テスト"""
        session_id = await optimization_system.create_session()
        
        # エラーを発生させるタスク
        try:
            await optimization_system.execute_task(
                session_id=session_id,
                title="エラーテストタスク",
                description="これは意図的にエラーを発生させるタスクです: FORCE_ERROR",
                requirements={"force_error": True},
                use_optimization=True
            )
        except Exception as e:
            # エラーが適切にハンドリングされているか確認
            assert optimization_system.stats["failed_tasks"] >= 1
            logger.info(f"Expected error caught: {e}")
    
    async def test_performance_monitoring(self, optimization_system):
        """パフォーマンス監視テスト"""
        session_id = await optimization_system.create_session()
        
        # 複数タスクを実行してパフォーマンスデータを生成
        tasks = [
            ("タスク1", "分析タスク", {"task_type": "analysis"}),
            ("タスク2", "実行タスク", {"task_type": "execution"}),
            ("タスク3", "レビュータスク", {"task_type": "review"})
        ]
        
        for title, description, requirements in tasks:
            try:
                await optimization_system.execute_task(
                    session_id=session_id,
                    title=title,
                    description=description,
                    requirements=requirements,
                    use_optimization=True
                )
            except Exception as e:
                logger.warning(f"Task failed: {e}")
        
        # メトリクス取得
        report = await optimization_system.get_comprehensive_report()
        assert "agent_metrics" in report
        assert "statistics" in report
        
        # システムステータス確認
        status = await optimization_system.get_system_status()
        assert status.total_tasks_processed >= 3
        assert status.optimization_score >= 0.0
    
    async def test_learning_functionality(self, optimization_system):
        """学習機能テスト"""
        session_id = await optimization_system.create_session()
        
        # 学習エンジンが利用可能か確認
        if optimization_system.learning_engine:
            # 複数の類似タスクを実行して学習データを蓄積
            for i in range(5):
                try:
                    await optimization_system.execute_task(
                        session_id=session_id,
                        title=f"学習テストタスク{i+1}",
                        description="これは学習機能をテストするためのタスクです",
                        requirements={"task_type": "learning_test", "iteration": i},
                        use_optimization=True
                    )
                except Exception as e:
                    logger.warning(f"Learning task {i+1} failed: {e}")
            
            # 学習パターン分析
            await optimization_system.learning_engine.analyze_patterns()
            
            # 推奨事項取得
            recommendations = await optimization_system.learning_engine.get_agent_recommendations(
                "学習機能をテストする"
            )
            assert isinstance(recommendations, dict)
    
    async def test_context_management(self, optimization_system):
        """コンテキスト管理テスト"""
        if optimization_system.context_manager:
            session_id = await optimization_system.create_session()
            
            # コンテキスト継承を伴うタスク実行
            result1 = await optimization_system.execute_task(
                session_id=session_id,
                title="コンテキストテスト1",
                description="最初のコンテキストタスク",
                requirements={"context_test": True, "phase": 1},
                use_optimization=True
            )
            
            result2 = await optimization_system.execute_task(
                session_id=session_id,
                title="コンテキストテスト2",
                description="コンテキスト継承テスト",
                requirements={"context_test": True, "phase": 2, "previous_task": "コンテキストテスト1"},
                use_optimization=True
            )
            
            # コンテキスト統合
            await optimization_system.context_manager.consolidate_memory()
    
    async def test_diagnostic_system(self, optimization_system):
        """診断システムテスト"""
        if optimization_system.diagnostic_system:
            # システム診断実行
            from .self_diagnostic import HealthMetric
            
            test_metrics = [
                HealthMetric(
                    metric_name="test_metric_1",
                    value=0.8,
                    threshold=0.7,
                    status="healthy",
                    timestamp=datetime.now()
                ),
                HealthMetric(
                    metric_name="test_metric_2",
                    value=0.5,
                    threshold=0.7,
                    status="warning",
                    timestamp=datetime.now()
                )
            ]
            
            await optimization_system.diagnostic_system.run_diagnostics(test_metrics)
    
    async def test_force_optimization(self, optimization_system):
        """手動最適化テスト"""
        # 手動最適化実行
        await optimization_system.force_optimization()
        
        # 最適化カウント確認
        assert optimization_system.stats["optimizations_applied"] >= 1
    
    async def test_system_status_and_reporting(self, optimization_system):
        """システムステータス・レポート機能テスト"""
        # システムステータス取得
        status = await optimization_system.get_system_status()
        assert status.status in ["healthy", "warning", "error", "initializing"]
        assert status.uptime.total_seconds() >= 0
        
        # 包括的レポート取得
        report = await optimization_system.get_comprehensive_report()
        assert "timestamp" in report
        assert "system_status" in report
        assert "statistics" in report
        assert "configuration" in report
        
        # レポートの構造確認
        assert isinstance(report["statistics"], dict)
        assert isinstance(report["configuration"], dict)


class TestPerformanceBenchmark:
    """パフォーマンスベンチマークテスト"""
    
    async def test_task_execution_performance(self):
        """タスク実行パフォーマンステスト"""
        # テスト用LLMサービス
        config = {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "timeout": 30
        }
        llm_service = LLMServiceManager(config)
        
        # 最適化システム初期化
        system = await create_optimized_ai_system(llm_service, get_development_config())
        await system.start()
        
        try:
            session_id = await system.create_session()
            
            # ベンチマークタスク実行
            task_count = 10
            start_time = time.time()
            
            successful_tasks = 0
            failed_tasks = 0
            
            for i in range(task_count):
                try:
                    result = await system.execute_task(
                        session_id=session_id,
                        title=f"ベンチマークタスク{i+1}",
                        description=f"パフォーマンステスト用タスク {i+1}/{task_count}",
                        requirements={"benchmark": True, "task_id": i},
                        use_optimization=True
                    )
                    successful_tasks += 1
                    logger.info(f"Task {i+1} completed successfully")
                except Exception as e:
                    failed_tasks += 1
                    logger.warning(f"Task {i+1} failed: {e}")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # パフォーマンス結果
            logger.info(f"Benchmark Results:")
            logger.info(f"  Total tasks: {task_count}")
            logger.info(f"  Successful: {successful_tasks}")
            logger.info(f"  Failed: {failed_tasks}")
            logger.info(f"  Total time: {total_time:.2f} seconds")
            logger.info(f"  Average time per task: {total_time/task_count:.2f} seconds")
            logger.info(f"  Success rate: {successful_tasks/task_count*100:.1f}%")
            
            # 最終レポート取得
            final_report = await system.get_comprehensive_report()
            logger.info(f"Final optimization score: {final_report.get('system_status', {}).get('optimization_score', 'N/A')}")
            
        finally:
            await system.stop()
            await system.cleanup()


class TestStressTest:
    """ストレステスト"""
    
    async def test_concurrent_task_execution(self):
        """並行タスク実行ストレステスト"""
        config = {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "timeout": 60
        }
        llm_service = LLMServiceManager(config)
        
        system = await create_optimized_ai_system(llm_service, get_development_config())
        await system.start()
        
        try:
            # 複数セッションを作成
            sessions = []
            for i in range(3):
                session_id = await system.create_session()
                sessions.append(session_id)
            
            # 並行タスク実行
            async def execute_task_batch(session_id: str, batch_id: int):
                tasks_per_batch = 5
                results = []
                
                for i in range(tasks_per_batch):
                    try:
                        result = await system.execute_task(
                            session_id=session_id,
                            title=f"並行タスク_バッチ{batch_id}_タスク{i+1}",
                            description=f"ストレステスト用並行タスク",
                            requirements={"stress_test": True, "batch_id": batch_id, "task_id": i},
                            use_optimization=True
                        )
                        results.append({"success": True, "result": result})
                    except Exception as e:
                        results.append({"success": False, "error": str(e)})
                
                return results
            
            # 並行実行
            start_time = time.time()
            batch_tasks = [
                execute_task_batch(sessions[i], i) for i in range(len(sessions))
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            end_time = time.time()
            
            # 結果集計
            total_tasks = 0
            successful_tasks = 0
            
            for batch_result in batch_results:
                if isinstance(batch_result, list):
                    for task_result in batch_result:
                        total_tasks += 1
                        if task_result.get("success", False):
                            successful_tasks += 1
            
            logger.info(f"Stress Test Results:")
            logger.info(f"  Total tasks: {total_tasks}")
            logger.info(f"  Successful: {successful_tasks}")
            logger.info(f"  Failed: {total_tasks - successful_tasks}")
            logger.info(f"  Total time: {end_time - start_time:.2f} seconds")
            logger.info(f"  Success rate: {successful_tasks/total_tasks*100:.1f}%")
            
        finally:
            await system.stop()
            await system.cleanup()


# テスト実行用のメイン関数

async def run_integration_tests():
    """統合テストを実行"""
    logger.info("Starting AI Agent Optimization System Integration Tests...")
    
    try:
        # 基本的なテスト
        logger.info("Running basic functionality tests...")
        
        # LLMサービス設定
        config = {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "timeout": 30
        }
        llm_service = LLMServiceManager(config)
        
        # システム作成と初期化
        system = await create_optimized_ai_system(llm_service, get_testing_config())
        await system.start()
        
        # 基本動作テスト
        session_id = await system.create_session(ProgressMode.AUTO)
        
        # サンプルタスク実行
        result = await system.execute_task(
            session_id=session_id,
            title="統合テスト用タスク",
            description="システム全体の動作を確認するためのテストタスクです",
            requirements={"test_type": "integration"},
            use_optimization=True
        )
        
        logger.info(f"Sample task completed: {result.get('type', 'unknown')}")
        
        # システムステータス確認
        status = await system.get_system_status()
        logger.info(f"System status: {status.status}")
        logger.info(f"Optimization score: {status.optimization_score:.2f}")
        
        # 最適化実行
        await system.force_optimization()
        
        # 最終レポート
        report = await system.get_comprehensive_report()
        logger.info(f"Total tasks processed: {report['statistics']['total_tasks_processed']}")
        
        await system.stop()
        await system.cleanup()
        
        logger.info("Integration tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Integration tests failed: {e}")
        return False


if __name__ == "__main__":
    # テスト実行
    result = asyncio.run(run_integration_tests())
    if result:
        print("✅ All integration tests passed!")
    else:
        print("❌ Integration tests failed!")
