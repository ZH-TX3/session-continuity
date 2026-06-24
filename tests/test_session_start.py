"""SessionStart hook 测试"""

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


def test_session_start_import():
    """测试 session-start.py 可以导入"""
    try:
        module = _import_hook_module("session-start")
        print("[OK] test_session_start_import passed")
        return module
    except Exception as e:
        print(f"[FAIL] test_session_start_import failed: {e}")
        return None


def test_extract_topic():
    """测试主题提取"""
    module = _import_hook_module("session-start")
    if module is None:
        print("[SKIP] test_extract_topic skipped")
        return

    extract_topic = module.extract_topic

    # 测试标准格式
    content = """# Handoff — 2026-06-24

## 本会话主题
测试主题

## 完成的工作
- 任务 1
"""
    topic = extract_topic(content)
    assert "测试主题" in topic
    print("[OK] test_extract_topic passed")


if __name__ == "__main__":
    test_session_start_import()
    test_extract_topic()
    print("\n[OK] All session-start tests passed")
