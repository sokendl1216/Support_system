import sys
import traceback

# コア層の動作確認
def test_core():
    from core.app import Application
    app = Application()
    try:
        app.run()
        print("core.app.Application: OK")
    except Exception as e:
        print("core.app.Application: NG", e)
        traceback.print_exc()

# データ層の動作確認
def test_data():
    from data.models.base import BaseModel
    m = BaseModel()
    assert isinstance(m.to_dict(), dict)
    print("data.models.base.BaseModel: OK")
    from data.repositories.base import BaseRepository
    class DummyRepo(BaseRepository):
        def get(self, id):
            return id
        def save(self, obj):
            return True
    repo = DummyRepo(storage=None)
    assert repo.get(1) == 1
    assert repo.save({}) is True
    print("data.repositories.base.BaseRepository: OK")

# サービス層の動作確認
def test_services():
    from services.base import BaseService
    class DummyService(BaseService):
        def execute(self):
            return "ok"
    s = DummyService(repository=None)
    assert s.execute() == "ok"
    print("services.base.BaseService: OK")
    from services.di import DIContainer
    di = DIContainer()
    di.register("test", lambda: 123)
    assert di.resolve("test") == 123
    print("services.di.DIContainer: OK")

# API層の動作確認
def test_api():
    import importlib
    try:
        importlib.import_module("api.main")
        print("api.main: OK (importable)")
    except Exception as e:
        print("api.main: NG", e)
        traceback.print_exc()

# UI層の動作確認（Streamlitアプリのimportのみ）
def test_ui():
    import importlib
    try:
        importlib.import_module("ui.app")
        print("ui.app: OK (importable)")
    except Exception as e:
        print("ui.app: NG", e)
        traceback.print_exc()

# AI層の動作確認
def test_ai():
    try:
        from ai.agent_base import BaseAgent, LLMClient
        from ai.orchestrator import AgentOrchestrator
        from ai.llm_oss_client import OSSLLMClient
        # ダミーLLMクライアントとエージェントのテスト実装
        class DummyAgent(BaseAgent):
            def run(self, input_data):
                return "dummy-agent-result"
        llm = OSSLLMClient()
        agent = DummyAgent()
        orchestrator = AgentOrchestrator([agent])
        # Ollama API統合により、エラーハンドリングメッセージが返されることを確認
        result = llm.generate("test")
        assert any(keyword in result for keyword in ["[Connection Error]", "[Model Unavailable]", "[Ollama Unavailable]"])
        assert agent.run("test") == "dummy-agent-result"
        assert orchestrator.run_all("test") == ["dummy-agent-result"]
        print("ai.agent_base/LLMClient/OSSLLMClient/AgentOrchestrator: OK")
    except Exception as e:
        print("ai.agent_base/LLMClient/OSSLLMClient/AgentOrchestrator: NG", e)
        traceback.print_exc()

def test_llm_oss_client():
    try:
        from ai.llm_oss_client import OSSLLMClient
        client = OSSLLMClient()
        result = client.generate("テストプロンプト")
        # Ollama API統合により、エラーハンドリングメッセージが返されることを確認
        assert any(keyword in result for keyword in ["[Connection Error]", "[Model Unavailable]", "[Ollama Unavailable]"])
        print("ai.llm_oss_client.OSSLLMClient: OK")
    except Exception as e:
        print("ai.llm_oss_client.OSSLLMClient: NG", e)
        traceback.print_exc()

def test_event_bus():
    try:
        from core.events import EventBus, Event, EventPriority, event_bus
        
        # カスタムイベントバスのテスト
        custom_bus = EventBus()
        test_results = []
        
        def test_handler(event):
            test_results.append(event.data)
        
        # ハンドラー登録と発火テスト
        handler_id = custom_bus.on("test_event", test_handler, EventPriority.HIGH)
        assert isinstance(handler_id, str)
        
        emitted_event = custom_bus.emit("test_event", {"message": "test"})
        assert isinstance(emitted_event, Event)
        assert len(test_results) == 1
        assert test_results[0]["message"] == "test"
        
        # グローバルイベントバスのテスト
        global_results = []
        
        def global_handler(event):
            global_results.append("global_handled")
        
        event_bus.on("global_test", global_handler)
        event_bus.emit("global_test", {"global": True})
        assert len(global_results) == 1
        
        print("core.events.EventBus: OK")
    except Exception as e:
        print("core.events.EventBus: NG", e)
        traceback.print_exc()

if __name__ == "__main__":
    test_core()
    test_data()
    test_services()
    test_api()
    test_ui()
    test_ai()
    test_llm_oss_client()
    test_event_bus()
    print("全層の基本import・初期化テスト完了")
