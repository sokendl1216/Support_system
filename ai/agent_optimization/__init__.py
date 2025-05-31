"""
AIエージェント最適化システム

このパッケージは、OllamaベースのAIエージェントシステムに高度な最適化機能を提供します。

主要機能:
- 自律学習エンジン: エージェントの自動学習・改善
- 動的パフォーマンス最適化: リアルタイム負荷分散・最適化
- 高度なコンテキスト管理: 長期記憶・コンテキスト継承
- 自己診断・修復システム: 自動エラー検出・回復

使用例:
    from ai.agent_optimization import create_optimized_ai_system
    from ai.agent_optimization.config import get_development_config
    
    # システム作成・初期化
    system = await create_optimized_ai_system(llm_service, get_development_config())
    await system.start()
    
    # タスク実行
    session_id = await system.create_session()
    result = await system.execute_task(
        session_id=session_id,
        title="テストタスク", 
        description="最適化機能をテストする",
        use_optimization=True
    )
"""

from .optimization_system import (
    AIAgentOptimizationSystem,
    create_optimized_ai_system,
    OptimizationConfig,
    SystemStatus
)

from .config import (
    ConfigurationManager,
    get_development_config,
    get_production_config,
    get_testing_config,
    get_lightweight_config,
    create_default_optimization_config,
    validate_config,
    load_config_from_env
)

from .enhanced_agent_orchestrator import (
    EnhancedAgentOrchestrator,
    EnhancedBaseAgent,
    EnhancedAgentMetrics
)

from .autonomous_learning_engine import (
    AutonomousLearningEngine,
    LearningRecord,
    LearningPattern
)

from .performance_optimizer import (
    PerformanceOptimizer,
    PerformanceMetrics,
    OptimizationStrategy
)

from .context_manager import (
    AdvancedContextManager,
    ContextEntry,
    SessionContext,
    LongTermMemory
)

from .self_diagnostic import (
    SelfDiagnosticSystem,
    HealthMetric,
    DiagnosticIssue,
    RecoveryAction
)

# バージョン情報
__version__ = "1.0.0"
__author__ = "AI Development Team"
__description__ = "Advanced optimization system for AI agents with Ollama"

# パッケージメタデータ
__all__ = [
    # メインシステム
    "AIAgentOptimizationSystem",
    "create_optimized_ai_system",
    "OptimizationConfig",
    "SystemStatus",
    
    # 設定管理
    "ConfigurationManager",
    "get_development_config",
    "get_production_config", 
    "get_testing_config",
    "get_lightweight_config",
    "create_default_optimization_config",
    "validate_config",
    "load_config_from_env",
    
    # 拡張オーケストレーター
    "EnhancedAgentOrchestrator",
    "EnhancedBaseAgent",
    "EnhancedAgentMetrics",
    
    # 自律学習
    "AutonomousLearningEngine",
    "LearningRecord",
    "LearningPattern",
    
    # パフォーマンス最適化
    "PerformanceOptimizer",
    "PerformanceMetrics",
    "OptimizationStrategy",
    
    # コンテキスト管理
    "AdvancedContextManager",
    "ContextEntry",
    "SessionContext",
    "LongTermMemory",
    
    # 自己診断
    "SelfDiagnosticSystem",
    "HealthMetric",
    "DiagnosticIssue",
    "RecoveryAction",
]

# 便利な関数とクラスのエイリアス
create_system = create_optimized_ai_system
DevConfig = get_development_config
ProdConfig = get_production_config
TestConfig = get_testing_config
LiteConfig = get_lightweight_config

# パッケージ初期化時の設定
import logging

# ログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ハンドラーが既に設定されていない場合のみ追加
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.info(f"AI Agent Optimization System v{__version__} initialized")

# 環境チェック
def check_environment():
    """実行環境の基本チェック"""
    import sys
    
    # Python バージョンチェック
    if sys.version_info < (3, 8):
        logger.warning("Python 3.8+ is recommended for optimal performance")
    
    # 必要なライブラリのチェック
    required_packages = ["asyncio", "json", "sqlite3", "dataclasses"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        return False
    
    logger.info("Environment check passed")
    return True

# 初期化時に環境チェック実行
_env_check_passed = check_environment()

def get_package_info():
    """パッケージ情報を取得"""
    return {
        "name": "ai-agent-optimization",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "environment_check_passed": _env_check_passed,
        "available_configs": [
            "development",
            "production", 
            "testing",
            "lightweight"
        ],
        "main_components": [
            "AutonomousLearningEngine",
            "PerformanceOptimizer",
            "AdvancedContextManager",
            "SelfDiagnosticSystem"
        ]
    }

# パッケージ情報表示関数
def show_info():
    """パッケージ情報を表示"""
    info = get_package_info()
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                   AI Agent Optimization System                      ║
║                            v{info['version']}                              ║
╠══════════════════════════════════════════════════════════════════════╣
║ Author: {info['author']:<55} ║
║ Python: {info['python_version']:<55} ║
║ Status: {'✅ Ready' if info['environment_check_passed'] else '❌ Check Failed':<55} ║
╠══════════════════════════════════════════════════════════════════════╣
║ Available Configurations:                                           ║
║   • Development (高頻度監視・学習)                                    ║
║   • Production (保守的・高信頼性)                                      ║
║   • Testing (テスト専用設定)                                          ║
║   • Lightweight (リソース制限環境用)                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║ Main Components:                                                     ║
║   • AutonomousLearningEngine (自律学習)                              ║
║   • PerformanceOptimizer (動的最適化)                                ║
║   • AdvancedContextManager (コンテキスト管理)                        ║
║   • SelfDiagnosticSystem (自己診断・修復)                            ║
╚══════════════════════════════════════════════════════════════════════╝

Quick Start:
    from ai.agent_optimization import create_system, DevConfig
    system = await create_system(llm_service, DevConfig())
    """)

# 初期設定の検証
def validate_installation():
    """インストールの妥当性を検証"""
    try:
        # 基本的なインポートテスト
        from .optimization_system import AIAgentOptimizationSystem
        from .config import get_development_config
        from .autonomous_learning_engine import AutonomousLearningEngine
        from .performance_optimizer import PerformanceOptimizer
        from .context_manager import AdvancedContextManager
        from .self_diagnostic import SelfDiagnosticSystem
        
        logger.info("✅ All components imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        return False

# 便利なショートカット関数
async def quick_start(llm_service, config_type="development"):
    """クイックスタート用の便利関数"""
    config_map = {
        "development": get_development_config,
        "production": get_production_config,
        "testing": get_testing_config,
        "lightweight": get_lightweight_config
    }
    
    if config_type not in config_map:
        raise ValueError(f"Invalid config type: {config_type}. Available: {list(config_map.keys())}")
    
    config = config_map[config_type]()
    system = await create_optimized_ai_system(llm_service, config)
    await system.start()
    
    logger.info(f"🚀 Quick start completed with {config_type} configuration")
    return system

# パッケージ初期化完了ログ
logger.info("🔧 AI Agent Optimization System package loaded successfully")

# 初期検証実行
if not validate_installation():
    logger.warning("⚠️  Installation validation failed - some features may not work properly")
