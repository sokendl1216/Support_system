"""
Task 4-7: 高度な統合機能 - Adaptive UI System
アダプティブUIシステムの実装

機能:
- 使用パターン分析によるUI自動調整
- アクセシビリティ自動最適化
- パーソナライゼーション機能
- 動的テーマ・レイアウト調整
"""

import asyncio
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from enum import Enum
import tkinter as tk
from tkinter import ttk
import colorsys

class UIAdaptationLevel(Enum):
    """UI適応レベル"""
    MINIMAL = "minimal"      # 最小限の調整
    MODERATE = "moderate"    # 中程度の調整
    AGGRESSIVE = "aggressive" # 積極的な調整
    CUSTOM = "custom"        # カスタム設定

class AccessibilityMode(Enum):
    """アクセシビリティモード"""
    NORMAL = "normal"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    REDUCED_MOTION = "reduced_motion"
    VOICE_FOCUS = "voice_focus"

class LayoutType(Enum):
    """レイアウトタイプ"""
    COMPACT = "compact"
    STANDARD = "standard"
    SPACIOUS = "spacious"
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

@dataclass
class UIMetrics:
    """UI使用メトリクス"""
    element_id: str
    element_type: str
    usage_count: int = 0
    total_time: float = 0.0
    error_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    user_satisfaction: float = 0.0
    accessibility_issues: List[str] = field(default_factory=list)

@dataclass
class UserPreferences:
    """ユーザー設定"""
    font_size: int = 11
    theme: str = "default"
    layout: LayoutType = LayoutType.STANDARD
    accessibility_mode: AccessibilityMode = AccessibilityMode.NORMAL
    color_scheme: str = "light"
    animation_speed: float = 1.0
    voice_priority: bool = False
    high_contrast: bool = False
    reduced_motion: bool = False

@dataclass
class UIElement:
    """UI要素定義"""
    element_id: str
    element_type: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    visible: bool = True
    priority: int = 1
    accessibility_role: str = ""
    tooltip: str = ""
    voice_command: str = ""

class UsageAnalyzer:
    """使用パターン分析エンジン"""
    
    def __init__(self):
        self.metrics: Dict[str, UIMetrics] = {}
        self.interaction_history: List[Dict] = []
        self.analysis_window = timedelta(days=7)
        
    def record_interaction(self, element_id: str, element_type: str, 
                         interaction_type: str, duration: float = 0.0,
                         success: bool = True):
        """インタラクション記録"""
        timestamp = datetime.now()
        
        # 履歴記録
        interaction = {
            'element_id': element_id,
            'element_type': element_type,
            'interaction_type': interaction_type,
            'duration': duration,
            'success': success,
            'timestamp': timestamp
        }
        self.interaction_history.append(interaction)
        
        # メトリクス更新
        if element_id not in self.metrics:
            self.metrics[element_id] = UIMetrics(
                element_id=element_id,
                element_type=element_type
            )
        
        metric = self.metrics[element_id]
        metric.usage_count += 1
        metric.total_time += duration
        metric.last_used = timestamp
        
        if not success:
            metric.error_count += 1
        
        # 満足度更新（成功率ベース）
        metric.user_satisfaction = 1.0 - (metric.error_count / metric.usage_count)
    
    def get_usage_patterns(self, timeframe: timedelta = None) -> Dict[str, Any]:
        """使用パターン分析"""
        if timeframe is None:
            timeframe = self.analysis_window
        
        cutoff = datetime.now() - timeframe
        recent_interactions = [
            i for i in self.interaction_history 
            if i['timestamp'] > cutoff
        ]
        
        patterns = {
            'most_used_elements': [],
            'least_used_elements': [],
            'error_prone_elements': [],
            'peak_usage_times': [],
            'interaction_sequences': []
        }
        
        # 最も使用される要素
        usage_counts = {}
        for interaction in recent_interactions:
            element_id = interaction['element_id']
            usage_counts[element_id] = usage_counts.get(element_id, 0) + 1
        
        sorted_usage = sorted(usage_counts.items(), key=lambda x: x[1], reverse=True)
        patterns['most_used_elements'] = sorted_usage[:10]
        patterns['least_used_elements'] = sorted_usage[-10:]
        
        # エラーの多い要素
        error_counts = {}
        for interaction in recent_interactions:
            if not interaction['success']:
                element_id = interaction['element_id']
                error_counts[element_id] = error_counts.get(element_id, 0) + 1
        
        patterns['error_prone_elements'] = sorted(
            error_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        
        return patterns
    
    def recommend_optimizations(self) -> List[Dict[str, Any]]:
        """最適化推奨"""
        patterns = self.get_usage_patterns()
        recommendations = []
        
        # よく使われる要素を目立たせる
        for element_id, count in patterns['most_used_elements'][:5]:
            recommendations.append({
                'type': 'promote_element',
                'element_id': element_id,
                'reason': f'高頻度使用 ({count}回)',
                'suggestion': '位置を上位に移動、サイズを拡大'
            })
        
        # エラーの多い要素を改善
        for element_id, error_count in patterns['error_prone_elements']:
            recommendations.append({
                'type': 'improve_element',
                'element_id': element_id,
                'reason': f'エラー率が高い ({error_count}回)',
                'suggestion': 'ツールチップ追加、確認ダイアログ追加'
            })
        
        # 未使用要素を隠す
        for element_id, count in patterns['least_used_elements']:
            if count == 0:
                recommendations.append({
                    'type': 'hide_element',
                    'element_id': element_id,
                    'reason': '未使用',
                    'suggestion': 'メニューに移動または非表示'
                })
        
        return recommendations

class AccessibilityOptimizer:
    """アクセシビリティ最適化エンジン"""
    
    def __init__(self):
        self.current_mode = AccessibilityMode.NORMAL
        self.optimization_rules = self._load_optimization_rules()
        
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """最適化ルール読み込み"""
        return {
            'font_size_adjustments': {
                AccessibilityMode.LARGE_TEXT: 1.5,
                AccessibilityMode.HIGH_CONTRAST: 1.2,
                AccessibilityMode.VOICE_FOCUS: 1.1
            },
            'color_adjustments': {
                AccessibilityMode.HIGH_CONTRAST: {
                    'background': '#000000',
                    'foreground': '#FFFFFF',
                    'accent': '#FFFF00'
                },
                AccessibilityMode.VOICE_FOCUS: {
                    'background': '#F0F8FF',
                    'foreground': '#000080',
                    'accent': '#FF4500'
                }
            },
            'motion_settings': {
                AccessibilityMode.REDUCED_MOTION: {
                    'animation_duration': 0.1,
                    'transitions': False,
                    'effects': False
                }
            }
        }
    
    def analyze_accessibility_needs(self, usage_patterns: Dict, 
                                  user_feedback: List[str] = None) -> AccessibilityMode:
        """アクセシビリティニーズ分析"""
        if user_feedback:
            # ユーザーフィードバックから判定
            feedback_text = ' '.join(user_feedback).lower()
            
            if any(word in feedback_text for word in ['見えない', '小さい', '読めない']):
                return AccessibilityMode.LARGE_TEXT
            elif any(word in feedback_text for word in ['コントラスト', '薄い', 'はっきり']):
                return AccessibilityMode.HIGH_CONTRAST
            elif any(word in feedback_text for word in ['音声', 'ボイス', '声']):
                return AccessibilityMode.VOICE_FOCUS
            elif any(word in feedback_text for word in ['動き', 'アニメーション', 'ちらつき']):
                return AccessibilityMode.REDUCED_MOTION
        
        # 使用パターンから推定
        error_elements = usage_patterns.get('error_prone_elements', [])
        if len(error_elements) > 3:
            # エラーが多い場合は大きなテキストを推奨
            return AccessibilityMode.LARGE_TEXT
        
        return AccessibilityMode.NORMAL
    
    def apply_accessibility_mode(self, mode: AccessibilityMode, 
                               preferences: UserPreferences) -> UserPreferences:
        """アクセシビリティモード適用"""
        self.current_mode = mode
        new_preferences = UserPreferences(**asdict(preferences))
        
        # フォントサイズ調整
        if mode in self.optimization_rules['font_size_adjustments']:
            multiplier = self.optimization_rules['font_size_adjustments'][mode]
            new_preferences.font_size = int(preferences.font_size * multiplier)
        
        # 色調整
        if mode in self.optimization_rules['color_adjustments']:
            if mode == AccessibilityMode.HIGH_CONTRAST:
                new_preferences.high_contrast = True
                new_preferences.color_scheme = 'high_contrast'
        
        # アニメーション調整
        if mode == AccessibilityMode.REDUCED_MOTION:
            new_preferences.reduced_motion = True
            new_preferences.animation_speed = 0.1
        
        # 音声優先設定
        if mode == AccessibilityMode.VOICE_FOCUS:
            new_preferences.voice_priority = True
        
        return new_preferences

class ThemeManager:
    """テーマ管理システム"""
    
    def __init__(self):
        self.themes = self._load_themes()
        self.current_theme = "default"
        self.dynamic_theming = True
        
    def _load_themes(self) -> Dict[str, Dict]:
        """テーマ定義読み込み"""
        return {
            'default': {
                'colors': {
                    'primary': '#0078D4',
                    'secondary': '#107C10',
                    'background': '#FFFFFF',
                    'surface': '#F3F2F1',
                    'text': '#323130',
                    'accent': '#8764B8'
                },
                'fonts': {
                    'primary': 'Segoe UI',
                    'monospace': 'Consolas',
                    'size_base': 11
                }
            },
            'dark': {
                'colors': {
                    'primary': '#0078D4',
                    'secondary': '#00BCF2',
                    'background': '#1E1E1E',
                    'surface': '#2D2D30',
                    'text': '#FFFFFF',
                    'accent': '#BB86FC'
                },
                'fonts': {
                    'primary': 'Segoe UI',
                    'monospace': 'Consolas',
                    'size_base': 11
                }
            },
            'high_contrast': {
                'colors': {
                    'primary': '#FFFF00',
                    'secondary': '#00FF00',
                    'background': '#000000',
                    'surface': '#000000',
                    'text': '#FFFFFF',
                    'accent': '#FF0000'
                },
                'fonts': {
                    'primary': 'Segoe UI',
                    'monospace': 'Consolas',
                    'size_base': 13
                }
            }
        }
    
    def auto_select_theme(self, time_of_day: int = None, 
                         accessibility_mode: AccessibilityMode = AccessibilityMode.NORMAL) -> str:
        """自動テーマ選択"""
        if accessibility_mode == AccessibilityMode.HIGH_CONTRAST:
            return 'high_contrast'
        
        if time_of_day is None:
            time_of_day = datetime.now().hour
        
        # 時刻ベースの選択
        if 6 <= time_of_day <= 18:
            return 'default'  # 昼間は明るいテーマ
        else:
            return 'dark'     # 夜間は暗いテーマ
    
    def generate_adaptive_colors(self, usage_patterns: Dict) -> Dict[str, str]:
        """使用パターンに基づく色生成"""
        base_theme = self.themes[self.current_theme]
        adaptive_colors = base_theme['colors'].copy()
        
        # よく使用される要素の色を調整
        most_used = usage_patterns.get('most_used_elements', [])
        if most_used:
            # 最も使用される要素は目立つ色に
            primary_hue = 0.6  # 青系
            adaptive_colors['primary'] = self._hsl_to_hex(primary_hue, 0.8, 0.5)
            
            # 二番目に使用される要素は補完色に
            if len(most_used) > 1:
                secondary_hue = (primary_hue + 0.3) % 1.0
                adaptive_colors['secondary'] = self._hsl_to_hex(secondary_hue, 0.7, 0.5)
        
        return adaptive_colors
    
    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """HSLからHEXへの変換"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

class LayoutOptimizer:
    """レイアウト最適化エンジン"""
    
    def __init__(self):
        self.layout_templates = self._load_layout_templates()
        
    def _load_layout_templates(self) -> Dict[str, Dict]:
        """レイアウトテンプレート読み込み"""
        return {
            'compact': {
                'padding': 5,
                'spacing': 3,
                'element_size_multiplier': 0.8,
                'priority_boost': 1.2
            },
            'standard': {
                'padding': 10,
                'spacing': 5,
                'element_size_multiplier': 1.0,
                'priority_boost': 1.0
            },
            'spacious': {
                'padding': 20,
                'spacing': 10,
                'element_size_multiplier': 1.2,
                'priority_boost': 0.8
            }
        }
    
    def optimize_layout(self, elements: List[UIElement], 
                       usage_patterns: Dict, 
                       screen_size: Tuple[int, int],
                       layout_type: LayoutType = LayoutType.STANDARD) -> List[UIElement]:
        """レイアウト最適化"""
        optimized_elements = []
        template = self.layout_templates[layout_type.value]
        
        # 使用頻度でソート
        most_used = {item[0]: item[1] for item in usage_patterns.get('most_used_elements', [])}
        
        sorted_elements = sorted(
            elements,
            key=lambda e: most_used.get(e.element_id, 0),
            reverse=True
        )
        
        # レイアウト調整
        screen_width, screen_height = screen_size
        current_y = template['padding']
        
        for element in sorted_elements:
            # 使用頻度に基づく位置調整
            usage_count = most_used.get(element.element_id, 0)
            
            if usage_count > 10:  # 高頻度使用要素
                # 上部に配置
                new_element = UIElement(
                    element_id=element.element_id,
                    element_type=element.element_type,
                    position=(template['padding'], current_y),
                    size=(
                        int(element.size[0] * template['element_size_multiplier'] * 1.1),
                        int(element.size[1] * template['element_size_multiplier'] * 1.1)
                    ),
                    visible=True,
                    priority=element.priority + 1,
                    accessibility_role=element.accessibility_role,
                    tooltip=element.tooltip,
                    voice_command=element.voice_command
                )
                current_y += new_element.size[1] + template['spacing']
            else:
                # 標準配置
                new_element = UIElement(
                    element_id=element.element_id,
                    element_type=element.element_type,
                    position=(template['padding'], current_y),
                    size=(
                        int(element.size[0] * template['element_size_multiplier']),
                        int(element.size[1] * template['element_size_multiplier'])
                    ),
                    visible=element.visible,
                    priority=element.priority,
                    accessibility_role=element.accessibility_role,
                    tooltip=element.tooltip,
                    voice_command=element.voice_command
                )
                current_y += new_element.size[1] + template['spacing']
            
            optimized_elements.append(new_element)
        
        return optimized_elements

class AdaptiveUISystem:
    """アダプティブUIシステム メインクラス"""
    
    def __init__(self, root: tk.Tk = None):
        self.root = root
        self.adaptation_level = UIAdaptationLevel.MODERATE
        
        # コンポーネント初期化
        self.usage_analyzer = UsageAnalyzer()
        self.accessibility_optimizer = AccessibilityOptimizer()
        self.theme_manager = ThemeManager()
        self.layout_optimizer = LayoutOptimizer()
        
        # 設定・状態
        self.user_preferences = UserPreferences()
        self.ui_elements: List[UIElement] = []
        self.current_layout = LayoutType.STANDARD
        
        # 適応設定
        self.auto_adaptation = True
        self.adaptation_interval = 300  # 5分
        self.minimum_usage_threshold = 5
        
        # データ永続化
        self.data_file = Path("adaptive_ui_data.json")
        self._load_data()
        
        # 自動適応スレッド
        self.adaptation_active = True
        self.adaptation_thread = threading.Thread(target=self._adaptation_loop)
        self.adaptation_thread.daemon = True
        self.adaptation_thread.start()
        
        # コールバック
        self.ui_update_callback: Optional[Callable] = None
        self.voice_feedback_callback: Optional[Callable] = None
    
    def set_adaptation_level(self, level: UIAdaptationLevel):
        """適応レベル設定"""
        self.adaptation_level = level
        logging.info(f"UI適応レベルを{level.value}に設定")
    
    def set_callbacks(self, ui_update: Callable = None, voice_feedback: Callable = None):
        """コールバック設定"""
        self.ui_update_callback = ui_update
        self.voice_feedback_callback = voice_feedback
    
    def record_user_interaction(self, element_id: str, element_type: str,
                              interaction_type: str, duration: float = 0.0,
                              success: bool = True):
        """ユーザーインタラクション記録"""
        self.usage_analyzer.record_interaction(
            element_id, element_type, interaction_type, duration, success
        )
        
        # 即座に適応（積極的モードの場合）
        if self.adaptation_level == UIAdaptationLevel.AGGRESSIVE:
            self._trigger_adaptation()
    
    def register_ui_element(self, element: UIElement):
        """UI要素登録"""
        # 既存要素の更新または新規追加
        existing_index = next(
            (i for i, e in enumerate(self.ui_elements) if e.element_id == element.element_id),
            None
        )
        
        if existing_index is not None:
            self.ui_elements[existing_index] = element
        else:
            self.ui_elements.append(element)
    
    def get_optimized_layout(self, screen_size: Tuple[int, int] = None) -> List[UIElement]:
        """最適化されたレイアウト取得"""
        if screen_size is None and self.root:
            screen_size = (self.root.winfo_width(), self.root.winfo_height())
        elif screen_size is None:
            screen_size = (1024, 768)  # デフォルトサイズ
        
        usage_patterns = self.usage_analyzer.get_usage_patterns()
        
        return self.layout_optimizer.optimize_layout(
            self.ui_elements,
            usage_patterns,
            screen_size,
            self.current_layout
        )
    
    def get_adaptive_theme(self) -> Dict[str, Any]:
        """適応的テーマ取得"""
        # 時刻とアクセシビリティモードに基づくテーマ選択
        theme_name = self.theme_manager.auto_select_theme(
            accessibility_mode=self.accessibility_optimizer.current_mode
        )
        
        base_theme = self.theme_manager.themes[theme_name]
        
        # 使用パターンに基づく色調整
        if self.theme_manager.dynamic_theming:
            usage_patterns = self.usage_analyzer.get_usage_patterns()
            adaptive_colors = self.theme_manager.generate_adaptive_colors(usage_patterns)
            
            # テーマに色を統合
            adapted_theme = base_theme.copy()
            adapted_theme['colors'].update(adaptive_colors)
            return adapted_theme
        
        return base_theme
    
    def apply_accessibility_optimization(self, user_feedback: List[str] = None):
        """アクセシビリティ最適化適用"""
        usage_patterns = self.usage_analyzer.get_usage_patterns()
        
        # アクセシビリティニーズ分析
        optimal_mode = self.accessibility_optimizer.analyze_accessibility_needs(
            usage_patterns, user_feedback
        )
        
        # 設定適用
        if optimal_mode != self.accessibility_optimizer.current_mode:
            self.user_preferences = self.accessibility_optimizer.apply_accessibility_mode(
                optimal_mode, self.user_preferences
            )
            
            if self.voice_feedback_callback:
                self.voice_feedback_callback(f"アクセシビリティを{optimal_mode.value}モードに最適化しました")
    
    def get_usage_recommendations(self) -> List[Dict[str, Any]]:
        """使用改善推奨取得"""
        return self.usage_analyzer.recommend_optimizations()
    
    def _trigger_adaptation(self):
        """適応トリガー"""
        if not self.auto_adaptation:
            return
        
        try:
            # 使用パターン分析
            usage_patterns = self.usage_analyzer.get_usage_patterns()
            recommendations = self.usage_analyzer.recommend_optimizations()
            
            # 適応レベルに応じた処理
            if self.adaptation_level == UIAdaptationLevel.MINIMAL:
                # 最小限の調整のみ
                self._apply_minimal_adaptations(recommendations)
            elif self.adaptation_level == UIAdaptationLevel.MODERATE:
                # 中程度の調整
                self._apply_moderate_adaptations(recommendations, usage_patterns)
            elif self.adaptation_level == UIAdaptationLevel.AGGRESSIVE:
                # 積極的な調整
                self._apply_aggressive_adaptations(recommendations, usage_patterns)
            
            # UI更新通知
            if self.ui_update_callback:
                self.ui_update_callback({
                    'type': 'adaptation_applied',
                    'level': self.adaptation_level.value,
                    'recommendations_count': len(recommendations)
                })
                
        except Exception as e:
            logging.error(f"UI適応エラー: {e}")
    
    def _apply_minimal_adaptations(self, recommendations: List[Dict]):
        """最小限の適応"""
        # エラーの多い要素のツールチップ追加のみ
        for rec in recommendations:
            if rec['type'] == 'improve_element':
                element = next(
                    (e for e in self.ui_elements if e.element_id == rec['element_id']), 
                    None
                )
                if element and not element.tooltip:
                    element.tooltip = "使用時は注意してください"
    
    def _apply_moderate_adaptations(self, recommendations: List[Dict], patterns: Dict):
        """中程度の適応"""
        # ツールチップ追加 + 位置調整
        self._apply_minimal_adaptations(recommendations)
        
        # よく使われる要素の優先度上昇
        most_used = dict(patterns.get('most_used_elements', [])[:5])
        for element in self.ui_elements:
            if element.element_id in most_used:
                element.priority = min(element.priority + 1, 10)
    
    def _apply_aggressive_adaptations(self, recommendations: List[Dict], patterns: Dict):
        """積極的な適応"""
        # 全ての推奨事項を適用
        for rec in recommendations:
            if rec['type'] == 'hide_element':
                element = next(
                    (e for e in self.ui_elements if e.element_id == rec['element_id']), 
                    None
                )
                if element:
                    element.visible = False
            elif rec['type'] == 'promote_element':
                element = next(
                    (e for e in self.ui_elements if e.element_id == rec['element_id']), 
                    None
                )
                if element:
                    element.priority = min(element.priority + 2, 10)
                    # サイズ拡大
                    element.size = (
                        int(element.size[0] * 1.1),
                        int(element.size[1] * 1.1)
                    )
        
        # レイアウト自動調整
        if patterns.get('most_used_elements'):
            # 最適なレイアウトタイプを選択
            usage_count = len(patterns['most_used_elements'])
            if usage_count > 15:
                self.current_layout = LayoutType.COMPACT
            elif usage_count < 5:
                self.current_layout = LayoutType.SPACIOUS
    
    def _adaptation_loop(self):
        """適応ループ"""
        while self.adaptation_active:
            try:
                # 定期的な適応チェック
                if self.auto_adaptation:
                    self._trigger_adaptation()
                
                time.sleep(self.adaptation_interval)
                
            except Exception as e:
                logging.error(f"適応ループエラー: {e}")
                time.sleep(30)
    
    def _load_data(self):
        """データ読み込み"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 設定復元
                if 'preferences' in data:
                    pref_data = data['preferences']
                    self.user_preferences = UserPreferences(**pref_data)
                
                # メトリクス復元
                if 'metrics' in data:
                    for element_id, metric_data in data['metrics'].items():
                        metric_data['last_used'] = datetime.fromisoformat(metric_data['last_used'])
                        self.usage_analyzer.metrics[element_id] = UIMetrics(**metric_data)
                        
        except Exception as e:
            logging.error(f"UI適応データ読み込みエラー: {e}")
    
    def save_data(self):
        """データ保存"""
        try:
            data = {
                'preferences': asdict(self.user_preferences),
                'metrics': {},
                'adaptation_level': self.adaptation_level.value,
                'timestamp': datetime.now().isoformat()
            }
            
            # メトリクスデータ変換
            for element_id, metric in self.usage_analyzer.metrics.items():
                metric_dict = asdict(metric)
                metric_dict['last_used'] = metric.last_used.isoformat()
                data['metrics'][element_id] = metric_dict
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"UI適応データ保存エラー: {e}")
    
    def get_adaptation_status(self) -> Dict[str, Any]:
        """適応ステータス取得"""
        usage_patterns = self.usage_analyzer.get_usage_patterns()
        recommendations = self.usage_analyzer.recommend_optimizations()
        
        return {
            'adaptation_level': self.adaptation_level.value,
            'accessibility_mode': self.accessibility_optimizer.current_mode.value,
            'current_theme': self.theme_manager.current_theme,
            'layout_type': self.current_layout.value,
            'elements_count': len(self.ui_elements),
            'tracked_elements': len(self.usage_analyzer.metrics),
            'recommendations_count': len(recommendations),
            'auto_adaptation': self.auto_adaptation,
            'most_used_elements': usage_patterns.get('most_used_elements', [])[:5]
        }
    
    def shutdown(self):
        """シャットダウン"""
        self.adaptation_active = False
        self.save_data()
        logging.info("アダプティブUIシステムをシャットダウンしました")

# テスト・デモ用関数
def demo_adaptive_ui():
    """アダプティブUIデモ"""
    print("=== アダプティブUI システム デモ ===")
    
    # システム初期化
    ui_system = AdaptiveUISystem()
    
    # サンプル要素登録
    elements = [
        UIElement("btn_file_open", "button", (10, 10), (100, 30), True, 1, "button", "ファイルを開く", "ファイルを開いて"),
        UIElement("btn_file_save", "button", (120, 10), (100, 30), True, 1, "button", "ファイルを保存", "ファイルを保存して"),
        UIElement("menu_edit", "menu", (10, 50), (200, 25), True, 2, "menu", "編集メニュー", "編集メニューを開いて"),
        UIElement("text_area", "text", (10, 80), (400, 300), True, 3, "textbox", "メインテキストエリア", "テキストを入力して")
    ]
    
    for element in elements:
        ui_system.register_ui_element(element)
    
    # 使用パターンシミュレーション
    print("📊 使用パターンをシミュレーション中...")
    
    # ファイルを開くボタンを頻繁に使用
    for i in range(20):
        ui_system.record_user_interaction("btn_file_open", "button", "click", 1.0, True)
    
    # 保存ボタンも使用（エラーあり）
    for i in range(10):
        success = i < 8  # 8/10で成功
        ui_system.record_user_interaction("btn_file_save", "button", "click", 1.5, success)
    
    # メニューはあまり使用しない
    for i in range(3):
        ui_system.record_user_interaction("menu_edit", "menu", "hover", 0.5, True)
    
    # テキストエリアは長時間使用
    ui_system.record_user_interaction("text_area", "text", "focus", 120.0, True)
    
    # 適応結果表示
    print("\n💡 使用改善推奨:")
    recommendations = ui_system.get_usage_recommendations()
    for rec in recommendations:
        print(f"  - {rec['element_id']}: {rec['suggestion']} ({rec['reason']})")
    
    # 最適化されたレイアウト取得
    print("\n🎨 最適化されたレイアウト:")
    optimized_elements = ui_system.get_optimized_layout((800, 600))
    for element in optimized_elements:
        print(f"  - {element.element_id}: 位置{element.position}, サイズ{element.size}, 優先度{element.priority}")
    
    # アダプティブテーマ取得
    print("\n🎭 アダプティブテーマ:")
    theme = ui_system.get_adaptive_theme()
    print(f"  - 主要色: {theme['colors']['primary']}")
    print(f"  - 背景色: {theme['colors']['background']}")
    print(f"  - テキスト色: {theme['colors']['text']}")
    
    # ステータス表示
    print("\n📈 適応ステータス:")
    status = ui_system.get_adaptation_status()
    for key, value in status.items():
        print(f"  - {key}: {value}")
    
    ui_system.shutdown()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # デモ実行
    demo_adaptive_ui()
