# data/models/job.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseModel


@dataclass
class JobInput(BaseModel):
    """仕事入力データモデル"""
    job_id: str
    job_type: str  # 仕事の種類ID（例: "program_image_classifier"）
    user_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)  # ユーザー入力パラメータ
    mode: str = "interactive"  # 進行モード: "auto", "interactive", "hybrid"
    files: List[Dict[str, Any]] = field(default_factory=list)  # アップロードファイル情報
    metadata: Dict[str, Any] = field(default_factory=dict)  # メタデータ
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class JobOutput(BaseModel):
    """仕事出力データモデル"""
    job_id: str
    job_type: str
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    content: str = ""  # 生成されたコンテンツ（コード、HTML等）
    content_type: str = "text"  # "python", "javascript", "html", "text", "zip"
    preview_html: Optional[str] = None  # プレビュー用HTML
    files: List[Dict[str, Any]] = field(default_factory=list)  # 生成ファイル情報
    download_url: Optional[str] = None  # ダウンロードURL
    metadata: Dict[str, Any] = field(default_factory=dict)  # メタデータ
    error_message: Optional[str] = None  # エラーメッセージ
    generation_time: float = 0.0  # 生成時間（秒）
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = super().to_dict()
        # datetimeオブジェクトをISO形式文字列に変換
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        return result


@dataclass 
class JobTemplate(BaseModel):
    """仕事テンプレートデータモデル"""
    template_id: str
    job_type: str
    name: str
    description: str
    template_content: str  # テンプレートコンテンツ
    variables: List[str] = field(default_factory=list)  # テンプレート変数
    language: str = "python"  # プログラミング言語
    category: str = "general"  # カテゴリ
    tags: List[str] = field(default_factory=list)  # タグ
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GenerationRequest(BaseModel):
    """生成リクエストデータモデル"""
    job_input: JobInput
    template_id: Optional[str] = None
    custom_prompt: Optional[str] = None
    generation_config: Dict[str, Any] = field(default_factory=dict)
    use_rag: bool = True  # RAG検索を使用するか
    context: Dict[str, Any] = field(default_factory=dict)  # 追加コンテキスト


@dataclass
class GenerationResult(BaseModel):
    """生成結果データモデル"""
    success: bool
    content: str = ""
    content_type: str = "text"
    files: List[Dict[str, Any]] = field(default_factory=list)  # 生成ファイル情報
    download_url: Optional[str] = None  # ダウンロードURL
    preview_html: Optional[str] = None  # プレビュー用HTML
    template_used: Optional[str] = None
    generation_time: float = 0.0
    token_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
