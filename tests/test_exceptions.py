"""
例外処理モジュールのテスト
"""
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exceptions import AppException, ValidationError, NotFoundError

@pytest.mark.unit
@pytest.mark.core
def test_app_exception():
    """AppExceptionのテスト"""
    # 基本的な例外生成
    ex = AppException("テストエラー")
    assert str(ex) == "テストエラー"
    
    # 継承関係の確認
    assert issubclass(AppException, Exception)
    assert isinstance(AppException("エラー"), Exception)

@pytest.mark.unit
@pytest.mark.core
def test_validation_error():
    """ValidationErrorのテスト"""
    # 基本的な例外生成
    ex = ValidationError("検証エラー")
    assert str(ex) == "検証エラー"
    
    # 継承関係の確認
    assert issubclass(ValidationError, AppException)
    assert issubclass(ValidationError, Exception)
    assert isinstance(ValidationError("エラー"), AppException)
    
    # 追加データを含む例外
    ex_with_data = ValidationError("フィールドエラー", fields=["name", "email"])
    assert "フィールドエラー" in str(ex_with_data)
    assert hasattr(ex_with_data, "fields")
    assert ex_with_data.fields == ["name", "email"]

@pytest.mark.unit
@pytest.mark.core
def test_not_found_error():
    """NotFoundErrorのテスト"""
    # 基本的な例外生成
    ex = NotFoundError("リソースが見つかりません")
    assert str(ex) == "リソースが見つかりません"
    
    # 継承関係の確認
    assert issubclass(NotFoundError, AppException)
    assert issubclass(NotFoundError, Exception)
    assert isinstance(NotFoundError("エラー"), AppException)
    
    # リソース情報を含む例外
    ex_with_resource = NotFoundError("ユーザーが見つかりません", resource_id=123)
    assert "ユーザーが見つかりません" in str(ex_with_resource)
    assert hasattr(ex_with_resource, "resource_id")
    assert ex_with_resource.resource_id == 123

@pytest.mark.unit
@pytest.mark.core
def test_exception_handling():
    """例外ハンドリングのテスト"""
    # try-exceptでキャッチできることを確認
    try:
        raise ValidationError("フォーム検証エラー")
        assert False, "例外が発生していない"
    except ValidationError as e:
        assert str(e) == "フォーム検証エラー"
    
    # 継承関係による例外キャッチ
    try:
        raise ValidationError("フォーム検証エラー")
        assert False, "例外が発生していない"
    except AppException as e:
        assert isinstance(e, ValidationError)
    
    # 特定の例外以外をキャッチ
    try:
        raise NotFoundError("データが見つかりません")
    except ValidationError:
        assert False, "ValidationErrorで捕捉されるべきではない"
    except NotFoundError:
        pass  # 期待通り
