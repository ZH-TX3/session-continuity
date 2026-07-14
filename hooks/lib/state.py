"""状态管理模块 — 跨 hooks 共享状态。"""

import json
import os
import uuid
from pathlib import Path

from locking import file_lock
from .paths import get_state_path

_MAX_SESSION_ENTRIES = 100


def _default_state() -> dict:
    return {
        "session_models": {},
        "prompted_sessions": [],
        "warned_sessions": [],
        "insight_turns": {},
    }


def _read_state(cwd: str | Path | None = None) -> dict:
    state_path = get_state_path(cwd)
    if not state_path.exists():
        return _default_state()
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return _default_state()
    except (OSError, json.JSONDecodeError):
        return _default_state()

    defaults = _default_state()
    for key, value in defaults.items():
        if key not in state or not isinstance(state[key], type(value)):
            state[key] = value
    state.pop("session_model", None)
    return state


def _write_state_unlocked(state: dict, cwd: str | Path | None = None) -> None:
    state_path = get_state_path(cwd)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.parent / f".state.{uuid.uuid4().hex}.tmp"
    try:
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, state_path)
    finally:
        temporary.unlink(missing_ok=True)


def _update_state(update, cwd: str | Path | None = None) -> None:
    state_path = get_state_path(cwd)
    with file_lock(state_path.parent / ".state.lock"):
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


def is_session_prompted(session_id: str, cwd: str | Path | None = None) -> bool:
    return session_id in _read_state(cwd).get("prompted_sessions", [])


def mark_session_prompted(session_id: str, cwd: str | Path | None = None) -> None:
    _update_state(lambda state: _append_bounded(state, "prompted_sessions", session_id), cwd)


def is_session_warned(session_id: str, cwd: str | Path | None = None) -> bool:
    return session_id in _read_state(cwd).get("warned_sessions", [])


def mark_session_warned(session_id: str, cwd: str | Path | None = None) -> None:
    _update_state(lambda state: _append_bounded(state, "warned_sessions", session_id), cwd)


def is_session_warned_early(session_id: str, cwd: str | Path | None = None) -> bool:
    return session_id in _read_state(cwd).get("warned_sessions_early", [])


def mark_session_warned_early(session_id: str, cwd: str | Path | None = None) -> None:
    _update_state(lambda state: _append_bounded(state, "warned_sessions_early", session_id), cwd)


def get_last_insight_turn(session_id: str, cwd: str | Path | None = None) -> int:
    return int(_read_state(cwd).get("insight_turns", {}).get(session_id, 0))


def set_last_insight_turn(session_id: str, turns: int, cwd: str | Path | None = None) -> None:
    def update(state):
        turns_by_session = state.setdefault("insight_turns", {})
        turns_by_session[session_id] = turns
        while len(turns_by_session) > _MAX_SESSION_ENTRIES:
            del turns_by_session[next(iter(turns_by_session))]

    _update_state(update, cwd)
