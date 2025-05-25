"""
LLMサービスユーティリティ

LLMサービスの簡易利用インターフェースを提供します。
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator

from .llm_service import llm_service, GenerationRequest, GenerationConfig
from .llm_initializer import initialize_llm_service, shutdown_llm_service

logger = logging.getLogger(__name__)

class LLMServiceClient:
    """LLMサービスの簡易クライアント"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self, config_path: str = "config.json") -> bool:
        """LLMサービスの初期化"""
        if self._initialized:
            return True
        
        success = await initialize_llm_service(config_path)
        if success:
            self._initialized = True
            logger.info("LLMサービスクライアントを初期化しました")
        return success
    
    async def generate_text(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """テキスト生成"""
        if not self._initialized:
            await self.initialize()
        
        config = GenerationConfig(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=kwargs.get('top_p', 0.9),
            top_k=kwargs.get('top_k', 40),
            stop_sequences=kwargs.get('stop_sequences', []),
            seed=kwargs.get('seed')
        )
        
        request = GenerationRequest(
            prompt=prompt,
            model_name=model,
            config=config
        )
        
        response = await llm_service.generate(request)
        
        if response.error:
            logger.error(f"生成エラー: {response.error}")
            return f"[Error] {response.error}"
        
        return response.text
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """ストリーミングテキスト生成"""
        if not self._initialized:
            await self.initialize()
        
        config = GenerationConfig(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=kwargs.get('top_p', 0.9),
            top_k=kwargs.get('top_k', 40),
            stop_sequences=kwargs.get('stop_sequences', []),
            seed=kwargs.get('seed'),
            stream=True
        )
        
        request = GenerationRequest(
            prompt=prompt,
            model_name=model,
            config=config
        )
        
        async for chunk in llm_service.generate_stream(request):
            yield chunk
    
    async def list_available_models(self) -> List[str]:
        """利用可能なモデル一覧"""
        if not self._initialized:
            await self.initialize()
        
        models = llm_service.list_all_models()
        return [model.name for model in models if model.is_available]
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """モデル情報取得"""
        if not self._initialized:
            await self.initialize()
        
        model_info = llm_service.get_model_info(model_name)
        if not model_info:
            return None
        
        return {
            "name": model_info.name,
            "display_name": model_info.display_name,
            "type": model_info.model_type.value,
            "capabilities": [cap.value for cap in model_info.capabilities],
            "max_tokens": model_info.max_tokens,
            "context_length": model_info.context_length,
            "parameter_size": model_info.parameter_size,
            "memory_requirement": model_info.memory_requirement,
            "description": model_info.description,
            "is_available": model_info.is_available,
            "performance_score": model_info.performance_score
        }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """サービス状態取得"""
        if not self._initialized:
            await self.initialize()
        
        return await llm_service.get_service_status()
    
    async def shutdown(self):
        """サービス終了"""
        if self._initialized:
            await shutdown_llm_service()
            self._initialized = False
            logger.info("LLMサービスクライアントを終了しました")

# グローバルクライアントインスタンス
llm_client = LLMServiceClient()

# 便利関数
async def generate_text(prompt: str, **kwargs) -> str:
    """グローバルクライアント経由でテキスト生成"""
    return await llm_client.generate_text(prompt, **kwargs)

async def generate_stream(prompt: str, **kwargs) -> AsyncGenerator[str, None]:
    """グローバルクライアント経由でストリーミング生成"""
    async for chunk in llm_client.generate_stream(prompt, **kwargs):
        yield chunk

async def list_models() -> List[str]:
    """利用可能なモデル一覧"""
    return await llm_client.list_available_models()

async def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    """モデル情報取得"""
    return await llm_client.get_model_info(model_name)

async def get_service_status() -> Dict[str, Any]:
    """サービス状態取得"""
    return await llm_client.get_service_status()

# 同期版ラッパー（必要に応じて）
def generate_text_sync(prompt: str, **kwargs) -> str:
    """同期版テキスト生成"""
    return asyncio.run(generate_text(prompt, **kwargs))

def list_models_sync() -> List[str]:
    """同期版モデル一覧"""
    return asyncio.run(list_models())

def get_service_status_sync() -> Dict[str, Any]:
    """同期版サービス状態"""
    return asyncio.run(get_service_status())
