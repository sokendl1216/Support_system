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
        # ダミーLLMクライアントとエージェントのテスト実装
        class DummyLLM(LLMClient):
            def generate(self, prompt: str) -> str:
                return "dummy-response"
        class DummyAgent(BaseAgent):
            def run(self, input_data):
                return "dummy-agent-result"
        llm = DummyLLM()
        agent = DummyAgent()
        orchestrator = AgentOrchestrator([agent])
        assert llm.generate("test") == "dummy-response"
        assert agent.run("test") == "dummy-agent-result"
        assert orchestrator.run_all("test") == ["dummy-agent-result"]
        print("ai.agent_base/LLMClient/AgentOrchestrator: OK")
    except Exception as e:
        print("ai.agent_base/LLMClient/AgentOrchestrator: NG", e)
        traceback.print_exc()

if __name__ == "__main__":
    test_core()
    test_data()
    test_services()
    test_api()
    test_ui()
    test_ai()
    print("全層の基本import・初期化テスト完了")
