"""
Python プログラムジェネレーター

Python言語に特化したプログラム生成機能を提供します。
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from data.models.job import JobInput, GenerationResult
from services.program_generator.base import BaseProgramGenerator

logger = logging.getLogger(__name__)


class PythonGenerator(BaseProgramGenerator):
    """
    Python プログラムジェネレーター
    
    Python言語に特化したコード生成機能を提供します。
    ライブラリ依存関係の自動検出、requirements.txt生成、
    適切なプロジェクト構造の作成などを行います。
    """
    
    def __init__(self):
        super().__init__()
        self.language = 'python'
        self.file_extension = '.py'
        
    async def validate_input(self, job_input: JobInput) -> bool:
        """Python固有の入力検証"""
        try:
            await super().validate_input(job_input)
            
            # Python固有の検証ロジック
            parameters = job_input.parameters
            
            # プロジェクトタイプの確認
            project_type = parameters.get('project_type', 'script')
            valid_types = [
                'script', 'cli', 'web_app', 'data_analysis', 
                'machine_learning', 'api', 'desktop_app', 'game'
            ]
            
            if project_type not in valid_types:
                logger.warning(f"未知のプロジェクトタイプ: {project_type}, 'script'を使用")
                parameters['project_type'] = 'script'
            
            return True
            
        except Exception as e:
            logger.error(f"Python入力検証エラー: {str(e)}")
            return False
    
    async def generate(self, job_input: JobInput) -> GenerationResult:
        """Python プログラム生成のメイン処理"""
        try:
            if not await self.validate_input(job_input):
                return GenerationResult(
                    success=False,
                    error_message="入力検証エラー"
                )
            
            logger.info(f"Python生成開始: {job_input.job_id}")
            
            # 生成リクエストの準備
            generation_request = await self._prepare_generation_request(job_input)
              # AI呼び出しでコード生成
            ai_response = await self._call_ai_for_generation(generation_request)
            
            # コード抽出と処理
            extracted_code = self._extract_code_from_response(ai_response)
            
            # プロジェクトファイル作成
            project_files = await self._create_project_files(job_input, extracted_code)
            
            # ZIPパッケージ作成
            zip_path = await self._create_zip_package(job_input.job_id, project_files)
            
            # HTMLプレビュー生成
            preview_html = await self._generate_html_preview(project_files, 'python')
            
            # 要件抽出
            requirements = await self._extract_python_requirements(extracted_code)
            
            result = GenerationResult(
                success=True,
                content=extracted_code,
                files=project_files,
                download_url=zip_path,
                preview_html=preview_html,
                metadata={
                    'language': 'python',
                    'project_type': job_input.parameters.get('project_type', 'script'),
                    'requirements': requirements,
                    'file_count': len(project_files),
                    'template_used': self._get_template_name(job_input)
                }
            )
            
            logger.info(f"Python生成完了: {job_input.job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Python生成エラー: {job_input.job_id}, エラー: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=f"Python生成エラー: {str(e)}"
            )
    
    async def _prepare_generation_request(self, job_input: JobInput) -> Dict[str, Any]:
        """Python生成用のリクエストを準備"""
        parameters = job_input.parameters
        project_type = parameters.get('project_type', 'script')
        description = parameters.get('description', '')
        
        # プロジェクトタイプ別のテンプレート選択
        template_name = self._get_template_name(job_input)
        template_content = await self._load_template(template_name)
        
        # プロンプト構築
        prompt_context = {
            'description': description,
            'project_type': project_type,
            'language': 'Python',
            'requirements': parameters.get('requirements', []),
            'features': parameters.get('features', []),
            'complexity': parameters.get('complexity', 'medium'),
            'template': template_content,
            'guidelines': self._get_python_guidelines()
        }
        
        return {
            'prompt_template': 'python_generation',
            'context': prompt_context,
            'max_tokens': 8000,
            'temperature': 0.7
        }
    
    def _get_template_name(self, job_input: JobInput) -> str:
        """プロジェクトタイプに基づいてテンプレート名を決定"""
        project_type = job_input.parameters.get('project_type', 'script')
        
        template_mapping = {
            'script': 'python_script',
            'cli': 'python_cli',
            'web_app': 'python_flask',
            'data_analysis': 'python_data_analysis',
            'machine_learning': 'python_ml',
            'api': 'python_fastapi',
            'desktop_app': 'python_tkinter',
            'game': 'python_pygame'
        }
        
        return template_mapping.get(project_type, 'python_script')
    
    def _get_python_guidelines(self) -> List[str]:
        """Python コーディングガイドライン"""
        return [
            "PEP 8に準拠したコードスタイルを使用してください",
            "適切なdocstringを関数やクラスに記載してください",
            "型ヒントを積極的に使用してください",
            "エラーハンドリングを適切に実装してください",
            "必要に応じてloggingを使用してください",
            "セキュリティを考慮した実装を行ってください",
            "テストしやすい構造で実装してください",
            "requirements.txtに必要なパッケージを記載してください",
            "README.mdに使用方法を記載してください"
        ]
    
    async def _extract_python_requirements(self, code: str) -> List[str]:
        """Pythonコードから必要なライブラリを抽出"""
        try:
            requirements = []
            
            # import文の正規表現パターン
            import_patterns = [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
            ]
            
            # 標準ライブラリは除外
            stdlib_modules = {
                'os', 'sys', 'json', 'time', 'datetime', 'math', 'random',
                'collections', 'itertools', 'functools', 'operator',
                're', 'string', 'pathlib', 'logging', 'configparser',
                'argparse', 'subprocess', 'threading', 'multiprocessing',
                'urllib', 'http', 'email', 'base64', 'hashlib', 'hmac',
                'sqlite3', 'csv', 'xml', 'html', 'unicodedata'
            }
            
            for pattern in import_patterns:
                matches = re.findall(pattern, code)
                for match in matches:
                    module_name = match.split('.')[0]  # パッケージ名のみ取得
                    if module_name not in stdlib_modules:
                        if module_name not in requirements:
                            requirements.append(module_name)
            
            # 一般的なパッケージの推奨バージョン
            version_mapping = {
                'flask': 'flask>=2.0.0',
                'fastapi': 'fastapi>=0.68.0',
                'requests': 'requests>=2.25.0',
                'numpy': 'numpy>=1.21.0',
                'pandas': 'pandas>=1.3.0',
                'matplotlib': 'matplotlib>=3.4.0',
                'seaborn': 'seaborn>=0.11.0',
                'scikit-learn': 'scikit-learn>=1.0.0',
                'tensorflow': 'tensorflow>=2.6.0',
                'torch': 'torch>=1.9.0',
                'django': 'django>=3.2.0',
                'sqlalchemy': 'sqlalchemy>=1.4.0',
                'pytest': 'pytest>=6.2.0',
                'click': 'click>=8.0.0',
                'pydantic': 'pydantic>=1.8.0'
            }
            
            # バージョン付きrequirementsを生成
            versioned_requirements = []
            for req in requirements:
                if req in version_mapping:
                    versioned_requirements.append(version_mapping[req])
                else:
                    versioned_requirements.append(req)
            
            return sorted(versioned_requirements)
            
        except Exception as e:
            logger.error(f"requirements抽出エラー: {str(e)}")
            return []
    
    async def _create_project_files(self, job_input: JobInput, code: str) -> List[Dict[str, Any]]:
        """Pythonプロジェクトファイルを作成"""
        try:
            files = []
            project_type = job_input.parameters.get('project_type', 'script')
            requirements = await self._extract_python_requirements(code)
            
            # メインコードファイル
            main_filename = self._get_main_filename(project_type)
            files.append({
                'filename': main_filename,
                'content': code,
                'type': 'python',
                'line_count': len(code.split('\n'))
            })
            
            # requirements.txt
            if requirements:
                files.append({
                    'filename': 'requirements.txt',
                    'content': '\n'.join(requirements),
                    'type': 'text',
                    'line_count': len(requirements)
                })
            
            # README.md
            readme_content = await self._generate_readme(job_input, requirements)
            files.append({
                'filename': 'README.md',
                'content': readme_content,
                'type': 'markdown',
                'line_count': len(readme_content.split('\n'))
            })
            
            # プロジェクトタイプ別の追加ファイル
            additional_files = await self._create_additional_files(job_input, project_type)
            files.extend(additional_files)
            
            return files
            
        except Exception as e:
            logger.error(f"プロジェクトファイル作成エラー: {str(e)}")
            return []
    
    def _get_main_filename(self, project_type: str) -> str:
        """プロジェクトタイプに応じたメインファイル名を取得"""
        filename_mapping = {
            'script': 'main.py',
            'cli': 'cli.py',
            'web_app': 'app.py',
            'data_analysis': 'analysis.py',
            'machine_learning': 'model.py',
            'api': 'main.py',
            'desktop_app': 'gui.py',
            'game': 'game.py'
        }
        return filename_mapping.get(project_type, 'main.py')
    
    async def _generate_readme(self, job_input: JobInput, requirements: List[str]) -> str:
        """README.md を生成"""
        description = job_input.parameters.get('description', '')
        project_type = job_input.parameters.get('project_type', 'script')
        main_filename = self._get_main_filename(project_type)
        
        readme_content = f"""# {job_input.job_id or 'Python Project'}

## 概要
{description}

## 必要要件
- Python 3.8以上

## インストール

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. 仮想環境の作成
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

### 3. 依存関係のインストール
"""
        
        if requirements:
            readme_content += """```bash
pip install -r requirements.txt
```
"""
        else:
            readme_content += "追加の依存関係は必要ありません。\n"
        
        readme_content += f"""
## 使用方法
```bash
python {main_filename}
```

## プロジェクト構造
```
.
├── {main_filename}          # メインプログラム
├── README.md               # このファイル
"""
        
        if requirements:
            readme_content += "├── requirements.txt       # 依存関係\n"
        
        readme_content += """└── ...
```

## 注意事項
- プログラムを実行する前に仮想環境を有効化してください
- 必要に応じて設定ファイルを編集してください

## ライセンス
MIT License
"""
        
        return readme_content
    
    async def _create_additional_files(self, job_input: JobInput, project_type: str) -> List[Dict[str, Any]]:
        """プロジェクトタイプに応じた追加ファイルを作成"""
        files = []
        
        try:
            if project_type == 'cli':
                # CLI用の設定ファイル
                files.append({
                    'filename': 'config.ini',
                    'content': '[settings]\ndebug = false\nlog_level = INFO\n',
                    'type': 'ini',
                    'line_count': 3
                })
                
            elif project_type == 'web_app':
                # Webアプリ用の設定
                files.append({
                    'filename': 'config.py',
                    'content': '''import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
''',
                    'type': 'python',
                    'line_count': 5
                })
                
            elif project_type == 'api':
                # API用のDockerfile
                files.append({
                    'filename': 'Dockerfile',
                    'content': '''FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
''',
                    'type': 'dockerfile',
                    'line_count': 10
                })
            
            # 共通のgitignore
            files.append({
                'filename': '.gitignore',
                'content': '''__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.idea/
.vscode/
*.log
.env
''',
                'type': 'gitignore',
                'line_count': 15
            })
            
        except Exception as e:
            logger.error(f"追加ファイル作成エラー: {str(e)}")
        
        return files
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """利用可能なPythonテンプレートの一覧を取得"""
        return [
            {
                'name': 'python_script',
                'display_name': 'Pythonスクリプト',
                'description': '基本的なPythonスクリプト',
                'project_type': 'script'
            },
            {
                'name': 'python_cli',
                'display_name': 'CLIツール',
                'description': 'コマンドライン実行可能なツール',
                'project_type': 'cli'
            },
            {
                'name': 'python_flask',
                'display_name': 'Flask Webアプリ',
                'description': 'FlaskベースのWebアプリケーション',
                'project_type': 'web_app'
            },
            {
                'name': 'python_fastapi',
                'display_name': 'FastAPI',
                'description': 'FastAPIベースのREST API',
                'project_type': 'api'
            },
            {
                'name': 'python_data_analysis',
                'display_name': 'データ分析',
                'description': 'pandas/numpyを使ったデータ分析',
                'project_type': 'data_analysis'
            },
            {
                'name': 'python_ml',
                'display_name': '機械学習',
                'description': 'scikit-learnを使った機械学習',
                'project_type': 'machine_learning'
            }
        ]
    
    async def get_generation_preview(self, job_input: JobInput) -> Dict[str, Any]:
        """生成プレビュー情報を取得"""
        project_type = job_input.parameters.get('project_type', 'script')
        main_filename = self._get_main_filename(project_type)
        
        estimated_files = [main_filename, 'README.md']
        
        # プロジェクトタイプに応じた追加ファイル予測
        if project_type in ['web_app', 'api', 'cli']:
            estimated_files.append('requirements.txt')
            
        if project_type == 'api':
            estimated_files.append('Dockerfile')
            
        estimated_files.append('.gitignore')
        
        return {
            'files': estimated_files,
            'structure': {
                'main_file': main_filename,
                'project_type': project_type,
                'language': 'python'
            },
            'requirements': ['予想される依存関係は実際の生成時に決定されます'],
            'template': self._get_template_name(job_input)
        }
    
    async def _load_template(self, template_name: str) -> Optional[str]:
        """
        JSONテンプレートファイルからテンプレート内容を読み込み
        
        Args:
            template_name: テンプレート名（例: 'python_script', 'python_cli'）
            
        Returns:
            Optional[str]: テンプレート内容、見つからない場合はNone
        """
        try:
            # JSONテンプレートデータを読み込み
            template_data = self._load_template_from_json(template_name)
            
            if template_data and 'template' in template_data:
                logger.info(f"Pythonテンプレート読み込み成功: {template_name}")
                return template_data['template']
            else:
                logger.warning(f"Pythonテンプレートが見つかりません: {template_name}")
                # フォールバック用のデフォルトテンプレート
                return self._get_default_template()
                
        except Exception as e:
            logger.error(f"Pythonテンプレート読み込みエラー: {e}")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """デフォルトのPythonテンプレートを返す"""
        return '''#!/usr/bin/env python3
"""
{description}
"""

import sys
import logging
from typing import Any, Dict, List, Optional

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    メイン処理
    """
    try:
        # ここにメインロジックを実装
        print("Hello, World!")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
