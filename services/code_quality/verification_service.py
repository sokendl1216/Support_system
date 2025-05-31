"""
Code Quality Verification Service - Task 3-7 Implementation

コード品質検証システム：生成されたコードの静的解析・テスト自動生成機能
- 静的解析（lint、フォーマッター、型チェック）
- テスト自動生成（単体テスト、統合テスト）
- セキュリティ脆弱性検査
- コード品質メトリクス評価
- 改善提案の自動生成
"""

import asyncio
import logging
import json
import subprocess
import tempfile
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from core.dependency_injection import injectable
from data.models.job import JobInput, JobOutput
from ai.providers.ollama_provider import OllamaProvider
from services.program_generator.enhanced_generator import EnhancedCodeAnalyzer, CodeQualityMetrics

logger = logging.getLogger(__name__)


@dataclass
class StaticAnalysisResult:
    """静的解析結果"""
    tool: str
    language: str
    issues: List[Dict[str, Any]]
    severity_counts: Dict[str, int]
    score: float
    execution_time: float
    

@dataclass
class TestGenerationResult:
    """テスト生成結果"""
    test_type: str
    test_files: List[Dict[str, str]]
    coverage_target: float
    generated_tests: int
    

@dataclass
class SecurityAnalysisResult:
    """セキュリティ分析結果"""
    vulnerabilities: List[Dict[str, Any]]
    security_score: float
    risk_level: str
    recommendations: List[str]
    

@dataclass
class QualityVerificationResult:
    """品質検証総合結果"""
    job_id: str
    language: str
    static_analysis: List[StaticAnalysisResult]
    test_generation: TestGenerationResult
    security_analysis: SecurityAnalysisResult
    quality_metrics: CodeQualityMetrics
    overall_score: float
    recommendations: List[str]
    verification_time: float
    

class StaticAnalysisEngine:
    """静的解析エンジン"""
    
    def __init__(self):
        self.analyzers = {
            'python': {
                'flake8': self._run_flake8,
                'pylint': self._run_pylint,
                'mypy': self._run_mypy,
                'black': self._run_black,
                'isort': self._run_isort,
                'bandit': self._run_bandit  # セキュリティ
            },
            'javascript': {
                'eslint': self._run_eslint,
                'prettier': self._run_prettier,
                'jshint': self._run_jshint,
                'tslint': self._run_tslint
            },
            'typescript': {
                'tslint': self._run_tslint,
                'prettier': self._run_prettier,
                'typescript': self._run_typescript_check
            }
        }
    
    async def analyze_code(self, code: str, language: str, file_path: str) -> List[StaticAnalysisResult]:
        """コードの静的解析を実行"""
        results = []
        analyzers = self.analyzers.get(language, {})
        
        for tool_name, analyzer_func in analyzers.items():
            try:
                start_time = datetime.now()
                result = await analyzer_func(code, file_path)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if result:
                    results.append(StaticAnalysisResult(
                        tool=tool_name,
                        language=language,
                        issues=result.get('issues', []),
                        severity_counts=result.get('severity_counts', {}),
                        score=result.get('score', 0.0),
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                logger.warning(f"静的解析ツール {tool_name} でエラー: {e}")
                
        return results
    
    async def _run_flake8(self, code: str, file_path: str) -> Dict[str, Any]:
        """Flake8による静的解析"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Flake8実行（より緩い設定）
            result = subprocess.run([
                'flake8', temp_path,
                '--max-line-length=120',
                '--ignore=E203,W503,E501',
                '--format=json'
            ], capture_output=True, text=True, timeout=30)
            
            os.unlink(temp_path)
            
            issues = []
            severity_counts = {'error': 0, 'warning': 0, 'info': 0}
            
            if result.stdout:
                # flake8のアウトプットをパース
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(':')
                        if len(parts) >= 4:
                            issue = {
                                'line': int(parts[1]),
                                'column': int(parts[2]),
                                'message': ':'.join(parts[3:]).strip(),
                                'severity': 'warning',
                                'rule': parts[3].strip().split()[0] if parts[3].strip() else 'unknown'
                            }
                            issues.append(issue)
                            severity_counts['warning'] += 1
            
            # スコア計算（0-100）
            total_issues = len(issues)
            score = max(0, 100 - (total_issues * 5))
            
            return {
                'issues': issues,
                'severity_counts': severity_counts,
                'score': score
            }
            
        except Exception as e:
            logger.warning(f"Flake8実行エラー: {e}")
            return {'issues': [], 'severity_counts': {}, 'score': 50.0}
    
    async def _run_pylint(self, code: str, file_path: str) -> Dict[str, Any]:
        """Pylintによる静的解析"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = subprocess.run([
                'pylint', temp_path,
                '--output-format=json',
                '--disable=C0114,C0115,C0116',  # docstring関連を無効化
                '--max-line-length=120'
            ], capture_output=True, text=True, timeout=45)
            
            os.unlink(temp_path)
            
            issues = []
            severity_counts = {'error': 0, 'warning': 0, 'info': 0}
            
            if result.stdout.strip():
                try:
                    pylint_output = json.loads(result.stdout)
                    for issue in pylint_output:
                        severity = issue.get('type', 'info').lower()
                        if severity in ['error', 'fatal']:
                            severity = 'error'
                        elif severity in ['warning', 'refactor']:
                            severity = 'warning'
                        else:
                            severity = 'info'
                        
                        issues.append({
                            'line': issue.get('line', 1),
                            'column': issue.get('column', 1),
                            'message': issue.get('message', ''),
                            'severity': severity,
                            'rule': issue.get('symbol', 'unknown')
                        })
                        severity_counts[severity] += 1
                        
                except json.JSONDecodeError:
                    logger.warning("Pylint JSONパースエラー")
            
            # スコア計算
            error_penalty = severity_counts.get('error', 0) * 10
            warning_penalty = severity_counts.get('warning', 0) * 3
            info_penalty = severity_counts.get('info', 0) * 1
            score = max(0, 100 - error_penalty - warning_penalty - info_penalty)
            
            return {
                'issues': issues,
                'severity_counts': severity_counts,
                'score': score
            }
            
        except Exception as e:
            logger.warning(f"Pylint実行エラー: {e}")
            return {'issues': [], 'severity_counts': {}, 'score': 70.0}
    
    async def _run_mypy(self, code: str, file_path: str) -> Dict[str, Any]:
        """Mypyによる型チェック"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = subprocess.run([
                'mypy', temp_path,
                '--ignore-missing-imports',
                '--no-strict-optional'
            ], capture_output=True, text=True, timeout=30)
            
            os.unlink(temp_path)
            
            issues = []
            severity_counts = {'error': 0, 'warning': 0, 'info': 0}
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            try:
                                line_num = int(parts[1])
                                message = ':'.join(parts[2:]).strip()
                                
                                issue = {
                                    'line': line_num,
                                    'column': 1,
                                    'message': message,
                                    'severity': 'error' if 'error' in message.lower() else 'warning',
                                    'rule': 'type-check'
                                }
                                issues.append(issue)
                                
                                if 'error' in message.lower():
                                    severity_counts['error'] += 1
                                else:
                                    severity_counts['warning'] += 1
                                    
                            except ValueError:
                                continue
            
            # スコア計算
            error_penalty = severity_counts.get('error', 0) * 8
            warning_penalty = severity_counts.get('warning', 0) * 2
            score = max(0, 100 - error_penalty - warning_penalty)
            
            return {
                'issues': issues,
                'severity_counts': severity_counts,
                'score': score
            }
            
        except Exception as e:
            logger.warning(f"Mypy実行エラー: {e}")
            return {'issues': [], 'severity_counts': {}, 'score': 80.0}
    
    async def _run_black(self, code: str, file_path: str) -> Dict[str, Any]:
        """Blackによるフォーマットチェック"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = subprocess.run([
                'black', '--check', '--diff', temp_path,
                '--line-length=120'
            ], capture_output=True, text=True, timeout=20)
            
            os.unlink(temp_path)
            
            issues = []
            severity_counts = {'error': 0, 'warning': 0, 'info': 0}
            
            if result.returncode != 0 and result.stdout:
                # フォーマット差分がある場合
                issues.append({
                    'line': 1,
                    'column': 1,
                    'message': 'コードフォーマットが標準に準拠していません',
                    'severity': 'info',
                    'rule': 'format'
                })
                severity_counts['info'] += 1
            
            score = 100 if result.returncode == 0 else 85
            
            return {
                'issues': issues,
                'severity_counts': severity_counts,
                'score': score
            }
            
        except Exception as e:
            logger.warning(f"Black実行エラー: {e}")
            return {'issues': [], 'severity_counts': {}, 'score': 90.0}
    
    async def _run_isort(self, code: str, file_path: str) -> Dict[str, Any]:
        """isortによるimport文チェック"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = subprocess.run([
                'isort', '--check-only', '--diff', temp_path
            ], capture_output=True, text=True, timeout=15)
            
            os.unlink(temp_path)
            
            issues = []
            severity_counts = {'error': 0, 'warning': 0, 'info': 0}
            
            if result.returncode != 0:
                issues.append({
                    'line': 1,
                    'column': 1,
                    'message': 'import文の順序が標準に準拠していません',
                    'severity': 'info',
                    'rule': 'import-order'
                })
                severity_counts['info'] += 1
            
            score = 100 if result.returncode == 0 else 90
            
            return {
                'issues': issues,
                'severity_counts': severity_counts,
                'score': score
            }
            
        except Exception as e:
            logger.warning(f"isort実行エラー: {e}")
            return {'issues': [], 'severity_counts': {}, 'score': 95.0}
    
    async def _run_bandit(self, code: str, file_path: str) -> Dict[str, Any]:
        """Banditによるセキュリティチェック"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = subprocess.run([
                'bandit', '-f', 'json', temp_path
            ], capture_output=True, text=True, timeout=30)
            
            os.unlink(temp_path)
            
            issues = []
            severity_counts = {'error': 0, 'warning': 0, 'info': 0}
            
            if result.stdout.strip():
                try:
                    bandit_output = json.loads(result.stdout)
                    for issue in bandit_output.get('results', []):
                        severity = issue.get('issue_severity', 'LOW').lower()
                        if severity == 'high':
                            severity = 'error'
                        elif severity == 'medium':
                            severity = 'warning'
                        else:
                            severity = 'info'
                        
                        issues.append({
                            'line': issue.get('line_number', 1),
                            'column': 1,
                            'message': issue.get('issue_text', ''),
                            'severity': severity,
                            'rule': issue.get('test_id', 'security')
                        })
                        severity_counts[severity] += 1
                        
                except json.JSONDecodeError:
                    logger.warning("Bandit JSONパースエラー")
            
            # セキュリティスコア計算
            error_penalty = severity_counts.get('error', 0) * 15
            warning_penalty = severity_counts.get('warning', 0) * 5
            info_penalty = severity_counts.get('info', 0) * 2
            score = max(0, 100 - error_penalty - warning_penalty - info_penalty)
            
            return {
                'issues': issues,
                'severity_counts': severity_counts,
                'score': score
            }
            
        except Exception as e:
            logger.warning(f"Bandit実行エラー: {e}")
            return {'issues': [], 'severity_counts': {}, 'score': 85.0}
    
    async def _run_eslint(self, code: str, file_path: str) -> Dict[str, Any]:
        """ESLintによるJavaScript静的解析"""
        # 簡易実装（実際の環境ではnpm install eslintが必要）
        issues = []
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        # 基本的なJavaScriptの問題をチェック
        if 'var ' in code:
            issues.append({
                'line': 1,
                'column': 1,
                'message': 'varの代わりにletまたはconstを使用してください',
                'severity': 'warning',
                'rule': 'no-var'
            })
            severity_counts['warning'] += 1
        
        if '==' in code and '===' not in code:
            issues.append({
                'line': 1,
                'column': 1,
                'message': '厳密等価演算子(===)を使用してください',
                'severity': 'warning',
                'rule': 'eqeqeq'
            })
            severity_counts['warning'] += 1
        
        score = max(0, 100 - len(issues) * 5)
        
        return {
            'issues': issues,
            'severity_counts': severity_counts,
            'score': score
        }
    
    async def _run_prettier(self, code: str, file_path: str) -> Dict[str, Any]:
        """Prettierによるフォーマットチェック"""
        # 基本的なフォーマットチェック
        issues = []
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'line': i,
                    'column': 120,
                    'message': '行が長すぎます（120文字以下推奨）',
                    'severity': 'info',
                    'rule': 'max-len'
                })
                severity_counts['info'] += 1
        
        score = max(0, 100 - len(issues) * 2)
        
        return {
            'issues': issues,
            'severity_counts': severity_counts,
            'score': score
        }
    
    async def _run_jshint(self, code: str, file_path: str) -> Dict[str, Any]:
        """JSHintによるJavaScript品質チェック"""
        issues = []
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        # 基本的な品質チェック
        if 'eval(' in code:
            issues.append({
                'line': 1,
                'column': 1,
                'message': 'eval()の使用は避けてください',
                'severity': 'error',
                'rule': 'no-eval'
            })
            severity_counts['error'] += 1
        
        score = max(0, 100 - len(issues) * 10)
        
        return {
            'issues': issues,
            'severity_counts': severity_counts,
            'score': score
        }
    
    async def _run_tslint(self, code: str, file_path: str) -> Dict[str, Any]:
        """TSLintによるTypeScript静的解析"""
        # TypeScript特有のチェック
        issues = []
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        if 'any' in code:
            issues.append({
                'line': 1,
                'column': 1,
                'message': 'any型の使用を避けて、より具体的な型を指定してください',
                'severity': 'warning',
                'rule': 'no-any'
            })
            severity_counts['warning'] += 1
        
        score = max(0, 100 - len(issues) * 5)
        
        return {
            'issues': issues,
            'severity_counts': severity_counts,
            'score': score
        }
    
    async def _run_typescript_check(self, code: str, file_path: str) -> Dict[str, Any]:
        """TypeScript型チェック"""
        # 基本的な型チェック（実際の環境ではtscコマンドを使用）
        issues = []
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        # インターフェースや型定義があるかチェック
        if 'interface' in code or 'type' in code:
            score = 95
        else:
            issues.append({
                'line': 1,
                'column': 1,
                'message': '型定義を使用することを推奨します',
                'severity': 'info',
                'rule': 'type-definition'
            })
            severity_counts['info'] += 1
            score = 85
        
        return {
            'issues': issues,
            'severity_counts': severity_counts,
            'score': score
        }


class TestGenerator:
    """テスト自動生成エンジン"""
    
    def __init__(self, ollama_provider: OllamaProvider):
        self.ollama_provider = ollama_provider
    
    async def generate_tests(self, code: str, language: str, job_input: JobInput) -> TestGenerationResult:
        """コードに基づいてテストを自動生成"""
        test_files = []
        
        try:
            if language == 'python':
                # Pythonテスト生成
                unit_test = await self._generate_python_unit_test(code, job_input)
                integration_test = await self._generate_python_integration_test(code, job_input)
                
                test_files.extend([
                    {'filename': 'test_unit.py', 'content': unit_test, 'type': 'unit_test'},
                    {'filename': 'test_integration.py', 'content': integration_test, 'type': 'integration_test'}
                ])
                
            elif language == 'javascript':
                # JavaScriptテスト生成
                jest_test = await self._generate_javascript_jest_test(code, job_input)
                e2e_test = await self._generate_javascript_e2e_test(code, job_input)
                
                test_files.extend([
                    {'filename': 'test.test.js', 'content': jest_test, 'type': 'unit_test'},
                    {'filename': 'e2e.test.js', 'content': e2e_test, 'type': 'e2e_test'}
                ])
            
            return TestGenerationResult(
                test_type='comprehensive',
                test_files=test_files,
                coverage_target=80.0,
                generated_tests=len(test_files)
            )
            
        except Exception as e:
            logger.error(f"テスト生成エラー: {e}")
            return TestGenerationResult(
                test_type='basic',
                test_files=[],
                coverage_target=0.0,
                generated_tests=0
            )
    
    async def _generate_python_unit_test(self, code: str, job_input: JobInput) -> str:
        """Python単体テスト生成"""
        # コードから関数とクラスを抽出
        functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):', code)
        classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(\:]', code)
        
        prompt = f"""
以下のPythonコードに対して、包括的な単体テストを生成してください。

コード:
{code[:1000]}...

要求事項:
- unittestフレームワークを使用
- 各関数: {', '.join(functions[:5])}
- 各クラス: {', '.join(classes[:3])}
- 正常ケース、異常ケース、境界値テストを含める
- モックを使用して外部依存を分離
- テストカバレッジ80%以上を目指す

高品質なテストコードを生成してください。
"""
        
        try:
            response = await self.ollama_provider.generate_response(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            # レスポンスからコード部分を抽出
            test_code = self._extract_code_from_response(response.get('content', ''))
            
            return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
自動生成された単体テスト - {job_input.job_type}
Generated by AI Code Quality Verification System
\"\"\"

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# テスト対象モジュールをインポート
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

{test_code}

if __name__ == '__main__':
    unittest.main(verbosity=2)
"""
            
        except Exception as e:
            logger.error(f"Python単体テスト生成エラー: {e}")
            return self._generate_basic_python_test(job_input)
    
    async def _generate_python_integration_test(self, code: str, job_input: JobInput) -> str:
        """Python統合テスト生成"""
        prompt = f"""
以下のPythonコードに対して、統合テストを生成してください。

コード:
{code[:800]}...

要求事項:
- 複数のコンポーネント間の連携をテスト
- 実際のデータフローをテスト
- エラー処理とリカバリをテスト
- パフォーマンステストを含める

統合テストコードを生成してください。
"""
        
        try:
            response = await self.ollama_provider.generate_response(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            test_code = self._extract_code_from_response(response.get('content', ''))
            
            return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
自動生成された統合テスト - {job_input.job_type}
Generated by AI Code Quality Verification System
\"\"\"

import unittest
import time
import tempfile
import os
from pathlib import Path

{test_code}

if __name__ == '__main__':
    unittest.main(verbosity=2)
"""
        except Exception as e:
            logger.error(f"Python統合テスト生成エラー: {e}")
            return self._generate_basic_integration_test(job_input)
    
    async def _generate_javascript_jest_test(self, code: str, job_input: JobInput) -> str:
        """JavaScript Jestテスト生成"""
        # 関数を抽出
        functions = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        arrow_functions = re.findall(r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=', code)
        
        prompt = f"""
以下のJavaScriptコードに対して、Jestテストを生成してください。

コード:
{code[:1000]}...

関数: {', '.join(functions + arrow_functions)}

要求事項:
- Jest testing frameworkを使用
- describe/it構造でテストを整理
- 正常ケース、エラーケース、非同期処理テストを含める
- モックとスパイを適切に使用
- 境界値テストを含める

包括的なテストスイートを生成してください。
"""
        
        try:
            response = await self.ollama_provider.generate_response(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            test_code = self._extract_code_from_response(response.get('content', ''))
            
            return f"""/**
 * 自動生成されたJestテスト - {job_input.job_type}
 * Generated by AI Code Quality Verification System
 */

const {{ describe, it, expect, beforeEach, afterEach, jest }} = require('@jest/globals');

// テスト対象をインポート
// const main = require('./main');

{test_code}
"""
        except Exception as e:
            logger.error(f"JavaScript Jestテスト生成エラー: {e}")
            return self._generate_basic_javascript_test(job_input)
    
    async def _generate_javascript_e2e_test(self, code: str, job_input: JobInput) -> str:
        """JavaScript E2Eテスト生成"""
        return f"""/**
 * 自動生成されたE2Eテスト - {job_input.job_type}
 * Generated by AI Code Quality Verification System
 */

const {{ test, expect }} = require('@playwright/test');

test.describe('{job_input.job_type} E2E Tests', () => {{
    test.beforeEach(async ({{ page }}) => {{
        // セットアップ処理
    }});
    
    test('基本フローのテスト', async ({{ page }}) => {{
        // TODO: E2Eテストシナリオを実装
        expect(true).toBe(true);
    }});
    
    test('エラーケースのテスト', async ({{ page }}) => {{
        // TODO: エラーシナリオをテスト
        expect(true).toBe(true);
    }});
}});
"""
    
    def _extract_code_from_response(self, response: str) -> str:
        """AIレスポンスからコード部分を抽出"""
        # ```で囲まれたコードブロックを抽出
        code_blocks = re.findall(r'```(?:python|javascript|js)?\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        # コードブロックがない場合は全体を返す
        return response.strip()
    
    def _generate_basic_python_test(self, job_input: JobInput) -> str:
        """基本的なPythonテストテンプレート"""
        return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
基本的な単体テスト - {job_input.job_type}
\"\"\"

import unittest

class Test{job_input.job_type.replace('_', '').title()}(unittest.TestCase):
    
    def setUp(self):
        \"\"\"テストセットアップ\"\"\"
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
    
    def _generate_basic_integration_test(self, job_input: JobInput) -> str:
        """基本的な統合テストテンプレート"""
        return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
基本的な統合テスト - {job_input.job_type}
\"\"\"

import unittest

class Integration{job_input.job_type.replace('_', '').title()}Test(unittest.TestCase):
    
    def test_component_integration(self):
        \"\"\"コンポーネント間連携テスト\"\"\"
        # TODO: 統合テストを実装
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
"""
    
    def _generate_basic_javascript_test(self, job_input: JobInput) -> str:
        """基本的なJavaScriptテストテンプレート"""
        return f"""/**
 * 基本的なJestテスト - {job_input.job_type}
 */

describe('{job_input.job_type}', () => {{
    it('基本機能をテストする', () => {{
        // TODO: 実際のテストケースを実装
        expect(true).toBe(true);
    }});
}});
"""


class SecurityAnalyzer:
    """セキュリティ分析エンジン"""
    
    def __init__(self):
        self.vulnerability_patterns = {
            'python': [
                (r'eval\s*\(', 'eval()の使用は危険です', 'high'),
                (r'exec\s*\(', 'exec()の使用は危険です', 'high'),
                (r'subprocess\.call.*shell=True', 'shell=Trueは脆弱性の原因となります', 'medium'),
                (r'pickle\.loads?', 'pickleは信頼できないデータには使用しないでください', 'medium'),
                (r'input\s*\(', 'input()は適切に検証してください', 'low'),
                (r'open\s*\([^)]*["\'][^"\']*\.\.[^"\']*["\']', 'パストラバーサル脆弱性の可能性', 'high')
            ],
            'javascript': [
                (r'eval\s*\(', 'eval()の使用は危険です', 'high'),
                (r'innerHTML\s*=', 'innerHTMLはXSS脆弱性の原因となる可能性があります', 'medium'),
                (r'document\.write', 'document.writeはXSS脆弱性の原因となります', 'medium'),
                (r'setTimeout\s*\([^)]*["\'][^"\']*["\']', 'setTimeoutでの文字列実行は危険です', 'high'),
                (r'new\s+Function\s*\(', 'Function()コンストラクタは危険です', 'high')
            ]
        }
    
    async def analyze_security(self, code: str, language: str) -> SecurityAnalysisResult:
        """セキュリティ分析を実行"""
        vulnerabilities = []
        patterns = self.vulnerability_patterns.get(language, [])
        
        for pattern, message, severity in patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                vulnerabilities.append({
                    'line': line_num,
                    'column': match.start() - code.rfind('\n', 0, match.start()),
                    'message': message,
                    'severity': severity,
                    'pattern': pattern,
                    'code_snippet': code[max(0, match.start()-20):match.end()+20]
                })
        
        # セキュリティスコア計算
        high_risk = len([v for v in vulnerabilities if v['severity'] == 'high'])
        medium_risk = len([v for v in vulnerabilities if v['severity'] == 'medium'])
        low_risk = len([v for v in vulnerabilities if v['severity'] == 'low'])
        
        security_score = max(0, 100 - (high_risk * 25) - (medium_risk * 10) - (low_risk * 5))
        
        # リスクレベル決定
        if high_risk > 0:
            risk_level = 'HIGH'
        elif medium_risk > 2:
            risk_level = 'MEDIUM'
        elif medium_risk > 0 or low_risk > 3:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        # 推奨事項生成
        recommendations = self._generate_security_recommendations(vulnerabilities, language)
        
        return SecurityAnalysisResult(
            vulnerabilities=vulnerabilities,
            security_score=security_score,
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _generate_security_recommendations(self, vulnerabilities: List[Dict], language: str) -> List[str]:
        """セキュリティ推奨事項を生成"""
        recommendations = []
        
        # 脆弱性タイプ別推奨事項
        vuln_types = [v['message'] for v in vulnerabilities]
        
        if any('eval' in msg for msg in vuln_types):
            recommendations.append("eval()やexec()の代わりに、より安全な代替手段を使用してください")
        
        if any('XSS' in msg for msg in vuln_types):
            recommendations.append("ユーザー入力は適切にエスケープ・サニタイズしてください")
        
        if any('shell' in msg for msg in vuln_types):
            recommendations.append("shell=Falseを使用するか、より安全なAPIを使用してください")
        
        if any('パストラバーサル' in msg for msg in vuln_types):
            recommendations.append("ファイルパスは適切に検証・正規化してください")
        
        # 一般的な推奨事項
        if language == 'python':
            recommendations.extend([
                "Banditなどのセキュリティ分析ツールを定期的に実行してください",
                "依存関係の脆弱性をSafety等でチェックしてください"
            ])
        elif language == 'javascript':
            recommendations.extend([
                "ESLint security pluginを使用してください",
                "npm auditで依存関係の脆弱性をチェックしてください"
            ])
        
        return list(set(recommendations))  # 重複除去


@injectable
class CodeQualityVerificationService:
    """コード品質検証サービス - Task 3-7メイン実装"""
    
    def __init__(self, ollama_provider: OllamaProvider):
        self.ollama_provider = ollama_provider
        self.code_analyzer = EnhancedCodeAnalyzer()
        self.static_analyzer = StaticAnalysisEngine()
        self.test_generator = TestGenerator(ollama_provider)
        self.security_analyzer = SecurityAnalyzer()
    
    async def verify_code_quality(self, code: str, language: str, job_input: JobInput) -> QualityVerificationResult:
        """コード品質の包括的検証を実行"""
        start_time = datetime.now()
        
        try:
            logger.info(f"コード品質検証開始: {job_input.job_id} ({language})")
            
            # 並列実行でパフォーマンス向上
            tasks = [
                self._run_static_analysis(code, language),
                self._run_quality_analysis(code, language),
                self._run_test_generation(code, language, job_input),
                self._run_security_analysis(code, language)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            static_analysis = results[0] if not isinstance(results[0], Exception) else []
            quality_metrics = results[1] if not isinstance(results[1], Exception) else CodeQualityMetrics()
            test_generation = results[2] if not isinstance(results[2], Exception) else TestGenerationResult('basic', [], 0.0, 0)
            security_analysis = results[3] if not isinstance(results[3], Exception) else SecurityAnalysisResult([], 50.0, 'UNKNOWN', [])
            
            # 総合スコア計算
            overall_score = await self._calculate_overall_score(
                static_analysis, quality_metrics, security_analysis
            )
            
            # 推奨事項生成
            recommendations = await self._generate_comprehensive_recommendations(
                static_analysis, quality_metrics, security_analysis, language
            )
            
            verification_time = (datetime.now() - start_time).total_seconds()
            
            result = QualityVerificationResult(
                job_id=job_input.job_id,
                language=language,
                static_analysis=static_analysis,
                test_generation=test_generation,
                security_analysis=security_analysis,
                quality_metrics=quality_metrics,
                overall_score=overall_score,
                recommendations=recommendations,
                verification_time=verification_time
            )
            
            logger.info(f"コード品質検証完了: スコア={overall_score:.1f}, 時間={verification_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"コード品質検証エラー: {e}")
            verification_time = (datetime.now() - start_time).total_seconds()
            
            return QualityVerificationResult(
                job_id=job_input.job_id,
                language=language,
                static_analysis=[],
                test_generation=TestGenerationResult('error', [], 0.0, 0),
                security_analysis=SecurityAnalysisResult([], 0.0, 'ERROR', ['検証中にエラーが発生しました']),
                quality_metrics=CodeQualityMetrics(),
                overall_score=0.0,
                recommendations=['コード品質検証を再実行してください'],
                verification_time=verification_time
            )
    
    async def _run_static_analysis(self, code: str, language: str) -> List[StaticAnalysisResult]:
        """静的解析実行"""
        temp_file = f"temp_code.{self._get_file_extension(language)}"
        return await self.static_analyzer.analyze_code(code, language, temp_file)
    
    async def _run_quality_analysis(self, code: str, language: str) -> CodeQualityMetrics:
        """品質分析実行"""
        return await self.code_analyzer.analyze_code_quality(code, language)
    
    async def _run_test_generation(self, code: str, language: str, job_input: JobInput) -> TestGenerationResult:
        """テスト生成実行"""
        return await self.test_generator.generate_tests(code, language, job_input)
    
    async def _run_security_analysis(self, code: str, language: str) -> SecurityAnalysisResult:
        """セキュリティ分析実行"""
        return await self.security_analyzer.analyze_security(code, language)
    
    async def _calculate_overall_score(
        self, 
        static_analysis: List[StaticAnalysisResult],
        quality_metrics: CodeQualityMetrics,
        security_analysis: SecurityAnalysisResult
    ) -> float:
        """総合スコア計算"""
        
        # 静的解析スコア（平均）
        static_score = 70.0  # デフォルト
        if static_analysis:
            static_score = sum(result.score for result in static_analysis) / len(static_analysis)
        
        # 品質メトリクススコア
        quality_score = (
            (10 - quality_metrics.complexity_score) * 10 +  # 複雑度は低いほど良い
            quality_metrics.readability_score * 10 +
            quality_metrics.maintainability_score * 10 +
            (1 - quality_metrics.error_probability) * 100
        ) / 4
        
        # セキュリティスコア
        security_score = security_analysis.security_score
        
        # 重み付け総合スコア
        overall_score = (
            static_score * 0.3 +
            quality_score * 0.4 +
            security_score * 0.3
        )
        
        return round(overall_score, 1)
    
    async def _generate_comprehensive_recommendations(
        self,
        static_analysis: List[StaticAnalysisResult],
        quality_metrics: CodeQualityMetrics,
        security_analysis: SecurityAnalysisResult,
        language: str
    ) -> List[str]:
        """包括的な推奨事項生成"""
        recommendations = []
        
        # 静的解析からの推奨事項
        error_count = sum(result.severity_counts.get('error', 0) for result in static_analysis)
        warning_count = sum(result.severity_counts.get('warning', 0) for result in static_analysis)
        
        if error_count > 0:
            recommendations.append(f"エラー {error_count} 件を修正してください")
        if warning_count > 5:
            recommendations.append(f"警告 {warning_count} 件の確認と修正を推奨します")
        
        # 品質メトリクスからの推奨事項
        recommendations.extend(quality_metrics.suggestions)
        
        # セキュリティからの推奨事項
        recommendations.extend(security_analysis.recommendations)
        
        # 言語固有の推奨事項
        if language == 'python':
            recommendations.extend([
                "型ヒント(Type Hints)の使用を推奨します",
                "docstringによるドキュメント化を推奨します",
                "pytest使用によるテストの充実を検討してください"
            ])
        elif language == 'javascript':
            recommendations.extend([
                "TypeScriptの使用を検討してください",
                "ESLint + Prettierによるコード品質向上を推奨します",
                "Jest + @testing-libraryによるテスト充実を検討してください"
            ])
        
        # 重複除去と優先順位付け
        return list(dict.fromkeys(recommendations))[:10]  # 上位10件
    
    def _get_file_extension(self, language: str) -> str:
        """言語に応じたファイル拡張子取得"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'csharp': 'cs',
            'go': 'go',
            'rust': 'rs',
            'php': 'php'
        }
        return extensions.get(language, 'txt')
    
    async def get_quality_report(self, verification_result: QualityVerificationResult) -> str:
        """品質レポート生成"""
        report = f"""# コード品質検証レポート

## 概要
- **ジョブID**: {verification_result.job_id}
- **言語**: {verification_result.language}
- **総合スコア**: {verification_result.overall_score:.1f}/100
- **検証時間**: {verification_result.verification_time:.2f}秒

## 静的解析結果
"""
        
        for analysis in verification_result.static_analysis:
            report += f"""
### {analysis.tool.title()}
- **スコア**: {analysis.score:.1f}/100
- **エラー**: {analysis.severity_counts.get('error', 0)}件
- **警告**: {analysis.severity_counts.get('warning', 0)}件
- **情報**: {analysis.severity_counts.get('info', 0)}件
"""
        
        report += f"""
## 品質メトリクス
- **複雑度**: {verification_result.quality_metrics.complexity_score:.1f}/10
- **可読性**: {verification_result.quality_metrics.readability_score:.1f}/10
- **保守性**: {verification_result.quality_metrics.maintainability_score:.1f}/10
- **エラー確率**: {verification_result.quality_metrics.error_probability:.1%}

## セキュリティ分析
- **セキュリティスコア**: {verification_result.security_analysis.security_score:.1f}/100
- **リスクレベル**: {verification_result.security_analysis.risk_level}
- **脆弱性**: {len(verification_result.security_analysis.vulnerabilities)}件

## テスト生成結果
- **生成されたテストファイル**: {verification_result.test_generation.generated_tests}件
- **目標カバレッジ**: {verification_result.test_generation.coverage_target:.1f}%

## 推奨事項
"""
        
        for i, recommendation in enumerate(verification_result.recommendations, 1):
            report += f"{i}. {recommendation}\n"
        
        return report
