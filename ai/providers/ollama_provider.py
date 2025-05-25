"""
Ollamaプロバイダー実装 - OSSモデルを統一インターフェースで提供

このモジュールは、Ollama APIを通じてOSSモデルへのアクセスを提供します。
DeepSeek, Llama, Mistral, CodeLlama等の無料モデルをサポートします。
"""

import asyncio
import aiohttp
import logging
import time
from typing import Optional, Dict, List, Any, AsyncGenerator
import json

from ai.llm_service import (
    LLMProvider, ModelInfo, ModelType, ModelCapability,
    GenerationRequest, GenerationResponse, GenerationConfig
)

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Ollama API統合プロバイダー"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30, model_config: Optional[Dict[str, Any]] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.model_config = model_config or {}
        self._models_cache: Optional[List[ModelInfo]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5分間のキャッシュ
        self._actual_models_cache: Optional[List[str]] = None
        
        # OSSモデルの定義
        self._model_definitions = {
            "deepseek-coder": ModelInfo(
                name="deepseek-coder",
                display_name="DeepSeek Coder",
                model_type=ModelType.CODE,
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_ANSWERING
                ],
                max_tokens=4096,
                context_length=16384,
                parameter_size="6.7B",
                memory_requirement="8GB",
                description="コード生成に特化した高性能OSSモデル"
            ),
            "llama2": ModelInfo(
                name="llama2",
                display_name="Llama 2",
                model_type=ModelType.GENERAL,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.SUMMARIZATION
                ],
                max_tokens=4096,
                context_length=8192,
                parameter_size="7B",
                memory_requirement="6GB",
                description="Metaの汎用LLMモデル"
            ),
            "mistral": ModelInfo(
                name="mistral",
                display_name="Mistral",
                model_type=ModelType.GENERAL,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_ANSWERING
                ],
                max_tokens=4096,
                context_length=8192,
                parameter_size="7B",
                memory_requirement="6GB",
                description="高性能でコンパクトなフランス製LLM"
            ),
            "codellama": ModelInfo(
                name="codellama",
                display_name="Code Llama",
                model_type=ModelType.CODE,
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.TEXT_GENERATION
                ],
                max_tokens=4096,
                context_length=16384,
                parameter_size="7B",
                memory_requirement="8GB",
                description="Metaのコード生成特化モデル"
            )
        }
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """テキスト生成"""
        start_time = time.time()
        
        try:
            # モデル名の決定
            if request.model_name:
                # 指定されたモデル名から実際のモデル名を検索
                actual_model = await self._find_actual_model_name(request.model_name)
                model_name = actual_model or request.model_name
            else:
                # 自動選択
                model_name = await self._select_best_model()
            
            if not model_name:
                return GenerationResponse(
                    text="",
                    model_name="unknown",
                    generation_time=0.0,
                    token_count=0,
                    finish_reason="error",
                    error="利用可能なモデルがありません"
                )
            
            # リクエストデータの構築
            data = {
                "model": model_name,
                "prompt": request.prompt,
                "stream": False,
                "options": self._build_options(request.config)
            }
            
            # API呼び出し
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return GenerationResponse(
                            text="",
                            model_name=model_name,
                            generation_time=time.time() - start_time,
                            token_count=0,
                            finish_reason="error",
                            error=f"API エラー: {response.status} - {error_text}"
                        )
                    
                    result = await response.json()
                    text = result.get("response", "")
                    
                    return GenerationResponse(
                        text=text,
                        model_name=model_name,
                        generation_time=time.time() - start_time,
                        token_count=self._estimate_token_count(text),
                        finish_reason="stop"
                    )
                    
        except Exception as e:
            logger.error(f"テキスト生成エラー: {e}")
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
            # モデル名の決定
            if request.model_name:
                # 指定されたモデル名から実際のモデル名を検索
                actual_model = await self._find_actual_model_name(request.model_name)
                model_name = actual_model or request.model_name
            else:
                # 自動選択
                model_name = await self._select_best_model()
            
            if not model_name:
                yield "[ERROR] 利用可能なモデルがありません"
                return
            
            data = {
                "model": model_name,
                "prompt": request.prompt,
                "stream": True,
                "options": self._build_options(request.config)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        yield f"[ERROR] API エラー: {response.status}"
                        return
                    
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            yield f"[ERROR] {str(e)}"
    
    def list_models(self) -> List[ModelInfo]:
        """利用可能なモデル一覧"""
        return list(self._model_definitions.values())
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """モデル情報取得"""
        return self._model_definitions.get(model_name)
    
    async def is_healthy(self) -> bool:
        """ヘルスチェック"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    async def get_available_models(self) -> List[str]:
        """実際に利用可能なモデル名の取得（キャッシュ機能付き）"""
        # キャッシュの確認
        if (self._actual_models_cache is not None and 
            self._cache_time is not None and 
            time.time() - self._cache_time < self._cache_ttl):
            return self._actual_models_cache
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status != 200:
                        return []
                    
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    
                    # キャッシュに保存
                    self._actual_models_cache = models
                    self._cache_time = time.time()
                    
                    return models
                    
        except Exception as e:
            logger.error(f"モデル一覧取得エラー: {e}")
            return []
    
    async def _find_actual_model_name(self, config_name: str) -> Optional[str]:
        """設定ファイルのモデル名から実際のOllamaモデル名を検索"""
        # まず利用可能なモデルを取得
        await self.get_available_models()
        
        if not self._actual_models_cache:
            return None
        
        # 設定から該当モデルのパターンを取得
        model_info = self.model_config.get(config_name, {})
        patterns = model_info.get("patterns", [config_name])
        
        # パターンマッチング
        for pattern in patterns:
            for actual_model in self._actual_models_cache:
                if pattern.lower() in actual_model.lower():
                    return actual_model
        
        return None

    async def _select_best_model(self) -> Optional[str]:
        """最適なモデルを自動選択（設定ファイルの優先度を考慮）"""
        # 実際のモデル一覧を取得
        await self.get_available_models()
        
        if not self._actual_models_cache:
            return None
        
        # 設定ファイルの優先度順にモデルを探す
        enabled_models = []
        for config_name, config in self.model_config.items():
            if config.get("enabled", True):
                enabled_models.append((config_name, config.get("priority", 999)))
        
        # 優先度順にソート
        enabled_models.sort(key=lambda x: x[1])
        
        # 優先度順に実際のモデルを探す
        for config_name, _ in enabled_models:
            actual_model = await self._find_actual_model_name(config_name)
            if actual_model:
                logger.info(f"選択されたモデル: {config_name} -> {actual_model}")
                return actual_model
        
        # 設定にないモデルの場合、利用可能な最初のモデルを使用
        if self._actual_models_cache:
            logger.warning(f"設定にないモデルを使用: {self._actual_models_cache[0]}")
            return self._actual_models_cache[0]
        
        return None
    
    def _build_options(self, config: GenerationConfig) -> Dict[str, Any]:
        """生成オプションの構築"""
        return {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "num_predict": config.max_tokens,
            "stop": config.stop_sequences,
            "seed": config.seed
        }
    
    def _estimate_token_count(self, text: str) -> int:
        """トークン数の概算（簡易実装）"""
        # 簡易的な推定：英語は4文字=1トークン、日本語は1文字=1トークン程度
        english_chars = sum(1 for c in text if ord(c) < 128)
        japanese_chars = len(text) - english_chars
        return int(english_chars / 4 + japanese_chars)
