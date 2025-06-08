# -*- coding: utf-8 -*-
"""
ヘルプシステム - コンテキスト依存のヘルプとチュートリアル機能

このモジュールは以下の機能を提供します：
- コンテキスト依存ヘルプ表示
- インタラクティブチュートリアル
- FAQ・よくある質問への対応
- 操作ガイド・ヘルプドキュメント
- アクセシビリティ対応ヘルプ
"""

import streamlit as st
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

class HelpType(Enum):
    """ヘルプの種類"""
    CONTEXTUAL = "contextual"      # コンテキスト依存ヘルプ
    TUTORIAL = "tutorial"          # チュートリアル
    FAQ = "faq"                    # よくある質問
    GUIDE = "guide"                # 操作ガイド
    TOOLTIP = "tooltip"            # ツールチップ
    QUICK_START = "quick_start"    # クイックスタート

class HelpContext(Enum):
    """ヘルプコンテキスト"""
    HOME = "home"
    JOB_SELECTION = "job_selection"
    MODE_SELECTION = "mode_selection"
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    WEB_GENERATION = "web_generation"
    VOICE_INTERFACE = "voice_interface"
    SETTINGS = "settings"
    RESULTS = "results"

@dataclass
class HelpItem:
    """ヘルプアイテム"""
    id: str
    title: str
    content: str
    help_type: HelpType
    context: HelpContext
    keywords: List[str]
    difficulty: int = 1  # 1-5の難易度
    prerequisites: List[str] = None
    next_steps: List[str] = None
    media_url: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class TutorialStep:
    """チュートリアルステップ"""
    step_id: str
    title: str
    description: str
    target_element: Optional[str] = None
    action_required: bool = False
    completion_criteria: Optional[str] = None
    hints: List[str] = None

class HelpSystemManager:
    """ヘルプシステム管理クラス"""
    
    def __init__(self):
        self.help_items: Dict[str, HelpItem] = {}
        self.tutorials: Dict[str, List[TutorialStep]] = {}
        self.user_progress: Dict[str, Any] = {}
        self._initialize_help_content()
        self._load_user_progress()
    
    def _initialize_help_content(self):
        """ヘルプコンテンツの初期化"""
        # ホーム画面のヘルプ
        self.add_help_item(HelpItem(
            id="home_welcome",
            title="支援システムへようこそ",
            content="""
            このシステムは、多様なニーズを持つ方の仕事をAIが支援するためのツールです。
            
            **主な機能：**
            - 📝 テキスト生成・編集支援
            - 💻 プログラムコード生成
            - 🌐 Webページ作成支援
            - 🎤 音声による対話操作
            - 🔧 カスタマイズ可能な設定
            
            まずは「ジョブ選択」から始めてみましょう。
            """,
            help_type=HelpType.CONTEXTUAL,
            context=HelpContext.HOME,
            keywords=["ホーム", "開始", "機能", "概要"]
        ))
        
        # ジョブ選択のヘルプ
        self.add_help_item(HelpItem(
            id="job_selection_guide",
            title="作業の種類を選択",
            content="""
            作業に適したジョブタイプを選択してください：
            
            **📝 テキスト生成：**
            - 文書作成、編集、要約
            - メール文面、レポート作成
            - 文章の校正・改善
            
            **💻 プログラム生成：**
            - コード作成・修正
            - デバッグ支援
            - 技術文書作成
            
            **🌐 Webページ生成：**
            - HTML/CSS作成
            - レスポンシブデザイン
            - アクセシブルなサイト構築
            """,
            help_type=HelpType.CONTEXTUAL,
            context=HelpContext.JOB_SELECTION,
            keywords=["ジョブ", "選択", "作業種類", "テキスト", "コード", "Web"]
        ))
        
        # モード選択のヘルプ
        self.add_help_item(HelpItem(
            id="mode_selection_guide",
            title="進行モードの選択",
            content="""
            作業の進め方を選択してください：
            
            **🤖 全自動モード：**
            - AIが自動的に作業を進行
            - 最小限のユーザー入力で完了
            - 初心者や効率重視の方におすすめ
            
            **💬 対話モード：**
            - ユーザーとAIが協力して作業
            - 細かい調整や要望の反映が可能
            - カスタマイズ重視の方におすすめ
            
            いつでもモードを切り替えることができます。
            """,
            help_type=HelpType.CONTEXTUAL,
            context=HelpContext.MODE_SELECTION,
            keywords=["モード", "全自動", "対話", "進行方法"]
        ))
        
        # 音声インターフェースのヘルプ
        self.add_help_item(HelpItem(
            id="voice_interface_guide",
            title="音声機能の使い方",
            content="""
            音声機能を使って手軽に操作できます：
            
            **🎤 音声入力：**
            - マイクボタンを押して音声で指示
            - 自然な言葉で要望を伝えられます
            - 「〇〇について説明して」等の指示が可能
            
            **🔊 音声出力：**
            - AIの回答を音声で読み上げ
            - 画面を見なくても内容を確認
            - 読み上げ速度・音量の調整可能
            
            **⚙️ 音声設定：**
            - マイク・スピーカーの選択
            - 音質・感度の調整
            - 言語・方言の設定
            """,
            help_type=HelpType.CONTEXTUAL,
            context=HelpContext.VOICE_INTERFACE,
            keywords=["音声", "マイク", "スピーカー", "読み上げ", "音声入力"]
        ))
        
        # FAQアイテム
        self._add_faq_items()
        
        # チュートリアル初期化
        self._initialize_tutorials()
    
    def _add_faq_items(self):
        """FAQ項目の追加"""
        faqs = [
            {
                "id": "faq_first_use",
                "title": "初めて使用する時は何をすればいい？",
                "content": """
                1. **ホーム画面**で機能概要を確認
                2. **ジョブ選択**で作業タイプを選択
                3. **モード選択**で進行方法を決定
                4. 簡単な要望から始めてみる
                
                不明な点があれば、各画面のヘルプボタン（❓）をクリックしてください。
                """,
                "keywords": ["初回", "使い方", "開始方法", "初心者"]
            },
            {
                "id": "faq_voice_not_working",
                "title": "音声機能が動作しない場合",
                "content": """
                **確認事項：**
                1. マイク・スピーカーが正しく接続されているか
                2. ブラウザでマイクアクセスが許可されているか
                3. 音声設定で正しいデバイスが選択されているか
                4. 音量・感度設定が適切か
                
                **解決方法：**
                - ページを再読み込みしてマイクアクセスを再許可
                - 音声設定画面でデバイステストを実行
                - 他のアプリケーションでマイクが使用されていないか確認
                """,
                "keywords": ["音声", "マイク", "動作しない", "トラブル"]
            },
            {
                "id": "faq_generation_slow",
                "title": "生成処理が遅い場合",
                "content": """
                **原因：**
                - AIモデルの処理負荷
                - ネットワーク接続状況
                - 複雑な要求内容
                
                **改善方法：**
                1. 要求内容を簡潔にする
                2. 段階的に作業を分割する
                3. キャッシュ機能を活用する
                4. 処理中は他の作業を避ける
                
                進行状況は画面上部のプログレスバーで確認できます。
                """,
                "keywords": ["遅い", "処理時間", "パフォーマンス", "速度"]
            }
        ]
        
        for faq in faqs:
            self.add_help_item(HelpItem(
                id=faq["id"],
                title=faq["title"],
                content=faq["content"],
                help_type=HelpType.FAQ,
                context=HelpContext.HOME,  # FAQは全体共通
                keywords=faq["keywords"]
            ))
    
    def _initialize_tutorials(self):
        """チュートリアルの初期化"""
        # 初回ユーザー向けクイックスタート
        quick_start_steps = [
            TutorialStep(
                step_id="welcome",
                title="支援システムへようこそ",
                description="このチュートリアルでは、基本的な使い方をご案内します。",
                action_required=False
            ),
            TutorialStep(
                step_id="job_selection",
                title="ジョブを選択",
                description="まず、どのような作業をしたいかを選択しましょう。「テキスト生成」を選んでみてください。",
                target_element="job_selector",
                action_required=True,
                completion_criteria="job_selected"
            ),
            TutorialStep(
                step_id="mode_selection",
                title="進行モードを選択",
                description="作業の進め方を選択します。初回は「全自動モード」がおすすめです。",
                target_element="mode_selector",
                action_required=True,
                completion_criteria="mode_selected"
            ),
            TutorialStep(
                step_id="input_request",
                title="要望を入力",
                description="テキストエリアに「会議の議事録を作成してください」等、具体的な要望を入力してみましょう。",
                target_element="request_input",
                action_required=True,
                completion_criteria="request_entered"
            ),
            TutorialStep(
                step_id="generate",
                title="生成開始",
                description="「生成開始」ボタンを押すと、AIが作業を開始します。",
                target_element="generate_button",
                action_required=True,
                completion_criteria="generation_started"
            ),
            TutorialStep(
                step_id="completion",
                title="チュートリアル完了",
                description="お疲れ様でした！基本的な操作をマスターしました。他の機能もぜひお試しください。",
                action_required=False
            )
        ]
        
        self.tutorials["quick_start"] = quick_start_steps
    
    def add_help_item(self, help_item: HelpItem):
        """ヘルプアイテムの追加"""
        self.help_items[help_item.id] = help_item
    
    def get_contextual_help(self, context: HelpContext) -> List[HelpItem]:
        """コンテキストに応じたヘルプを取得"""
        return [
            item for item in self.help_items.values()
            if item.context == context and item.help_type == HelpType.CONTEXTUAL
        ]
    
    def get_faq_items(self, search_query: str = "") -> List[HelpItem]:
        """FAQ項目を取得"""
        faq_items = [
            item for item in self.help_items.values()
            if item.help_type == HelpType.FAQ
        ]
        
        if search_query:
            # キーワード検索
            search_query = search_query.lower()
            faq_items = [
                item for item in faq_items
                if (search_query in item.title.lower() or 
                    search_query in item.content.lower() or
                    any(search_query in keyword.lower() for keyword in item.keywords))
            ]
        
        return faq_items
    
    def search_help(self, query: str) -> List[HelpItem]:
        """ヘルプ検索"""
        query = query.lower()
        results = []
        
        for item in self.help_items.values():
            score = 0
            
            # タイトルマッチ（高スコア）
            if query in item.title.lower():
                score += 10
            
            # コンテンツマッチ（中スコア）
            if query in item.content.lower():
                score += 5
            
            # キーワードマッチ（低スコア）
            for keyword in item.keywords:
                if query in keyword.lower():
                    score += 3
            
            if score > 0:
                results.append((item, score))
        
        # スコア順でソート
        results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in results]
    
    def get_tutorial(self, tutorial_id: str) -> List[TutorialStep]:
        """チュートリアルを取得"""
        return self.tutorials.get(tutorial_id, [])
    
    def _load_user_progress(self):
        """ユーザー進捗の読み込み"""
        if 'help_progress' not in st.session_state:
            st.session_state.help_progress = {
                'completed_tutorials': [],
                'dismissed_tips': [],
                'help_preferences': {
                    'show_tooltips': True,
                    'auto_help': True,
                    'tutorial_completed': False
                }
            }
        
        self.user_progress = st.session_state.help_progress
    
    def mark_tutorial_completed(self, tutorial_id: str):
        """チュートリアル完了マーク"""
        if tutorial_id not in self.user_progress['completed_tutorials']:
            self.user_progress['completed_tutorials'].append(tutorial_id)
            st.session_state.help_progress = self.user_progress
    
    def is_tutorial_completed(self, tutorial_id: str) -> bool:
        """チュートリアル完了状況確認"""
        return tutorial_id in self.user_progress['completed_tutorials']
    
    def dismiss_tip(self, tip_id: str):
        """ヒントの非表示設定"""
        if tip_id not in self.user_progress['dismissed_tips']:
            self.user_progress['dismissed_tips'].append(tip_id)
            st.session_state.help_progress = self.user_progress
    
    def is_tip_dismissed(self, tip_id: str) -> bool:
        """ヒント非表示状況確認"""
        return tip_id in self.user_progress['dismissed_tips']

class HelpUIComponents:
    """ヘルプUI コンポーネント"""
    
    def __init__(self, help_manager: HelpSystemManager):
        self.help_manager = help_manager
    
    def render_help_button(self, context: HelpContext, position="right"):
        """ヘルプボタンの表示"""
        if position == "right":
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("❓ ヘルプ", key=f"help_btn_{context.value}"):
                    self._show_contextual_help(context)
        else:
            if st.button("❓ ヘルプ", key=f"help_btn_{context.value}"):
                self._show_contextual_help(context)
    
    def _show_contextual_help(self, context: HelpContext):
        """コンテキスト依存ヘルプの表示"""
        help_items = self.help_manager.get_contextual_help(context)
        
        if help_items:
            st.info("💡 **この画面のヘルプ**")
            for item in help_items:
                with st.expander(f"📖 {item.title}"):
                    st.markdown(item.content)
        else:
            st.info("この画面のヘルプはまだ準備中です。")
    
    def render_tooltip(self, text: str, help_text: str):
        """ツールチップの表示"""
        st.help(help_text)
        return text
    
    def render_quick_tip(self, tip_id: str, title: str, content: str, dismissible: bool = True):
        """クイックヒントの表示"""
        if self.help_manager.is_tip_dismissed(tip_id):
            return
        
        with st.container():
            col1, col2 = st.columns([10, 1]) if dismissible else st.columns([1])
            
            with col1:
                st.info(f"💡 **{title}**\n\n{content}")
            
            if dismissible:
                with col2:
                    if st.button("×", key=f"dismiss_{tip_id}"):
                        self.help_manager.dismiss_tip(tip_id)
                        st.rerun()
    
    def render_faq_section(self):
        """FAQ セクションの表示"""
        st.subheader("❓ よくある質問")
        
        # 検索ボックス
        search_query = st.text_input("🔍 質問を検索", placeholder="キーワードを入力...")
        
        # FAQ表示
        faq_items = self.help_manager.get_faq_items(search_query)
        
        if faq_items:
            for item in faq_items:
                with st.expander(f"❓ {item.title}"):
                    st.markdown(item.content)
        else:
            if search_query:
                st.warning("該当するFAQが見つかりませんでした。")
            else:
                st.info("FAQを読み込み中...")
    
    def render_tutorial_launcher(self):
        """チュートリアル起動UI"""
        st.subheader("🎓 チュートリアル")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("初めての方向けに使い方をガイドします。")
        
        with col2:
            if st.button("▶️ 開始", key="start_tutorial"):
                self._start_tutorial("quick_start")
    
    def _start_tutorial(self, tutorial_id: str):
        """チュートリアル開始"""
        st.session_state.active_tutorial = tutorial_id
        st.session_state.tutorial_step = 0
        st.rerun()
    
    def render_active_tutorial(self):
        """アクティブチュートリアルの表示"""
        if 'active_tutorial' not in st.session_state:
            return
        
        tutorial_id = st.session_state.active_tutorial
        step_index = st.session_state.get('tutorial_step', 0)
        
        steps = self.help_manager.get_tutorial(tutorial_id)
        if not steps or step_index >= len(steps):
            return
        
        current_step = steps[step_index]
        
        # チュートリアルUI
        with st.container():
            st.info(f"🎓 **チュートリアル（{step_index + 1}/{len(steps)}）**")
            
            with st.expander(f"📝 {current_step.title}", expanded=True):
                st.write(current_step.description)
                
                # ヒント表示
                if current_step.hints:
                    with st.expander("💡 ヒント"):
                        for hint in current_step.hints:
                            st.write(f"• {hint}")
                
                # ナビゲーションボタン
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if step_index > 0:
                        if st.button("⬅️ 前へ", key="tutorial_prev"):
                            st.session_state.tutorial_step = step_index - 1
                            st.rerun()
                
                with col2:
                    if st.button("❌ 終了", key="tutorial_exit"):
                        self._end_tutorial()
                
                with col3:
                    if step_index < len(steps) - 1:
                        if st.button("➡️ 次へ", key="tutorial_next"):
                            st.session_state.tutorial_step = step_index + 1
                            st.rerun()
                    else:
                        if st.button("✅ 完了", key="tutorial_complete"):
                            self.help_manager.mark_tutorial_completed(tutorial_id)
                            self._end_tutorial()
    
    def _end_tutorial(self):
        """チュートリアル終了"""
        if 'active_tutorial' in st.session_state:
            del st.session_state.active_tutorial
        if 'tutorial_step' in st.session_state:
            del st.session_state.tutorial_step
        st.rerun()
    
    def render_help_search(self):
        """ヘルプ検索UI"""
        st.subheader("🔍 ヘルプ検索")
        
        search_query = st.text_input("検索キーワード", placeholder="知りたいことを入力...")
        
        if search_query:
            results = self.help_manager.search_help(search_query)
            
            if results:
                st.success(f"💡 {len(results)}件の結果が見つかりました")
                
                for item in results[:5]:  # 上位5件表示
                    with st.expander(f"📖 {item.title}"):
                        st.markdown(item.content)
                        
                        # タグ表示
                        if item.keywords:
                            st.write("**関連キーワード:**")
                            tags = " • ".join([f"`{keyword}`" for keyword in item.keywords[:5]])
                            st.write(tags)
            else:
                st.warning("該当するヘルプが見つかりませんでした。")
                st.info("💡 **検索のコツ:**\n- 具体的なキーワードを使用\n- 「音声」「生成」「エラー」等の機能名で検索\n- 困っている症状を具体的に入力")

# ヘルプシステムのグローバルインスタンス
_help_manager_instance = None
_help_ui_instance = None

def get_help_manager() -> HelpSystemManager:
    """ヘルプマネージャーのシングルトンインスタンス取得"""
    global _help_manager_instance
    if _help_manager_instance is None:
        _help_manager_instance = HelpSystemManager()
    return _help_manager_instance

def get_help_ui() -> HelpUIComponents:
    """ヘルプUIコンポーネントのシングルトンインスタンス取得"""
    global _help_ui_instance
    if _help_ui_instance is None:
        _help_ui_instance = HelpUIComponents(get_help_manager())
    return _help_ui_instance

# 便利関数
def show_contextual_help(context: HelpContext):
    """コンテキスト依存ヘルプを表示"""
    help_ui = get_help_ui()
    help_ui._show_contextual_help(context)

def show_quick_tip(tip_id: str, title: str, content: str, dismissible: bool = True):
    """クイックヒントを表示"""
    help_ui = get_help_ui()
    help_ui.render_quick_tip(tip_id, title, content, dismissible)

def show_help_button(context: HelpContext, position="right"):
    """ヘルプボタンを表示"""
    help_ui = get_help_ui()
    help_ui.render_help_button(context, position)
