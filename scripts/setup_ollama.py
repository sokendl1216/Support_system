#!/usr/bin/env python3
"""
Ollama環境セットアップスクリプト
OSSモデルの自動インストールと設定管理
"""

import json
import subprocess
import asyncio
import aiohttp
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaSetup:
    """Ollama環境セットアップクラス"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # スクリプトの場所から相対的に設定ファイルを探す
            script_dir = Path(__file__).parent
            config_path = script_dir.parent / "config" / "ollama_models.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.base_url = f"http://{self.config['server_config']['host']}:{self.config['server_config']['port']}"
    
    def _load_config(self) -> Dict:
        """設定ファイルの読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルの形式が無効です: {e}")
            sys.exit(1)
    
    async def check_ollama_server(self) -> bool:
        """Ollamaサーバーの稼働確認"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        logger.info("Ollamaサーバーが稼働中です")
                        return True
                    else:
                        logger.warning(f"Ollamaサーバーのレスポンスが異常です: {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"Ollamaサーバーに接続できません: {e}")
            return False
    
    async def get_installed_models(self) -> List[str]:
        """インストール済みモデルの取得"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
                    return []
        except Exception as e:
            logger.error(f"モデル一覧の取得に失敗: {e}")
            return []
    
    def install_model(self, model_name: str, install_command: str) -> bool:
        """モデルのインストール"""
        logger.info(f"モデル '{model_name}' のインストールを開始...")
        try:
            result = subprocess.run(
                install_command.split(),
                capture_output=True,
                text=True,
                timeout=600  # 10分のタイムアウト
            )
            if result.returncode == 0:
                logger.info(f"モデル '{model_name}' のインストールが完了しました")
                return True
            else:
                logger.error(f"モデル '{model_name}' のインストールに失敗: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"モデル '{model_name}' のインストールがタイムアウトしました")
            return False
        except Exception as e:
            logger.error(f"モデル '{model_name}' のインストール中にエラー: {e}")
            return False
    
    async def setup_models(self, force_reinstall: bool = False) -> Dict[str, bool]:
        """有効なモデルのセットアップ"""
        results = {}
        
        # サーバー確認
        if not await self.check_ollama_server():
            logger.error("Ollamaサーバーが利用できません。先にOllamaをインストール・起動してください。")
            return results
        
        # インストール済みモデルの確認
        installed_models = await self.get_installed_models()
        logger.info(f"インストール済みモデル: {installed_models}")
        
        # 有効なモデルのインストール
        for model_name, model_config in self.config["models"].items():
            if not model_config.get("enabled", False):
                logger.info(f"モデル '{model_name}' はスキップ（無効化されています）")
                results[model_name] = True
                continue
            
            # モデルがすでにインストールされているかチェック
            model_installed = any(
                pattern in installed_model 
                for pattern in model_config.get("patterns", [model_name])
                for installed_model in installed_models
            )
            
            if model_installed and not force_reinstall:
                logger.info(f"モデル '{model_name}' は既にインストール済みです")
                results[model_name] = True
            else:
                install_command = model_config.get("install_command", f"ollama pull {model_name}")
                results[model_name] = self.install_model(model_name, install_command)
        
        return results
    
    def generate_installation_guide(self) -> str:
        """インストールガイドの生成"""
        guide = []
        guide.append("# Ollama環境セットアップガイド\n")
        
        # システム要件
        guide.append("## システム要件")
        perf_config = self.config["performance_config"]
        guide.append(f"- メモリ: 最低 {perf_config['memory_limit_gb']}GB RAM推奨")
        guide.append(f"- CPU: {perf_config['cpu_threads']}コア以上推奨")
        guide.append("- ディスク容量: 各モデルあたり4-8GB\n")
        
        # Ollamaインストール手順
        guide.append("## Ollamaのインストール")
        guide.append("### Windows:")
        guide.append("1. https://ollama.ai からOllamaをダウンロード")
        guide.append("2. インストーラーを実行")
        guide.append("3. コマンドプロンプトで `ollama serve` を実行してサーバーを起動\n")
        
        guide.append("### Linux/macOS:")
        guide.append("```bash")
        guide.append("curl -fsSL https://ollama.ai/install.sh | sh")
        guide.append("ollama serve")
        guide.append("```\n")
        
        # モデルインストール手順
        guide.append("## モデルのインストール")
        for model_name, model_config in self.config["models"].items():
            if model_config.get("enabled", False):
                guide.append(f"### {model_name}")
                guide.append(f"- 説明: {model_config['description']}")
                guide.append(f"- サイズ: {model_config['model_size']}")
                guide.append(f"- 必要メモリ: {model_config['memory_requirement']}")
                guide.append(f"- インストール: `{model_config['install_command']}`")
                guide.append(f"- 用途: {', '.join(model_config['use_cases'])}\n")
        
        # 自動セットアップ
        guide.append("## 自動セットアップ")
        guide.append("```bash")
        guide.append("python scripts/setup_ollama.py")
        guide.append("```\n")
        
        return "\n".join(guide)
    
    async def health_check(self) -> Dict[str, any]:
        """環境のヘルスチェック"""
        result = {
            "server_status": False,
            "installed_models": [],
            "enabled_models_status": {},
            "system_info": {}
        }
        
        # サーバー状態
        result["server_status"] = await self.check_ollama_server()
        
        if result["server_status"]:
            # インストール済みモデル
            result["installed_models"] = await self.get_installed_models()
            
            # 有効モデルの状態
            for model_name, model_config in self.config["models"].items():
                if model_config.get("enabled", False):
                    patterns = model_config.get("patterns", [model_name])
                    installed = any(
                        pattern in installed_model 
                        for pattern in patterns
                        for installed_model in result["installed_models"]
                    )
                    result["enabled_models_status"][model_name] = installed
        
        return result

async def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama環境セットアップ")
    parser.add_argument("--config", help="設定ファイルのパス")
    parser.add_argument("--check", action="store_true", help="ヘルスチェックのみ実行")
    parser.add_argument("--force", action="store_true", help="強制再インストール")
    parser.add_argument("--guide", action="store_true", help="インストールガイドを生成")
    
    args = parser.parse_args()
    
    setup = OllamaSetup(args.config)
    
    if args.guide:
        guide = setup.generate_installation_guide()
        guide_path = Path("docs/ollama_setup_guide.md")
        guide_path.parent.mkdir(exist_ok=True)
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide)
        logger.info(f"インストールガイドを生成しました: {guide_path}")
        return
    
    if args.check:
        health = await setup.health_check()
        print("=== Ollama環境ヘルスチェック ===")
        print(f"サーバー状態: {'稼働中' if health['server_status'] else '停止中'}")
        print(f"インストール済みモデル: {len(health['installed_models'])}個")
        for model in health['installed_models']:
            print(f"  - {model}")
        print("有効モデル状態:")
        for model, status in health['enabled_models_status'].items():
            status_text = "インストール済み" if status else "未インストール"
            print(f"  - {model}: {status_text}")
        return
    
    # セットアップ実行
    logger.info("Ollama環境のセットアップを開始します...")
    results = await setup.setup_models(force_reinstall=args.force)
    
    # 結果表示
    print("\n=== セットアップ結果 ===")
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")
    
    for model_name, success in results.items():
        status = "成功" if success else "失敗"
        print(f"  {model_name}: {status}")
    
    if success_count == total_count:
        logger.info("すべてのモデルのセットアップが完了しました！")
    else:
        logger.warning("一部のモデルのセットアップに失敗しました。ログを確認してください。")

if __name__ == "__main__":
    asyncio.run(main())
