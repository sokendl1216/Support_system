import asyncio
import importlib
import sys

# モジュールを強制リロード
if 'ai.providers.ollama_provider' in sys.modules:
    importlib.reload(sys.modules['ai.providers.ollama_provider'])

from ai.providers.ollama_provider import OllamaProvider

async def test_new_session():
    print('=== 新しいセッション管理テスト ===')
    
    provider = OllamaProvider()
    
    # メソッドの存在確認
    print(f'_create_session メソッドが存在: {hasattr(provider, "_create_session")}')
    
    if hasattr(provider, '_create_session'):
        try:
            session = provider._create_session()
            print(f'セッション作成成功: {type(session)}')
            
            async with session:
                async with session.get('http://localhost:11434/api/tags') as response:
                    print(f'API呼び出し成功: {response.status}')
                    if response.status == 200:
                        result = await response.json()
                        models = [model["name"] for model in result.get("models", [])]
                        print(f'モデル数: {len(models)}')
        except Exception as e:
            print(f'エラー: {e}')
            import traceback
            traceback.print_exc()
    else:
        print('メソッドが見つかりません')
        # メソッド一覧を表示
        methods = [method for method in dir(provider) if not method.startswith('__')]
        print(f'利用可能なメソッド: {methods}')

if __name__ == "__main__":
    asyncio.run(test_new_session())
