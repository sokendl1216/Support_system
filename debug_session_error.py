import asyncio
import aiohttp
import traceback

async def test_direct_ollama():
    """直接Ollama APIにアクセステスト"""
    print('=== 直接Ollama APIテスト ===')
    
    try:
        # 方法1: 基本的なHTTPセッション
        print('1. 基本HTTPセッションテスト')
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:11434/api/tags') as response:
                print(f'ステータス: {response.status}')
                if response.status == 200:
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    print(f'モデル数: {len(models)}')
                    print(f'モデル: {models}')
                else:
                    print(f'エラー: {response.status}')
    
    except Exception as e:
        print(f'基本テストエラー: {e}')
        traceback.print_exc()
    
    try:
        # 方法2: カスタムコネクターでのセッション
        print('\n2. カスタムコネクターテスト')
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get('http://localhost:11434/api/tags') as response:
                print(f'ステータス: {response.status}')
                if response.status == 200:
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    print(f'モデル数: {len(models)}')
                    print(f'モデル: {models}')
                else:
                    print(f'エラー: {response.status}')
        
        await connector.close()
    
    except Exception as e:
        print(f'カスタムコネクターテストエラー: {e}')
        traceback.print_exc()

    try:
        # 方法3: OllamaProvider._create_sessionメソッドテスト
        print('\n3. OllamaProvider._create_sessionテスト')
        from ai.providers.ollama_provider import OllamaProvider
        
        provider = OllamaProvider()
        session = provider._create_session()
        
        async with session:
            async with session.get('http://localhost:11434/api/tags') as response:
                print(f'ステータス: {response.status}')
                if response.status == 200:
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    print(f'モデル数: {len(models)}')
                    print(f'モデル: {models}')
                else:
                    print(f'エラー: {response.status}')
        
    except Exception as e:
        print(f'OllamaProvider._create_sessionテストエラー: {e}')
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_ollama())
