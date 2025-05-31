"""
プログラム生成サービス - AI統合強化版

このサービスは多言語対応のプログラム生成機能を提供します。
Enhanced Program Generatorとの統合により、高品質なコード生成を実現します。
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Type, Optional, Any, List
from datetime import datetime

from core.dependency_injection import injectable
from data.models.job import JobInput, JobOutput, GenerationRequest, GenerationResult
from services.program_generator.base import BaseProgramGenerator
from services.program_generator.python.generator import PythonGenerator
from services.program_generator.javascript.generator import JavaScriptGenerator
from services.program_generator.web.generator import WebGenerator
from services.program_generator.enhanced_generator import EnhancedProgramGenerator

logger = logging.getLogger(__name__)


@injectable
class ProgramGeneratorService:
    """
    プログラム生成サービス - AI統合強化版
    
    複数の言語に対応したプログラム生成機能を提供します。
    AI駆動のコード生成、テンプレート管理、プロジェクト構造生成、
    品質分析、自動最適化などの高度な機能を含みます。
    """
    
    def __init__(self):
        self.generators: Dict[str, Type[BaseProgramGenerator]] = {}
        self.enhanced_generator: Optional[EnhancedProgramGenerator] = None
        self.use_enhanced_generation = True  # 強化版使用フラグ
        self._initialize_generators()
        
    def _initialize_generators(self):
        """利用可能なジェネレーターを初期化"""
        self.generators = {
            'python': PythonGenerator,
            'javascript': JavaScriptGenerator,
            'nodejs': JavaScriptGenerator,  # エイリアス
            'js': JavaScriptGenerator,      # エイリアス
            'web': WebGenerator,
            'html': WebGenerator,           # エイリアス
            'website': WebGenerator,        # エイリアス
        }
        logger.info(f"初期化されたジェネレーター: {list(self.generators.keys())}")
    
    async def initialize(self) -> bool:
        """サービス初期化"""
        try:
            logger.info("ProgramGeneratorService初期化開始...")
            
            if self.use_enhanced_generation:
                # 強化版ジェネレーター初期化
                self.enhanced_generator = EnhancedProgramGenerator()
                if not await self.enhanced_generator.initialize():
                    logger.warning("強化版ジェネレーター初期化失敗、基本版を使用")
                    self.use_enhanced_generation = False
                else:
                    logger.info("強化版ジェネレーター初期化完了")
            
            logger.info("ProgramGeneratorService初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"ProgramGeneratorService初期化エラー: {e}")
            return False
    
    async def generate_program(self, job_input: JobInput) -> JobOutput:
        """
        プログラム生成のメインエントリーポイント
        
        Args:
            job_input: ジョブ入力データ
            
        Returns:
            JobOutput: 生成結果
        """
        try:
            # 入力検証
            await self._validate_input(job_input)
            
            # 強化版使用判定
            if self.use_enhanced_generation and self.enhanced_generator:
                return await self._generate_with_enhanced_generator(job_input)
            else:
                return await self._generate_with_basic_generator(job_input)
            
        except Exception as e:
            logger.error(f"プログラム生成エラー: {job_input.job_id}, エラー: {str(e)}")
            return self._create_error_output(job_input, str(e))
    
    async def _generate_with_enhanced_generator(self, job_input: JobInput) -> JobOutput:
        """強化版ジェネレーターでの生成"""
        try:
            logger.info(f"強化版プログラム生成開始: {job_input.job_id}")
            
            # 強化版生成実行
            result = await self.enhanced_generator.generate(job_input)
            
            # 結果をJobOutputに変換
            job_output = self._convert_to_job_output(job_input, result)
            
            # 追加メタデータ設定
            if hasattr(job_output, 'metadata'):
                job_output.metadata['generator_type'] = 'enhanced'
                job_output.metadata['ai_powered'] = True
                job_output.metadata['quality_analysis'] = True
            
            logger.info(f"強化版プログラム生成完了: {job_input.job_id}")
            return job_output
            
        except Exception as e:
            logger.error(f"強化版生成エラー: {e}")
            # フォールバックで基本版を使用
            logger.info("基本版ジェネレーターにフォールバック")
            return await self._generate_with_basic_generator(job_input)
    
    async def _generate_with_basic_generator(self, job_input: JobInput) -> JobOutput:
        """基本版ジェネレーターでの生成"""
        try:
            # 言語/タイプの決定
            language = self._determine_language(job_input)
            
            # 適切なジェネレーターを取得
            generator_class = self.generators.get(language.lower())
            if not generator_class:
                raise ValueError(f"サポートされていない言語/タイプ: {language}")
            
            # ジェネレーターを初期化
            generator = generator_class()
            
            # プログラム生成実行
            logger.info(f"基本版プログラム生成開始: {job_input.job_id}, 言語: {language}")
            result = await generator.generate(job_input)
            
            # 結果をJobOutputに変換
            job_output = self._convert_to_job_output(job_input, result)
            
            # 追加メタデータ設定
            if hasattr(job_output, 'metadata'):
                job_output.metadata['generator_type'] = 'basic'
                job_output.metadata['ai_powered'] = False
            
            logger.info(f"基本版プログラム生成完了: {job_input.job_id}")
            return job_output
            
        except Exception as e:
            logger.error(f"基本版生成エラー: {e}")
            raise

    async def preview_generation(self, job_input: JobInput) -> Dict[str, Any]:
        """
        生成前のプレビュー情報を取得
        
        実際の生成は行わず、どのような構成でプログラムが生成されるかの
        概要情報を返します。
        """
        try:
            # 強化版の場合はより詳細な情報を提供
            if self.use_enhanced_generation and self.enhanced_generator:
                return await self._get_enhanced_preview(job_input)
            else:
                return await self._get_basic_preview(job_input)
            
        except Exception as e:
            logger.error(f"プレビュー生成エラー: {str(e)}")
            return {'error': str(e)}
    
    async def _get_enhanced_preview(self, job_input: JobInput) -> Dict[str, Any]:
        """強化版プレビュー情報取得"""
        language = self._determine_language(job_input)
        
        # プロジェクト構造予測
        estimated_files = []
        if language == 'python':
            estimated_files = [
                {'name': 'main.py', 'type': 'python', 'description': 'メインプログラム'},
                {'name': 'requirements.txt', 'type': 'text', 'description': '依存関係'},
                {'name': 'test_main.py', 'type': 'python', 'description': 'テストファイル'},
                {'name': 'README.md', 'type': 'markdown', 'description': 'プロジェクト説明'},
                {'name': 'QUALITY_REPORT.md', 'type': 'markdown', 'description': '品質レポート'}
            ]
        elif language == 'javascript':
            estimated_files = [
                {'name': 'main.js', 'type': 'javascript', 'description': 'メインプログラム'},
                {'name': 'package.json', 'type': 'json', 'description': 'プロジェクト設定'},
                {'name': 'main.test.js', 'type': 'javascript', 'description': 'テストファイル'},
                {'name': 'README.md', 'type': 'markdown', 'description': 'プロジェクト説明'},
                {'name': 'QUALITY_REPORT.md', 'type': 'markdown', 'description': '品質レポート'}
            ]
        elif language == 'web':
            estimated_files = [
                {'name': 'index.html', 'type': 'html', 'description': 'メインHTMLファイル'},
                {'name': 'styles.css', 'type': 'css', 'description': 'スタイルシート'},
                {'name': 'script.js', 'type': 'javascript', 'description': 'JavaScriptファイル'},
                {'name': 'README.md', 'type': 'markdown', 'description': 'プロジェクト説明'},
                {'name': 'QUALITY_REPORT.md', 'type': 'markdown', 'description': '品質レポート'}
            ]
        
        return {
            'language': language,
            'estimated_files': estimated_files,
            'estimated_structure': {
                'main_files': len([f for f in estimated_files if f['type'] in ['python', 'javascript', 'html']]),
                'config_files': len([f for f in estimated_files if f['type'] in ['json', 'text']]),
                'documentation_files': len([f for f in estimated_files if f['type'] == 'markdown'])
            },
            'features': [
                'AI駆動のコード生成',
                '自動品質分析',
                'テストファイル自動生成',
                '詳細な品質レポート',
                '改善提案付き',
                'セキュリティ考慮済み'
            ],
            'requirements': [
                f'{language.title()}実行環境',
                'テストフレームワーク（推奨）',
                'コードエディター'
            ],
            'generator_type': 'enhanced',
            'quality_analysis': True
        }
    
    async def _get_basic_preview(self, job_input: JobInput) -> Dict[str, Any]:
        """基本版プレビュー情報取得"""
        language = self._determine_language(job_input)
        generator_class = self.generators.get(language.lower())
        
        if not generator_class:
            return {'error': f"サポートされていない言語: {language}"}
        
        generator = generator_class()
        preview_info = await generator.get_generation_preview(job_input)
        
        return {
            'language': language,
            'estimated_files': preview_info.get('files', []),
            'estimated_structure': preview_info.get('structure', {}),
            'requirements': preview_info.get('requirements', []),
            'template_used': preview_info.get('template', None),
            'generator_type': 'basic',
            'quality_analysis': False
        }

    async def batch_generate(self, job_inputs: List[JobInput]) -> List[JobOutput]:
        """
        複数のプログラムを並列生成
        
        Args:
            job_inputs: 複数のジョブ入力
            
        Returns:
            List[JobOutput]: 生成結果のリスト
        """
        try:
            logger.info(f"バッチ生成開始: {len(job_inputs)}件")
            
            # 並列実行でパフォーマンス向上
            tasks = [self.generate_program(job_input) for job_input in job_inputs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 例外が発生した場合はエラー用出力に変換
            outputs = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_output = self._create_error_output(
                        job_inputs[i], 
                        f"バッチ生成エラー: {str(result)}"
                    )
                    outputs.append(error_output)
                else:
                    outputs.append(result)
            
            logger.info(f"バッチ生成完了: {len(outputs)}件")
            return outputs
            
        except Exception as e:
            logger.error(f"バッチ生成エラー: {str(e)}")
            return [self._create_error_output(job_input, str(e)) for job_input in job_inputs]

    async def get_supported_languages(self) -> List[str]:
        """サポートされている言語/タイプの一覧を取得"""
        return list(self.generators.keys())

    async def get_language_templates(self, language: str) -> List[Dict[str, Any]]:
        """指定された言語の利用可能なテンプレート一覧を取得"""
        try:
            generator_class = self.generators.get(language.lower())
            if not generator_class:
                return []

            generator = generator_class()
            return await generator.get_available_templates()

        except Exception as e:
            logger.error(f"テンプレート取得エラー: {str(e)}")
            return []

    async def get_generation_statistics(self) -> Dict[str, Any]:
        """生成統計情報を取得"""
        try:
            if self.use_enhanced_generation and self.enhanced_generator:
                # 強化版の詳細統計
                enhanced_stats = await self.enhanced_generator.get_generation_statistics()
                enhanced_stats['service_type'] = 'enhanced'
                return enhanced_stats
            else:
                # 基本統計
                return {
                    'service_type': 'basic',
                    'message': '基本版ジェネレーターでは詳細統計は利用できません'
                }
                
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {'error': str(e)}

    async def cleanup_old_files(self, days: int = 7):
        """古いファイルのクリーンアップ"""
        try:
            if self.use_enhanced_generation and self.enhanced_generator:
                await self.enhanced_generator.cleanup_old_files(days)
            else:
                # 基本的なクリーンアップ
                import glob
                import shutil
                from datetime import timedelta
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # temp/generated ディレクトリのクリーンアップ
                temp_pattern = "temp/generated/project_*"
                for temp_path in glob.glob(temp_pattern):
                    try:
                        path_stat = os.path.stat(temp_path)
                        if datetime.fromtimestamp(path_stat.st_mtime) < cutoff_date:
                            if os.path.isdir(temp_path):
                                shutil.rmtree(temp_path)
                            else:
                                os.remove(temp_path)
                            logger.info(f"古いファイル削除: {temp_path}")
                    except Exception as e:
                        logger.warning(f"ファイル削除エラー: {temp_path}, {e}")
                        
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")

    async def _validate_input(self, job_input: JobInput) -> bool:
        """入力検証"""
        try:
            if not job_input or not job_input.job_type:
                raise ValueError("ジョブ入力またはジョブタイプが指定されていません")

            parameters = job_input.parameters or {}
            if not parameters.get('description'):
                raise ValueError("プログラムの説明が指定されていません")

            # 強化版の場合はより詳細な検証
            if self.use_enhanced_generation and self.enhanced_generator:
                return await self.enhanced_generator.validate_input(job_input)
            
            return True

        except Exception as e:
            logger.error(f"入力検証エラー: {str(e)}")
            raise

    def _determine_language(self, job_input: JobInput) -> str:
        """ジョブタイプから言語を決定"""
        job_type_lower = job_input.job_type.lower()
        
        # 直接マッピング
        if job_type_lower in self.generators:
            return job_type_lower
        
        # パターンマッチング
        if any(pattern in job_type_lower for pattern in ['python', 'py']):
            return 'python'
        elif any(pattern in job_type_lower for pattern in ['javascript', 'js', 'node']):
            return 'javascript'
        elif any(pattern in job_type_lower for pattern in ['web', 'html', 'website', 'site']):
            return 'web'
        
        # パラメータからの推定
        parameters = job_input.parameters or {}
        language_hint = parameters.get('language', '').lower()
        if language_hint in self.generators:
            return language_hint
        
        # デフォルト
        return 'python'

    def _convert_to_job_output(self, job_input: JobInput, result: GenerationResult) -> JobOutput:
        """GenerationResultをJobOutputに変換"""
        try:            # 基本的なJobOutput作成
            job_output = JobOutput(
                job_id=job_input.job_id,
                job_type=job_input.job_type,
                status="completed" if result.success else "failed",
                content=result.content if result.success else "",
                content_type=result.content_type,
                preview_html=result.preview_html,
                files=result.files if result.files else [],
                download_url=result.download_url,
                error_message=result.error_message if not result.success else None,
                generation_time=result.generation_time,
                metadata={
                    'generation_time': result.generation_time,
                    'content_type': result.content_type,
                    'files_generated': len(result.files) if result.files else 0,
                    'download_available': bool(result.download_url),
                    'preview_available': bool(result.preview_html)
                }
            )
            
            # 追加メタデータのマージ
            if result.metadata:
                job_output.metadata.update(result.metadata)
            
            # 結果ファイル情報の追加
            if result.files:
                job_output.metadata['files'] = result.files
            
            if result.download_url:
                job_output.metadata['download_url'] = result.download_url
            
            if result.preview_html:
                job_output.metadata['preview_html'] = result.preview_html
            
            return job_output
            
        except Exception as e:
            logger.error(f"JobOutput変換エラー: {e}")
            return self._create_error_output(job_input, f"結果変換エラー: {str(e)}")

    def _create_error_output(self, job_input: JobInput, error_message: str) -> JobOutput:
        """エラー用のJobOutputを作成"""
        return JobOutput(
            job_id=job_input.job_id,
            job_type=job_input.job_type,
            status="failed",
            content="",
            error_message=error_message,
            metadata={
                'error_timestamp': datetime.now().isoformat(),
                'job_type': job_input.job_type,
                'generator_type': 'enhanced' if self.use_enhanced_generation else 'basic'
            }
        )
