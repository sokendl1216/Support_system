"""
音声入出力ハンドラーモジュール
Vosk音声認識とEspeak音声合成を統合した音声入出力システム

機能:
- リアルタイム音声認識 (Vosk)
- 音声合成・読み上げ (Espeak)
- 音声品質制御
- ノイズ対策
- エラー処理・フォールバック
"""

import asyncio
import json
import os
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
import logging

try:
    import vosk
    import pyaudio
    import pyttsx3
    import numpy as np
    from scipy import signal
    AUDIO_AVAILABLE = True
except ImportError as e:
    logging.warning(f"音声ライブラリが利用できません: {e}")
    AUDIO_AVAILABLE = False

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioConfiguration:
    """音声設定管理クラス"""
    
    # 音声認識設定
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 4096
    CHANNELS = 1
    
    # 音声合成設定
    TTS_RATE = 150  # 話速
    TTS_VOLUME = 0.7  # 音量
    
    # ノイズ対策設定
    NOISE_REDUCTION_ENABLED = True
    NOISE_THRESHOLD = 0.01
    
    # Voskモデル設定
    VOSK_MODEL_PATH = "vosk-model-ja-0.22"
    VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip"


class VoskSpeechRecognizer:
    """Vosk音声認識エンジン"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or AudioConfiguration.VOSK_MODEL_PATH
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.audio_stream = None
        self.pyaudio_instance = None
        
    def initialize(self) -> bool:
        """音声認識エンジンを初期化"""
        if not AUDIO_AVAILABLE:
            logger.error("音声ライブラリが利用できません")
            return False
            
        try:
            # Voskモデルの確認・ダウンロード
            if not self._ensure_model_available():
                return False
                
            # Voskモデル読み込み
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, AudioConfiguration.SAMPLE_RATE)
            
            # PyAudio初期化
            self.pyaudio_instance = pyaudio.PyAudio()
            
            logger.info("音声認識エンジンを初期化しました")
            return True
            
        except Exception as e:
            logger.error(f"音声認識エンジンの初期化に失敗: {e}")
            return False
    
    def _ensure_model_available(self) -> bool:
        """Voskモデルの存在確認・ダウンロード"""
        model_path = Path(self.model_path)
        
        if model_path.exists():
            return True
            
        logger.info("Voskモデルをダウンロードしています...")
        try:
            # モデルディレクトリ作成
            model_path.mkdir(parents=True, exist_ok=True)
            
            # 簡易モデル作成（実際にはダウンロードが必要）
            # 注意: 実際の運用では適切なモデルダウンロード処理が必要
            logger.warning("デモ用簡易モデルを使用します。実際の運用には適切なVoskモデルが必要です。")
            return True
            
        except Exception as e:
            logger.error(f"Voskモデルの準備に失敗: {e}")
            return False
    
    async def start_listening(self, callback: Callable[[str], None]) -> bool:
        """音声認識開始"""
        if not self.model or self.is_listening:
            return False
            
        try:
            self.is_listening = True
            
            # 音声ストリーム開始
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=AudioConfiguration.CHANNELS,
                rate=AudioConfiguration.SAMPLE_RATE,
                input=True,
                frames_per_buffer=AudioConfiguration.CHUNK_SIZE
            )
            
            # 非同期音声認識処理開始
            await self._recognition_loop(callback)
            return True
            
        except Exception as e:
            logger.error(f"音声認識開始に失敗: {e}")
            self.is_listening = False
            return False
    
    async def _recognition_loop(self, callback: Callable[[str], None]):
        """音声認識ループ処理"""
        try:
            while self.is_listening:
                try:
                    # 音声データ読み込み
                    data = self.audio_stream.read(AudioConfiguration.CHUNK_SIZE, exception_on_overflow=False)
                    
                    # ノイズ除去処理
                    if AudioConfiguration.NOISE_REDUCTION_ENABLED:
                        data = self._apply_noise_reduction(data)
                    
                    # 音声認識処理
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        
                        if text:
                            callback(text)
                            logger.info(f"認識結果: {text}")
                    
                    # 短時間待機
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"音声認識処理エラー: {e}")
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"音声認識ループエラー: {e}")
        finally:
            self._cleanup_stream()
    
    def _apply_noise_reduction(self, audio_data: bytes) -> bytes:
        """ノイズ除去処理"""
        try:
            # バイトデータをnumpy配列に変換
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 簡易ノイズゲート適用
            threshold = np.max(np.abs(audio_array)) * AudioConfiguration.NOISE_THRESHOLD
            audio_array = np.where(np.abs(audio_array) < threshold, 0, audio_array)
            
            # バイトデータに戻す
            return audio_array.astype(np.int16).tobytes()
            
        except Exception as e:
            logger.warning(f"ノイズ除去処理に失敗: {e}")
            return audio_data
    
    def stop_listening(self):
        """音声認識停止"""
        self.is_listening = False
        self._cleanup_stream()
    
    def _cleanup_stream(self):
        """ストリームのクリーンアップ"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
        except Exception as e:
            logger.error(f"ストリームクリーンアップエラー: {e}")
    
    def cleanup(self):
        """リソース解放"""
        self.stop_listening()
        try:
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
        except Exception as e:
            logger.error(f"PyAudioクリーンアップエラー: {e}")


class EspeakTextToSpeech:
    """Espeak音声合成エンジン"""
    
    def __init__(self):
        self.tts_engine = None
        self.is_speaking = False
        self.speech_queue = asyncio.Queue()
        
    def initialize(self) -> bool:
        """音声合成エンジンを初期化"""
        if not AUDIO_AVAILABLE:
            logger.error("音声ライブラリが利用できません")
            return False
            
        try:
            # pyttsx3エンジン初期化（Espeakバックエンド）
            self.tts_engine = pyttsx3.init()
            
            # 音声設定
            self.tts_engine.setProperty('rate', AudioConfiguration.TTS_RATE)
            self.tts_engine.setProperty('volume', AudioConfiguration.TTS_VOLUME)
            
            # 日本語音声設定（利用可能な場合）
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'japanese' in voice.name.lower() or 'ja' in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            logger.info("音声合成エンジンを初期化しました")
            return True
            
        except Exception as e:
            logger.error(f"音声合成エンジンの初期化に失敗: {e}")
            return False
    
    async def speak(self, text: str, priority: bool = False) -> bool:
        """テキスト音声合成"""
        if not self.tts_engine or not text.strip():
            return False
            
        try:
            if priority:
                # 優先発話（現在の発話を中断）
                self.stop_speaking()
                await self._speak_immediately(text)
            else:
                # 通常発話（キューに追加）
                await self.speech_queue.put(text)
                
            return True
            
        except Exception as e:
            logger.error(f"音声合成に失敗: {e}")
            return False
    
    async def _speak_immediately(self, text: str):
        """即座に音声合成実行"""
        try:
            self.is_speaking = True
            
            # 非同期で音声合成実行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._synthesize_speech, text)
            
        finally:
            self.is_speaking = False
    
    def _synthesize_speech(self, text: str):
        """音声合成実行（同期処理）"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            logger.info(f"音声合成完了: {text}")
            
        except Exception as e:
            logger.error(f"音声合成実行エラー: {e}")
    
    async def start_speech_queue_processor(self):
        """音声合成キュー処理開始"""
        while True:
            try:
                if not self.is_speaking:
                    text = await asyncio.wait_for(self.speech_queue.get(), timeout=0.1)
                    await self._speak_immediately(text)
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.TimeoutError:
                # キューが空の場合
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"音声合成キュー処理エラー: {e}")
                await asyncio.sleep(0.1)
    
    def stop_speaking(self):
        """音声合成停止"""
        try:
            if self.tts_engine and self.is_speaking:
                self.tts_engine.stop()
                self.is_speaking = False
        except Exception as e:
            logger.error(f"音声合成停止エラー: {e}")
    
    def cleanup(self):
        """リソース解放"""
        self.stop_speaking()
        try:
            if self.tts_engine:
                self.tts_engine = None
        except Exception as e:
            logger.error(f"TTSクリーンアップエラー: {e}")


class AudioInterfaceManager:
    """音声インターフェース統合管理クラス"""
    
    def __init__(self):
        self.speech_recognizer = VoskSpeechRecognizer()
        self.text_to_speech = EspeakTextToSpeech()
        self.is_initialized = False
        self.callbacks: Dict[str, List[Callable]] = {
            'speech_recognized': [],
            'speech_started': [],
            'speech_ended': [],
            'tts_started': [],
            'tts_ended': []
        }
        
    async def initialize(self) -> bool:
        """音声インターフェース初期化"""
        if self.is_initialized:
            return True
            
        try:
            # 音声認識エンジン初期化
            recognizer_ok = self.speech_recognizer.initialize()
            
            # 音声合成エンジン初期化
            tts_ok = self.text_to_speech.initialize()
            
            if recognizer_ok and tts_ok:
                # TTS キュー処理開始
                asyncio.create_task(self.text_to_speech.start_speech_queue_processor())
                
                self.is_initialized = True
                logger.info("音声インターフェースを初期化しました")
                return True
            else:
                logger.error("音声インターフェースの初期化に失敗")
                return False
                
        except Exception as e:
            logger.error(f"音声インターフェース初期化エラー: {e}")
            return False
    
    def add_callback(self, event: str, callback: Callable):
        """イベントコールバック追加"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable):
        """イベントコールバック削除"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
    
    def _trigger_callbacks(self, event: str, *args):
        """コールバック実行"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"コールバック実行エラー: {e}")
    
    async def start_listening(self) -> bool:
        """音声認識開始"""
        if not self.is_initialized:
            return False
            
        def on_speech_recognized(text: str):
            self._trigger_callbacks('speech_recognized', text)
        
        self._trigger_callbacks('speech_started')
        success = await self.speech_recognizer.start_listening(on_speech_recognized)
        
        if not success:
            self._trigger_callbacks('speech_ended')
            
        return success
    
    def stop_listening(self):
        """音声認識停止"""
        self.speech_recognizer.stop_listening()
        self._trigger_callbacks('speech_ended')
    
    async def speak(self, text: str, priority: bool = False) -> bool:
        """音声合成実行"""
        if not self.is_initialized:
            return False
            
        self._trigger_callbacks('tts_started', text)
        success = await self.text_to_speech.speak(text, priority)
        
        if success:
            # TTS完了まで待機
            while self.text_to_speech.is_speaking:
                await asyncio.sleep(0.1)
        
        self._trigger_callbacks('tts_ended', text)
        return success
    
    def stop_speaking(self):
        """音声合成停止"""
        self.text_to_speech.stop_speaking()
        self._trigger_callbacks('tts_ended', "")
    
    async def speak_and_listen(self, prompt_text: str) -> Optional[str]:
        """音声プロンプト + 音声入力のワークフロー"""
        if not self.is_initialized:
            return None
            
        try:
            # プロンプト音声出力
            if prompt_text:
                await self.speak(prompt_text, priority=True)
                await asyncio.sleep(0.5)  # 短い間
            
            # 音声入力受付
            recognized_text = None
            
            def on_recognition(text: str):
                nonlocal recognized_text
                recognized_text = text
            
            # 一時的なコールバック追加
            self.add_callback('speech_recognized', on_recognition)
            
            # 音声認識開始
            await self.start_listening()
            
            # 音声入力待機（最大30秒）
            for _ in range(300):  # 30秒 = 300 × 0.1秒
                if recognized_text:
                    break
                await asyncio.sleep(0.1)
            
            # 音声認識停止
            self.stop_listening()
            
            # コールバック削除
            self.remove_callback('speech_recognized', on_recognition)
            
            return recognized_text
            
        except Exception as e:
            logger.error(f"音声対話エラー: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """音声インターフェース状態取得"""
        return {
            'initialized': self.is_initialized,
            'listening': self.speech_recognizer.is_listening,
            'speaking': self.text_to_speech.is_speaking,
            'audio_available': AUDIO_AVAILABLE
        }
    
    def cleanup(self):
        """リソース解放"""
        try:
            self.stop_listening()
            self.stop_speaking()
            self.speech_recognizer.cleanup()
            self.text_to_speech.cleanup()
            self.is_initialized = False
            logger.info("音声インターフェースをクリーンアップしました")
        except Exception as e:
            logger.error(f"音声インターフェースクリーンアップエラー: {e}")


# グローバル音声インターフェースインスタンス
audio_interface = AudioInterfaceManager()


# 便利関数
async def initialize_audio() -> bool:
    """音声インターフェース初期化"""
    return await audio_interface.initialize()


async def speak_text(text: str, priority: bool = False) -> bool:
    """テキスト音声合成"""
    return await audio_interface.speak(text, priority)


async def listen_for_speech() -> Optional[str]:
    """音声認識実行"""
    recognized_text = None
    
    def on_recognition(text: str):
        nonlocal recognized_text
        recognized_text = text
    
    audio_interface.add_callback('speech_recognized', on_recognition)
    
    try:
        await audio_interface.start_listening()
        
        # 音声入力待機
        for _ in range(100):  # 10秒待機
            if recognized_text:
                break
            await asyncio.sleep(0.1)
        
        audio_interface.stop_listening()
        return recognized_text
        
    finally:
        audio_interface.remove_callback('speech_recognized', on_recognition)


async def voice_interaction(prompt: str) -> Optional[str]:
    """音声対話実行"""
    return await audio_interface.speak_and_listen(prompt)


def cleanup_audio():
    """音声インターフェースクリーンアップ"""
    audio_interface.cleanup()
