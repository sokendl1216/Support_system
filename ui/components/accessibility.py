# -*- coding: utf-8 -*-
"""
アクセシビリティツールセット

タスク4-5: アクセシビリティツールセット実装
スクリーンリーダー対応、キーボードナビゲーション、カラースキーム設定など
包括的なアクセシビリティ機能を提供します。
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class ColorScheme(Enum):
    """カラースキーム列挙"""
    DEFAULT = "default"                # デフォルト
    HIGH_CONTRAST = "high_contrast"    # ハイコントラスト
    DARK_MODE = "dark_mode"           # ダークモード
    LIGHT_MODE = "light_mode"         # ライトモード
    DEUTERANOPIA = "deuteranopia"     # 緑色覚異常対応
    PROTANOPIA = "protanopia"         # 赤色覚異常対応
    TRITANOPIA = "tritanopia"         # 青色覚異常対応


class FontSize(Enum):
    """フォントサイズ列挙"""
    SMALL = "small"      # 小
    MEDIUM = "medium"    # 中（標準）
    LARGE = "large"      # 大
    EXTRA_LARGE = "xl"   # 特大


@dataclass
class AccessibilitySettings:
    """アクセシビリティ設定"""
    color_scheme: ColorScheme = ColorScheme.DEFAULT
    font_size: FontSize = FontSize.MEDIUM
    screen_reader_enabled: bool = False
    keyboard_navigation_enabled: bool = True
    high_contrast_enabled: bool = False
    animations_enabled: bool = True
    auto_play_disabled: bool = False
    focus_indicators_enhanced: bool = False
    text_spacing_increased: bool = False
    click_target_enlarged: bool = False


class AccessibilityToolset:
    """アクセシビリティツールセット管理クラス"""
    
    def __init__(self):
        self.settings = self._load_settings()
        self.css_cache = {}
        self._init_session_state()
    
    def _init_session_state(self):
        """セッション状態の初期化"""
        if 'accessibility_settings' not in st.session_state:
            st.session_state.accessibility_settings = self.settings
        if 'keyboard_focus_index' not in st.session_state:
            st.session_state.keyboard_focus_index = 0
        if 'screen_reader_announcements' not in st.session_state:
            st.session_state.screen_reader_announcements = []
    
    def _load_settings(self) -> AccessibilitySettings:
        """設定の読み込み"""
        settings_path = Path("ui/config/accessibility_settings.json")
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return AccessibilitySettings(**data)
            except Exception:
                pass
        return AccessibilitySettings()
    
    def save_settings(self) -> bool:
        """設定の保存"""
        try:
            settings_path = Path("ui/config/accessibility_settings.json")
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            settings_dict = {
                'color_scheme': self.settings.color_scheme.value,
                'font_size': self.settings.font_size.value,
                'screen_reader_enabled': self.settings.screen_reader_enabled,
                'keyboard_navigation_enabled': self.settings.keyboard_navigation_enabled,
                'high_contrast_enabled': self.settings.high_contrast_enabled,
                'animations_enabled': self.settings.animations_enabled,
                'auto_play_disabled': self.settings.auto_play_disabled,
                'focus_indicators_enhanced': self.settings.focus_indicators_enhanced,
                'text_spacing_increased': self.settings.text_spacing_increased,
                'click_target_enlarged': self.settings.click_target_enlarged
            }
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_color_scheme_css(self, scheme: ColorScheme) -> str:
        """カラースキーム用CSS生成"""
        if scheme in self.css_cache:
            return self.css_cache[scheme]
        
        css = ""
        
        if scheme == ColorScheme.HIGH_CONTRAST:
            css = """
            <style>
            .stApp {
                background-color: #000000 !important;
                color: #FFFFFF !important;
            }
            .stButton > button {
                background-color: #FFFFFF !important;
                color: #000000 !important;
                border: 2px solid #FFFFFF !important;
                font-weight: bold !important;
            }
            .stButton > button:hover {
                background-color: #FFFF00 !important;
                color: #000000 !important;
            }
            .stSelectbox > div > div {
                background-color: #000000 !important;
                color: #FFFFFF !important;
                border: 2px solid #FFFFFF !important;
            }
            .stTextInput > div > div > input {
                background-color: #000000 !important;
                color: #FFFFFF !important;
                border: 2px solid #FFFFFF !important;
            }
            .stSidebar {
                background-color: #000000 !important;
            }
            .stSidebar .stMarkdown {
                color: #FFFFFF !important;
            }
            </style>
            """
        
        elif scheme == ColorScheme.DARK_MODE:
            css = """
            <style>
            .stApp {
                background-color: #1E1E1E !important;
                color: #FFFFFF !important;
            }
            .stButton > button {
                background-color: #404040 !important;
                color: #FFFFFF !important;
                border: 1px solid #606060 !important;
            }
            .stSidebar {
                background-color: #2D2D2D !important;
            }
            </style>
            """
        
        elif scheme == ColorScheme.DEUTERANOPIA:
            css = """
            <style>
            /* 緑色覚異常対応 */
            .stSuccess {
                background-color: #0066CC !important;
                color: #FFFFFF !important;
            }
            .stError {
                background-color: #CC3300 !important;
                color: #FFFFFF !important;
            }
            .stWarning {
                background-color: #FF9900 !important;
                color: #000000 !important;
            }
            </style>
            """
        
        elif scheme == ColorScheme.PROTANOPIA:
            css = """
            <style>
            /* 赤色覚異常対応 */
            .stSuccess {
                background-color: #0066FF !important;
                color: #FFFFFF !important;
            }
            .stError {
                background-color: #999999 !important;
                color: #FFFFFF !important;
            }
            .stWarning {
                background-color: #FFCC00 !important;
                color: #000000 !important;
            }
            </style>
            """
        
        elif scheme == ColorScheme.TRITANOPIA:
            css = """
            <style>
            /* 青色覚異常対応 */
            .stSuccess {
                background-color: #00AA00 !important;
                color: #FFFFFF !important;
            }
            .stError {
                background-color: #DD0000 !important;
                color: #FFFFFF !important;
            }
            .stWarning {
                background-color: #FF8800 !important;
                color: #000000 !important;
            }
            </style>
            """
        
        self.css_cache[scheme] = css
        return css
    
    def get_font_size_css(self, size: FontSize) -> str:
        """フォントサイズ用CSS生成"""
        multipliers = {
            FontSize.SMALL: 0.85,
            FontSize.MEDIUM: 1.0,
            FontSize.LARGE: 1.15,
            FontSize.EXTRA_LARGE: 1.3
        }
        
        multiplier = multipliers.get(size, 1.0)
        
        return f"""
        <style>
        .stApp {{
            font-size: {14 * multiplier}px !important;
        }}
        .stButton > button {{
            font-size: {14 * multiplier}px !important;
            min-height: {40 * multiplier}px !important;
            padding: {8 * multiplier}px {16 * multiplier}px !important;
        }}
        .stSelectbox label {{
            font-size: {14 * multiplier}px !important;
        }}
        .stTextInput label {{
            font-size: {14 * multiplier}px !important;
        }}
        h1 {{
            font-size: {32 * multiplier}px !important;
        }}
        h2 {{
            font-size: {28 * multiplier}px !important;
        }}
        h3 {{
            font-size: {24 * multiplier}px !important;
        }}
        </style>
        """
    
    def get_accessibility_css(self) -> str:
        """総合アクセシビリティCSS生成"""
        css_parts = []
        
        # カラースキーム
        css_parts.append(self.get_color_scheme_css(self.settings.color_scheme))
        
        # フォントサイズ
        css_parts.append(self.get_font_size_css(self.settings.font_size))
        
        # 追加のアクセシビリティ機能
        if self.settings.focus_indicators_enhanced:
            css_parts.append("""
            <style>
            .stButton > button:focus,
            .stSelectbox > div:focus-within,
            .stTextInput > div:focus-within {
                outline: 3px solid #0066CC !important;
                outline-offset: 2px !important;
            }
            </style>
            """)
        
        if self.settings.text_spacing_increased:
            css_parts.append("""
            <style>
            .stApp {
                line-height: 1.6 !important;
                letter-spacing: 0.05em !important;
            }
            </style>
            """)
        
        if self.settings.click_target_enlarged:
            css_parts.append("""
            <style>
            .stButton > button {
                min-width: 48px !important;
                min-height: 48px !important;
            }
            .stSelectbox, .stTextInput {
                min-height: 48px !important;
            }
            </style>
            """)
        
        if not self.settings.animations_enabled:
            css_parts.append("""
            <style>
            * {
                animation: none !important;
                transition: none !important;
            }
            </style>
            """)
        
        return '\n'.join(css_parts)
    
    def apply_accessibility_styles(self):
        """アクセシビリティスタイルの適用"""
        css = self.get_accessibility_css()
        if css:
            st.markdown(css, unsafe_allow_html=True)
    
    def announce_to_screen_reader(self, message: str, priority: str = "polite"):
        """スクリーンリーダー向けアナウンス"""
        if not self.settings.screen_reader_enabled:
            return
        
        announcement = {
            'message': message,
            'priority': priority,  # "polite" or "assertive"
            'timestamp': st.timestamp()
        }
        
        st.session_state.screen_reader_announcements.append(announcement)
        
        # ARIAライブリージョンの更新
        aria_live = "polite" if priority == "polite" else "assertive"
        st.markdown(
            f'<div aria-live="{aria_live}" style="position: absolute; left: -10000px;">{message}</div>',
            unsafe_allow_html=True
        )
    
    def create_accessible_button(self, label: str, key: str = None, 
                                help_text: str = None, **kwargs) -> bool:
        """アクセシブルなボタンの作成"""
        button_html = f"""
        <button 
            type="button" 
            aria-label="{label}"
            {f'aria-describedby="{key}_help"' if help_text else ''}
            onclick="document.getElementById('{key or label}_trigger').click()"
            style="
                background-color: var(--primary-color, #FF4B4B);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 0.25rem;
                cursor: pointer;
                font-size: 1rem;
                min-height: 44px;
                min-width: 44px;
            "
        >
            {label}
        </button>
        """
        
        if help_text:
            button_html += f'<div id="{key}_help" style="display: none;">{help_text}</div>'
        
        st.markdown(button_html, unsafe_allow_html=True)
        
        # 隠しボタンで実際のクリックハンドリング
        return st.button(label, key=f"{key or label}_trigger", 
                        help=help_text, **kwargs)
    
    def render_skip_links(self):
        """スキップリンクの表示"""
        skip_links_html = """
        <style>
        .skip-links {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            z-index: 1000;
            text-decoration: none;
            border-radius: 4px;
        }
        .skip-links:focus {
            top: 6px;
        }
        </style>
        <a href="#main-content" class="skip-links">メインコンテンツにスキップ</a>
        <a href="#navigation" class="skip-links">ナビゲーションにスキップ</a>
        """
        st.markdown(skip_links_html, unsafe_allow_html=True)
    
    def handle_keyboard_navigation(self, elements: List[str]):
        """キーボードナビゲーション処理"""
        if not self.settings.keyboard_navigation_enabled:
            return
        
        # キーボードイベントハンドラーのJavaScript
        keyboard_js = f"""
        <script>
        document.addEventListener('keydown', function(e) {{
            const elements = {elements};
            let currentIndex = {st.session_state.keyboard_focus_index};
            
            if (e.key === 'Tab') {{
                if (e.shiftKey) {{
                    currentIndex = Math.max(0, currentIndex - 1);
                }} else {{
                    currentIndex = Math.min(elements.length - 1, currentIndex + 1);
                }}
                
                // フォーカス更新のためのStreamlitイベント送信
                window.parent.postMessage({{
                    type: 'streamlit:setFocus',
                    index: currentIndex
                }}, '*');
            }}
            
            if (e.key === 'Enter' || e.key === ' ') {{
                const currentElement = document.getElementById(elements[currentIndex]);
                if (currentElement) {{
                    currentElement.click();
                    e.preventDefault();
                }}
            }}
        }});
        </script>
        """
        st.markdown(keyboard_js, unsafe_allow_html=True)


def get_accessibility_toolset() -> AccessibilityToolset:
    """アクセシビリティツールセットのシングルトン取得"""
    if 'accessibility_toolset' not in st.session_state:
        st.session_state.accessibility_toolset = AccessibilityToolset()
    return st.session_state.accessibility_toolset


def render_accessibility_settings():
    """アクセシビリティ設定UI"""
    toolset = get_accessibility_toolset()
    settings = toolset.settings
    
    st.subheader("♿ アクセシビリティ設定")
    
    # カラースキーム設定
    st.write("**カラースキーム**")
    color_scheme_options = {
        "デフォルト": ColorScheme.DEFAULT,
        "ハイコントラスト": ColorScheme.HIGH_CONTRAST,
        "ダークモード": ColorScheme.DARK_MODE,
        "ライトモード": ColorScheme.LIGHT_MODE,
        "緑色覚異常対応": ColorScheme.DEUTERANOPIA,
        "赤色覚異常対応": ColorScheme.PROTANOPIA,
        "青色覚異常対応": ColorScheme.TRITANOPIA
    }
    
    current_scheme = [k for k, v in color_scheme_options.items() 
                     if v == settings.color_scheme][0]
    
    new_scheme_name = st.selectbox(
        "カラースキームを選択",
        list(color_scheme_options.keys()),
        index=list(color_scheme_options.keys()).index(current_scheme),
        help="視覚的なニーズに合わせてカラースキームを選択してください"
    )
    
    new_scheme = color_scheme_options[new_scheme_name]
    if new_scheme != settings.color_scheme:
        settings.color_scheme = new_scheme
        toolset.announce_to_screen_reader(f"カラースキームを{new_scheme_name}に変更しました")
    
    # フォントサイズ設定
    st.write("**フォントサイズ**")
    font_size_options = {
        "小": FontSize.SMALL,
        "中（標準）": FontSize.MEDIUM,
        "大": FontSize.LARGE,
        "特大": FontSize.EXTRA_LARGE
    }
    
    current_font = [k for k, v in font_size_options.items() 
                   if v == settings.font_size][0]
    
    new_font_name = st.selectbox(
        "フォントサイズを選択",
        list(font_size_options.keys()),
        index=list(font_size_options.keys()).index(current_font),
        help="読みやすいフォントサイズを選択してください"
    )
    
    new_font = font_size_options[new_font_name]
    if new_font != settings.font_size:
        settings.font_size = new_font
        toolset.announce_to_screen_reader(f"フォントサイズを{new_font_name}に変更しました")
    
    # その他の設定
    st.write("**支援機能**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_screen_reader = st.checkbox(
            "スクリーンリーダー対応",
            value=settings.screen_reader_enabled,
            help="スクリーンリーダー用の音声案内を有効にします"
        )
        if new_screen_reader != settings.screen_reader_enabled:
            settings.screen_reader_enabled = new_screen_reader
            message = "スクリーンリーダー対応を有効にしました" if new_screen_reader else "スクリーンリーダー対応を無効にしました"
            toolset.announce_to_screen_reader(message)
        
        new_keyboard = st.checkbox(
            "キーボードナビゲーション",
            value=settings.keyboard_navigation_enabled,
            help="キーボードでの操作を有効にします"
        )
        if new_keyboard != settings.keyboard_navigation_enabled:
            settings.keyboard_navigation_enabled = new_keyboard
        
        new_focus = st.checkbox(
            "強化フォーカス表示",
            value=settings.focus_indicators_enhanced,
            help="フォーカス表示を強化して見やすくします"
        )
        if new_focus != settings.focus_indicators_enhanced:
            settings.focus_indicators_enhanced = new_focus
        
        new_spacing = st.checkbox(
            "文字間隔拡大",
            value=settings.text_spacing_increased,
            help="テキストの行間・文字間隔を広げます"
        )
        if new_spacing != settings.text_spacing_increased:
            settings.text_spacing_increased = new_spacing
    
    with col2:
        new_animations = st.checkbox(
            "アニメーション有効",
            value=settings.animations_enabled,
            help="画面のアニメーション効果を制御します"
        )
        if new_animations != settings.animations_enabled:
            settings.animations_enabled = new_animations
        
        new_autoplay = st.checkbox(
            "自動再生無効",
            value=settings.auto_play_disabled,
            help="音声・動画の自動再生を無効にします"
        )
        if new_autoplay != settings.auto_play_disabled:
            settings.auto_play_disabled = new_autoplay
        
        new_targets = st.checkbox(
            "クリック対象拡大",
            value=settings.click_target_enlarged,
            help="ボタンなどのクリック対象を大きくします"
        )
        if new_targets != settings.click_target_enlarged:
            settings.click_target_enlarged = new_targets
    
    # 設定保存
    if st.button("💾 アクセシビリティ設定を保存", type="primary"):
        if toolset.save_settings():
            st.success("設定を保存しました")
            toolset.announce_to_screen_reader("アクセシビリティ設定を保存しました")
        else:
            st.error("設定の保存に失敗しました")
            toolset.announce_to_screen_reader("設定の保存に失敗しました")
    
    # 設定のプレビュー
    st.write("**設定プレビュー**")
    with st.expander("現在の設定を確認"):
        st.write(f"- カラースキーム: {new_scheme_name}")
        st.write(f"- フォントサイズ: {new_font_name}")
        st.write(f"- スクリーンリーダー: {'有効' if new_screen_reader else '無効'}")
        st.write(f"- キーボードナビゲーション: {'有効' if new_keyboard else '無効'}")
        st.write(f"- 強化フォーカス: {'有効' if new_focus else '無効'}")
        st.write(f"- 文字間隔拡大: {'有効' if new_spacing else '無効'}")
        st.write(f"- アニメーション: {'有効' if new_animations else '無効'}")
        st.write(f"- 自動再生無効: {'有効' if new_autoplay else '無効'}")
        st.write(f"- クリック対象拡大: {'有効' if new_targets else '無効'}")


def render_accessibility_demo():
    """アクセシビリティ機能のデモ"""
    toolset = get_accessibility_toolset()
    
    st.subheader("🎯 アクセシビリティ機能デモ")
    
    # スキップリンクのデモ
    toolset.render_skip_links()
    
    # アクセシブルボタンのデモ
    st.write("**アクセシブルボタンの例**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if toolset.create_accessible_button(
            "🔊 音声案内", 
            key="voice_demo",
            help_text="音声案内機能をテストします"
        ):
            toolset.announce_to_screen_reader("音声案内機能をテストしています", "assertive")
            st.success("音声案内を実行しました")
    
    with col2:
        if toolset.create_accessible_button(
            "⌨️ キーボード", 
            key="keyboard_demo",
            help_text="キーボードナビゲーションをテストします"
        ):
            elements = ["voice_demo", "keyboard_demo", "focus_demo"]
            toolset.handle_keyboard_navigation(elements)
            st.info("キーボードナビゲーションが有効です")
    
    with col3:
        if toolset.create_accessible_button(
            "🎯 フォーカス", 
            key="focus_demo",
            help_text="フォーカス表示をテストします"
        ):
            st.info("フォーカス表示機能をテストしました")
    
    # カラーパレットのデモ
    st.write("**色覚対応カラーパレット**")
    color_demo_cols = st.columns(4)
    
    with color_demo_cols[0]:
        st.success("成功メッセージ")
    with color_demo_cols[1]:
        st.error("エラーメッセージ")
    with color_demo_cols[2]:
        st.warning("警告メッセージ")
    with color_demo_cols[3]:
        st.info("情報メッセージ")
    
    # テキスト可読性のデモ
    st.write("**テキスト可読性**")
    st.markdown("""
    これは通常のテキストです。アクセシビリティ設定により、
    フォントサイズや行間が調整されて読みやすくなります。
    
    **太字のテキスト**や*斜体のテキスト*も適切に表示されます。
    """)
    
    # フォーム要素のアクセシビリティデモ
    st.write("**アクセシブルフォーム要素**")
    
    form_col1, form_col2 = st.columns(2)
    
    with form_col1:
        user_name = st.text_input(
            "お名前",
            help="あなたのお名前を入力してください",
            placeholder="例: 田中太郎"
        )
        
        user_age = st.selectbox(
            "年齢層",
            ["20代未満", "20代", "30代", "40代", "50代", "60代以上"],
            help="最適な表示設定のために年齢層を選択してください"
        )
    
    with form_col2:
        accessibility_needs = st.multiselect(
            "必要なアクセシビリティ機能",
            [
                "スクリーンリーダー対応",
                "ハイコントラスト表示",
                "大きなフォント",
                "キーボードナビゲーション",
                "色覚対応"
            ],
            help="必要な機能を選択してください（複数選択可）"
        )
        
        notifications = st.checkbox(
            "音声通知を有効にする",
            help="重要な操作で音声による通知を行います"
        )
    
    if st.button("✨ アクセシビリティプロフィールを作成"):
        if user_name:
            profile_info = f"""
            プロフィールを作成しました:
            - お名前: {user_name}
            - 年齢層: {user_age}
            - 必要な機能: {', '.join(accessibility_needs) if accessibility_needs else 'なし'}
            - 音声通知: {'有効' if notifications else '無効'}
            """
            st.success("アクセシビリティプロフィールを作成しました")
            st.code(profile_info)
            
            if toolset.settings.screen_reader_enabled:
                toolset.announce_to_screen_reader(
                    f"{user_name}さんのアクセシビリティプロフィールを作成しました"
                )
        else:
            st.error("お名前を入力してください")
            if toolset.settings.screen_reader_enabled:
                toolset.announce_to_screen_reader("お名前の入力が必要です", "assertive")


if __name__ == "__main__":
    # デモ実行
    st.title("♿ アクセシビリティツールセット")
    
    toolset = get_accessibility_toolset()
    toolset.apply_accessibility_styles()
    
    tab1, tab2 = st.tabs(["設定", "デモ"])
    
    with tab1:
        render_accessibility_settings()
    
    with tab2:
        render_accessibility_demo()
