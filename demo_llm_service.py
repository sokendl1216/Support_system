"""
LLMサービス抽象化レイヤーのサンプル使用例

統一インターフェースによるOSSモデル活用のデモンストレーション
"""

import asyncio
import logging
from ai import (
    initialize_llm_service,
    shutdown_llm_service,
    generate_text,
    generate_stream,
    list_models,
    get_model_info,
    get_service_status,
    LLMServiceClient
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_basic_usage():
    """基本的な使用例のデモ"""
    print("=== LLMサービス抽象化レイヤー デモ ===\n")
    
    # 1. サービス初期化
    print("1. LLMサービスを初期化中...")
    success = await initialize_llm_service()
    if not success:
        print("❌ LLMサービスの初期化に失敗しました")
        return
    print("✅ LLMサービスが正常に初期化されました\n")
    
    # 2. サービス状態確認
    print("2. サービス状態を確認中...")
    status = await get_service_status()
    print(f"サービス健康状態: {'✅ 正常' if status['service_healthy'] else '❌ 異常'}")
    print(f"利用可能なモデル数: {status['available_models']}")
    print()
    
    # 3. 利用可能なモデル一覧
    print("3. 利用可能なモデル一覧:")
    models = await list_models()
    for model in models:
        model_info = await get_model_info(model)
        if model_info:
            print(f"  - {model_info['display_name']} ({model})")
            print(f"    タイプ: {model_info['type']}")
            print(f"    パラメータ数: {model_info['parameter_size']}")
            print(f"    利用可能: {'✅' if model_info['is_available'] else '❌'}")
    print()
    
    # 4. テキスト生成（自動モデル選択）
    print("4. テキスト生成（自動モデル選択）:")
    prompt = "日本の美しい四季について、短い詩を作ってください。"
    print(f"プロンプト: {prompt}")
    
    try:
        response = await generate_text(prompt, temperature=0.8, max_tokens=200)
        print(f"応答:\n{response}\n")
    except Exception as e:
        print(f"❌ 生成エラー: {e}\n")
    
    # 5. 指定モデルでの生成
    if models:
        print("5. 指定モデルでのテキスト生成:")
        model_name = models[0]
        prompt = "プログラミングの学習方法について教えてください。"
        print(f"使用モデル: {model_name}")
        print(f"プロンプト: {prompt}")
        
        try:
            response = await generate_text(
                prompt, 
                model=model_name,
                temperature=0.7, 
                max_tokens=300
            )
            print(f"応答:\n{response}\n")
        except Exception as e:
            print(f"❌ 生成エラー: {e}\n")
    
    # 6. ストリーミング生成
    print("6. ストリーミング生成:")
    prompt = "人工知能の未来について説明してください。"
    print(f"プロンプト: {prompt}")
    print("応答:")
    
    try:
        async for chunk in generate_stream(prompt, temperature=0.7, max_tokens=200):
            print(chunk, end='', flush=True)
        print("\n")
    except Exception as e:
        print(f"❌ ストリーミング生成エラー: {e}\n")
    
    # サービス終了
    print("7. LLMサービスを終了中...")
    await shutdown_llm_service()
    print("✅ LLMサービスが正常に終了されました")

async def demo_client_usage():
    """クライアントクラスを使用した例"""
    print("\n=== LLMServiceClient使用例 ===\n")
    
    client = LLMServiceClient()
    
    try:
        # 初期化
        await client.initialize()
        
        # コード生成特化のプロンプト
        code_prompt = """
以下の要件でPythonのクラスを作成してください：
- クラス名: Calculator
- メソッド: add, subtract, multiply, divide
- エラーハンドリングを含める
"""
        
        print("コード生成の例:")
        print(f"プロンプト: {code_prompt}")
        
        # DeepSeek Coderがあれば使用、なければ自動選択
        models = await client.list_available_models()
        model = "deepseek-coder" if "deepseek-coder" in models else None
        
        if model:
            print(f"使用モデル: {model} (コード生成特化)")
        else:
            print("使用モデル: 自動選択")
        
        response = await client.generate_text(
            code_prompt,
            model=model,
            temperature=0.3,  # コード生成では低めの温度
            max_tokens=500
        )
        
        print(f"生成されたコード:\n{response}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        await client.shutdown()

async def demo_error_handling():
    """エラーハンドリングのデモ"""
    print("\n=== エラーハンドリング例 ===\n")
    
    client = LLMServiceClient()
    
    try:
        # わざと初期化をスキップしてエラーを発生させる
        print("1. 初期化なしでの生成テスト:")
        response = await client.generate_text("テストプロンプト")
        print(f"応答: {response}")
        
        # 存在しないモデルを指定
        await client.initialize()
        print("\n2. 存在しないモデル指定テスト:")
        response = await client.generate_text(
            "テストプロンプト", 
            model="non-existent-model"
        )
        print(f"応答: {response}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        await client.shutdown()

async def demo_model_mapping():
    """モデル名マッピング機能のテスト"""
    print("=== モデル名マッピング機能テスト ===\n")
    
    from ai.providers.ollama_provider import OllamaProvider
    
    # Ollamaプロバイダーのインスタンスを取得
    from ai.llm_service import llm_service
    ollama_provider = llm_service.get_provider("ollama")
    
    if not ollama_provider:
        print("❌ Ollamaプロバイダーが見つかりません")
        return
    
    # 実際のモデル一覧を取得
    print("1. 実際に利用可能なOllamaモデル:")
    actual_models = await ollama_provider.get_available_models()
    for model in actual_models:
        print(f"  - {model}")
    print()
      # 設定ファイルのモデル名マッピングをテスト
    print("2. 設定ファイルのモデル名マッピングテスト:")
    test_models = ["deepseek-coder", "openhermes", "qwen", "mistral", "llama2"]
    
    for config_name in test_models:
        actual_model = await ollama_provider._find_actual_model_name(config_name)
        status = "✅ マッピング成功" if actual_model else "❌ マッピング失敗"
        print(f"  設定名: {config_name} -> 実際のモデル: {actual_model or 'なし'} ({status})")
    print()
    
    # 自動選択のテスト
    print("3. 自動モデル選択テスト:")
    selected_model = await ollama_provider._select_best_model()
    print(f"  自動選択されたモデル: {selected_model}")
    print()

async def main():
    """メイン実行関数"""
    try:
        # 基本的な使用例
        await demo_basic_usage()
        
        # モデル名マッピング機能テスト
        await demo_model_mapping()
        
        # クライアント使用例
        await demo_client_usage()
        
        # エラーハンドリング例
        await demo_error_handling()
        
        # モデル名マッピング機能テスト
        await demo_model_mapping()
        
    except KeyboardInterrupt:
        print("\n\n操作がキャンセルされました")
    except Exception as e:
        logger.error(f"デモ実行中にエラーが発生しました: {e}")
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("LLMサービス抽象化レイヤーのデモを開始します...")
    print("注意: Ollamaサーバーが localhost:11434 で動作している必要があります\n")
    
    # 非同期実行
    asyncio.run(main())
