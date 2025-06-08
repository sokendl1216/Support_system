# -*- coding: utf-8 -*-
"""
レスポンシブUI最適化システム

様々なデバイス・画面サイズに対応したレスポンシブUI機能を提供します。
タスク4-10: レスポンシブUI最適化の実装
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DeviceType(Enum):
    """デバイスタイプ列挙"""
    MOBILE = "mobile"          # スマートフォン (< 768px)
    TABLET = "tablet"          # タブレット (768px - 1024px)
    DESKTOP = "desktop"        # デスクトップ (> 1024px)
    LARGE_DESKTOP = "large"    # 大画面デスクトップ (> 1440px)


@dataclass
class ScreenSize:
    """画面サイズ情報"""
    width: int
    height: int
    device_type: DeviceType
    is_mobile: bool
    is_tablet: bool
    is_desktop: bool


@dataclass
class ResponsiveLayout:
    """レスポンシブレイアウト設定"""
    mobile_columns: List[Union[int, float]]
    tablet_columns: List[Union[int, float]]
    desktop_columns: List[Union[int, float]]
    mobile_gap: str = "1rem"
    tablet_gap: str = "1.5rem"
    desktop_gap: str = "2rem"


class ResponsiveUIManager:
    """レスポンシブUI管理クラス"""
    
    def __init__(self):
        self.current_screen_size: Optional[ScreenSize] = None
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'large': 1440
        }
    
    def detect_device_type(self) -> DeviceType:
        """デバイスタイプの検出（JavaScript経由）"""
        # StreamlitのJavaScript実行機能を使用してクライアント画面サイズを取得
        js_code = """
        <script>
        function getScreenInfo() {
            return {
                width: window.innerWidth,
                height: window.innerHeight,
                userAgent: navigator.userAgent
            };
        }
        
        // Streamlitに画面情報を送信
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: getScreenInfo()
        }, '*');
        </script>
        """
        
        # デフォルト値として中型画面を設定
        width = st.session_state.get('screen_width', 1024)
        
        if width < self.breakpoints['mobile']:
            return DeviceType.MOBILE
        elif width < self.breakpoints['tablet']:
            return DeviceType.TABLET
        elif width < self.breakpoints['large']:
            return DeviceType.DESKTOP
        else:
            return DeviceType.LARGE_DESKTOP
    
    def get_current_screen_size(self) -> ScreenSize:
        """現在の画面サイズ情報を取得"""
        if self.current_screen_size is None:
            device_type = self.detect_device_type()
            width = st.session_state.get('screen_width', 1024)
            height = st.session_state.get('screen_height', 768)
            
            self.current_screen_size = ScreenSize(
                width=width,
                height=height,
                device_type=device_type,
                is_mobile=device_type == DeviceType.MOBILE,
                is_tablet=device_type == DeviceType.TABLET,
                is_desktop=device_type in [DeviceType.DESKTOP, DeviceType.LARGE_DESKTOP]
            )
        
        return self.current_screen_size
    
    def create_responsive_columns(self, layout: ResponsiveLayout) -> List:
        """レスポンシブカラム作成"""
        screen_size = self.get_current_screen_size()
        
        if screen_size.is_mobile:
            return st.columns(layout.mobile_columns)
        elif screen_size.is_tablet:
            return st.columns(layout.tablet_columns)
        else:
            return st.columns(layout.desktop_columns)
    
    def apply_responsive_styling(self) -> str:
        """レスポンシブスタイリングの適用"""
        screen_size = self.get_current_screen_size()
        
        base_css = """
        <style>
        /* レスポンシブベーススタイル */
        .main .block-container {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* モバイルスタイル */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            .stButton button {
                width: 100%;
                margin-bottom: 0.5rem;
            }
            
            .stSelectbox, .stTextInput, .stTextArea {
                width: 100%;
            }
            
            .responsive-card {
                margin-bottom: 1rem;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        }
        
        /* タブレットスタイル */
        @media (min-width: 769px) and (max-width: 1024px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            
            .responsive-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 1.5rem;
            }
        }
        
        /* デスクトップスタイル */
        @media (min-width: 1025px) {
            .main .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
            }
            
            .responsive-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 2rem;
            }
            
            .sidebar-layout {
                display: flex;
                gap: 2rem;
            }
            
            .main-content {
                flex: 2;
            }
            
            .sidebar-content {
                flex: 1;
            }
        }
        
        /* 大画面デスクトップスタイル */
        @media (min-width: 1441px) {
            .main .block-container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .responsive-grid {
                grid-template-columns: repeat(4, 1fr);
                gap: 2.5rem;
            }
        }
        
        /* 共通スタイル */
        .responsive-text {
            font-size: clamp(0.875rem, 2.5vw, 1.125rem);
            line-height: 1.6;
        }
        
        .responsive-heading {
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            line-height: 1.2;
            margin-bottom: 1rem;
        }
        
        .responsive-button {
            font-size: clamp(0.875rem, 2vw, 1rem);
            padding: clamp(0.5rem, 2vw, 1rem) clamp(1rem, 3vw, 2rem);
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .responsive-image {
            width: 100%;
            height: auto;
            border-radius: 8px;
        }
        
        /* アクセシビリティ考慮 */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* 高コントラストモード */
        @media (prefers-contrast: high) {
            .responsive-card {
                border: 2px solid #000;
            }
        }
        
        /* フォーカス表示強化 */
        .stButton button:focus,
        .stSelectbox select:focus,
        .stTextInput input:focus {
            outline: 3px solid #4CAF50;
            outline-offset: 2px;
        }
        </style>
        """
        
        return base_css
    
    def render_responsive_card(self, title: str, content: str, icon: str = "📄") -> None:
        """レスポンシブカード表示"""
        screen_size = self.get_current_screen_size()
        
        # デバイス別のスタイル調整
        if screen_size.is_mobile:
            padding = "0.75rem"
            title_size = "### "
        elif screen_size.is_tablet:
            padding = "1rem"
            title_size = "### "
        else:
            padding = "1.25rem"
            title_size = "### "
        
        card_html = f"""
        <div class="responsive-card" style="padding: {padding};">
            <h3 style="margin-bottom: 0.5rem;">{icon} {title}</h3>
            <div class="responsive-text">{content}</div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
    
    def create_responsive_grid(self, items: List[Dict], max_columns: int = 3) -> None:
        """レスポンシブグリッドレイアウト"""
        screen_size = self.get_current_screen_size()
        
        # デバイス別カラム数決定
        if screen_size.is_mobile:
            cols = 1
        elif screen_size.is_tablet:
            cols = min(2, max_columns)
        elif screen_size.device_type == DeviceType.DESKTOP:
            cols = min(3, max_columns)
        else:  # LARGE_DESKTOP
            cols = min(4, max_columns)
        
        # グリッド表示
        for i in range(0, len(items), cols):
            columns = st.columns(cols)
            for j, item in enumerate(items[i:i+cols]):
                with columns[j]:
                    if 'title' in item and 'content' in item:
                        self.render_responsive_card(
                            item['title'],
                            item['content'],
                            item.get('icon', '📄')
                        )
    
    def adapt_layout_for_device(self, mobile_layout: callable, 
                               tablet_layout: callable = None,
                               desktop_layout: callable = None) -> None:
        """デバイス別レイアウト適用"""
        screen_size = self.get_current_screen_size()
        
        if screen_size.is_mobile:
            mobile_layout()
        elif screen_size.is_tablet and tablet_layout:
            tablet_layout()
        elif screen_size.is_desktop and desktop_layout:
            desktop_layout()
        else:
            # フォールバック: モバイルレイアウトを使用
            mobile_layout()
    
    def render_responsive_navigation(self, nav_items: List[Dict], layout: str = "horizontal") -> str:
        """レスポンシブナビゲーション"""
        screen_size = self.get_current_screen_size()
        
        # モバイルでは縦型、デスクトップでは横型
        if screen_size.is_mobile or layout == "vertical":
            # 縦型ナビゲーション
            selected = st.selectbox(
                "ナビゲーション",
                [item['label'] for item in nav_items],
                key="responsive_nav"
            )
        else:
            # 横型ナビゲーション（タブ）
            selected = st.radio(
                "ナビゲーション",
                [item['label'] for item in nav_items],
                horizontal=True,
                key="responsive_nav_tabs"
            )
        
        return selected
    
    def get_optimal_image_size(self, base_width: int, base_height: int) -> Tuple[str, str]:
        """最適画像サイズ取得"""
        screen_size = self.get_current_screen_size()
        
        if screen_size.is_mobile:
            width = min(base_width, screen_size.width - 40)  # マージン考慮
            ratio = width / base_width
            height = int(base_height * ratio)
        elif screen_size.is_tablet:
            width = min(base_width, int(screen_size.width * 0.8))
            ratio = width / base_width
            height = int(base_height * ratio)
        else:
            width = base_width
            height = base_height
        
        return f"{width}px", f"{height}px"
    
    def render_responsive_sidebar(self, sidebar_content: List[Dict]) -> None:
        """レスポンシブサイドバー"""
        screen_size = self.get_current_screen_size()
        
        if screen_size.is_mobile:
            # モバイル: エキスパンダーとして表示
            with st.expander("メニュー", expanded=False):
                for item in sidebar_content:
                    if item['type'] == 'button':
                        st.button(item['label'], key=item.get('key'))
                    elif item['type'] == 'selectbox':
                        st.selectbox(item['label'], item['options'], key=item.get('key'))
                    elif item['type'] == 'info':
                        st.info(item['content'])
        else:
            # タブレット・デスクトップ: 通常のサイドバー
            with st.sidebar:
                for item in sidebar_content:
                    if item['type'] == 'button':
                        st.button(item['label'], key=item.get('key'))
                    elif item['type'] == 'selectbox':
                        st.selectbox(item['label'], item['options'], key=item.get('key'))
                    elif item['type'] == 'info':
                        st.info(item['content'])


# グローバルインスタンス
_responsive_ui_manager = None

def get_responsive_ui() -> ResponsiveUIManager:
    """レスポンシブUIマネージャーのシングルトンインスタンスを取得"""
    global _responsive_ui_manager
    if _responsive_ui_manager is None:
        _responsive_ui_manager = ResponsiveUIManager()
    return _responsive_ui_manager


# 便利関数
def apply_responsive_css():
    """レスポンシブCSSを適用"""
    responsive_ui = get_responsive_ui()
    css = responsive_ui.apply_responsive_styling()
    st.markdown(css, unsafe_allow_html=True)

def responsive_columns(mobile: List, tablet: List = None, desktop: List = None):
    """レスポンシブカラム作成の便利関数"""
    if tablet is None:
        tablet = mobile
    if desktop is None:
        desktop = tablet
    
    layout = ResponsiveLayout(
        mobile_columns=mobile,
        tablet_columns=tablet,
        desktop_columns=desktop
    )
    
    responsive_ui = get_responsive_ui()
    return responsive_ui.create_responsive_columns(layout)

def is_mobile_device() -> bool:
    """モバイルデバイス判定"""
    responsive_ui = get_responsive_ui()
    screen_size = responsive_ui.get_current_screen_size()
    return screen_size.is_mobile

def get_device_type() -> DeviceType:
    """現在のデバイスタイプを取得"""
    responsive_ui = get_responsive_ui()
    screen_size = responsive_ui.get_current_screen_size()
    return screen_size.device_type
