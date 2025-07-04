"""
Ollamaプロバイダー実装 - OSSモデルを統一インターフェースで提供（セッション管理最適化版）

このモジュールは、Ollama APIを通じてOSSモデルへのアクセスを提供します。
DeepSeek, Llama, Mistral, CodeLlama等の無料モデルをサポートします。
"""

import asyncio
import aiohttp
import logging
import time
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
    max_delay: float = 10.0
    backoff_multiplier: float = 2.0
    timeout_multiplier: float = 1.5

class OllamaProvider(LLMProvider):
    """Ollama API統合プロバイダー（セッション管理最適化版）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60, model_config: Optional[Dict[str, Any]] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.model_config = model_config or self._load_oss_model_config()
        self._models_cache: Optional[List[ModelInfo]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5分間のキャッシュ
        self._actual_models_cache: Optional[List[str]] = None
        
        # リトライ設定
        self.retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            timeout_multiplier=1.5
        )
        
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
    
    def _load_oss_model_config(self) -> Dict[str, Any]:
        """OSS モデル設定ファイルの読み込み"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "ollama_models.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"OSS model config loading failed: {e}")
        return {}
    
    async def _make_request_with_retry(self, method: str, endpoint: str, session: Optional[aiohttp.ClientSession] = None, **kwargs) -> aiohttp.ClientResponse:
        """リトライ機能付きHTTPリクエストメソッド（セッション管理最適化）"""
        last_exception = None
        delay = self.retry_config.initial_delay
        close_session = session is None
        
        if session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            session = aiohttp.ClientSession(timeout=timeout)
        
        try:
            for attempt in range(self.retry_config.max_retries + 1):
                try:
                    url = f"{self.base_url}{endpoint}"
                    timeout_multiplier = self.retry_config.timeout_multiplier ** attempt
                    adjusted_timeout = min(self.timeout * timeout_multiplier, 300)  # 最大5分
                    
                    # セッションのタイムアウトを更新
                    session._timeout = aiohttp.ClientTimeout(total=adjusted_timeout)
                    
                    logger.debug(f"HTTP Request attempt {attempt + 1}/{self.retry_config.max_retries + 1}: {method} {url}")
                    
                    async with session.request(method, url, **kwargs) as response:
                        if response.status < 500:  # 4xx, 2xxは成功とみなす
                            # レスポンスの内容を読み取って新しいレスポンスオブジェクトを作成
                            content = await response.read()
                            headers = response.headers
                            status = response.status
                            
                            # 簡易的なレスポンスラッパー
                            class ResponseWrapper:
                                def __init__(self, content, headers, status):
                                    self._content = content
                                    self.headers = headers
                                    self.status = status
                                
                                async def text(self):
                                    return self._content.decode('utf-8')
                                
                                async def json(self):
                                    return json.loads(await self.text())
                                
                                async def read(self):
                                    return self._content
                            
                            return ResponseWrapper(content, headers, status)
                        
                        if attempt == self.retry_config.max_retries:
                            response.raise_for_status()
                        
                        logger.warning(f"Server error {response.status}, retrying in {delay}s...")
                        
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_exception = e
                    if attempt == self.retry_config.max_retries:
                        logger.error(f"Request failed after {self.retry_config.max_retries + 1} attempts: {e}")
                        raise
                    
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                
                # 指数バックオフでリトライ待機
                if attempt < self.retry_config.max_retries:
                    await asyncio.sleep(delay)
                    delay = min(delay * self.retry_config.backoff_multiplier, self.retry_config.max_delay)
            
            # 最後の例外を再発生
            if last_exception:
                raise last_exception
                
        finally:
            if close_session:
                await session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """統一されたHTTPリクエストメソッド（リトライ機能付き）"""
        return await self._make_request_with_retry(method, endpoint, **kwargs)
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """テキスト生成（リトライ機能付きセッション管理）"""
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
            
            # リトライ機能付きAPI呼び出し
            async with aiohttp.ClientSession() as session:
                response = await self._make_request_with_retry(
                    method="POST",
                    endpoint="/api/generate",                    session=session,
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
        """ストリーミングテキスト生成（リトライ機能付きセッション管理）"""
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
            
            # ストリーミング用の直接リクエスト（ResponseWrapperを回避）
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.base_url}/api/generate", json=data) as response:
                    
                    if response.status != 200:
                        yield f"[ERROR] API エラー: {response.status}"
                        return
                    
                    # ストリーミングレスポンスの処理
                    async for line in response.content:
                        if line:
                            try:
                                line_str = line.decode('utf-8').strip()
                                if line_str:
                                    response_data = json.loads(line_str)
                                    if "response" in response_data:
                                        yield response_data["response"]
                                    if response_data.get("done", False):
                                        break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"ストリーミング生成エラー: {e}")
            yield f"[ERROR] {str(e)}"
    
    def list_models(self) -> List[ModelInfo]:
        """利用可能なモデル一覧"""
        return list(self._model_definitions.values())
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """モデル情報取得"""
        return self._model_definitions.get(model_name)
    
    async def is_healthy(self) -> bool:
        """ヘルスチェック（リトライ機能付き）"""
        try:
            response = await self._make_request("GET", "/api/tags")
            return response.status == 200
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """実際に利用可能なモデル名の取得（キャッシュ機能付き）"""
        # キャッシュの確認
        if (self._actual_models_cache is not None and 
            self._cache_time is not None and 
            time.time() - self._cache_time < self._cache_ttl):
            return self._actual_models_cache
        
        try:
            response = await self._make_request("GET", "/api/tags")
            
            if response.status != 200:
                logger.warning(f"モデル一覧取得失敗: ステータス {response.status}")
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
        models = await self.get_available_models()
        
        if not models:
            return None
          # 設定から該当モデルのパターンを取得
        model_info = self.model_config.get(config_name, {})
        patterns = model_info.get("patterns", [config_name])
        
        # パターンマッチング（生成可能なモデルのみ）
        for pattern in patterns:
            for actual_model in models:
                # 埋め込み専用モデルは除外
                if "embed" in actual_model.lower():
                    continue
                if pattern.lower() in actual_model.lower():
                    return actual_model
        
        return None

    async def _select_best_model(self) -> Optional[str]:
        """最適なモデルを自動選択（設定ファイルの優先度を考慮）"""
        # 実際のモデル一覧を取得
        models = await self.get_available_models()
        
        if not models:
            return None
        
        # 生成可能なモデルのみをフィルタリング
        generation_models = [m for m in models if "embed" not in m.lower()]
        
        # 設定ファイルの優先度順にモデルを探す
        models_config = self.model_config.get("models", self.model_config)
        enabled_models = []
        for config_name, config in models_config.items():
            if config.get("enabled", True):
                enabled_models.append((config_name, config.get("priority", 999)))
        
        # 優先度順にソート
        enabled_models.sort(key=lambda x: x[1])
        
        # 優先度順に実際のモデルを探す
        for config_name, _ in enabled_models:
            actual_model = await self._find_actual_model_name(config_name)
            if actual_model and actual_model in generation_models:
                logger.info(f"選択されたモデル: {config_name} -> {actual_model}")
                return actual_model
        
        # 設定にないモデルの場合、生成可能な最初のモデルを使用
        if generation_models:
            # deepseek-coder, codellama, mistral, llama2 の順に優先
            preferred_order = ["deepseek-coder", "codellama", "mistral", "llama2"]
            for preferred in preferred_order:
                for model in generation_models:
                    if preferred in model.lower():
                        logger.info(f"推奨モデルを使用: {model}")
                        return model
            
            # それでも見つからない場合は最初の生成可能モデルを使用
            logger.warning(f"設定にないモデルを使用: {generation_models[0]}")
            return generation_models[0]
        
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
