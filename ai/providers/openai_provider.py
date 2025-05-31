"""
OpenAIプロバイダー実装 - ChatGPTモデルを統一インターフェースで提供（セッション管理最適化版）

このモジュールは、OpenAI APIを通じてChatGPTモデルへのアクセスを提供します。
GPT-4o、GPT-4、GPT-3.5-turbo等のモデルをサポートします。
"""

import asyncio
import aiohttp
import logging
import time
import os
from typing import Optional, Dict, List, Any, AsyncGenerator
import json
from dataclasses import dataclass
from pathlib import Path

from ai.llm_service import (
    LLMProvider, ModelInfo, ModelType, ModelCapability,
    GenerationRequest, GenerationResponse, GenerationConfig
)

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    timeout_multiplier: float = 1.5

class OpenAIProvider(LLMProvider):
    """OpenAI API統合プロバイダー（セッション管理最適化版）"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.openai.com/v1", timeout: int = 60, model_config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.model_config = model_config or {}
        self._models_cache: Optional[List[ModelInfo]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5分間のキャッシュ
        
        # リトライ設定
        self.retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            timeout_multiplier=1.5
        )
        
        # OpenAIモデルの定義
        self._model_definitions = {
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                display_name="GPT-4o",
                model_type=ModelType.GENERAL,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.SUMMARIZATION,
                    ModelCapability.TRANSLATION
                ],
                max_tokens=4096,
                context_length=128000,
                parameter_size="Unknown",
                memory_requirement="Cloud",
                description="OpenAIの最新高性能マルチモーダルモデル"
            ),
            "gpt-4": ModelInfo(
                name="gpt-4",
                display_name="GPT-4",
                model_type=ModelType.GENERAL,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.SUMMARIZATION,
                    ModelCapability.TRANSLATION
                ],
                max_tokens=4096,
                context_length=8192,
                parameter_size="Unknown",
                memory_requirement="Cloud",
                description="OpenAIの高性能大規模言語モデル"
            ),
            "gpt-4-turbo": ModelInfo(
                name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                model_type=ModelType.GENERAL,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.SUMMARIZATION,
                    ModelCapability.TRANSLATION
                ],
                max_tokens=4096,
                context_length=128000,
                parameter_size="Unknown",
                memory_requirement="Cloud",
                description="GPT-4の高速・長コンテキスト版"
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                model_type=ModelType.GENERAL,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.SUMMARIZATION
                ],
                max_tokens=4096,
                context_length=16385,
                parameter_size="Unknown",
                memory_requirement="Cloud",
                description="高速で効率的なGPTモデル"
            )
        }
        
        if not self.api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    async def _make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        session: aiohttp.ClientSession,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """リトライ機能付きHTTPリクエスト"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        kwargs.setdefault("headers", {}).update(headers)
        
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # タイムアウトの動的調整
                current_timeout = min(
                    self.timeout * (self.retry_config.timeout_multiplier ** attempt),
                    300  # 最大5分
                )
                
                timeout = aiohttp.ClientTimeout(total=current_timeout)
                
                async with session.request(method, url, timeout=timeout, **kwargs) as response:
                    # 成功またはクライアントエラー（4xx）の場合はリトライしない
                    if response.status < 500:
                        return response
                    
                    # サーバーエラー（5xx）の場合はリトライ
                    if attempt < self.retry_config.max_retries:
                        logger.warning(f"OpenAI API server error {response.status}, retrying... (attempt {attempt + 1})")
                        continue
                    
                    return response
                    
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self.retry_config.max_retries:
                    delay = min(
                        self.retry_config.initial_delay * (self.retry_config.backoff_multiplier ** attempt),
                        self.retry_config.max_delay
                    )
                    logger.warning(f"OpenAI API timeout, retrying in {delay}s... (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                break
                
            except Exception as e:
                last_exception = e
                if attempt < self.retry_config.max_retries:
                    delay = min(
                        self.retry_config.initial_delay * (self.retry_config.backoff_multiplier ** attempt),
                        self.retry_config.max_delay
                    )
                    logger.warning(f"OpenAI API error: {e}, retrying in {delay}s... (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                break
        
        # すべてのリトライが失敗した場合
        raise last_exception or Exception("All retry attempts failed")
    
    def _load_openai_model_config(self) -> Dict[str, Any]:
        """OpenAIモデル設定の読み込み"""
        config_path = Path("config/openai_models.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"OpenAIモデル設定の読み込みに失敗: {e}")
        return {}
    
    async def _select_best_model(self) -> Optional[str]:
        """設定に基づく最適モデル選択"""
        try:
            # 設定ファイルから優先度順にモデルを選択
            if self.model_config:
                # 優先度順にソート
                models = [(name, config) for name, config in self.model_config.items() 
                         if config.get('enabled', True)]
                models.sort(key=lambda x: x[1].get('priority', 999))
                
                for model_name, model_config in models:
                    if model_name in self._model_definitions:
                        logger.info(f"Selected OpenAI model: {model_name}")
                        return model_name
            
            # デフォルトの優先順序
            default_priority = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            for model_name in default_priority:
                if model_name in self._model_definitions:
                    logger.info(f"Selected default OpenAI model: {model_name}")
                    return model_name
                    
        except Exception as e:
            logger.error(f"モデル選択エラー: {e}")
        
        return "gpt-3.5-turbo"  # フォールバック
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """テキスト生成（リトライ機能付きセッション管理）"""
        start_time = time.time()
        
        try:
            if not self.api_key:
                return GenerationResponse(
                    text="",
                    model_name="unknown",
                    generation_time=0.0,
                    token_count=0,
                    finish_reason="error",
                    error="OpenAI API key not configured"
                )
            
            # モデル名の決定
            model_name = request.model_name or await self._select_best_model()
            
            if not model_name:
                return GenerationResponse(
                    text="",
                    model_name="unknown",
                    generation_time=0.0,
                    token_count=0,
                    finish_reason="error",
                    error="利用可能なモデルがありません"
                )
            
            # ChatCompletion形式のリクエストデータ構築
            data = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "stream": False,
                **self._build_options(request.config)
            }
            
            # リトライ機能付きAPI呼び出し
            async with aiohttp.ClientSession() as session:
                response = await self._make_request_with_retry(
                    method="POST",
                    endpoint="/chat/completions",
                    session=session,
                    json=data
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    return GenerationResponse(
                        text="",
                        model_name=model_name,
                        generation_time=time.time() - start_time,
                        token_count=0,
                        finish_reason="error",
                        error=f"OpenAI API エラー: {response.status} - {error_text}"
                    )
                
                result = await response.json()
                
                # レスポンス解析
                if "choices" not in result or not result["choices"]:
                    return GenerationResponse(
                        text="",
                        model_name=model_name,
                        generation_time=time.time() - start_time,
                        token_count=0,
                        finish_reason="error",
                        error="無効なレスポンス形式"
                    )
                
                choice = result["choices"][0]
                text = choice.get("message", {}).get("content", "")
                finish_reason = choice.get("finish_reason", "stop")
                
                # トークン使用量の取得
                usage = result.get("usage", {})
                token_count = usage.get("total_tokens", self._estimate_token_count(text))
                
                return GenerationResponse(
                    text=text,
                    model_name=model_name,
                    generation_time=time.time() - start_time,
                    token_count=token_count,
                    finish_reason=finish_reason
                )
                    
        except Exception as e:
            logger.error(f"OpenAIテキスト生成エラー: {e}")
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
            if not self.api_key:
                yield ""
                return
            
            # モデル名の決定
            model_name = request.model_name or await self._select_best_model()
            
            if not model_name:
                yield ""
                return
            
            # ストリーミング用リクエストデータ
            data = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "stream": True,
                **self._build_options(request.config)
            }
            
            async with aiohttp.ClientSession() as session:
                response = await self._make_request_with_retry(
                    method="POST",
                    endpoint="/chat/completions",
                    session=session,
                    json=data
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenAI streaming API error: {response.status} - {error_text}")
                    yield ""
                    return
                
                # ストリーミングレスポンスの処理
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 'data: ' を除去
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    yield content
                                    
                        except json.JSONDecodeError:
                            continue  # 無効なJSONをスキップ
                            
        except Exception as e:
            logger.error(f"OpenAIストリーミング生成エラー: {e}")
            yield ""
    
    def list_models(self) -> List[ModelInfo]:
        """利用可能なモデル一覧"""
        if not self.api_key:
            return []
        
        return list(self._model_definitions.values())
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """モデル情報取得"""
        return self._model_definitions.get(model_name)
    
    async def is_healthy(self) -> bool:
        """ヘルスチェック"""
        try:
            if not self.api_key:
                return False
            
            # モデル一覧取得でAPIの生存確認
            async with aiohttp.ClientSession() as session:
                response = await self._make_request_with_retry(
                    method="GET",
                    endpoint="/models",
                    session=session
                )
                
                return response.status == 200
                
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def _build_options(self, config: GenerationConfig) -> Dict[str, Any]:
        """生成オプションの構築"""
        options = {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
        }
        
        if config.stop_sequences:
            options["stop"] = config.stop_sequences
        
        if config.seed is not None:
            options["seed"] = config.seed
        
        return options
    
    def _estimate_token_count(self, text: str) -> int:
        """トークン数の推定"""
        # 簡易的な推定（実際のトークナイザーより粗い）
        return max(1, len(text.split()) * 4 // 3)
