"""
AIプロセス監視システム - 24時間統計更新用メソッド
"""

def _update_24h_stats(self) -> None:
    """24時間統計情報を更新"""
    try:
        # 現在時刻からの24時間前のタイムスタンプ
        now = datetime.now().timestamp()
        day_ago = now - (24 * 60 * 60)  # 24時間 = 86400秒
        
        # 直近24時間のプロセス数カウント
        recent_timestamps = [ts for ts in self.performance_history["timestamps"] if ts > day_ago]
        self.stats["last_24h_processes"] = len(recent_timestamps)
        
        # 直近24時間の履歴から成功率を計算
        if recent_timestamps:
            recent_processes = []
            
            # 24時間以内のプロセスを履歴から取得
            for process in self.process_history:
                if process.end_time and process.end_time.timestamp() > day_ago:
                    recent_processes.append(process)
            
            # 成功と失敗をカウント
            success_count = len([p for p in recent_processes if p.status == ProcessStatus.COMPLETED])
            failed_count = len([p for p in recent_processes if p.status == ProcessStatus.FAILED])
            
            # 成功率を計算
            if success_count + failed_count > 0:
                self.stats["last_24h_success_rate"] = success_count / (success_count + failed_count)
            else:
                self.stats["last_24h_success_rate"] = 0.0
    
    except Exception as e:
        logger.error(f"24時間統計の更新エラー: {e}")
