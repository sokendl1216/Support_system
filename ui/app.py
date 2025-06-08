# ui/app.py

import streamlit as st
from ui.components.buttons import primary_button
from ui.components.multilingual import (
    render_language_selector,
    render_multilingual_title,
    render_multilingual_text,
    render_multilingual_button
)
from ui.pages.home import render as render_home
from ui.pages.job_selection import render as render_job_selection
from ui.pages.progress_notification import main as render_progress_notification
from ui.pages.help import render as render_help
from ui.state import UIState
from ui.i18n import get_translator, get_language_manager
from ui.components.help_system import get_help_ui, HelpContext, show_quick_tip
# アクセシビリティ機能追加
from ui.components.accessibility import get_accessibility_toolset, render_accessibility_settings

def main():
    # アクセシビリティツールセット初期化
    accessibility_toolset = get_accessibility_toolset()
    accessibility_toolset.apply_accessibility_styles()
    accessibility_toolset.render_skip_links()
    
    # 言語マネージャー初期化
    lang_manager = get_language_manager()
    translator = get_translator()
    
    # 自動言語検出
    auto_lang = lang_manager.auto_detect_language()
    if auto_lang != lang_manager.get_current_language():
        lang_manager.set_language(auto_lang)
    
    st.set_page_config(
        page_title=translator.translate("app.title"), 
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
        st.title("🤖 " + translator.translate("app.title"))
        st.markdown("---")
        
        # 言語選択UI
        render_language_selector()
        
        # ページ選択
        page_options = {
            "🏠 " + translator.translate("navigation.home"): "home",
            "🎯 " + translator.translate("navigation.job_selection"): "job_selection", 
            "🔄 " + translator.translate("navigation.progress_notification"): "progress_notification",
            "♿ アクセシビリティ": "accessibility",
            "⚙️ " + translator.translate("navigation.settings"): "settings"
        }
        
        selected_page = st.radio(
            translator.translate("navigation.home"),
            list(page_options.keys()),
            key="main_navigation"
        )
        
        current_page = page_options[selected_page]
        ui_state.set_page(current_page)
        
        st.markdown("---")
        
        # クイックアクセシビリティ設定
        st.write("**🚀 クイック設定**")
        settings = accessibility_toolset.settings
        
        # ハイコントラストトグル
        if st.checkbox("ハイコントラスト", value=settings.color_scheme.value == "high_contrast", key="quick_hc"):
            from ui.components.accessibility import ColorScheme
            settings.color_scheme = ColorScheme.HIGH_CONTRAST if not (settings.color_scheme.value == "high_contrast") else ColorScheme.DEFAULT
            accessibility_toolset.apply_accessibility_styles()
            accessibility_toolset.announce_to_screen_reader("コントラスト設定を変更しました")
            st.rerun()
        
        # 音声案内トグル
        if st.checkbox("音声案内", value=settings.screen_reader_enabled, key="quick_sr") != settings.screen_reader_enabled:
            settings.screen_reader_enabled = not settings.screen_reader_enabled
            message = "音声案内を有効にしました" if settings.screen_reader_enabled else "音声案内を無効にしました"
            accessibility_toolset.announce_to_screen_reader(message)
        
        st.markdown("---")
        
        # 実装状況表示
        progress_title = "### 📊 " + translator.translate("footer.implementation_status")
        st.markdown(progress_title)
        cache_status = "✅ " + translator.translate("home.system_status.ai_cache_optimization") + ": " + translator.translate("ui.completed")
        st.success(cache_status)
        ui_status = "✅ " + translator.translate("home.system_status.ui_implementation") + ": " + translator.translate("ui.completed")
        st.success(ui_status)
        accessibility_status = "✅ アクセシビリティ: " + translator.translate("ui.completed")
        st.success(accessibility_status)
        st.markdown("- ✅ " + translator.translate("navigation.home"))
        st.markdown("- ✅ " + translator.translate("navigation.job_selection"))
        st.markdown("- ✅ **" + translator.translate("navigation.progress_notification") + "**")
        st.markdown("- ✅ **アクセシビリティツールセット**")
        st.markdown("- ✅ **" + translator.translate("footer.task_current") + "**")
        st.markdown("- 🔄 " + translator.translate("home.features.voice_support"))
    
    # メインコンテンツ
    if current_page == "home":
        render_multilingual_title("app.subtitle")
        render_home()
        
        # 最新実装のハイライト
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("### 🎉 " + translator.translate("home.latest_updates.new_feature"))
            st.markdown("**♿ アクセシビリティツールセット実装完了**")
            if st.button("♿ アクセシビリティ機能を試す", key="try_accessibility"):
                ui_state.set_page("accessibility")
                accessibility_toolset.announce_to_screen_reader("アクセシビリティ設定ページを開きます")
                st.rerun()
        
        with col2:
            st.info("### 📈 " + translator.translate("home.system_status.title"))
            st.markdown("- " + translator.translate("home.system_status.ai_cache_optimization") + ": **100% " + translator.translate("ui.completed") + "**")
            st.markdown("- " + translator.translate("home.system_status.ui_implementation") + ": **100% " + translator.translate("ui.completed") + "**")
            st.markdown("- **アクセシビリティ**: **100% " + translator.translate("ui.completed") + "**")
            st.markdown("- " + translator.translate("home.system_status.overall_progress") + ": **95% " + translator.translate("ui.completed") + "**")
    
    elif current_page == "job_selection":
        st.title("ジョブ選択")
        render_job_selection()
    
    elif current_page == "progress_notification":
        render_progress_notification()
    
    elif current_page == "accessibility":
        st.title("♿ アクセシビリティ設定")
        
        # アクセシビリティ初回ガイド
        if not st.session_state.get('accessibility_guide_shown', False):
            with st.expander("♿ アクセシビリティ機能について", expanded=True):
                st.markdown("""
                ### 🎉 アクセシビリティ機能が利用可能です！
                
                **🎨 表示設定**
                - ハイコントラスト表示、フォントサイズ調整
                - 色覚異常対応カラーパレット、ダークモード
                
                **⌨️ 操作支援**
                - キーボードナビゲーション、スキップリンク
                - 強化フォーカス表示
                
                **🔊 音声サポート**
                - スクリーンリーダー対応、音声フィードバック
                """)
                
                if st.button("このガイドを閉じる"):
                    st.session_state.accessibility_guide_shown = True
                    accessibility_toolset.announce_to_screen_reader("アクセシビリティガイドを閉じました")
                    st.rerun()
        
        # アクセシビリティ設定UI
        render_accessibility_settings()
    
    elif current_page == "settings":
        st.title("設定")
        st.write("設定画面（実装予定）")
        
        if primary_button("ホームに戻る", key="back_to_home"):
            ui_state.set_page("home")
            accessibility_toolset.announce_to_screen_reader("ホームページに戻ります")
            st.rerun()
    
    # フッター
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "多様なニーズを持つ方の仕事支援AIシステム | タスク4-5: アクセシビリティツールセット実装完了 ✅"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
