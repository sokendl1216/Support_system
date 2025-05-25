"""
LLMサービス初期化モジュール

設定ファイルからLLMサービスを初期化し、プロバイダーを登録します。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from .llm_service import llm_service, GenerationConfig
from .providers import OllamaProvider

logger = logging.getLogger(__name__)

class LLMServiceInitializer:
    """LLMサービス初期化クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
    
    def load_config(self) -> bool:
        """設定ファイル読み込み"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"設定ファイルが見つかりません: {self.config_path}")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                # JSONCファイル（コメント付きJSON）を読み込むため、
                # 簡易的にコメント行を除去
                content = f.read()
                lines = content.split('\n')
                filtered_lines = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped.startswith('//'):
                        filtered_lines.append(line)
                clean_content = '\n'.join(filtered_lines)
                
                self.config = json.loads(clean_content)
                logger.info(f"設定ファイルを読み込みました: {self.config_path}")
                return True
                
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return False
    
    async def initialize_llm_service(self) -> bool:
        """LLMサービスの初期化"""
        try:
            if not self.config:
                logger.error("設定が読み込まれていません")
                return False
            
            ai_config = self.config.get("ai", {})
            llm_config = ai_config.get("llm_service", {})
            
            # ヘルスチェック間隔の設定
            health_check_interval = llm_config.get("health_check_interval", 300)
            llm_service._health_check_interval = health_check_interval
            
            # プロバイダーの初期化と登録
            providers_config = llm_config.get("providers", {})
              # Ollamaプロバイダーの初期化
            if "ollama" in providers_config:
                ollama_config = providers_config["ollama"]
                models_config = ollama_config.get("models", {})
                
                ollama_provider = OllamaProvider(
                    base_url=ollama_config.get("base_url", "http://localhost:11434"),
                    timeout=ollama_config.get("timeout", 30),
                    model_config=models_config
                )
                
                # モデル優先度の設定
                await self._configure_ollama_models(ollama_provider, models_config)
                
                llm_service.register_provider("ollama", ollama_provider)
                logger.info("Ollamaプロバイダーを登録しました")
            
            # デフォルト生成設定の適用
            generation_config = ai_config.get("generation", {})
            llm_service._default_config = GenerationConfig(
                temperature=generation_config.get("default_temperature", 0.7),
                max_tokens=generation_config.get("default_max_tokens", 1000),
                top_p=generation_config.get("default_top_p", 0.9),
                top_k=generation_config.get("default_top_k", 40)
            )
            
            # サービス開始
            await llm_service.start()
            logger.info("LLMサービスを開始しました")
            return True
            
        except Exception as e:
            logger.error(f"LLMサービス初期化エラー: {e}")
            return False
    
    async def _configure_ollama_models(self, provider: OllamaProvider, models_config: Dict[str, Any]):
        """Ollamaモデルの設定"""
        try:
            # 利用可能なモデルを取得
            available_models = await provider.get_available_models()
            logger.info(f"利用可能なOllamaモデル: {available_models}")
            
            # 設定されたモデルの優先度に基づいてパフォーマンススコアを設定
            for model_name, model_config in models_config.items():
                if model_config.get("enabled", True):
                    model_info = provider.get_model_info(model_name)
                    if model_info:
                        # 優先度から性能スコアを計算（優先度が低い数値ほど高スコア）
                        priority = model_config.get("priority", 10)
                        model_info.performance_score = 1.0 - (priority - 1) * 0.1
                        
                        # 実際に利用可能かチェック
                        model_info.is_available = any(
                            model_name in available for available in available_models
                        )
                        
                        logger.info(f"モデル設定: {model_name} - 優先度: {priority}, "
                                  f"利用可能: {model_info.is_available}")
            
        except Exception as e:
            logger.error(f"Ollamaモデル設定エラー: {e}")

# グローバル初期化インスタンス
llm_initializer = LLMServiceInitializer()

async def initialize_llm_service(config_path: str = "config.json") -> bool:
    """LLMサービスの初期化（簡易インターフェース）"""
    global llm_initializer
    llm_initializer = LLMServiceInitializer(config_path)
    
    if not llm_initializer.load_config():
        return False
    
    return await llm_initializer.initialize_llm_service()

async def shutdown_llm_service():
    """LLMサービスの終了"""
    await llm_service.stop()
    logger.info("LLMサービスを終了しました")
