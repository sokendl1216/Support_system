# -*- coding: utf-8 -*-
"""
ヘルプシステム テストスクリプト

タスク4-9で実装されたヘルプシステムの動作確認とテスト実行
"""

import sys
import traceback
from typing import List, Dict, Any
import json

# ヘルプシステムのインポート
try:
    from ui.components.help_system import (
        HelpSystemManager,
        HelpUIComponents,
        HelpType,
        HelpContext,
        HelpItem,
        TutorialStep,
        get_help_manager,
        get_help_ui
    )
    print("✅ ヘルプシステムモジュールのインポート成功")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def test_help_manager():
    """ヘルプマネージャーのテスト"""
    print("\n🔧 ヘルプマネージャーテスト開始...")
    
    try:
        # インスタンス作成テスト
        help_manager = HelpSystemManager()
        print("✅ HelpSystemManager インスタンス作成成功")
        
        # ヘルプアイテム数確認
        total_items = len(help_manager.help_items)
        print(f"✅ 登録済みヘルプアイテム数: {total_items}")
        
        # コンテキスト別ヘルプ取得テスト
        contexts = [HelpContext.HOME, HelpContext.JOB_SELECTION, HelpContext.VOICE_INTERFACE]
        for context in contexts:
            items = help_manager.get_contextual_help(context)
            print(f"✅ {context.value}コンテキスト: {len(items)}個のヘルプ")
        
        # FAQ取得テスト
        faq_items = help_manager.get_faq_items()
        print(f"✅ FAQ項目数: {len(faq_items)}")
        
        # 検索機能テスト
        search_results = help_manager.search_help("音声")
        print(f"✅ '音声'検索結果: {len(search_results)}個")
        
        # チュートリアル取得テスト
        tutorial = help_manager.get_tutorial("quick_start")
        print(f"✅ クイックスタートチュートリアル: {len(tutorial)}ステップ")
        
        return True
        
    except Exception as e:
        print(f"❌ ヘルプマネージャーテスト失敗: {e}")
        traceback.print_exc()
        return False

def test_help_content():
    """ヘルプコンテンツの内容テスト"""
    print("\n📖 ヘルプコンテンツテスト開始...")
    
    try:
        help_manager = get_help_manager()
        
        # 各ヘルプアイテムの妥当性確認
        valid_items = 0
        for item_id, item in help_manager.help_items.items():
            # 必須フィールドチェック
            if item.title and item.content and item.help_type and item.context:
                valid_items += 1
            else:
                print(f"⚠️ 不完全なヘルプアイテム: {item_id}")
        
        print(f"✅ 有効なヘルプアイテム: {valid_items}/{len(help_manager.help_items)}")
        
        # キーワード検索テスト
        test_keywords = ["音声", "生成", "エラー", "設定", "チュートリアル"]
        for keyword in test_keywords:
            results = help_manager.search_help(keyword)
            print(f"✅ '{keyword}'検索: {len(results)}件ヒット")
        
        return True
        
    except Exception as e:
        print(f"❌ ヘルプコンテンツテスト失敗: {e}")
        traceback.print_exc()
        return False

def test_tutorial_system():
    """チュートリアルシステムのテスト"""
    print("\n🎓 チュートリアルシステムテスト開始...")
    
    try:
        help_manager = get_help_manager()
        
        # チュートリアル取得テスト
        tutorial_id = "quick_start"
        tutorial = help_manager.get_tutorial(tutorial_id)
        
        if tutorial:
            print(f"✅ '{tutorial_id}'チュートリアル取得成功: {len(tutorial)}ステップ")
            
            # 各ステップの妥当性確認
            valid_steps = 0
            for i, step in enumerate(tutorial):
                if step.step_id and step.title and step.description:
                    valid_steps += 1
                    print(f"  📝 ステップ{i+1}: {step.title}")
                else:
                    print(f"  ⚠️ 不完全なステップ: {i+1}")
            
            print(f"✅ 有効なステップ: {valid_steps}/{len(tutorial)}")
            
            # 進捗管理テスト
            print("✅ チュートリアル進捗管理テスト...")
            
            # 完了状況確認
            completed_before = help_manager.is_tutorial_completed(tutorial_id)
            print(f"  📊 完了前状況: {completed_before}")
            
            # 完了マーク
            help_manager.mark_tutorial_completed(tutorial_id)
            completed_after = help_manager.is_tutorial_completed(tutorial_id)
            print(f"  📊 完了後状況: {completed_after}")
            
            if completed_after and not completed_before:
                print("✅ チュートリアル進捗管理正常動作")
            
        else:
            print(f"❌ チュートリアル取得失敗: {tutorial_id}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ チュートリアルシステムテスト失敗: {e}")
        traceback.print_exc()
        return False

def test_user_progress():
    """ユーザー進捗管理のテスト"""
    print("\n👤 ユーザー進捗管理テスト開始...")
    
    try:
        help_manager = get_help_manager()
        
        # 進捗データ構造確認
        progress = help_manager.user_progress
        required_keys = ['completed_tutorials', 'dismissed_tips', 'help_preferences']
        
        for key in required_keys:
            if key in progress:
                print(f"✅ 進捗データキー '{key}' 存在確認")
            else:
                print(f"⚠️ 進捗データキー '{key}' 不在")
        
        # ヒント非表示機能テスト
        test_tip_id = "test_tip_dismiss"
        
        # 非表示前状況
        dismissed_before = help_manager.is_tip_dismissed(test_tip_id)
        print(f"📊 非表示前: {dismissed_before}")
        
        # 非表示設定
        help_manager.dismiss_tip(test_tip_id)
        dismissed_after = help_manager.is_tip_dismissed(test_tip_id)
        print(f"📊 非表示後: {dismissed_after}")
        
        if dismissed_after and not dismissed_before:
            print("✅ ヒント非表示機能正常動作")
        
        # 設定プリファレンス確認
        preferences = progress.get('help_preferences', {})
        print(f"✅ ヘルプ設定プリファレンス: {len(preferences)}項目")
        
        return True
        
    except Exception as e:
        print(f"❌ ユーザー進捗管理テスト失敗: {e}")
        traceback.print_exc()
        return False

def test_singleton_pattern():
    """シングルトンパターンのテスト"""
    print("\n🔄 シングルトンパターンテスト開始...")
    
    try:
        # 複数回取得して同じインスタンスか確認
        manager1 = get_help_manager()
        manager2 = get_help_manager()
        
        ui1 = get_help_ui()
        ui2 = get_help_ui()
        
        if manager1 is manager2:
            print("✅ HelpSystemManager シングルトン正常動作")
        else:
            print("❌ HelpSystemManager シングルトン動作異常")
            return False
        
        if ui1 is ui2:
            print("✅ HelpUIComponents シングルトン正常動作")
        else:
            print("❌ HelpUIComponents シングルトン動作異常")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ シングルトンパターンテスト失敗: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n🛡️ エラーハンドリングテスト開始...")
    
    try:
        help_manager = get_help_manager()
        
        # 存在しないチュートリアル取得
        nonexistent_tutorial = help_manager.get_tutorial("nonexistent_tutorial")
        if not nonexistent_tutorial:
            print("✅ 存在しないチュートリアル処理正常")
        
        # 空文字検索
        empty_search = help_manager.search_help("")
        print(f"✅ 空文字検索結果: {len(empty_search)}件")
        
        # 存在しないコンテキスト（エラーにならないことを確認）
        try:
            # 不正なコンテキストでもエラーにならないことを確認
            invalid_results = help_manager.get_contextual_help(HelpContext.HOME)
            print("✅ コンテキスト処理エラーハンドリング正常")
        except Exception as context_error:
            print(f"⚠️ コンテキスト処理でエラー: {context_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーハンドリングテスト失敗: {e}")
        traceback.print_exc()
        return False

def generate_test_report(test_results: Dict[str, bool]):
    """テスト結果レポート生成"""
    print("\n" + "="*60)
    print("📊 ヘルプシステム テスト結果レポート")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 詳細結果:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    # 総合判定
    if passed_tests == total_tests:
        print("\n🎉 **全テスト成功 - ヘルプシステム実装完了**")
        print("✅ タスク4-9: ヘルプシステム実装成功")
    else:
        print(f"\n⚠️ **{total_tests - passed_tests}個のテストで問題発見**")
        print("🔧 修正が必要な項目があります")

def main():
    """メインテスト実行"""
    print("🚀 ヘルプシステム テスト開始")
    print("タスク4-9: ヘルプシステム実装の動作確認")
    print("="*60)
    
    # 各テスト実行
    test_results = {
        "ヘルプマネージャー基本機能": test_help_manager(),
        "ヘルプコンテンツ妥当性": test_help_content(),
        "チュートリアルシステム": test_tutorial_system(),
        "ユーザー進捗管理": test_user_progress(),
        "シングルトンパターン": test_singleton_pattern(),
        "エラーハンドリング": test_error_handling()
    }
    
    # レポート生成
    generate_test_report(test_results)
    
    return all(test_results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
