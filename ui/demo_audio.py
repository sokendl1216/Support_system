"""
音声入出力システムデモアプリケーション
Vosk/Espeak音声機能の包括的テスト・デモンストレーション

機能:
- 音声認識テスト
- 音声合成テスト
- 音声品質検証
- パフォーマンステスト
- 統合動作確認
"""

import streamlit as st
import asyncio
import time
import logging
from pathlib import Path
import sys
from typing import Dict, List, Any

# パス設定
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent))

# コンポーネントインポート
from components.audio_handler import (
    AudioInterfaceManager,
    VoskSpeechRecognizer,
    EspeakTextToSpeech,
    AudioConfiguration,
    initialize_audio,
    speak_text,
    listen_for_speech,
    voice_interaction,
    cleanup_audio,
    AUDIO_AVAILABLE
)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioSystemDemo:
    """音声システムデモアプリケーション"""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
        self.audio_manager = AudioInterfaceManager()
    
    def setup_page_config(self):
        """ページ設定"""
        st.set_page_config(
            page_title="音声システムデモ",
            page_icon="🎵",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """セッション状態初期化"""
        if 'demo_results' not in st.session_state:
            st.session_state.demo_results = {
                'recognition_tests': [],
                'synthesis_tests': [],
                'integration_tests': [],
                'performance_metrics': {}
            }
        
        if 'test_running' not in st.session_state:
            st.session_state.test_running = False
    
    def render_header(self):
        """ヘッダー描画"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #1f77b4; margin-bottom: 0.5rem;'>
                🎵 音声入出力システムデモ
            </h1>
            <p style='color: #666; font-size: 1.2rem; margin: 0;'>
                Vosk音声認識 & Espeak音声合成 - 包括的機能テスト
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_system_status(self):
        """システム状態表示"""
        st.markdown("## 📊 システム状態")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # 音声ライブラリ状態
        with col1:
            if AUDIO_AVAILABLE:
                st.success("✅ 音声ライブラリ")
                st.caption("vosk, pyaudio, pyttsx3")
            else:
                st.error("❌ 音声ライブラリ")
                st.caption("インストール必要")
          # 音声システム状態
        status = self.audio_manager.get_status()
        
        with col2:
            if status['initialized']:
                st.success("✅ システム初期化")
            else:
                st.warning("⚠️ 未初期化")
            st.caption("音声エンジン状態")
        
        with col3:
            if status['listening']:
                st.info("🎤 音声認識中")
            else:
                st.success("🎤 認識待機")
            st.caption("音声入力状態")
        
        with col4:
            if status['speaking']:
                st.info("🔊 音声出力中")
            else:
                st.success("🔊 出力待機")
            st.caption("音声出力状態")
        
        return status
    
    def render_quick_controls(self):
        """クイック制御"""
        st.markdown("## 🎛️ クイック制御")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔧 システム初期化", use_container_width=True):
                self._initialize_system()
        
        with col2:
            if st.button("🎤 音声認識テスト", use_container_width=True):
                self._quick_recognition_test()
        
        with col3:
            if st.button("🔊 音声合成テスト", use_container_width=True):
                self._quick_synthesis_test()
        
        with col4:
            if st.button("🧹 システムクリーンアップ", use_container_width=True):
                self._cleanup_system()
    
    def _initialize_system(self):
        """システム初期化"""
        with st.spinner("音声システムを初期化中..."):
            try:
                success = asyncio.run(initialize_audio())
                if success:
                    st.success("✅ 音声システム初期化完了")
                    # 初期化完了通知
                    asyncio.run(speak_text("音声システムの初期化が完了しました"))
                else:
                    st.error("❌ 音声システム初期化失敗")
            except Exception as e:
                st.error(f"初期化エラー: {e}")
    
    def _quick_recognition_test(self):
        """クイック音声認識テスト"""
        with st.spinner("音声認識テストを実行中..."):
            try:
                # 事前通知
                asyncio.run(speak_text("音声認識テストを開始します。何か話してください。"))
                
                # 音声認識実行
                result = asyncio.run(listen_for_speech())
                
                if result:
                    st.success(f"✅ 認識成功: {result}")
                    # 確認読み上げ
                    asyncio.run(speak_text(f"認識結果は、{result}、です。"))
                else:
                    st.warning("⚠️ 音声が認識できませんでした")
                    
            except Exception as e:
                st.error(f"認識テストエラー: {e}")
    
    def _quick_synthesis_test(self):
        """クイック音声合成テスト"""
        test_text = "こんにちは。これは音声合成のテストです。日本語の読み上げ機能が正常に動作しています。"
        
        with st.spinner("音声合成テストを実行中..."):
            try:
                success = asyncio.run(speak_text(test_text))
                if success:
                    st.success("✅ 音声合成テスト完了")
                else:
                    st.error("❌ 音声合成テスト失敗")
            except Exception as e:
                st.error(f"合成テストエラー: {e}")
    
    def _cleanup_system(self):
        """システムクリーンアップ"""
        try:
            cleanup_audio()
            st.success("✅ システムクリーンアップ完了")
        except Exception as e:
            st.error(f"クリーンアップエラー: {e}")
    
    def render_detailed_tests(self):
        """詳細テストセクション"""
        st.markdown("## 🧪 詳細テスト")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎤 音声認識テスト",
            "🔊 音声合成テスト", 
            "🔄 統合テスト",
            "⚡ パフォーマンステスト"
        ])
        
        with tab1:
            self.render_recognition_tests()
        
        with tab2:
            self.render_synthesis_tests()
        
        with tab3:
            self.render_integration_tests()
        
        with tab4:
            self.render_performance_tests()
    
    def render_recognition_tests(self):
        """音声認識テスト"""
        st.markdown("### 🎤 音声認識機能テスト")
        
        # テスト設定
        with st.expander("🔧 認識テスト設定"):
            test_duration = st.slider("テスト時間（秒）", 5, 30, 10)
            noise_reduction = st.checkbox("ノイズ除去有効", value=True)
            auto_stop = st.checkbox("自動停止", value=True)
        
        # テスト実行
        if st.button("🎤 音声認識テスト開始", use_container_width=True):
            self._run_recognition_test(test_duration, noise_reduction, auto_stop)
        
        # テスト結果表示
        self._display_recognition_results()
    
    def _run_recognition_test(self, duration: int, noise_reduction: bool, auto_stop: bool):
        """音声認識テスト実行"""
        st.session_state.test_running = True
        
        try:
            with st.spinner(f"音声認識テスト実行中... ({duration}秒)"):
                # テスト開始通知
                asyncio.run(speak_text(f"{duration}秒間の音声認識テストを開始します"))
                
                start_time = time.time()
                recognized_texts = []
                
                def on_recognition(text: str):
                    recognized_texts.append({
                        'text': text,
                        'timestamp': time.time() - start_time,
                        'length': len(text)
                    })
                
                # コールバック設定
                self.audio_manager.add_callback('speech_recognized', on_recognition)
                
                # 音声認識開始
                asyncio.run(self.audio_manager.start_listening())
                
                # 指定時間待機
                time.sleep(duration)
                
                # 音声認識停止
                self.audio_manager.stop_listening()
                
                # コールバック削除
                self.audio_manager.remove_callback('speech_recognized', on_recognition)
                
                # 結果保存
                test_result = {
                    'timestamp': time.time(),
                    'duration': duration,
                    'noise_reduction': noise_reduction,
                    'auto_stop': auto_stop,
                    'recognition_count': len(recognized_texts),
                    'recognized_texts': recognized_texts,
                    'success': len(recognized_texts) > 0
                }
                
                st.session_state.demo_results['recognition_tests'].append(test_result)
                
                # 結果通知
                if recognized_texts:
                    st.success(f"✅ 認識成功: {len(recognized_texts)}個のテキストを認識")
                    asyncio.run(speak_text(f"音声認識テストが完了しました。{len(recognized_texts)}個のテキストを認識しました。"))
                else:
                    st.warning("⚠️ 音声が認識されませんでした")
                    asyncio.run(speak_text("音声認識テストが完了しましたが、音声が認識されませんでした。"))
        
        except Exception as e:
            st.error(f"音声認識テストエラー: {e}")
        
        finally:
            st.session_state.test_running = False
    
    def _display_recognition_results(self):
        """音声認識結果表示"""
        results = st.session_state.demo_results['recognition_tests']
        
        if not results:
            st.info("まだテスト結果がありません")
            return
        
        st.markdown("#### 📊 認識テスト結果")
        
        for i, result in enumerate(reversed(results[-5:])):  # 最新5件
            with st.expander(f"テスト {len(results)-i} - {time.ctime(result['timestamp'])}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.metric("認識回数", result['recognition_count'])
                    st.metric("テスト時間", f"{result['duration']}秒")
                
                with col2:
                    st.metric("成功", "✅" if result['success'] else "❌")
                    st.metric("ノイズ除去", "✅" if result['noise_reduction'] else "❌")
                
                # 認識テキスト詳細
                if result['recognized_texts']:
                    st.markdown("**認識されたテキスト:**")
                    for j, text_data in enumerate(result['recognized_texts']):
                        st.write(f"{j+1}. [{text_data['timestamp']:.1f}s] {text_data['text']}")
    
    def render_synthesis_tests(self):
        """音声合成テスト"""
        st.markdown("### 🔊 音声合成機能テスト")
        
        # テストテキスト選択
        test_texts = [
            "こんにちは。これは音声合成のテストです。",
            "日本語の読み上げ機能をテストしています。句読点や文の区切りも確認します。",
            "数字の読み上げテスト：1234567890",
            "英語混じりテスト：Hello World, これはTest用のSentenceです。",
            "長文テスト：システムが正常に動作している場合、この長い文章も適切に読み上げられるはずです。音声合成エンジンの性能と品質を確認するためのテストです。"
        ]
        
        selected_text = st.selectbox("テストテキスト選択", test_texts)
        custom_text = st.text_area("カスタムテキスト", placeholder="独自のテストテキストを入力...")
        
        test_text = custom_text if custom_text.strip() else selected_text
        
        # 合成設定
        with st.expander("🔧 合成テスト設定"):
            priority_mode = st.checkbox("優先モード", value=False)
            repeat_count = st.slider("繰り返し回数", 1, 5, 1)
        
        # テスト実行
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔊 音声合成テスト開始", use_container_width=True):
                self._run_synthesis_test(test_text, priority_mode, repeat_count)
        
        with col2:
            if st.button("⏹️ 音声停止", use_container_width=True):
                self.audio_manager.stop_speaking()
                st.info("音声出力を停止しました")
        
        # テスト結果表示
        self._display_synthesis_results()
    
    def _run_synthesis_test(self, text: str, priority: bool, repeat_count: int):
        """音声合成テスト実行"""
        try:
            start_time = time.time()
            
            with st.spinner(f"音声合成テスト実行中... ({repeat_count}回)"):
                for i in range(repeat_count):
                    success = asyncio.run(speak_text(text, priority=priority))
                    time.sleep(0.5)  # 短い間隔
                
                duration = time.time() - start_time
                
                # 結果保存
                test_result = {
                    'timestamp': time.time(),
                    'text': text,
                    'text_length': len(text),
                    'priority': priority,
                    'repeat_count': repeat_count,
                    'duration': duration,
                    'success': success
                }
                
                st.session_state.demo_results['synthesis_tests'].append(test_result)
                
                if success:
                    st.success(f"✅ 音声合成テスト完了 ({duration:.1f}秒)")
                else:
                    st.error("❌ 音声合成テスト失敗")
        
        except Exception as e:
            st.error(f"音声合成テストエラー: {e}")
    
    def _display_synthesis_results(self):
        """音声合成結果表示"""
        results = st.session_state.demo_results['synthesis_tests']
        
        if not results:
            st.info("まだテスト結果がありません")
            return
        
        st.markdown("#### 📊 合成テスト結果")
        
        for i, result in enumerate(reversed(results[-5:])):  # 最新5件
            with st.expander(f"テスト {len(results)-i} - {time.ctime(result['timestamp'])}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.metric("テキスト長", f"{result['text_length']}文字")
                    st.metric("繰り返し", f"{result['repeat_count']}回")
                
                with col2:
                    st.metric("実行時間", f"{result['duration']:.1f}秒")
                    st.metric("成功", "✅" if result['success'] else "❌")
                
                st.markdown("**テストテキスト:**")
                st.write(result['text'])
    
    def render_integration_tests(self):
        """統合テスト"""
        st.markdown("### 🔄 音声対話統合テスト")
        
        # 対話シナリオ
        scenarios = [
            "簡単な挨拶対話",
            "質問応答対話",
            "長い説明文の対話",
            "多段階対話フロー"
        ]
        
        selected_scenario = st.selectbox("対話シナリオ選択", scenarios)
        
        if st.button("🔄 統合テスト開始", use_container_width=True):
            self._run_integration_test(selected_scenario)
        
        # 統合テスト結果
        self._display_integration_results()
    
    def _run_integration_test(self, scenario: str):
        """統合テスト実行"""
        try:
            start_time = time.time()
            
            with st.spinner(f"統合テスト実行中: {scenario}"):
                # シナリオ別テスト実行
                if scenario == "簡単な挨拶対話":
                    result = asyncio.run(voice_interaction("こんにちは。お名前を教えてください。"))
                elif scenario == "質問応答対話":
                    result = asyncio.run(voice_interaction("今日の予定について教えてください。"))
                elif scenario == "長い説明文の対話":
                    result = asyncio.run(voice_interaction("システムの使い方について詳しく説明してください。"))
                elif scenario == "多段階対話フロー":
                    result = asyncio.run(voice_interaction("まず最初の質問です。"))
                else:
                    result = None
                
                duration = time.time() - start_time
                
                # 結果保存
                test_result = {
                    'timestamp': time.time(),
                    'scenario': scenario,
                    'duration': duration,
                    'user_input': result,
                    'success': result is not None
                }
                
                st.session_state.demo_results['integration_tests'].append(test_result)
                
                if result:
                    st.success(f"✅ 統合テスト完了: {result}")
                    # 確認読み上げ
                    asyncio.run(speak_text(f"統合テストが完了しました。入力内容は{result}でした。"))
                else:
                    st.warning("⚠️ 統合テスト：音声が認識できませんでした")
        
        except Exception as e:
            st.error(f"統合テストエラー: {e}")
    
    def _display_integration_results(self):
        """統合テスト結果表示"""
        results = st.session_state.demo_results['integration_tests']
        
        if not results:
            st.info("まだテスト結果がありません")
            return
        
        st.markdown("#### 📊 統合テスト結果")
        
        for i, result in enumerate(reversed(results[-3:])):  # 最新3件
            with st.expander(f"統合テスト {len(results)-i} - {result['scenario']}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.metric("実行時間", f"{result['duration']:.1f}秒")
                    st.metric("成功", "✅" if result['success'] else "❌")
                
                with col2:
                    st.write("**ユーザー入力:**")
                    st.write(result['user_input'] or "（認識されませんでした）")
    
    def render_performance_tests(self):
        """パフォーマンステスト"""
        st.markdown("### ⚡ パフォーマンステスト")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 初期化時間測定", use_container_width=True):
                self._measure_initialization_time()
        
        with col2:
            if st.button("📊 応答時間測定", use_container_width=True):
                self._measure_response_time()
        
        # パフォーマンス結果表示
        self._display_performance_results()
    
    def _measure_initialization_time(self):
        """初期化時間測定"""
        try:
            # システムクリーンアップ
            cleanup_audio()
            
            # 初期化時間測定
            start_time = time.time()
            success = asyncio.run(initialize_audio())
            init_time = time.time() - start_time
            
            # 結果保存
            perf_result = {
                'test_type': 'initialization',
                'timestamp': time.time(),
                'duration': init_time,
                'success': success
            }
            
            if 'performance_metrics' not in st.session_state.demo_results:
                st.session_state.demo_results['performance_metrics'] = {}
            
            if 'initialization' not in st.session_state.demo_results['performance_metrics']:
                st.session_state.demo_results['performance_metrics']['initialization'] = []
            
            st.session_state.demo_results['performance_metrics']['initialization'].append(perf_result)
            
            st.success(f"✅ 初期化時間: {init_time:.3f}秒")
            
        except Exception as e:
            st.error(f"初期化時間測定エラー: {e}")
    
    def _measure_response_time(self):
        """応答時間測定"""
        try:
            test_text = "応答時間測定テスト"
            
            # 音声合成応答時間測定
            start_time = time.time()
            success = asyncio.run(speak_text(test_text))
            response_time = time.time() - start_time
            
            # 結果保存
            perf_result = {
                'test_type': 'response',
                'timestamp': time.time(),
                'duration': response_time,
                'success': success,
                'text_length': len(test_text)
            }
            
            if 'response' not in st.session_state.demo_results['performance_metrics']:
                st.session_state.demo_results['performance_metrics']['response'] = []
            
            st.session_state.demo_results['performance_metrics']['response'].append(perf_result)
            
            st.success(f"✅ 応答時間: {response_time:.3f}秒")
            
        except Exception as e:
            st.error(f"応答時間測定エラー: {e}")
    
    def _display_performance_results(self):
        """パフォーマンス結果表示"""
        metrics = st.session_state.demo_results.get('performance_metrics', {})
        
        if not metrics:
            st.info("まだパフォーマンスデータがありません")
            return
        
        st.markdown("#### 📈 パフォーマンス統計")
        
        col1, col2 = st.columns(2)
        
        # 初期化時間統計
        with col1:
            if 'initialization' in metrics:
                init_times = [m['duration'] for m in metrics['initialization'] if m['success']]
                if init_times:
                    st.metric(
                        "平均初期化時間",
                        f"{sum(init_times)/len(init_times):.3f}秒",
                        f"最新: {init_times[-1]:.3f}秒"
                    )
        
        # 応答時間統計
        with col2:
            if 'response' in metrics:
                response_times = [m['duration'] for m in metrics['response'] if m['success']]
                if response_times:
                    st.metric(
                        "平均応答時間",
                        f"{sum(response_times)/len(response_times):.3f}秒",
                        f"最新: {response_times[-1]:.3f}秒"
                    )
    
    def render_test_summary(self):
        """テスト結果サマリー"""
        st.markdown("## 📋 テスト結果サマリー")
        
        results = st.session_state.demo_results
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            recognition_count = len(results['recognition_tests'])
            recognition_success = sum(1 for r in results['recognition_tests'] if r['success'])
            st.metric(
                "音声認識テスト",
                f"{recognition_success}/{recognition_count}",
                f"成功率: {recognition_success/recognition_count*100:.1f}%" if recognition_count else "0%"
            )
        
        with col2:
            synthesis_count = len(results['synthesis_tests'])
            synthesis_success = sum(1 for r in results['synthesis_tests'] if r['success'])
            st.metric(
                "音声合成テスト",
                f"{synthesis_success}/{synthesis_count}",
                f"成功率: {synthesis_success/synthesis_count*100:.1f}%" if synthesis_count else "0%"
            )
        
        with col3:
            integration_count = len(results['integration_tests'])
            integration_success = sum(1 for r in results['integration_tests'] if r['success'])
            st.metric(
                "統合テスト",
                f"{integration_success}/{integration_count}",
                f"成功率: {integration_success/integration_count*100:.1f}%" if integration_count else "0%"
            )
        
        with col4:
            total_tests = recognition_count + synthesis_count + integration_count
            total_success = recognition_success + synthesis_success + integration_success
            st.metric(
                "総合結果",
                f"{total_success}/{total_tests}",
                f"総合成功率: {total_success/total_tests*100:.1f}%" if total_tests else "0%"
            )
        
        # データエクスポート
        if st.button("📊 テスト結果エクスポート", use_container_width=True):
            self._export_test_results()
    
    def _export_test_results(self):
        """テスト結果エクスポート"""
        try:
            import json
            
            export_data = {
                'export_timestamp': time.time(),
                'system_info': {
                    'audio_available': AUDIO_AVAILABLE,
                    'system_status': self.audio_manager.get_status()
                },
                'test_results': st.session_state.demo_results
            }
            
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📥 JSON形式でダウンロード",
                data=json_data,
                file_name=f"audio_test_results_{int(time.time())}.json",
                mime="application/json"
            )
            
            st.success("✅ テスト結果エクスポート準備完了")
            
        except Exception as e:
            st.error(f"エクスポートエラー: {e}")
    
    def run(self):
        """デモアプリケーション実行"""
        try:
            # ヘッダー
            self.render_header()
            
            # システム状態
            self.render_system_status()
            
            st.divider()
            
            # クイック制御
            self.render_quick_controls()
            
            st.divider()
            
            # 詳細テスト
            self.render_detailed_tests()
            
            st.divider()
            
            # テスト結果サマリー
            self.render_test_summary()
            
        except Exception as e:
            st.error(f"デモアプリケーションエラー: {e}")
            logger.error(f"Demo application error: {e}", exc_info=True)


def main():
    """メイン関数"""
    try:
        demo = AudioSystemDemo()
        demo.run()
    except Exception as e:
        st.error(f"起動エラー: {e}")
        logger.error(f"Startup error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
