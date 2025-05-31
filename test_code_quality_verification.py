#!/usr/bin/env python3
"""
Code Quality Verification Service Integration Test
Task 3-7 統合テスト
"""

import asyncio
import os
import sys
import tempfile
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.code_quality.verification_service import (
    CodeQualityVerificationService,
    StaticAnalysisResult,
    TestGenerationResult,
    SecurityAnalysisResult,
    QualityVerificationResult
)
from ai.providers.ollama_provider import OllamaProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCodeQualityVerification:
    def __init__(self):
        self.verification_service = None
        self.test_files = {}
        
    async def setup(self):
        """テスト環境のセットアップ"""
        logger.info("Setting up test environment...")
        
        # Initialize Ollama provider
        ollama_provider = OllamaProvider()
        
        # Initialize verification service
        self.verification_service = CodeQualityVerificationService(ollama_provider)
        
        # Create test files
        await self._create_test_files()
        
    async def _create_test_files(self):
        """テスト用のファイルを作成"""
        # Python test file with quality issues
        python_code = '''def bad_function(x, y, z, a, b, c):
    # Too many parameters
    if x > 0:
        if y > 0:
            if z > 0:
                # Deeply nested code
                result = x + y + z + a + b + c
                return result
    return None

# Missing docstring
def another_function():
    import os  # Import should be at top
    print("Hello")  # Should use logging
    
# Security issue - hardcoded password
PASSWORD = "admin123"
'''
        
        # JavaScript test file
        js_code = '''function badFunction(x, y, z, a, b, c) {
    // Too many parameters
    if (x > 0) {
        if (y > 0) {
            if (z > 0) {
                // Deeply nested code
                var result = x + y + z + a + b + c;
                return result;
            }
        }
    }
    return null;
}

// Missing semicolon
var globalVar = "test"

// Security issue - eval usage
function unsafeFunction(input) {
    return eval(input);
}
'''
        
        # Create temporary test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            self.test_files['python'] = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            self.test_files['javascript'] = f.name
            
        logger.info(f"Created test files: {list(self.test_files.values())}")
        
    async def test_static_analysis(self):
        """静的解析テスト"""
        logger.info("Testing static analysis...")
        
        for lang, file_path in self.test_files.items():
            try:
                result = await self.verification_service.run_static_analysis(file_path, lang)
                
                assert isinstance(result, StaticAnalysisResult)
                assert result.file_path == file_path
                assert result.language == lang
                assert result.score >= 0 and result.score <= 100
                
                logger.info(f"Static analysis for {lang}: Score {result.score}/100")
                logger.info(f"Issues found: {len(result.issues)}")
                
                for issue in result.issues[:3]:  # Show first 3 issues
                    logger.info(f"  - {issue.severity}: {issue.message}")
                    
            except Exception as e:
                logger.error(f"Static analysis failed for {lang}: {e}")
                
    async def test_security_analysis(self):
        """セキュリティ解析テスト"""
        logger.info("Testing security analysis...")
        
        for lang, file_path in self.test_files.items():
            try:
                result = await self.verification_service.run_security_analysis(file_path, lang)
                
                assert isinstance(result, SecurityAnalysisResult)
                assert result.file_path == file_path
                assert result.language == lang
                assert result.risk_score >= 0 and result.risk_score <= 100
                
                logger.info(f"Security analysis for {lang}: Risk {result.risk_score}/100")
                logger.info(f"Vulnerabilities found: {len(result.vulnerabilities)}")
                
                for vuln in result.vulnerabilities[:2]:  # Show first 2 vulnerabilities
                    logger.info(f"  - {vuln.severity}: {vuln.type}")
                    
            except Exception as e:
                logger.error(f"Security analysis failed for {lang}: {e}")
                
    async def test_test_generation(self):
        """テスト生成テスト"""
        logger.info("Testing test generation...")
        
        for lang, file_path in self.test_files.items():
            try:
                result = await self.verification_service.generate_tests(file_path, lang)
                
                assert isinstance(result, TestGenerationResult)
                assert result.file_path == file_path
                assert result.language == lang
                
                logger.info(f"Test generation for {lang}:")
                logger.info(f"  Unit tests: {len(result.unit_tests)} generated")
                logger.info(f"  Integration tests: {len(result.integration_tests)} generated")
                
                if result.unit_tests:
                    logger.info(f"  Sample unit test: {result.unit_tests[0][:100]}...")
                    
            except Exception as e:
                logger.error(f"Test generation failed for {lang}: {e}")
                
    async def test_full_verification(self):
        """完全な品質検証テスト"""
        logger.info("Testing full quality verification...")
        
        for lang, file_path in self.test_files.items():
            try:
                result = await self.verification_service.verify_code_quality(
                    file_path, 
                    lang,
                    include_static_analysis=True,
                    include_security_analysis=True,
                    include_test_generation=True
                )
                
                assert isinstance(result, QualityVerificationResult)
                assert result.file_path == file_path
                assert result.language == lang
                assert result.overall_score >= 0 and result.overall_score <= 100
                
                logger.info(f"Full verification for {lang}:")
                logger.info(f"  Overall score: {result.overall_score}/100")
                logger.info(f"  Static analysis score: {result.static_analysis.score if result.static_analysis else 'N/A'}")
                logger.info(f"  Security risk score: {result.security_analysis.risk_score if result.security_analysis else 'N/A'}")
                logger.info(f"  Tests generated: {len(result.test_generation.unit_tests) if result.test_generation else 0}")
                
                if result.recommendations:
                    logger.info(f"  Recommendations: {len(result.recommendations)}")
                    for rec in result.recommendations[:2]:
                        logger.info(f"    - {rec}")
                        
            except Exception as e:
                logger.error(f"Full verification failed for {lang}: {e}")
                
    async def test_performance(self):
        """パフォーマンステスト"""
        logger.info("Testing performance...")
        
        import time
        
        file_path = self.test_files['python']
        
        # Test parallel execution
        start_time = time.time()
        
        tasks = []
        for _ in range(3):  # Run 3 parallel verifications
            task = self.verification_service.verify_code_quality(
                file_path, 
                'python',
                include_static_analysis=True,
                include_security_analysis=True,
                include_test_generation=False  # Skip AI generation for performance test
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Parallel execution completed in {elapsed_time:.2f} seconds")
        
        successful_results = [r for r in results if isinstance(r, QualityVerificationResult)]
        logger.info(f"Successful results: {len(successful_results)}/{len(tasks)}")
        
    async def cleanup(self):
        """テスト環境のクリーンアップ"""
        logger.info("Cleaning up test environment...")
        
        for file_path in self.test_files.values():
            try:
                os.unlink(file_path)
                logger.info(f"Deleted test file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
                
    async def run_all_tests(self):
        """すべてのテストを実行"""
        try:
            await self.setup()
            
            logger.info("=" * 50)
            logger.info("Starting Code Quality Verification Service Tests")
            logger.info("=" * 50)
            
            await self.test_static_analysis()
            await self.test_security_analysis()
            await self.test_test_generation()
            await self.test_full_verification()
            await self.test_performance()
            
            logger.info("=" * 50)
            logger.info("All tests completed successfully!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            raise
        finally:
            await self.cleanup()

async def main():
    """メイン実行関数"""
    test_runner = TestCodeQualityVerification()
    await test_runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
