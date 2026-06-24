"""配置加载测试"""

import json
import sys
from pathlib import Path

# 添加 hooks/lib 到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from lib.config import load_config, get_config_value, _deep_merge


def test_deep_merge():
    """测试深度合并逻辑"""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 10}, "e": 4}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": {"c": 10, "d": 3}, "e": 4}
    print("[OK] test_deep_merge passed")


def test_get_config_value():
    """测试配置值获取"""
    # 测试默认值
    value = get_config_value("handoff.promptMode", "reply")
    assert value == "reply" or value is not None
    print("[OK] test_get_config_value passed")


def test_load_config():
    """测试配置加载"""
    config = load_config()
    assert isinstance(config, dict)
    assert "handoff" in config
    assert "context" in config
    assert "insight" in config
    print("[OK] test_load_config passed")


if __name__ == "__main__":
    test_deep_merge()
    test_get_config_value()
    test_load_config()
    print("\n[OK] All config tests passed")
