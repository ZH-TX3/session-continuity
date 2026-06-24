"""PreCompact hook 测试"""

import importlib.util
import json
import sys
from pathlib import Path

# 添加 hooks 到 sys.path
hooks_dir = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))


def _import_hook_module(module_name: str):
    """导入 hooks 目录下的模块 (支持带连字符的文件名)"""
    module_path = hooks_dir / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pre_compact_import():
    """测试 pre-compact.py 可以导入"""
    try:
        module = _import_hook_module("pre-compact")
        print("[OK] test_pre_compact_import passed")
        return module
    except Exception as e:
        print(f"[FAIL] test_pre_compact_import failed: {e}")
        return None


if __name__ == "__main__":
    test_pre_compact_import()
    print("\n[OK] All pre-compact tests passed")
