# -*- coding: utf-8 -*-
"""
ヘルプページ - 包括的なヘルプとサポート機能

このページは以下の機能を提供します：
- よくある質問（FAQ）
- 操作ガイド・チュートリアル
- ヘルプ検索
- トラブルシューティング
- アクセシビリティ情報
"""

import streamlit as st
from ui.components.help_system import (
    get_help_manager, 
    get_help_ui, 
    HelpContext,
    HelpType
)

def render():
    """ヘルプページのメイン表示"""
    st.title("🎯 ヘルプ・サポート")
    st.markdown("システムの使い方やよくある質問を確認できます。")
    
    help_ui = get_help_ui()
    help_manager = get_help_manager()
    
    # タブ分割
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 検索", 
        "❓ FAQ", 
        "🎓 チュートリアル", 
        "📖 操作ガイド", 
        "♿ アクセシビリティ"
    ])
    
    # 検索タブ
    with tab1:
        render_help_search_tab(help_ui)
    
    # FAQタブ
    with tab2:
        render_faq_tab(help_ui)
    
    # チュートリアルタブ
    with tab3:
        render_tutorial_tab(help_ui, help_manager)
    
    # 操作ガイドタブ
    with tab4:
        render_guide_tab(help_manager)
    
    # アクセシビリティタブ
    with tab5:
        render_accessibility_tab()

def render_help_search_tab(help_ui):
    """ヘルプ検索タブ"""
    st.header("🔍 ヘルプ検索")
    st.write("知りたいことをキーワードで検索できます。")
    
    help_ui.render_help_search()
    
    st.markdown("---")
    
    # 人気の検索キーワード
    st.subheader("🔥 よく検索されるキーワード")
    popular_keywords = [
        ("音声", "音声機能の使い方"),
        ("生成", "テキスト・コード生成について"),
        ("エラー", "トラブル解決方法"),
        ("設定", "システム設定の変更"),
        ("初回", "初めての使用方法")
    ]
    
    cols = st.columns(3)
    for i, (keyword, description) in enumerate(popular_keywords):
        with cols[i % 3]:
            if st.button(f"🏷️ {keyword}", key=f"keyword_{i}"):
                st.session_state.help_search_query = keyword

def render_faq_tab(help_ui):
    """FAQタブ"""
    st.header("❓ よくある質問")
    st.write("頻繁にお寄せいただく質問と回答をまとめました。")
    
    help_ui.render_faq_section()
    
    st.markdown("---")
    
    # 追加のFAQカテゴリ
    with st.expander("📱 システム動作環境について"):
        st.markdown("""
        **Q: 推奨ブラウザは何ですか？**
        A: Chrome、Firefox、Safari、Edgeの最新版を推奨します。
        
        **Q: スマートフォンでも使用できますか？**
        A: はい、レスポンシブデザインに対応しており、スマートフォンやタブレットでもご利用いただけます。
        
        **Q: インターネット接続は必要ですか？**
        A: はい、AIサービスを利用するためインターネット接続が必要です。
        """)
    
    with st.expander("🔐 プライバシー・セキュリティについて"):
        st.markdown("""
        **Q: 入力したデータはどこに保存されますか？**
        A: データは一時的に処理のためにのみ使用され、セッション終了後に自動削除されます。
        
        **Q: 個人情報の取り扱いは？**
        A: 個人情報は適切に保護され、第三者と共有されることはありません。
        
        **Q: 生成されたコンテンツの著作権は？**
        A: 生成されたコンテンツの著作権はユーザーに帰属します。
        """)

def render_tutorial_tab(help_ui, help_manager):
    """チュートリアルタブ"""
    st.header("🎓 チュートリアル")
    st.write("ステップバイステップで使い方を学習できます。")
    
    # アクティブチュートリアルがある場合は表示
    help_ui.render_active_tutorial()
    
    if 'active_tutorial' not in st.session_state:
        # チュートリアル一覧
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚀 クイックスタート")
            st.write("初めての方向けの基本的な使い方ガイド")
            
            completed = help_manager.is_tutorial_completed("quick_start")
            status = "✅ 完了済み" if completed else "📝 未完了"
            st.write(f"ステータス: {status}")
            
            if st.button("▶️ 開始", key="start_quick_tutorial"):
                st.session_state.active_tutorial = "quick_start"
                st.session_state.tutorial_step = 0
                st.rerun()
        
        with col2:
            st.subheader("🎯 機能別ガイド")
            st.write("各機能の詳細な使い方")
            
            feature_tutorials = [
                ("テキスト生成", "text_generation"),
                ("コード生成", "code_generation"),
                ("音声機能", "voice_features"),
                ("設定カスタマイズ", "customization")
            ]
            
            for title, tutorial_id in feature_tutorials:
                completed = help_manager.is_tutorial_completed(tutorial_id)
                status_icon = "✅" if completed else "📝"
                
                if st.button(f"{status_icon} {title}", key=f"tutorial_{tutorial_id}"):
                    st.info(f"{title}のチュートリアルは準備中です。")
    
    st.markdown("---")
    
    # 学習進捗
    st.subheader("📊 学習進捗")
    completed_tutorials = help_manager.user_progress.get('completed_tutorials', [])
    total_tutorials = 4  # 将来的に増える予定
    
    progress = len(completed_tutorials) / total_tutorials
    st.progress(progress)
    st.write(f"完了したチュートリアル: {len(completed_tutorials)}/{total_tutorials}")

def render_guide_tab(help_manager):
    """操作ガイドタブ"""
    st.header("📖 操作ガイド")
    st.write("各機能の詳細な説明と使用方法を確認できます。")
    
    # ガイドカテゴリ
    guide_categories = {
        "🏠 基本操作": [
            "ホーム画面の使い方",
            "ジョブ選択の方法",
            "進行モードの選択",
            "基本的な設定変更"
        ],
        "📝 テキスト生成": [
            "効果的なプロンプトの書き方",
            "生成結果の編集・調整",
            "テンプレートの活用",
            "長文生成のコツ"
        ],
        "💻 コード生成": [
            "プログラミング言語の指定",
            "コード品質の向上",
            "デバッグ支援の活用",
            "複雑なアルゴリズムの生成"
        ],
        "🌐 Webページ生成": [
            "レスポンシブデザインの作成",
            "アクセシビリティ対応",
            "CSS・JavaScriptの調整",
            "SEO最適化"
        ],
        "🎤 音声機能": [
            "マイク設定の最適化",
            "音声認識の精度向上",
            "読み上げ機能の活用",
            "音声コマンドの使い方"
        ]
    }
    
    for category, guides in guide_categories.items():
        with st.expander(category):
            for guide in guides:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📄 {guide}")
                with col2:
                    if st.button("見る", key=f"guide_{guide}"):
                        show_detailed_guide(guide)

def show_detailed_guide(guide_title):
    """詳細ガイドの表示"""
    st.info(f"📖 **{guide_title}**の詳細ガイドは準備中です。")
    
    # 将来的には詳細なガイドコンテンツを表示
    # 現在はプレースホルダー
    sample_guides = {
        "効果的なプロンプトの書き方": """
        **良いプロンプトの特徴：**
        1. 具体的で明確な指示
        2. 期待する形式・スタイルの指定
        3. 必要な情報の事前提供
        4. 段階的な指示の分割
        
        **例：**
        悪い例：「文章を書いて」
        良い例：「新入社員向けの歓迎メールを、親しみやすく丁寧な口調で200文字程度で作成してください」
        """,
        
        "マイク設定の最適化": """
        **設定手順：**
        1. システム設定から音声デバイスを確認
        2. マイクレベルを適切に調整
        3. ノイズキャンセリング機能を有効化
        4. テスト機能で動作確認
        
        **トラブルシューティング：**
        - 音声が認識されない → マイクアクセス許可を確認
        - 雑音が多い → マイク位置を調整、背景音を最小化
        """
    }
    
    if guide_title in sample_guides:
        st.markdown(sample_guides[guide_title])

def render_accessibility_tab():
    """アクセシビリティタブ"""
    st.header("♿ アクセシビリティ情報")
    st.write("誰もが使いやすいシステムを目指して、アクセシビリティ機能を提供しています。")
    
    # アクセシビリティ機能一覧
    accessibility_features = {
        "🎤 音声機能": {
            "description": "音声による入力・出力対応",
            "features": [
                "音声コマンドによる操作",
                "画面読み上げ機能",
                "音声フィードバック",
                "ハンズフリー操作"
            ]
        },
        "⌨️ キーボード操作": {
            "description": "マウスを使わない操作方法",
            "features": [
                "Tabキーによるナビゲーション",
                "Enterキーでの実行",
                "Escキーでのキャンセル",
                "ショートカットキー対応"
            ]
        },
        "👀 視覚的支援": {
            "description": "見やすさの向上機能",
            "features": [
                "高コントラストモード",
                "文字サイズ調整",
                "色覚サポート",
                "画面拡大対応"
            ]
        },
        "🎯 認知的支援": {
            "description": "理解しやすさの向上",
            "features": [
                "シンプルなインターフェース",
                "明確なラベルと説明",
                "エラーメッセージの改善",
                "進捗状況の可視化"
            ]
        }
    }
    
    for category, info in accessibility_features.items():
        with st.expander(f"{category} - {info['description']}"):
            st.write("**提供機能：**")
            for feature in info["features"]:
                st.write(f"• {feature}")
    
    st.markdown("---")
    
    # アクセシビリティ設定
    st.subheader("⚙️ アクセシビリティ設定")
    st.write("個人のニーズに合わせてシステムをカスタマイズできます。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 視覚設定
        st.write("**👀 視覚設定**")
        high_contrast = st.checkbox("高コントラストモード", value=False)
        large_text = st.checkbox("大きな文字", value=False)
        reduce_motion = st.checkbox("アニメーション削減", value=False)
    
    with col2:
        # 音声設定
        st.write("**🎤 音声設定**")
        voice_feedback = st.checkbox("音声フィードバック", value=True)
        auto_read = st.checkbox("自動読み上げ", value=False)
        voice_speed = st.slider("読み上げ速度", 0.5, 2.0, 1.0, 0.1)
    
    if st.button("💾 設定を保存"):
        # 設定をセッションステートに保存
        st.session_state.accessibility_settings = {
            'high_contrast': high_contrast,
            'large_text': large_text,
            'reduce_motion': reduce_motion,
            'voice_feedback': voice_feedback,
            'auto_read': auto_read,
            'voice_speed': voice_speed
        }
        st.success("✅ アクセシビリティ設定を保存しました。")
    
    st.markdown("---")
    
    # サポート情報
    st.subheader("📞 サポート情報")
    st.info("""
    **アクセシビリティに関するお問い合わせ**
    
    システムの使用に困難を感じられた場合は、以下の方法でサポートを受けることができます：
    
    • **技術的なサポート**: ヘルプデスク（準備中）
    • **使い方の相談**: オンラインチュートリアル
    • **改善要望**: フィードバック機能（準備中）
    
    私たちは、誰もが平等にシステムを利用できることを目指しています。
    """)

# メイン関数（テスト用）
if __name__ == "__main__":
    render()
