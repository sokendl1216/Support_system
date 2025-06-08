"""
音声入出力対応UIコンポーネント
Streamlit用の音声インターフェースコンポーネント

機能:
- 音声認識UI（マイクボタン）
- 音声合成UI（スピーカーボタン）
- 音声設定UI
- 音声ステータス表示
- 音声対話ワークフロー
"""

import asyncio
import streamlit as st
from typing import Optional, Dict, Any, Callable
import logging

from .audio_handler import (
    audio_interface, 
    initialize_audio, 
    speak_text, 
    listen_for_speech, 
    voice_interaction,
    cleanup_audio,
    AUDIO_AVAILABLE
)

# ログ設定
logger = logging.getLogger(__name__)


class AudioUIComponents:
    """音声UI統合コンポーネントクラス"""
    
    @staticmethod
    def render_audio_status_indicator() -> Dict[str, Any]:
        """音声システム状態表示"""
        status = audio_interface.get_status()
        
        with st.container():
            st.markdown("### 🎵 音声システム状態")
            
            # 音声システム利用可能性
            if status['audio_available']:
                st.success("✅ 音声システム利用可能")
            else:
                st.error("❌ 音声システム利用不可（ライブラリが見つかりません）")
            
            # 初期化状態
            if status['initialized']:
                st.info("🔧 音声システム初期化済み")
            else:
                st.warning("⚠️ 音声システム未初期化")
            
            # 動作状態
            col1, col2 = st.columns(2)
            
            with col1:
                if status['listening']:
                    st.markdown("🎤 **音声認識中**")
                else:
                    st.markdown("🎤 音声認識停止中")
            
            with col2:
                if status['speaking']:
                    st.markdown("🔊 **音声出力中**")
                else:
                    st.markdown("🔊 音声出力停止中")
        
        return status
    
    @staticmethod
    def render_audio_controls() -> Dict[str, bool]:
        """音声制御ボタン群"""
        controls = {
            'initialize': False,
            'start_listening': False,
            'stop_listening': False,
            'stop_speaking': False,
            'cleanup': False
        }
        
        with st.container():
            st.markdown("### 🎛️ 音声制御")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                controls['initialize'] = st.button(
                    "🔧 初期化",
                    help="音声システムを初期化します"
                )
            
            with col2:
                controls['start_listening'] = st.button(
                    "🎤 録音開始",
                    help="音声認識を開始します"
                )
            
            with col3:
                controls['stop_listening'] = st.button(
                    "⏹️ 録音停止",
                    help="音声認識を停止します"
                )
            
            with col4:
                controls['stop_speaking'] = st.button(
                    "🔇 読み上げ停止",
                    help="音声出力を停止します"
                )
            
            with col5:
                controls['cleanup'] = st.button(
                    "🧹 クリーンアップ",
                    help="音声システムをクリーンアップします"
                )
        
        return controls
    
    @staticmethod
    def render_voice_input_button() -> bool:
        """音声入力ボタン"""
        return st.button(
            "🎤 音声で入力",
            help="マイクをクリックして音声で入力できます"
        )
    
    @staticmethod
    def render_voice_output_button(text: str) -> bool:
        """音声出力ボタン"""
        if not text.strip():
            return False
            
        return st.button(
            "🔊 読み上げ",
            help="内容を音声で読み上げます"
        )
    
    @staticmethod
    def render_audio_settings() -> Dict[str, Any]:
        """音声設定UI"""
        settings = {}
        
        with st.expander("🔧 音声設定"):
            # 音声認識設定
            st.markdown("#### 音声認識設定")
            settings['recognition_enabled'] = st.checkbox(
                "音声認識を有効にする",
                value=True,
                help="音声からテキストへの変換機能"
            )
            
            settings['noise_reduction'] = st.checkbox(
                "ノイズ除去を有効にする",
                value=True,
                help="背景雑音の除去機能"
            )
            
            # 音声合成設定
            st.markdown("#### 音声合成設定")
            settings['tts_enabled'] = st.checkbox(
                "音声読み上げを有効にする",
                value=True,
                help="テキストから音声への変換機能"
            )
            
            settings['speech_rate'] = st.slider(
                "読み上げ速度",
                min_value=50,
                max_value=300,
                value=150,
                step=10,
                help="音声の読み上げ速度（単語/分）"
            )
            
            settings['speech_volume'] = st.slider(
                "音量",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="音声出力の音量レベル"
            )
            
            # 自動機能設定
            st.markdown("#### 自動機能設定")
            settings['auto_read_responses'] = st.checkbox(
                "AI応答を自動読み上げ",
                value=False,
                help="AI応答を自動的に音声で読み上げます"
            )
            
            settings['auto_listen_after_response'] = st.checkbox(
                "応答後に自動音声入力",
                value=False,
                help="AI応答後に自動的に音声入力を開始します"
            )
        
        return settings
    
    @staticmethod
    def render_voice_interaction_form() -> Optional[str]:
        """音声対話フォーム"""
        user_input = None
        
        with st.form("voice_interaction_form"):
            st.markdown("### 🗣️ 音声対話")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                prompt = st.text_input(
                    "音声プロンプト（任意）",
                    placeholder="音声で質問してください...",
                    help="先に読み上げるメッセージ（省略可能）"
                )
            
            with col2:
                start_interaction = st.form_submit_button(
                    "🎙️ 対話開始",
                    help="音声対話を開始します"
                )
            
            if start_interaction:
                with st.spinner("音声対話を実行中..."):
                    try:
                        # 音声対話実行
                        result = asyncio.run(voice_interaction(prompt or ""))
                        if result:
                            user_input = result
                            st.success(f"認識結果: {result}")
                        else:
                            st.warning("音声が認識できませんでした")
                    except Exception as e:
                        st.error(f"音声対話エラー: {e}")
        
        return user_input
    
    @staticmethod
    def render_text_to_speech_form() -> bool:
        """テキスト読み上げフォーム"""
        spoken = False
        
        with st.form("text_to_speech_form"):
            st.markdown("### 📢 テキスト読み上げ")
            
            text_input = st.text_area(
                "読み上げテキスト",
                placeholder="読み上げたいテキストを入力してください...",
                height=100
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                speak_normal = st.form_submit_button(
                    "🔊 通常読み上げ",
                    help="テキストを通常の優先度で読み上げます"
                )
            
            with col2:
                speak_priority = st.form_submit_button(
                    "⚡ 優先読み上げ",
                    help="現在の読み上げを中断して優先的に読み上げます"
                )
            
            if (speak_normal or speak_priority) and text_input.strip():
                with st.spinner("音声合成中..."):
                    try:
                        success = asyncio.run(speak_text(text_input, priority=speak_priority))
                        if success:
                            st.success("読み上げを開始しました")
                            spoken = True
                        else:
                            st.error("読み上げに失敗しました")
                    except Exception as e:
                        st.error(f"音声合成エラー: {e}")
        
        return spoken


class VoiceAssistantWorkflow:
    """音声アシスタントワークフロー管理"""
    
    @staticmethod
    def render_voice_assistant_interface():
        """音声アシスタント統合インターフェース"""
        st.markdown("## 🎤 音声アシスタント")
        
        # 音声システム状態確認
        status = AudioUIComponents.render_audio_status_indicator()
        
        if not status['audio_available']:
            st.error("""
            音声機能を使用するには、以下のライブラリをインストールしてください：
            ```bash
            pip install vosk pyaudio pyttsx3 numpy scipy
            ```
            """)
            return
        
        # 音声システム初期化確認
        if not status['initialized']:
            st.warning("音声システムが初期化されていません")
            if st.button("🔧 今すぐ初期化"):
                with st.spinner("音声システムを初期化中..."):
                    try:
                        success = asyncio.run(initialize_audio())
                        if success:
                            st.success("音声システムを初期化しました")
                            st.experimental_rerun()
                        else:
                            st.error("音声システムの初期化に失敗しました")
                    except Exception as e:
                        st.error(f"初期化エラー: {e}")
            return
        
        # 音声制御パネル
        controls = AudioUIComponents.render_audio_controls()
        
        # 制御処理実行
        VoiceAssistantWorkflow._handle_audio_controls(controls)
        
        st.divider()
        
        # 音声対話フォーム
        voice_input = AudioUIComponents.render_voice_interaction_form()
        if voice_input:
            st.session_state['voice_input'] = voice_input
        
        st.divider()
        
        # テキスト読み上げフォーム
        AudioUIComponents.render_text_to_speech_form()
        
        st.divider()
        
        # 音声設定
        settings = AudioUIComponents.render_audio_settings()
        st.session_state['audio_settings'] = settings
    
    @staticmethod
    def _handle_audio_controls(controls: Dict[str, bool]):
        """音声制御処理"""
        try:
            if controls['initialize']:
                with st.spinner("音声システムを初期化中..."):
                    success = asyncio.run(initialize_audio())
                    if success:
                        st.success("音声システムを初期化しました")
                    else:
                        st.error("音声システムの初期化に失敗しました")
            
            if controls['start_listening']:
                with st.spinner("音声認識を開始中..."):
                    asyncio.run(audio_interface.start_listening())
                    st.info("音声認識を開始しました")
            
            if controls['stop_listening']:
                audio_interface.stop_listening()
                st.info("音声認識を停止しました")
            
            if controls['stop_speaking']:
                audio_interface.stop_speaking()
                st.info("音声出力を停止しました")
            
            if controls['cleanup']:
                cleanup_audio()
                st.info("音声システムをクリーンアップしました")
                
        except Exception as e:
            st.error(f"音声制御エラー: {e}")


# 便利関数
def render_inline_voice_button(text: str, button_text: str = "🔊") -> bool:
    """インライン音声ボタン"""
    if st.button(button_text, key=f"voice_{hash(text)}"):
        try:
            asyncio.run(speak_text(text))
            return True
        except Exception as e:
            st.error(f"音声出力エラー: {e}")
            return False
    return False


def render_voice_input_widget(key: str, placeholder: str = "音声で入力...") -> Optional[str]:
    """音声入力ウィジェット"""
    col1, col2 = st.columns([4, 1])
    
    with col1:
        text_input = st.text_input(
            "入力",
            key=f"{key}_text",
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("🎤", key=f"{key}_voice"):
            with st.spinner("音声認識中..."):
                try:
                    result = asyncio.run(listen_for_speech())
                    if result:
                        st.session_state[f"{key}_text"] = result
                        st.experimental_rerun()
                    else:
                        st.warning("音声が認識できませんでした")
                except Exception as e:
                    st.error(f"音声認識エラー: {e}")
    
    return text_input


def auto_speak_if_enabled(text: str):
    """自動音声出力（設定が有効な場合）"""
    if st.session_state.get('audio_settings', {}).get('auto_read_responses', False):
        try:
            asyncio.run(speak_text(text))
        except Exception as e:
            logger.error(f"自動音声出力エラー: {e}")


def get_voice_input_if_enabled() -> Optional[str]:
    """自動音声入力（設定が有効な場合）"""
    if st.session_state.get('audio_settings', {}).get('auto_listen_after_response', False):
        try:
            return asyncio.run(listen_for_speech())
        except Exception as e:
            logger.error(f"自動音声入力エラー: {e}")
            return None
    return None
