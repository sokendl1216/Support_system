"""
AIモジュール

仕事支援AIシステムのAI関連機能を提供します。

主要コンポーネント:
- LLMサービス抽象化レイヤー: 統一インターフェースによるOSSモデル活用
- エージェントシステム: AIエージェントの基盤クラス
- オーケストレーション: 複数エージェントの連携制御
"""

# LLMサービス関連
from .llm_service import (
    LLMServiceManager,
    ModelInfo,
    ModelType, 
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
    GenerationConfig,
    llm_service
)

from .llm_utils import (
    LLMServiceClient,
    llm_client,
    generate_text,
    generate_stream,
    list_models,
    get_model_info,
    get_service_status,
    generate_text_sync,
    list_models_sync,
    get_service_status_sync
)

from .llm_initializer import (
    LLMServiceInitializer,
    llm_initializer,
    initialize_llm_service,
    shutdown_llm_service
)

# プロバイダー
from .providers import OllamaProvider

# 既存のクライアントとエージェント
from .llm_oss_client import OSSLLMClient, OllamaLLMClient
from .agent_base import Agent, LLMClient

# エージェントオーケストレーション
from .agent_orchestrator import (
    AgentOrchestrator,
    ProgressMode,
    TaskStatus,
    AgentRole,
    Task,
    AgentContext,
    OrchestratorState,
    BaseAgent,
    CoordinatorAgent,
    AnalyzerAgent,
    ExecutorAgent,
    ReviewerAgent
)

from .orchestrator_utils import (
    OrchestratorClient,
    TaskBuilder,
    TaskTemplates,
    create_orchestrator_from_config,
    quick_auto_execution,
    quick_interactive_execution,
    task
)

__all__ = [
    # LLMサービス抽象化レイヤー
    "LLMServiceManager",
    "ModelInfo",
    "ModelType",
    "ModelCapability", 
    "GenerationRequest",
    "GenerationResponse",
    "GenerationConfig",
    "llm_service",
    
    # LLMユーティリティ
    "LLMServiceClient",
    "llm_client",
    "generate_text",
    "generate_stream",
    "list_models",
    "get_model_info",
    "get_service_status",
    "generate_text_sync",
    "list_models_sync",
    "get_service_status_sync",
    
    # 初期化
    "LLMServiceInitializer",
    "llm_initializer",
    "initialize_llm_service",
    "shutdown_llm_service",
    
    # プロバイダー
    "OllamaProvider",
      # 既存クライアント・エージェント
    "OSSLLMClient",
    "OllamaLLMClient",
    "Agent",
    "LLMClient",
    
    # エージェントオーケストレーション
    "AgentOrchestrator",
    "ProgressMode",
    "TaskStatus",
    "AgentRole",
    "Task",
    "AgentContext",
    "OrchestratorState",
    "BaseAgent",
    "CoordinatorAgent",
    "AnalyzerAgent",
    "ExecutorAgent",
    "ReviewerAgent",
    
    # オーケストレーションユーティリティ
    "OrchestratorClient",
    "TaskBuilder",
    "TaskTemplates",
    "create_orchestrator_from_config",
    "quick_auto_execution",
    "quick_interactive_execution",
    "task"
]
