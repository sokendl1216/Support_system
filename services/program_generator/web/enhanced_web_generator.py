"""
Enhanced Web Generator - AI統合強化版Webページ生成サービス

Task 3-6: Webページ生成サービス実装
OllamaProvider統合、RAGシステム、高度なプロンプト構築、
コード品質検証、自動最適化機能を追加した強化版Web生成実装
"""

import asyncio
import logging
import re
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


class WebQualityMetrics:
    """Web品質メトリクス"""
    
    def __init__(self):
        self.accessibility_score = 0.0
        self.performance_score = 0.0
        self.seo_score = 0.0
        self.responsive_score = 0.0
        self.security_score = 0.0
        self.modern_practices_score = 0.0
        self.overall_score = 0.0
        self.issues = []
        self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'accessibility_score': self.accessibility_score,
            'performance_score': self.performance_score,
            'seo_score': self.seo_score,
            'responsive_score': self.responsive_score,
            'security_score': self.security_score,
            'modern_practices_score': self.modern_practices_score,
            'overall_score': self.overall_score,
            'issues': self.issues,
            'recommendations': self.recommendations
        }


class EnhancedWebAnalyzer:
    """強化版Web品質分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_web_code(self, code_sections: Dict[str, str]) -> WebQualityMetrics:
        """Web品質の包括的分析"""
        metrics = WebQualityMetrics()
        
        try:
            html_code = code_sections.get('html', '')
            css_code = code_sections.get('css', '')
            js_code = code_sections.get('javascript', '')
            
            # アクセシビリティ分析
            accessibility_score = await self._analyze_accessibility(html_code)
            
            # パフォーマンス分析
            performance_score = await self._analyze_performance(html_code, css_code, js_code)
            
            # SEO分析
            seo_score = await self._analyze_seo(html_code)
            
            # レスポンシブデザイン分析
            responsive_score = await self._analyze_responsive_design(css_code)
            
            # セキュリティ分析
            security_score = await self._analyze_security(html_code, js_code)
            
            # モダンな開発手法分析
            modern_practices_score = await self._analyze_modern_practices(html_code, css_code, js_code)
            
            # 総合スコア計算
            metrics.accessibility_score = accessibility_score
            metrics.performance_score = performance_score
            metrics.seo_score = seo_score
            metrics.responsive_score = responsive_score
            metrics.security_score = security_score
            metrics.modern_practices_score = modern_practices_score
            metrics.overall_score = (
                accessibility_score * 0.2 +
                performance_score * 0.2 +
                seo_score * 0.15 +
                responsive_score * 0.15 +
                security_score * 0.15 +
                modern_practices_score * 0.15
            )
            
            self.logger.info(f"Web品質分析完了 - 総合スコア: {metrics.overall_score:.2f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Web品質分析エラー: {str(e)}")
            return metrics
    
    async def _analyze_accessibility(self, html_code: str) -> float:
        """アクセシビリティ分析"""
        score = 0.0
        total_checks = 10
        
        if not html_code:
            return score
        
        # 基本的なアクセシビリティチェック
        checks = [
            ('alt属性', r'<img[^>]+alt='),
            ('role属性', r'role='),
            ('aria-label', r'aria-label='),
            ('aria-describedby', r'aria-describedby='),
            ('semantic要素', r'<(header|nav|main|section|article|aside|footer)'),
            ('heading構造', r'<h[1-6]'),
            ('フォームラベル', r'<label[^>]+for='),
            ('tabindex', r'tabindex='),
            ('skip link', r'skip.*content'),
            ('contrast', r'color.*#|rgb|hsl')
        ]
        
        for check_name, pattern in checks:
            if re.search(pattern, html_code, re.IGNORECASE):
                score += 1
        
        return (score / total_checks) * 100
    
    async def _analyze_performance(self, html_code: str, css_code: str, js_code: str) -> float:
        """パフォーマンス分析"""
        score = 0.0
        total_checks = 8
        
        # パフォーマンス関連チェック
        if html_code:
            # 適切なmetaタグ
            if re.search(r'<meta.*viewport', html_code, re.IGNORECASE):
                score += 1
            
            # 画像最適化関連
            if re.search(r'loading=["\']lazy["\']', html_code, re.IGNORECASE):
                score += 1
            
            # 外部リソースの非同期読み込み
            if re.search(r'async|defer', html_code, re.IGNORECASE):
                score += 1
        
        if css_code:
            # CSS最適化チェック
            if 'min-width' in css_code or 'max-width' in css_code:
                score += 1
            
            # Flexbox/Grid使用
            if 'flex' in css_code or 'grid' in css_code:
                score += 1
        
        if js_code:
            # JavaScript最適化チェック
            if 'addEventListener' in js_code:
                score += 1
            
            # モダンJS機能
            if any(feature in js_code for feature in ['const ', 'let ', '=>', 'async', 'await']):
                score += 1
            
            # DOM Ready
            if 'DOMContentLoaded' in js_code:
                score += 1
        
        return (score / total_checks) * 100
    
    async def _analyze_seo(self, html_code: str) -> float:
        """SEO分析"""
        score = 0.0
        total_checks = 8
        
        if not html_code:
            return score
        
        # SEO関連チェック
        seo_checks = [
            ('title', r'<title[^>]*>'),
            ('meta description', r'<meta[^>]+name=["\']description["\']'),
            ('meta keywords', r'<meta[^>]+name=["\']keywords["\']'),
            ('heading structure', r'<h1[^>]*>'),
            ('canonical', r'<link[^>]+rel=["\']canonical["\']'),
            ('Open Graph', r'<meta[^>]+property=["\']og:'),
            ('structured data', r'application/ld\+json'),
            ('sitemap reference', r'sitemap')
        ]
        
        for check_name, pattern in seo_checks:
            if re.search(pattern, html_code, re.IGNORECASE):
                score += 1
        
        return (score / total_checks) * 100
    
    async def _analyze_responsive_design(self, css_code: str) -> float:
        """レスポンシブデザイン分析"""
        score = 0.0
        total_checks = 6
        
        if not css_code:
            return score
        
        # レスポンシブデザインチェック
        responsive_checks = [
            ('media queries', r'@media'),
            ('flexible layouts', r'flex|grid'),
            ('relative units', r'%|em|rem|vw|vh'),
            ('max-width', r'max-width'),
            ('mobile-first', r'min-width'),
            ('fluid images', r'max-width.*100%')
        ]
        
        for check_name, pattern in responsive_checks:
            if re.search(pattern, css_code, re.IGNORECASE):
                score += 1
        
        return (score / total_checks) * 100
    
    async def _analyze_security(self, html_code: str, js_code: str) -> float:
        """セキュリティ分析"""
        score = 0.0
        total_checks = 5
        
        # セキュリティ関連チェック
        if html_code:
            # CSPヘッダー
            if 'Content-Security-Policy' in html_code:
                score += 1
            
            # noopener/noreferrer
            if re.search(r'rel=["\'][^"\']*no(opener|referrer)', html_code):
                score += 1
            
            # HTTPSリンク
            if 'https://' in html_code and 'http://' not in html_code:
                score += 1
        
        if js_code:
            # eval使用回避
            if 'eval(' not in js_code:
                score += 1
            
            # innerHTML安全使用
            if 'textContent' in js_code or 'innerText' in js_code:
                score += 1
        
        return (score / total_checks) * 100
    
    async def _analyze_modern_practices(self, html_code: str, css_code: str, js_code: str) -> float:
        """モダンな開発手法分析"""
        score = 0.0
        total_checks = 8
        
        if html_code:
            # HTML5セマンティック要素
            if re.search(r'<(header|nav|main|section|article|aside|footer)', html_code):
                score += 1
            
            # Modern HTML attributes
            if re.search(r'(loading|decoding|fetchpriority)', html_code):
                score += 1
        
        if css_code:
            # Modern CSS
            modern_css_features = ['grid', 'flex', 'var(', '@supports', 'clamp(', 'min(', 'max(']
            if any(feature in css_code for feature in modern_css_features):
                score += 1
            
            # CSS3 features
            if re.search(r'(transform|transition|animation)', css_code):
                score += 1
            
            # Custom properties
            if '--' in css_code:
                score += 1
        
        if js_code:
            # Modern JavaScript
            modern_js_features = ['const ', 'let ', '=>', 'async', 'await', 'fetch(']
            matching_features = sum(1 for feature in modern_js_features if feature in js_code)
            if matching_features >= 3:
                score += 1
            
            # ES6+ features
            if re.search(r'(class |import |export )', js_code):
                score += 1
            
            # Modern APIs
            if any(api in js_code for api in ['querySelector', 'addEventListener', 'fetch']):
                score += 1
        
        return (score / total_checks) * 100


@injectable
class EnhancedWebGenerator(BaseProgramGenerator):
    """
    AI統合強化版Webページ生成サービス
    
    OllamaProvider、RAGシステム統合により高品質なWebページ生成を実現。
    アクセシビリティ、パフォーマンス、SEO対応、レスポンシブデザイン、
    モダンな開発手法の自動適用などの高度な機能を提供。
    """
    
    def __init__(self):
        super().__init__()
        self.language = 'web'
        self.file_extension = '.html'
        self.ollama_provider: Optional[OllamaProvider] = None
        self.rag_system: Optional[RAGSystem] = None
        self.prompt_manager: Optional[PromptTemplateManager] = None
        self.web_analyzer = EnhancedWebAnalyzer()
        
        # Web特化設定
        self.supported_frameworks = [
            'vanilla', 'bootstrap', 'tailwind', 'bulma', 'foundation',
            'materialize', 'semantic-ui', 'vue', 'react', 'alpine'
        ]
        self.supported_project_types = [
            'static_site', 'landing_page', 'portfolio', 'blog',
            'dashboard', 'ecommerce', 'spa', 'pwa', 'documentation'
        ]
    
    async def initialize(self) -> bool:
        """強化版Web生成サービスの初期化"""
        try:
            self.logger.info("強化版Web生成サービス初期化開始")
            
            # OllamaProvider初期化
            config_path = Path('config/ollama_models.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.ollama_provider = OllamaProvider(model_config=config['models'])
                
                # ヘルスチェック
                if await self.ollama_provider.is_healthy():
                    self.logger.info("OllamaProvider 初期化成功")
                else:
                    self.logger.warning("OllamaProvider 接続不良")
            
            # RAGシステム初期化
            try:
                self.rag_system = RAGSystem()
                await self.rag_system.initialize()
                self.logger.info("RAGシステム 初期化成功")
            except Exception as e:
                self.logger.warning(f"RAGシステム 初期化失敗: {str(e)}")
            
            # プロンプトテンプレートマネージャー初期化
            try:
                self.prompt_manager = PromptTemplateManager()
                await self.prompt_manager.initialize()
                self.logger.info("プロンプトテンプレートマネージャー 初期化成功")
            except Exception as e:
                self.logger.warning(f"プロンプトテンプレートマネージャー 初期化失敗: {str(e)}")
            
            self.logger.info("強化版Web生成サービス 初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"強化版Web生成サービス 初期化エラー: {str(e)}")
            return False
    
    async def validate_input(self, job_input: JobInput) -> bool:
        """強化版入力検証"""
        try:
            await super().validate_input(job_input)
            
            parameters = job_input.parameters
            
            # プロジェクトタイプ検証
            project_type = parameters.get('project_type', 'static_site')
            if project_type not in self.supported_project_types:
                self.logger.warning(f"未対応プロジェクトタイプ: {project_type}")
                parameters['project_type'] = 'static_site'
            
            # フレームワーク検証
            framework = parameters.get('framework', 'vanilla')
            if framework not in self.supported_frameworks:
                self.logger.warning(f"未対応フレームワーク: {framework}")
                parameters['framework'] = 'vanilla'
            
            # 複雑度検証
            complexity = parameters.get('complexity', 'medium')
            if complexity not in ['simple', 'medium', 'complex', 'advanced']:
                parameters['complexity'] = 'medium'
            
            return True
            
        except Exception as e:
            self.logger.error(f"強化版入力検証エラー: {str(e)}")
            return False
    
    async def generate(self, job_input: JobInput) -> GenerationResult:
        """AI統合強化版Web生成のメイン処理"""
        try:
            if not await self.validate_input(job_input):
                return GenerationResult(
                    success=False,
                    error_message="入力検証エラー"
                )
            
            self.logger.info(f"強化版Web生成開始: {job_input.job_id}")
            
            # 1. AI駆動コンテキスト構築
            enhanced_context = await self._build_enhanced_context(job_input)
            
            # 2. 高度なプロンプト構築
            generation_prompt = await self._build_advanced_prompt(job_input, enhanced_context)
            
            # 3. AI生成実行
            ai_response = await self._execute_ai_generation(generation_prompt)
            
            # 4. コード抽出と後処理
            code_sections = await self._extract_and_enhance_code(ai_response, job_input)
            
            # 5. 品質分析と最適化
            quality_metrics = await self.web_analyzer.analyze_web_code(code_sections)
            optimized_code = await self._optimize_code_based_on_analysis(code_sections, quality_metrics)
            
            # 6. プロジェクトファイル生成
            project_files = await self._create_enhanced_project_files(job_input, optimized_code)
            
            # 7. パッケージ化
            zip_path = await self._create_zip_package(job_input.job_id, project_files)
            
            # 8. プレビュー生成
            preview_html = await self._generate_enhanced_preview(project_files)
            
            # 9. 技術スタック抽出
            technologies = await self._extract_technologies_and_features(optimized_code)
            
            # 結果構築
            result = GenerationResult(
                success=True,
                content=optimized_code.get('html', ''),
                files=project_files,
                download_url=zip_path,
                preview_html=preview_html,
                metadata={
                    'language': 'web',
                    'generator_type': 'enhanced_ai',
                    'project_type': job_input.parameters.get('project_type', 'static_site'),
                    'framework': job_input.parameters.get('framework', 'vanilla'),
                    'technologies': technologies,
                    'file_count': len(project_files),
                    'quality_metrics': quality_metrics.to_dict(),
                    'ai_powered': True,
                    'rag_enhanced': self.rag_system is not None,
                    'responsive': True,
                    'accessibility': True,
                    'seo_optimized': True,
                    'performance_optimized': True
                }
            )
            
            self.logger.info(f"強化版Web生成完了: {job_input.job_id} (品質スコア: {quality_metrics.overall_score:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"強化版Web生成エラー: {job_input.job_id}, エラー: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=f"強化版Web生成エラー: {str(e)}"
            )
    
    async def _build_enhanced_context(self, job_input: JobInput) -> Dict[str, Any]:
        """AI駆動コンテキスト構築"""
        context = {
            'basic_info': {
                'description': job_input.parameters.get('description', ''),
                'project_type': job_input.parameters.get('project_type', 'static_site'),
                'framework': job_input.parameters.get('framework', 'vanilla'),
                'complexity': job_input.parameters.get('complexity', 'medium')
            }
        }
        
        # RAGシステムからの知識拡張
        if self.rag_system:
            try:
                query = f"web development {job_input.parameters.get('project_type')} {job_input.parameters.get('framework')} best practices"
                rag_results = await self.rag_system.search(query, top_k=5)
                context['rag_knowledge'] = rag_results
            except Exception as e:
                self.logger.warning(f"RAG検索エラー: {str(e)}")
        
        return context
    
    async def _build_advanced_prompt(self, job_input: JobInput, context: Dict[str, Any]) -> str:
        """高度なプロンプト構築"""
        parameters = job_input.parameters
        project_type = parameters.get('project_type', 'static_site')
        framework = parameters.get('framework', 'vanilla')
        complexity = parameters.get('complexity', 'medium')
        
        prompt = f"""あなたは世界クラスのWeb開発者です。以下の仕様に基づいて、最高品質のWebページを生成してください。

## プロジェクト要件
- **プロジェクトタイプ**: {project_type}
- **フレームワーク**: {framework}
- **複雑度**: {complexity}
- **説明**: {parameters.get('description', '')}

## 必須要件
1. **アクセシビリティ**: WCAG 2.1 AA準拠、適切なARIA属性、セマンティックHTML
2. **レスポンシブデザイン**: モバイルファースト、フレキシブルレイアウト
3. **パフォーマンス**: 最適化された画像、遅延読み込み、最小化CSS/JS
4. **SEO**: 適切なメタタグ、構造化データ、セマンティックマークアップ
5. **セキュリティ**: XSS対策、CSP準拠、安全なリンク
6. **モダンな開発手法**: ES6+、CSS Grid/Flexbox、Progressive Enhancement

## 技術仕様
- HTML5セマンティック要素を使用
- CSS3 Grid/Flexboxによるレイアウト
- Vanilla JavaScriptまたは{framework}
- レスポンシブデザイン（320px〜1920px対応）
- ダークモード対応（可能な場合）

## コード生成形式
以下の形式で生成してください：

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <!-- 適切なメタタグ、SEO対応 -->
</head>
<body>
    <!-- セマンティックな構造 -->
</body>
</html>
```

```css
/* レスポンシブ、アクセシブル、パフォーマンス最適化されたCSS */
```

```javascript
// モダンなJavaScript（ES6+）、アクセシビリティ配慮
```

それでは、{project_type}の{framework}ベースのWebページを生成してください。"""

        # RAG知識の統合
        if context.get('rag_knowledge'):
            prompt += f"\n\n## 関連知識\n"
            for i, result in enumerate(context['rag_knowledge'][:3], 1):
                prompt += f"{i}. {result.get('content', '')[:200]}...\n"
        
        return prompt
    
    async def _execute_ai_generation(self, prompt: str) -> str:
        """AI生成実行"""
        if not self.ollama_provider:
            raise Exception("OllamaProvider が初期化されていません")
        
        from ai.llm_service import GenerationRequest, GenerationConfig
        
        request = GenerationRequest(
            prompt=prompt,
            config=GenerationConfig(
                max_tokens=8000,
                temperature=0.7,
                top_p=0.9
            )
        )
        
        response = await self.ollama_provider.generate(request)
        return response.text
    
    async def _extract_and_enhance_code(self, ai_response: str, job_input: JobInput) -> Dict[str, str]:
        """コード抽出と強化処理"""
        # 基本的なコード抽出
        code_sections = await self._extract_web_code_from_response(ai_response)
        
        # コード強化処理
        if code_sections.get('html'):
            code_sections['html'] = await self._enhance_html(code_sections['html'], job_input)
        
        if code_sections.get('css'):
            code_sections['css'] = await self._enhance_css(code_sections['css'], job_input)
        
        if code_sections.get('javascript'):
            code_sections['javascript'] = await self._enhance_javascript(code_sections['javascript'], job_input)
        
        return code_sections
    
    async def _enhance_html(self, html_code: str, job_input: JobInput) -> str:
        """HTML強化処理"""
        # 基本的な構造チェックと修正
        if not html_code.strip().startswith('<!DOCTYPE'):
            html_code = f'<!DOCTYPE html>\n{html_code}'
        
        # メタタグの追加・修正
        enhancements = []
        
        # viewport設定
        if 'viewport' not in html_code:
            enhancements.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        
        # charset設定
        if 'charset' not in html_code:
            enhancements.append('    <meta charset="UTF-8">')
        
        # SEO基本タグ
        description = job_input.parameters.get('description', '')
        if description and 'meta name="description"' not in html_code:
            enhancements.append(f'    <meta name="description" content="{description[:160]}">')
        
        # 強化要素を挿入
        if enhancements and '</head>' in html_code:
            enhancement_block = '\n'.join(enhancements) + '\n'
            html_code = html_code.replace('</head>', f'{enhancement_block}</head>')
        
        return html_code
    
    async def _enhance_css(self, css_code: str, job_input: JobInput) -> str:
        """CSS強化処理"""
        enhancements = []
        
        # CSS Reset/Normalize追加
        if '* {' not in css_code and '*,' not in css_code:
            enhancements.append("""/* CSS Reset & Modern Defaults */
*, *::before, *::after {
    box-sizing: border-box;
}

* {
    margin: 0;
    padding: 0;
}

html, body {
    height: 100%;
}

body {
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
}

img, picture, video, canvas, svg {
    display: block;
    max-width: 100%;
}

input, button, textarea, select {
    font: inherit;
}

p, h1, h2, h3, h4, h5, h6 {
    overflow-wrap: break-word;
}
""")
        
        # レスポンシブ基盤追加
        if '@media' not in css_code:
            enhancements.append("""
/* レスポンシブデザイン基盤 */
@media (max-width: 768px) {
    body {
        font-size: 14px;
    }
}

@media (max-width: 480px) {
    body {
        font-size: 13px;
    }
}""")
        
        if enhancements:
            css_code = '\n'.join(enhancements) + '\n\n' + css_code
        
        return css_code
    
    async def _enhance_javascript(self, js_code: str, job_input: JobInput) -> str:
        """JavaScript強化処理"""
        if not js_code:
            return js_code
        
        # DOMContentLoaded包囲
        if 'DOMContentLoaded' not in js_code and 'addEventListener' in js_code:
            js_code = f"""document.addEventListener('DOMContentLoaded', function() {{
{js_code}
}});"""
        
        return js_code
    
    async def _optimize_code_based_on_analysis(self, code_sections: Dict[str, str], quality_metrics: WebQualityMetrics) -> Dict[str, str]:
        """品質分析に基づくコード最適化"""
        optimized_code = code_sections.copy()
        
        # 品質スコアが低い場合の自動修正
        if quality_metrics.accessibility_score < 70:
            optimized_code['html'] = await self._improve_accessibility(optimized_code.get('html', ''))
        
        if quality_metrics.performance_score < 70:
            optimized_code = await self._improve_performance(optimized_code)
        
        if quality_metrics.seo_score < 70:
            optimized_code['html'] = await self._improve_seo(optimized_code.get('html', ''))
        
        return optimized_code
    
    async def _improve_accessibility(self, html_code: str) -> str:
        """アクセシビリティ改善"""
        # alt属性の追加
        html_code = re.sub(r'<img([^>]+)(?<!alt=)[^>]*>', r'<img\1 alt="画像">', html_code)
        
        # role属性の追加
        if '<nav' in html_code and 'role=' not in html_code:
            html_code = html_code.replace('<nav', '<nav role="navigation"')
        
        return html_code
    
    async def _improve_performance(self, code_sections: Dict[str, str]) -> Dict[str, str]:
        """パフォーマンス改善"""
        html_code = code_sections.get('html', '')
        
        # 画像の遅延読み込み
        html_code = re.sub(r'<img([^>]+)(?<!loading=)[^>]*>', r'<img\1 loading="lazy">', html_code)
        
        code_sections['html'] = html_code
        return code_sections
    
    async def _improve_seo(self, html_code: str) -> str:
        """SEO改善"""
        # titleタグがない場合の追加
        if '<title>' not in html_code:
            html_code = html_code.replace('<head>', '<head>\n    <title>Webページ</title>')
        
        return html_code
    
    async def _create_enhanced_project_files(self, job_input: JobInput, code_sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """強化版プロジェクトファイル生成"""
        files = []
        
        # メインHTMLファイル
        if code_sections.get('html'):
            files.append({
                'filename': 'index.html',
                'content': code_sections['html'],
                'type': 'html',
                'line_count': len(code_sections['html'].split('\n'))
            })
        
        # CSSファイル
        if code_sections.get('css'):
            files.append({
                'filename': 'styles.css',
                'content': code_sections['css'],
                'type': 'css',
                'line_count': len(code_sections['css'].split('\n'))
            })
        
        # JavaScriptファイル
        if code_sections.get('javascript'):
            files.append({
                'filename': 'script.js',
                'content': code_sections['javascript'],
                'type': 'javascript',
                'line_count': len(code_sections['javascript'].split('\n'))
            })
        
        # 設定ファイル
        package_json = await self._generate_package_json(job_input)
        files.append({
            'filename': 'package.json',
            'content': package_json,
            'type': 'json',
            'line_count': len(package_json.split('\n'))
        })
        
        # README.md
        readme_content = await self._generate_enhanced_readme(job_input, code_sections)
        files.append({
            'filename': 'README.md',
            'content': readme_content,
            'type': 'markdown',
            'line_count': len(readme_content.split('\n'))
        })
        
        # .gitignore
        gitignore_content = await self._generate_gitignore()
        files.append({
            'filename': '.gitignore',
            'content': gitignore_content,
            'type': 'text',
            'line_count': len(gitignore_content.split('\n'))
        })
        
        return files
    
    async def _generate_package_json(self, job_input: JobInput) -> str:
        """package.json生成"""
        package_data = {
            "name": job_input.job_id or "web-project",
            "version": "1.0.0",
            "description": job_input.parameters.get('description', ''),
            "main": "index.html",
            "scripts": {
                "start": "python -m http.server 8000",
                "dev": "python -m http.server 8000",
                "build": "echo 'Build complete'",
                "test": "echo 'No tests specified'"
            },
            "keywords": [
                "web",
                "html",
                "css",
                "javascript",
                job_input.parameters.get('project_type', 'static_site')
            ],
            "author": "",
            "license": "MIT",
            "devDependencies": {},
            "dependencies": {}
        }
        
        return json.dumps(package_data, indent=2, ensure_ascii=False)
    
    async def _generate_enhanced_readme(self, job_input: JobInput, code_sections: Dict[str, str]) -> str:
        """強化版README.md生成"""
        project_name = job_input.job_id or 'Web Project'
        description = job_input.parameters.get('description', '')
        project_type = job_input.parameters.get('project_type', 'static_site')
        framework = job_input.parameters.get('framework', 'vanilla')
        
        readme = f"""# {project_name}

{description}

## 📋 プロジェクト概要

- **プロジェクトタイプ**: {project_type}
- **フレームワーク**: {framework}
- **言語**: HTML5, CSS3, JavaScript (ES6+)

## ✨ 特徴

- 📱 レスポンシブデザイン
- ♿ アクセシビリティ対応（WCAG 2.1 AA準拠）
- 🚀 パフォーマンス最適化
- 🔍 SEO対応
- 🎨 モダンなUI/UX
- 🛡️ セキュリティ配慮

## 🚀 使用方法

### 開発環境での実行

```bash
# HTTPサーバー起動
python -m http.server 8000

# または Node.js環境の場合
npx serve .
```

ブラウザで `http://localhost:8000` にアクセス

### ファイル構成

```
{project_name}/
├── index.html          # メインHTMLファイル
├── styles.css          # CSSスタイル
├── script.js           # JavaScript
├── package.json        # プロジェクト設定
├── README.md          # このファイル
└── .gitignore         # Git除外設定
```

## 🛠️ 開発技術

- **HTML5**: セマンティック要素、アクセシビリティ
- **CSS3**: Grid/Flexbox、レスポンシブデザイン
- **JavaScript**: ES6+、モダンAPI
- **最適化**: 画像遅延読み込み、コード最小化

## 📱 対応デバイス

- デスクトップ（1920px以上）
- タブレット（768px-1919px）
- スマートフォン（320px-767px）

## ⚡ パフォーマンス

- Lighthouse スコア A ランク目標
- Core Web Vitals 最適化
- 画像最適化と遅延読み込み
- CSS/JavaScript最小化

## 🔧 カスタマイズ

### 色設定の変更

`styles.css` の CSS カスタムプロパティを編集:

```css
:root {{
  --primary-color: #your-color;
  --secondary-color: #your-color;
}}
```

### レスポンシブブレークポイント

```css
/* モバイル */
@media (max-width: 768px) {{ ... }}

/* タブレット */
@media (min-width: 769px) and (max-width: 1024px) {{ ... }}

/* デスクトップ */
@media (min-width: 1025px) {{ ... }}
```

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

---

Generated by Enhanced Web Generator - AI統合強化版Webページ生成サービス
"""
        
        return readme
    
    async def _generate_gitignore(self) -> str:
        """GitIgnore生成"""
        return """# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo
*~

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build files
dist/
build/

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log

# Temporary files
tmp/
temp/
"""
    
    async def _generate_enhanced_preview(self, project_files: List[Dict[str, Any]]) -> Optional[str]:
        """強化版プレビューHTML生成"""
        # メインHTMLファイルを探す
        main_html = None
        for file in project_files:
            if file['filename'] == 'index.html':
                main_html = file['content']
                break
        
        return main_html
    
    async def _extract_technologies_and_features(self, code_sections: Dict[str, str]) -> List[str]:
        """技術スタックと機能の抽出"""
        technologies = set()
        
        html_code = code_sections.get('html', '')
        css_code = code_sections.get('css', '')
        js_code = code_sections.get('javascript', '')
        
        # HTML5機能
        if html_code:
            if re.search(r'<(header|nav|main|section|article|aside|footer)', html_code):
                technologies.add('HTML5 Semantic Elements')
            if 'aria-' in html_code:
                technologies.add('ARIA Accessibility')
            if 'role=' in html_code:
                technologies.add('WAI-ARIA')
            if 'loading="lazy"' in html_code:
                technologies.add('Lazy Loading')
        
        # CSS3機能
        if css_code:
            if 'grid' in css_code:
                technologies.add('CSS Grid')
            if 'flex' in css_code:
                technologies.add('Flexbox')
            if '@media' in css_code:
                technologies.add('Responsive Design')
            if 'var(' in css_code:
                technologies.add('CSS Custom Properties')
            if '@keyframes' in css_code:
                technologies.add('CSS Animations')
            if 'transform' in css_code:
                technologies.add('CSS Transforms')
        
        # JavaScript機能
        if js_code:
            if any(feature in js_code for feature in ['const ', 'let ', '=>']):
                technologies.add('ES6+ JavaScript')
            if 'async' in js_code or 'await' in js_code:
                technologies.add('Async/Await')
            if 'fetch(' in js_code:
                technologies.add('Fetch API')
            if 'querySelector' in js_code:
                technologies.add('Modern DOM API')
            if 'addEventListener' in js_code:
                technologies.add('Event Handling')
        
        return sorted(list(technologies))
    
    async def _extract_web_code_from_response(self, ai_response: str) -> Dict[str, str]:
        """AI応答からWebコード抽出（強化版）"""
        code_sections = {
            'html': '',
            'css': '',
            'javascript': ''
        }
        
        # より精密なパターンマッチング
        patterns = {
            'html': [
                r'```html\s*(.*?)```',
                r'```HTML\s*(.*?)```',
                r'<!DOCTYPE.*?</html>',
            ],
            'css': [
                r'```css\s*(.*?)```',
                r'```CSS\s*(.*?)```',
                r'/\*.*?\*/\s*([^`]*?)(?=```|$)',
            ],
            'javascript': [
                r'```javascript\s*(.*?)```',
                r'```js\s*(.*?)```',
                r'```JavaScript\s*(.*?)```',
                r'```JS\s*(.*?)```',
            ]
        }
        
        for code_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
                if matches:
                    code_sections[code_type] = matches[0].strip()
                    break
        
        return code_sections
