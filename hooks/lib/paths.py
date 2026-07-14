"""路径查找逻辑 — 自动查找 .claude 目录。"""

import os
from pathlib import Path


def find_project_root(cwd: str | Path | None = None) -> Path:
    """优先使用 CLAUDE_PROJECT_DIR，否则从 cwd 向上查找 .claude。"""
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()

    current = Path(cwd) if cwd else Path.cwd()
    current = current.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".claude").is_dir():
            return candidate
    raise RuntimeError(f"无法从 {current} 定位包含 .claude 的项目目录")


def get_claude_dir(cwd: str | Path | None = None) -> Path:
    """获取项目 .claude 目录路径。"""
    return find_project_root(cwd) / ".claude"


def get_continuity_dir(cwd: str | Path | None = None) -> Path:
    return get_claude_dir(cwd) / "session-continuity"


def get_config_path(cwd: str | Path | None = None) -> Path:
    return get_claude_dir(cwd) / "session-continuity.json"


def get_state_path(cwd: str | Path | None = None) -> Path:
    return get_continuity_dir(cwd) / "state.json"


def get_handoff_path(cwd: str | Path | None = None) -> Path:
    return get_claude_dir(cwd) / "HANDOFF.md"


def get_insights_index_path(cwd: str | Path | None = None) -> Path:
    return get_claude_dir(cwd) / "insights" / "INDEX.md"


def get_log_path(cwd: str | Path | None = None) -> Path:
    log_dir = get_continuity_dir(cwd) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "hook.log"


def is_continuity_handler(handler: str = "plugin") -> bool:
    """确保项目 Hook 与插件 Hook 只启用一个主处理器。"""
    owner = os.environ.get("CLAUDE_SESSION_CONTINUITY_HANDLER", "project").strip().lower()
    return owner == handler
