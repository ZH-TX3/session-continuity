"""状态管理模块 — 跨 hooks 共享状态"""

import json
from pathlib import Path

from .paths import get_state_path


def _read_state() -> dict:
    """读取状态文件，不存在则返回默认结构。

    Returns:
        dict: 状态字典
    """
    state_path = get_state_path()
    if not state_path.exists():
        return {
            "session_model": "",
            "prompted_sessions": [],
            "warned_sessions": [],
        }
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception):
        return {
            "session_model": "",
            "prompted_sessions": [],
            "warned_sessions": [],
        }


def _write_state(state: dict) -> None:
    """写入状态文件。

    Args:
        state: 状态字典
    """
    state_path = get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_session_model() -> str:
    """获取当前 session 的模型名称。

    Returns:
        str: 模型名称
    """
    return _read_state().get("session_model", "")


def set_session_model(model: str) -> None:
    """设置当前 session 的模型名称。

    Args:
        model: 模型名称
    """
    state = _read_state()
    state["session_model"] = model
    _write_state(state)


def is_session_prompted(session_id: str) -> bool:
    """检查 session 是否已提示过 handoff。

    Args:
        session_id: 会话 ID

    Returns:
        bool: 是否已提示
    """
    return session_id in _read_state().get("prompted_sessions", [])


def mark_session_prompted(session_id: str) -> None:
    """标记 session 已提示过 handoff。

    Args:
        session_id: 会话 ID
    """
    state = _read_state()
    if session_id not in state.get("prompted_sessions", []):
        state.setdefault("prompted_sessions", []).append(session_id)
        _write_state(state)


def is_session_warned(session_id: str) -> bool:
    """检查 session 是否已警告过上下文超限。

    Args:
        session_id: 会话 ID

    Returns:
        bool: 是否已警告
    """
    return session_id in _read_state().get("warned_sessions", [])


def mark_session_warned(session_id: str) -> None:
    """标记 session 已警告过上下文超限。

    Args:
        session_id: 会话 ID
    """
    state = _read_state()
    if session_id not in state.get("warned_sessions", []):
        state.setdefault("warned_sessions", []).append(session_id)
        _write_state(state)
