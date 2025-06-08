# -*- coding: utf-8 -*-
"""
ヘルプシステム デモアプリケーション

タスク4-9で実装されたヘルプシステムの全機能を
デモンストレーションするアプリケーション。
"""

import streamlit as st
import time
from ui.components.help_system import (
    get_help_manager, 
    get_help_ui, 
    HelpContext, 
    HelpType,
    show_quick_tip,
    show_contextual_help
)

def main():
    st.set_page_config(
        page_title="ヘルプシステム デモ", 
        page_icon="❓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ヘルプシステム初期化
    help_manager = get_help_manager()
    help_ui = get_help_ui()
    
    # ヘッダー
    st.title("❓ ヘルプシステム デモアプリケーション")
    st.markdown("**タスク4-9: ヘルプシステム実装完了** - 全機能のデモンストレーション")
    
    # サイドバー
    with st.sidebar:
        st.header("🎯 デモメニュー")
        
        demo_options = [
            "📖 ヘルプシステム概要",
            "❓ コンテキスト依存ヘルプ",
            "🎓 チュートリアルシステム",
            "🔍 ヘルプ検索機能",
            "💡 FAQ・よくある質問",
            "⚡ クイックヒント",
            "♿ アクセシビリティ機能",
            "📊 統計・進捗管理"
        ]
        
        selected_demo = st.radio("デモを選択", demo_options)
        
        st.markdown("---")
        st.info("💡 **使い方**\nサイドバーからデモを選択して、各機能を試してみてください。")
    
    # メインコンテンツ
    if selected_demo == "📖 ヘルプシステム概要":
        demo_overview()
    elif selected_demo == "❓ コンテキスト依存ヘルプ":
        demo_contextual_help()
    elif selected_demo == "🎓 チュートリアルシステム":
        demo_tutorial_system()
    elif selected_demo == "🔍 ヘルプ検索機能":
        demo_help_search()
    elif selected_demo == "💡 FAQ・よくある質問":
        demo_faq()
    elif selected_demo == "⚡ クイックヒント":
        demo_quick_tips()
    elif selected_demo == "♿ アクセシビリティ機能":
        demo_accessibility()
    elif selected_demo == "📊 統計・進捗管理":
        demo_statistics()

def demo_overview():
    """ヘルプシステム概要デモ"""
    st.header("📖 ヘルプシステム概要")
    
    st.success("🎉 **タスク4-9: ヘルプシステム実装完了**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 実装された機能")
        
        features = [
            ("📖 コンテキスト依存ヘルプ", "各画面に応じた適切なヘルプを表示"),
            ("🎓 インタラクティブチュートリアル", "ステップバイステップの学習ガイド"),
            ("🔍 ヘルプ検索", "キーワードベースの高速検索"),
            ("❓ FAQ システム", "よくある質問と回答の管理"),
            ("💡 クイックヒント", "操作に関する即座のガイダンス"),
            ("♿ アクセシビリティ対応", "誰もが使いやすいヘルプUI"),
            ("📊 進捗追跡", "学習・ヘルプ利用状況の管理"),
            ("⚙️ 設定カスタマイズ", "個人のニーズに合わせた調整")
        ]
        
        for feature, description in features:
            with st.expander(f"{feature}"):
                st.write(description)
    
    with col2:
        st.subheader("🎯 技術的特徴")
        
        tech_features = [
            "**モジュラー設計**: 各コンポーネントが独立して動作",
            "**状態管理**: ユーザーの進捗とプリファレンスを永続化",
            "**検索エンジン**: 効率的なキーワードマッチング",
            "**多言語対応**: 国際化フレームワーク統合",
            "**レスポンシブUI**: 様々なデバイスに対応",
            "**WAI-ARIA準拠**: アクセシビリティ標準に準拠"
        ]
        
        for feature in tech_features:
            st.write(f"• {feature}")
        
        st.markdown("---")
        
        # 統計情報
        st.subheader("📈 システム統計")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("実装したヘルプアイテム", "15+", "4")
            st.metric("チュートリアルステップ", "6", "6")
        
        with col_b:
            st.metric("FAQアイテム", "8+", "3")
            st.metric("サポート機能", "12", "8")

def demo_contextual_help():
    """コンテキスト依存ヘルプデモ"""
    st.header("❓ コンテキスト依存ヘルプデモ")
    
    st.write("各画面のコンテキストに応じて、適切なヘルプを表示します。")
    
    # コンテキスト選択
    context_options = {
        "🏠 ホーム画面": HelpContext.HOME,
        "🎯 ジョブ選択": HelpContext.JOB_SELECTION,
        "🎯 モード選択": HelpContext.MODE_SELECTION,
        "📝 テキスト生成": HelpContext.TEXT_GENERATION,
        "💻 コード生成": HelpContext.CODE_GENERATION,
        "🌐 Web生成": HelpContext.WEB_GENERATION,
        "🎤 音声インターフェース": HelpContext.VOICE_INTERFACE,
        "⚙️ 設定画面": HelpContext.SETTINGS,
        "📊 結果画面": HelpContext.RESULTS
    }
    
    selected_context = st.selectbox(
        "コンテキストを選択してください",
        list(context_options.keys())
    )
    
    context = context_options[selected_context]
    
    if st.button("❓ このコンテキストのヘルプを表示"):
        help_manager = get_help_manager()
        help_items = help_manager.get_contextual_help(context)
        
        if help_items:
            st.success(f"💡 **{selected_context}のヘルプ**")
            for item in help_items:
                with st.expander(f"📖 {item.title}"):
                    st.markdown(item.content)
                    
                    # キーワード表示
                    if item.keywords:
                        st.write("**関連キーワード:**")
                        tags = " • ".join([f"`{keyword}`" for keyword in item.keywords])
                        st.write(tags)
        else:
            st.info("このコンテキストのヘルプは準備中です。")

def demo_tutorial_system():
    """チュートリアルシステムデモ"""
    st.header("🎓 チュートリアルシステムデモ")
    
    help_ui = get_help_ui()
    help_manager = get_help_manager()
    
    st.write("インタラクティブなチュートリアルで、ユーザーをガイドします。")
    
    # チュートリアル一覧
    tutorials = {
        "🚀 クイックスタート": "quick_start",
        "📝 テキスト生成ガイド": "text_generation",
        "💻 コード生成ガイド": "code_generation",
        "🎤 音声機能ガイド": "voice_features"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 利用可能なチュートリアル")
        
        for tutorial_name, tutorial_id in tutorials.items():
            completed = help_manager.is_tutorial_completed(tutorial_id)
            status = "✅ 完了済み" if completed else "📝 未完了"
            
            st.write(f"{tutorial_name}: {status}")
            
            if st.button(f"▶️ 開始", key=f"start_{tutorial_id}"):
                st.session_state.active_tutorial = tutorial_id
                st.session_state.tutorial_step = 0
                st.rerun()
    
    with col2:
        st.subheader("📊 学習進捗")
        
        completed_count = len(help_manager.user_progress.get('completed_tutorials', []))
        total_count = len(tutorials)
        progress = completed_count / total_count if total_count > 0 else 0
        
        st.progress(progress)
        st.write(f"完了: {completed_count}/{total_count} チュートリアル")
        
        # 進捗詳細
        if completed_count > 0:
            st.success(f"🎉 {completed_count}個のチュートリアルを完了しました！")
        else:
            st.info("💡 チュートリアルを開始して学習を進めましょう。")
    
    # アクティブチュートリアル表示
    help_ui.render_active_tutorial()

def demo_help_search():
    """ヘルプ検索デモ"""
    st.header("🔍 ヘルプ検索機能デモ")
    
    help_ui = get_help_ui()
    
    st.write("キーワードで関連するヘルプを検索できます。")
    
    # 検索UI
    help_ui.render_help_search()
    
    st.markdown("---")
    
    # 検索例の提示
    st.subheader("💡 検索のコツ")
    
    search_tips = [
        ("具体的なキーワード", "「音声認識」「生成エラー」など具体的な語句"),
        ("機能名で検索", "「テキスト生成」「コード生成」「音声」など"),
        ("問題の症状で検索", "「動作しない」「遅い」「エラー」など"),
        ("操作名で検索", "「設定」「開始」「保存」など")
    ]
    
    for tip_title, tip_content in search_tips:
        st.write(f"**{tip_title}**: {tip_content}")

def demo_faq():
    """FAQデモ"""
    st.header("💡 FAQ・よくある質問デモ")
    
    help_ui = get_help_ui()
    
    st.write("頻繁にお寄せいただく質問をまとめています。")
    
    # FAQ UI
    help_ui.render_faq_section()
    
    # カテゴリ別FAQ（例）
    st.markdown("---")
    st.subheader("📂 カテゴリ別FAQ")
    
    faq_categories = {
        "🚀 基本的な使い方": [
            "システムの起動方法は？",
            "最初に何をすればいい？",
            "どの機能から始めればいい？"
        ],
        "🎤 音声機能": [
            "マイクが認識されない",
            "音声認識の精度を上げるには？",
            "読み上げ機能の設定方法"
        ],
        "⚙️ 設定・カスタマイズ": [
            "設定の変更方法",
            "言語の切り替え方法",
            "アクセシビリティ設定"
        ]
    }
    
    for category, questions in faq_categories.items():
        with st.expander(category):
            for question in questions:
                st.write(f"• {question}")

def demo_quick_tips():
    """クイックヒントデモ"""
    st.header("⚡ クイックヒントデモ")
    
    st.write("操作に関する即座のヒントやガイダンスを提供します。")
    
    # 各種クイックヒントの例
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💡 情報ヒント")
        
        if st.button("情報ヒントを表示"):
            show_quick_tip(
                "demo_info_tip",
                "📝 テキスト生成のコツ",
                "具体的で明確な指示を与えると、より良い結果が得られます。例：「新入社員向けの歓迎メールを親しみやすく200文字程度で」",
                dismissible=True
            )
        
        if st.button("成功ヒントを表示"):
            st.success("✅ **成功ヒント**: ファイルが正常に保存されました。編集履歴から前のバージョンを復元することもできます。")
        
        if st.button("警告ヒントを表示"):
            st.warning("⚠️ **注意**: 長時間の処理が実行中です。画面を閉じずにお待ちください。")
    
    with col2:
        st.subheader("🎯 操作ガイド")
        
        if st.button("操作ヒントを表示"):
            show_quick_tip(
                "demo_operation_tip",
                "🎤 音声機能の活用",
                "マイクボタンを押して「〇〇について説明して」と話すだけで、AIが回答します。ハンズフリー操作に便利です。",
                dismissible=True
            )
        
        if st.button("学習ヒントを表示"):
            st.info("🎓 **学習ヒント**: チュートリアルを完了すると、より高度な機能へのアクセスが可能になります。")
        
        if st.button("エラーヒントを表示"):
            st.error("❌ **エラー対応**: 接続エラーが発生しました。ネットワーク設定を確認するか、しばらく待ってから再試行してください。")

def demo_accessibility():
    """アクセシビリティ機能デモ"""
    st.header("♿ アクセシビリティ機能デモ")
    
    st.write("誰もが使いやすいヘルプシステムを目指しています。")
    
    # アクセシビリティ機能の表示
    tab1, tab2, tab3 = st.tabs(["🎤 音声対応", "⌨️ キーボード操作", "👀 視覚サポート"])
    
    with tab1:
        st.subheader("🎤 音声対応機能")
        st.write("音声によるヘルプアクセスとナビゲーション")
        
        features = [
            "音声でヘルプ検索（「音声機能について教えて」）",
            "ヘルプ内容の音声読み上げ",
            "音声によるチュートリアル進行",
            "音声フィードバック"
        ]
        
        for feature in features:
            st.write(f"• {feature}")
        
        if st.button("🎤 音声ヘルプテスト"):
            st.info("🎤 音声ヘルプ機能のテストです。実際の環境では音声で操作できます。")
    
    with tab2:
        st.subheader("⌨️ キーボード操作")
        st.write("マウスを使わない操作方法")
        
        shortcuts = [
            ("F1", "現在画面のヘルプを表示"),
            ("Ctrl+?", "ヘルプ検索を開く"),
            ("Tab", "次の要素に移動"),
            ("Enter", "選択した項目を実行"),
            ("Esc", "ヘルプを閉じる")
        ]
        
        for key, description in shortcuts:
            st.write(f"• **{key}**: {description}")
    
    with tab3:
        st.subheader("👀 視覚サポート")
        st.write("見やすさを向上する機能")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.checkbox("高コントラストモード", help="背景と文字のコントラストを強化")
            st.checkbox("大きな文字", help="フォントサイズを拡大")
            st.checkbox("アニメーション削減", help="動きを最小限に抑制")
        
        with col_b:
            st.slider("文字サイズ", 80, 150, 100, 10, format="%d%%")
            st.selectbox("カラーテーマ", ["標準", "ハイコントラスト", "ダークモード"])

def demo_statistics():
    """統計・進捗管理デモ"""
    st.header("📊 統計・進捗管理デモ")
    
    help_manager = get_help_manager()
    
    st.write("ヘルプシステムの利用状況と学習進捗を追跡します。")
    
    # 統計データ（デモ用）
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("ヘルプアクセス数", "42", "12")
        st.metric("FAQ閲覧数", "28", "8")
    
    with col2:
        st.metric("検索実行回数", "15", "5")
        st.metric("チュートリアル進行率", "75%", "25%")
    
    with col3:
        st.metric("解決済み問題", "18", "6")
        st.metric("平均解決時間", "2.3分", "-0.5分")
    
    # 進捗グラフ（デモ用）
    st.subheader("📈 利用状況推移")
    
    import random
    chart_data = {
        "日付": ["月", "火", "水", "木", "金", "土", "日"],
        "ヘルプアクセス": [random.randint(5, 20) for _ in range(7)],
        "問題解決": [random.randint(2, 10) for _ in range(7)]
    }
    
    st.line_chart(chart_data, x="日付")
    
    # ユーザープロファイル
    st.subheader("👤 学習プロファイル")
    
    user_stats = {
        "完了したチュートリアル": len(help_manager.user_progress.get('completed_tutorials', [])),
        "非表示にしたヒント": len(help_manager.user_progress.get('dismissed_tips', [])),
        "ヘルプ設定": "カスタマイズ済み" if help_manager.user_progress.get('help_preferences') else "デフォルト"
    }
    
    for stat_name, stat_value in user_stats.items():
        st.write(f"**{stat_name}**: {stat_value}")

# フッター情報
def render_footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "<strong>ヘルプシステム デモアプリケーション</strong><br>"
        "タスク4-9: ヘルプシステム実装完了 ✅<br>"
        "包括的なユーザーサポート機能を提供"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
    render_footer()
