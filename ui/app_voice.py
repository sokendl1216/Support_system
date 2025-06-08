"""
音声対応支援システムメインアプリケーション
Vosk/Espeak音声入出力統合版

機能:
- 音声認識による入力
- 音声合成による出力
- 音声対話ワークフロー
- 既存UI機能との統合
- アクセシビリティ対応
"""

import streamlit as st
import asyncio
import logging
from pathlib import Path
import sys

# パス設定
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent))

# コンポーネントインポート
from components.audio_ui import (
    AudioUIComponents,
    VoiceAssistantWorkflow,
    render_inline_voice_button,
    render_voice_input_widget,
    auto_speak_if_enabled,
    get_voice_input_if_enabled
)
from components.audio_handler import initialize_audio, AUDIO_AVAILABLE

# 多言語対応インポート
try:
    from i18n.language_manager import LanguageManager
    from i18n.translator import Translator
    from components.multilingual import MultilingualComponents
    MULTILINGUAL_AVAILABLE = True
except ImportError:
    MULTILINGUAL_AVAILABLE = False
    logging.warning("多言語対応コンポーネントが利用できません")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceEnabledApp:
    """音声対応支援システムアプリケーション"""
    
    def __init__(self):
        self.initialize_session_state()
        self.setup_page_config()
        
        # 多言語対応初期化
        if MULTILINGUAL_AVAILABLE:
            self.language_manager = LanguageManager()
            self.translator = Translator(self.language_manager)
        else:
            self.language_manager = None
            self.translator = None
    
    def initialize_session_state(self):
        """セッション状態初期化"""
        if 'audio_initialized' not in st.session_state:
            st.session_state.audio_initialized = False
        
        if 'voice_input' not in st.session_state:
            st.session_state.voice_input = ""
        
        if 'audio_settings' not in st.session_state:
            st.session_state.audio_settings = {
                'recognition_enabled': True,
                'tts_enabled': True,
                'auto_read_responses': False,
                'auto_listen_after_response': False,
                'speech_rate': 150,
                'speech_volume': 0.7,
                'noise_reduction': True
            }
        
        if 'current_language' not in st.session_state:
            st.session_state.current_language = 'ja'
    
    def setup_page_config(self):
        """ページ設定"""
        st.set_page_config(
            page_title="音声対応支援システム",
            page_icon="🎤",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_header(self):
        """ヘッダー描画"""
        # 多言語対応タイトル
        if self.translator:
            title = self.translator.get("app.title_voice", "音声対応支援システム")
            subtitle = self.translator.get("app.subtitle_voice", "音声入出力で簡単操作")
        else:
            title = "音声対応支援システム"
            subtitle = "音声入出力で簡単操作"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #1f77b4; margin-bottom: 0.5rem;'>
                🎤 {title}
            </h1>
            <p style='color: #666; font-size: 1.2rem; margin: 0;'>
                {subtitle}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # インライン音声読み上げボタン
        if render_inline_voice_button(f"{title} - {subtitle}", "🔊 タイトル読み上げ"):
            st.success("タイトルを読み上げました")
    
    def render_sidebar(self):
        """サイドバー描画"""
        with st.sidebar:
            st.markdown("## 🎛️ 設定・制御")
            
            # 多言語選択（利用可能な場合）
            if MULTILINGUAL_AVAILABLE and self.language_manager:
                MultilingualComponents.render_language_selector()
            
            st.divider()
            
            # 音声システム状態
            status = AudioUIComponents.render_audio_status_indicator()
            
            st.divider()
            
            # 音声制御
            controls = AudioUIComponents.render_audio_controls()
            self._handle_audio_controls(controls)
            
            st.divider()
            
            # 音声設定
            settings = AudioUIComponents.render_audio_settings()
            st.session_state.audio_settings.update(settings)
            
            st.divider()
            
            # クイックアクション
            self.render_quick_actions()
    
    def _handle_audio_controls(self, controls):
        """音声制御処理"""
        try:
            if controls['initialize']:
                self._initialize_audio_system()
            
            if controls['cleanup']:
                self._cleanup_audio_system()
                
        except Exception as e:
            st.error(f"音声制御エラー: {e}")
    
    def _initialize_audio_system(self):
        """音声システム初期化"""
        with st.spinner("音声システムを初期化中..."):
            try:
                success = asyncio.run(initialize_audio())
                if success:
                    st.session_state.audio_initialized = True
                    st.success("音声システムを初期化しました")
                    
                    # 初期化完了音声通知
                    if st.session_state.audio_settings.get('tts_enabled', True):
                        asyncio.run(auto_speak_if_enabled("音声システムの初期化が完了しました"))
                else:
                    st.error("音声システムの初期化に失敗しました")
            except Exception as e:
                st.error(f"初期化エラー: {e}")
    
    def _cleanup_audio_system(self):
        """音声システムクリーンアップ"""
        try:
            from components.audio_handler import cleanup_audio
            cleanup_audio()
            st.session_state.audio_initialized = False
            st.info("音声システムをクリーンアップしました")
        except Exception as e:
            st.error(f"クリーンアップエラー: {e}")
    
    def render_quick_actions(self):
        """クイックアクション"""
        st.markdown("### ⚡ クイックアクション")
        
        if st.button("🎤 即座に音声入力", use_container_width=True):
            self._quick_voice_input()
        
        if st.button("🔊 状態読み上げ", use_container_width=True):
            self._announce_system_status()
        
        if st.button("❓ 音声ヘルプ", use_container_width=True):
            self._voice_help()
    
    def _quick_voice_input(self):
        """クイック音声入力"""
        with st.spinner("音声を入力してください..."):
            try:
                from components.audio_handler import listen_for_speech
                result = asyncio.run(listen_for_speech())
                if result:
                    st.session_state.voice_input = result
                    st.success(f"認識結果: {result}")
                else:
                    st.warning("音声が認識できませんでした")
            except Exception as e:
                st.error(f"音声入力エラー: {e}")
    
    def _announce_system_status(self):
        """システム状態音声通知"""
        try:
            from components.audio_handler import audio_interface, speak_text
            status = audio_interface.get_status()
            
            status_text = "システム状態をお知らせします。"
            
            if status['audio_available']:
                status_text += "音声システムは利用可能です。"
            else:
                status_text += "音声システムは利用できません。"
            
            if status['initialized']:
                status_text += "音声システムは初期化済みです。"
            else:
                status_text += "音声システムは未初期化です。"
            
            if status['listening']:
                status_text += "現在音声認識中です。"
            
            if status['speaking']:
                status_text += "現在音声出力中です。"
            
            asyncio.run(speak_text(status_text, priority=True))
            
        except Exception as e:
            st.error(f"状態読み上げエラー: {e}")
    
    def _voice_help(self):
        """音声ヘルプ"""
        help_text = """
        音声支援システムの使い方をご説明します。
        
        マイクボタンをクリックすると音声入力ができます。
        スピーカーボタンをクリックすると読み上げができます。
        サイドバーで音声設定を変更できます。
        
        音声コマンドで操作することも可能です。
        """
        
        try:
            from components.audio_handler import speak_text
            asyncio.run(speak_text(help_text, priority=True))
        except Exception as e:
            st.error(f"ヘルプ読み上げエラー: {e}")
    
    def render_main_content(self):
        """メインコンテンツ描画"""
        # 音声対話セクション
        self.render_voice_interaction_section()
        
        st.divider()
        
        # 音声入力フォーム
        self.render_voice_input_form()
        
        st.divider()
        
        # テキスト読み上げセクション
        self.render_text_to_speech_section()
        
        st.divider()
        
        # AI支援機能（従来機能）
        self.render_ai_assistance_section()
    
    def render_voice_interaction_section(self):
        """音声対話セクション"""
        st.markdown("## 🗣️ 音声対話")
        
        if not AUDIO_AVAILABLE:
            st.warning("音声機能を使用するには、音声ライブラリのインストールが必要です")
            return
        
        # 音声対話フォーム
        user_input = AudioUIComponents.render_voice_interaction_form()
        
        if user_input:
            # AI応答処理（簡易版）
            with st.spinner("AI応答を生成中..."):
                try:
                    # 簡易AI応答（実際にはLLMサービスを呼び出し）
                    ai_response = f"音声入力「{user_input}」を受け取りました。具体的な処理を実行します。"
                    
                    st.success("AI応答:")
                    st.write(ai_response)
                    
                    # 自動読み上げ（設定に応じて）
                    auto_speak_if_enabled(ai_response)
                    
                    # 音声読み上げボタン
                    if render_inline_voice_button(ai_response, "🔊 応答を読み上げ"):
                        st.info("応答を読み上げました")
                    
                except Exception as e:
                    st.error(f"AI応答エラー: {e}")
    
    def render_voice_input_form(self):
        """音声入力フォーム"""
        st.markdown("## 🎤 音声入力フォーム")
        
        with st.form("voice_input_form"):
            st.markdown("### 入力内容")
            
            # 音声入力ウィジェット
            text_input = render_voice_input_widget(
                "main_input",
                "テキスト入力または音声ボタンで入力してください..."
            )
            
            # 送信ボタン
            submitted = st.form_submit_button("📤 送信", use_container_width=True)
            
            if submitted and text_input:
                st.success(f"入力内容: {text_input}")
                
                # 確認読み上げ
                confirmation = f"入力内容を確認します。{text_input}"
                if render_inline_voice_button(confirmation, "🔊 入力内容確認"):
                    st.info("入力内容を読み上げました")
    
    def render_text_to_speech_section(self):
        """テキスト読み上げセクション"""
        st.markdown("## 📢 テキスト読み上げ")
        AudioUIComponents.render_text_to_speech_form()
    
    def render_ai_assistance_section(self):
        """AI支援機能セクション"""
        st.markdown("## 🤖 AI支援機能")
        
        tab1, tab2, tab3 = st.tabs(["📝 テキスト生成", "💻 コード生成", "🌐 ウェブページ生成"])
        
        with tab1:
            self.render_text_generation()
        
        with tab2:
            self.render_code_generation()
        
        with tab3:
            self.render_webpage_generation()
    
    def render_text_generation(self):
        """テキスト生成機能"""
        st.markdown("### テキスト生成")
        
        # 音声入力対応プロンプト
        prompt = render_voice_input_widget(
            "text_gen_prompt",
            "生成したいテキストの内容を説明してください..."
        )
        
        if st.button("✨ テキスト生成", use_container_width=True) and prompt:
            with st.spinner("テキストを生成中..."):
                # 簡易テキスト生成（実際にはLLMサービスを使用）
                generated_text = f"""
                生成されたテキスト例:
                
                ユーザーのリクエスト「{prompt}」に基づいて、
                以下のテキストを生成しました。
                
                これは音声対応テキスト生成システムのデモです。
                実際の運用では、高度なAIモデルによって
                より詳細で有用なテキストが生成されます。
                """
                
                st.success("生成完了:")
                st.write(generated_text)
                
                # 音声読み上げボタン
                if render_inline_voice_button(generated_text, "🔊 生成結果を読み上げ"):
                    st.info("生成結果を読み上げました")
    
    def render_code_generation(self):
        """コード生成機能"""
        st.markdown("### コード生成")
        
        # 音声入力対応プロンプト
        code_prompt = render_voice_input_widget(
            "code_gen_prompt",
            "作成したいプログラムの内容を説明してください..."
        )
        
        language = st.selectbox(
            "プログラミング言語",
            ["Python", "JavaScript", "HTML/CSS", "Java", "C++"],
            index=0
        )
        
        if st.button("⚡ コード生成", use_container_width=True) and code_prompt:
            with st.spinner("コードを生成中..."):
                # 簡易コード生成例
                generated_code = f"""
# {language}コード例
# プロンプト: {code_prompt}

def example_function():
    '''
    音声入力で要求された機能: {code_prompt}
    '''
    print("Hello, Voice-Enabled AI System!")
    return "Generated by voice input"

if __name__ == "__main__":
    result = example_function()
    print(result)
                """
                
                st.success("コード生成完了:")
                st.code(generated_code, language=language.lower())
                
                # 音声説明
                explanation = f"{language}でのコード生成が完了しました。{code_prompt}の機能を実装したコードです。"
                if render_inline_voice_button(explanation, "🔊 コード説明"):
                    st.info("コードの説明を読み上げました")
    
    def render_webpage_generation(self):
        """ウェブページ生成機能"""
        st.markdown("### ウェブページ生成")
        
        # 音声入力対応プロンプト
        web_prompt = render_voice_input_widget(
            "web_gen_prompt",
            "作成したいウェブページの内容を説明してください..."
        )
        
        if st.button("🌟 ページ生成", use_container_width=True) and web_prompt:
            with st.spinner("ウェブページを生成中..."):
                # 簡易HTML生成例
                generated_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>音声生成ページ</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2rem; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #1f77b4; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>音声生成ページ</h1>
        <p>要求内容: {web_prompt}</p>
        <p>このページは音声入力により生成されました。</p>
        <button onclick="alert('音声対応システムで生成!')">クリック</button>
    </div>
</body>
</html>
                """
                
                st.success("ウェブページ生成完了:")
                st.code(generated_html, language="html")
                
                # プレビュー
                with st.expander("📱 プレビュー"):
                    st.html(generated_html)
                
                # 音声説明
                explanation = f"ウェブページの生成が完了しました。{web_prompt}の内容でページを作成しました。"
                if render_inline_voice_button(explanation, "🔊 ページ説明"):
                    st.info("ページの説明を読み上げました")
    
    def render_footer(self):
        """フッター描画"""
        st.divider()
        
        footer_text = """
        ### 🎤 音声対応支援システム
        
        **特徴:**
        - Vosk音声認識による高精度音声入力
        - Espeak音声合成による自然な読み上げ
        - リアルタイム音声対話
        - アクセシビリティ対応
        - 完全オープンソース・無料
        
        **対応機能:**
        - 音声でのテキスト入力
        - AI生成結果の音声読み上げ
        - 音声コマンドによる操作
        - 多言語音声対応（拡張可能）
        """
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(footer_text)
        
        with col2:
            if render_inline_voice_button(footer_text, "🔊 システム説明"):
                st.info("システム説明を読み上げました")
    
    def run(self):
        """アプリケーション実行"""
        try:
            # ヘッダー
            self.render_header()
            
            # サイドバー
            self.render_sidebar()
            
            # メインコンテンツ
            self.render_main_content()
            
            # フッター
            self.render_footer()
            
        except Exception as e:
            st.error(f"アプリケーションエラー: {e}")
            logger.error(f"Application error: {e}", exc_info=True)


def main():
    """メイン関数"""
    try:
        app = VoiceEnabledApp()
        app.run()
    except Exception as e:
        st.error(f"起動エラー: {e}")
        logger.error(f"Startup error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
