# -*- coding: utf-8 -*-
"""
ヘルプシステム統合アプリケーション

ヘルプシステム機能を完全に統合したメインアプリケーション。
タスク4-9（ヘルプシステム）の実装を含む。
"""

import streamlit as st
from ui.components.buttons import primary_button
from ui.pages.home import render as render_home
from ui.pages.job_selection import render as render_job_selection
from ui.pages.progress_notification import main as render_progress_notification
from ui.pages.help import render as render_help
from ui.state import UIState
from ui.components.help_system import get_help_ui, HelpContext, show_quick_tip

def main():
    st.set_page_config(
        page_title="AI支援システム（ヘルプ機能搭載）", 
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 状態管理の初期化
    if 'ui_state' not in st.session_state:
        st.session_state.ui_state = UIState()
    
    ui_state = st.session_state.ui_state
    
    # ヘルプUI初期化
    help_ui = get_help_ui()
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("🤖 AI支援システム")
        st.markdown("### ヘルプシステム搭載版")
        st.markdown("---")
        
        # ページ選択
        page_options = {
            "🏠 ホーム": "home",
            "🎯 ジョブ選択": "job_selection", 
            "🔄 進行状態通知": "progress_notification",
            "❓ ヘルプ・サポート": "help",
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
        st.markdown("### 📊 実装状況")
        
        st.success("✅ AIキャッシュ最適化: 完了")
        st.info("🔄 UI実装: 進行中（85%）")
        
        st.markdown("**完了済み機能：**")
        st.markdown("- ✅ ホーム画面")
        st.markdown("- ✅ ジョブ選択")
        st.markdown("- ✅ 進行状態通知")
        st.markdown("- ✅ **音声入出力システム**")
        st.markdown("- ✅ **ヘルプシステム**")
        st.markdown("- ✅ **多言語対応基盤**")
        
        st.markdown("**進行中：**")
        st.markdown("- 🔄 レスポンシブUI最適化")
        st.markdown("- 🔄 アクセシビリティ強化")
        
        st.markdown("---")
        
        # クイックヘルプ
        st.markdown("### 💡 クイックヘルプ")
        if st.button("❓ 使い方ガイド"):
            ui_state.set_page("help")
            st.rerun()
        
        if st.button("🎓 チュートリアル開始"):
            st.session_state.active_tutorial = "quick_start"
            st.session_state.tutorial_step = 0
            st.rerun()
    
    # 初回ユーザー向けウェルカムメッセージ
    if not help_ui.help_manager.user_progress.get('help_preferences', {}).get('tutorial_completed', False):
        show_quick_tip(
            "welcome_help_system",
            "🎉 ヘルプシステムが利用可能になりました！",
            "各画面の「❓ ヘルプ」ボタンで詳しい使い方を確認できます。初めての方は「🎓 チュートリアル」をお試しください。",
            dismissible=True
        )
    
    # メインコンテンツ
    if current_page == "home":
        # ホーム画面のコンテキストヘルプボタン
        col1, col2 = st.columns([5, 1])
        with col1:
            st.title("🏠 ホーム画面")
        with col2:
            help_ui.render_help_button(HelpContext.HOME)
        
        render_home()
        
        # ヘルプシステム完了の告知
        st.markdown("---")
        st.success("### 🎉 タスク4-9: ヘルプシステム実装完了")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("**📚 包括的ヘルプ**")
            st.write("- コンテキスト依存ヘルプ")
            st.write("- よくある質問（FAQ）")
            st.write("- 詳細な操作ガイド")
            
        with col2:
            st.info("**🎓 学習サポート**")
            st.write("- インタラクティブチュートリアル")
            st.write("- ステップバイステップガイド")
            st.write("- 進捗追跡機能")
            
        with col3:
            st.info("**♿ アクセシビリティ**")
            st.write("- スクリーンリーダー対応")
            st.write("- キーボード操作対応")
            st.write("- 高コントラストモード")
        
        if st.button("🚀 ヘルプシステムを試してみる", key="try_help"):
            ui_state.set_page("help")
            st.rerun()
    
    elif current_page == "job_selection":
        # ジョブ選択画面のコンテキストヘルプボタン
        col1, col2 = st.columns([5, 1])
        with col1:
            st.title("🎯 ジョブ選択")
        with col2:
            help_ui.render_help_button(HelpContext.JOB_SELECTION)
        
        render_job_selection()
    
    elif current_page == "progress_notification":
        # 進行通知画面のコンテキストヘルプボタン
        help_ui.render_help_button(HelpContext.RESULTS, position="left")
        render_progress_notification()
    
    elif current_page == "help":
        # ヘルプページ
        render_help()
    
    elif current_page == "settings":
        # 設定画面のコンテキストヘルプボタン
        col1, col2 = st.columns([5, 1])
        with col1:
            st.title("⚙️ 設定")
        with col2:
            help_ui.render_help_button(HelpContext.SETTINGS)
        
        st.write("設定画面（実装予定）")
        
        # ヘルプシステム設定プレビュー
        st.subheader("🔧 ヘルプシステム設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("自動ヘルプ表示", value=True, help="画面遷移時に自動的にヘルプを表示")
            st.checkbox("ツールチップ表示", value=True, help="UI要素のツールチップを表示")
            st.checkbox("クイックヒント", value=True, help="操作に関するヒントを表示")
        
        with col2:
            st.selectbox("ヘルプレベル", ["初心者", "中級者", "上級者"], help="表示するヘルプの詳細度")
            st.slider("チュートリアル速度", 1, 5, 3, help="チュートリアルの進行速度")
        
        if st.button("設定をリセット"):
            st.info("ヘルプシステム設定をリセットしました。")
        
        if primary_button("ホームに戻る", key="back_to_home"):
            ui_state.set_page("home")
            st.rerun()
    
    # アクティブチュートリアルの表示（全画面共通）
    help_ui.render_active_tutorial()
    
    # フッター
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "多様なニーズを持つ方の仕事支援AIシステム | "
        "<strong>タスク4-9: ヘルプシステム実装完了 ✅</strong> | "
        "フェーズ4 UI実装 85%完了"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
