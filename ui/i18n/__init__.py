# -*- coding: utf-8 -*-
"""
多言語対応基盤モジュール
International support module for multi-language UI
"""

from .translator import Translator, get_translator
from .language_manager import LanguageManager, get_language_manager
from .constants import SupportedLanguages

__all__ = [
    'Translator',
    'get_translator', 
    'LanguageManager',
    'get_language_manager',
    'SupportedLanguages'
]
