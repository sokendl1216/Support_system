"""
LLMサービス抽象化レイヤー - 統一インターフェースによるOSSモデル活用

このモジュールは、以下の機能を提供します：
1. 複数のOSSモデルを統一インターフェースで利用
2. モデル間のシームレスな切り替え
3. エラーハンドリングと回復機構
4. パフォーマンス最適化
5. 設定ベースのモデル管理
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Any, Union, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """サポートされるモデルタイプ"""
    GENERAL = "general"          # 汎用タスク
    CODE = "code"               # コード生成・解析
    CHAT = "chat"               # 対話型
    INSTRUCTION = "instruction"  # 指示追従型
    EMBEDDING = "embedding"     # 埋め込みベクトル生成

class ModelCapability(Enum):
    """モデルの能力特性"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    EMBEDDING = "embedding"
    FUNCTION_CALLING = "function_calling"

@dataclass
class ModelInfo:
    """モデル情報"""
    name: str
    display_name: str
    model_type: ModelType
    capabilities: List[ModelCapability]
    max_tokens: int
    context_length: int
    parameter_size: str  # "7B", "13B", "70B" など
    memory_requirement: str  # "4GB", "8GB", "32GB" など
    description: str
    is_available: bool = False
    performance_score: float = 0.0  # 0.0-1.0

@dataclass
class GenerationConfig:
    """テキスト生成設定"""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 1000
    stop_sequences: List[str] = None
    seed: Optional[int] = None
    stream: bool = False
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []

@dataclass
class GenerationRequest:
    """生成リクエスト"""
    prompt: str
    model_name: Optional[str] = None
    config: Optional[GenerationConfig] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = GenerationConfig()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class GenerationResponse:
    """生成レスポンス"""
    text: str
    model_name: str
    generation_time: float
    token_count: int
    finish_reason: str  # "stop", "length", "error"
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス"""
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """テキスト生成"""
        pass
    
    @abstractmethod
    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """ストリーミングテキスト生成"""
        pass
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """利用可能なモデル一覧"""
        pass
    
    @abstractmethod
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """モデル情報取得"""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """ヘルスチェック"""
        pass

class ModelSelector:
    """モデル選択ロジック"""
    
    def __init__(self):
        self.selection_strategy = "capability_based"
        self.fallback_enabled = True
        
    def select_model(self, 
                    providers: List[LLMProvider],
                    capability: ModelCapability,
                    preferred_model: Optional[str] = None) -> Optional[str]:
        """
        要求される能力に基づいてモデルを選択
        
        Args:
            providers: 利用可能なプロバイダー一覧
            capability: 必要な能力
            preferred_model: 優先モデル名
            
        Returns:
            選択されたモデル名
        """
        available_models = []
        
        # 全プロバイダーから利用可能なモデルを収集
        for provider in providers:
            models = provider.list_models()
            for model in models:
                if model.is_available and capability in model.capabilities:
                    available_models.append(model)
        
        if not available_models:
            return None
        
        # 優先モデルが指定されている場合は優先
        if preferred_model:
            for model in available_models:
                if model.name == preferred_model:
                    return model.name
        
        # パフォーマンススコアで選択
        best_model = max(available_models, key=lambda m: m.performance_score)
        return best_model.name

class LLMServiceManager:
    """LLMサービス管理クラス"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.model_selector = ModelSelector()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._health_check_interval = 60  # 秒
        self._health_check_task = None
        self._running = False
        
    def register_provider(self, name: str, provider: LLMProvider):
        """プロバイダーを登録"""
        self.providers[name] = provider
        logger.info(f"LLMプロバイダー '{name}' を登録しました")
    
    def unregister_provider(self, name: str):
        """プロバイダーの登録を解除"""
        if name in self.providers:
            del self.providers[name]
            logger.info(f"LLMプロバイダー '{name}' の登録を解除しました")
    
    async def start(self):
        """サービス開始"""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("LLMサービスマネージャーを開始しました")
    
    async def stop(self):
        """サービス停止"""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        self.executor.shutdown(wait=True)
        logger.info("LLMサービスマネージャーを停止しました")
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        統一インターフェースでテキスト生成
        
        Args:
            request: 生成リクエスト
            
        Returns:
            生成レスポンス
        """
        start_time = time.time()
        
        try:
            # モデル選択
            if request.model_name:
                model_name = request.model_name
                provider = self._find_provider_for_model(model_name)
            else:
                # 自動選択（将来的にはcapabilityベースで選択）
                provider, model_name = self._select_best_provider_and_model()
            
            if not provider:
                return GenerationResponse(
                    text="",
                    model_name=request.model_name or "unknown",
                    generation_time=time.time() - start_time,
                    token_count=0,
                    finish_reason="error",
                    error="利用可能なプロバイダーが見つかりません"
                )
            
            # リクエストにモデル名を設定
            request.model_name = model_name
            
            # 生成実行
            response = await provider.generate(request)
            
            return response
            
        except Exception as e:
            logger.error(f"テキスト生成中にエラーが発生しました: {e}")
            return GenerationResponse(
                text="",
                model_name=request.model_name or "unknown",
                generation_time=time.time() - start_time,
                token_count=0,
                finish_reason="error",
                error=str(e)
            )
    
    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """ストリーミングテキスト生成"""
        try:
            # モデル選択（generate()と同じロジック）
            if request.model_name:
                provider = self._find_provider_for_model(request.model_name)
            else:
                provider, model_name = self._select_best_provider_and_model()
                request.model_name = model_name
            
            if not provider:
                yield "エラー: 利用可能なプロバイダーが見つかりません"
                return
            
            # ストリーミング生成
            async for chunk in provider.generate_stream(request):
                yield chunk
                
        except Exception as e:
            logger.error(f"ストリーミング生成中にエラーが発生しました: {e}")
            yield f"エラー: {str(e)}"
    
    def list_all_models(self) -> List[ModelInfo]:
        """全プロバイダーの利用可能なモデル一覧"""
        all_models = []
        for provider in self.providers.values():
            models = provider.list_models()
            all_models.extend(models)
        return all_models
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """モデル情報取得"""
        for provider in self.providers.values():
            model_info = provider.get_model_info(model_name)
            if model_info:
                return model_info
        return None
    
    async def get_service_status(self) -> Dict[str, Any]:
        """サービス状態取得"""
        status = {
            "providers": {},
            "total_models": 0,
            "available_models": 0,
            "service_healthy": True
        }
        
        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.is_healthy()
                models = provider.list_models()
                available_models = [m for m in models if m.is_available]
                
                status["providers"][name] = {
                    "healthy": is_healthy,
                    "total_models": len(models),
                    "available_models": len(available_models),
                    "models": [m.name for m in available_models]
                }
                
                status["total_models"] += len(models)
                status["available_models"] += len(available_models)
                
                if not is_healthy:
                    status["service_healthy"] = False
                    
            except Exception as e:
                logger.error(f"プロバイダー '{name}' の状態チェックでエラー: {e}")
                status["providers"][name] = {
                    "healthy": False,
                    "error": str(e)
                }
                status["service_healthy"] = False
        
        return status
    
    def _find_provider_for_model(self, model_name: str) -> Optional[LLMProvider]:
        """指定されたモデルを提供するプロバイダーを検索"""
        for provider in self.providers.values():
            if provider.get_model_info(model_name):
                return provider
        return None
    
    def _select_best_provider_and_model(self) -> tuple[Optional[LLMProvider], Optional[str]]:
        """最適なプロバイダーとモデルを選択"""
        for provider in self.providers.values():
            models = provider.list_models()
            available_models = [m for m in models if m.is_available]
            if available_models:
                # パフォーマンススコアが最も高いモデルを選択
                best_model = max(available_models, key=lambda m: m.performance_score)
                return provider, best_model.name
        return None, None
    
    async def _health_check_loop(self):
        """定期的なヘルスチェック"""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                if not self._running:
                    break
                    
                for name, provider in self.providers.items():
                    try:
                        is_healthy = await provider.is_healthy()
                        if not is_healthy:
                            logger.warning(f"プロバイダー '{name}' がヘルスチェックに失敗しました")
                    except Exception as e:
                        logger.error(f"プロバイダー '{name}' のヘルスチェックでエラー: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"ヘルスチェックループでエラー: {e}")

    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """指定されたプロバイダーを取得"""
        return self.providers.get(provider_name)

# シングルトンインスタンス
llm_service = LLMServiceManager()
