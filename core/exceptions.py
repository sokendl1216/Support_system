# core/exceptions.py

class AppException(Exception):
    """アプリケーション共通例外"""
    pass

class ValidationError(AppException):
    """バリデーションエラー"""
    pass

class NotFoundError(AppException):
    """リソース未検出エラー"""
    pass
