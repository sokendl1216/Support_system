# -*- coding: utf-8 -*-
"""
レスポンシブUIコンポーネントライブラリ

各種UIコンポーネントのレスポンシブ対応版を提供します。
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Union, Callable
from ui.components.responsive_ui import get_responsive_ui, DeviceType, apply_responsive_css
from ui.components.buttons import primary_button


class ResponsiveComponents:
    """レスポンシブUIコンポーネントクラス"""
    
    def __init__(self):
        self.responsive_ui = get_responsive_ui()
    
    def render_adaptive_header(self, title: str, subtitle: str = "", 
                              icon: str = "", level: int = 1) -> None:
        """適応型ヘッダー表示"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        # デバイス別のヘッダーサイズ調整
        if screen_size.is_mobile:
            if level == 1:
                header_func = st.title
            else:
                header_func = st.header
            icon_size = "1.2em"
        elif screen_size.is_tablet:
            if level == 1:
                header_func = st.title
            else:
                header_func = st.header
            icon_size = "1.5em"
        else:
            if level == 1:
                header_func = st.title
            else:
                header_func = st.header
            icon_size = "1.8em"
        
        # ヘッダー表示
        if icon:
            display_title = f"{icon} {title}"
        else:
            display_title = title
        
        header_func(display_title)
        
        if subtitle:
            if screen_size.is_mobile:
                st.caption(subtitle)
            else:
                st.subheader(subtitle)
    
    def render_adaptive_button_group(self, buttons: List[Dict[str, Any]], 
                                   layout: str = "auto") -> Optional[str]:
        """適応型ボタングループ"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        # レイアウト決定
        if layout == "auto":
            if screen_size.is_mobile:
                layout = "vertical"
            elif screen_size.is_tablet:
                layout = "grid"
            else:
                layout = "horizontal"
        
        clicked_button = None
        
        if layout == "vertical":
            # 縦型レイアウト（モバイル）
            for button in buttons:
                if st.button(
                    button['label'], 
                    key=button.get('key'),
                    help=button.get('help'),
                    use_container_width=True
                ):
                    clicked_button = button['value']
        
        elif layout == "horizontal":
            # 横型レイアウト（デスクトップ）
            cols = st.columns(len(buttons))
            for i, button in enumerate(buttons):
                with cols[i]:
                    if st.button(
                        button['label'], 
                        key=button.get('key'),
                        help=button.get('help'),
                        use_container_width=True
                    ):
                        clicked_button = button['value']
        
        elif layout == "grid":
            # グリッドレイアウト（タブレット）
            cols_per_row = 2 if screen_size.is_tablet else 3
            for i in range(0, len(buttons), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, button in enumerate(buttons[i:i+cols_per_row]):
                    with cols[j]:
                        if st.button(
                            button['label'], 
                            key=button.get('key'),
                            help=button.get('help'),
                            use_container_width=True
                        ):
                            clicked_button = button['value']
        
        return clicked_button
    
    def render_adaptive_form(self, form_config: Dict[str, Any]) -> Dict[str, Any]:
        """適応型フォーム"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        form_data = {}
        
        with st.form(form_config.get('key', 'responsive_form')):
            if screen_size.is_mobile:
                # モバイル: 1カラムレイアウト
                for field in form_config['fields']:
                    form_data[field['name']] = self._render_form_field(field, full_width=True)
            
            elif screen_size.is_tablet:
                # タブレット: 2カラムレイアウト
                for i in range(0, len(form_config['fields']), 2):
                    cols = st.columns(2)
                    for j, field in enumerate(form_config['fields'][i:i+2]):
                        with cols[j]:
                            form_data[field['name']] = self._render_form_field(field)
            
            else:
                # デスクトップ: 3カラムレイアウト（または指定に従う）
                cols_per_row = form_config.get('desktop_columns', 3)
                for i in range(0, len(form_config['fields']), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, field in enumerate(form_config['fields'][i:i+cols_per_row]):
                        with cols[j]:
                            form_data[field['name']] = self._render_form_field(field)
            
            # サブミットボタン
            submitted = st.form_submit_button(
                form_config.get('submit_label', '送信'),
                use_container_width=screen_size.is_mobile
            )
        
        return form_data if submitted else {}
    
    def _render_form_field(self, field: Dict[str, Any], full_width: bool = False) -> Any:
        """フォームフィールドレンダリング"""
        field_type = field['type']
        label = field['label']
        key = field.get('key', field['name'])
        
        if field_type == 'text':
            return st.text_input(label, key=key, help=field.get('help'))
        elif field_type == 'textarea':
            return st.text_area(label, key=key, help=field.get('help'))
        elif field_type == 'number':
            return st.number_input(
                label, 
                min_value=field.get('min_value'),
                max_value=field.get('max_value'),
                value=field.get('default_value', 0),
                key=key,
                help=field.get('help')
            )
        elif field_type == 'select':
            return st.selectbox(label, field['options'], key=key, help=field.get('help'))
        elif field_type == 'multiselect':
            return st.multiselect(label, field['options'], key=key, help=field.get('help'))
        elif field_type == 'checkbox':
            return st.checkbox(label, value=field.get('default_value', False), key=key, help=field.get('help'))
        elif field_type == 'radio':
            return st.radio(label, field['options'], key=key, help=field.get('help'))
        elif field_type == 'slider':
            return st.slider(
                label,
                min_value=field.get('min_value', 0),
                max_value=field.get('max_value', 100),
                value=field.get('default_value', 50),
                key=key,
                help=field.get('help')
            )
        elif field_type == 'date':
            return st.date_input(label, key=key, help=field.get('help'))
        elif field_type == 'time':
            return st.time_input(label, key=key, help=field.get('help'))
        elif field_type == 'file':
            return st.file_uploader(label, key=key, help=field.get('help'))
        else:
            st.warning(f"未対応のフィールドタイプ: {field_type}")
            return None
    
    def render_adaptive_data_display(self, data: List[Dict], display_type: str = "auto") -> None:
        """適応型データ表示"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        if display_type == "auto":
            if screen_size.is_mobile:
                display_type = "cards"
            elif screen_size.is_tablet:
                display_type = "grid"
            else:
                display_type = "table"
        
        if display_type == "table":
            # テーブル表示（デスクトップ）
            st.dataframe(data, use_container_width=True)
        
        elif display_type == "cards":
            # カード表示（モバイル）
            for item in data:
                with st.container():
                    self.responsive_ui.render_responsive_card(
                        title=str(item.get('title', item.get('name', '項目'))),
                        content=self._format_card_content(item),
                        icon=item.get('icon', '📄')
                    )
        
        elif display_type == "grid":
            # グリッド表示（タブレット）
            self.responsive_ui.create_responsive_grid([
                {
                    'title': str(item.get('title', item.get('name', '項目'))),
                    'content': self._format_card_content(item),
                    'icon': item.get('icon', '📄')
                }
                for item in data
            ])
    
    def _format_card_content(self, item: Dict) -> str:
        """カードコンテンツのフォーマット"""
        content_parts = []
        for key, value in item.items():
            if key not in ['title', 'name', 'icon']:
                content_parts.append(f"**{key}:** {value}")
        return "<br>".join(content_parts)
    
    def render_adaptive_metrics(self, metrics: List[Dict[str, Any]]) -> None:
        """適応型メトリクス表示"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        if screen_size.is_mobile:
            # モバイル: 縦型レイアウト
            for metric in metrics:
                st.metric(
                    label=metric['label'],
                    value=metric['value'],
                    delta=metric.get('delta'),
                    help=metric.get('help')
                )
        
        elif screen_size.is_tablet:
            # タブレット: 2カラム
            for i in range(0, len(metrics), 2):
                cols = st.columns(2)
                for j, metric in enumerate(metrics[i:i+2]):
                    with cols[j]:
                        st.metric(
                            label=metric['label'],
                            value=metric['value'],
                            delta=metric.get('delta'),
                            help=metric.get('help')
                        )
        
        else:
            # デスクトップ: 3-4カラム
            cols_per_row = min(4, len(metrics))
            for i in range(0, len(metrics), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, metric in enumerate(metrics[i:i+cols_per_row]):
                    with cols[j]:
                        st.metric(
                            label=metric['label'],
                            value=metric['value'],
                            delta=metric.get('delta'),
                            help=metric.get('help')
                        )
    
    def render_adaptive_navigation(self, nav_items: List[Dict], current_page: str = "") -> str:
        """適応型ナビゲーション"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        if screen_size.is_mobile:
            # モバイル: セレクトボックス
            options = [item['label'] for item in nav_items]
            if current_page:
                try:
                    index = next(i for i, item in enumerate(nav_items) if item['value'] == current_page)
                except StopIteration:
                    index = 0
            else:
                index = 0
            
            selected_label = st.selectbox(
                "ページ選択",
                options,
                index=index,
                key="responsive_nav_mobile"
            )
            
            # 選択されたアイテムの値を返す
            return next(item['value'] for item in nav_items if item['label'] == selected_label)
        
        else:
            # タブレット・デスクトップ: タブまたはサイドバー
            options = [item['label'] for item in nav_items]
            if current_page:
                try:
                    index = next(i for i, item in enumerate(nav_items) if item['value'] == current_page)
                except StopIteration:
                    index = 0
            else:
                index = 0
            
            selected_label = st.radio(
                "ナビゲーション",
                options,
                index=index,
                horizontal=True,
                key="responsive_nav_desktop"
            )
            
            return next(item['value'] for item in nav_items if item['label'] == selected_label)
    
    def render_responsive_layout(self, content_config: Dict[str, Any]) -> None:
        """レスポンシブレイアウト全体管理"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        # CSS適用
        apply_responsive_css()
        
        # ページ設定
        if screen_size.is_mobile:
            # モバイル設定
            st.set_page_config(
                page_title=content_config.get('title', 'AI支援システム'),
                page_icon=content_config.get('icon', '🤖'),
                layout="centered",
                initial_sidebar_state="collapsed"
            )
        else:
            # デスクトップ・タブレット設定
            st.set_page_config(
                page_title=content_config.get('title', 'AI支援システム'),
                page_icon=content_config.get('icon', '🤖'),
                layout="wide",
                initial_sidebar_state="expanded"
            )
    
    def render_adaptive_sidebar(self, sidebar_config: Dict[str, Any]) -> None:
        """適応型サイドバー"""
        screen_size = self.responsive_ui.get_current_screen_size()
        
        if screen_size.is_mobile:
            # モバイル: エクスパンダーとして表示
            with st.expander("メニュー", expanded=False):
                self._render_sidebar_content(sidebar_config)
        else:
            # デスクトップ・タブレット: 通常のサイドバー
            with st.sidebar:
                self._render_sidebar_content(sidebar_config)
    
    def _render_sidebar_content(self, sidebar_config: Dict[str, Any]) -> None:
        """サイドバーコンテンツ描画"""
        if 'title' in sidebar_config:
            st.title(sidebar_config['title'])
        
        if 'sections' in sidebar_config:
            for section in sidebar_config['sections']:
                if section['type'] == 'navigation':
                    # ナビゲーション
                    for item in section['items']:
                        if st.button(item['label'], key=item.get('key')):
                            st.session_state.current_page = item['value']
                
                elif section['type'] == 'info':
                    # 情報表示
                    st.markdown(f"### {section['title']}")
                    for item in section['items']:
                        st.markdown(f"- {item}")
                
                elif section['type'] == 'metrics':
                    # メトリクス
                    st.markdown(f"### {section['title']}")
                    for metric in section['items']:
                        st.metric(
                            label=metric['label'],
                            value=metric['value'],
                            delta=metric.get('delta')
                        )
                
                st.markdown("---")


# グローバルインスタンス
_responsive_components = None

def get_responsive_components() -> ResponsiveComponents:
    """レスポンシブコンポーネントのシングルトンインスタンスを取得"""
    global _responsive_components
    if _responsive_components is None:
        _responsive_components = ResponsiveComponents()
    return _responsive_components


# 便利関数
def adaptive_header(title: str, subtitle: str = "", icon: str = "", level: int = 1):
    """適応型ヘッダーの便利関数"""
    components = get_responsive_components()
    components.render_adaptive_header(title, subtitle, icon, level)

def adaptive_button_group(buttons: List[Dict[str, Any]], layout: str = "auto") -> Optional[str]:
    """適応型ボタングループの便利関数"""
    components = get_responsive_components()
    return components.render_adaptive_button_group(buttons, layout)

def adaptive_form(form_config: Dict[str, Any]) -> Dict[str, Any]:
    """適応型フォームの便利関数"""
    components = get_responsive_components()
    return components.render_adaptive_form(form_config)

def adaptive_data_display(data: List[Dict], display_type: str = "auto"):
    """適応型データ表示の便利関数"""
    components = get_responsive_components()
    components.render_adaptive_data_display(data, display_type)

def adaptive_metrics(metrics: List[Dict[str, Any]]):
    """適応型メトリクス表示の便利関数"""
    components = get_responsive_components()
    components.render_adaptive_metrics(metrics)
