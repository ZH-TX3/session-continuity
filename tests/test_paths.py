"""路径查找测试"""

import sys
from pathlib import Path

# 添加 hooks/lib 到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from lib.paths import (
    find_project_root,
    get_claude_dir,
    get_config_path,
    get_state_path,
    get_handoff_path,
)


def test_find_project_root():
    """测试项目根目录查找"""
    root = find_project_root()
    assert isinstance(root, Path)
    assert root.is_dir()
    print("[OK] test_find_project_root passed (root={root})")


def test_get_claude_dir():
    """测试 .claude 目录获取"""
    claude_dir = get_claude_dir()
    assert isinstance(claude_dir, Path)
    print("[OK] test_get_claude_dir passed (dir={claude_dir})")


def test_get_config_path():
    """测试配置文件路径"""
    config_path = get_config_path()
    assert isinstance(config_path, Path)
    assert config_path.name == "session-continuity.json"
    print("[OK] test_get_config_path passed (path={config_path})")


def test_get_state_path():
    """测试状态文件路径"""
    state_path = get_state_path()
    assert isinstance(state_path, Path)
    assert state_path.name == ".hooks-state.json"
    print("[OK] test_get_state_path passed (path={state_path})")


def test_get_handoff_path():
    """测试 HANDOFF 文件路径"""
    handoff_path = get_handoff_path()
    assert isinstance(handoff_path, Path)
    assert handoff_path.name == "HANDOFF.md"
    print("[OK] test_get_handoff_path passed (path={handoff_path})")


if __name__ == "__main__":
    test_find_project_root()
    test_get_claude_dir()
    test_get_config_path()
    test_get_state_path()
    test_get_handoff_path()
    print("\n[OK] All paths tests passed")
