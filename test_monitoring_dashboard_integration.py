"""
AIキャッシュシステム監視ダッシュボード統合テスト

本番環境向けの統合テストとして、監視ダッシュボードとキャッシュシステムの
連携動作を総合的に検証します。
"""

import asyncio
import logging
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# インポート
from ai.cache_manager import AICacheManager
from ai.simplified_high_performance_cache import SimplifiedHighPerformanceCache
from ai.monitoring.cache_dashboard import (
    CacheDashboard, AlertConfig, CacheMetrics, 
    setup_monitoring_dashboard, slack_alert_handler, email_alert_handler
)

class IntegrationTestSuite:
    """統合テストスイート"""
    
    def __init__(self):
        self.test_results = []
        self.dashboard = None
        self.cache_managers = []
        self.test_start_time = None
        
    async def setup_test_environment(self):
        """テスト環境セットアップ"""
        logger.info("🔧 テスト環境をセットアップ中...")
        
        # テスト用キャッシュディレクトリ
        test_cache_dir = Path("./test_integration_cache")
        if test_cache_dir.exists():
            import shutil
            shutil.rmtree(test_cache_dir)
        test_cache_dir.mkdir(exist_ok=True)
        
        # 複数のキャッシュマネージャーを初期化
        self.cache_managers = [
            AICacheManager(
                cache_dir=str(test_cache_dir / "basic"),
                ttl_seconds=3600,
                max_cache_size_mb=50,
                enable_cache=True
            ),
            SimplifiedHighPerformanceCache(
                cache_dir=str(test_cache_dir / "high_perf"),
                ttl_seconds=3600,
                max_cache_size_mb=50,
                enable_cache=True
            )
        ]
        
        # 監視ダッシュボードセットアップ
        alert_config = AlertConfig(
            hit_ratio_threshold=0.6,  # テスト用低い閾値
            response_time_threshold_ms=500.0,
            memory_usage_threshold_mb=100.0,
            error_rate_threshold=0.1
        )
        
        self.dashboard = CacheDashboard(
            cache_manager_refs=self.cache_managers,
            alert_config=alert_config,
            metrics_history_size=100
        )
        
        # テスト用アラートハンドラー
        self.dashboard.add_alert_handler(self._test_alert_handler)
        
        # 監視開始
        await self.dashboard.start_monitoring()
        self.test_start_time = time.time()
        
        logger.info("✅ テスト環境セットアップ完了")
        
    async def _test_alert_handler(self, alert: Dict[str, Any]):
        """テスト用アラートハンドラー"""
        logger.warning(f"🚨 テストアラート受信: {alert['severity']} - {alert['message']}")
        
    async def test_basic_cache_operations(self) -> bool:
        """基本キャッシュ操作テスト"""
        logger.info("\n📋 テスト1: 基本キャッシュ操作")
        
        try:
            test_data = [
                {"query": f"テストクエリ {i}", "model": "test-model"}
                for i in range(10)
            ]
            
            test_results = [
                {"answer": f"テスト回答 {i}", "tokens": 100 + i * 10}
                for i in range(10)
            ]
            
            # 書き込みテスト
            write_times = []
            for i, (key_data, result) in enumerate(zip(test_data, test_results)):
                start_time = time.time()
                
                # 各キャッシュマネージャーに書き込み
                for cache_manager in self.cache_managers:
                    await cache_manager.set_cache(key_data, result)
                
                write_time = time.time() - start_time
                write_times.append(write_time)
                
                if i % 5 == 0:
                    logger.info(f"  書き込み進捗: {i+1}/10 (平均時間: {sum(write_times)/len(write_times):.4f}秒)")
            
            # 読み込みテスト
            hit_count = 0
            read_times = []
            
            for key_data in test_data:
                start_time = time.time()
                
                # 各キャッシュマネージャーから読み込み
                for cache_manager in self.cache_managers:
                    hit, cached_result = await cache_manager.get_cache(key_data)
                    if hit:
                        hit_count += 1
                
                read_time = time.time() - start_time
                read_times.append(read_time)
            
            # 結果評価
            expected_hits = len(test_data) * len(self.cache_managers)
            hit_ratio = hit_count / expected_hits
            avg_write_time = sum(write_times) / len(write_times)
            avg_read_time = sum(read_times) / len(read_times)
            
            logger.info(f"  ✅ ヒット率: {hit_ratio:.2%} ({hit_count}/{expected_hits})")
            logger.info(f"  ✅ 平均書き込み時間: {avg_write_time:.4f}秒")
            logger.info(f"  ✅ 平均読み込み時間: {avg_read_time:.4f}秒")
            
            success = hit_ratio >= 0.95  # 95%以上のヒット率を期待
            self.test_results.append({
                "test_name": "基本キャッシュ操作",
                "success": success,
                "hit_ratio": hit_ratio,
                "avg_write_time": avg_write_time,
                "avg_read_time": avg_read_time
            })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 基本キャッシュ操作テスト失敗: {e}")
            self.test_results.append({
                "test_name": "基本キャッシュ操作",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_monitoring_metrics_collection(self) -> bool:
        """監視メトリクス収集テスト"""
        logger.info("\n📊 テスト2: 監視メトリクス収集")
        
        try:
            # 初期メトリクス数
            initial_metrics_count = len(self.dashboard.metrics_history)
            
            # 20秒間監視して、メトリクスが収集されることを確認
            logger.info("  20秒間メトリクス収集を観測...")
            await asyncio.sleep(22)  # 監視間隔10秒 + バッファ
            
            # メトリクス確認
            final_metrics_count = len(self.dashboard.metrics_history)
            new_metrics = final_metrics_count - initial_metrics_count
            
            logger.info(f"  ✅ 新規メトリクス: {new_metrics}個")
            
            if new_metrics > 0:
                latest_metrics = self.dashboard.metrics_history[-1]
                logger.info(f"  ✅ 最新ヒット率: {latest_metrics.hit_ratio:.2%}")
                logger.info(f"  ✅ 最新レスポンス時間: {latest_metrics.response_time_ms:.1f}ms")
                logger.info(f"  ✅ 最新メモリ使用量: {latest_metrics.memory_usage_mb:.1f}MB")
                
                success = new_metrics >= 1
            else:
                success = False
                logger.error("  ❌ メトリクスが収集されていません")
            
            self.test_results.append({
                "test_name": "監視メトリクス収集",
                "success": success,
                "new_metrics_count": new_metrics,
                "latest_metrics": latest_metrics.__dict__ if new_metrics > 0 else None
            })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 監視メトリクス収集テスト失敗: {e}")
            self.test_results.append({
                "test_name": "監視メトリクス収集",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_alert_system(self) -> bool:
        """アラートシステムテスト"""
        logger.info("\n🚨 テスト3: アラートシステム")
        
        try:
            # 初期アラート数
            initial_alerts = len(self.dashboard.alerts_history)
            
            # 低ヒット率を意図的に作成（アラート発生させる）
            logger.info("  低ヒット率状況を作成中...")
            
            # 存在しないキーでミスを大量発生
            miss_data = [
                {"query": f"存在しないクエリ {i}", "model": "test-model"}
                for i in range(20)
            ]
            
            for key_data in miss_data:
                for cache_manager in self.cache_managers:
                    hit, _ = await cache_manager.get_cache(key_data)
                    # 意図的にミス発生
            
            # アラートチェックを待つ
            logger.info("  アラート発生を待機中...")
            await asyncio.sleep(15)  # 監視間隔を待つ
            
            # アラート確認
            final_alerts = len(self.dashboard.alerts_history)
            new_alerts = final_alerts - initial_alerts
            
            logger.info(f"  ✅ 新規アラート: {new_alerts}個")
            
            if new_alerts > 0:
                for alert in list(self.dashboard.alerts_history)[-new_alerts:]:
                    logger.info(f"    - {alert['severity']}: {alert['type']} - {alert['message']}")
                success = True
            else:
                logger.warning("  ⚠️ アラートが発生していません（閾値調整が必要な可能性）")
                success = False
            
            self.test_results.append({
                "test_name": "アラートシステム",
                "success": success,
                "new_alerts_count": new_alerts,
                "alerts": list(self.dashboard.alerts_history)[-new_alerts:] if new_alerts > 0 else []
            })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ アラートシステムテスト失敗: {e}")
            self.test_results.append({
                "test_name": "アラートシステム",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_dashboard_data_generation(self) -> bool:
        """ダッシュボードデータ生成テスト"""
        logger.info("\n📈 テスト4: ダッシュボードデータ生成")
        
        try:
            # 現在のステータス取得
            status = self.dashboard.get_current_status()
            logger.info(f"  ✅ 監視ステータス: {status['status']}")
            
            # パフォーマンス概要取得
            summary = self.dashboard.get_performance_summary(hours=1)
            logger.info(f"  ✅ データポイント数: {summary.get('data_points', 0)}")
            
            # ダッシュボードファイル確認
            dashboard_file = self.dashboard.dashboard_data_path / "dashboard.json"
            if dashboard_file.exists():
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    dashboard_data = json.load(f)
                    
                logger.info(f"  ✅ ダッシュボードファイル更新: {dashboard_data.get('last_updated', 'N/A')}")
                
                success = (
                    status['status'] == 'active' and 
                    summary.get('data_points', 0) > 0 and
                    dashboard_data.get('latest_metrics') is not None
                )
            else:
                success = False
                logger.error("  ❌ ダッシュボードファイルが生成されていません")
            
            self.test_results.append({
                "test_name": "ダッシュボードデータ生成",
                "success": success,
                "status": status,
                "summary": summary,
                "dashboard_file_exists": dashboard_file.exists()
            })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ ダッシュボードデータ生成テスト失敗: {e}")
            self.test_results.append({
                "test_name": "ダッシュボードデータ生成",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_stress_and_performance(self) -> bool:
        """ストレステスト・パフォーマンステスト"""
        logger.info("\n⚡ テスト5: ストレス・パフォーマンス")
        
        try:
            # 大量リクエスト処理テスト
            request_count = 100
            concurrent_requests = 10
            
            logger.info(f"  {request_count}リクエストを{concurrent_requests}並行で処理...")
            
            async def process_request_batch(start_idx: int, batch_size: int):
                """リクエストバッチ処理"""
                batch_times = []
                for i in range(start_idx, start_idx + batch_size):
                    key_data = {"query": f"ストレステストクエリ {i}", "model": "stress-test"}
                    result_data = {"answer": f"ストレステスト回答 {i}", "tokens": 150}
                    
                    start_time = time.time()
                    
                    # 書き込み
                    for cache_manager in self.cache_managers:
                        await cache_manager.set_cache(key_data, result_data)
                    
                    # 読み込み
                    for cache_manager in self.cache_managers:
                        await cache_manager.get_cache(key_data)
                    
                    batch_times.append(time.time() - start_time)
                
                return batch_times
            
            # 並行処理実行
            batch_size = request_count // concurrent_requests
            tasks = [
                process_request_batch(i * batch_size, batch_size)
                for i in range(concurrent_requests)
            ]
            
            start_time = time.time()
            batch_results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # 結果集計
            all_times = []
            for batch_times in batch_results:
                all_times.extend(batch_times)
            
            avg_request_time = sum(all_times) / len(all_times)
            max_request_time = max(all_times)
            throughput = request_count / total_time
            
            logger.info(f"  ✅ 総処理時間: {total_time:.2f}秒")
            logger.info(f"  ✅ 平均リクエスト時間: {avg_request_time:.4f}秒")
            logger.info(f"  ✅ 最大リクエスト時間: {max_request_time:.4f}秒")
            logger.info(f"  ✅ スループット: {throughput:.1f}req/sec")
            
            # パフォーマンス基準
            success = (
                avg_request_time < 0.1 and  # 平均100ms未満
                max_request_time < 0.5 and  # 最大500ms未満
                throughput > 10              # 10req/sec以上
            )
            
            self.test_results.append({
                "test_name": "ストレス・パフォーマンス",
                "success": success,
                "total_time": total_time,
                "avg_request_time": avg_request_time,
                "max_request_time": max_request_time,
                "throughput": throughput,
                "request_count": request_count
            })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ ストレス・パフォーマンステスト失敗: {e}")
            self.test_results.append({
                "test_name": "ストレス・パフォーマンス",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def generate_test_report(self):
        """テストレポート生成"""
        logger.info("\n📄 テストレポート生成中...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        test_duration = time.time() - self.test_start_time if self.test_start_time else 0
        
        # レポート生成
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "test_duration_seconds": test_duration,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "monitoring_status": self.dashboard.get_current_status() if self.dashboard else None,
            "performance_summary": self.dashboard.get_performance_summary(hours=1) if self.dashboard else None
        }
        
        # ファイル保存
        report_file = Path("./test_integration_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # コンソール表示
        logger.info("=" * 60)
        logger.info("🎯 統合テスト結果サマリー")
        logger.info("=" * 60)
        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {passed_tests} ✅")
        logger.info(f"失敗: {total_tests - passed_tests} ❌")
        logger.info(f"成功率: {passed_tests/total_tests:.1%}")
        logger.info(f"実行時間: {test_duration:.1f}秒")
        logger.info(f"レポートファイル: {report_file}")
        
        # 個別テスト結果
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"  {status} {result['test_name']}")
            
        return report
    
    async def cleanup(self):
        """クリーンアップ"""
        logger.info("\n🧹 テスト環境クリーンアップ中...")
        
        if self.dashboard:
            await self.dashboard.stop_monitoring()
        
        # テストファイル削除
        test_cache_dir = Path("./test_integration_cache")
        if test_cache_dir.exists():
            import shutil
            shutil.rmtree(test_cache_dir)
        
        logger.info("✅ クリーンアップ完了")

async def run_integration_tests():
    """統合テスト実行"""
    logger.info("🚀 AIキャッシュシステム監視ダッシュボード統合テスト開始")
    
    test_suite = IntegrationTestSuite()
    
    try:
        # テスト環境セットアップ
        await test_suite.setup_test_environment()
        
        # テスト実行
        test_functions = [
            test_suite.test_basic_cache_operations,
            test_suite.test_monitoring_metrics_collection,
            test_suite.test_alert_system,
            test_suite.test_dashboard_data_generation,
            test_suite.test_stress_and_performance
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"テスト実行エラー: {test_func.__name__}: {e}")
        
        # レポート生成
        report = await test_suite.generate_test_report()
        
        return report
        
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
