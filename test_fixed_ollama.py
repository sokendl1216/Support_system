import asyncio
import json
from pathlib import Path
from ai.providers.ollama_provider_fixed_v2 import OllamaProvider

async def test_fixed_ollama_integration():
    print('=== 修正版Ollama統合テスト ===')
    
    # 設定ファイルを読み込み
    config_path = Path('config/ollama_models.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    provider = OllamaProvider(model_config=config['models'])
    
    # ヘルスチェック
    try:
        is_healthy = await provider.is_healthy()
        print(f'ヘルスチェック: {"成功" if is_healthy else "失敗"}')
        
        if is_healthy:
            # 利用可能なモデル取得
            models = await provider.get_available_models()
            print(f'利用可能なモデル数: {len(models)}')
            print(f'モデル一覧: {models[:3]}...' if len(models) > 3 else f'モデル一覧: {models}')
            
            # モデル選択テスト
            selected = await provider._select_best_model()
            print(f'自動選択されたモデル: {selected}')
            
            # 簡単な生成テスト
            if models:
                from ai.llm_service import GenerationRequest, GenerationConfig
                request = GenerationRequest(
                    prompt="Hello! Please respond briefly.",
                    config=GenerationConfig(max_tokens=50)
                )
                response = await provider.generate(request)
                print(f'生成テスト結果: {response.text[:100]}...')
                print(f'使用モデル: {response.model_name}')
                print(f'生成時間: {response.generation_time:.2f}秒')
        else:
            print('Ollamaサーバーが利用できません')
            
    except Exception as e:
        print(f'エラーが発生しました: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_ollama_integration())
