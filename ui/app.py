# ui/app.py

import streamlit as st
from ui.components.buttons import primary_button
from ui.pages.home import render as render_home
from ui.pages.job_selection import render as render_job_selection
from ui.pages.progress_notification import main as render_progress_notification
from ui.state import UIState

def main():
    st.set_page_config(
        page_title="仕事支援AIシステム", 
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 状態管理の初期化
    if 'ui_state' not in st.session_state:
        st.session_state.ui_state = UIState()
    
    ui_state = st.session_state.ui_state
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("🤖 仕事支援AI")
        st.markdown("---")
        
        # ページ選択
        page_options = {
            "🏠 ホーム": "home",
            "🎯 ジョブ選択": "job_selection", 
            "🔄 進行状態通知": "progress_notification",
            "⚙️ 設定": "settings"
        }
        
        selected_page = st.radio(
            "ページ選択",
            list(page_options.keys()),
            key="main_navigation"
        )
        
        current_page = page_options[selected_page]
        ui_state.set_page(current_page)
        
        st.markdown("---")
        
        # 実装状況表示
        st.markdown("### 📊 実装進捗")
        st.success("✅ フェーズ1-3（設計・基盤・AI）")
        st.info("🔄 フェーズ4（UI実装中）")
        st.markdown("- ✅ トップ画面")
        st.markdown("- ✅ ジョブ選択画面")
        st.markdown("- ✅ **進行状態通知システム**")
        st.markdown("- 🔄 音声入出力システム")
        st.markdown("- 🔄 アクセシビリティツール")
    
    # メインコンテンツ
    if current_page == "home":
        st.title("多様なニーズを持つ方の仕事支援AIシステム")
        render_home()
        
        # 最新実装のハイライト
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("### 🎉 新機能リリース")
            st.markdown("**タスク4-6: 進行状態通知システム**が完成しました！")
            if st.button("🔄 進行状態通知を試す"):
                ui_state.set_page("progress_notification")
                st.rerun()
        
        with col2:
            st.info("### 📈 システム状況")
            st.markdown("- AIキャッシュ最適化: **100%完了**")
            st.markdown("- UI実装進捗: **60%完了**")
            st.markdown("- 全体進捗: **75%完了**")
    
    elif current_page == "job_selection":
        st.title("ジョブ選択")
        render_job_selection()
    
    elif current_page == "progress_notification":
        render_progress_notification()
    
    elif current_page == "settings":
        st.title("設定")
        st.write("設定画面（実装予定）")
        
        if primary_button("ホームに戻る", key="back_to_home"):
            ui_state.set_page("home")
            st.rerun()
    
    # フッター
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "多様なニーズを持つ方の仕事支援AIシステム | タスク4-6: 進行状態通知システム実装完了 ✅"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
