"""
音声システム設定ファイル
Vosk/Espeak音声システムの設定管理

設定項目:
- 音声認識設定 (Vosk)
- 音声合成設定 (Espeak)
- パフォーマンス設定
- アクセシビリティ設定
- ログ設定
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class AudioSystemConfig:
    """音声システム設定管理クラス"""
    
    # デフォルト設定
    DEFAULT_CONFIG = {
        # 音声認識設定 (Vosk)
        "speech_recognition": {
            "enabled": True,
            "sample_rate": 16000,
            "chunk_size": 4096,
            "channels": 1,
            "model_path": "vosk-model-ja-0.22",
            "model_download_url": "https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip",
            "language": "ja",
            "timeout": 30,
            "auto_stop_silence": 3.0,  # 無音継続時間（秒）
            "noise_reduction": {
                "enabled": True,
                "threshold": 0.01,
                "filter_type": "basic"
            }
        },
        
        # 音声合成設定 (Espeak/pyttsx3)
        "text_to_speech": {
            "enabled": True,
            "engine": "pyttsx3",  # pyttsx3, espeak
            "voice": {
                "language": "ja",
                "rate": 150,  # 話速 (単語/分)
                "volume": 0.7,  # 音量 (0.0-1.0)
                "pitch": 50,   # 音程 (0-100)
                "voice_id": None  # 特定の音声ID（None=自動選択）
            },
            "queue_management": {
                "max_queue_size": 10,
                "priority_interrupt": True,
                "auto_clear_on_error": True
            }
        },
        
        # パフォーマンス設定
        "performance": {
            "initialization_timeout": 10.0,
            "response_timeout": 5.0,
            "memory_limit_mb": 512,
            "concurrent_operations": 2,
            "cache_enabled": True,
            "cache_size": 100,
            "async_processing": True
        },
        
        # アクセシビリティ設定
        "accessibility": {
            "auto_read_responses": False,
            "auto_listen_after_response": False,
            "keyboard_shortcuts": {
                "start_listening": "F1",
                "stop_listening": "F2",
                "stop_speaking": "F3",
                "repeat_last": "F4"
            },
            "visual_feedback": {
                "show_recognition_status": True,
                "show_synthesis_status": True,
                "show_audio_levels": False
            },
            "audio_feedback": {
                "confirmation_sounds": True,
                "error_sounds": True,
                "status_announcements": True
            }
        },
        
        # UI統合設定
        "ui_integration": {
            "streamlit_integration": True,
            "real_time_display": True,
            "inline_voice_buttons": True,
            "voice_input_widgets": True,
            "auto_scroll_to_results": True
        },
        
        # ログ設定
        "logging": {
            "enabled": True,
            "level": "INFO",
            "file_logging": False,
            "log_file_path": "logs/audio_system.log",
            "max_log_size_mb": 50,
            "log_retention_days": 7
        },
        
        # 開発・デバッグ設定
        "development": {
            "debug_mode": False,
            "verbose_logging": False,
            "performance_monitoring": True,
            "test_mode": False,
            "mock_audio_devices": False
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else None
        self.config = self.DEFAULT_CONFIG.copy()
        
        if self.config_file and self.config_file.exists():
            self.load_config()
    
    def load_config(self) -> bool:
        """設定ファイル読み込み"""
        try:
            if not self.config_file or not self.config_file.exists():
                logger.info("設定ファイルが見つかりません。デフォルト設定を使用します。")
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # 設定をマージ（デフォルト値を保持）
            self._merge_config(self.config, loaded_config)
            
            logger.info(f"設定ファイルを読み込みました: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return False
    
    def save_config(self) -> bool:
        """設定ファイル保存"""
        try:
            if not self.config_file:
                logger.warning("設定ファイルパスが指定されていません")
                return False
            
            # ディレクトリ作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"設定ファイルを保存しました: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")
            return False
    
    def _merge_config(self, default: dict, loaded: dict):
        """設定マージ（再帰的）"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
    
    def get(self, key_path: str, default=None) -> Any:
        """設定値取得（ドット記法対応）"""
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                value = value[key]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """設定値設定（ドット記法対応）"""
        try:
            keys = key_path.split('.')
            config = self.config
            
            # 最後のキー以外をたどる
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 最後のキーに値を設定
            config[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"設定値設定エラー: {e}")
            return False
    
    def reset_to_default(self, section: Optional[str] = None):
        """設定をデフォルトにリセット"""
        if section:
            if section in self.DEFAULT_CONFIG:
                self.config[section] = self.DEFAULT_CONFIG[section].copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
    
    def validate_config(self) -> Dict[str, Any]:
        """設定検証"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 音声認識設定検証
            sr_config = self.get('speech_recognition', {})
            
            # サンプルレート検証
            sample_rate = sr_config.get('sample_rate', 16000)
            if sample_rate not in [8000, 16000, 22050, 44100, 48000]:
                validation_results['warnings'].append(
                    f"非標準のサンプルレート: {sample_rate}Hz"
                )
            
            # チャンクサイズ検証
            chunk_size = sr_config.get('chunk_size', 4096)
            if chunk_size < 1024 or chunk_size > 8192:
                validation_results['warnings'].append(
                    f"推奨範囲外のチャンクサイズ: {chunk_size}"
                )
            
            # 音声合成設定検証
            tts_config = self.get('text_to_speech', {})
            voice_config = tts_config.get('voice', {})
            
            # 話速検証
            rate = voice_config.get('rate', 150)
            if rate < 50 or rate > 400:
                validation_results['errors'].append(
                    f"話速が範囲外: {rate} (50-400)"
                )
                validation_results['valid'] = False
            
            # 音量検証
            volume = voice_config.get('volume', 0.7)
            if volume < 0.0 or volume > 1.0:
                validation_results['errors'].append(
                    f"音量が範囲外: {volume} (0.0-1.0)"
                )
                validation_results['valid'] = False
            
            # パフォーマンス設定検証
            perf_config = self.get('performance', {})
            
            # メモリ制限検証
            memory_limit = perf_config.get('memory_limit_mb', 512)
            if memory_limit < 128:
                validation_results['warnings'].append(
                    f"メモリ制限が低すぎる可能性: {memory_limit}MB"
                )
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"設定検証エラー: {e}")
        
        return validation_results
    
    def get_summary(self) -> Dict[str, Any]:
        """設定サマリー取得"""
        return {
            'speech_recognition_enabled': self.get('speech_recognition.enabled', False),
            'text_to_speech_enabled': self.get('text_to_speech.enabled', False),
            'sample_rate': self.get('speech_recognition.sample_rate', 16000),
            'speech_rate': self.get('text_to_speech.voice.rate', 150),
            'volume': self.get('text_to_speech.voice.volume', 0.7),
            'noise_reduction': self.get('speech_recognition.noise_reduction.enabled', False),
            'auto_read_responses': self.get('accessibility.auto_read_responses', False),
            'debug_mode': self.get('development.debug_mode', False)
        }
    
    def export_config(self) -> str:
        """設定をJSON文字列としてエクスポート"""
        try:
            return json.dumps(self.config, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"設定エクスポートエラー: {e}")
            return "{}"
    
    def import_config(self, config_json: str) -> bool:
        """JSON文字列から設定をインポート"""
        try:
            imported_config = json.loads(config_json)
            self._merge_config(self.config, imported_config)
            logger.info("設定をインポートしました")
            return True
        except Exception as e:
            logger.error(f"設定インポートエラー: {e}")
            return False


# グローバル設定インスタンス
audio_config = AudioSystemConfig()


# 便利関数
def load_audio_config(config_file: str) -> AudioSystemConfig:
    """音声設定読み込み"""
    return AudioSystemConfig(config_file)


def get_audio_setting(key_path: str, default=None) -> Any:
    """音声設定値取得"""
    return audio_config.get(key_path, default)


def set_audio_setting(key_path: str, value: Any) -> bool:
    """音声設定値設定"""
    return audio_config.set(key_path, value)


def save_audio_config() -> bool:
    """音声設定保存"""
    return audio_config.save_config()


def validate_audio_config() -> Dict[str, Any]:
    """音声設定検証"""
    return audio_config.validate_config()


# 設定プリセット
AUDIO_PRESETS = {
    "high_quality": {
        "speech_recognition": {
            "sample_rate": 22050,
            "chunk_size": 4096,
            "noise_reduction": {
                "enabled": True,
                "threshold": 0.005
            }
        },
        "text_to_speech": {
            "voice": {
                "rate": 180,
                "volume": 0.8
            }
        }
    },
    
    "low_latency": {
        "speech_recognition": {
            "sample_rate": 16000,
            "chunk_size": 2048,
            "timeout": 15
        },
        "text_to_speech": {
            "voice": {
                "rate": 200,
                "volume": 0.7
            }
        },
        "performance": {
            "response_timeout": 2.0,
            "cache_enabled": True
        }
    },
    
    "accessibility": {
        "accessibility": {
            "auto_read_responses": True,
            "audio_feedback": {
                "confirmation_sounds": True,
                "status_announcements": True
            },
            "visual_feedback": {
                "show_recognition_status": True,
                "show_synthesis_status": True
            }
        },
        "text_to_speech": {
            "voice": {
                "rate": 140,
                "volume": 0.9
            }
        }
    },
    
    "development": {
        "development": {
            "debug_mode": True,
            "verbose_logging": True,
            "performance_monitoring": True
        },
        "logging": {
            "level": "DEBUG",
            "file_logging": True
        }
    }
}


def apply_preset(preset_name: str) -> bool:
    """設定プリセット適用"""
    try:
        if preset_name not in AUDIO_PRESETS:
            logger.error(f"不明なプリセット: {preset_name}")
            return False
        
        preset_config = AUDIO_PRESETS[preset_name]
        audio_config._merge_config(audio_config.config, preset_config)
        
        logger.info(f"プリセット「{preset_name}」を適用しました")
        return True
        
    except Exception as e:
        logger.error(f"プリセット適用エラー: {e}")
        return False


def get_available_presets() -> List[str]:
    """利用可能なプリセット一覧取得"""
    return list(AUDIO_PRESETS.keys())
