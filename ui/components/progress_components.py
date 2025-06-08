"""
進行状態通知システム - UIコンポーネント

視覚的な進捗表示とアクセシビリティ対応のUIコンポーネントを提供します。
"""

import streamlit as st
import time
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from .progress_notification import (
    ProgressNotificationSystem, 
    ProgressInfo, 
    Notification, 
    ProgressStatus, 
    NotificationType,
    get_progress_system
)

def render_progress_bar(progress_info: ProgressInfo, key_suffix: str = "") -> None:
    """
    プログレスバーコンポーネント
    
    WAI-ARIA準拠のアクセシブルなプログレスバーを表示
    """
    # プログレスバーのスタイル
    status_colors = {
        ProgressStatus.PENDING: "#ffc107",  # 黄色
        ProgressStatus.RUNNING: "#007bff",  # 青
        ProgressStatus.COMPLETED: "#28a745",  # 緑
        ProgressStatus.ERROR: "#dc3545",  # 赤
        ProgressStatus.CANCELLED: "#6c757d"  # グレー
    }
    
    color = status_colors.get(progress_info.status, "#007bff")
    
    # プログレスバーHTML（アクセシビリティ対応）
    progress_html = f"""
    <div style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong style="font-size: 1rem;">{progress_info.title}</strong>
            <span style="font-size: 0.9rem; color: #666;">{progress_info.progress:.1%}</span>
        </div>
        
        <div 
            role="progressbar" 
            aria-valuenow="{int(progress_info.progress * 100)}" 
            aria-valuemin="0" 
            aria-valuemax="100"
            aria-label="{progress_info.title}の進捗: {progress_info.progress:.1%}"
            style="
                width: 100%; 
                height: 20px; 
                background-color: #e9ecef; 
                border-radius: 10px; 
                overflow: hidden;
                margin-bottom: 0.5rem;
            "
        >
            <div style="
                width: {progress_info.progress * 100}%; 
                height: 100%; 
                background-color: {color};
                transition: width 0.3s ease;
                border-radius: 10px;
            "></div>
        </div>
        
        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">
            ステップ {progress_info.current_step_number}/{progress_info.total_steps}: {progress_info.current_step}
        </div>
    """
    
    # 残り時間表示
    if (progress_info.estimated_remaining_time and 
        progress_info.status == ProgressStatus.RUNNING and 
        progress_info.estimated_remaining_time > 0):
        
        remaining_minutes = int(progress_info.estimated_remaining_time / 60)
        remaining_seconds = int(progress_info.estimated_remaining_time % 60)
        
        if remaining_minutes > 0:
            time_text = f"残り時間: 約{remaining_minutes}分{remaining_seconds}秒"
        else:
            time_text = f"残り時間: 約{remaining_seconds}秒"
            
        progress_html += f"""
        <div style="font-size: 0.8rem; color: #999;">
            {time_text}
        </div>
        """
    
    progress_html += "</div>"
    
    # HTML表示
    st.markdown(progress_html, unsafe_allow_html=True)
    
    # ステータス別の追加情報
    if progress_info.status == ProgressStatus.ERROR:
        st.error(f"エラー: {progress_info.current_step}")
    elif progress_info.status == ProgressStatus.COMPLETED:
        st.success("✅ 処理が完了しました")
    elif progress_info.status == ProgressStatus.CANCELLED:
        st.warning("⚠️ 処理がキャンセルされました")

def render_notification_toast(notification: Notification, key_suffix: str = "") -> bool:
    """
    トースト通知コンポーネント
    
    Returns:
        bool: 通知が削除された場合True
    """
    # 通知タイプ別のスタイル
    type_styles = {
        NotificationType.INFO: {"color": "#007bff", "icon": "ℹ️", "bg": "#cce7ff"},
        NotificationType.SUCCESS: {"color": "#28a745", "icon": "✅", "bg": "#d4edda"},
        NotificationType.WARNING: {"color": "#ffc107", "icon": "⚠️", "bg": "#fff3cd"},
        NotificationType.ERROR: {"color": "#dc3545", "icon": "❌", "bg": "#f8d7da"},
        NotificationType.PROGRESS: {"color": "#17a2b8", "icon": "🔄", "bg": "#d1ecf1"}
    }
    
    style = type_styles.get(notification.type, type_styles[NotificationType.INFO])
    
    # 経過時間計算
    elapsed = time.time() - notification.timestamp
    time_ago = _format_time_ago(elapsed)
    
    # 通知HTML
    notification_html = f"""
    <div style="
        background-color: {style['bg']};
        border-left: 4px solid {style['color']};
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 4px 4px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: relative;
    " role="alert" aria-live="polite">
        <div style="display: flex; align-items: flex-start; justify-content: space-between;">
            <div style="flex-grow: 1;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">{style['icon']}</span>
                    <strong style="color: {style['color']};">{notification.title}</strong>
                    <span style="font-size: 0.8rem; color: #666; margin-left: auto;">{time_ago}</span>
                </div>
                <div style="color: #333;">
                    {notification.message}
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(notification_html, unsafe_allow_html=True)
    
    # 自動削除の処理
    dismissed = False
    if notification.auto_dismiss and elapsed > notification.dismiss_after:
        dismissed = True
    
    # 手動削除ボタン（エラー通知など）
    if not notification.auto_dismiss:
        if st.button("✕ 閉じる", key=f"dismiss_{notification.id}_{key_suffix}"):
            dismissed = True
    
    return dismissed

def render_active_processes_panel(key_suffix: str = "") -> None:
    """アクティブプロセスパネル"""
    progress_system = get_progress_system()
    active_processes = progress_system.get_active_processes()
    
    if not active_processes:
        return
    
    st.subheader("🔄 実行中のタスク")
    
    for i, process_info in enumerate(active_processes):
        with st.container():
            render_progress_bar(process_info, f"{key_suffix}_{i}")
            
            # キャンセルボタン（実行中のプロセスのみ）
            if process_info.status == ProgressStatus.RUNNING:
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("キャンセル", key=f"cancel_{process_info.process_id}_{key_suffix}"):
                        progress_system.cancel_process(process_info.process_id)
                        st.rerun()

def render_notifications_panel(max_notifications: int = 5, key_suffix: str = "") -> None:
    """通知パネル"""
    progress_system = get_progress_system()
    recent_notifications = progress_system.get_recent_notifications(max_notifications)
    
    if not recent_notifications:
        return
    
    st.subheader("🔔 通知")
    
    # 通知のクリーンアップ処理
    to_dismiss = []
    
    for i, notification in enumerate(reversed(recent_notifications)):
        dismissed = render_notification_toast(notification, f"{key_suffix}_{i}")
        if dismissed:
            to_dismiss.append(notification.id)
    
    # 削除処理
    for notification_id in to_dismiss:
        progress_system.dismiss_notification(notification_id)
    
    # 古い通知のクリーンアップ
    progress_system.cleanup_old_notifications()
    
    if to_dismiss:
        st.rerun()

def render_progress_sidebar():
    """サイドバー用進捗表示"""
    with st.sidebar:
        st.markdown("---")
        render_active_processes_panel("sidebar")
        render_notifications_panel(3, "sidebar")

def create_progress_container(container_title: str = "進捗状況") -> None:
    """メイン画面用進捗コンテナ"""
    with st.container():
        st.markdown(f"### {container_title}")
        
        # タブで分ける
        tab1, tab2 = st.tabs(["🔄 実行中", "🔔 通知"])
        
        with tab1:
            render_active_processes_panel("main")
        
        with tab2:
            render_notifications_panel(10, "main")

def _format_time_ago(seconds: float) -> str:
    """経過時間を人間が読みやすい形式に変換"""
    if seconds < 60:
        return f"{int(seconds)}秒前"
    elif seconds < 3600:
        return f"{int(seconds/60)}分前"
    elif seconds < 86400:
        return f"{int(seconds/3600)}時間前"
    else:
        return f"{int(seconds/86400)}日前"

# デモ用関数
def demo_progress_system():
    """進行状態通知システムのデモ"""
    st.title("進行状態通知システム デモ")
    
    progress_system = get_progress_system()
    
    # コントロールパネル
    st.subheader("コントロールパネル")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("サンプルタスク開始"):
            process_id = f"demo_{int(time.time())}"
            progress_system.start_process(
                process_id=process_id,
                title="サンプル処理",
                description="デモ用の処理です",
                total_steps=5
            )
            st.session_state[f"demo_process_{process_id}"] = 0
            st.rerun()
    
    with col2:
        if st.button("テスト通知"):
            progress_system._add_notification(
                type=NotificationType.INFO,
                title="テスト",
                message="これはテスト通知です"
            )
            st.rerun()
    
    with col3:
        if st.button("すべてクリア"):
            progress_system.active_processes.clear()
            progress_system.notifications.clear()
            st.rerun()
    
    # 進捗表示
    create_progress_container()
    
    # サイドバー
    render_progress_sidebar()
    
    # デモプロセスの進行（シミュレーション）
    for key in list(st.session_state.keys()):
        if key.startswith("demo_process_"):
            process_id = key.replace("demo_process_", "")
            step = st.session_state[key]
            
            if step < 5:
                progress = (step + 1) / 5
                progress_system.update_progress(
                    process_id=process_id,
                    progress=progress,
                    current_step=f"ステップ {step + 1}を実行中...",
                    step_number=step + 1
                )
                
                st.session_state[key] += 1
                
                if step + 1 >= 5:
                    progress_system.complete_process(
                        process_id=process_id,
                        final_message="デモ処理が完了しました"
                    )
                    del st.session_state[key]
                
                time.sleep(0.1)  # 少し遅延
                st.rerun()

if __name__ == "__main__":
    demo_progress_system()
