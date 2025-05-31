"""
Web プログラムジェネレーター

HTML/CSS/JavaScript Webサイト/アプリケーション生成機能を提供します。
AI統合とEnhanced Web Generator連携に対応。
"""

import re
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from data.models.job import JobInput, GenerationResult
from services.program_generator.base import BaseProgramGenerator

logger = logging.getLogger(__name__)


class WebGenerator(BaseProgramGenerator):
    """
    Web プログラムジェネレーター
    
    HTML/CSS/JavaScriptを使ったWebサイト/アプリケーション生成機能を提供します。
    レスポンシブデザイン、アクセシビリティ対応、モダンなWeb技術を活用した
    プロジェクト構造の作成などを行います。
    
    Enhanced Web Generator連携により、AI駆動の高品質生成も可能です。
    """
    
    def __init__(self):
        super().__init__()
        self.language = 'web'
        self.file_extension = '.html'
        self.enhanced_generator = None  # Enhanced Web Generator への参照
        
    async def initialize(self) -> bool:
        """Web Generator初期化"""
        try:
            # Enhanced Web Generator初期化を試行
            try:
                from .enhanced_web_generator import EnhancedWebGenerator
                self.enhanced_generator = EnhancedWebGenerator()
                await self.enhanced_generator.initialize()
                logger.info("Enhanced Web Generator 統合成功")
            except Exception as e:
                logger.warning(f"Enhanced Web Generator 統合失敗: {str(e)}")
                self.enhanced_generator = None
            
            return True
        except Exception as e:
            logger.error(f"Web Generator 初期化エラー: {str(e)}")
            return False
    
    async def generate(self, job_input: JobInput) -> GenerationResult:
        """Web プログラム生成のメイン処理"""
        try:
            # AI強化生成を優先的に試行
            if self.enhanced_generator and job_input.parameters.get('use_ai', True):
                try:
                    logger.info(f"Enhanced Web Generator で生成試行: {job_input.job_id}")
                    return await self.enhanced_generator.generate(job_input)
                except Exception as e:
                    logger.warning(f"Enhanced生成失敗、基本生成にフォールバック: {str(e)}")
            
            # 基本生成処理
            return await self._generate_basic(job_input)
            
        except Exception as e:
            logger.error(f"Web生成エラー: {job_input.job_id}, エラー: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=f"Web生成エラー: {str(e)}"
            )
    
    async def _generate_basic(self, job_input: JobInput) -> GenerationResult:
        """基本版Web生成処理"""
        try:
            if not await self.validate_input(job_input):
                return GenerationResult(
                    success=False,
                    error_message="入力検証エラー"
                )
            
            logger.info(f"基本版Web生成開始: {job_input.job_id}")
            
            # テンプレートベース生成
            template_content = await self._generate_from_template(job_input)
            
            # プロジェクトファイル作成
            project_files = await self._create_basic_project_files(job_input, template_content)
            
            # ZIPパッケージ作成
            zip_path = await self._create_zip_package(job_input.job_id, project_files)
            
            # プレビュー生成
            preview_html = self._get_main_html_content(project_files)
            
            result = GenerationResult(
                success=True,
                content=template_content.get('html', ''),
                files=project_files,
                download_url=zip_path,
                preview_html=preview_html,
                metadata={
                    'language': 'web',
                    'generator_type': 'basic',
                    'project_type': job_input.parameters.get('project_type', 'static_site'),
                    'file_count': len(project_files),
                    'template_used': self._get_template_name(job_input),
                    'responsive': True,
                    'accessibility': True,
                    'ai_powered': False
                }
            )
            
            logger.info(f"基本版Web生成完了: {job_input.job_id}")
            return result
            
        except Exception as e:
            logger.error(f"基本版Web生成エラー: {str(e)}")
            raise
    
    async def validate_input(self, job_input: JobInput) -> bool:
        """Web固有の入力検証"""
        try:
            await super().validate_input(job_input)
            
            # Web固有の検証ロジック
            parameters = job_input.parameters
            
            # プロジェクトタイプの確認
            project_type = parameters.get('project_type', 'static_site')
            valid_types = [
                'static_site', 'landing_page', 'portfolio', 'blog',
                'dashboard', 'ecommerce', 'spa', 'pwa'
            ]
            
            if project_type not in valid_types:
                logger.warning(f"未知のプロジェクトタイプ: {project_type}, 'static_site'を使用")
                parameters['project_type'] = 'static_site'
            
            return True
            
        except Exception as e:
            logger.error(f"Web入力検証エラー: {str(e)}")
            return False
    
    async def _generate_from_template(self, job_input: JobInput) -> Dict[str, str]:
        """テンプレートベースのWeb生成"""
        try:
            template_name = self._get_template_name(job_input)
            template_content = await self._load_template(template_name)
            
            # パラメータの取得
            parameters = job_input.parameters
            description = parameters.get('description', 'Webサイト')
            title = parameters.get('title', description)
            
            # テンプレート変数の置換
            html_content = template_content.format(
                title=title,
                description=description
            )
            
            # 基本的なCSS/JS生成
            css_content = self._generate_basic_css(parameters)
            js_content = self._generate_basic_js(parameters)
            
            return {
                'html': html_content,
                'css': css_content,
                'javascript': js_content
            }
            
        except Exception as e:
            logger.error(f"テンプレート生成エラー: {str(e)}")
            return self._get_fallback_content(job_input)
    
    def _generate_basic_css(self, parameters: Dict[str, Any]) -> str:
        """基本的なCSS生成"""
        color_scheme = parameters.get('color_scheme', 'modern')
        
        css_content = """/* CSS Reset & Modern Defaults */
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
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    -webkit-font-smoothing: antialiased;
}

.container {
    width: 90%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

/* Header */
header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem 0;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

/* Main Content */
main {
    padding: 3rem 0;
    min-height: 60vh;
}

/* Footer */
footer {
    background-color: #f8f9fa;
    padding: 2rem 0;
    text-align: center;
    border-top: 1px solid #e9ecef;
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        width: 95%;
        padding: 0.5rem;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    main {
        padding: 2rem 0;
    }
}

@media (max-width: 480px) {
    header h1 {
        font-size: 1.5rem;
    }
    
    body {
        font-size: 14px;
    }
}
"""
        return css_content
    
    def _generate_basic_js(self, parameters: Dict[str, Any]) -> str:
        """基本的なJavaScript生成"""
        js_content = """// Modern JavaScript with DOM manipulation
document.addEventListener('DOMContentLoaded', function() {
    console.log('Webサイトが読み込まれました');
    
    // スムーススクロール対応
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // アクセシビリティ強化
    const focusableElements = document.querySelectorAll('button, a, input, textarea, select');
    focusableElements.forEach(element => {
        element.addEventListener('focus', function() {
            this.style.outline = '2px solid #667eea';
        });
        
        element.addEventListener('blur', function() {
            this.style.outline = '';
        });
    });
    
    // 基本的なイベントハンドリング
    const header = document.querySelector('header');
    if (header) {
        header.addEventListener('click', function() {
            console.log('ヘッダーがクリックされました');
        });
    }
});

// ユーティリティ関数
function fadeIn(element, duration = 300) {
    element.style.opacity = 0;
    element.style.display = 'block';
    
    const start = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = elapsed / duration;
        
        if (progress < 1) {
            element.style.opacity = progress;
            requestAnimationFrame(animate);
        } else {
            element.style.opacity = 1;
        }
    }
    
    requestAnimationFrame(animate);
}

function fadeOut(element, duration = 300) {
    const start = performance.now();
    const startOpacity = parseFloat(element.style.opacity) || 1;
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = elapsed / duration;
        
        if (progress < 1) {
            element.style.opacity = startOpacity * (1 - progress);
            requestAnimationFrame(animate);
        } else {
            element.style.opacity = 0;
            element.style.display = 'none';
        }
    }
    
    requestAnimationFrame(animate);
}
"""
        return js_content
    
    async def _create_basic_project_files(self, job_input: JobInput, template_content: Dict[str, str]) -> List[Dict[str, Any]]:
        """基本版プロジェクトファイル生成"""
        files = []
        
        # メインHTMLファイル
        if template_content.get('html'):
            files.append({
                'filename': 'index.html',
                'content': template_content['html'],
                'type': 'html',
                'line_count': len(template_content['html'].split('\n'))
            })
        
        # CSSファイル
        if template_content.get('css'):
            files.append({
                'filename': 'styles.css',
                'content': template_content['css'],
                'type': 'css',
                'line_count': len(template_content['css'].split('\n'))
            })
        
        # JavaScriptファイル
        if template_content.get('javascript'):
            files.append({
                'filename': 'script.js',
                'content': template_content['javascript'],
                'type': 'javascript',
                'line_count': len(template_content['javascript'].split('\n'))
            })
        
        # README.md
        readme_content = await self._generate_readme(job_input)
        files.append({
            'filename': 'README.md',
            'content': readme_content,
            'type': 'markdown',
            'line_count': len(readme_content.split('\n'))
        })
        
        # .gitignore
        gitignore_content = self._generate_gitignore()
        files.append({
            'filename': '.gitignore',
            'content': gitignore_content,
            'type': 'text',
            'line_count': len(gitignore_content.split('\n'))
        })
        
        return files
    
    def _get_template_name(self, job_input: JobInput) -> str:
        """プロジェクトタイプに基づいてテンプレート名を決定"""
        project_type = job_input.parameters.get('project_type', 'static_site')
        
        template_mapping = {
            'static_site': 'web_static',
            'landing_page': 'web_landing',
            'portfolio': 'web_portfolio',
            'blog': 'web_blog',
            'dashboard': 'web_dashboard',
            'ecommerce': 'web_ecommerce',
            'spa': 'web_spa',
            'pwa': 'web_pwa'
        }
        
        return template_mapping.get(project_type, 'web_static')
    
    async def _load_template(self, template_name: str) -> str:
        """テンプレート読み込み"""
        try:
            # テンプレートデータを読み込み
            template_data = self._load_template_from_json(template_name)
            
            if template_data and 'template' in template_data:
                logger.info(f"Webテンプレート読み込み成功: {template_name}")
                return template_data['template']
            else:
                logger.warning(f"Webテンプレートが見つかりません: {template_name}")
                return self._get_default_template()
                
        except Exception as e:
            logger.error(f"Webテンプレート読み込みエラー: {e}")
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """デフォルトのWebテンプレート"""
        return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <p class="subtitle">{description}</p>
        </div>
    </header>

    <main>
        <div class="container">
            <section class="content">
                <h2>ようこそ</h2>
                <p>{description}</p>
                <p>このWebサイトは最新の技術を使用して構築されており、レスポンシブデザイン、アクセシビリティ、パフォーマンス最適化に配慮しています。</p>
            </section>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2023 {title}. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    def _get_fallback_content(self, job_input: JobInput) -> Dict[str, str]:
        """フォールバック用コンテンツ"""
        parameters = job_input.parameters
        title = parameters.get('title', parameters.get('description', 'Webサイト'))
        description = parameters.get('description', 'モダンなWebサイト')
        
        html = self._get_default_template().format(title=title, description=description)
        css = self._generate_basic_css(parameters)
        js = self._generate_basic_js(parameters)
        
        return {
            'html': html,
            'css': css,
            'javascript': js
        }
    
    def _get_main_html_content(self, project_files: List[Dict[str, Any]]) -> Optional[str]:
        """メインHTMLファイルの内容を取得"""
        for file in project_files:
            if file['filename'] == 'index.html':
                return file['content']
        return None
    
    async def _generate_readme(self, job_input: JobInput) -> str:
        """README.md 生成"""
        description = job_input.parameters.get('description', '')
        project_type = job_input.parameters.get('project_type', 'static_site')
        
        readme_content = f"""# {job_input.job_id or 'Web Project'}

## 概要
{description}

## プロジェクトタイプ
{project_type}

## 技術スタック
- HTML5
- CSS3 (Flexbox, Grid, Responsive Design)
- JavaScript (ES6+)

## 特徴
- 📱 レスポンシブデザイン
- ♿ アクセシビリティ対応
- 🚀 パフォーマンス最適化
- 🎨 モダンなUI/UX
- 📱 モバイルファースト

## 使用方法

### ローカル環境での実行
1. プロジェクトファイルをダウンロード・展開
2. `index.html` をブラウザで開く

### 開発サーバーでの実行（推奨）
```bash
# Python 3を使用
python -m http.server 8000

# Node.jsを使用
npx http-server .
```

ブラウザで http://localhost:8000 にアクセス

## ファイル構成
```
{job_input.job_id or 'web-project'}/
├── index.html          # メインHTMLファイル
├── styles.css          # CSSスタイル
├── script.js           # JavaScript
├── README.md          # このファイル
└── .gitignore         # Git除外設定
```

## カスタマイズ
- `styles.css`: デザインの変更
- `script.js`: 機能の追加
- `index.html`: 構造の変更

## ライセンス
MIT License
"""
        
        return readme_content
    
    def _generate_gitignore(self) -> str:
        """GitIgnore生成"""
        return """.DS_Store
Thumbs.db
*.log
node_modules/
dist/
.env
.vscode/
.idea/
*.swp
*.swo
*~
"""

    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """利用可能なWebテンプレートの一覧を取得"""
        return [
            {
                'name': 'web_static',
                'display_name': '静的サイト',
                'description': '基本的な静的Webサイト',
                'project_type': 'static_site'
            },
            {
                'name': 'web_landing',
                'display_name': 'ランディングページ',
                'description': '効果的なランディングページ',
                'project_type': 'landing_page'
            },
            {
                'name': 'web_portfolio',
                'display_name': 'ポートフォリオ',
                'description': '個人・作品紹介サイト',
                'project_type': 'portfolio'
            },
            {
                'name': 'web_dashboard',
                'display_name': 'ダッシュボード',
                'description': 'データ表示・管理画面',
                'project_type': 'dashboard'
            },
            {
                'name': 'web_spa',
                'display_name': 'SPA',
                'description': 'シングルページアプリケーション',
                'project_type': 'spa'
            },
            {
                'name': 'web_pwa',
                'display_name': 'PWA',
                'description': 'Progressive Web Application',
                'project_type': 'pwa'
            }
        ]
    
    async def get_generation_preview(self, job_input: JobInput) -> Dict[str, Any]:
        """生成プレビュー情報を取得"""
        project_type = job_input.parameters.get('project_type', 'static_site')
        
        return {
            'files': ['index.html', 'styles.css', 'script.js', 'README.md', '.gitignore'],
            'structure': {
                'main_file': 'index.html',
                'project_type': project_type,
                'language': 'web',
                'technologies': ['HTML5', 'CSS3', 'JavaScript']
            },
            'requirements': ['モダンブラウザでの表示', 'HTTPサーバーでの実行推奨'],
            'template': self._get_template_name(job_input)
        }
