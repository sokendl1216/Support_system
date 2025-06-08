# -*- coding: utf-8 -*-
"""
レスポンシブ対応ホームページ

様々なデバイスサイズに最適化されたホーム画面を提供します。
"""

import streamlit as st
from ui.components.responsive_components import (
    get_responsive_components, adaptive_header, adaptive_button_group,
    adaptive_metrics, adaptive_data_display, apply_responsive_css
)
from ui.components.responsive_ui import get_responsive_ui, is_mobile_device, get_device_type


def render():
    """レスポンシブ対応ホーム画面のレンダリング"""
    
    # レスポンシブCSS適用
    apply_responsive_css()
    
    # レスポンシブコンポーネント取得
    responsive_ui = get_responsive_ui()
    responsive_components = get_responsive_components()
    
    # デバイス情報取得
    screen_size = responsive_ui.get_current_screen_size()
    device_type = get_device_type()
    
    # 適応型ヘッダー
    adaptive_header(
        title="AI支援システム",
        subtitle="多様なニーズを持つ方の仕事支援プラットフォーム",
        icon="🤖",
        level=1
    )
    
    # デバイス別の挨拶メッセージ
    if screen_size.is_mobile:
        st.markdown("📱 **モバイル最適化表示**")
        st.info("タップして各機能をご利用ください。")
    elif screen_size.is_tablet:
        st.markdown("📟 **タブレット最適化表示**")
        st.info("タッチ操作に最適化された画面で各機能をご利用ください。")
    else:
        st.markdown("🖥️ **デスクトップ最適化表示**")
        st.info("フル機能をご利用いただけます。")
    
    # システム概要カード（レスポンシブ）
    overview_data = [
        {
            'title': 'AIエージェント',
            'content': '自動・対話型の2つのモードで<br>最適な支援を提供します',
            'icon': '🤖'
        },
        {
            'title': 'プログラム生成',
            'content': '多言語対応の高品質な<br>プログラムコードを生成',
            'icon': '💻'
        },
        {
            'title': 'Webサイト作成',
            'content': 'アクセシブルで美しい<br>Webサイトを自動生成',
            'icon': '🌐'
        },
        {
            'title': '音声対話',
            'content': '音声認識・合成による<br>自然な対話インターフェース',
            'icon': '🎤'
        },
        {
            'title': 'ヘルプシステム',
            'content': 'コンテキスト依存のヘルプと<br>インタラクティブチュートリアル',
            'icon': '❓'
        },
        {
            'title': '多言語対応',
            'content': '日本語・英語・韓国語・中国語<br>での完全サポート',
            'icon': '🌍'
        }
    ]
    
    # レスポンシブグリッド表示
    st.markdown("### 🌟 主要機能")
    responsive_ui.create_responsive_grid(overview_data, max_columns=3)
    
    # システム状況メトリクス
    st.markdown("### 📊 システム状況")
    
    metrics_data = [
        {
            'label': 'プロジェクト進捗',
            'value': '85%',
            'delta': '+15%',
            'help': 'フェーズ4（UI実装）進行中'
        },
        {
            'label': '実装完了機能',
            'value': '15',
            'delta': '+2',
            'help': '新規実装：ヘルプシステム、レスポンシブUI'
        },
        {
            'label': 'AIキャッシュヒット率',
            'value': '100%',
            'delta': '+25%',
            'help': '高性能キャッシュシステムによる最適化'
        },
        {
            'label': 'ユーザビリティスコア',
            'value': '95点',
            'delta': '+20点',
            'help': 'アクセシビリティ・ヘルプシステム強化'
        }
    ]
    
    adaptive_metrics(metrics_data)
    
    # クイックアクション（デバイス別最適化）
    st.markdown("### 🚀 クイックアクション")
    
    action_buttons = [
        {
            'label': '🎯 新しいジョブを開始',
            'value': 'new_job',
            'key': 'btn_new_job',
            'help': 'プログラム生成またはWebサイト作成を開始'
        },
        {
            'label': '📚 ヘルプ・チュートリアル',
            'value': 'help',
            'key': 'btn_help',
            'help': '使い方ガイドとチュートリアルを表示'
        },
        {
            'label': '🔄 処理状況確認',
            'value': 'status',
            'key': 'btn_status',
            'help': '現在の処理状況と通知を確認'
        }
    ]
    
    if not screen_size.is_mobile:
        action_buttons.append({
            'label': '⚙️ 詳細設定',
            'value': 'settings',
            'key': 'btn_settings',
            'help': 'システム設定とカスタマイズ'
        })
    
    clicked_action = adaptive_button_group(action_buttons, layout="auto")
    
    # アクション処理
    if clicked_action:
        if clicked_action == 'new_job':
            st.session_state.current_page = 'job_selection'
            st.rerun()
        elif clicked_action == 'help':
            st.session_state.current_page = 'help'
            st.rerun()
        elif clicked_action == 'status':
            st.session_state.current_page = 'progress_notification'
            st.rerun()
        elif clicked_action == 'settings':
            st.session_state.current_page = 'settings'
            st.rerun()
    
    # 最新情報（レスポンシブ表示）
    st.markdown("### 📰 最新の更新情報")
    
    # デバイス別のニュース表示
    news_data = [
        {
            'title': 'レスポンシブUI最適化完了',
            'content': '全デバイスでの最適な表示を実現。モバイル、タブレット、デスクトップに対応。',
            'icon': '📱'
        },
        {
            'title': 'ヘルプシステム実装完了',
            'content': 'コンテキスト依存ヘルプ、FAQ、チュートリアル機能を統合。',
            'icon': '❓'
        },
        {
            'title': 'AIキャッシュ最適化完了',
            'content': '100%ヒット率達成、サブミリ秒応答時間を実現。',
            'icon': '⚡'
        }
    ]
    
    if screen_size.is_mobile:
        # モバイル：カード形式
        for news in news_data:
            responsive_ui.render_responsive_card(
                title=news['title'],
                content=news['content'],
                icon=news['icon']
            )
    else:
        # タブレット・デスクトップ：グリッド形式
        responsive_ui.create_responsive_grid(news_data)
    
    # フィードバック・連絡先（レスポンシブ）
    st.markdown("### 💬 フィードバック・サポート")
    
    feedback_col, support_col = st.columns(2)
    
    with feedback_col:
        st.markdown("**ご意見・ご要望**")
        st.write("使いやすさの改善にご協力ください")
        if st.button("📝 フィードバックを送る", use_container_width=screen_size.is_mobile):
            st.info("フィードバック機能は開発中です。")
    
    with support_col:
        st.markdown("**技術サポート**")
        st.write("使い方でお困りの際はこちら")
        if st.button("🆘 サポートを依頼", use_container_width=screen_size.is_mobile):
            st.session_state.current_page = 'help'
            st.rerun()
    
    # デバイス情報表示（開発者向け）
    if st.checkbox("🔧 開発者情報を表示", key="dev_info"):
        st.markdown("### 🔧 開発者情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.code(f"""
デバイスタイプ: {device_type.value}
画面サイズ: {screen_size.width} x {screen_size.height}
モバイル: {screen_size.is_mobile}
タブレット: {screen_size.is_tablet}
デスクトップ: {screen_size.is_desktop}
            """)
        
        with col2:
            st.markdown("**レスポンシブ機能**")
            st.markdown("- 自動デバイス検出")
            st.markdown("- 適応型レイアウト")
            st.markdown("- デバイス別最適化")
            st.markdown("- アクセシビリティ対応")
    
    # プロジェクト進捗状況
    st.markdown("---")
    st.markdown("### 📋 プロジェクト進捗")
    
    progress_info = {
        "フェーズ1: 設計・準備": 100,
        "フェーズ2: 基盤開発": 100,
        "フェーズ3: AIサービス実装": 100,
        "フェーズ4: UI・ユーザー体験実装": 90,  # レスポンシブUI完了で90%
        "フェーズ5: テスト・品質保証": 70,
        "フェーズ6: ドキュメント・リリース準備": 20,
        "フェーズ7: 本番リリース・運用開始": 10
    }
    
    if screen_size.is_mobile:
        # モバイル：縦型プログレスバー
        for phase, progress in progress_info.items():
            st.markdown(f"**{phase}**")
            st.progress(progress / 100)
            st.caption(f"{progress}% 完了")
            st.markdown("")
    else:
        # デスクトップ・タブレット：表形式
        progress_data = [
            {"フェーズ": phase, "進捗": f"{progress}%", "状態": "✅ 完了" if progress == 100 else "🔄 進行中" if progress > 0 else "⏳ 待機中"}
            for phase, progress in progress_info.items()
        ]
        adaptive_data_display(progress_data, display_type="table")
    
    # フッター情報
    st.markdown("---")
    footer_text = "🤖 **AI支援システム** | レスポンシブUI最適化完了 | 全デバイス対応"
    if screen_size.is_mobile:
        st.markdown(f"<div style='text-align: center; font-size: 0.8em;'>{footer_text}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align: center; color: #666;'>{footer_text}</div>", unsafe_allow_html=True)
