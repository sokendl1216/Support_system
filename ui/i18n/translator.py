# -*- coding: utf-8 -*-
"""
翻訳システム
Translation system with fallback support and dynamic loading
"""

import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from .language_manager import get_language_manager
from .constants import DEFAULT_LANGUAGE

class Translator:
    """多言語翻訳を担当するクラス"""
    
    def __init__(self, language_manager=None):
        """
        初期化
        
        Args:
            language_manager: 言語マネージャーインスタンス
        """
        self.language_manager = language_manager or get_language_manager()
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def translate(self, key: str, **kwargs) -> str:
        """
        キーを使って翻訳を取得
        
        Args:
            key: 翻訳キー（ドット記法対応: "ui.buttons.save"）
            **kwargs: 翻訳文字列のプレースホルダー値
            
        Returns:
            str: 翻訳された文字列
        """
        current_lang = self.language_manager.get_current_language()
        
        # 現在の言語で翻訳を試行
        translation = self._get_translation(current_lang, key)
        
        # フォールバック言語で試行
        if translation is None:
            fallback_languages = self.language_manager.get_fallback_languages()
            for fallback_lang in fallback_languages:
                translation = self._get_translation(fallback_lang, key)
                if translation is not None:
                    break
        
        # デフォルト言語で最終試行
        if translation is None and current_lang != DEFAULT_LANGUAGE:
            translation = self._get_translation(DEFAULT_LANGUAGE, key)
        
        # 翻訳が見つからない場合はキーをそのまま返す
        if translation is None:
            translation = key
        
        # プレースホルダーの置換
        if kwargs and isinstance(translation, str):
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError) as e:
                # 置換エラーの場合は元の文字列を返す
                print(f"Translation placeholder error for key '{key}': {e}")
        
        return translation
    
    def _get_translation(self, lang_code: str, key: str) -> Optional[str]:
        """
        指定言語から翻訳を取得
        
        Args:
            lang_code: 言語コード
            key: 翻訳キー
            
        Returns:
            Optional[str]: 翻訳文字列（見つからない場合はNone）
        """
        # 言語マネージャーから翻訳データを取得
        translations = self.language_manager._translations.get(lang_code, {})
        
        # ドット記法でネストしたキーをサポート
        keys = key.split('.')
        current = translations
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def t(self, key: str, **kwargs) -> str:
        """translate()のエイリアス"""
        return self.translate(key, **kwargs)
    
    def has_translation(self, key: str, lang_code: Optional[str] = None) -> bool:
        """
        翻訳が存在するかチェック
        
        Args:
            key: 翻訳キー
            lang_code: 言語コード（省略時は現在の言語）
            
        Returns:
            bool: 翻訳存在フラグ
        """
        lang = lang_code or self.language_manager.get_current_language()
        return self._get_translation(lang, key) is not None
    
    def get_available_keys(self, lang_code: Optional[str] = None) -> List[str]:
        """
        利用可能な翻訳キーのリストを取得
        
        Args:
            lang_code: 言語コード（省略時は現在の言語）
            
        Returns:
            List[str]: 翻訳キーのリスト
        """
        lang = lang_code or self.language_manager.get_current_language()
        translations = self.language_manager._translations.get(lang, {})
        
        def _extract_keys(data: Dict[str, Any], prefix: str = "") -> List[str]:
            keys = []
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    keys.extend(_extract_keys(value, full_key))
                elif isinstance(value, str):
                    keys.append(full_key)
            return keys
        
        return _extract_keys(translations)
    
    def translate_dict(self, data: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """
        辞書のキーを一括翻訳
        
        Args:
            data: {翻訳キー: デフォルト値} の辞書
            **kwargs: プレースホルダー値
            
        Returns:
            Dict[str, str]: {元キー: 翻訳後文字列} の辞書
        """
        result = {}
        for key, default_value in data.items():
            translation = self.translate(key, **kwargs)
            result[key] = translation if translation != key else str(default_value)
        return result
    
    def translate_list(self, keys: List[str], **kwargs) -> List[str]:
        """
        キーリストを一括翻訳
        
        Args:
            keys: 翻訳キーのリスト
            **kwargs: プレースホルダー値
            
        Returns:
            List[str]: 翻訳後文字列のリスト
        """
        return [self.translate(key, **kwargs) for key in keys]
    
    def get_translation_status(self) -> Dict[str, Any]:
        """
        翻訳状況の統計情報を取得
        
        Returns:
            Dict[str, Any]: 翻訳状況情報
        """
        current_lang = self.language_manager.get_current_language()
        supported_langs = self.language_manager.get_supported_languages()
        
        status = {
            "current_language": current_lang,
            "total_languages": len(supported_langs),
            "translation_coverage": {}
        }
        
        # 各言語の翻訳カバレッジを計算
        base_keys = set(self.get_available_keys(DEFAULT_LANGUAGE))
        
        for lang_code in supported_langs.keys():
            lang_keys = set(self.get_available_keys(lang_code))
            if base_keys:
                coverage = len(lang_keys & base_keys) / len(base_keys) * 100
            else:
                coverage = 0
            
            status["translation_coverage"][lang_code] = {
                "percentage": round(coverage, 2),
                "translated_keys": len(lang_keys & base_keys),
                "total_keys": len(base_keys),
                "missing_keys": len(base_keys - lang_keys)
            }
        
        return status


# シングルトンインスタンス
_translator: Optional[Translator] = None

def get_translator() -> Translator:
    """翻訳システムのシングルトンインスタンスを取得"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator

def init_translator(language_manager=None) -> Translator:
    """翻訳システムを初期化"""
    global _translator
    _translator = Translator(language_manager)
    return _translator

# 便利関数
def t(key: str, **kwargs) -> str:
    """翻訳のショートカット関数"""
    return get_translator().translate(key, **kwargs)
