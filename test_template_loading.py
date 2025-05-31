#!/usr/bin/env python3
"""
テンプレート読み込み機能のテスト

プログラム生成システムのテンプレート読み込み機能が正常に動作することを確認します。
"""

import asyncio
import logging
import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from services.program_generator.python.generator import PythonGenerator
from services.program_generator.javascript.generator import JavaScriptGenerator
from services.program_generator.web.generator import WebGenerator
from data.models.job import JobInput

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_template_loading():
    """テンプレート読み込み機能のテスト"""
    print("=" * 60)
    print("テンプレート読み込み機能テスト開始")
    print("=" * 60)
    
    # テスト用のJobInputを作成
    test_job_input = JobInput(
        job_id="test_template_001",
        job_type="test",
        parameters={
            "description": "テスト用プログラム",
            "project_type": "script",
            "complexity": "simple"
        }
    )
    
    # 1. Pythonジェネレーターのテスト
    print("\n1. Pythonジェネレーターのテンプレート読み込みテスト")
    print("-" * 40)
    try:
        python_gen = PythonGenerator()
        
        # 利用可能なテンプレート一覧を取得
        python_templates = await python_gen.get_available_templates()
        print(f"利用可能なPythonテンプレート数: {len(python_templates)}")
        
        for template in python_templates:
            print(f"  - {template['name']}: {template['description']}")
        
        # 基本テンプレートの読み込みテスト
        template_content = await python_gen._load_template("python_script")
        if template_content:
            print(f"✓ python_scriptテンプレート読み込み成功 (長さ: {len(template_content)}文字)")
        else:
            print("✗ python_scriptテンプレート読み込み失敗")
            
    except Exception as e:
        print(f"✗ Pythonジェネレーターテストエラー: {e}")
    
    # 2. JavaScriptジェネレーターのテスト
    print("\n2. JavaScriptジェネレーターのテンプレート読み込みテスト")
    print("-" * 40)
    try:
        js_gen = JavaScriptGenerator()
        
        # 利用可能なテンプレート一覧を取得
        js_templates = await js_gen.get_available_templates()
        print(f"利用可能なJavaScriptテンプレート数: {len(js_templates)}")
        
        for template in js_templates:
            print(f"  - {template['name']}: {template['description']}")
        
        # 基本テンプレートの読み込みテスト
        template_content = await js_gen._load_template("javascript_script")
        if template_content:
            print(f"✓ javascript_scriptテンプレート読み込み成功 (長さ: {len(template_content)}文字)")
        else:
            print("✗ javascript_scriptテンプレート読み込み失敗")
            
    except Exception as e:
        print(f"✗ JavaScriptジェネレーターテストエラー: {e}")
    
    # 3. Webジェネレーターのテスト
    print("\n3. Webジェネレーターのテンプレート読み込みテスト")
    print("-" * 40)
    try:
        web_gen = WebGenerator()
        
        # 利用可能なテンプレート一覧を取得
        web_templates = await web_gen.get_available_templates()
        print(f"利用可能なWebテンプレート数: {len(web_templates)}")
        
        for template in web_templates:
            print(f"  - {template['name']}: {template['description']}")
        
        # 基本テンプレートの読み込みテスト
        template_content = await web_gen._load_template("web_static")
        if template_content:
            print(f"✓ web_staticテンプレート読み込み成功 (長さ: {len(template_content)}文字)")
        else:
            print("✗ web_staticテンプレート読み込み失敗")
            
    except Exception as e:
        print(f"✗ Webジェネレーターテストエラー: {e}")
    
    # 4. JSONテンプレートファイルの詳細テスト
    print("\n4. JSONテンプレートファイルの詳細テスト")
    print("-" * 40)
    try:
        # Pythonテンプレートの詳細テスト
        python_gen = PythonGenerator()
        python_template_data = python_gen._load_template_from_json("python_script")
        if python_template_data:
            print(f"✓ Pythonテンプレートデータ読み込み成功")
            print(f"  - テンプレート名: {python_template_data.get('name', 'N/A')}")
            print(f"  - 説明: {python_template_data.get('description', 'N/A')}")
            print(f"  - 変数: {python_template_data.get('variables', [])}")
            print(f"  - ファイル: {python_template_data.get('files', [])}")
        else:
            print("✗ Pythonテンプレートデータ読み込み失敗")
            
        # WebテンプレートのHTML/CSS/JavaScript分離テスト
        web_gen = WebGenerator()
        web_template_data = web_gen._load_template_from_json("web_static")
        if web_template_data:
            print(f"✓ Webテンプレートデータ読み込み成功")
            print(f"  - HTML部分: {'✓' if 'html' in web_template_data else '✗'}")
            print(f"  - CSS部分: {'✓' if 'css' in web_template_data else '✗'}")
            print(f"  - JavaScript部分: {'✓' if 'javascript' in web_template_data else '✗'}")
        else:
            print("✗ Webテンプレートデータ読み込み失敗")
            
    except Exception as e:
        print(f"✗ JSONテンプレート詳細テストエラー: {e}")
    
    print("\n" + "=" * 60)
    print("テンプレート読み込み機能テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_template_loading())
