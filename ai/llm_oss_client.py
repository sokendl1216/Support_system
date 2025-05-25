# OSSモデル用LLMクライアントの実装（統合抽象化レイヤー利用）
import asyncio
import logging
from typing import Optional, List, AsyncGenerator
from .agent_base import LLMClient
from .llm_service import llm_service, GenerationRequest, GenerationConfig

logger = logging.getLogger(__name__)

class OSSLLMClient(LLMClient):
    """OSS（無料）LLMモデル用のクライアント - 統合抽象化レイヤー経由"""
    
    def __init__(self, model: str = None, **config):
        """
        Args:
            model: 使用するモデル名（指定しない場合は自動選択）
            **config: 生成設定のパラメータ
        """
        self.model = model
        self.generation_config = GenerationConfig(
            temperature=config.get('temperature', 0.7),
            top_p=config.get('top_p', 0.9),
            top_k=config.get('top_k', 40),
            max_tokens=config.get('max_tokens', 1000),
            stream=config.get('stream', False)
        )
    
    def generate(self, prompt: str) -> str:
        """統合LLMサービスを使用してテキスト生成（同期版）"""
        try:
            # 非同期関数を同期的に実行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既にイベントループが動いている場合
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._async_generate(prompt))
                    return future.result(timeout=30)
            else:
                # 新しいイベントループを作成
                return asyncio.run(self._async_generate(prompt))
                
        except Exception as e:
            logger.error(f"同期生成エラー: {e}")
            return f"[Error] {prompt} (エラー: {str(e)})"
    
    async def generate_async(self, prompt: str) -> str:
        """統合LLMサービスを使用してテキスト生成（非同期版）"""
        return await self._async_generate(prompt)
    
    async def generate_stream_async(self, prompt: str) -> AsyncGenerator[str, None]:
        """統合LLMサービスを使用してストリーミング生成"""
        try:
            request = GenerationRequest(
                prompt=prompt,
                model_name=self.model,
                config=self.generation_config
            )
            
            async for chunk in llm_service.generate_stream(request):
                yield chunk
                
        except Exception as e:
            logger.error(f"ストリーミング生成エラー: {e}")
            yield f"[Error] {str(e)}"
    
    async def _async_generate(self, prompt: str) -> str:
        """内部用非同期生成メソッド"""
        try:
            request = GenerationRequest(
                prompt=prompt,
                model_name=self.model,
                config=self.generation_config
            )
            
            response = await llm_service.generate(request)
            
            if response.error:
                return f"[Error] {prompt} ({response.error})"
            
            return response.text
            
        except Exception as e:
            logger.error(f"非同期生成エラー: {e}")
            return f"[Error] {prompt} (エラー: {str(e)})"
    
    def list_available_models(self) -> List[str]:
        """利用可能なモデル一覧を取得"""
        try:
            models = llm_service.list_all_models()
            return [model.name for model in models if model.is_available]
        except Exception as e:
            logger.error(f"モデル一覧取得エラー: {e}")
            return []
    
    async def get_service_status(self) -> dict:
        """LLMサービスの状態を取得"""
        try:
            return await llm_service.get_service_status()
        except Exception as e:
            logger.error(f"サービス状態取得エラー: {e}")
            return {"error": str(e), "service_healthy": False}
    
    def set_model(self, model_name: str):
        """使用モデルを変更"""
        self.model = model_name
        logger.info(f"使用モデルを変更しました: {model_name}")
    
    def update_config(self, **config):
        """生成設定を更新"""
        for key, value in config.items():
            if hasattr(self.generation_config, key):
                setattr(self.generation_config, key, value)
        logger.info(f"生成設定を更新しました: {config}")

# 後方互換性のためのエイリアス
class OllamaLLMClient(OSSLLMClient):
    """後方互換性のためのエイリアス"""
    pass
