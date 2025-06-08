# -*- coding: utf-8 -*-
"""
レスポンシブ対応ジョブ選択ページ

様々なデバイスサイズに最適化されたジョブ選択画面を提供します。
"""

import streamlit as st
from ui.components.responsive_components import (
    get_responsive_components, adaptive_header, adaptive_button_group,
    adaptive_form, apply_responsive_css
)
from ui.components.responsive_ui import get_responsive_ui, is_mobile_device, get_device_type


def render():
    """レスポンシブ対応ジョブ選択画面のレンダリング"""
    
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
        title="ジョブ選択",
        subtitle="作成したいコンテンツのタイプを選択してください",
        icon="🎯",
        level=1
    )
    
    # デバイス別の説明
    if screen_size.is_mobile:
        st.info("📱 タップして希望する作業を選択してください。")
    else:
        st.info("🖱️ クリックして希望する作業を選択してください。")
    
    # ジョブカテゴリ選択
    st.markdown("### 📋 作業カテゴリ")
    
    job_categories = [
        {
            'label': '💻 プログラム開発',
            'value': 'programming',
            'key': 'cat_programming',
            'help': 'Webアプリ、デスクトップアプリ、スクリプトなどの開発'
        },
        {
            'label': '🌐 Webサイト作成',
            'value': 'website',
            'key': 'cat_website',
            'help': 'レスポンシブWebサイト、ランディングページの作成'
        },
        {
            'label': '📄 ドキュメント作成',
            'value': 'document',
            'key': 'cat_document',
            'help': '技術文書、マニュアル、報告書の作成'
        }
    ]
    
    selected_category = adaptive_button_group(job_categories, layout="auto")
    
    # 選択されたカテゴリに応じた詳細選択
    if selected_category:
        st.session_state.selected_category = selected_category
        
        st.markdown("---")
        st.markdown("### 🔧 詳細設定")
        
        if selected_category == 'programming':
            render_programming_options(responsive_ui, screen_size)
        elif selected_category == 'website':
            render_website_options(responsive_ui, screen_size)
        elif selected_category == 'document':
            render_document_options(responsive_ui, screen_size)
    
    # 進行モード選択
    if 'selected_category' in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 AI進行モード選択")
        
        mode_buttons = [
            {
                'label': '🔄 対話型モード',
                'value': 'interactive',
                'key': 'mode_interactive',
                'help': 'AIと対話しながら段階的に作業を進める'
            },
            {
                'label': '⚡ 全自動モード',
                'value': 'auto',
                'key': 'mode_auto',
                'help': 'AIが自動的に最適な結果を生成する'
            }
        ]
        
        selected_mode = adaptive_button_group(mode_buttons, layout="auto")
        
        if selected_mode:
            st.session_state.selected_mode = selected_mode
            
            # モード別の説明
            if selected_mode == 'interactive':
                st.success("🔄 **対話型モード**を選択しました")
                st.write("AIとの対話を通じて、段階的に作業を進めます。")
                st.write("- 要件確認とフィードバック")
                st.write("- 段階的な改善と調整")
                st.write("- ユーザーの意思決定を重視")
            
            elif selected_mode == 'auto':
                st.success("⚡ **全自動モード**を選択しました")
                st.write("AIが自動的に最適な結果を生成します。")
                st.write("- 高速な作業完了")
                st.write("- AI判断による最適化")
                st.write("- 最小限のユーザー入力")
    
    # 開始ボタン
    if 'selected_category' in st.session_state and 'selected_mode' in st.session_state:
        st.markdown("---")
        st.markdown("### 🚀 作業開始")
        
        if screen_size.is_mobile:
            start_button = st.button(
                "🎯 作業を開始する",
                key="start_job_mobile",
                use_container_width=True,
                type="primary"
            )
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                start_button = st.button(
                    "🎯 作業を開始する",
                    key="start_job_desktop",
                    use_container_width=True,
                    type="primary"
                )
        
        if start_button:
            # 作業開始処理
            category = st.session_state.selected_category
            mode = st.session_state.selected_mode
            
            st.success(f"🎉 {category}作業を{mode}モードで開始します！")
            
            # 進行状況ページに遷移
            st.session_state.current_page = 'progress_notification'
            st.session_state.job_in_progress = True
            st.session_state.job_details = {
                'category': category,
                'mode': mode,
                'start_time': st.session_state.get('current_time', 'now')
            }
            
            st.rerun()


def render_programming_options(responsive_ui, screen_size):
    """プログラミングオプションの表示"""
    
    # プログラミング言語選択
    programming_languages = [
        {
            'title': 'Python',
            'content': 'データ分析、Web開発、AI/ML<br>初心者から上級者まで対応',
            'icon': '🐍'
        },
        {
            'title': 'JavaScript',
            'content': 'フロントエンド、バックエンド<br>モダンWeb開発に最適',
            'icon': '📜'
        },
        {
            'title': 'Java',
            'content': 'エンタープライズ開発<br>安定性と拡張性重視',
            'icon': '☕'
        },
        {
            'title': 'C#',
            'content': '.NET開発、デスクトップアプリ<br>Windows環境に最適',
            'icon': '🔷'
        },
        {
            'title': 'Go',
            'content': '高性能バックエンド<br>クラウドネイティブ開発',
            'icon': '🔄'
        },
        {
            'title': 'Rust',
            'content': 'システムプログラミング<br>安全性とパフォーマンス重視',
            'icon': '⚙️'
        }
    ]
    
    st.write("**プログラミング言語を選択してください：**")
    
    if screen_size.is_mobile:
        # モバイル：セレクトボックス
        language_options = [lang['title'] for lang in programming_languages]
        selected_language = st.selectbox(
            "言語選択",
            language_options,
            key="programming_language_mobile"
        )
        
        # 選択した言語の詳細表示
        selected_lang_info = next(lang for lang in programming_languages if lang['title'] == selected_language)
        responsive_ui.render_responsive_card(
            title=selected_lang_info['title'],
            content=selected_lang_info['content'],
            icon=selected_lang_info['icon']
        )
    
    else:
        # デスクトップ・タブレット：グリッド表示
        responsive_ui.create_responsive_grid(programming_languages, max_columns=3)
    
    # プロジェクトタイプ
    st.markdown("**プロジェクトタイプ：**")
    
    project_types = [
        {
            'label': '🌐 Webアプリケーション',
            'value': 'webapp',
            'key': 'proj_webapp',
            'help': 'フルスタックWebアプリケーションの開発'
        },
        {
            'label': '🖥️ デスクトップアプリ',
            'value': 'desktop',
            'key': 'proj_desktop',
            'help': 'GUI付きデスクトップアプリケーション'
        },
        {
            'label': '📊 データ分析スクリプト',
            'value': 'data_analysis',
            'key': 'proj_data',
            'help': 'データ処理・分析・可視化スクリプト'
        },
        {
            'label': '🔧 ユーティリティツール',
            'value': 'utility',
            'key': 'proj_utility',
            'help': '自動化ツール・コマンドラインユーティリティ'
        }
    ]
    
    selected_project_type = adaptive_button_group(project_types, layout="auto")
    
    if selected_project_type:
        st.session_state.project_type = selected_project_type


def render_website_options(responsive_ui, screen_size):
    """Webサイトオプションの表示"""
    
    # Webサイトタイプ選択
    website_types = [
        {
            'title': 'コーポレートサイト',
            'content': '企業・団体の公式サイト<br>信頼性とプロフェッショナル性を重視',
            'icon': '🏢'
        },
        {
            'title': 'ポートフォリオサイト',
            'content': '個人作品・実績の紹介<br>クリエイティブな表現に最適',
            'icon': '🎨'
        },
        {
            'title': 'ランディングページ',
            'content': '製品・サービスの紹介<br>コンバージョン最適化',
            'icon': '🎯'
        },
        {
            'title': 'ブログサイト',
            'content': '記事投稿・管理機能<br>コンテンツマーケティング',
            'icon': '📝'
        },
        {
            'title': 'ECサイト',
            'content': 'オンラインショップ<br>商品販売・決済機能',
            'icon': '🛒'
        },
        {
            'title': 'イベントサイト',
            'content': 'イベント告知・申込み<br>期間限定キャンペーン',
            'icon': '🎪'
        }
    ]
    
    st.write("**Webサイトタイプを選択してください：**")
    responsive_ui.create_responsive_grid(website_types, max_columns=3)
    
    # デザインスタイル
    st.markdown("**デザインスタイル：**")
    
    design_styles = [
        {
            'label': '🎨 モダン・ミニマル',
            'value': 'modern',
            'key': 'design_modern',
            'help': '洗練されたシンプルなデザイン'
        },
        {
            'label': '🎪 カラフル・ポップ',
            'value': 'colorful',
            'key': 'design_colorful',
            'help': '明るく活気のあるデザイン'
        },
        {
            'label': '🏢 ビジネス・フォーマル',
            'value': 'business',
            'key': 'design_business',
            'help': '信頼性を重視したプロフェッショナルデザイン'
        },
        {
            'label': '🌿 ナチュラル・オーガニック',
            'value': 'natural',
            'key': 'design_natural',
            'help': '自然をモチーフとした温かみのあるデザイン'
        }
    ]
    
    selected_design = adaptive_button_group(design_styles, layout="auto")
    
    if selected_design:
        st.session_state.design_style = selected_design


def render_document_options(responsive_ui, screen_size):
    """ドキュメントオプションの表示"""
    
    # ドキュメントタイプ選択
    document_types = [
        {
            'title': '技術文書',
            'content': 'API仕様書、設計書<br>開発者向け技術資料',
            'icon': '📋'
        },
        {
            'title': 'ユーザーマニュアル',
            'content': '操作手順書、ガイドブック<br>エンドユーザー向け説明書',
            'icon': '📖'
        },
        {
            'title': 'プレゼンテーション',
            'content': '提案書、企画書<br>視覚的なプレゼンテーション資料',
            'icon': '📊'
        },
        {
            'title': '報告書',
            'content': '調査結果、分析レポート<br>データに基づいた報告文書',
            'icon': '📄'
        }
    ]
    
    st.write("**ドキュメントタイプを選択してください：**")
    responsive_ui.create_responsive_grid(document_types, max_columns=2)
    
    # フォーマット選択
    st.markdown("**出力フォーマット：**")
    
    format_options = [
        {
            'label': '📄 Markdown',
            'value': 'markdown',
            'key': 'format_markdown',
            'help': 'GitHub、Wiki等で使用可能'
        },
        {
            'label': '📝 Word文書',
            'value': 'docx',
            'key': 'format_docx',
            'help': 'Microsoft Word形式'
        },
        {
            'label': '🔗 HTML',
            'value': 'html',
            'key': 'format_html',
            'help': 'Web表示可能なHTML形式'
        },
        {
            'label': '📊 PDF',
            'value': 'pdf',
            'key': 'format_pdf',
            'help': '印刷・配布に最適なPDF形式'
        }
    ]
    
    selected_format = adaptive_button_group(format_options, layout="auto")
    
    if selected_format:
        st.session_state.document_format = selected_format
