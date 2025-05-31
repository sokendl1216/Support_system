# services/program_generator/base.py

import os
import re
import json
import tempfile
import shutil
import zipfile
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from data.models.job import JobInput, JobOutput, JobTemplate, GenerationRequest, GenerationResult
from ai.prompts.integrated_prompt_service import IntegratedPromptService, PromptMode
from ai.rag.stub_rag_system import StubRAGSystem
from ai.llm_utils import generate_text

logger = logging.getLogger(__name__)


class BaseProgramGenerator(ABC):
    """プログラム生成サービスの基底クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # テスト用のスタブRAGSystemを使用
        stub_rag_system = StubRAGSystem()
        self.prompt_service = IntegratedPromptService(stub_rag_system)
        self.templates_dir = "services/program_generator/templates"
        self.output_dir = "temp/generated"
        self.supported_languages = ["python", "javascript", "html", "css"]
        
        # 出力ディレクトリの作成
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"初期化完了: {self.__class__.__name__}")
    
    @abstractmethod
    async def validate_input(self, job_input: JobInput) -> bool:
        """
        入力データのバリデーション
        
        Args:
            job_input: 仕事入力データ
            
        Returns:
            bool: バリデーション結果
        """
        pass
    
    @abstractmethod
    async def generate(self, job_input: JobInput) -> JobOutput:
        """
        プログラム生成のメイン処理
        
        Args:
            job_input: 仕事入力データ
            
        Returns:
            JobOutput: 生成結果
        """
        pass
    
    async def generate_with_ai(
        self, 
        job_input: JobInput, 
        template_id: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> GenerationResult:
        """
        AIを使用したコード生成
        
        Args:
            job_input: 仕事入力データ
            template_id: 使用するテンプレートID
            custom_prompt: カスタムプロンプト
            
        Returns:
            GenerationResult: 生成結果
        """
        try:
            start_time = datetime.now()
            
            # プロンプトモードの決定
            mode = self._get_prompt_mode(job_input.mode)
            
            # プロンプト生成
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt_result = await self.prompt_service.generate_prompt(
                    query=self._build_generation_query(job_input),
                    mode=mode,
                    variables=self._extract_template_variables(job_input),
                    use_rag=True
                )
                prompt = prompt_result.prompt
            
            # AI生成実行
            logger.info(f"AI生成開始: {job_input.job_type}")
            generated_content = await generate_text(
                prompt=prompt,
                temperature=0.3,  # コード生成では低めの温度
                max_tokens=3000
            )
            
            # コード抽出
            extracted_code = self._extract_code_from_response(generated_content)
            
            # 生成時間計算
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GenerationResult(
                success=True,
                content=extracted_code,
                content_type=self._determine_content_type(job_input),
                generation_time=generation_time,
                template_used=template_id,
                metadata={
                    "prompt_length": len(prompt),
                    "response_length": len(generated_content),
                    "extracted_code_length": len(extracted_code)
                }
            )
            
        except Exception as e:
            logger.error(f"AI生成エラー: {e}")
            return GenerationResult(
                success=False,
                error_message=str(e),
                generation_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _get_prompt_mode(self, mode: str) -> PromptMode:
        """進行モードからプロンプトモードを決定"""
        mode_mapping = {
            "auto": PromptMode.AUTONOMOUS,
            "interactive": PromptMode.INTERACTIVE,
            "hybrid": PromptMode.HYBRID
        }
        return mode_mapping.get(mode, PromptMode.INTERACTIVE)
    
    def _build_generation_query(self, job_input: JobInput) -> str:
        """生成クエリを構築"""
        parameters = job_input.parameters
        
        query = f"{job_input.job_type}のプログラムを生成してください。"
        
        # パラメータから要件を抽出
        requirements = []
        for key, value in parameters.items():
            if value:
                requirements.append(f"{key}: {value}")
        
        if requirements:
            query += f"\n要件:\n" + "\n".join(f"- {req}" for req in requirements)
        
        return query
    
    def _extract_template_variables(self, job_input: JobInput) -> Dict[str, Any]:
        """テンプレート変数を抽出"""
        variables = {
            "job_type": job_input.job_type,
            "mode": job_input.mode,
            **job_input.parameters
        }
        return variables
    
    def _determine_content_type(self, job_input: JobInput) -> str:
        """コンテンツタイプを決定"""
        job_type = job_input.job_type.lower()
        
        if "python" in job_type or "data" in job_type or "analysis" in job_type:
            return "python"
        elif "web" in job_type or "html" in job_type:
            return "html"
        elif "javascript" in job_type or "js" in job_type:
            return "javascript"
        else:
            return "python"  # デフォルト
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        AIの応答からコード部分を抽出
        
        Args:
            response: AIの応答テキスト
            
        Returns:
            str: 抽出されたコード
        """
        # コードブロックパターンを試行
        patterns = [
            r'```(?:python|py)\n(.*?)\n```',
            r'```(?:javascript|js)\n(.*?)\n```',
            r'```(?:html)\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'```(.*?)```'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return matches[0].strip()
        
        # コードブロックが見つからない場合、全体を返す
        logger.warning("コードブロックが見つかりませんでした。応答全体を返します。")
        return response.strip()
    
    def load_template(self, template_name: str) -> Optional[str]:
        """
        テンプレートファイルを読み込み
        
        Args:
            template_name: テンプレートファイル名
            
        Returns:
            str: テンプレート内容
        """
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"テンプレートファイルが見つかりません: {template_path}")
                return None
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {e}")
            return None
    
    def fill_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        テンプレートに変数を埋め込み
        
        Args:
            template: テンプレート文字列
            variables: 変数辞書
            
        Returns:
            str: 埋め込み後の文字列
        """
        try:
            # {{variable}} 形式の置換
            for key, value in variables.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            
            return template
        except Exception as e:
            logger.error(f"テンプレート埋め込みエラー: {e}")
            return template
    
    def create_project_files(
        self, 
        code: str, 
        job_input: JobInput,
        additional_files: Optional[Dict[str, str]] = None
    ) -> str:
        """
        プロジェクトファイルを作成
        
        Args:
            code: 生成されたコード
            job_input: 仕事入力データ
            additional_files: 追加ファイル
            
        Returns:
            str: 生成したファイルのディレクトリパス
        """
        try:
            # 一時ディレクトリの作成
            project_dir = tempfile.mkdtemp(prefix="generated_project_")
            
            # メインファイルの作成
            content_type = self._determine_content_type(job_input)
            main_filename = self._get_main_filename(job_input.job_type, content_type)
            
            with open(os.path.join(project_dir, main_filename), 'w', encoding='utf-8') as f:
                f.write(code)
            
            # README.mdの作成
            readme_content = self._generate_readme(job_input, main_filename)
            with open(os.path.join(project_dir, "README.md"), 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # requirements.txtの作成（Pythonの場合）
            if content_type == "python":
                requirements = self._extract_requirements(code)
                if requirements:
                    with open(os.path.join(project_dir, "requirements.txt"), 'w', encoding='utf-8') as f:
                        f.write("\n".join(requirements))
            
            # 追加ファイルの作成
            if additional_files:
                for filename, content in additional_files.items():
                    with open(os.path.join(project_dir, filename), 'w', encoding='utf-8') as f:
                        f.write(content)
            
            logger.info(f"プロジェクトファイル作成完了: {project_dir}")
            return project_dir
            
        except Exception as e:
            logger.error(f"プロジェクトファイル作成エラー: {e}")
            raise
    
    def _get_main_filename(self, job_type: str, content_type: str) -> str:
        """メインファイル名を生成"""
        base_name = job_type.replace("program_", "").replace("_", "_")
        
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "html": ".html"
        }
        
        return f"{base_name}{extensions.get(content_type, '.py')}"
    
    def _generate_readme(self, job_input: JobInput, main_filename: str) -> str:
        """README.mdを生成"""
        job_name = job_input.parameters.get("name", job_input.job_type)
        
        readme = f"""# {job_name}

## 概要
このプログラムは{job_name}を実現するために生成されました。

## ファイル構成
- `{main_filename}`: メインプログラム
- `README.md`: このファイル

## 実行方法
```bash
python {main_filename}
```

## 要件
- Python 3.7以上（Pythonの場合）
- 必要なライブラリ（requirements.txtを参照）

## 注意事項
このプログラムはAIによって自動生成されました。
実際の使用前に内容を確認し、必要に応じて修正してください。

## 作成日時
{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
"""
        return readme
    
    def _extract_requirements(self, code: str) -> List[str]:
        """コードから必要なライブラリを抽出"""
        import_pattern = r'^(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(import_pattern, code, re.MULTILINE)
        
        # 標準ライブラリを除外
        standard_libs = {
            'os', 'sys', 'json', 'csv', 're', 'math', 'datetime', 'time', 
            'random', 'collections', 'itertools', 'functools', 'operator'
        }
        
        requirements = []
        for lib in set(matches):
            if lib not in standard_libs:
                # よく使われるライブラリのバージョン指定
                version_map = {
                    'numpy': 'numpy>=1.20.0',
                    'pandas': 'pandas>=1.3.0',
                    'matplotlib': 'matplotlib>=3.5.0',
                    'seaborn': 'seaborn>=0.11.0',
                    'scikit': 'scikit-learn>=1.0.0',
                    'sklearn': 'scikit-learn>=1.0.0',
                    'tensorflow': 'tensorflow>=2.8.0',
                    'torch': 'torch>=1.10.0',
                    'cv2': 'opencv-python>=4.5.0',
                    'PIL': 'Pillow>=8.0.0',
                    'requests': 'requests>=2.25.0'
                }
                requirements.append(version_map.get(lib, lib))
        
        return sorted(requirements)
    
    def create_zip_file(self, project_dir: str) -> str:
        """
        プロジェクトディレクトリをZIPファイルに圧縮
        
        Args:
            project_dir: プロジェクトディレクトリパス
            
        Returns:
            str: ZIPファイルパス
        """
        try:
            zip_path = f"{project_dir}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, project_dir)
                        zipf.write(file_path, arc_name)
            
            logger.info(f"ZIPファイル作成完了: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"ZIPファイル作成エラー: {e}")
            raise
    
    def create_preview_html(self, code: str, job_input: JobInput) -> str:
        """
        プレビュー用HTMLを生成
        
        Args:
            code: 生成されたコード
            job_input: 仕事入力データ
            
        Returns:
            str: プレビューHTML
        """
        job_name = job_input.parameters.get("name", job_input.job_type)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{job_name} - プレビュー</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }}
                .preview-container {{ max-width: 1000px; margin: 0 auto; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .code-preview {{ background: #f4f4f4; padding: 15px; border-radius: 8px; margin: 20px 0; overflow-x: auto; }}
                .code-preview pre {{ margin: 0; white-space: pre-wrap; }}
                .info-section {{ background: #e9ecef; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .download-section {{ text-align: center; margin: 20px 0; }}
                .download-button {{ 
                    background: #007bff; color: white; padding: 12px 24px; 
                    border: none; border-radius: 6px; font-size: 16px; cursor: pointer; 
                }}
                .download-button:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="preview-container">
                <div class="header">
                    <h1>{job_name}</h1>
                    <p>このプログラムはAIによって自動生成されました。</p>
                </div>
                
                <div class="info-section">
                    <h3>生成されたプログラムの概要</h3>
                    <p><strong>プログラムタイプ:</strong> {job_input.job_type}</p>
                    <p><strong>生成日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                    <p><strong>進行モード:</strong> {job_input.mode}</p>
                </div>
                
                <div class="code-preview">
                    <h3>生成されたコード:</h3>
                    <pre><code>{self._escape_html(code)}</code></pre>
                </div>
                
                <div class="info-section">
                    <h3>使用方法:</h3>
                    <ol>
                        <li>ダウンロードボタンからファイルをダウンロードします</li>
                        <li>ZIPファイルを解凍します</li>
                        <li>README.mdファイルの指示に従って実行します</li>
                    </ol>
                </div>
                
                <div class="download-section">
                    <button class="download-button" onclick="downloadFiles()">
                        プロジェクトファイルをダウンロード
                    </button>
                </div>
            </div>
            
            <script>
                function downloadFiles() {{
                    alert('ダウンロード機能は実装中です。');
                }}
            </script>
        </body>
        </html>
        """
        return html
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def cleanup_temp_files(self, paths: List[str]):
        """一時ファイルのクリーンアップ"""
        for path in paths:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
                logger.debug(f"一時ファイル削除: {path}")
            except Exception as e:
                logger.warning(f"一時ファイル削除失敗: {path}, エラー: {e}")
    
    def _load_template_from_json(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        JSONテンプレートファイルからテンプレートを読み込み
        
        Args:
            template_id: テンプレートID
            
        Returns:
            Dict[str, Any]: テンプレートデータ、見つからない場合はNone
        """
        try:
            # 言語固有のテンプレートファイルパスを決定
            template_filename = f"{self.language}_templates.json"
            template_path = os.path.join(
                os.path.dirname(__file__), 
                "templates", 
                template_filename
            )
            
            if not os.path.exists(template_path):
                logger.warning(f"テンプレートファイルが見つかりません: {template_path}")
                return None
                
            with open(template_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                
            if template_id in templates:
                return templates[template_id]
            else:
                logger.warning(f"テンプレートID '{template_id}' が見つかりません")
                return None
                
        except Exception as e:
            logger.error(f"JSONテンプレート読み込みエラー: {e}")
            return None
    
    async def _call_ai_for_generation(self, generation_request: Dict[str, Any]) -> str:
        """AI呼び出しでコード生成（スタブ実装）"""
        # 現在はスタブ実装として、テンプレートベースの簡単な生成を行う
        template_content = generation_request.get('template_content', '')
        description = generation_request.get('description', '')
        
        if template_content:
            # テンプレート変数を置換
            variables = generation_request.get('variables', {})
            result = template_content
            for key, value in variables.items():
                result = result.replace(f"${{{key}}}", str(value))
            return result
        else:
            # デフォルトの簡単なコード生成
            language = generation_request.get('language', 'python')
            if language == 'python':
                return f'''#!/usr/bin/env python3
"""
{description}
"""

def main():
    print("Hello, World!");
    console.log("Generated program: {description}");
}}

main();
'''
            elif language == 'javascript':
                return f'''// {description}

function main() {{
    console.log("Hello, World!");
    console.log("Generated program: {description}");
}}

main();
'''
            elif language == 'web':
                return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description}</title>
</head>
<body>
    <h1>{description}</h1>
    <p>Generated web page</p>
</body>
</html>
'''
            else:
                return f"// Generated code for {description}"
    
    async def _extract_code_from_response_async(self, response: str) -> str:
        """
        AI応答からコード部分を抽出（非同期版）
        """
        return self._extract_code_from_response(response)
    
    async def _create_project_files(self, job_input: JobInput, code: str) -> List[Dict[str, Any]]:
        """
        プロジェクトファイル作成（基底実装）
        継承クラスでオーバーライドする
        """
        files = []
        project_type = job_input.parameters.get('project_type', 'script')
        language = self._determine_content_type(job_input)
        
        # メインファイル
        main_filename = self._get_main_filename(job_input.job_type, language)
        files.append({
            'filename': main_filename,
            'content': code,
            'type': language,
            'line_count': len(code.split('\n'))
        })
        
        # README.md
        readme_content = self._generate_readme(job_input, main_filename)
        files.append({
            'filename': 'README.md',
            'content': readme_content,
            'type': 'markdown',
            'line_count': len(readme_content.split('\n'))
        })
        
        return files
    
    async def _create_zip_package(self, job_id: str, project_files: List[Dict[str, Any]]) -> str:
        """
        プロジェクトファイルからZIPパッケージを作成
        """
        try:
            # 一時ディレクトリ作成
            temp_dir = tempfile.mkdtemp(prefix=f"project_{job_id}_")
            
            # ファイル作成
            for file_info in project_files:
                filename = file_info['filename']
                content = file_info['content']
                
                # サブディレクトリの場合はディレクトリを作成
                file_path = os.path.join(temp_dir, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # ZIP作成
            zip_path = self.create_zip_file(temp_dir)
            
            # 一時ディレクトリクリーンアップ
            shutil.rmtree(temp_dir)
            
            return zip_path
            
        except Exception as e:
            logger.error(f"ZIPパッケージ作成エラー: {str(e)}")
            raise
    
    async def _generate_html_preview(self, project_files: List[Dict[str, Any]], language: str) -> str:
        """
        プロジェクトファイルからHTMLプレビューを生成
        """
        try:
            main_file = None
            for file_info in project_files:
                if file_info['filename'].endswith(('.py', '.js', '.html')):
                    main_file = file_info
                    break
            
            if not main_file:
                return "<p>プレビューできるファイルがありません。</p>"
            
            content = main_file['content']
            filename = main_file['filename']
            
            # HTMLとして直接表示可能な場合
            if filename.endswith('.html'):
                return content
            
            # コードとして表示
            return f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Preview - {filename}</title>
    <style>
        body {{ font-family: monospace; margin: 20px; }}
        .code {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .filename {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="filename">{filename}</div>
    <pre class="code">{self._escape_html(content)}</pre>
</body>
</html>
'''
        except Exception as e:
            logger.error(f"HTMLプレビュー生成エラー: {str(e)}")
            return f"<p>プレビュー生成エラー: {str(e)}</p>"
