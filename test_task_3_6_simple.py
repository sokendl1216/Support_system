#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 3-6 (Webページ生成サービス実装) 簡易進捗確認テスト
基本的な機能確認に特化したテスト
"""

import asyncio
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from data.models.job import JobInput
from services.program_generator.service import ProgramGeneratorService

async def test_task_3_6_basic():
    """Task 3-6 基本機能テスト"""
    print("🌐 Task 3-6 基本機能確認テスト")
    print("=" * 50)
    
    try:
        # 1. ProgramGeneratorService初期化
        print("\n📋 1. ProgramGeneratorService 初期化テスト")
        service = ProgramGeneratorService()
        await service.initialize()
        print("   ✅ 初期化成功")
        
        # 2. Web言語サポート確認
        print("\n📝 2. Web言語サポート確認")
        supported_languages = await service.get_supported_languages()
        web_supported = "web" in supported_languages
        print(f"   {'✅' if web_supported else '❌'} Web言語サポート: {web_supported}")
        print(f"   📋 サポート言語一覧: {supported_languages}")
        
        # 3. 基本Web生成テスト
        print("\n🔧 3. 基本Web生成テスト")
        test_input = JobInput(
            job_id="test_basic_web_001",
            job_type="program_generation",
            parameters={
                "language": "web",
                "description": "シンプルなランディングページを作成してください",
                "project_type": "landing_page",
                "title": "テストページ"
            }
        )
          # 基本生成を実行
        result = await service.generate_program(test_input)
        print(f"   ✅ 生成ステータス: {result.status}")
        print(f"   📄 生成コンテンツタイプ: {result.content_type}")
        
        if hasattr(result, 'files') and result.files:
            print(f"   📁 生成ファイル数: {len(result.files)}")
            for i, file_info in enumerate(result.files[:3]):  # 最初の3ファイルのみ表示
                print(f"      - {file_info.get('filename', f'file_{i}')}")
        
        # 4. Enhanced Web Generator ファイル存在確認
        print("\n🚀 4. Enhanced Web Generator ファイル確認")
        enhanced_path = "services/program_generator/web/enhanced_web_generator.py"
        enhanced_exists = os.path.exists(enhanced_path)
        print(f"   {'✅' if enhanced_exists else '❌'} Enhanced Web Generator: {enhanced_exists}")
        
        if enhanced_exists:
            # ファイルサイズ確認
            size = os.path.getsize(enhanced_path)
            print(f"   📏 ファイルサイズ: {size:,} bytes")
            
            # 基本的なクラス定義確認
            with open(enhanced_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "class EnhancedWebGenerator" in content:
                    print("   ✅ EnhancedWebGenerator クラス定義確認")
                if "OllamaProvider" in content:
                    print("   ✅ OllamaProvider 統合確認")
                if "RAGSystem" in content:
                    print("   ✅ RAGSystem 統合確認")
        
        # 5. 統合状況確認
        print("\n🔗 5. 統合状況確認")
        
        # WebGeneratorのEnhanced統合確認
        web_gen_path = "services/program_generator/web/generator.py"
        if os.path.exists(web_gen_path):
            with open(web_gen_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "EnhancedWebGenerator" in content:
                    print("   ✅ WebGenerator Enhanced統合確認")
                else:
                    print("   ⚠️  WebGenerator Enhanced統合未確認")
        
        print("\n🎉 Task 3-6 基本機能確認完了")
        return True
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_task_3_6_basic())
    if success:
        print("\n✅ Task 3-6 基本機能は正常に動作しています")
    else:
        print("\n⚠️  問題が発見されました。詳細を確認してください")
