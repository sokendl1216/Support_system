"""
AIキャッシュシステム運用監視ダッシュボード

このモジュールは、本番運用時のキャッシュヒット率・レスポンス・エラー監視を
リアルタイムで可視化するダッシュボードを提供します。
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import threading
from dataclasses import dataclass, asdict
from collections import deque
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class CacheMetrics:
    """キャッシュメトリクス"""
    timestamp: float
    hit_ratio: float
    response_time_ms: float
    memory_usage_mb: float
    disk_usage_mb: float
    active_connections: int
    error_count: int
    total_requests: int

@dataclass
class AlertConfig:
    """アラート設定"""
    hit_ratio_threshold: float = 0.7  # ヒット率70%未満でアラート
    response_time_threshold_ms: float = 1000.0  # 1秒以上でアラート
    memory_usage_threshold_mb: float = 500.0  # 500MB以上でアラート
    error_rate_threshold: float = 0.05  # エラー率5%以上でアラート

class CacheDashboard:
    """
    AIキャッシュシステム運用監視ダッシュボード
    """
    
    def __init__(self, cache_manager_refs: List[Any], 
                 alert_config: AlertConfig = None,
                 metrics_history_size: int = 1000):
        """
        初期化
        
        Args:
            cache_manager_refs: 監視対象のキャッシュマネージャーのリスト
            alert_config: アラート設定
            metrics_history_size: メトリクス履歴の保持数
        """
        self.cache_managers = cache_manager_refs
        self.alert_config = alert_config or AlertConfig()
        self.metrics_history = deque(maxlen=metrics_history_size)
        self.alerts_history = deque(maxlen=100)
        
        # 監視状態
        self.is_monitoring = False
        self.monitoring_interval = 10.0  # 10秒間隔
        self.monitoring_task = None
        
        # アラート通知設定
        self.alert_handlers = []
        
        # ダッシュボードデータ保存パス
        self.dashboard_data_path = Path("./dashboard_data")
        self.dashboard_data_path.mkdir(exist_ok=True)
        
        logger.info("キャッシュダッシュボードを初期化しました")
    
    def add_alert_handler(self, handler):
        """アラートハンドラーを追加"""
        self.alert_handlers.append(handler)
        logger.info(f"アラートハンドラーを追加: {handler.__name__}")
    
    async def start_monitoring(self):
        """監視開始"""
        if self.is_monitoring:
            logger.warning("監視は既に開始されています")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("キャッシュ監視を開始しました")
    
    async def stop_monitoring(self):
        """監視停止"""
        if not self.is_monitoring:
            logger.warning("監視は開始されていません")
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("キャッシュ監視を停止しました")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        logger.info("監視ループを開始")
        
        try:
            while self.is_monitoring:
                # メトリクス収集
                await self._collect_metrics()
                
                # アラートチェック
                await self._check_alerts()
                
                # ダッシュボードデータ保存
                await self._save_dashboard_data()
                
                # 次の監視まで待機
                await asyncio.sleep(self.monitoring_interval)
        
        except asyncio.CancelledError:
            logger.info("監視ループがキャンセルされました")
        except Exception as e:
            logger.error(f"監視ループエラー: {e}")
    
    async def _collect_metrics(self):
        """メトリクス収集"""
        try:
            current_time = time.time()
            
            # 各キャッシュマネージャーからメトリクス収集
            total_hits = 0
            total_requests = 0
            total_errors = 0
            total_response_times = []
            memory_usage = 0
            disk_usage = 0
            active_connections = 0
            
            for cache_manager in self.cache_managers:
                if hasattr(cache_manager, 'get_stats'):
                    stats = await cache_manager.get_stats()
                    
                    total_hits += stats.get('hits', 0) + stats.get('memory_hits', 0) + stats.get('similarity_hits', 0)
                    total_requests += stats.get('total_requests', 0)
                    total_errors += stats.get('errors', 0)
                    
                    # レスポンス時間（推定）
                    if stats.get('avg_response_time'):
                        total_response_times.append(stats['avg_response_time'])
                    
                    # メモリ使用量
                    memory_usage += stats.get('size_mb', 0)
                    
                    # ディスク使用量
                    disk_usage += stats.get('disk_usage_mb', 0)
                    
                    # アクティブ接続数（推定）
                    active_connections += stats.get('active_processes', 0)
            
            # ヒット率計算
            hit_ratio = total_hits / total_requests if total_requests > 0 else 0.0
            
            # 平均レスポンス時間
            avg_response_time = sum(total_response_times) / len(total_response_times) if total_response_times else 0.0
            
            # システムメモリ使用量も追加
            process = psutil.Process(os.getpid())
            system_memory_mb = process.memory_info().rss / 1024 / 1024
            
            # メトリクス作成
            metrics = CacheMetrics(
                timestamp=current_time,
                hit_ratio=hit_ratio,
                response_time_ms=avg_response_time * 1000,  # ミリ秒に変換
                memory_usage_mb=memory_usage + system_memory_mb,
                disk_usage_mb=disk_usage,
                active_connections=active_connections,
                error_count=total_errors,
                total_requests=total_requests
            )
            
            # 履歴に追加
            self.metrics_history.append(metrics)
            
            logger.debug(f"メトリクス収集完了: ヒット率={hit_ratio:.2%}, "
                        f"レスポンス={avg_response_time*1000:.1f}ms, "
                        f"メモリ={memory_usage:.1f}MB")
        
        except Exception as e:
            logger.error(f"メトリクス収集エラー: {e}")
    
    async def _check_alerts(self):
        """アラートチェック"""
        if not self.metrics_history:
            return
        
        current_metrics = self.metrics_history[-1]
        alerts = []
        
        # ヒット率チェック
        if current_metrics.hit_ratio < self.alert_config.hit_ratio_threshold:
            alerts.append({
                "type": "hit_ratio",
                "severity": "warning",
                "message": f"キャッシュヒット率が低下: {current_metrics.hit_ratio:.2%} (閾値: {self.alert_config.hit_ratio_threshold:.2%})",
                "timestamp": current_metrics.timestamp,
                "value": current_metrics.hit_ratio
            })
        
        # レスポンス時間チェック
        if current_metrics.response_time_ms > self.alert_config.response_time_threshold_ms:
            alerts.append({
                "type": "response_time",
                "severity": "warning",
                "message": f"レスポンス時間が遅延: {current_metrics.response_time_ms:.1f}ms (閾値: {self.alert_config.response_time_threshold_ms:.1f}ms)",
                "timestamp": current_metrics.timestamp,
                "value": current_metrics.response_time_ms
            })
        
        # メモリ使用量チェック
        if current_metrics.memory_usage_mb > self.alert_config.memory_usage_threshold_mb:
            alerts.append({
                "type": "memory_usage",
                "severity": "critical",
                "message": f"メモリ使用量が上限近い: {current_metrics.memory_usage_mb:.1f}MB (閾値: {self.alert_config.memory_usage_threshold_mb:.1f}MB)",
                "timestamp": current_metrics.timestamp,
                "value": current_metrics.memory_usage_mb
            })
        
        # エラー率チェック
        if current_metrics.total_requests > 0:
            error_rate = current_metrics.error_count / current_metrics.total_requests
            if error_rate > self.alert_config.error_rate_threshold:
                alerts.append({
                    "type": "error_rate",
                    "severity": "critical",
                    "message": f"エラー率が上昇: {error_rate:.2%} (閾値: {self.alert_config.error_rate_threshold:.2%})",
                    "timestamp": current_metrics.timestamp,
                    "value": error_rate
                })
        
        # アラート処理
        for alert in alerts:
            await self._handle_alert(alert)
    
    async def _handle_alert(self, alert: Dict[str, Any]):
        """アラート処理"""
        # アラート履歴に追加
        self.alerts_history.append(alert)
        
        # ログ出力
        severity = alert['severity']
        message = alert['message']
        if severity == "critical":
            logger.error(f"🚨 CRITICAL ALERT: {message}")
        else:
            logger.warning(f"⚠️  WARNING ALERT: {message}")
        
        # 登録されたハンドラーに通知
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"アラートハンドラーエラー: {e}")
    
    async def _save_dashboard_data(self):
        """ダッシュボードデータ保存"""
        try:
            # 最新のメトリクス
            latest_metrics = None
            if self.metrics_history:
                latest_metrics = asdict(self.metrics_history[-1])
            
            # 過去1時間のメトリクス
            one_hour_ago = time.time() - 3600
            recent_metrics = [
                asdict(m) for m in self.metrics_history 
                if m.timestamp > one_hour_ago
            ]
            
            # 最新のアラート
            recent_alerts = list(self.alerts_history)[-10:]  # 最新10件
            
            dashboard_data = {
                "last_updated": time.time(),
                "latest_metrics": latest_metrics,
                "recent_metrics": recent_metrics,
                "recent_alerts": recent_alerts,
                "alert_config": asdict(self.alert_config),
                "monitoring_status": {
                    "is_active": self.is_monitoring,
                    "interval_seconds": self.monitoring_interval,
                    "cache_managers_count": len(self.cache_managers)
                }
            }
            
            # JSON形式で保存
            dashboard_file = self.dashboard_data_path / "dashboard.json"
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("ダッシュボードデータを保存しました")
        
        except Exception as e:
            logger.error(f"ダッシュボードデータ保存エラー: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """現在のステータス取得"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "メトリクスデータがありません"}
        
        latest = self.metrics_history[-1]
        
        # 直近5分間のトレンド計算
        five_minutes_ago = time.time() - 300
        recent_metrics = [m for m in self.metrics_history if m.timestamp > five_minutes_ago]
        
        trend_data = {}
        if len(recent_metrics) >= 2:
            first = recent_metrics[0]
            last = recent_metrics[-1]
            
            trend_data = {
                "hit_ratio_trend": last.hit_ratio - first.hit_ratio,
                "response_time_trend": last.response_time_ms - first.response_time_ms,
                "memory_usage_trend": last.memory_usage_mb - first.memory_usage_mb
            }
        
        return {
            "status": "active" if self.is_monitoring else "inactive",
            "latest_metrics": asdict(latest),
            "trend_data": trend_data,
            "alert_count": len([a for a in self.alerts_history if a['timestamp'] > time.time() - 3600]),
            "uptime_seconds": time.time() - latest.timestamp if self.metrics_history else 0
        }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンス概要取得"""
        cutoff_time = time.time() - (hours * 3600)
        period_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not period_metrics:
            return {"status": "no_data", "period_hours": hours}
        
        # 統計計算
        hit_ratios = [m.hit_ratio for m in period_metrics]
        response_times = [m.response_time_ms for m in period_metrics]
        memory_usage = [m.memory_usage_mb for m in period_metrics]
        
        summary = {
            "period_hours": hours,
            "data_points": len(period_metrics),
            "hit_ratio": {
                "avg": sum(hit_ratios) / len(hit_ratios),
                "min": min(hit_ratios),
                "max": max(hit_ratios)
            },
            "response_time_ms": {
                "avg": sum(response_times) / len(response_times),
                "min": min(response_times),
                "max": max(response_times)
            },
            "memory_usage_mb": {
                "avg": sum(memory_usage) / len(memory_usage),
                "min": min(memory_usage),
                "max": max(memory_usage)
            },
            "total_requests": sum(m.total_requests for m in period_metrics),
            "total_errors": sum(m.error_count for m in period_metrics)
        }
        
        return summary

# アラートハンドラー例
async def slack_alert_handler(alert: Dict[str, Any]):
    """Slack通知ハンドラー例（実装は環境に応じて）"""
    # 実際の実装では、SlackのWebhook URLを使用
    logger.info(f"📱 Slack通知: {alert['message']}")

def email_alert_handler(alert: Dict[str, Any]):
    """メール通知ハンドラー例（実装は環境に応じて）"""
    # 実際の実装では、SMTPサーバーを使用
    logger.info(f"📧 メール通知: {alert['message']}")

# ダッシュボード HTML生成
def generate_dashboard_html(dashboard_data: Dict[str, Any]) -> str:
    """ダッシュボード用HTML生成"""
    html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIキャッシュシステム監視ダッシュボード</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            margin-bottom: 10px;
        }
        .alert {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        }
        .alert.critical {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ AIキャッシュシステム監視ダッシュボード</h1>
            <p>最終更新: {last_updated}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">キャッシュヒット率</div>
                <div class="metric-value {hit_ratio_status}">{hit_ratio}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">平均レスポンス時間</div>
                <div class="metric-value {response_time_status}">{response_time}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">メモリ使用量</div>
                <div class="metric-value {memory_status}">{memory_usage}MB</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">総リクエスト数</div>
                <div class="metric-value">{total_requests}</div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h2>🚨 最新アラート</h2>
            {alerts_html}
        </div>
    </div>
    
    <script>
        // 30秒ごとに自動更新
        setTimeout(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
    """
    
    # データ抽出とフォーマット
    latest = dashboard_data.get('latest_metrics', {})
    alerts = dashboard_data.get('recent_alerts', [])
    
    # ステータス判定
    hit_ratio = latest.get('hit_ratio', 0)
    response_time = latest.get('response_time_ms', 0)
    memory_usage = latest.get('memory_usage_mb', 0)
    
    hit_ratio_status = 'status-good' if hit_ratio > 0.7 else 'status-warning' if hit_ratio > 0.5 else 'status-critical'
    response_time_status = 'status-good' if response_time < 500 else 'status-warning' if response_time < 1000 else 'status-critical'
    memory_status = 'status-good' if memory_usage < 300 else 'status-warning' if memory_usage < 500 else 'status-critical'
    
    # アラートHTML生成
    alerts_html = ""
    if alerts:
        for alert in alerts[-5:]:  # 最新5件
            alert_class = "critical" if alert['severity'] == 'critical' else ""
            alert_time = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
            alerts_html += f'<div class="alert {alert_class}">[{alert_time}] {alert["message"]}</div>'
    else:
        alerts_html = '<div class="alert">アラートはありません</div>'
    
    # HTML生成
    return html_template.format(
        last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        hit_ratio=f"{hit_ratio:.1%}",
        hit_ratio_status=hit_ratio_status,
        response_time=f"{response_time:.1f}",
        response_time_status=response_time_status,
        memory_usage=f"{memory_usage:.1f}",
        memory_status=memory_status,
        total_requests=latest.get('total_requests', 0),
        alerts_html=alerts_html
    )

# 使用例
async def setup_monitoring_dashboard(cache_managers: List[Any]) -> CacheDashboard:
    """監視ダッシュボードセットアップ"""
    # アラート設定
    alert_config = AlertConfig(
        hit_ratio_threshold=0.75,  # 75%未満でアラート
        response_time_threshold_ms=800.0,  # 800ms以上でアラート
        memory_usage_threshold_mb=400.0,  # 400MB以上でアラート
        error_rate_threshold=0.03  # 3%以上でアラート
    )
    
    # ダッシュボード作成
    dashboard = CacheDashboard(
        cache_manager_refs=cache_managers,
        alert_config=alert_config
    )
    
    # アラートハンドラー登録
    dashboard.add_alert_handler(slack_alert_handler)
    dashboard.add_alert_handler(email_alert_handler)
    
    # 監視開始
    await dashboard.start_monitoring()
    
    logger.info("監視ダッシュボードのセットアップが完了しました")
    return dashboard
