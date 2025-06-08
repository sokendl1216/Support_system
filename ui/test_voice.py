#!/usr/bin/env python3
"""
音声システムの基本動作テスト
"""
import logging
import sys
import os

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_audio_libraries():
    """音声ライブラリの基本テスト"""
    results = {}
    
    # Vosk音声認識テスト
    try:
        import vosk
        logger.info("✓ Vosk音声認識ライブラリ正常")
        results['vosk'] = True
    except ImportError as e:
        logger.error(f"✗ Voskインポートエラー: {e}")
        results['vosk'] = False
    
    # PyAudio音声入力テスト
    try:
        import pyaudio
        logger.info("✓ PyAudio音声入力ライブラリ正常")
        results['pyaudio'] = True
    except ImportError as e:
        logger.error(f"✗ PyAudioインポートエラー: {e}")
        results['pyaudio'] = False
    
    # pyttsx3音声合成テスト
    try:
        import pyttsx3
        logger.info("✓ pyttsx3音声合成ライブラリ正常")
        results['pyttsx3'] = True
    except ImportError as e:
        logger.error(f"✗ pyttsx3インポートエラー: {e}")
        results['pyttsx3'] = False
    
    # SpeechRecognitionテスト
    try:
        import speech_recognition
        logger.info("✓ SpeechRecognition音声認識ライブラリ正常")
        results['speech_recognition'] = True
    except ImportError as e:
        logger.error(f"✗ SpeechRecognitionインポートエラー: {e}")
        results['speech_recognition'] = False
    
    return results

def test_audio_devices():
    """音声デバイス確認テスト"""
    try:
        import pyaudio
        
        audio = pyaudio.PyAudio()
        logger.info(f"利用可能な音声デバイス数: {audio.get_device_count()}")
        
        # 入力デバイス検索
        input_devices = []
        output_devices = []
        
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
            if device_info['maxOutputChannels'] > 0:
                output_devices.append(device_info['name'])
        
        logger.info(f"入力デバイス({len(input_devices)}): {input_devices}")
        logger.info(f"出力デバイス({len(output_devices)}): {output_devices}")
        
        audio.terminate()
        return True
        
    except Exception as e:
        logger.error(f"音声デバイステストエラー: {e}")
        return False

def test_tts_basic():
    """音声合成基本テスト"""
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        
        # 利用可能な音声確認
        voices = engine.getProperty('voices')
        logger.info(f"利用可能な音声数: {len(voices) if voices else 0}")
        
        if voices:
            for i, voice in enumerate(voices[:3]):  # 最大3個まで表示
                logger.info(f"音声 {i+1}: {voice.name} ({voice.id})")
        
        # 設定確認
        rate = engine.getProperty('rate')
        volume = engine.getProperty('volume')
        logger.info(f"音声設定 - 話速: {rate}, 音量: {volume}")
        
        engine.stop()
        return True
        
    except Exception as e:
        logger.error(f"音声合成テストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    logger.info("🎵 音声システム基本動作テスト開始")
    logger.info("=" * 50)
    
    # ライブラリテスト
    logger.info("📚 音声ライブラリテスト")
    lib_results = test_audio_libraries()
    
    # デバイステスト
    logger.info("\n🎤 音声デバイステスト")
    device_ok = test_audio_devices()
    
    # TTS基本テスト
    logger.info("\n🔊 音声合成基本テスト")
    tts_ok = test_tts_basic()
    
    # 結果サマリー
    logger.info("\n" + "=" * 50)
    logger.info("📋 テスト結果サマリー")
    
    all_libs_ok = all(lib_results.values())
    logger.info(f"音声ライブラリ: {'✓ 正常' if all_libs_ok else '✗ 問題あり'}")
    logger.info(f"音声デバイス: {'✓ 正常' if device_ok else '✗ 問題あり'}")
    logger.info(f"音声合成: {'✓ 正常' if tts_ok else '✗ 問題あり'}")
    
    total_status = all_libs_ok and device_ok and tts_ok
    logger.info(f"\n総合判定: {'🎉 音声システム利用可能' if total_status else '⚠️ 設定確認必要'}")
    
    return total_status

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
