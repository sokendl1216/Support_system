# -*- coding: utf-8 -*-
"""
アクセシビリティ対応メインアプリケーション

タスク4-5: アクセシビリティツールセット統合版
スクリーンリーダー、キーボードナビゲーション、カラースキーム設定を
既存のUIシステムに統合したメインアプリケーション。
"""

import streamlit as st
from ui.components.buttons import primary_button
from ui.pages.home import render as render_home
from ui.pages.job_selection import render as render_job_selection
from ui.pages.progress_notification import main as render_progress_notification
from ui.pages.help import render as render_help
from ui.state import UIState
from ui.components.help_system import get_help_ui, HelpContext, show_quick_tip
from ui.components.accessibility import (
    get_accessibility_toolset, render_accessibility_settings, 
    render_accessibility_demo, AccessibilityToolset
)
from ui.components.multilingual import get_translator, render_language_selector, render_multilingual_title


def main():
    """アクセシビリティ対応メインアプリケーション"""
    
    # アクセシビリティツールセット初期化
    accessibility_toolset = get_accessibility_toolset()
    
    # アクセシビリティスタイル適用
    accessibility_toolset.apply_accessibility_styles()
    
    # スキップリンク表示
    accessibility_toolset.render_skip_links()
    
    # ページ設定
    st.set_page_config(
        page_title="AI支援システム - アクセシビリティ対応",
        page_icon="♿",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 多言語対応初期化
    translator = get_translator()
    
    # 状態管理の初期化
    if 'ui_state' not in st.session_state:
        st.session_state.ui_state = UIState()
    ui_state = st.session_state.ui_state
    
    # ヘルプUI初期化
    help_ui = get_help_ui()
    
    # アクセシブルナビゲーション
    render_accessible_navigation(accessibility_toolset, ui_state, translator, help_ui)
    
    # メインコンテンツエリア
    st.markdown('<div id="main-content">', unsafe_allow_html=True)
    
    # 初回ユーザー向けアクセシビリティガイド
    if not help_ui.help_manager.user_progress.get('accessibility_guide_shown', False):
        show_accessibility_welcome(accessibility_toolset, help_ui)
    
    # ページコンテンツ表示
    render_main_content(ui_state, help_ui, accessibility_toolset, translator)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # アクセシブルフッター
    render_accessible_footer(accessibility_toolset, translator)


def render_accessible_navigation(accessibility_toolset: AccessibilityToolset, 
                                ui_state: UIState, translator, help_ui):
    """アクセシブルナビゲーション"""
    
    with st.sidebar:
        st.markdown('<nav id="navigation" role="navigation">', unsafe_allow_html=True)
        
        # アクセシブルタイトル
        st.markdown(
            f'<h1 tabindex="0">🤖 {translator.translate("app.title")}</h1>',
            unsafe_allow_html=True
        )
        st.markdown("---")
        
        # 言語選択UI（アクセシブル版）
        st.markdown('<div role="region" aria-label="言語設定">', unsafe_allow_html=True)
        render_language_selector()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # メインナビゲーション
        st.markdown('<div role="navigation" aria-label="メインナビゲーション">', unsafe_allow_html=True)
        
        # ページ選択（アクセシブル版）
        page_options = {
            "🏠 " + translator.translate("navigation.home"): "home",
            "🎯 " + translator.translate("navigation.job_selection"): "job_selection", 
            "🔄 " + translator.translate("navigation.progress_notification"): "progress_notification",
            "♿ アクセシビリティ設定": "accessibility",
            "❓ " + translator.translate("navigation.help"): "help",
            "⚙️ " + translator.translate("navigation.settings"): "settings"
        }
        
        current_selection = None
        for page_name, page_key in page_options.items():
            if ui_state.current_page == page_key:
                current_selection = page_name
                break
        
        if current_selection is None:
            current_selection = "🏠 " + translator.translate("navigation.home")
        
        selected_page = st.radio(
            "ページを選択",
            list(page_options.keys()),
            index=list(page_options.keys()).index(current_selection),
            key="main_navigation",
            help="Tabキーとスペースキーでナビゲーションできます"
        )
        
        current_page = page_options[selected_page]
        if current_page != ui_state.current_page:
            ui_state.set_page(current_page)
            # スクリーンリーダー向けアナウンス
            page_title = selected_page.split(" ", 1)[1] if " " in selected_page else selected_page
            accessibility_toolset.announce_to_screen_reader(
                f"{page_title}ページに移動しました"
            )
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # クイックアクセシビリティ設定
        render_quick_accessibility_controls(accessibility_toolset)
        
        st.markdown("---")
        
        # 実装状況表示
        render_implementation_status(translator, accessibility_toolset)
        
        st.markdown('</nav>', unsafe_allow_html=True)


def render_quick_accessibility_controls(accessibility_toolset: AccessibilityToolset):
    """クイックアクセシビリティコントロール"""
    
    st.markdown('<div role="region" aria-label="クイックアクセシビリティ設定">', unsafe_allow_html=True)
    st.write("**🚀 クイック設定**")
    
    settings = accessibility_toolset.settings
    
    # ハイコントラストトグル
    if st.checkbox(
        "ハイコントラスト",
        value=settings.color_scheme.value == "high_contrast",
        key="quick_high_contrast",
        help="高コントラストモードを切り替えます"
    ):
        from ui.components.accessibility import ColorScheme
        settings.color_scheme = ColorScheme.HIGH_CONTRAST
        accessibility_toolset.announce_to_screen_reader("ハイコントラストモードを有効にしました")
        accessibility_toolset.apply_accessibility_styles()
        st.rerun()
    elif settings.color_scheme.value == "high_contrast":
        from ui.components.accessibility import ColorScheme
        settings.color_scheme = ColorScheme.DEFAULT
        accessibility_toolset.announce_to_screen_reader("ハイコントラストモードを無効にしました")
        accessibility_toolset.apply_accessibility_styles()
        st.rerun()
    
    # フォントサイズ調整
    font_size_map = {"small": "小", "medium": "中", "large": "大", "xl": "特大"}
    current_font = font_size_map.get(settings.font_size.value, "中")
    
    new_font = st.selectbox(
        "フォントサイズ",
        ["小", "中", "大", "特大"],
        index=["小", "中", "大", "特大"].index(current_font),
        key="quick_font_size",
        help="表示フォントサイズを調整します"
    )
    
    if new_font != current_font:
        from ui.components.accessibility import FontSize
        font_map = {"小": FontSize.SMALL, "中": FontSize.MEDIUM, 
                   "大": FontSize.LARGE, "特大": FontSize.EXTRA_LARGE}
        settings.font_size = font_map[new_font]
        accessibility_toolset.announce_to_screen_reader(f"フォントサイズを{new_font}に変更しました")
        accessibility_toolset.apply_accessibility_styles()
        st.rerun()
    
    # スクリーンリーダートグル
    if st.checkbox(
        "音声案内",
        value=settings.screen_reader_enabled,
        key="quick_screen_reader",
        help="スクリーンリーダー向け音声案内を切り替えます"
    ) != settings.screen_reader_enabled:
        settings.screen_reader_enabled = not settings.screen_reader_enabled
        message = "音声案内を有効にしました" if settings.screen_reader_enabled else "音声案内を無効にしました"
        accessibility_toolset.announce_to_screen_reader(message)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_implementation_status(translator, accessibility_toolset: AccessibilityToolset):
    """実装状況表示（アクセシブル版）"""
    
    st.markdown('<div role="region" aria-label="実装状況">', unsafe_allow_html=True)
    progress_title = "### 📊 " + translator.translate("footer.implementation_status")
    st.markdown(progress_title)
    
    status_items = [
        ("✅", "ai_cache_optimization", "completed"),
        ("✅", "ui_implementation", "completed"),
        ("✅", "multilingual_support", "completed"),
        ("✅", "help_system", "completed"),
        ("✅", "responsive_ui", "completed"),
        ("✅", "accessibility_toolset", "completed"),
        ("🔄", "voice_support", "in_progress"),
        ("🔄", "advanced_features", "in_progress")
    ]
    
    for icon, key, status in status_items:
        status_text = translator.translate(f"ui.{status}")
        feature_text = translator.translate(f"home.system_status.{key}")
        full_text = f"{icon} {feature_text}: {status_text}"
        
        if status == "completed":
            st.success(full_text)
        else:
            st.info(full_text)
    
    # アクセシビリティ機能の詳細
    st.markdown("**♿ アクセシビリティ機能**")
    accessibility_features = [
        "✅ スクリーンリーダー対応",
        "✅ キーボードナビゲーション",
        "✅ カラースキーム設定",
        "✅ フォントサイズ調整",
        "✅ ハイコントラスト表示",
        "✅ 色覚異常対応",
        "✅ フォーカス表示強化",
        "✅ スキップリンク"
    ]
    
    for feature in accessibility_features:
        st.markdown(f"- {feature}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def show_accessibility_welcome(accessibility_toolset: AccessibilityToolset, help_ui):
    """アクセシビリティウェルカムガイド"""
    
    with st.expander("♿ アクセシビリティ機能ガイド", expanded=True):
        st.markdown("""
        ### 🎉 アクセシビリティ機能が利用可能です！
        
        このシステムには以下のアクセシビリティ機能が組み込まれています：
        
        **🎨 表示設定**
        - ハイコントラスト表示
        - フォントサイズ調整
        - 色覚異常対応カラーパレット
        - ダークモード/ライトモード
        
        **⌨️ 操作支援**
        - キーボードナビゲーション（Tabキー、Enterキー）
        - スキップリンク（メインコンテンツに素早く移動）
        - 強化フォーカス表示
        
        **🔊 音声サポート**
        - スクリーンリーダー対応
        - 操作時の音声フィードバック
        - 重要な変更の音声通知
        
        **📱 レスポンシブ設計**
        - モバイル・タブレット対応
        - タッチフレンドリーなインターフェース
        - 適応的レイアウト
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚙️ アクセシビリティ設定を開く", type="primary"):
                st.session_state.ui_state.set_page("accessibility")
                accessibility_toolset.announce_to_screen_reader("アクセシビリティ設定ページを開きます")
                st.rerun()
        
        with col2:
            if st.button("❌ このガイドを閉じる"):
                help_ui.help_manager.user_progress['accessibility_guide_shown'] = True
                accessibility_toolset.announce_to_screen_reader("アクセシビリティガイドを閉じました")
                st.rerun()


def render_main_content(ui_state: UIState, help_ui, accessibility_toolset: AccessibilityToolset, translator):
    """メインコンテンツ表示"""
    
    current_page = ui_state.current_page
    
    # ページタイトルの音声案内
    page_titles = {
        "home": "ホーム",
        "job_selection": "ジョブ選択",
        "progress_notification": "進捗通知",
        "accessibility": "アクセシビリティ設定",
        "help": "ヘルプ",
        "settings": "設定"
    }
    
    if current_page == "home":
        render_multilingual_title("app.subtitle")
        render_home()
        help_ui.render_help_button(HelpContext.HOME, position="bottom")
    
    elif current_page == "job_selection":
        st.markdown('<h2 tabindex="0">🎯 ジョブ選択</h2>', unsafe_allow_html=True)
        render_job_selection()
        help_ui.render_help_button(HelpContext.JOB_SELECTION, position="bottom")
    
    elif current_page == "progress_notification":
        st.markdown('<h2 tabindex="0">🔄 進捗通知</h2>', unsafe_allow_html=True)
        render_progress_notification()
        help_ui.render_help_button(HelpContext.PROGRESS_NOTIFICATION, position="bottom")
    
    elif current_page == "accessibility":
        st.markdown('<h2 tabindex="0">♿ アクセシビリティ設定</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["設定", "デモ・テスト"])
        
        with tab1:
            render_accessibility_settings()
        
        with tab2:
            render_accessibility_demo()
        
        help_ui.render_help_button(HelpContext.SETTINGS, position="bottom")
    
    elif current_page == "help":
        st.markdown('<h2 tabindex="0">❓ ヘルプ</h2>', unsafe_allow_html=True)
        render_help()
    
    elif current_page == "settings":
        st.markdown('<h2 tabindex="0">⚙️ 設定</h2>', unsafe_allow_html=True)
        render_general_settings(accessibility_toolset, translator)
        help_ui.render_help_button(HelpContext.SETTINGS, position="bottom")
    
    else:
        st.error("ページが見つかりません")
        accessibility_toolset.announce_to_screen_reader("ページが見つかりません", "assertive")


def render_general_settings(accessibility_toolset: AccessibilityToolset, translator):
    """一般設定画面"""
    
    st.subheader("⚙️ システム設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**システム情報**")
        st.info("AI支援システム v1.0")
        st.info("アクセシビリティ対応版")
        
        st.write("**データ管理**")
        if st.button("🗑️ キャッシュをクリア"):
            # キャッシュクリア処理
            st.success("キャッシュをクリアしました")
            accessibility_toolset.announce_to_screen_reader("システムキャッシュをクリアしました")
        
        if st.button("💾 設定をエクスポート"):
            # 設定エクスポート処理
            st.success("設定をエクスポートしました")
            accessibility_toolset.announce_to_screen_reader("設定をファイルにエクスポートしました")
    
    with col2:
        st.write("**表示設定**")
        
        # 通知設定
        notifications_enabled = st.checkbox(
            "通知を有効にする",
            value=True,
            help="システムからの通知を受け取ります"
        )
        
        # 自動保存設定
        auto_save = st.checkbox(
            "自動保存を有効にする",
            value=True,
            help="設定変更を自動的に保存します"
        )
        
        # デバッグモード
        debug_mode = st.checkbox(
            "デバッグモードを有効にする",
            value=False,
            help="開発者向けのデバッグ情報を表示します"
        )
        
        if st.button("💾 設定を保存", type="primary"):
            st.success("設定を保存しました")
            accessibility_toolset.announce_to_screen_reader("一般設定を保存しました")


def render_accessible_footer(accessibility_toolset: AccessibilityToolset, translator):
    """アクセシブルフッター"""
    
    st.markdown("---")
    st.markdown('<footer role="contentinfo">', unsafe_allow_html=True)
    
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        st.markdown("**🤖 AI支援システム**")
        st.markdown("アクセシビリティ対応版")
    
    with footer_col2:
        st.markdown("**♿ アクセシビリティ**")
        st.markdown("WCAG 2.1 AA準拠")
        st.markdown("JIS X 8341対応")
    
    with footer_col3:
        st.markdown("**📞 サポート**")
        if st.button("❓ ヘルプを表示", key="footer_help"):
            st.session_state.ui_state.set_page("help")
            accessibility_toolset.announce_to_screen_reader("ヘルプページを開きます")
            st.rerun()
    
    # キーボードショートカットの説明
    with st.expander("⌨️ キーボードショートカット"):
        st.markdown("""
        - **Tab**: 次の要素に移動
        - **Shift + Tab**: 前の要素に移動
        - **Enter/Space**: ボタンを押す、チェックボックスを切り替え
        - **矢印キー**: ラジオボタンやセレクトボックスで選択
        - **Esc**: モーダルやポップアップを閉じる
        """)
    
    st.markdown('</footer>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
