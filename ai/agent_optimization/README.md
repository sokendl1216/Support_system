# AIエージェント最適化システム - 使用ガイド

## 概要

AIエージェント最適化システムは、既存のOllamaベースAIエージェントシステムに高度な最適化機能を追加するシステムです。以下の主要機能を提供します：

- **自律学習エンジン**: エージェントの実行結果から自動学習し、パフォーマンスを向上
- **動的パフォーマンス最適化**: リアルタイムでエージェントの負荷分散と最適化
- **高度なコンテキスト管理**: 長期記憶とコンテキスト継承による知識の蓄積
- **自己診断・修復システム**: 自動エラー検出と回復による高可用性

## クイックスタート

### 1. 基本的な使用方法

```python
import asyncio
from ai.llm_service import LLMServiceManager
from ai.agent_optimization.optimization_system import create_optimized_ai_system
from ai.agent_optimization.config import get_development_config

async def main():
    # LLMサービス設定
    llm_config = {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "llama3.1:8b",
        "timeout": 30
    }
    llm_service = LLMServiceManager(llm_config)
    
    # 最適化システム作成・初期化
    system = await create_optimized_ai_system(llm_service, get_development_config())
    await system.start()
    
    try:
        # セッション作成
        session_id = await system.create_session()
        
        # タスク実行（最適化機能付き）
        result = await system.execute_task(
            session_id=session_id,
            title="テストタスク",
            description="AIエージェントに実行させたいタスク",
            requirements={"task_type": "analysis"},
            use_optimization=True
        )
        
        print(f"実行結果: {result}")
        
        # システムステータス確認
        status = await system.get_system_status()
        print(f"システム状態: {status.status}")
        print(f"最適化スコア: {status.optimization_score:.2f}")
        
    finally:
        await system.stop()
        await system.cleanup()

# 実行
asyncio.run(main())
```

### 2. 設定のカスタマイズ

```python
from ai.agent_optimization.config import OptimizationConfig

# カスタム設定作成
config = OptimizationConfig(
    learning_enabled=True,
    learning_rate=0.1,
    performance_monitoring_enabled=True,
    health_monitoring_enabled=True,
    context_retention_days=7,
    auto_recovery_enabled=True
)

# システム作成
system = await create_optimized_ai_system(llm_service, config)
```

### 3. プリセット設定の使用

```python
from ai.agent_optimization.config import (
    get_development_config,
    get_production_config,
    get_testing_config,
    get_lightweight_config
)

# 開発環境用設定
dev_system = await create_optimized_ai_system(llm_service, get_development_config())

# 本番環境用設定
prod_system = await create_optimized_ai_system(llm_service, get_production_config())
```

## 主要機能の詳細

### 自律学習エンジン

エージェントの実行結果を自動的に学習し、以下の最適化を行います：

- **成功パターンの学習**: 成功したタスクの特徴を学習
- **失敗要因の分析**: 失敗したタスクの原因を分析
- **エージェント選択の最適化**: タスクに最適なエージェントを推奨

```python
# 学習機能の手動実行
if system.learning_engine:
    await system.learning_engine.analyze_patterns()
    recommendations = await system.learning_engine.get_agent_recommendations("分析タスク")
    print(f"推奨エージェント: {recommendations}")
```

### 動的パフォーマンス最適化

リアルタイムでエージェントのパフォーマンスを監視・最適化：

- **負荷分散**: エージェント間の負荷を自動調整
- **応答時間最適化**: レスポンス時間を改善
- **メモリ最適化**: メモリ使用量を最適化
- **専門化**: エージェントの特化分野を発見・強化

```python
# パフォーマンス最適化の手動実行
await system.force_optimization()

# パフォーマンスメトリクス取得
metrics = await system.get_comprehensive_metrics()
print(f"総タスク数: {metrics['system_metrics']['total_tasks_completed']}")
print(f"平均成功率: {metrics['system_metrics']['average_success_rate']:.2f}")
```

### 高度なコンテキスト管理

長期記憶とコンテキスト継承により知識を蓄積：

- **セッション間でのコンテキスト継承**
- **長期記憶への知識蓄積**
- **関連コンテキストの自動検索**
- **古いコンテキストの自動クリーンアップ**

```python
# コンテキスト継承を活用したタスク実行
result1 = await system.execute_task(
    session_id=session_id,
    title="ステップ1",
    description="最初のタスク",
    requirements={"phase": 1}
)

# 前のタスクのコンテキストを継承
result2 = await system.execute_task(
    session_id=session_id,
    title="ステップ2", 
    description="前のタスクの結果を活用するタスク",
    requirements={"phase": 2, "depends_on": "ステップ1"}
)
```

### 自己診断・修復システム

システムの健全性を監視し、問題を自動修復：

- **ヘルスメトリクス監視**
- **問題の自動検出**
- **自動回復アクション**
- **アラート機能**

```python
# システム診断の手動実行
status = await system.get_system_status()
if status.issues:
    print(f"検出された問題: {status.issues}")
    print(f"推奨事項: {status.recommendations}")
```

## 進行モード

3つの進行モードをサポート：

### AUTO モード（全自動）
```python
session_id = await system.create_session(ProgressMode.AUTO)
# エージェントが自律的にタスクを実行
```

### INTERACTIVE モード（対話型）
```python
session_id = await system.create_session(ProgressMode.INTERACTIVE)
# ユーザーとの対話を含むタスク実行
```

### HYBRID モード（ハイブリッド）
```python
session_id = await system.create_session(ProgressMode.HYBRID)
# 状況に応じて自動・対話を切り替え
```

## 監視とメトリクス

### システムステータスの確認

```python
status = await system.get_system_status()
print(f"ステータス: {status.status}")  # healthy, warning, error
print(f"稼働時間: {status.uptime}")
print(f"処理タスク数: {status.total_tasks_processed}")
print(f"最適化スコア: {status.optimization_score}")
```

### 詳細レポートの取得

```python
report = await system.get_comprehensive_report()

# システム全体の統計
print(f"統計: {report['statistics']}")

# エージェント別メトリクス
for agent_id, metrics in report['agent_metrics']['enhanced_metrics'].items():
    print(f"エージェント {agent_id}:")
    print(f"  成功率: {metrics['success_rate']:.2f}")
    print(f"  平均実行時間: {metrics['average_execution_time']:.2f}s")
    print(f"  品質スコア: {metrics['quality_average']:.2f}")
```

## イベントハンドリング

システムイベントに対するカスタムハンドラーを登録：

```python
def on_task_completed(data):
    print(f"タスク完了: {data['task_id']}")

def on_optimization_applied(data):
    print(f"最適化実行: {data['optimization_count']}")

# イベントハンドラー登録
system.add_event_handler("task_completed", on_task_completed)
system.add_event_handler("optimization_forced", on_optimization_applied)
```

## エラーハンドリング

```python
try:
    result = await system.execute_task(
        session_id=session_id,
        title="リスクタスク",
        description="失敗する可能性があるタスク",
        use_optimization=True
    )
except Exception as e:
    print(f"タスク実行エラー: {e}")
    
    # システムの自動回復を確認
    status = await system.get_system_status()
    if status.status == "healthy":
        print("システムは正常に回復しました")
```

## パフォーマンス最適化のベストプラクティス

### 1. 適切な設定選択
- 開発時: `get_development_config()`
- 本番時: `get_production_config()`
- テスト時: `get_testing_config()`
- リソース制限時: `get_lightweight_config()`

### 2. 定期的な最適化
```python
# 定期的な手動最適化
import asyncio

async def periodic_optimization():
    while system.is_running:
        await asyncio.sleep(3600)  # 1時間間隔
        await system.force_optimization()

# バックグラウンドで実行
asyncio.create_task(periodic_optimization())
```

### 3. メトリクス監視
```python
# メトリクス監視ループ
async def monitor_metrics():
    while system.is_running:
        status = await system.get_system_status()
        if status.optimization_score < 0.7:
            print("⚠️ 最適化スコアが低下しています")
            await system.force_optimization()
        
        await asyncio.sleep(300)  # 5分間隔
```

## トラブルシューティング

### 一般的な問題と解決方法

#### 1. システム初期化失敗
```python
# 設定検証
from ai.agent_optimization.config import validate_config

config = get_development_config()
is_valid, errors = validate_config(config)
if not is_valid:
    print(f"設定エラー: {errors}")
```

#### 2. タスク実行エラー
```python
# エラー詳細の確認
try:
    result = await system.execute_task(...)
except Exception as e:
    # エラーログの確認
    report = await system.get_comprehensive_report()
    print(f"システム状態: {report['system_status']}")
```

#### 3. パフォーマンス低下
```python
# メトリクス分析
metrics = await system.get_comprehensive_metrics()
for agent_id, agent_metrics in metrics['enhanced_metrics'].items():
    if agent_metrics['success_rate'] < 0.7:
        print(f"エージェント {agent_id} のパフォーマンス低下")
```

#### 4. メモリ使用量増加
```python
# コンテキストクリーンアップ
if system.context_manager:
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=1)
    await system.context_manager.cleanup_old_contexts(cutoff)
```

## 環境変数設定

システム設定を環境変数で制御可能：

```bash
# 学習機能設定
export AI_OPT_LEARNING_ENABLED=true
export AI_OPT_LEARNING_RATE=0.1

# パフォーマンス監視設定
export AI_OPT_PERF_MONITORING=true
export AI_OPT_PERF_INTERVAL=60

# データベース設定
export AI_OPT_DATABASE_PATH="/path/to/ai_optimization.db"
```

```python
from ai.agent_optimization.config import load_config_from_env, merge_configs

# 環境変数から設定読み込み
env_overrides = load_config_from_env()
base_config = get_production_config()
final_config = merge_configs(base_config, env_overrides)
```

## 統合例

### FastAPI Webアプリケーションとの統合

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
optimization_system = None

class TaskRequest(BaseModel):
    title: str
    description: str
    requirements: dict = {}

@app.on_event("startup")
async def startup():
    global optimization_system
    llm_service = LLMServiceManager({"provider": "ollama", ...})
    optimization_system = await create_optimized_ai_system(llm_service)
    await optimization_system.start()

@app.post("/execute_task")
async def execute_task(request: TaskRequest):
    try:
        session_id = await optimization_system.create_session()
        result = await optimization_system.execute_task(
            session_id=session_id,
            title=request.title,
            description=request.description,
            requirements=request.requirements,
            use_optimization=True
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system_status")
async def get_system_status():
    status = await optimization_system.get_system_status()
    return status.__dict__
```

このガイドを参考に、AIエージェント最適化システムを効果的に活用してください。
