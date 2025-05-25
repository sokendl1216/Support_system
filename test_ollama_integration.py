#!/usr/bin/env python3
"""
Ollama統合テストスクリプト
Task 3-1a の最終確認用
"""

import asyncio
import json
from pathlib import Path
from ai.providers.ollama_provider import OllamaProvider
from ai.llm_service import GenerationRequest, GenerationConfig

async def test_ollama_integration():
    print('=' * 50)
    print('🚀 Ollama統合テスト開始')
    print('=' * 50)
    
    try:
        # 設定ファイルを読み込み
        config_path = Path('config/ollama_models.json')
        if not config_path.exists():
            print(f"❌ 設定ファイルが見つかりません: {config_path}")
            return False
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 設定ファイル読み込み成功: {config_path}")
        
        # OllamaProviderインスタンス作成
        provider = OllamaProvider(model_config=config['models'])
        print("✅ OllamaProvider インスタンス作成成功")
        
        # 1. ヘルスチェック
        print("\n📊 ヘルスチェック実行中...")
        is_healthy = await provider.is_healthy()
        if is_healthy:
            print("✅ Ollamaサーバー接続成功")
        else:
            print("❌ Ollamaサーバー接続失敗")
            return False
        
        # 2. 利用可能なモデル取得
        print("\n📋 利用可能なモデル取得中...")
        models = await provider.get_available_models()
        print(f"✅ 利用可能なモデル数: {len(models)}")
        for i, model in enumerate(models, 1):
            print(f"   {i}. {model}")
        
        if not models:
            print("❌ 利用可能なモデルがありません")
            return False
        
        # 3. モデル選択テスト
        print("\n🎯 最適モデル選択テスト...")
        selected = await provider._select_best_model()
        if selected:
            print(f"✅ 自動選択されたモデル: {selected}")
        else:
            print("❌ モデル選択に失敗しました")
            return False
        
        # 4. 簡単なテキスト生成テスト
        print("\n💬 テキスト生成テスト...")
        request = GenerationRequest(
            prompt="Hello, how are you?",
            config=GenerationConfig(
                max_tokens=50,
                temperature=0.7
            )
        )
        
        response = await provider.generate(request)
        if response.error:
            print(f"❌ テキスト生成エラー: {response.error}")
            return False
        else:
            print(f"✅ テキスト生成成功")
            print(f"   モデル: {response.model_name}")
            print(f"   生成時間: {response.generation_time:.2f}秒")
            print(f"   トークン数: {response.token_count}")
            print(f"   生成テキスト: {response.text[:100]}{'...' if len(response.text) > 100 else ''}")
        
        # 5. 設定ファイルモデルマッピングテスト
        print("\n🔍 設定ファイルモデルマッピングテスト...")
        for config_name in config['models']:
            actual_model = await provider._find_actual_model_name(config_name)
            if actual_model:
                print(f"   ✅ {config_name} -> {actual_model}")
            else:
                print(f"   ⚠️  {config_name} -> マッピング失敗（モデル未インストール）")
        
        print('\n' + '=' * 50)
        print('🎉 Ollama統合テスト完了！すべて正常に動作しています')
        print('✅ Task 3-1a (Ollama Installation & Setup) 完了確認')
        print('=' * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 統合テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama_integration())
    if success:
        print("\n🚀 次のタスクに進む準備ができました！")
    else:
        print("\n⚠️  問題を修正してから次のタスクに進んでください")
