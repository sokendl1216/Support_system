# -*- coding: utf-8 -*-
"""
言語定数とサポート言語定義
Language constants and supported languages definition
"""

from enum import Enum
from typing import Dict, List

class SupportedLanguages(Enum):
    """サポート言語の定義"""
    JAPANESE = "ja"
    ENGLISH = "en"
    KOREAN = "ko"
    CHINESE_SIMPLIFIED = "zh-cn"
    CHINESE_TRADITIONAL = "zh-tw"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    ITALIAN = "it"
    DUTCH = "nl"
    RUSSIAN = "ru"
    ARABIC = "ar"
    HINDI = "hi"
    THAI = "th"
    VIETNAMESE = "vi"

# 言語表示名（各言語の自国語表記）
LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "ja": "日本語",
    "en": "English", 
    "ko": "한국어",
    "zh-cn": "简体中文",
    "zh-tw": "繁體中文",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "it": "Italiano",
    "nl": "Nederlands",
    "ru": "Русский",
    "ar": "العربية",
    "hi": "हिन्दी",
    "th": "ไทย",
    "vi": "Tiếng Việt"
}

# RTL（右から左）言語のリスト
RTL_LANGUAGES: List[str] = ["ar"]

# フォールバック言語の優先順位
FALLBACK_PRIORITY: Dict[str, List[str]] = {
    "ja": ["en", "zh-cn"],
    "en": ["ja", "es"],
    "ko": ["ja", "en", "zh-cn"],
    "zh-cn": ["zh-tw", "ja", "en"],
    "zh-tw": ["zh-cn", "ja", "en"],
    "es": ["en", "pt", "fr"],
    "fr": ["en", "es", "de"],
    "de": ["en", "fr", "nl"],
    "pt": ["es", "en", "fr"],
    "it": ["en", "es", "fr"],
    "nl": ["en", "de", "fr"],
    "ru": ["en", "de", "fr"],
    "ar": ["en", "fr", "es"],
    "hi": ["en", "ja", "zh-cn"],
    "th": ["en", "ja", "zh-cn"],
    "vi": ["en", "ja", "zh-cn"]
}

# デフォルト言語
DEFAULT_LANGUAGE = "ja"

# 自動検出対象のブラウザ言語
BROWSER_LANGUAGE_MAPPING: Dict[str, str] = {
    "ja": "ja",
    "ja-JP": "ja",
    "en": "en",
    "en-US": "en",
    "en-GB": "en",
    "ko": "ko",
    "ko-KR": "ko",
    "zh": "zh-cn",
    "zh-CN": "zh-cn",
    "zh-TW": "zh-tw",
    "zh-HK": "zh-tw",
    "es": "es",
    "es-ES": "es",
    "es-MX": "es",
    "fr": "fr",
    "fr-FR": "fr",
    "de": "de",
    "de-DE": "de",
    "pt": "pt",
    "pt-BR": "pt",
    "pt-PT": "pt",
    "it": "it",
    "it-IT": "it",
    "nl": "nl",
    "nl-NL": "nl",
    "ru": "ru",
    "ru-RU": "ru",
    "ar": "ar",
    "hi": "hi",
    "th": "th",
    "vi": "vi"
}
