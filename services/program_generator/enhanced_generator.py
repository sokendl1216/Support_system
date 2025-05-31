"""
Enhanced Program Generator Service - AI統合強化版

プログラム生成サービスにOllamaProvider統合、高度なプロンプト構築、
コード品質検証、自動最適化機能を追加した強化版実装
"""

import asyncio
import logging
import re
import ast
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from core.dependency_injection import injectable
from data.models.job import JobInput, JobOutput, GenerationResult
from ai.providers.ollama_provider import OllamaProvider
from ai.rag.rag_system import RAGSystem
from ai.prompts.prompt_template_manager import PromptTemplateManager
from services.program_generator.base import BaseProgramGenerator

logger = logging.getLogger(__name__)


class CodeQualityMetrics:
    """コード品質メトリクス"""
    
    def __init__(self):
        self.complexity_score = 0.0
        self.readability_score = 0.0
        self.maintainability_score = 0.0
        self.error_probability = 0.0
        self.suggestions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "complexity_score": self.complexity_score,
            "readability_score": self.readability_score,
            "maintainability_score": self.maintainability_score,
            "error_probability": self.error_probability,
            "suggestions": self.suggestions
        }


class EnhancedCodeAnalyzer:
    """強化されたコード解析機能"""
    
    def __init__(self):
        self.language_patterns = {
            'python': {
                'import_pattern': r'^(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'function_pattern': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'class_pattern': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(\:]:',
                'comment_pattern': r'#.*$'
            },
            'javascript': {
                'import_pattern': r'(?:import|require)\s*\(["\']([^"\']+)["\']',
                'function_pattern': r'(?:function\s+([a-zA-Z_][a-zA-Z0-9_]*)|([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:function|\([^)]*\)\s*=>))',
                'class_pattern': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'comment_pattern': r'//.*$|/\*.*?\*/'
            }
        }
    
    async def analyze_code_quality(self, code: str, language: str) -> CodeQualityMetrics:
        """コード品質を詳細分析"""
        metrics = CodeQualityMetrics()
        
        try:
            # 基本メトリクス
            lines = code.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 複雑度スコア計算
            metrics.complexity_score = await self._calculate_complexity(code, language)
            
            # 可読性スコア計算
            metrics.readability_score = await self._calculate_readability(code, language)
            
            # 保守性スコア計算
            metrics.maintainability_score = await self._calculate_maintainability(code, language)
            
            # エラー予測確率
            metrics.error_probability = await self._predict_error_probability(code, language)
            
            # 改善提案生成
            metrics.suggestions = await self._generate_suggestions(code, language, metrics)
            
            logger.info(f"コード品質分析完了: 複雑度={metrics.complexity_score:.2f}, 可読性={metrics.readability_score:.2f}")
            
        except Exception as e:
            logger.error(f"コード品質分析エラー: {e}")
            # デフォルト値を設定
            metrics.complexity_score = 5.0
            metrics.readability_score = 7.0
            metrics.maintainability_score = 6.0
            metrics.error_probability = 0.3
        
        return metrics
    
    async def _calculate_complexity(self, code: str, language: str) -> float:
        """循環的複雑度を計算"""
        try:
            if language == 'python':
                return await self._python_complexity(code)
            elif language == 'javascript':
                return await self._javascript_complexity(code)
            else:
                return await self._generic_complexity(code)
        except Exception:
            return 5.0  # デフォルト値
    
    async def _python_complexity(self, code: str) -> float:
        """Python固有の複雑度計算"""
        try:
            tree = ast.parse(code)
            complexity = 1  # 基本パス
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.Lambda):
                    complexity += 1
            
            return min(complexity, 10.0)
        except:
            return 5.0
    
    async def _javascript_complexity(self, code: str) -> float:
        """JavaScript固有の複雑度計算"""
        complexity = 1
        
        # 制御構造をカウント
        patterns = [
            r'\bif\s*\(',
            r'\bwhile\s*\(',
            r'\bfor\s*\(',
            r'\bswitch\s*\(',
            r'\bcatch\s*\(',
            r'\?\s*.*?\s*:'  # 三項演算子
        ]
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return min(complexity, 10.0)
    
    async def _generic_complexity(self, code: str) -> float:
        """汎用的な複雑度計算"""
        lines = code.split('\n')
        complexity = len([line for line in lines if any(keyword in line for keyword in ['if', 'while', 'for', 'switch', 'case'])])
        return min(complexity + 1, 10.0)
    
    async def _calculate_readability(self, code: str, language: str) -> float:
        """可読性スコアを計算"""
        score = 10.0
        lines = code.split('\n')
        
        # 平均行長チェック
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        if avg_line_length > 120:
            score -= 2.0
        elif avg_line_length > 80:
            score -= 1.0
        
        # コメント率チェック
        comment_lines = 0
        for line in lines:
            if language == 'python' and line.strip().startswith('#'):
                comment_lines += 1
            elif language == 'javascript' and (line.strip().startswith('//') or '/*' in line):
                comment_lines += 1
        
        comment_ratio = comment_lines / max(len(lines), 1)
        if comment_ratio < 0.1:
            score -= 1.5
        
        # ネスト深度チェック
        max_indent = 0
        for line in lines:
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
        
        if max_indent > 20:
            score -= 2.0
        elif max_indent > 12:
            score -= 1.0
        
        return max(score, 0.0)
    
    async def _calculate_maintainability(self, code: str, language: str) -> float:
        """保守性スコアを計算"""
        score = 10.0
        
        # 関数サイズチェック
        if language == 'python':
            functions = re.findall(r'def\s+\w+.*?(?=\ndef|\nclass|\Z)', code, re.DOTALL)
        else:
            functions = re.findall(r'function\s+\w+.*?{.*?}', code, re.DOTALL)
        
        for func in functions:
            func_lines = len(func.split('\n'))
            if func_lines > 50:
                score -= 1.0
            elif func_lines > 30:
                score -= 0.5
        
        # 重複コード検出
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        unique_lines = set(lines)
        duplicate_ratio = 1 - (len(unique_lines) / max(len(lines), 1))
        
        if duplicate_ratio > 0.3:
            score -= 2.0
        elif duplicate_ratio > 0.2:
            score -= 1.0
        
        return max(score, 0.0)
    
    async def _predict_error_probability(self, code: str, language: str) -> float:
        """エラー発生確率を予測"""
        error_indicators = 0
        
        # 一般的なエラーパターン
        error_patterns = [
            r'TODO|FIXME|XXX',  # 未完成マーカー
            r'print\s*\(',      # デバッグ文
            r'console\.log',    # デバッグ文
            r'//\s*hack',       # ハックコメント
            r'#\s*hack',        # ハックコメント
        ]
        
        for pattern in error_patterns:
            error_indicators += len(re.findall(pattern, code, re.IGNORECASE))
        
        # 複雑な正規表現や文字列操作
        complex_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'\.replace\([^)]*\)',
            r'\.split\([^)]*\)'
        ]
        
        for pattern in complex_patterns:
            error_indicators += len(re.findall(pattern, code))
        
        # 確率を0-1の範囲に正規化
        probability = min(error_indicators * 0.1, 1.0)
        return probability
    
    async def _generate_suggestions(self, code: str, language: str, metrics: CodeQualityMetrics) -> List[str]:
        """改善提案を生成"""
        suggestions = []
        
        if metrics.complexity_score > 7:
            suggestions.append("関数をより小さな関数に分割することを検討してください")
        
        if metrics.readability_score < 6:
            suggestions.append("コメントを追加して可読性を向上させてください")
            suggestions.append("変数名をより分かりやすくすることを検討してください")
        
        if metrics.maintainability_score < 6:
            suggestions.append("重複コードをリファクタリングしてください")
            suggestions.append("関数のサイズを小さくすることを検討してください")
        
        if metrics.error_probability > 0.5:
            suggestions.append("エラーハンドリングを追加してください")
            suggestions.append("入力検証を強化してください")
        
        # 言語固有の提案
        if language == 'python':
            if 'import *' in code:
                suggestions.append("ワイルドカードインポートを避けて、具体的なインポートを使用してください")
            if not re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', code):
                suggestions.append("if __name__ == '__main__': ガードを追加することを検討してください")
        
        elif language == 'javascript':
            if 'var ' in code:
                suggestions.append("varの代わりにletやconstを使用してください")
            if '==' in code and '===' not in code:
                suggestions.append("厳密等価演算子(===)の使用を検討してください")
        
        return suggestions


@injectable
class EnhancedProgramGenerator(BaseProgramGenerator):
    """AI統合強化版プログラム生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.ollama_provider = OllamaProvider()
        self.rag_system = None
        self.prompt_manager = PromptTemplateManager()
        self.code_analyzer = EnhancedCodeAnalyzer()
        self.generation_history = []
        
        # 生成パラメータ
        self.default_params = {
            'temperature': 0.3,
            'max_tokens': 4000,
            'top_p': 0.9,
            'frequency_penalty': 0.1
        }
    
    async def initialize(self) -> bool:
        """強化版ジェネレーターの初期化"""
        try:
            logger.info("Enhanced Program Generator初期化開始...")
            
            # OllamaProvider初期化
            if not await self.ollama_provider.initialize():
                logger.error("OllamaProvider初期化失敗")
                return False
            
            # RAGシステム初期化
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            rag_config = await config_manager.get_config("rag_config.json")
            
            if rag_config:
                from ai.rag.rag_system import RAGSystem
                self.rag_system = RAGSystem(rag_config)
                await self.rag_system.initialize()
                logger.info("RAGシステム統合完了")
            
            # プロンプトテンプレート読み込み
            await self.prompt_manager.load_templates()
            
            logger.info("Enhanced Program Generator初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"Enhanced Program Generator初期化エラー: {e}")
            return False
    
    async def validate_input(self, job_input: JobInput) -> bool:
        """強化された入力検証"""
        try:
            # 基本検証
            if not job_input or not job_input.job_type:
                return False
            
            # パラメータ検証
            parameters = job_input.parameters or {}
            description = parameters.get('description', '')
            
            if not description or len(description.strip()) < 10:
                logger.warning("説明が短すぎます")
                return False
            
            # 不適切な内容検出
            inappropriate_keywords = [
                'virus', 'malware', 'hack', 'crack', 'illegal', 
                'piracy', 'exploit', 'backdoor'
            ]
            
            for keyword in inappropriate_keywords:
                if keyword.lower() in description.lower():
                    logger.warning(f"不適切なキーワードが検出されました: {keyword}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"入力検証エラー: {e}")
            return False
    
    async def generate(self, job_input: JobInput) -> GenerationResult:
        """強化されたプログラム生成"""
        try:
            if not await self.validate_input(job_input):
                return GenerationResult(
                    success=False,
                    error_message="入力検証に失敗しました"
                )
            
            logger.info(f"強化版プログラム生成開始: {job_input.job_id}")
            start_time = datetime.now()
            
            # 複数回の生成試行で品質向上
            best_result = None
            best_quality_score = 0.0
            
            for attempt in range(3):  # 最大3回試行
                try:
                    # 生成実行
                    result = await self._generate_with_quality_check(job_input, attempt)
                    
                    if result.success:
                        # 品質評価
                        quality_score = await self._evaluate_generation_quality(result, job_input)
                        
                        if quality_score > best_quality_score:
                            best_result = result
                            best_quality_score = quality_score
                        
                        # 十分な品質なら終了
                        if quality_score >= 8.0:
                            break
                            
                except Exception as e:
                    logger.warning(f"生成試行 {attempt + 1} でエラー: {e}")
                    continue
            
            if not best_result:
                return GenerationResult(
                    success=False,
                    error_message="すべての生成試行が失敗しました"
                )
            
            # 生成履歴に記録
            generation_time = (datetime.now() - start_time).total_seconds()
            self._record_generation_history(job_input, best_result, generation_time, best_quality_score)
            
            logger.info(f"強化版プログラム生成完了: {job_input.job_id}, 品質スコア: {best_quality_score:.2f}")
            return best_result
            
        except Exception as e:
            logger.error(f"強化版プログラム生成エラー: {e}")
            return GenerationResult(
                success=False,
                error_message=f"生成エラー: {str(e)}"
            )
    
    async def _generate_with_quality_check(self, job_input: JobInput, attempt: int) -> GenerationResult:
        """品質チェック付きの生成実行"""
        # 高品質プロンプト構築
        enhanced_prompt = await self._build_enhanced_prompt(job_input, attempt)
        
        # AI生成実行
        generated_content = await self.ollama_provider.generate_text(
            prompt=enhanced_prompt,
            **self.default_params
        )
        
        # コード抽出
        extracted_code = self._extract_code_from_response(generated_content)
        
        # 品質分析
        language = self._determine_content_type(job_input)
        quality_metrics = await self.code_analyzer.analyze_code_quality(extracted_code, language)
        
        # プロジェクトファイル作成
        project_files = await self._create_enhanced_project_files(job_input, extracted_code, quality_metrics)
        
        # ZIP作成
        zip_path = await self._create_zip_package(job_input.job_id, project_files)
        
        # プレビュー生成
        preview_html = await self._create_enhanced_preview(project_files, quality_metrics, language)
        
        return GenerationResult(
            success=True,
            content=extracted_code,
            files=project_files,
            download_url=zip_path,
            preview_html=preview_html,
            metadata={
                'language': language,
                'quality_metrics': quality_metrics.to_dict(),
                'generation_attempt': attempt + 1,
                'ai_model': self.ollama_provider.current_model,
                'prompt_length': len(enhanced_prompt),
                'code_length': len(extracted_code)
            }
        )
    
    async def _build_enhanced_prompt(self, job_input: JobInput, attempt: int) -> str:
        """強化されたプロンプト構築"""
        try:
            parameters = job_input.parameters
            description = parameters.get('description', '')
            language = self._determine_content_type(job_input)
            
            # ベースプロンプト
            base_prompt = f"""あなたは熟練したプログラマーです。以下の要件に基づいて高品質な{language}プログラムを生成してください。

## 要件
{description}

## 制約
- 実用的で動作する完全なコードを生成してください
- 適切なコメントを含めてください  
- エラーハンドリングを含めてください
- 可読性と保守性を重視してください
- セキュリティを考慮してください
"""
            
            # RAGからの関連情報を追加
            if self.rag_system:
                rag_results = await self.rag_system.search(
                    query=f"{language} {description}",
                    mode="interactive",
                    top_k=3
                )
                
                if rag_results:
                    base_prompt += "\n## 参考情報\n"
                    for result in rag_results:
                        base_prompt += f"- {result.chunk.content[:200]}...\n"
            
            # 言語固有のガイドライン
            guidelines = await self._get_language_guidelines(language)
            base_prompt += f"\n## {language}固有のガイドライン\n{guidelines}"
            
            # 試行回数に応じた調整
            if attempt > 0:
                base_prompt += f"\n\n## 追加要求（試行 {attempt + 1}）\n"
                base_prompt += "前回の生成結果を改善し、より高品質なコードを生成してください。\n"
                base_prompt += "特に以下の点に注意してください：\n"
                base_prompt += "- コードの複雑度を下げる\n"
                base_prompt += "- 可読性を向上させる\n"
                base_prompt += "- エラー処理を強化する\n"
            
            # 出力形式指定
            base_prompt += f"\n\n## 出力形式\n```{language}\n[完全なコードをここに記述]\n```"
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"プロンプト構築エラー: {e}")
            return f"{language}プログラムを生成してください: {description}"
    
    async def _get_language_guidelines(self, language: str) -> str:
        """言語固有のガイドライン取得"""
        guidelines = {
            'python': """
- PEP 8スタイルガイドに従ってください
- 型ヒントを使用してください
- docstringを適切に記述してください
- if __name__ == "__main__": を使用してください
- 例外処理を適切に行ってください
""",
            'javascript': """
- ES6+の構文を使用してください
- const/letを使用し、varは避けてください
- 厳密等価演算子(===)を使用してください
- 適切なエラーハンドリングを行ってください
- JSDocコメントを記述してください
""",
            'web': """
- セマンティックなHTMLを使用してください
- アクセシビリティを考慮してください
- レスポンシブデザインを実装してください
- 適切なmetaタグを含めてください
- CSSは外部ファイルまたは<style>タグで記述してください
"""
        }
        
        return guidelines.get(language, "品質の高いコードを生成してください")
    
    async def _evaluate_generation_quality(self, result: GenerationResult, job_input: JobInput) -> float:
        """生成結果の品質評価"""
        try:
            if not result.success or not result.content:
                return 0.0
            
            # 品質メトリクスから基本スコア計算
            quality_metrics = result.metadata.get('quality_metrics', {})
            complexity_score = quality_metrics.get('complexity_score', 5.0)
            readability_score = quality_metrics.get('readability_score', 5.0)
            maintainability_score = quality_metrics.get('maintainability_score', 5.0)
            error_probability = quality_metrics.get('error_probability', 0.5)
            
            # 基本品質スコア（10点満点）
            base_score = (
                (10 - complexity_score) * 0.3 +  # 複雑度は低い方が良い
                readability_score * 0.3 +
                maintainability_score * 0.3 +
                (1 - error_probability) * 10 * 0.1
            )
            
            # 要件達成度評価
            requirements_score = await self._evaluate_requirements_fulfillment(result, job_input)
            
            # 最終スコア計算
            final_score = (base_score * 0.7) + (requirements_score * 0.3)
            
            return min(max(final_score, 0.0), 10.0)
            
        except Exception as e:
            logger.error(f"品質評価エラー: {e}")
            return 5.0  # デフォルトスコア
    
    async def _evaluate_requirements_fulfillment(self, result: GenerationResult, job_input: JobInput) -> float:
        """要件達成度評価"""
        try:
            description = job_input.parameters.get('description', '').lower()
            code = result.content.lower()
            
            # キーワードマッチング
            keywords = re.findall(r'\b\w+\b', description)
            important_keywords = [kw for kw in keywords if len(kw) > 3]
            
            matches = 0
            for keyword in important_keywords:
                if keyword in code:
                    matches += 1
            
            # マッチ率から要件達成度を計算
            if important_keywords:
                match_ratio = matches / len(important_keywords)
                return min(match_ratio * 10, 10.0)
            
            return 7.0  # デフォルト
            
        except Exception:
            return 7.0
    
    async def _create_enhanced_project_files(
        self, 
        job_input: JobInput, 
        code: str, 
        quality_metrics: CodeQualityMetrics
    ) -> List[Dict[str, Any]]:
        """強化されたプロジェクトファイル作成"""
        files = []
        language = self._determine_content_type(job_input)
        project_type = job_input.parameters.get('project_type', 'script')
        
        # メインコードファイル
        main_filename = self._get_main_filename(project_type, language)
        files.append({
            'filename': main_filename,
            'content': code,
            'type': language,
            'line_count': len(code.split('\n')),
            'quality_score': (quality_metrics.complexity_score + quality_metrics.readability_score + quality_metrics.maintainability_score) / 3
        })
        
        # 強化されたREADME.md
        readme_content = await self._generate_enhanced_readme(job_input, quality_metrics)
        files.append({
            'filename': 'README.md',
            'content': readme_content,
            'type': 'markdown',
            'line_count': len(readme_content.split('\n'))
        })
        
        # 品質レポート
        quality_report = await self._generate_quality_report(quality_metrics)
        files.append({
            'filename': 'QUALITY_REPORT.md',
            'content': quality_report,
            'type': 'markdown',
            'line_count': len(quality_report.split('\n'))
        })
        
        # 言語固有ファイル
        additional_files = await self._create_language_specific_files(job_input, code, language)
        files.extend(additional_files)
        
        return files
    
    async def _generate_enhanced_readme(self, job_input: JobInput, quality_metrics: CodeQualityMetrics) -> str:
        """強化されたREADME.md生成"""
        parameters = job_input.parameters
        description = parameters.get('description', '')
        language = self._determine_content_type(job_input)
        
        readme = f"""# {job_input.job_type.title()}

## 概要
{description}

## 特徴
- AI生成による高品質なコード
- 品質メトリクス付き
- 自動テスト対応
- セキュリティ考慮済み

## 品質指標
- **複雑度スコア**: {quality_metrics.complexity_score:.1f}/10
- **可読性スコア**: {quality_metrics.readability_score:.1f}/10
- **保守性スコア**: {quality_metrics.maintainability_score:.1f}/10
- **エラー予測確率**: {quality_metrics.error_probability:.1%}

## セットアップ
"""
        
        if language == 'python':
            readme += """
### Python環境
```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 依存関係インストール
pip install -r requirements.txt

# 実行
python main.py
```
"""
        elif language == 'javascript':
            readme += """
### Node.js環境
```bash
# 依存関係インストール
npm install

# 実行
node main.js
```
"""
        elif language == 'web':
            readme += """
### Web環境
```bash
# 静的サーバーで実行
python -m http.server 8000
# または
npx serve .
```
ブラウザで http://localhost:8000 にアクセス
"""
        
        # 改善提案追加
        if quality_metrics.suggestions:
            readme += "\n## 改善提案\n"
            for i, suggestion in enumerate(quality_metrics.suggestions, 1):
                readme += f"{i}. {suggestion}\n"
        
        readme += f"""
## 技術仕様
- **言語**: {language.title()}
- **生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **AI モデル**: Ollama (DeepSeek/Llama)
- **品質保証**: 自動分析済み

## ライセンス
MIT License

## サポート
生成されたコードに関する質問や改善要望は、Support Systemまでお問い合わせください。
"""
        
        return readme
    
    async def _generate_quality_report(self, quality_metrics: CodeQualityMetrics) -> str:
        """品質レポート生成"""
        report = f"""# コード品質レポート

## 生成日時
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 品質メトリクス

### 複雑度 ({quality_metrics.complexity_score:.1f}/10)
"""
        
        if quality_metrics.complexity_score <= 3:
            report += "✅ **優秀**: コードは非常にシンプルで理解しやすいです。"
        elif quality_metrics.complexity_score <= 6:
            report += "⚠️ **良好**: 適度な複雑さですが、さらなる簡略化が可能です。"
        else:
            report += "❌ **要改善**: コードが複雑すぎます。リファクタリングを推奨します。"
        
        report += f"""

### 可読性 ({quality_metrics.readability_score:.1f}/10)
"""
        
        if quality_metrics.readability_score >= 8:
            report += "✅ **優秀**: コードは非常に読みやすく書かれています。"
        elif quality_metrics.readability_score >= 6:
            report += "⚠️ **良好**: 可読性は十分ですが、改善の余地があります。"
        else:
            report += "❌ **要改善**: 可読性の向上が必要です。"
        
        report += f"""

### 保守性 ({quality_metrics.maintainability_score:.1f}/10)
"""
        
        if quality_metrics.maintainability_score >= 8:
            report += "✅ **優秀**: 保守しやすい構造になっています。"
        elif quality_metrics.maintainability_score >= 6:
            report += "⚠️ **良好**: 保守性は十分ですが、改善可能です。"
        else:
            report += "❌ **要改善**: 保守性の向上が必要です。"
        
        report += f"""

### エラー予測確率 ({quality_metrics.error_probability:.1%})
"""
        
        if quality_metrics.error_probability <= 0.2:
            report += "✅ **低リスク**: エラーの可能性は低いです。"
        elif quality_metrics.error_probability <= 0.5:
            report += "⚠️ **中リスク**: 一部のエラーリスクがあります。"
        else:
            report += "❌ **高リスク**: エラーハンドリングの強化が必要です。"
        
        # 改善提案
        if quality_metrics.suggestions:
            report += "\n## 改善提案\n\n"
            for i, suggestion in enumerate(quality_metrics.suggestions, 1):
                report += f"{i}. **{suggestion}**\n"
        
        report += """
## 総合評価

この品質レポートは、AIによって自動生成されたコードの品質を客観的に評価します。
提案された改善点を適用することで、より高品質で保守しやすいコードになります。

---
*このレポートは Enhanced Program Generator によって自動生成されました。*
"""
        
        return report
    
    async def _create_language_specific_files(self, job_input: JobInput, code: str, language: str) -> List[Dict[str, Any]]:
        """言語固有の追加ファイル作成"""
        files = []
        
        if language == 'python':
            # requirements.txt
            requirements = await self._extract_python_requirements(code)
            if requirements:
                files.append({
                    'filename': 'requirements.txt',
                    'content': '\n'.join(requirements),
                    'type': 'text',
                    'line_count': len(requirements)
                })
            
            # pytest用テストファイル
            test_content = await self._generate_python_test(job_input, code)
            files.append({
                'filename': 'test_main.py',
                'content': test_content,
                'type': 'python',
                'line_count': len(test_content.split('\n'))
            })
            
        elif language == 'javascript':
            # package.json
            package_json = await self._generate_enhanced_package_json(job_input, code)
            files.append({
                'filename': 'package.json',
                'content': package_json,
                'type': 'json',
                'line_count': len(package_json.split('\n'))
            })
            
            # Jest用テストファイル
            test_content = await self._generate_javascript_test(job_input, code)
            files.append({
                'filename': 'main.test.js',
                'content': test_content,
                'type': 'javascript',
                'line_count': len(test_content.split('\n'))
            })
        
        return files
    
    async def _generate_python_test(self, job_input: JobInput, code: str) -> str:
        """Python用テストファイル生成"""
        return f"""#!/usr/bin/env python3
\"\"\"
テストファイル - {job_input.job_type}
AI生成されたコードの自動テスト
\"\"\"

import pytest
import unittest
from unittest.mock import Mock, patch

# メインモジュールをインポート
# import main  # 実際のファイル名に応じて調整

class Test{job_input.job_type.title().replace('_', '')}(unittest.TestCase):
    \"\"\"メイン機能のテストクラス\"\"\"
    
    def setUp(self):
        \"\"\"テストの前処理\"\"\"
        pass
    
    def test_basic_functionality(self):
        \"\"\"基本機能のテスト\"\"\"
        # TODO: 実際のテストケースを実装
        self.assertTrue(True)
    
    def test_edge_cases(self):
        \"\"\"エッジケースのテスト\"\"\"
        # TODO: エッジケースのテストを実装
        pass
    
    def test_error_handling(self):
        \"\"\"エラーハンドリングのテスト\"\"\"
        # TODO: エラーケースのテストを実装
        pass

if __name__ == '__main__':
    unittest.main()
"""
    
    async def _generate_javascript_test(self, job_input: JobInput, code: str) -> str:
        """JavaScript用テストファイル生成"""
        return f"""/**
 * テストファイル - {job_input.job_type}
 * AI生成されたコードの自動テスト
 */

const {{ describe, it, expect, beforeEach }} = require('@jest/globals');
// const main = require('./main'); // 実際のファイル名に応じて調整

describe('{job_input.job_type}', () => {{
    beforeEach(() => {{
        // テストの前処理
    }});
    
    it('基本機能をテストする', () => {{
        // TODO: 実際のテストケースを実装
        expect(true).toBe(true);
    }});
    
    it('エッジケースをテストする', () => {{
        // TODO: エッジケースのテストを実装
    }});
    
    it('エラーハンドリングをテストする', () => {{
        // TODO: エラーケースのテストを実装
    }});
}});
"""
    
    async def _generate_enhanced_package_json(self, job_input: JobInput, code: str) -> str:
        """強化されたpackage.json生成"""
        package_data = {
            "name": job_input.job_type.replace('_', '-'),
            "version": "1.0.0",
            "description": job_input.parameters.get('description', ''),
            "main": "main.js",
            "scripts": {
                "start": "node main.js",
                "test": "jest",
                "lint": "eslint *.js",
                "dev": "nodemon main.js"
            },
            "dependencies": await self._extract_js_dependencies(code),
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0",
                "nodemon": "^2.0.0"
            },
            "keywords": ["ai-generated", "javascript"],
            "author": "Enhanced Program Generator",
            "license": "MIT"
        }
        
        return json.dumps(package_data, indent=2, ensure_ascii=False)
    
    async def _create_enhanced_preview(self, project_files: List[Dict[str, Any]], quality_metrics: CodeQualityMetrics, language: str) -> str:
        """強化されたプレビュー生成"""
        try:
            main_file = next((f for f in project_files if f['filename'].endswith(('.py', '.js', '.html'))), None)
            
            if not main_file:
                return "<p>プレビューできるファイルがありません。</p>"
            
            # 品質スコア計算
            overall_quality = (
                quality_metrics.complexity_score + 
                quality_metrics.readability_score + 
                quality_metrics.maintainability_score
            ) / 3
            
            quality_color = "green" if overall_quality >= 7 else "orange" if overall_quality >= 5 else "red"
            
            preview = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Code Preview - {main_file['filename']}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; 
            background: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 10px; 
            overflow: hidden; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }}
        .quality-badge {{ 
            display: inline-block; 
            padding: 5px 15px; 
            background: {quality_color}; 
            color: white; 
            border-radius: 20px; 
            font-size: 14px; 
            margin-top: 10px; 
        }}
        .metrics {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            padding: 30px; 
            background: #f8f9fa; 
        }}
        .metric {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            text-align: center; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }}
        .metric-value {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #667eea; 
            margin-bottom: 5px; 
        }}
        .code-section {{ 
            padding: 30px; 
        }}
        .code {{ 
            background: #2d3748; 
            color: #e2e8f0; 
            padding: 20px; 
            border-radius: 8px; 
            overflow-x: auto; 
            font-family: 'Consolas', 'Monaco', monospace; 
            line-height: 1.5; 
        }}
        .suggestions {{ 
            padding: 30px; 
            background: #fff3cd; 
        }}
        .suggestion {{ 
            background: white; 
            padding: 15px; 
            margin: 10px 0; 
            border-left: 4px solid #ffc107; 
            border-radius: 4px; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Enhanced Code Preview</h1>
            <p>{main_file['filename']} | {language.title()}</p>
            <div class="quality-badge">品質スコア: {overall_quality:.1f}/10</div>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{quality_metrics.complexity_score:.1f}</div>
                <div>複雑度</div>
            </div>
            <div class="metric">
                <div class="metric-value">{quality_metrics.readability_score:.1f}</div>
                <div>可読性</div>
            </div>
            <div class="metric">
                <div class="metric-value">{quality_metrics.maintainability_score:.1f}</div>
                <div>保守性</div>
            </div>
            <div class="metric">
                <div class="metric-value">{quality_metrics.error_probability:.0%}</div>
                <div>エラー予測確率</div>
            </div>
        </div>
        
        <div class="code-section">
            <h3>生成されたコード</h3>
            <pre class="code">{self._escape_html(main_file['content'])}</pre>
        </div>
"""
            
            if quality_metrics.suggestions:
                preview += """
        <div class="suggestions">
            <h3>改善提案</h3>
"""
                for suggestion in quality_metrics.suggestions:
                    preview += f'<div class="suggestion">💡 {suggestion}</div>'
                
                preview += "</div>"
            
            preview += """
    </div>
</body>
</html>"""
            
            return preview
            
        except Exception as e:
            logger.error(f"強化プレビュー生成エラー: {e}")
            return f"<p>プレビュー生成エラー: {str(e)}</p>"
    
    async def _extract_python_requirements(self, code: str) -> List[str]:
        """Python要件抽出（強化版）"""
        requirements = set()
        
        # インポート文を抽出
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            requirements.update(matches)
        
        # 標準ライブラリを除外
        stdlib_modules = {
            'os', 'sys', 'json', 'csv', 're', 'math', 'datetime', 'time',
            'random', 'collections', 'itertools', 'functools', 'operator',
            'urllib', 'http', 'email', 'html', 'xml', 'sqlite3', 'pickle',
            'base64', 'hashlib', 'hmac', 'secrets', 'ssl', 'socket',
            'threading', 'asyncio', 'multiprocessing', 'subprocess',
            'pathlib', 'shutil', 'tempfile', 'glob', 'fnmatch',
            'unittest', 'typing', 'enum', 'dataclasses', 'abc'
        }
        
        external_requirements = requirements - stdlib_modules
        
        # バージョン指定付きで返す
        versioned_requirements = []
        version_map = {
            'numpy': 'numpy>=1.21.0',
            'pandas': 'pandas>=1.3.0',
            'matplotlib': 'matplotlib>=3.5.0',
            'seaborn': 'seaborn>=0.11.0',
            'scipy': 'scipy>=1.7.0',
            'scikit-learn': 'scikit-learn>=1.0.0',
            'sklearn': 'scikit-learn>=1.0.0',
            'tensorflow': 'tensorflow>=2.8.0',
            'torch': 'torch>=1.10.0',
            'cv2': 'opencv-python>=4.5.0',
            'PIL': 'Pillow>=8.0.0',
            'requests': 'requests>=2.25.0',
            'flask': 'Flask>=2.0.0',
            'django': 'Django>=4.0.0',
            'fastapi': 'fastapi>=0.70.0',
            'pydantic': 'pydantic>=1.8.0',
            'sqlalchemy': 'SQLAlchemy>=1.4.0'
        }
        
        for req in sorted(external_requirements):
            versioned_requirements.append(version_map.get(req, req))
        
        return versioned_requirements
    
    async def _extract_js_dependencies(self, code: str) -> Dict[str, str]:
        """JavaScript依存関係抽出（強化版）"""
        dependencies = {}
        
        # require文を抽出
        require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
        requires = re.findall(require_pattern, code)
        
        # import文を抽出
        import_pattern = r'import\s+.*?\s+from\s+["\']([^"\']+)["\']'
        imports = re.findall(import_pattern, code)
        
        all_modules = set(requires + imports)
        
        # Node.js標準モジュールを除外
        stdlib_modules = {
            'fs', 'path', 'os', 'crypto', 'http', 'https', 'url',
            'querystring', 'util', 'events', 'stream', 'buffer',
            'process', 'child_process', 'cluster', 'net', 'dns',
            'assert', 'console', 'timers', 'readline', 'repl'
        }
        
        external_modules = [mod for mod in all_modules if mod not in stdlib_modules and not mod.startswith('.')]
        
        # バージョン指定
        version_map = {
            'express': '^4.18.0',
            'lodash': '^4.17.0',
            'axios': '^0.27.0',
            'moment': '^2.29.0',
            'uuid': '^8.3.0',
            'joi': '^17.6.0',
            'bcrypt': '^5.0.0',
            'jsonwebtoken': '^8.5.0',
            'mongoose': '^6.3.0',
            'sequelize': '^6.20.0',
            'react': '^18.1.0',
            'vue': '^3.2.0',
            'angular': '^14.0.0'
        }
        
        for module in external_modules:
            dependencies[module] = version_map.get(module, '^1.0.0')
        
        return dependencies
    
    def _record_generation_history(self, job_input: JobInput, result: GenerationResult, generation_time: float, quality_score: float):
        """生成履歴の記録"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'job_id': job_input.job_id,
            'job_type': job_input.job_type,
            'language': result.metadata.get('language', 'unknown'),
            'quality_score': quality_score,
            'generation_time': generation_time,
            'code_length': len(result.content),
            'file_count': len(result.files),
            'success': result.success
        }
        
        self.generation_history.append(history_entry)
        
        # 履歴は最新100件まで保持
        if len(self.generation_history) > 100:
            self.generation_history = self.generation_history[-100:]
        
        logger.info(f"生成履歴記録: 品質スコア {quality_score:.2f}, 時間 {generation_time:.2f}秒")
    
    async def get_generation_statistics(self) -> Dict[str, Any]:
        """生成統計情報を取得"""
        if not self.generation_history:
            return {"message": "生成履歴がありません"}
        
        total_generations = len(self.generation_history)
        successful_generations = sum(1 for entry in self.generation_history if entry['success'])
        
        quality_scores = [entry['quality_score'] for entry in self.generation_history if entry['success']]
        generation_times = [entry['generation_time'] for entry in self.generation_history if entry['success']]
        
        statistics = {
            'total_generations': total_generations,
            'successful_generations': successful_generations,
            'success_rate': successful_generations / total_generations if total_generations > 0 else 0,
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'average_generation_time': sum(generation_times) / len(generation_times) if generation_times else 0,
            'languages_used': list(set(entry['language'] for entry in self.generation_history)),
            'most_common_job_type': max(set(entry['job_type'] for entry in self.generation_history), 
                                      key=lambda x: sum(1 for e in self.generation_history if e['job_type'] == x)) if self.generation_history else None
        }
        
        return statistics
    
    async def cleanup_old_files(self, days: int = 7):
        """古いファイルのクリーンアップ"""
        try:
            import glob
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 一時ディレクトリのクリーンアップ
            temp_pattern = os.path.join(self.output_dir, "project_*")
            for temp_dir in glob.glob(temp_pattern):
                try:
                    dir_stat = os.path.stat(temp_dir)
                    if datetime.fromtimestamp(dir_stat.st_mtime) < cutoff_date:
                        shutil.rmtree(temp_dir)
                        logger.info(f"古いディレクトリを削除: {temp_dir}")
                except Exception as e:
                    logger.warning(f"ディレクトリ削除エラー: {temp_dir}, {e}")
            
            # ZIPファイルのクリーンアップ
            zip_pattern = os.path.join(self.output_dir, "*.zip")
            for zip_file in glob.glob(zip_pattern):
                try:
                    file_stat = os.path.stat(zip_file)
                    if datetime.fromtimestamp(file_stat.st_mtime) < cutoff_date:
                        os.remove(zip_file)
                        logger.info(f"古いZIPファイルを削除: {zip_file}")
                except Exception as e:
                    logger.warning(f"ZIPファイル削除エラー: {zip_file}, {e}")
            
            logger.info(f"{days}日以上古いファイルのクリーンアップ完了")
            
        except Exception as e:
            logger.error(f"ファイルクリーンアップエラー: {e}")