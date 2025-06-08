"""
Task 4-7: 高度な統合機能 - Smart Assistant System
スマートアシスタント機能の実装

機能:
- 状況認識アシスタント
- リアルタイム操作支援
- 学習型支援システム
- エラー予防・回復機能
"""

import asyncio
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

class AssistantMode(Enum):
    """アシスタントモード"""
    PASSIVE = "passive"      # 受動的支援
    ACTIVE = "active"        # 能動的支援
    LEARNING = "learning"    # 学習モード
    EXPERT = "expert"        # エキスパートモード

class ContextType(Enum):
    """コンテキストタイプ"""
    SCREEN = "screen"        # 画面状況
    TASK = "task"           # タスク状況
    USER = "user"           # ユーザー状況
    SYSTEM = "system"       # システム状況

@dataclass
class AssistantContext:
    """アシスタントコンテキスト"""
    context_type: ContextType
    current_screen: str
    current_task: str
    user_action: str
    system_state: Dict[str, Any]
    timestamp: datetime
    confidence: float = 1.0

@dataclass
class UserPattern:
    """ユーザーパターン"""
    action_sequence: List[str]
    frequency: int
    success_rate: float
    last_used: datetime
    context: str
    shortcuts: List[str] = None

@dataclass
class AssistantSuggestion:
    """アシスタント提案"""
    suggestion_id: str
    title: str
    description: str
    action_type: str
    confidence: float
    voice_command: str
    estimated_time: int
    benefits: List[str]

class PatternAnalyzer:
    """パターン分析エンジン"""
    
    def __init__(self):
        self.patterns: Dict[str, UserPattern] = {}
        self.action_history: List[Dict] = []
        self.learning_threshold = 3
        
    def record_action(self, action: str, context: str, success: bool = True):
        """アクション記録"""
        action_record = {
            'action': action,
            'context': context,
            'success': success,
            'timestamp': datetime.now()
        }
        self.action_history.append(action_record)
        
        # パターン更新
        self._update_patterns(action, context, success)
        
    def _update_patterns(self, action: str, context: str, success: bool):
        """パターン更新"""
        pattern_key = f"{context}:{action}"
        
        if pattern_key in self.patterns:
            pattern = self.patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_used = datetime.now()
            
            # 成功率更新
            total_attempts = pattern.frequency
            current_success = pattern.success_rate * (total_attempts - 1)
            new_success = current_success + (1 if success else 0)
            pattern.success_rate = new_success / total_attempts
        else:
            # 新パターン作成
            self.patterns[pattern_key] = UserPattern(
                action_sequence=[action],
                frequency=1,
                success_rate=1.0 if success else 0.0,
                last_used=datetime.now(),
                context=context
            )
    
    def get_frequent_patterns(self, context: str = None, min_frequency: int = 3) -> List[UserPattern]:
        """頻繁なパターン取得"""
        patterns = []
        for pattern_key, pattern in self.patterns.items():
            if pattern.frequency >= min_frequency:
                if context is None or pattern.context == context:
                    patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.frequency, reverse=True)
    
    def predict_next_action(self, current_context: str, current_action: str) -> List[str]:
        """次のアクション予測"""
        predictions = []
        
        # 履歴から類似パターン検索
        recent_history = self.action_history[-10:]  # 直近10アクション
        
        for i, record in enumerate(recent_history):
            if (record['context'] == current_context and 
                record['action'] == current_action and 
                i < len(recent_history) - 1):
                
                next_record = recent_history[i + 1]
                if next_record['action'] not in predictions:
                    predictions.append(next_record['action'])
        
        return predictions[:3]  # 上位3つ

class ContextAnalyzer:
    """コンテキスト分析エンジン"""
    
    def __init__(self):
        self.current_context: Optional[AssistantContext] = None
        self.context_history: List[AssistantContext] = []
        self.screen_analyzers = {
            'file_manager': self._analyze_file_manager,
            'text_editor': self._analyze_text_editor,
            'terminal': self._analyze_terminal,
            'browser': self._analyze_browser
        }
    
    def analyze_current_context(self, screen_info: Dict) -> AssistantContext:
        """現在のコンテキスト分析"""
        context = AssistantContext(
            context_type=ContextType.SCREEN,
            current_screen=screen_info.get('type', 'unknown'),
            current_task=screen_info.get('task', 'general'),
            user_action=screen_info.get('last_action', 'idle'),
            system_state=screen_info.get('system', {}),
            timestamp=datetime.now()
        )
        
        # 詳細分析
        if context.current_screen in self.screen_analyzers:
            analyzer = self.screen_analyzers[context.current_screen]
            context = analyzer(context, screen_info)
        
        self.current_context = context
        self.context_history.append(context)
        
        return context
    
    def _analyze_file_manager(self, context: AssistantContext, info: Dict) -> AssistantContext:
        """ファイルマネージャー分析"""
        files = info.get('files', [])
        selected = info.get('selected', [])
        
        if len(selected) > 1:
            context.current_task = 'batch_operation'
        elif any(f.endswith('.py') for f in files):
            context.current_task = 'python_development'
        elif any(f.endswith(('.txt', '.md', '.doc')) for f in files):
            context.current_task = 'document_editing'
        
        return context
    
    def _analyze_text_editor(self, context: AssistantContext, info: Dict) -> AssistantContext:
        """テキストエディター分析"""
        file_type = info.get('file_type', '')
        content_length = info.get('content_length', 0)
        
        if file_type == '.py':
            context.current_task = 'python_coding'
        elif file_type in ['.md', '.txt']:
            context.current_task = 'documentation'
        elif content_length > 10000:
            context.current_task = 'large_file_editing'
        
        return context
    
    def _analyze_terminal(self, context: AssistantContext, info: Dict) -> AssistantContext:
        """ターミナル分析"""
        last_command = info.get('last_command', '')
        
        if 'git' in last_command:
            context.current_task = 'version_control'
        elif 'python' in last_command:
            context.current_task = 'python_execution'
        elif 'npm' in last_command or 'node' in last_command:
            context.current_task = 'nodejs_development'
        
        return context
    
    def _analyze_browser(self, context: AssistantContext, info: Dict) -> AssistantContext:
        """ブラウザ分析"""
        url = info.get('url', '')
        
        if 'github.com' in url:
            context.current_task = 'code_repository'
        elif 'stackoverflow.com' in url:
            context.current_task = 'problem_solving'
        elif 'docs.' in url:
            context.current_task = 'documentation_reading'
        
        return context
    
    def get_context_suggestions(self, context: AssistantContext) -> List[str]:
        """コンテキスト固有の提案"""
        suggestions = []
        
        if context.current_task == 'python_development':
            suggestions.extend([
                "Pythonファイルの実行",
                "構文チェック",
                "コードフォーマット",
                "依存関係の確認"
            ])
        elif context.current_task == 'document_editing':
            suggestions.extend([
                "文章校正",
                "形式変換",
                "バックアップ作成",
                "版管理"
            ])
        elif context.current_task == 'batch_operation':
            suggestions.extend([
                "一括リネーム",
                "一括コピー",
                "一括削除（確認付き）",
                "アーカイブ作成"
            ])
        
        return suggestions

class ErrorPreventionSystem:
    """エラー予防システム"""
    
    def __init__(self):
        self.risk_patterns = self._load_risk_patterns()
        self.warning_threshold = 0.7
        
    def _load_risk_patterns(self) -> Dict[str, float]:
        """リスクパターン読み込み"""
        return {
            'delete_without_backup': 0.9,
            'overwrite_important_file': 0.8,
            'run_unknown_script': 0.7,
            'modify_system_file': 0.95,
            'batch_delete_large': 0.85,
            'network_operation_offline': 0.6
        }
    
    def analyze_risk(self, action: str, context: AssistantContext) -> float:
        """リスク分析"""
        risk_score = 0.0
        
        # アクション固有のリスク
        if 'delete' in action.lower():
            risk_score += 0.5
            if context.current_task == 'batch_operation':
                risk_score += 0.3
        
        if 'modify' in action.lower() or 'edit' in action.lower():
            if 'system' in context.current_screen:
                risk_score += 0.4
        
        if 'run' in action.lower() or 'execute' in action.lower():
            risk_score += 0.3
        
        # コンテキスト固有のリスク
        if context.system_state.get('backup_available', False) == False:
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def generate_warning(self, action: str, risk_score: float) -> Optional[str]:
        """警告生成"""
        if risk_score < self.warning_threshold:
            return None
        
        warnings = []
        
        if risk_score > 0.9:
            warnings.append("⚠️ 高リスク操作です")
        elif risk_score > 0.7:
            warnings.append("⚠️ 注意が必要な操作です")
        
        if 'delete' in action.lower():
            warnings.append("削除操作は元に戻せません")
        
        if 'modify' in action.lower():
            warnings.append("変更前にバックアップの作成をお勧めします")
        
        return ' - '.join(warnings) if warnings else None

class SmartAssistant:
    """スマートアシスタント メインクラス"""
    
    def __init__(self):
        self.mode = AssistantMode.ACTIVE
        self.context_analyzer = ContextAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.error_prevention = ErrorPreventionSystem()
        
        self.suggestions: List[AssistantSuggestion] = []
        self.active_warnings: List[str] = []
        
        # 設定
        self.suggestion_limit = 5
        self.learning_enabled = True
        self.proactive_suggestions = True
        
        # コールバック
        self.voice_callback: Optional[Callable] = None
        self.ui_callback: Optional[Callable] = None
        
        # データ永続化
        self.data_file = Path("assistant_data.json")
        self._load_data()
        
        # 監視スレッド
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def set_mode(self, mode: AssistantMode):
        """モード設定"""
        self.mode = mode
        logging.info(f"アシスタントモードを{mode.value}に設定")
    
    def set_callbacks(self, voice_callback: Callable = None, ui_callback: Callable = None):
        """コールバック設定"""
        self.voice_callback = voice_callback
        self.ui_callback = ui_callback
    
    def analyze_situation(self, screen_info: Dict) -> AssistantContext:
        """状況分析"""
        context = self.context_analyzer.analyze_current_context(screen_info)
        
        if self.mode in [AssistantMode.ACTIVE, AssistantMode.EXPERT]:
            self._generate_proactive_suggestions(context)
        
        return context
    
    def process_user_action(self, action: str, context: str = None, success: bool = True):
        """ユーザーアクション処理"""
        if context is None and self.context_analyzer.current_context:
            context = self.context_analyzer.current_context.current_task
        
        # パターン学習
        if self.learning_enabled:
            self.pattern_analyzer.record_action(action, context or 'general', success)
        
        # リスク分析
        current_context = self.context_analyzer.current_context
        if current_context:
            risk = self.error_prevention.analyze_risk(action, current_context)
            warning = self.error_prevention.generate_warning(action, risk)
            
            if warning:
                self._send_warning(warning)
    
    def get_suggestions(self, max_suggestions: int = None) -> List[AssistantSuggestion]:
        """提案取得"""
        limit = max_suggestions or self.suggestion_limit
        return self.suggestions[:limit]
    
    def execute_suggestion(self, suggestion_id: str) -> bool:
        """提案実行"""
        suggestion = next((s for s in self.suggestions if s.suggestion_id == suggestion_id), None)
        if not suggestion:
            return False
        
        try:
            # 提案実行ロジック（実装は使用ケースに依存）
            success = self._execute_action(suggestion.action_type, suggestion.voice_command)
            
            # 学習データ更新
            context = self.context_analyzer.current_context
            if context:
                self.process_user_action(suggestion.action_type, context.current_task, success)
            
            return success
        except Exception as e:
            logging.error(f"提案実行エラー: {e}")
            return False
    
    def _generate_proactive_suggestions(self, context: AssistantContext):
        """プロアクティブ提案生成"""
        self.suggestions.clear()
        
        # コンテキスト固有の提案
        context_suggestions = self.context_analyzer.get_context_suggestions(context)
        
        for i, suggestion_text in enumerate(context_suggestions):
            suggestion = AssistantSuggestion(
                suggestion_id=f"ctx_{i}",
                title=suggestion_text,
                description=f"{context.current_task}での推奨アクション",
                action_type="context_action",
                confidence=0.8,
                voice_command=f"{suggestion_text}を実行",
                estimated_time=30,
                benefits=["効率向上", "エラー減少"]
            )
            self.suggestions.append(suggestion)
        
        # パターンベースの提案
        patterns = self.pattern_analyzer.get_frequent_patterns(context.current_task)
        for i, pattern in enumerate(patterns[:3]):
            if pattern.success_rate > 0.7:
                suggestion = AssistantSuggestion(
                    suggestion_id=f"pattern_{i}",
                    title=f"よく使う操作: {pattern.action_sequence[0]}",
                    description=f"成功率{pattern.success_rate:.1%}の操作パターン",
                    action_type="pattern_action",
                    confidence=pattern.success_rate,
                    voice_command=f"{pattern.action_sequence[0]}を実行",
                    estimated_time=15,
                    benefits=["時間短縮", "操作簡単化"]
                )
                self.suggestions.append(suggestion)
    
    def _execute_action(self, action_type: str, command: str) -> bool:
        """アクション実行"""
        # 実際の実行ロジックは統合システムに委譲
        logging.info(f"アクション実行: {action_type} - {command}")
        
        # 音声フィードバック
        if self.voice_callback:
            self.voice_callback(f"{command}を実行します")
        
        return True
    
    def _send_warning(self, warning: str):
        """警告送信"""
        self.active_warnings.append(warning)
        
        # 音声警告
        if self.voice_callback:
            self.voice_callback(warning)
        
        # UI警告
        if self.ui_callback:
            self.ui_callback({'type': 'warning', 'message': warning})
        
        logging.warning(f"アシスタント警告: {warning}")
    
    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                # 定期的な分析・最適化
                if self.mode == AssistantMode.LEARNING:
                    self._optimize_patterns()
                
                # 古い警告のクリア
                self._cleanup_warnings()
                
                time.sleep(30)  # 30秒間隔
                
            except Exception as e:
                logging.error(f"監視ループエラー: {e}")
                time.sleep(5)
    
    def _optimize_patterns(self):
        """パターン最適化"""
        # 古いパターンの削除
        cutoff_date = datetime.now() - timedelta(days=30)
        patterns_to_remove = []
        
        for key, pattern in self.pattern_analyzer.patterns.items():
            if pattern.last_used < cutoff_date and pattern.frequency < 5:
                patterns_to_remove.append(key)
        
        for key in patterns_to_remove:
            del self.pattern_analyzer.patterns[key]
    
    def _cleanup_warnings(self):
        """警告クリーンアップ"""
        # 5分以上古い警告を削除
        self.active_warnings = self.active_warnings[-10:]  # 最新10件まで
    
    def _load_data(self):
        """データ読み込み"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # パターンデータ復元
                if 'patterns' in data:
                    for key, pattern_data in data['patterns'].items():
                        pattern_data['last_used'] = datetime.fromisoformat(pattern_data['last_used'])
                        self.pattern_analyzer.patterns[key] = UserPattern(**pattern_data)
                        
        except Exception as e:
            logging.error(f"データ読み込みエラー: {e}")
    
    def save_data(self):
        """データ保存"""
        try:
            data = {
                'patterns': {},
                'settings': {
                    'mode': self.mode.value,
                    'learning_enabled': self.learning_enabled,
                    'proactive_suggestions': self.proactive_suggestions
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # パターンデータ変換
            for key, pattern in self.pattern_analyzer.patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['last_used'] = pattern.last_used.isoformat()
                data['patterns'][key] = pattern_dict
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"データ保存エラー: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """ステータス取得"""
        context = self.context_analyzer.current_context
        return {
            'mode': self.mode.value,
            'current_context': asdict(context) if context else None,
            'suggestions_count': len(self.suggestions),
            'warnings_count': len(self.active_warnings),
            'patterns_learned': len(self.pattern_analyzer.patterns),
            'learning_enabled': self.learning_enabled
        }
    
    def shutdown(self):
        """シャットダウン"""
        self.monitoring = False
        self.save_data()
        logging.info("スマートアシスタントをシャットダウンしました")

# テスト・デモ用関数
def demo_smart_assistant():
    """スマートアシスタントデモ"""
    assistant = SmartAssistant()
    
    # コールバック設定
    def voice_feedback(message):
        print(f"🔊 音声: {message}")
    
    def ui_feedback(data):
        print(f"💻 UI: {data}")
    
    assistant.set_callbacks(voice_feedback, ui_feedback)
    
    # シミュレーション
    print("=== スマートアシスタント デモ ===")
    
    # 状況分析
    screen_info = {
        'type': 'file_manager',
        'task': 'python_development',
        'last_action': 'select_file',
        'files': ['main.py', 'test.py', 'README.md'],
        'selected': ['main.py'],
        'system': {'backup_available': False}
    }
    
    context = assistant.analyze_situation(screen_info)
    print(f"📊 コンテキスト: {context.current_task}")
    
    # 提案表示
    suggestions = assistant.get_suggestions()
    print(f"\n💡 提案数: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"  - {suggestion.title} (信頼度: {suggestion.confidence:.1%})")
    
    # ユーザーアクション処理
    assistant.process_user_action("run_python_file", context.current_task)
    
    # ステータス表示
    status = assistant.get_status()
    print(f"\n📈 ステータス: {status}")
    
    assistant.shutdown()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # デモ実行
    demo_smart_assistant()
