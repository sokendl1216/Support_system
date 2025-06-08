# -*- coding: utf-8 -*-
"""
多言語対応デモアプリケーション
Multilingual support demo application
"""

import streamlit as st
import sys
import os
from pathlib import Path

# パスの追加
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from ui.i18n import get_translator, get_language_manager
from ui.components.multilingual import (
    render_language_selector,
    render_multilingual_title,
    render_multilingual_text,
    render_multilingual_button,
    render_multilingual_selectbox,
    render_multilingual_alert,
    render_language_status_indicator,
    MultilingualForm
)

def main():
    st.set_page_config(
        page_title="多言語対応デモ | Multilingual Demo",
        page_icon="🌐",
        layout="wide"
    )
    
    # 言語システムの初期化
    lang_manager = get_language_manager()
    translator = get_translator()
    
    # ヘッダー
    st.title("🌐 多言語対応基盤デモ | Multilingual Support Demo")
    st.markdown("タスク4-8: 多言語対応基盤の実装デモンストレーション")
    
    # サイドバーで言語選択
    with st.sidebar:
        st.header("🌍 言語設定 | Language Settings")
        render_language_selector()
        
        st.markdown("---")
        
        # 言語状況インジケーター
        render_language_status_indicator()
    
    # メインコンテンツ
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 基本機能",
        "🔧 コンポーネント",
        "📊 統計情報", 
        "🧪 テスト"
    ])
    
    with tab1:
        render_basic_features_demo()
    
    with tab2:
        render_components_demo()
    
    with tab3:
        render_statistics_demo()
    
    with tab4:
        render_test_demo()

def render_basic_features_demo():
    """基本機能のデモ"""
    translator = get_translator()
    
    st.header("🏠 基本多言語機能")
    
    # 基本翻訳の例
    st.subheader("1. 基本翻訳システム")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**翻訳キー例:**")
        keys_to_test = [
            "app.title",
            "navigation.home",
            "buttons.start",
            "ui.loading",
            "home.welcome_message"
        ]
        
        for key in keys_to_test:
            translation = translator.translate(key)
            st.code(f"{key} → {translation}")
    
    with col2:
        st.markdown("**多言語対応コンポーネント:**")
        
        # タイトル
        render_multilingual_title("app.title")
        
        # テキスト
        render_multilingual_text("home.welcome_message")
        
        # ボタン
        if render_multilingual_button("buttons.start"):
            render_multilingual_alert("ui.success", "success")
    
    # アプリケーション統合例
    st.subheader("2. アプリケーション統合例")
    
    # 擬似ナビゲーション
    nav_options = {
        "home": "navigation.home",
        "job_selection": "navigation.job_selection",
        "settings": "navigation.settings"
    }
    
    selected = render_multilingual_selectbox(
        "navigation.home",
        nav_options
    )
    
    st.write(f"選択されたページ: {selected}")

def render_components_demo():
    """コンポーネントのデモ"""
    translator = get_translator()
    
    st.header("🔧 多言語対応UIコンポーネント")
    
    # アラート系
    st.subheader("1. アラート・通知")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("成功メッセージ"):
            render_multilingual_alert("ui.success", "success")
        
        if st.button("警告メッセージ"):
            render_multilingual_alert("ui.warning", "warning")
    
    with col2:
        if st.button("エラーメッセージ"):
            render_multilingual_alert("ui.error", "error")
        
        if st.button("情報メッセージ"):
            render_multilingual_alert("ui.info", "info")
    
    # フォーム系
    st.subheader("2. フォームコンポーネント")
    
    with MultilingualForm("demo_form"):
        user_input = st.text_input(
            translator.translate("ui.input_label", default="入力"),
            placeholder=translator.translate("ui.input_placeholder", default="ここに入力してください")
        )
        
        description = st.text_area(
            translator.translate("ui.description", default="説明"),
            placeholder=translator.translate("ui.description_placeholder", default="詳細を入力してください")
        )
        
        submitted = st.form_submit_button(translator.translate("buttons.submit"))
        
        if submitted:
            st.success(f"入力されたデータ: {user_input}, {description}")
    
    # 選択系
    st.subheader("3. 選択コンポーネント")
    
    # 進行モード選択
    mode_options = {
        "auto": "job_selection.job_types.auto",
        "interactive": "job_selection.job_types.interactive"
    }
    
    selected_mode = render_multilingual_selectbox(
        "job_selection.description",
        mode_options
    )
    
    st.write(f"選択されたモード: {selected_mode}")

def render_statistics_demo():
    """統計情報のデモ"""
    translator = get_translator()
    lang_manager = get_language_manager()
    
    st.header("📊 多言語対応統計情報")
    
    # 翻訳状況
    translation_status = translator.get_translation_status()
    
    st.subheader("1. 翻訳カバレッジ")
    
    current_lang = translation_status["current_language"]
    st.write(f"現在の言語: **{current_lang}**")
    st.write(f"サポート言語数: **{translation_status['total_languages']}**")
    
    # 各言語のカバレッジ
    coverage_data = translation_status["translation_coverage"]
    
    for lang_code, data in coverage_data.items():
        if data["total_keys"] > 0:
            progress_value = data["percentage"] / 100
            st.progress(
                progress_value, 
                text=f"{lang_code}: {data['percentage']}% ({data['translated_keys']}/{data['total_keys']})"
            )
    
    # 言語設定情報
    st.subheader("2. 言語設定情報")
    
    config = lang_manager.get_language_config()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("現在の言語", config["display_name"])
        st.metric("レイアウト方向", "RTL" if config["is_rtl"] else "LTR")
    
    with col2:
        st.metric("フォールバック言語数", len(config["fallback_languages"]))
        st.metric("サポート言語数", len(config["supported_languages"]))
    
    # 利用可能なキー
    st.subheader("3. 利用可能な翻訳キー")
    
    available_keys = translator.get_available_keys()
    st.write(f"総キー数: {len(available_keys)}")
    
    if st.checkbox("キー一覧を表示"):
        # カテゴリ別にグループ化
        categories = {}
        for key in available_keys:
            category = key.split('.')[0] if '.' in key else 'その他'
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        for category, keys in categories.items():
            with st.expander(f"{category} ({len(keys)} keys)"):
                for key in keys:
                    translation = translator.translate(key)
                    st.text(f"{key}: {translation}")

def render_test_demo():
    """テスト機能のデモ"""
    translator = get_translator()
    lang_manager = get_language_manager()
    
    st.header("🧪 テスト・検証機能")
    
    # カスタム翻訳テスト
    st.subheader("1. カスタム翻訳テスト")
    
    test_key = st.text_input("テスト用翻訳キー", value="app.title")
    
    if test_key:
        # 各言語での翻訳結果
        supported_langs = lang_manager.get_supported_languages()
        
        for lang_code, lang_name in supported_langs.items():
            # 一時的に言語を変更
            original_lang = lang_manager.get_current_language()
            lang_manager.set_language(lang_code)
            
            translation = translator.translate(test_key)
            st.write(f"**{lang_name} ({lang_code}):** {translation}")
            
            # 元の言語に戻す
            lang_manager.set_language(original_lang)
    
    # フォールバック機能テスト
    st.subheader("2. フォールバック機能テスト")
    
    non_existent_key = st.text_input("存在しないキー", value="non.existent.key")
    
    if non_existent_key:
        result = translator.translate(non_existent_key)
        st.write(f"結果: `{result}`")
        
        if result == non_existent_key:
            st.info("✓ フォールバック機能が正常に動作（キーがそのまま返される）")
        else:
            st.success(f"✓ 翻訳が見つかりました: {result}")
    
    # パフォーマンステスト
    st.subheader("3. パフォーマンステスト")
    
    if st.button("翻訳パフォーマンステスト実行"):
        import time
        
        test_keys = ["app.title", "navigation.home", "buttons.start", "ui.loading"]
        iterations = 100
        
        start_time = time.time()
        
        for _ in range(iterations):
            for key in test_keys:
                translator.translate(key)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / (iterations * len(test_keys))
        
        st.metric("総実行時間", f"{total_time:.4f}秒")
        st.metric("平均翻訳時間", f"{avg_time*1000:.2f}ミリ秒")
        st.metric("翻訳数", f"{iterations * len(test_keys)}")
    
    # デバッグ情報
    st.subheader("4. デバッグ情報")
    
    if st.checkbox("内部状態を表示"):
        st.json({
            "current_language": lang_manager.get_current_language(),
            "language_config": lang_manager.get_language_config(),
            "translation_status": translator.get_translation_status()
        })

if __name__ == "__main__":
    main()
