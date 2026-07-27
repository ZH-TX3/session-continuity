"""Insight Hook 独立状态管理。

存储 Insight 注入所需的运行态（session 模型、轮次计数），
与 session-continuity 的 state.json 完全隔离。
"""

import json
import os
import uuid
from pathlib import Path

from locking import file_lock

_MAX_SESSION_ENTRIES = 100


def _insight_state_path(cwd: str | Path | None = None) -> Path:
    from .paths import find_project_root
    return find_project_root(cwd) / ".claude" / "insights" / ".insight_state.json"


def _default_state() -> dict:
    return {
        "session_models": {},
        "insight_turns": {},
    }


def _read_state(cwd: str | Path | None = None) -> dict:
    path = _insight_state_path(cwd)
    if not path.exists():
        return _default_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return _default_state()
    except (OSError, json.JSONDecodeError):
        return _default_state()
    defaults = _default_state()
    for key, value in defaults.items():
        if key not in state or not isinstance(state[key], type(value)):
            state[key] = value
    return state


def _write_state_unlocked(state: dict, cwd: str | Path | None = None) -> None:
    path = _insight_state_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".insight-state.{uuid.uuid4().hex}.tmp"
    try:
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _update_state(update, cwd: str | Path | None = None) -> None:
    path = _insight_state_path(cwd)
    with file_lock(path.parent / ".insight-state.lock"):
        state = _read_state(cwd)
        update(state)
        _write_state_unlocked(state, cwd)


def _append_bounded(state: dict, key: str, session_id: str) -> bool:
    entries = state.setdefault(key, [])
    if session_id in entries:
        return False
    entries.append(session_id)
    del entries[:-_MAX_SESSION_ENTRIES]
    return True


def get_session_model(session_id: str, cwd: str | Path | None = None) -> str:
    return _read_state(cwd).get("session_models", {}).get(session_id, "")


def set_session_model(session_id: str, model: str, cwd: str | Path | None = None) -> None:
    def update(state):
        models = state.setdefault("session_models", {})
        models[session_id] = model
        while len(models) > _MAX_SESSION_ENTRIES:
            del models[next(iter(models))]

    _update_state(update, cwd)


def get_last_insight_turn(session_id: str, cwd: str | Path | None = None) -> int:
    return int(_read_state(cwd).get("insight_turns", {}).get(session_id, 0))


def set_last_insight_turn(session_id: str, turns: int, cwd: str | Path | None = None) -> None:
    def update(state):
        turns_by_session = state.setdefault("insight_turns", {})
        turns_by_session[session_id] = turns
        while len(turns_by_session) > _MAX_SESSION_ENTRIES:
            del turns_by_session[next(iter(turns_by_session))]

    _update_state(update, cwd)
