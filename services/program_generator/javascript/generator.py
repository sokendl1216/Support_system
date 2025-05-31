"""
JavaScript プログラムジェネレーター

JavaScript/Node.js言語に特化したプログラム生成機能を提供します。
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from data.models.job import JobInput, GenerationResult
from services.program_generator.base import BaseProgramGenerator

logger = logging.getLogger(__name__)


class JavaScriptGenerator(BaseProgramGenerator):
    """
    JavaScript プログラムジェネレーター
    
    JavaScript/Node.js言語に特化したコード生成機能を提供します。
    npm依存関係の自動検出、package.json生成、
    適切なプロジェクト構造の作成などを行います。
    """
    
    def __init__(self):
        super().__init__()
        self.language = 'javascript'
        self.file_extension = '.js'
        
    async def validate_input(self, job_input: JobInput) -> bool:
        """JavaScript固有の入力検証"""
        try:
            await super().validate_input(job_input)
            
            # JavaScript固有の検証ロジック
            parameters = job_input.parameters
            
            # プロジェクトタイプの確認
            project_type = parameters.get('project_type', 'script')
            valid_types = [
                'script', 'cli', 'express_app', 'react_app', 'vue_app',
                'api', 'electron_app', 'chrome_extension', 'discord_bot'
            ]
            
            if project_type not in valid_types:
                logger.warning(f"未知のプロジェクトタイプ: {project_type}, 'script'を使用")
                parameters['project_type'] = 'script'
            
            return True
            
        except Exception as e:
            logger.error(f"JavaScript入力検証エラー: {str(e)}")
            return False
    
    async def generate(self, job_input: JobInput) -> GenerationResult:
        """JavaScript プログラム生成のメイン処理"""
        try:
            if not await self.validate_input(job_input):
                return GenerationResult(
                    success=False,
                    error_message="入力検証エラー"
                )
            
            logger.info(f"JavaScript生成開始: {job_input.job_id}")
            
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
            preview_html = await self._generate_html_preview(project_files, 'javascript')
            
            # 依存関係抽出
            dependencies = await self._extract_js_dependencies(extracted_code)
            
            result = GenerationResult(
                success=True,
                content=extracted_code,
                files=project_files,
                download_url=zip_path,
                preview_html=preview_html,
                metadata={
                    'language': 'javascript',
                    'project_type': job_input.parameters.get('project_type', 'script'),
                    'dependencies': dependencies,
                    'file_count': len(project_files),
                    'template_used': self._get_template_name(job_input)
                }
            )
            
            logger.info(f"JavaScript生成完了: {job_input.job_id}")
            return result
            
        except Exception as e:
            logger.error(f"JavaScript生成エラー: {job_input.job_id}, エラー: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=f"JavaScript生成エラー: {str(e)}"
            )
    
    async def _prepare_generation_request(self, job_input: JobInput) -> Dict[str, Any]:
        """JavaScript生成用のリクエストを準備"""
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
            'language': 'JavaScript',
            'runtime': 'Node.js' if project_type in ['cli', 'express_app', 'api'] else 'Browser',
            'requirements': parameters.get('requirements', []),
            'features': parameters.get('features', []),
            'complexity': parameters.get('complexity', 'medium'),
            'template': template_content,
            'guidelines': self._get_javascript_guidelines()
        }
        
        return {
            'prompt_template': 'javascript_generation',
            'context': prompt_context,
            'max_tokens': 8000,
            'temperature': 0.7
        }
    
    def _get_template_name(self, job_input: JobInput) -> str:
        """プロジェクトタイプに基づいてテンプレート名を決定"""
        project_type = job_input.parameters.get('project_type', 'script')
        
        template_mapping = {
            'script': 'javascript_script',
            'cli': 'nodejs_cli',
            'express_app': 'nodejs_express',
            'react_app': 'react_app',
            'vue_app': 'vue_app',
            'api': 'nodejs_api',
            'electron_app': 'electron_app',
            'chrome_extension': 'chrome_extension',
            'discord_bot': 'discord_bot'
        }
        
        return template_mapping.get(project_type, 'javascript_script')
    
    def _get_javascript_guidelines(self) -> List[str]:
        """JavaScript コーディングガイドライン"""
        return [
            "ES6+の現代的なJavaScript構文を使用してください",
            "適切なエラーハンドリングを実装してください（try-catch, Promise.catch）",
            "JSDocコメントを関数に記載してください",
            "const/letを適切に使い分けてください",
            "アロー関数を適切に使用してください",
            "非同期処理はasync/awaitを優先してください",
            "セキュリティを考慮した実装を行ってください",
            "package.jsonに適切な依存関係を記載してください",
            "README.mdに使用方法を記載してください",
            "環境変数を適切に使用してください"
        ]
    
    async def _extract_js_dependencies(self, code: str) -> List[str]:
        """JavaScriptコードから必要なnpmパッケージを抽出"""
        try:
            dependencies = []
            dev_dependencies = []
            
            # import/requireの正規表現パターン
            import_patterns = [
                r"import\s+.*?from\s+['\"]([^'\"]+)['\"]",
                r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
                r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
            ]
            
            # Node.jsの組み込みモジュールは除外
            builtin_modules = {
                'fs', 'path', 'os', 'url', 'http', 'https', 'crypto',
                'events', 'stream', 'util', 'querystring', 'zlib',
                'buffer', 'child_process', 'cluster', 'dgram', 'dns',
                'net', 'readline', 'repl', 'tls', 'tty', 'vm', 'worker_threads'
            }
            
            for pattern in import_patterns:
                matches = re.findall(pattern, code)
                for match in matches:
                    # 相対パスやローカルファイルは除外
                    if not match.startswith('.') and not match.startswith('/'):
                        package_name = match.split('/')[0]  # スコープパッケージ対応
                        if package_name.startswith('@'):
                            package_name = match.split('/')[0] + '/' + match.split('/')[1]
                        
                        if package_name not in builtin_modules:
                            if package_name not in dependencies:
                                dependencies.append(package_name)
            
            # 一般的なパッケージの推奨バージョン
            version_mapping = {
                'express': '^4.18.0',
                'react': '^18.0.0',
                'vue': '^3.2.0',
                'axios': '^1.3.0',
                'lodash': '^4.17.0',
                'moment': '^2.29.0',
                'dayjs': '^1.11.0',
                'joi': '^17.7.0',
                'bcrypt': '^5.1.0',
                'jsonwebtoken': '^9.0.0',
                'mongoose': '^7.0.0',
                'sequelize': '^6.28.0',
                'socket.io': '^4.6.0',
                'discord.js': '^14.7.0',
                'electron': '^22.0.0',
                'dotenv': '^16.0.0',
                'cors': '^2.8.0',
                'helmet': '^6.0.0',
                'morgan': '^1.10.0',
                'nodemon': '^2.0.0',
                'jest': '^29.0.0',
                'eslint': '^8.30.0',
                'prettier': '^2.8.0'
            }
            
            # 開発依存関係を特定
            dev_packages = {'nodemon', 'jest', 'eslint', 'prettier', '@types/', 'typescript'}
            
            # バージョン付き依存関係を生成
            formatted_deps = {}
            formatted_dev_deps = {}
            
            for dep in dependencies:
                version = version_mapping.get(dep, '^1.0.0')
                
                # 開発依存関係かチェック
                is_dev = any(dev_pkg in dep for dev_pkg in dev_packages)
                
                if is_dev:
                    formatted_dev_deps[dep] = version
                else:
                    formatted_deps[dep] = version
            
            return {
                'dependencies': formatted_deps,
                'devDependencies': formatted_dev_deps
            }
            
        except Exception as e:
            logger.error(f"dependencies抽出エラー: {str(e)}")
            return {'dependencies': {}, 'devDependencies': {}}
    
    async def _create_project_files(self, job_input: JobInput, code: str) -> List[Dict[str, Any]]:
        """JavaScriptプロジェクトファイルを作成"""
        try:
            files = []
            project_type = job_input.parameters.get('project_type', 'script')
            dependencies = await self._extract_js_dependencies(code)
            
            # メインコードファイル
            main_filename = self._get_main_filename(project_type)
            files.append({
                'filename': main_filename,
                'content': code,
                'type': 'javascript',
                'line_count': len(code.split('\n'))
            })
            
            # package.json
            package_json = await self._generate_package_json(job_input, dependencies)
            files.append({
                'filename': 'package.json',
                'content': package_json,
                'type': 'json',
                'line_count': len(package_json.split('\n'))
            })
            
            # README.md
            readme_content = await self._generate_readme(job_input, dependencies)
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
            'script': 'index.js',
            'cli': 'cli.js',
            'express_app': 'app.js',
            'react_app': 'src/App.js',
            'vue_app': 'src/App.vue',
            'api': 'server.js',
            'electron_app': 'main.js',
            'chrome_extension': 'content.js',
            'discord_bot': 'bot.js'
        }
        return filename_mapping.get(project_type, 'index.js')
    
    async def _generate_package_json(self, job_input: JobInput, dependencies: Dict[str, Any]) -> str:
        """package.json を生成"""
        import json
        
        project_name = job_input.job_id or 'javascript-project'
        project_type = job_input.parameters.get('project_type', 'script')
        description = job_input.parameters.get('description', '')
        main_filename = self._get_main_filename(project_type)
        
        package_data = {
            "name": project_name.lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": description,
            "main": main_filename,
            "scripts": self._get_npm_scripts(project_type),
            "keywords": self._get_keywords(project_type),
            "author": "",
            "license": "MIT"
        }
        
        # 依存関係を追加
        if dependencies.get('dependencies'):
            package_data["dependencies"] = dependencies['dependencies']
        
        if dependencies.get('devDependencies'):
            package_data["devDependencies"] = dependencies['devDependencies']
        
        # プロジェクトタイプ固有の設定
        if project_type == 'cli':
            package_data["bin"] = {
                project_name: f"./{main_filename}"
            }
            package_data["preferGlobal"] = True
        
        return json.dumps(package_data, indent=2, ensure_ascii=False)
    
    def _get_npm_scripts(self, project_type: str) -> Dict[str, str]:
        """プロジェクトタイプに応じたnpmスクリプトを取得"""
        base_scripts = {
            "start": "node index.js",
            "test": "echo \"Error: no test specified\" && exit 1"
        }
        
        if project_type in ['express_app', 'api', 'discord_bot']:
            base_scripts.update({
                "dev": "nodemon index.js",
                "start": "node index.js"
            })
        
        if project_type == 'react_app':
            base_scripts.update({
                "dev": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            })
        
        if project_type == 'vue_app':
            base_scripts.update({
                "dev": "vue-cli-service serve",
                "build": "vue-cli-service build",
                "lint": "vue-cli-service lint"
            })
        
        return base_scripts
    
    def _get_keywords(self, project_type: str) -> List[str]:
        """プロジェクトタイプに応じたキーワードを取得"""
        keyword_mapping = {
            'script': ['javascript', 'script'],
            'cli': ['cli', 'command-line', 'tool'],
            'express_app': ['express', 'web', 'server'],
            'react_app': ['react', 'frontend', 'ui'],
            'vue_app': ['vue', 'frontend', 'ui'],
            'api': ['api', 'rest', 'server'],
            'electron_app': ['electron', 'desktop', 'app'],
            'chrome_extension': ['chrome', 'extension', 'browser'],
            'discord_bot': ['discord', 'bot', 'automation']
        }
        return keyword_mapping.get(project_type, ['javascript'])
    
    async def _generate_readme(self, job_input: JobInput, dependencies: Dict[str, Any]) -> str:
        """README.md を生成"""
        description = job_input.parameters.get('description', '')
        project_type = job_input.parameters.get('project_type', 'script')
        main_filename = self._get_main_filename(project_type)
        
        readme_content = f"""# {job_input.job_id or 'JavaScript Project'}

## 概要
{description}

## 必要要件
- Node.js 16.0以上
- npm または yarn

## インストール

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. 依存関係のインストール
```bash
npm install
# または
yarn install
```

## 使用方法
```bash
npm start
# または
yarn start
```
"""
        
        # プロジェクトタイプ固有の使用方法
        if project_type == 'cli':
            readme_content += """
### CLIツールとしてインストール
```bash
npm install -g .
```

### グローバルコマンドとして実行
```bash
your-command-name [options]
```
"""
        
        elif project_type in ['express_app', 'api']:
            readme_content += """
### 開発モード
```bash
npm run dev
```

サーバーは http://localhost:3000 で起動します。
"""
        
        readme_content += f"""
## プロジェクト構造
```
.
├── {main_filename}          # メインプログラム
├── package.json            # プロジェクト設定
├── README.md              # このファイル
"""
        
        if dependencies.get('dependencies') or dependencies.get('devDependencies'):
            readme_content += "├── node_modules/          # 依存関係（自動生成）\n"
        
        readme_content += """└── ...
```

## 開発

### 依存関係の追加
```bash
npm install <package-name>
# または
yarn add <package-name>
```

### 開発依存関係の追加
```bash
npm install --save-dev <package-name>
# または
yarn add --dev <package-name>
```

## 注意事項
- 本番環境では適切な環境変数を設定してください
- セキュリティ設定を確認してください

## ライセンス
MIT License
"""
        
        return readme_content
    
    async def _create_additional_files(self, job_input: JobInput, project_type: str) -> List[Dict[str, Any]]:
        """プロジェクトタイプに応じた追加ファイルを作成"""
        files = []
        
        try:
            # 共通の設定ファイル
            files.append({
                'filename': '.gitignore',
                'content': '''node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
dist/
build/
*.log
.DS_Store
.vscode/
.idea/
''',
                'type': 'gitignore',
                'line_count': 15
            })
            
            # ESLint設定
            if project_type in ['express_app', 'api', 'cli']:
                files.append({
                    'filename': '.eslintrc.js',
                    'content': '''module.exports = {
  env: {
    node: true,
    es2021: true,
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module',
  },
  rules: {
    'no-console': 'warn',
    'no-unused-vars': 'error',
  },
};
''',
                    'type': 'javascript',
                    'line_count': 14
                })
            
            # 環境変数テンプレート
            if project_type in ['express_app', 'api', 'discord_bot']:
                files.append({
                    'filename': '.env.example',
                    'content': '''# 環境変数のサンプル
# 本番環境では適切な値を設定してください

PORT=3000
NODE_ENV=development

# データベース接続情報
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=myapp
# DB_USER=user
# DB_PASS=password

# API キー
# API_KEY=your_api_key_here
''',
                    'type': 'env',
                    'line_count': 12
                })
            
            # Dockerfile（API、Express用）
            if project_type in ['express_app', 'api']:
                files.append({
                    'filename': 'Dockerfile',
                    'content': '''FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

USER node

CMD ["npm", "start"]
''',
                    'type': 'dockerfile',
                    'line_count': 12
                })
            
        except Exception as e:
            logger.error(f"追加ファイル作成エラー: {str(e)}")
        
        return files
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """利用可能なJavaScriptテンプレートの一覧を取得"""
        return [
            {
                'name': 'javascript_script',
                'display_name': 'JavaScriptスクリプト',
                'description': '基本的なJavaScriptスクリプト',
                'project_type': 'script'
            },
            {
                'name': 'nodejs_cli',
                'display_name': 'Node.js CLIツール',
                'description': 'コマンドライン実行可能なツール',
                'project_type': 'cli'
            },
            {
                'name': 'nodejs_express',
                'display_name': 'Express Webアプリ',
                'description': 'ExpressベースのWebアプリケーション',
                'project_type': 'express_app'
            },
            {
                'name': 'nodejs_api',
                'display_name': 'Node.js API',
                'description': 'RESTful APIサーバー',
                'project_type': 'api'
            },
            {
                'name': 'react_app',
                'display_name': 'React アプリ',
                'description': 'Reactベースのフロントエンドアプリ',
                'project_type': 'react_app'
            },
            {
                'name': 'discord_bot',
                'display_name': 'Discord Bot',
                'description': 'Discord.jsを使ったBot',
                'project_type': 'discord_bot'
            }
        ]
    
    async def get_generation_preview(self, job_input: JobInput) -> Dict[str, Any]:
        """生成プレビュー情報を取得"""
        project_type = job_input.parameters.get('project_type', 'script')
        description = job_input.parameters.get('description', '')
        
        return {
            'language': 'javascript',
            'project_type': project_type,
            'description': description,
            'estimated_files': self._estimate_file_count(project_type),
            'dependencies': self._get_expected_dependencies(project_type),
            'requirements': ['Node.js 14以上（一部プロジェクト）', 'モダンブラウザ（クライアントサイド）'],
            'template': self._get_template_name(job_input)
        }

    async def _load_template(self, template_name: str) -> Optional[str]:
        """
        JSONテンプレートファイルからテンプレート内容を読み込み
        
        Args:
            template_name: テンプレート名（例: 'javascript_script', 'nodejs_cli'）
            
        Returns:
            Optional[str]: テンプレート内容、見つからない場合はNone
        """
        try:
            # JSONテンプレートデータを読み込み
            template_data = self._load_template_from_json(template_name)
            
            if template_data and 'template' in template_data:
                logger.info(f"JavaScriptテンプレート読み込み成功: {template_name}")
                return template_data['template']
            else:
                logger.warning(f"JavaScriptテンプレートが見つかりません: {template_name}")
                # フォールバック用のデフォルトテンプレート
                return self._get_default_template()
                
        except Exception as e:
            logger.error(f"JavaScriptテンプレート読み込みエラー: {e}")
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """デフォルトのJavaScriptテンプレートを返す"""
        return '''/**
 * {description}
 * JavaScript スクリプト
 */

console.log('Hello, World!');

// メイン処理
function main() {
    try {
        // ここにメインロジックを実装
        console.log('JavaScriptプログラムが正常に開始されました');
        
    } catch (error) {
        console.error('エラーが発生しました:', error);
    }
}

// 実行
main();
'''
    
    def _estimate_file_count(self, project_type: str) -> List[str]:
        """プロジェクトタイプに基づいてファイル数を推定"""
        base_files = ['main.js', 'package.json', 'README.md', '.gitignore']
        
        if project_type == 'web_app':
            return ['index.html', 'style.css', 'script.js', 'package.json', 'README.md', '.gitignore']
        elif project_type == 'api':
            return ['server.js', 'package.json', 'README.md', '.gitignore', '.env.example']
        elif project_type == 'cli':
            return ['cli.js', 'package.json', 'README.md', '.gitignore']
        elif project_type == 'react_app':
            return ['src/App.js', 'src/index.js', 'public/index.html', 'package.json', 'README.md', '.gitignore']
        else:
            return base_files
    
    def _get_expected_dependencies(self, project_type: str) -> List[str]:
        """プロジェクトタイプに応じた期待される依存関係を取得"""
        dependencies_map = {
            'script': [],
            'cli': ['commander', 'chalk', 'inquirer'],
            'express_app': ['express', 'cors', 'helmet', 'morgan'],
            'api': ['express', 'cors', 'helmet', 'joi'],
            'react_app': ['react', 'react-dom', 'react-scripts'],
            'vue_app': ['vue', '@vue/cli-service'],
            'discord_bot': ['discord.js', 'dotenv'],
            'electron_app': ['electron', 'electron-builder'],
            'scraper': ['puppeteer', 'cheerio', 'axios']
        }
        return dependencies_map.get(project_type, [])
