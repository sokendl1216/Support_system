"""
LLMサービス抽象化レイヤーのテスト

統一インターフェースによるOSSモデル活用のテストスイート
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from ai.llm_service import (
    LLMServiceManager, ModelInfo, ModelType, ModelCapability,
    GenerationRequest, GenerationResponse, GenerationConfig
)
from ai.providers.ollama_provider import OllamaProvider
from ai.llm_initializer import LLMServiceInitializer
from ai.llm_utils import LLMServiceClient


class TestLLMService:
    """LLMサービス基本機能のテスト"""
    
    @pytest.fixture
    def llm_service(self):
        """LLMサービスマネージャーのフィクスチャ"""
        return LLMServiceManager()
    
    @pytest.fixture
    def mock_ollama_provider(self):
        """モックOllamaプロバイダー"""
        provider = AsyncMock(spec=OllamaProvider)
        provider.list_models.return_value = [
            ModelInfo(
                name="llama2",
                display_name="Llama 2",
                model_type=ModelType.GENERAL,
                capabilities=[ModelCapability.TEXT_GENERATION],
                max_tokens=4096,
                context_length=4096,
                parameter_size="7B",
                memory_requirement="8GB",
                description="Test model",
                is_available=True,
                performance_score=0.8
            )
        ]
        provider.get_model_info.return_value = provider.list_models.return_value[0]
        provider.is_healthy.return_value = True
        
        async def mock_generate(request):
            return GenerationResponse(
                text="Generated text",
                model_name=request.model_name or "llama2",
                generation_time=0.5,
                token_count=10,
                finish_reason="stop"
            )
        
        provider.generate = mock_generate
        
        async def mock_generate_stream(request):
            for chunk in ["Generated ", "text"]:
                yield chunk
        
        provider.generate_stream = mock_generate_stream
        
        return provider
    
    @pytest.mark.asyncio
    async def test_provider_registration(self, llm_service, mock_ollama_provider):
        """プロバイダー登録のテスト"""
        llm_service.register_provider("test_ollama", mock_ollama_provider)
        
        assert "test_ollama" in llm_service.providers
        assert llm_service.providers["test_ollama"] == mock_ollama_provider
    
    @pytest.mark.asyncio
    async def test_text_generation(self, llm_service, mock_ollama_provider):
        """テキスト生成のテスト"""
        llm_service.register_provider("test_ollama", mock_ollama_provider)
        
        request = GenerationRequest(
            prompt="Test prompt",
            model_name="llama2",
            config=GenerationConfig(temperature=0.7)
        )
        
        response = await llm_service.generate(request)
        
        assert response.text == "Generated text"
        assert response.model_name == "llama2"
        assert response.finish_reason == "stop"
        assert response.error is None
    
    @pytest.mark.asyncio
    async def test_streaming_generation(self, llm_service, mock_ollama_provider):
        """ストリーミング生成のテスト"""
        llm_service.register_provider("test_ollama", mock_ollama_provider)
        
        request = GenerationRequest(
            prompt="Test prompt",
            model_name="llama2"
        )
        
        chunks = []
        async for chunk in llm_service.generate_stream(request):
            chunks.append(chunk)
        
        assert chunks == ["Generated ", "text"]
    
    @pytest.mark.asyncio
    async def test_model_listing(self, llm_service, mock_ollama_provider):
        """モデル一覧取得のテスト"""
        llm_service.register_provider("test_ollama", mock_ollama_provider)
        
        models = llm_service.list_all_models()
        
        assert len(models) == 1
        assert models[0].name == "llama2"
        assert models[0].is_available == True
    
    @pytest.mark.asyncio
    async def test_service_status(self, llm_service, mock_ollama_provider):
        """サービス状態取得のテスト"""
        llm_service.register_provider("test_ollama", mock_ollama_provider)
        
        status = await llm_service.get_service_status()
        
        assert "providers" in status
        assert "test_ollama" in status["providers"]
        assert status["providers"]["test_ollama"]["healthy"] == True
        assert status["service_healthy"] == True


class TestOllamaProvider:
    """Ollamaプロバイダーのテスト"""
    
    @pytest.fixture
    def ollama_provider(self):
        """Ollamaプロバイダーのフィクスチャ"""
        return OllamaProvider(base_url="http://localhost:11434")
    
    def test_model_definitions(self, ollama_provider):
        """モデル定義のテスト"""
        models = ollama_provider.list_models()
        
        # 定義されたモデルが含まれているかチェック
        model_names = [m.name for m in models]
        assert "deepseek-coder" in model_names
        assert "llama2" in model_names
        assert "mistral" in model_names
        assert "codellama" in model_names
        
        # DeepSeek Coderの詳細チェック
        deepseek = ollama_provider.get_model_info("deepseek-coder")
        assert deepseek is not None
        assert deepseek.model_type == ModelType.CODE
        assert ModelCapability.CODE_GENERATION in deepseek.capabilities
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, ollama_provider):
        """ヘルスチェック失敗のテスト"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value.status = 500
            
            is_healthy = await ollama_provider.is_healthy()
            assert is_healthy == False
    
    def test_option_building(self, ollama_provider):
        """生成オプション構築のテスト"""
        config = GenerationConfig(
            temperature=0.8,
            max_tokens=2000,
            top_p=0.95,
            top_k=50
        )
        
        options = ollama_provider._build_options(config)
        
        assert options["temperature"] == 0.8
        assert options["num_predict"] == 2000
        assert options["top_p"] == 0.95
        assert options["top_k"] == 50
    
    def test_token_estimation(self, ollama_provider):
        """トークン数推定のテスト"""
        # 英語テキスト
        english_text = "Hello world"
        tokens = ollama_provider._estimate_token_count(english_text)
        assert tokens == 2  # 11文字 / 4 ≈ 2-3トークン
        
        # 日本語テキスト
        japanese_text = "こんにちは世界"
        tokens = ollama_provider._estimate_token_count(japanese_text)
        assert tokens == 7  # 7文字 = 7トークン
    
    @pytest.mark.asyncio
    async def test_model_selection(self, ollama_provider):
        """モデル自動選択のテスト"""
        with patch.object(ollama_provider, 'get_available_models') as mock_get_models:
            mock_get_models.return_value = ["llama2", "mistral", "deepseek-coder"]
            
            selected = await ollama_provider._select_best_model()
            assert selected == "deepseek-coder"  # 最高優先度


class TestLLMInitializer:
    """LLMサービス初期化のテスト"""
    
    @pytest.fixture
    def test_config(self, tmp_path):
        """テスト用設定ファイル"""
        config_data = {
            "ai": {
                "llm_service": {
                    "health_check_interval": 300,
                    "providers": {
                        "ollama": {
                            "base_url": "http://localhost:11434",
                            "timeout": 30,
                            "models": {
                                "llama2": {"enabled": True, "priority": 1}
                            }
                        }
                    }
                },
                "generation": {
                    "default_temperature": 0.7,
                    "default_max_tokens": 1000
                }
            }
        }
        
        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        return str(config_file)
    
    def test_config_loading(self, test_config):
        """設定ファイル読み込みのテスト"""
        initializer = LLMServiceInitializer(test_config)
        
        success = initializer.load_config()
        assert success == True
        assert "ai" in initializer.config
        assert "llm_service" in initializer.config["ai"]
    
    def test_config_loading_failure(self):
        """設定ファイル読み込み失敗のテスト"""
        initializer = LLMServiceInitializer("nonexistent.json")
        
        success = initializer.load_config()
        assert success == False


class TestLLMServiceClient:
    """LLMサービスクライアントのテスト"""
    
    @pytest.fixture
    def llm_client(self):
        """LLMサービスクライアントのフィクスチャ"""
        return LLMServiceClient()
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, llm_client):
        """クライアント初期化のテスト"""
        with patch('ai.llm_utils.initialize_llm_service') as mock_init:
            mock_init.return_value = True
            
            success = await llm_client.initialize()
            assert success == True
            assert llm_client._initialized == True
    
    @pytest.mark.asyncio
    async def test_text_generation_with_client(self, llm_client):
        """クライアント経由でのテキスト生成テスト"""
        # 初期化をモック
        llm_client._initialized = True
        
        # LLMサービスの生成をモック
        mock_response = GenerationResponse(
            text="Generated text",
            model_name="llama2",
            generation_time=0.5,
            token_count=10,
            finish_reason="stop"
        )
        
        with patch('ai.llm_utils.llm_service.generate') as mock_generate:
            mock_generate.return_value = mock_response
            
            result = await llm_client.generate_text("Test prompt")
            assert result == "Generated text"


# 統合テスト
class TestLLMServiceIntegration:
    """LLMサービス統合テスト"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """エンドツーエンドワークフローのテスト"""
        # このテストはOllamaサーバーが実際に動作している場合のみ実行
        pytest.skip("実際のOllamaサーバーが必要なため、手動テスト用")
        
        # 実際の統合テスト例：
        # 1. サービス初期化
        # 2. プロバイダー登録
        # 3. テキスト生成
        # 4. サービス終了


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
