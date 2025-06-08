# -*- coding: utf-8 -*-
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
from ui.state import UIState
from ui.i18n import get_translator, get_language_manager

def main():
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
        sidebar_title = "🤖 " + translator.translate("app.title")
        st.title(sidebar_title)
        st.markdown("---")
        
        # 言語選択UI
        render_language_selector()
        
        # ページ選択
        home_text = "🏠 " + translator.translate("navigation.home")
        job_text = "🎯 " + translator.translate("navigation.job_selection")
        progress_text = "🔄 " + translator.translate("navigation.progress_notification")
        settings_text = "⚙️ " + translator.translate("navigation.settings")
        
        page_options = {
            home_text: "home",
            job_text: "job_selection", 
            progress_text: "progress_notification",
            settings_text: "settings"
        }
        
        nav_label = translator.translate("navigation.home")
        selected_page = st.radio(
            nav_label,
            list(page_options.keys()),
            key="main_navigation"
        )
        
        current_page = page_options[selected_page]
        ui_state.set_page(current_page)
        
        st.markdown("---")
        
        # 実装状況表示
        progress_title = "### 📊 " + translator.translate("footer.implementation_status")
        st.markdown(progress_title)
        
        cache_text = "✅ " + translator.translate("home.system_status.ai_cache_optimization") + ": " + translator.translate("ui.completed")
        st.success(cache_text)
        
        ui_text = "🔄 " + translator.translate("home.system_status.ui_implementation") + ": " + translator.translate("ui.in_progress")
        st.info(ui_text)
        
        # 個別項目
        home_status = "- ✅ " + translator.translate("navigation.home")
        st.markdown(home_status)
        
        job_status = "- ✅ " + translator.translate("navigation.job_selection")
        st.markdown(job_status)
        
        progress_status = "- ✅ **" + translator.translate("navigation.progress_notification") + "**"
        st.markdown(progress_status)
        
        multilingual_status = "- ✅ **" + translator.translate("footer.task_current") + "**"
        st.markdown(multilingual_status)
        
        voice_status = "- 🔄 " + translator.translate("home.features.voice_support")
        st.markdown(voice_status)
        
        accessibility_status = "- 🔄 " + translator.translate("home.features.accessibility")
        st.markdown(accessibility_status)
    
    # メインコンテンツ
    if current_page == "home":
        render_multilingual_title("app.subtitle")
        render_home()
        
        # 最新実装のハイライト
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            feature_title = "### 🎉 " + translator.translate("home.latest_updates.new_feature")
            st.success(feature_title)
            
            task_message = "**" + translator.translate("footer.task_current") + "**"
            st.markdown(task_message)
            
            if render_multilingual_button("home.latest_updates.try_progress_notification"):
                ui_state.set_page("progress_notification")
                st.rerun()
        
        with col2:
            status_title = "### 📈 " + translator.translate("home.system_status.title")
            st.info(status_title)
            
            cache_progress = "- " + translator.translate("home.system_status.ai_cache_optimization") + ": **100% " + translator.translate("ui.completed") + "**"
            st.markdown(cache_progress)
            
            ui_progress = "- " + translator.translate("home.system_status.ui_implementation") + ": **75% " + translator.translate("ui.completed") + "**"
            st.markdown(ui_progress)
            
            overall_progress = "- " + translator.translate("home.system_status.overall_progress") + ": **80% " + translator.translate("ui.completed") + "**"
            st.markdown(overall_progress)
    
    elif current_page == "job_selection":
        render_multilingual_title("job_selection.title")
        render_job_selection()
    
    elif current_page == "progress_notification":
        render_progress_notification()
    
    elif current_page == "settings":
        render_multilingual_title("settings.title")
        render_multilingual_text("settings.language_settings")
        
        if render_multilingual_button("buttons.back_to_home", key="back_to_home"):
            ui_state.set_page("home")
            st.rerun()
    
    # フッター
    st.markdown("---")
    footer_text = (
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>" +
        translator.translate("footer.copyright") + " | " +
        translator.translate("footer.task_current") + " ✅" +
        "</div>"
    )
    st.markdown(footer_text, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
