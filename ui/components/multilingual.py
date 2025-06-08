# -*- coding: utf-8 -*-
"""
多言語対応UIコンポーネント
Multilingual UI components with i18n support
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from ..i18n import get_translator, get_language_manager

def render_language_selector() -> None:
    """言語選択UIを描画"""
    lang_manager = get_language_manager()
    
    with st.sidebar:
        st.markdown("---")
        selected_lang = lang_manager.create_language_selector_ui()
        
        if selected_lang != lang_manager.get_current_language():
            lang_manager.save_language_preference(selected_lang)
            st.rerun()

def render_multilingual_title(title_key: str, **kwargs) -> None:
    """多言語対応タイトルを描画"""
    translator = get_translator()
    title = translator.translate(title_key, **kwargs)
    st.title(title)

def render_multilingual_header(header_key: str, level: int = 1, **kwargs) -> None:
    """多言語対応ヘッダーを描画"""
    translator = get_translator()
    header = translator.translate(header_key, **kwargs)
    
    if level == 1:
        st.header(header)
    elif level == 2:
        st.subheader(header)
    elif level == 3:
        st.markdown(f"### {header}")
    elif level == 4:
        st.markdown(f"#### {header}")
    else:
        st.markdown(f"##### {header}")

def render_multilingual_text(text_key: str, markdown: bool = True, **kwargs) -> None:
    """多言語対応テキストを描画"""
    translator = get_translator()
    text = translator.translate(text_key, **kwargs)
    
    if markdown:
        st.markdown(text)
    else:
        st.text(text)

def render_multilingual_button(
    button_key: str, 
    key: Optional[str] = None,
    help_key: Optional[str] = None,
    **kwargs
) -> bool:
    """多言語対応ボタンを描画"""
    translator = get_translator()
    button_text = translator.translate(button_key, **kwargs)
    
    help_text = None
    if help_key:
        help_text = translator.translate(help_key, **kwargs)
    
    return st.button(button_text, key=key, help=help_text)

def render_multilingual_selectbox(
    label_key: str,
    options: Dict[str, str],  # {value: translation_key}
    key: Optional[str] = None,
    help_key: Optional[str] = None,
    **kwargs
) -> str:
    """多言語対応セレクトボックスを描画"""
    translator = get_translator()
    label = translator.translate(label_key, **kwargs)
    
    # オプションを翻訳
    translated_options = {}
    option_mapping = {}
    
    for value, option_key in options.items():
        translated_text = translator.translate(option_key, **kwargs)
        translated_options[value] = translated_text
        option_mapping[translated_text] = value
    
    help_text = None
    if help_key:
        help_text = translator.translate(help_key, **kwargs)
    
    selected_display = st.selectbox(
        label,
        options=list(translated_options.values()),
        key=key,
        help=help_text
    )
    
    return option_mapping.get(selected_display, list(options.keys())[0])

def render_multilingual_radio(
    label_key: str,
    options: Dict[str, str],  # {value: translation_key}
    key: Optional[str] = None,
    help_key: Optional[str] = None,
    horizontal: bool = False,
    **kwargs
) -> str:
    """多言語対応ラジオボタンを描画"""
    translator = get_translator()
    label = translator.translate(label_key, **kwargs)
    
    # オプションを翻訳
    translated_options = {}
    option_mapping = {}
    
    for value, option_key in options.items():
        translated_text = translator.translate(option_key, **kwargs)
        translated_options[value] = translated_text
        option_mapping[translated_text] = value
    
    help_text = None
    if help_key:
        help_text = translator.translate(help_key, **kwargs)
    
    selected_display = st.radio(
        label,
        options=list(translated_options.values()),
        key=key,
        help=help_text,
        horizontal=horizontal
    )
    
    return option_mapping.get(selected_display, list(options.keys())[0])

def render_multilingual_tabs(tab_keys: List[str], **kwargs) -> str:
    """多言語対応タブを描画"""
    translator = get_translator()
    tab_labels = [translator.translate(key, **kwargs) for key in tab_keys]
    
    tabs = st.tabs(tab_labels)
    
    # アクティブなタブのキーを返すため、セッションステートを使用
    for i, (tab_key, tab) in enumerate(zip(tab_keys, tabs)):
        with tab:
            if f"active_tab_{id(tab_keys)}" not in st.session_state:
                st.session_state[f"active_tab_{id(tab_keys)}"] = tab_keys[0]
            
            # タブがクリックされた場合の検出（簡易実装）
            if st.button("", key=f"tab_detector_{i}", help="Tab detector", disabled=True):
                st.session_state[f"active_tab_{id(tab_keys)}"] = tab_key
    
    return st.session_state.get(f"active_tab_{id(tab_keys)}", tab_keys[0])

def render_language_status_indicator() -> None:
    """現在の言語状況を表示するインジケーター"""
    lang_manager = get_language_manager()
    translator = get_translator()
    
    config = lang_manager.get_language_config()
    
    with st.expander("🌐 " + translator.translate("ui.language")):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{translator.translate('ui.status')}:**")
            st.write(f"📍 {config['display_name']} ({config['current_language']})")
            
            if config['is_rtl']:
                st.write("⬅️ RTL Layout")
            else:
                st.write("➡️ LTR Layout")
        
        with col2:
            st.markdown(f"**{translator.translate('navigation.help')}:**")
            st.write(f"🔄 Fallback: {', '.join(config['fallback_languages'][:2])}")
            st.write(f"🌍 Supported: {len(config['supported_languages'])} languages")

def render_multilingual_alert(
    message_key: str,
    alert_type: str = "info",  # "info", "success", "warning", "error"
    **kwargs
) -> None:
    """多言語対応アラートを描画"""
    translator = get_translator()
    message = translator.translate(message_key, **kwargs)
    
    if alert_type == "success":
        st.success(message)
    elif alert_type == "warning":
        st.warning(message)
    elif alert_type == "error":
        st.error(message)
    else:
        st.info(message)

def render_multilingual_progress(
    label_key: str,
    value: float,
    min_value: float = 0.0,
    max_value: float = 1.0,
    **kwargs
) -> None:
    """多言語対応プログレスバーを描画"""
    translator = get_translator()
    label = translator.translate(label_key, **kwargs)
    
    st.progress(value, text=label)

def render_multilingual_metric(
    label_key: str,
    value: str,
    delta_key: Optional[str] = None,
    delta_value: Optional[str] = None,
    **kwargs
) -> None:
    """多言語対応メトリクスを描画"""
    translator = get_translator()
    label = translator.translate(label_key, **kwargs)
    
    delta_text = None
    if delta_key and delta_value:
        delta_text = translator.translate(delta_key, **kwargs)
    
    st.metric(label=label, value=value, delta=delta_text)

class MultilingualForm:
    """多言語対応フォームヘルパークラス"""
    
    def __init__(self, form_key: str):
        self.translator = get_translator()
        self.form_key = form_key
        self.form = st.form(form_key)
    
    def __enter__(self):
        return self.form.__enter__()
    
    def __exit__(self, *args):
        return self.form.__exit__(*args)
    
    def text_input(self, label_key: str, **kwargs) -> str:
        """多言語対応テキスト入力"""
        label = self.translator.translate(label_key)
        placeholder = kwargs.pop('placeholder_key', None)
        if placeholder:
            kwargs['placeholder'] = self.translator.translate(placeholder)
        
        return st.text_input(label, **kwargs)
    
    def text_area(self, label_key: str, **kwargs) -> str:
        """多言語対応テキストエリア"""
        label = self.translator.translate(label_key)
        placeholder = kwargs.pop('placeholder_key', None)
        if placeholder:
            kwargs['placeholder'] = self.translator.translate(placeholder)
        
        return st.text_area(label, **kwargs)
    
    def submit_button(self, button_key: str, **kwargs) -> bool:
        """多言語対応送信ボタン"""
        button_text = self.translator.translate(button_key)
        return st.form_submit_button(button_text, **kwargs)
