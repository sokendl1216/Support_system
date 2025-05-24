#!/usr/bin/env python3
"""設定優先度のデバッグ"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.settings import SettingsManager

# デバッグ
manager = SettingsManager()

print("初期状態:")
print(f"config_data: {manager.config_data}")
print(f"_loaded: {manager._loaded}")

# 手動設定
print("\n手動設定:")
manager.set("test_priority", "low_priority", "source1")
print(f"設定後 config_data: {manager.config_data}")

manager.set("test_priority", "high_priority", "source2")
print(f"オーバーライド後 config_data: {manager.config_data}")

# 取得テスト
print("\n取得テスト:")
result = manager.get("test_priority")
print(f"取得結果: {result}")
print(f"_loaded: {manager._loaded}")

# 強制的にload_configsを呼ぶ
print("\nload_configs実行:")
success = manager.load_configs()
print(f"load_configs成功: {success}")
print(f"設定後 config_data: {manager.config_data}")

# 再度取得
result2 = manager.get("test_priority")
print(f"再取得結果: {result2}")
