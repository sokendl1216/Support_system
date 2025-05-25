# AI推論およびビジネスロジック検証テスト
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.llm_oss_client import OSSLLMClient
from ai.orchestrator import AgentOrchestrator

def test_oss_llm_client_initialize():
    """OSSLLMClientの初期化テスト"""
    client = OSSLLMClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "llama2"
    
def test_oss_llm_client_custom_config():
    """OSSLLMClientの設定カスタマイズテスト"""
    client = OSSLLMClient(base_url="http://localhost:8080", model="mistral")
    assert client.base_url == "http://localhost:8080"
    assert client.model == "mistral"

def test_oss_llm_client_generate_with_unavailable_model():
    """Ollamaが利用できない場合のエラーハンドリング確認"""
    client = OSSLLMClient()
    prompt = "Pythonで九九の表を作るプログラム"
    result = client.generate(prompt)
      # Ollamaサーバーが利用できない場合の適切なエラーメッセージが返されることを確認
    assert any(keyword in result for keyword in [
        "[Ollama Unavailable]", 
        "[Model Unavailable]", 
        "[Connection Error]",
        "[Error]",
        "利用可能なプロバイダーが見つかりません"
    ]), f"Expected error message not found in result: {result}"
    assert prompt in result  # プロンプトが結果に含まれていることを確認

@pytest.mark.parametrize("prompt,error_check_keywords", [
    ("Pythonで九九の表を作るプログラム", ["[", "Pythonで九九の表を作るプログラム"]),
    ("HTMLで自己紹介ページを作る", ["[", "HTMLで自己紹介ページを作る"])
])
def test_llm_oss_client_generate_error_handling(prompt, error_check_keywords):
    """OSSLLMClientのエラーハンドリング確認（パラメータ化テスト）"""
    client = OSSLLMClient()
    result = client.generate(prompt)
    
    # エラーハンドリングによる適切なレスポンス形式が返されることを確認
    for kw in error_check_keywords:
        assert kw in result, f"'{kw}' not in result: {result}"

def test_llm_oss_client_model_availability_check():
    """モデル利用可能性チェック機能の確認"""
    client = OSSLLMClient()
    
    # Ollamaサーバーが利用できない場合はFalseが返される
    is_available = client._is_ollama_available()
    assert isinstance(is_available, bool)
    
    # モデル利用可能性チェック
    is_model_available = client._is_model_available()
    assert isinstance(is_model_available, bool)
    
    # 利用可能モデル一覧取得
    models = client.list_available_models()
    assert isinstance(models, list)

def test_agent_orchestrator_mode_switch():
    """AgentOrchestratorのモード切り替えテスト"""
    orchestrator = AgentOrchestrator()
    
    # 初期モード確認
    assert orchestrator.current_mode == "default"
    
    # モード切り替えテスト
    orchestrator.set_mode("creative")
    assert orchestrator.current_mode == "creative"
    
    orchestrator.set_mode("analytical")
    assert orchestrator.current_mode == "analytical"

def test_agent_orchestrator_process_request():
    """AgentOrchestratorのリクエスト処理テスト"""
    orchestrator = AgentOrchestrator()
    
    # creativeモードに設定
    orchestrator.set_mode("creative")
    
    # テスト用のリクエスト
    test_request = "Pythonでフィボナッチ数列を計算する関数を作って"
    result = orchestrator.process_request(test_request)
    
    # 結果がスタイルが適用された形で返されることを確認
    assert "[creative mode]" in result
    assert test_request in result

# 統合テスト
def test_integration_orchestrator_with_oss_client():
    """AgentOrchestratorとOSSLLMClientの統合テスト"""
    client = OSSLLMClient()
    orchestrator = AgentOrchestrator()
    
    # リクエスト処理
    test_request = "Webアプリケーションの設計について教えて"
    orchestrated_result = orchestrator.process_request(test_request)
    
    # クライアント経由での生成も確認
    client_result = client.generate(test_request)
    
    # 両方とも適切にレスポンスが返されることを確認
    assert isinstance(orchestrated_result, str)
    assert isinstance(client_result, str)
    assert len(orchestrated_result) > 0
    assert len(client_result) > 0
