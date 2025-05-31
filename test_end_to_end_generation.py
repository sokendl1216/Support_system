#!/usr/bin/env python3
"""
エンドツーエンド プログラム生成テスト

プログラム生成システムの完全なワークフローをテストします。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from data.models.job import JobInput
from services.program_generator.service import ProgramGeneratorService

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_python_generation():
    """Python プログラム生成テスト"""
    print("\n" + "="*60)
    print("Python プログラム生成テスト")
    print("="*60)
    
    try:
        # ジョブ入力作成
        job_input = JobInput(
            job_id="test_python_001",
            job_type="python",
            mode="basic",
            parameters={
                "description": "簡単な挨拶メッセージを表示するPythonスクリプトを作成してください。ユーザーから名前を入力してもらい、個人化された挨拶を表示する機能を含めてください。",
                "project_type": "script",
                "name": "greeting_script"
            }
        )
        
        # サービス初期化
        service = ProgramGeneratorService()
        
        # プレビュー生成テスト
        print("1. プレビュー生成テスト")
        preview = await service.preview_generation(job_input)
        if 'error' not in preview:
            print(f"✓ プレビュー生成成功")
            print(f"  - 言語: {preview.get('language')}")
            print(f"  - 予想ファイル数: {len(preview.get('estimated_files', []))}")
            print(f"  - ファイル: {', '.join(preview.get('estimated_files', []))}")
        else:
            print(f"✗ プレビュー生成エラー: {preview['error']}")
            return False
        
        # 実際の生成テスト
        print("\n2. プログラム生成テスト")
        result = await service.generate_program(job_input)
        
        if result.status == 'completed':
            print(f"✓ プログラム生成成功")
            print(f"  - ジョブID: {result.job_id}")
            print(f"  - ファイル数: {len(result.files)}")
            print(f"  - 生成時間: {result.metadata.get('generation_time', 'N/A')}")
            
            # ファイル内容確認
            for file_info in result.files[:3]:  # 最初の3ファイルのみ表示
                print(f"\n--- {file_info['filename']} ---")
                content = file_info['content']
                if len(content) > 200:
                    print(content[:200] + "...")
                else:
                    print(content)
            
            return True
        else:
            print(f"✗ プログラム生成失敗: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"✗ Python生成テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_javascript_generation():
    """JavaScript プログラム生成テスト"""
    print("\n" + "="*60)
    print("JavaScript プログラム生成テスト")
    print("="*60)
    
    try:
        # ジョブ入力作成
        job_input = JobInput(
            job_id="test_js_001",
            job_type="javascript",
            mode="basic",
            parameters={
                "description": "インタラクティブなTODOリストWebアプリケーションを作成してください。タスクの追加、削除、完了状態の切り替えができる機能を含めてください。",
                "project_type": "web_app",
                "name": "todo_app"
            }
        )
        
        # サービス初期化
        service = ProgramGeneratorService()
        
        # プレビュー生成テスト
        print("1. プレビュー生成テスト")
        preview = await service.preview_generation(job_input)
        if 'error' not in preview:
            print(f"✓ プレビュー生成成功")
            print(f"  - 言語: {preview.get('language')}")
            print(f"  - 予想ファイル数: {len(preview.get('estimated_files', []))}")
        else:
            print(f"✗ プレビュー生成エラー: {preview['error']}")
            return False
        
        # 実際の生成テスト
        print("\n2. プログラム生成テスト")
        result = await service.generate_program(job_input)
        
        if result.status == 'completed':
            print(f"✓ プログラム生成成功")
            print(f"  - ジョブID: {result.job_id}")
            print(f"  - ファイル数: {len(result.files)}")
            return True
        else:
            print(f"✗ プログラム生成失敗: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"✗ JavaScript生成テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_web_generation():
    """Web プログラム生成テスト"""
    print("\n" + "="*60)
    print("Web プログラム生成テスト")
    print("="*60)
    
    try:
        # ジョブ入力作成
        job_input = JobInput(
            job_id="test_web_001",
            job_type="web",
            mode="basic",
            parameters={
                "description": "レスポンシブデザインの個人ポートフォリオサイトを作成してください。プロフィール、スキル、プロジェクト、連絡先のセクションを含めてください。",
                "project_type": "portfolio",
                "name": "portfolio_site"
            }
        )
        
        # サービス初期化
        service = ProgramGeneratorService()
        
        # プレビュー生成テスト
        print("1. プレビュー生成テスト")
        preview = await service.preview_generation(job_input)
        if 'error' not in preview:
            print(f"✓ プレビュー生成成功")
            print(f"  - 言語: {preview.get('language')}")
            print(f"  - 予想ファイル数: {len(preview.get('estimated_files', []))}")
        else:
            print(f"✗ プレビュー生成エラー: {preview['error']}")
            return False
        
        # 実際の生成テスト
        print("\n2. プログラム生成テスト")
        result = await service.generate_program(job_input)
        
        if result.status == 'completed':
            print(f"✓ プログラム生成成功")
            print(f"  - ジョブID: {result.job_id}")
            print(f"  - ファイル数: {len(result.files)}")
            return True
        else:
            print(f"✗ プログラム生成失敗: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"✗ Web生成テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_service_features():
    """サービス機能テスト"""
    print("\n" + "="*60)
    print("サービス機能テスト")
    print("="*60)
    
    try:
        service = ProgramGeneratorService()
        
        # サポート言語取得テスト
        print("1. サポート言語取得テスト")
        languages = await service.get_supported_languages()
        print(f"✓ サポート言語: {', '.join(languages)}")
        
        # 言語別テンプレート取得テスト
        print("\n2. 言語別テンプレート取得テスト")
        for language in languages[:3]:  # 最初の3言語のみテスト
            templates = await service.get_language_templates(language)
            print(f"✓ {language}: {len(templates)}個のテンプレート")
            
        return True
        
    except Exception as e:
        print(f"✗ サービス機能テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト実行"""
    print("="*60)
    print("エンドツーエンド プログラム生成テスト開始")
    print("="*60)
    
    results = []
    
    # 各テストを実行
    tests = [
        ("サービス機能テスト", test_service_features),
        ("Python生成テスト", test_python_generation),
        ("JavaScript生成テスト", test_javascript_generation),
        ("Web生成テスト", test_web_generation),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}開始...")
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}でエラー: {str(e)}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{len(results)} テスト成功")
    
    if passed == len(results):
        print("🎉 全てのテストが成功しました！")
    else:
        print("⚠️ 一部のテストが失敗しました。")

if __name__ == "__main__":
    asyncio.run(main())
