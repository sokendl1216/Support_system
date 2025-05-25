# core/exceptions.py

class AppException(Exception):
    """アプリケーション共通例外"""
    def __init__(self, message="アプリケーションエラーが発生しました", *args, **kwargs):
        super().__init__(message, *args)
        self.details = kwargs

class ValidationError(AppException):
    """バリデーションエラー"""
    def __init__(self, message="バリデーションエラーが発生しました", fields=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.fields = fields or []

class NotFoundError(AppException):
    """リソース未検出エラー"""
    def __init__(self, message="リソースが見つかりません", resource_id=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.resource_id = resource_id
