#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プログラム生成システム - シンプルテンプレート読み込みテスト
"""

import os
import sys
import json
import traceback

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("シンプル テンプレート読み込みテスト開始")
print("=" * 60)

try:
    # 1. ベースクラスの直接テスト
    print("1. ベースクラスのテンプレート読み込みテスト")
    print("-" * 40)
    
    from services.program_generator.base import BaseProgramGenerator
      # ダミーの実装を作成
    class TestGenerator(BaseProgramGenerator):
        def __init__(self):
            self.language = "test"
            self.template_dir = "services/program_generator/templates"
            
        async def generate(self, job_input):
            return None
            
        async def get_available_templates(self):
            return []
            
        async def get_generation_preview(self, job_input):
            return {}
            
        async def validate_input(self, job_input):
            return True
    
    generator = TestGenerator()
    
    # JSONテンプレート読み込みテスト
    python_templates = generator._load_template_from_json("python_templates.json")
    if python_templates:
        print(f"✓ Python テンプレート読み込み成功: {len(python_templates)} 件")
        template_names = [t.get('name', 'Unknown') for t in python_templates]
        print(f"  テンプレート: {', '.join(template_names[:3])}...")
    else:
        print("✗ Python テンプレート読み込み失敗")
        
    javascript_templates = generator._load_template_from_json("javascript_templates.json")
    if javascript_templates:
        print(f"✓ JavaScript テンプレート読み込み成功: {len(javascript_templates)} 件")
        template_names = [t.get('name', 'Unknown') for t in javascript_templates]
        print(f"  テンプレート: {', '.join(template_names[:3])}...")
    else:
        print("✗ JavaScript テンプレート読み込み失敗")
        
    web_templates = generator._load_template_from_json("web_templates.json")
    if web_templates:
        print(f"✓ Web テンプレート読み込み成功: {len(web_templates)} 件")
        template_names = [t.get('name', 'Unknown') for t in web_templates]
        print(f"  テンプレート: {', '.join(template_names[:3])}...")
    else:
        print("✗ Web テンプレート読み込み失敗")

except Exception as e:
    print(f"✗ ベースクラステストエラー: {str(e)}")
    traceback.print_exc()

try:
    # 2. 個別ジェネレーターテスト（インポートのみ）
    print("\n2. 個別ジェネレーターのインポートテスト")
    print("-" * 40)
    
    # Python ジェネレーター
    try:
        from services.program_generator.python.generator import PythonGenerator
        print("✓ PythonGenerator インポート成功")
    except Exception as e:
        print(f"✗ PythonGenerator インポートエラー: {str(e)}")
    
    # JavaScript ジェネレーター  
    try:
        from services.program_generator.javascript.generator import JavaScriptGenerator
        print("✓ JavaScriptGenerator インポート成功")
    except Exception as e:
        print(f"✗ JavaScriptGenerator インポートエラー: {str(e)}")
    
    # Web ジェネレーター
    try:
        from services.program_generator.web.generator import WebGenerator
        print("✓ WebGenerator インポート成功")
    except Exception as e:
        print(f"✗ WebGenerator インポートエラー: {str(e)}")

except Exception as e:
    print(f"✗ ジェネレーターインポートテストエラー: {str(e)}")

try:
    # 3. テンプレートファイルの直接読み込みテスト
    print("\n3. テンプレートファイル直接読み込みテスト")
    print("-" * 40)
    
    template_files = [
        "services/program_generator/templates/python_templates.json",
        "services/program_generator/templates/javascript_templates.json",
        "services/program_generator/templates/web_templates.json"
    ]
    
    for template_file in template_files:
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✓ {os.path.basename(template_file)}: {len(data)} テンプレート")
        except FileNotFoundError:
            print(f"✗ {os.path.basename(template_file)}: ファイルが見つかりません")
        except json.JSONDecodeError as e:
            print(f"✗ {os.path.basename(template_file)}: JSON解析エラー - {str(e)}")
        except Exception as e:
            print(f"✗ {os.path.basename(template_file)}: エラー - {str(e)}")

except Exception as e:
    print(f"✗ ファイル読み込みテストエラー: {str(e)}")

try:
    # 4. 実際のジェネレーターでのテンプレート読み込みテスト
    print("\n4. 実際のジェネレーターでのテンプレート読み込みテスト")
    print("-" * 40)
    
    # Python ジェネレーター
    try:
        python_gen = PythonGenerator()
        python_template = python_gen._load_template("basic_script")
        if python_template:
            print("✓ PythonGenerator: basic_script テンプレート読み込み成功")
        else:
            print("✗ PythonGenerator: basic_script テンプレート読み込み失敗")
    except Exception as e:
        print(f"✗ PythonGenerator テンプレート読み込みエラー: {str(e)}")
    
    # JavaScript ジェネレーター
    try:
        js_gen = JavaScriptGenerator()
        js_template = js_gen._load_template("basic_script")
        if js_template:
            print("✓ JavaScriptGenerator: basic_script テンプレート読み込み成功")
        else:
            print("✗ JavaScriptGenerator: basic_script テンプレート読み込み失敗")
    except Exception as e:
        print(f"✗ JavaScriptGenerator テンプレート読み込みエラー: {str(e)}")
    
    # Web ジェネレーター
    try:
        web_gen = WebGenerator()
        web_template = web_gen._load_template("static_website")
        if web_template:
            print("✓ WebGenerator: static_website テンプレート読み込み成功")
        else:
            print("✗ WebGenerator: static_website テンプレート読み込み失敗")
    except Exception as e:
        print(f"✗ WebGenerator テンプレート読み込みエラー: {str(e)}")

except Exception as e:
    print(f"✗ 実際のジェネレーターテストエラー: {str(e)}")

print("\n" + "=" * 60)
print("シンプル テンプレート読み込みテスト完了")
print("=" * 60)
