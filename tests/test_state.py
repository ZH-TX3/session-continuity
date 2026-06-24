"""状态管理测试"""

import json
import sys
import tempfile
from pathlib import Path

# 添加 hooks/lib 到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from lib.state import (
    get_session_model,
    set_session_model,
    is_session_prompted,
    mark_session_prompted,
    is_session_warned,
    mark_session_warned,
)


def test_session_model():
    """测试模型信息读写"""
    # 注意: 这会修改实际的状态文件
    # 在实际测试中应该使用临时文件
    model = get_session_model()
    assert isinstance(model, str)
    print("[OK] test_session_model passed")


def test_session_prompted():
    """测试已提示会话记录"""
    test_id = "test-session-123"
    # 确保初始状态
    assert not is_session_prompted(test_id)
    # 标记
    mark_session_prompted(test_id)
    # 验证
    assert is_session_prompted(test_id)
    print("[OK] test_session_prompted passed")


def test_session_warned():
    """测试已警告会话记录"""
    test_id = "test-session-456"
    # 确保初始状态
    assert not is_session_warned(test_id)
    # 标记
    mark_session_warned(test_id)
    # 验证
    assert is_session_warned(test_id)
    print("[OK] test_session_warned passed")


if __name__ == "__main__":
    test_session_model()
    test_session_prompted()
    test_session_warned()
    print("\n[OK] All state tests passed")
