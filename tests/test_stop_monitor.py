"""Stop hook 测试"""

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


def test_stop_monitor_import():
    """测试 stop-monitor.py 可以导入"""
    try:
        module = _import_hook_module("stop-monitor")
        print("[OK] test_stop_monitor_import passed")
        return module
    except Exception as e:
        print(f"[FAIL] test_stop_monitor_import failed: {e}")
        return None


def test_read_last_usage():
    """测试 usage 读取"""
    module = _import_hook_module("stop-monitor")
    if module is None:
        print("[SKIP] test_read_last_usage skipped")
        return

    read_last_usage = module.read_last_usage

    # 测试不存在的文件
    usage = read_last_usage("/nonexistent/path.jsonl")
    assert usage is None
    print("[OK] test_read_last_usage passed")


if __name__ == "__main__":
    test_stop_monitor_import()
    test_read_last_usage()
    print("\n[OK] All stop-monitor tests passed")
