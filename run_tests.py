#!/usr/bin/env python
"""
テスト自動化スクリプト
コードベース全体のテスト実行、カバレッジレポート生成を行います
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_tests(args):
    """テストを実行する"""
    cmd = ["pytest"]
    
    # テスト対象を指定
    if args.module:
        cmd.append(args.module)
    
    # 詳細表示
    if args.verbose:
        cmd.append("-v")
    
    # カバレッジ計測
    if args.coverage:
        cmd.extend(["--cov", "--cov-report=term", "--cov-config=.coveragerc"])
        
        # HTMLレポートも生成
        if args.html_report:
            cmd.append("--cov-report=html")
    
    # カテゴリでフィルタリング
    if args.category:
        cmd.extend(["-m", args.category])
    
    # キーワードでフィルタリング
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    # JUnitXML形式でレポート出力
    if args.xml_report:
        cmd.extend(["--junitxml", "test-reports/test-results.xml"])
    
    # ステータス表示
    print(f"実行コマンド: {' '.join(cmd)}")
    
    # テスト実行
    start_time = time.time()
    result = subprocess.run(cmd)
    elapsed_time = time.time() - start_time
    
    # 結果表示
    print(f"\nテスト実行完了 (所要時間: {elapsed_time:.2f}秒)")
    print(f"終了コード: {result.returncode}")
    
    return result.returncode

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="テスト自動化スクリプト")
    parser.add_argument("-m", "--module", help="テスト対象のモジュールやファイル")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細出力")
    parser.add_argument("-c", "--coverage", action="store_true", help="カバレッジを計測")
    parser.add_argument("--html-report", action="store_true", help="HTMLカバレッジレポートを生成")
    parser.add_argument("--xml-report", action="store_true", help="JUnit XML形式のレポートを生成")
    parser.add_argument("--category", help="テストカテゴリで絞り込み (unit, integration, api, core, ai, ui)")
    parser.add_argument("-k", "--keyword", help="キーワードによるテスト絞り込み")
    
    args = parser.parse_args()
    
    # テストレポートディレクトリを作成
    if args.xml_report:
        Path("test-reports").mkdir(exist_ok=True)
    
    # テスト実行
    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main())
