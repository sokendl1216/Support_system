# -*- coding: utf-8 -*-
"""
言語管理システム
Language management system for dynamic language switching
"""

import json
import os
from typing import Dict, Optional, List, Any
from pathlib import Path
import streamlit as st

from .constants import (
    SupportedLanguages, 
    DEFAULT_LANGUAGE, 
    LANGUAGE_DISPLAY_NAMES,
    RTL_LANGUAGES,
    FALLBACK_PRIORITY,
    BROWSER_LANGUAGE_MAPPING
)

class LanguageManager:
    """言語設定と切り替えを管理するクラス"""
    
    def __init__(self, locale_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            locale_dir: 言語ファイルのディレクトリパス
        """
        self.current_language = DEFAULT_LANGUAGE
        self.locale_dir = locale_dir or self._get_default_locale_dir()
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_all_translations()
    
    def _get_default_locale_dir(self) -> str:
        """デフォルトのロケールディレクトリパスを取得"""
        current_dir = Path(__file__).parent
        return str(current_dir / "locales")
    
    def _load_all_translations(self) -> None:
        """全ての翻訳ファイルを読み込み"""
        locale_path = Path(self.locale_dir)
        if not locale_path.exists():
            locale_path.mkdir(parents=True, exist_ok=True)
        
        for lang in SupportedLanguages:
            lang_code = lang.value
            file_path = locale_path / f"{lang_code}.json"
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Failed to load {lang_code}.json: {e}")
                    self._translations[lang_code] = {}
            else:
                self._translations[lang_code] = {}
    
    def get_current_language(self) -> str:
        """現在の言語コードを取得"""
        return self.current_language
    
    def set_language(self, lang_code: str) -> bool:
        """
        言語を設定
        
        Args:
            lang_code: 言語コード
            
        Returns:
            bool: 設定成功フラグ
        """
        if self.is_supported_language(lang_code):
            self.current_language = lang_code
            # Streamlitセッションステートに保存
            if 'language' in st.session_state:
                st.session_state.language = lang_code
            return True
        return False
    
    def is_supported_language(self, lang_code: str) -> bool:
        """
        サポート言語かどうか確認
        
        Args:
            lang_code: 言語コード
            
        Returns:
            bool: サポート言語フラグ
        """
        return lang_code in [lang.value for lang in SupportedLanguages]
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        サポート言語一覧を取得
        
        Returns:
            Dict[str, str]: {言語コード: 表示名} のマップ
        """
        return LANGUAGE_DISPLAY_NAMES.copy()
    
    def detect_browser_language(self) -> str:
        """
        ブラウザ言語を検出（Streamlitアプリでは限定的）
        
        Returns:
            str: 検出された言語コード
        """
        # Streamlitではブラウザ言語の直接取得は困難
        # セッションステートから取得を試み、なければデフォルト
        if hasattr(st, 'session_state') and 'browser_language' in st.session_state:
            browser_lang = st.session_state.browser_language
            return BROWSER_LANGUAGE_MAPPING.get(browser_lang, DEFAULT_LANGUAGE)
        
        return DEFAULT_LANGUAGE
    
    def auto_detect_language(self) -> str:
        """
        自動言語検出
        
        Returns:
            str: 検出された言語コード
        """
        # 1. セッションステートから取得
        if hasattr(st, 'session_state') and 'language' in st.session_state:
            saved_lang = st.session_state.language
            if self.is_supported_language(saved_lang):
                return saved_lang
        
        # 2. ブラウザ言語を試行
        detected_lang = self.detect_browser_language()
        if self.is_supported_language(detected_lang):
            return detected_lang
        
        # 3. デフォルト言語
        return DEFAULT_LANGUAGE
    
    def is_rtl_language(self, lang_code: Optional[str] = None) -> bool:
        """
        RTL（右から左）言語かどうか確認
        
        Args:
            lang_code: 言語コード（省略時は現在の言語）
            
        Returns:
            bool: RTL言語フラグ
        """
        lang = lang_code or self.current_language
        return lang in RTL_LANGUAGES
    
    def get_fallback_languages(self, lang_code: Optional[str] = None) -> List[str]:
        """
        フォールバック言語リストを取得
        
        Args:
            lang_code: 言語コード（省略時は現在の言語）
            
        Returns:
            List[str]: フォールバック言語コードのリスト
        """
        lang = lang_code or self.current_language
        return FALLBACK_PRIORITY.get(lang, [DEFAULT_LANGUAGE])
    
    def create_language_selector_ui(self) -> str:
        """
        言語選択UIを作成
        
        Returns:
            str: 選択された言語コード
        """
        supported_langs = self.get_supported_languages()
        
        # 現在の言語のインデックスを取得
        current_index = 0
        lang_codes = list(supported_langs.keys())
        if self.current_language in lang_codes:
            current_index = lang_codes.index(self.current_language)
        
        # 言語選択ボックス
        selected_display = st.selectbox(
            "🌐 言語 / Language",
            options=list(supported_langs.values()),
            index=current_index,
            key="language_selector",
            help="Select your preferred language / 使用言語を選択してください"
        )
        
        # 表示名から言語コードを逆引き
        selected_code = None
        for code, display in supported_langs.items():
            if display == selected_display:
                selected_code = code
                break
        
        if selected_code and selected_code != self.current_language:
            self.set_language(selected_code)
            return selected_code
        
        return self.current_language
    
    def save_language_preference(self, lang_code: str) -> None:
        """
        言語設定を永続化
        
        Args:
            lang_code: 言語コード
        """
        if hasattr(st, 'session_state'):
            st.session_state.language = lang_code
        
        # 将来的にはデータベースやファイルに保存も可能
    
    def get_language_config(self) -> Dict[str, Any]:
        """
        現在の言語設定情報を取得
        
        Returns:
            Dict[str, Any]: 言語設定情報
        """
        return {
            "current_language": self.current_language,
            "display_name": LANGUAGE_DISPLAY_NAMES.get(self.current_language, self.current_language),
            "is_rtl": self.is_rtl_language(),
            "fallback_languages": self.get_fallback_languages(),
            "supported_languages": list(self.get_supported_languages().keys())
        }


# シングルトンインスタンス
_language_manager: Optional[LanguageManager] = None

def get_language_manager() -> LanguageManager:
    """言語マネージャーのシングルトンインスタンスを取得"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def init_language_manager(locale_dir: Optional[str] = None) -> LanguageManager:
    """言語マネージャーを初期化"""
    global _language_manager
    _language_manager = LanguageManager(locale_dir)
    return _language_manager
