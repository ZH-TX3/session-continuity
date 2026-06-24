"""路径查找逻辑 — 自动查找 .claude 目录"""

import os
from pathlib import Path


def find_project_root() -> Path:
    """从当前目录向上查找包含 .claude 的目录作为项目根目录。

    查找顺序:
    1. 从当前工作目录开始
    2. 向上遍历父目录
    3. 找到包含 .claude 的目录即返回
    4. 如果遍历到根目录仍未找到，返回当前工作目录

    Returns:
        Path: 项目根目录路径
    """
    # 优先使用环境变量 (如果设置)
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_root:
        root = Path(env_root)
        if root.is_dir():
            return root

    # 从当前目录向上查找
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent

    # 未找到，返回当前目录
    return Path.cwd()


def get_claude_dir() -> Path:
    """获取 .claude 目录路径。

    Returns:
        Path: .claude 目录路径
    """
    return find_project_root() / ".claude"


def get_config_path() -> Path:
    """获取插件配置文件路径。

    Returns:
        Path: .claude/session-continuity.json 的完整路径
    """
    return get_claude_dir() / "session-continuity.json"


def get_state_path() -> Path:
    """获取状态文件路径。

    Returns:
        Path: .claude/.hooks-state.json 的完整路径
    """
    return get_claude_dir() / ".hooks-state.json"


def get_handoff_path() -> Path:
    """获取 HANDOFF 文件路径。

    Returns:
        Path: .claude/HANDOFF.md 的完整路径
    """
    return get_claude_dir() / "HANDOFF.md"


def get_consumed_path() -> Path:
    """获取已消费的 HANDOFF 文件路径。

    Returns:
        Path: .claude/HANDOFF.consumed.md 的完整路径
    """
    return get_claude_dir() / "HANDOFF.consumed.md"


def get_insights_index_path() -> Path:
    """获取 Insights 索引文件路径。

    Returns:
        Path: .claude/insights/INDEX.md 的完整路径
    """
    return get_claude_dir() / "insights" / "INDEX.md"


def get_log_path() -> Path:
    """获取日志文件路径。

    Returns:
        Path: .claude/hooks/log/hook.log 的完整路径
    """
    log_dir = get_claude_dir() / "hooks" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "hook.log"
