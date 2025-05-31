#!/usr/bin/env python3
"""
Ollamaプロバイダー最適化版の動作確認テスト
セッション管理とリトライ機能のテスト
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.providers.ollama_provider import OllamaProvider
from ai.llm_service import GenerationRequest, GenerationConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_ollama_optimized():
    """Ollamaプロバイダー最適化版のテスト"""
    
    print("=== Ollamaプロバイダー最適化版テスト開始 ===")
    
    # プロバイダーの初期化
    provider = OllamaProvider()
    
    # 1. ヘルスチェックテスト
    print("\n1. ヘルスチェックテスト")
    print("-" * 40)
    is_healthy = await provider.is_healthy()
    print(f"ヘルスチェック結果: {'✓ 正常' if is_healthy else '✗ 異常'}")
    
    if not is_healthy:
        print("⚠️  Ollamaサービスが起動していない可能性があります")
        print("   以下のコマンドでOllamaを起動してください：")
        print("   ollama serve")
        return
    
    # 2. 利用可能モデル取得テスト
    print("\n2. 利用可能モデル取得テスト")
    print("-" * 40)
    models = await provider.get_available_models()
    if models:
        print(f"利用可能なモデル数: {len(models)}")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
    else:
        print("⚠️  利用可能なモデルがありません")
        return
    
    # 3. モデル自動選択テスト
    print("\n3. モデル自動選択テスト")
    print("-" * 40)
    selected_model = await provider._select_best_model()
    print(f"自動選択されたモデル: {selected_model}")
    
    # 4. 基本的なテキスト生成テスト
    print("\n4. 基本的なテキスト生成テスト")
    print("-" * 40)
    
    config = GenerationConfig(
        temperature=0.7,
        max_tokens=100,
        top_p=0.9
    )
    
    request = GenerationRequest(
        prompt="こんにちは。簡単な挨拶を返してください。",
        config=config
    )
    
    start_time = time.time()
    response = await provider.generate(request)
    end_time = time.time()
    
    print(f"リクエスト:")
    print(f"  プロンプト: {request.prompt}")
    print(f"レスポンス:")
    print(f"  モデル: {response.model_name}")
    print(f"  生成時間: {response.generation_time:.2f}秒")
    print(f"  総時間: {end_time - start_time:.2f}秒")
    print(f"  トークン数: {response.token_count}")
    print(f"  完了理由: {response.finish_reason}")
    
    if response.error:
        print(f"  エラー: {response.error}")
    else:
        print(f"  生成テキスト:")
        print(f"    {response.text}")
    
    # 5. ストリーミング生成テスト
    print("\n5. ストリーミング生成テスト")
    print("-" * 40)
    
    stream_request = GenerationRequest(
        prompt="1から5まで数えてください。",
        config=config
    )
    
    print(f"プロンプト: {stream_request.prompt}")
    print("ストリーミング出力:")
    print("  ", end="", flush=True)
    
    start_time = time.time()
    async for chunk in provider.generate_stream(stream_request):
        if chunk.startswith("[ERROR]"):
            print(f"\n  エラー: {chunk}")
            break
        print(chunk, end="", flush=True)
    
    end_time = time.time()
    print(f"\n  ストリーミング時間: {end_time - start_time:.2f}秒")
    
    # 6. リトライ機能テスト（オプション）
    print("\n6. リトライ機能テスト")
    print("-" * 40)
    print("リトライ設定:")
    print(f"  最大リトライ回数: {provider.retry_config.max_retries}")
    print(f"  初期遅延: {provider.retry_config.initial_delay}秒")
    print(f"  最大遅延: {provider.retry_config.max_delay}秒")
    print(f"  バックオフ倍率: {provider.retry_config.backoff_multiplier}")
    
    print("\n=== テスト完了 ===")

async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    print("\n=== エラーハンドリングテスト ===")
    
    # 存在しないエンドポイントでプロバイダーを作成
    invalid_provider = OllamaProvider(base_url="http://localhost:99999")
    
    # ヘルスチェック（失敗するはず）
    is_healthy = await invalid_provider.is_healthy()
    print(f"無効なエンドポイントのヘルスチェック: {'✓ 正常' if is_healthy else '✗ 異常（期待される結果）'}")
    
    # 生成リクエスト（失敗するはず）
    config = GenerationConfig(temperature=0.7, max_tokens=50)
    request = GenerationRequest(prompt="テストプロンプト", config=config)
    
    response = await invalid_provider.generate(request)
    if response.error:
        print(f"エラーハンドリング確認: ✓ エラーが適切に処理されました")
        print(f"  エラー内容: {response.error}")
    else:
        print(f"エラーハンドリング確認: ✗ エラーが期待されましたが成功しました")

if __name__ == "__main__":
    try:
        # 基本テスト
        asyncio.run(test_ollama_optimized())
        
        # エラーハンドリングテスト
        asyncio.run(test_error_handling())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
    except Exception as e:
        print(f"\n\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
