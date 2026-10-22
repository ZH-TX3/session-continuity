"""UserPromptSubmit hook — 用户明确回复「加载/跳过」时的 Handoff 兜底注入。

SessionStart 只在 startup/clear 注入指令。若会话以 resume 等来源启动，
模型不会收到「加载 = 读取 HANDOFF.md」的说明，用户回复「加载」时会一头雾水。
本 Hook 在用户消息明确表示加载/跳过、且当前项目存在待处理 HANDOFF.md 时补注入。
"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from handoff import handoff_path, read_metadata
from lib.paths import get_claude_dir, find_project_root, is_continuity_handler

LOAD_TOKENS = {"加载", "载入", "加载吧", "加载handoff", "加载 handoff", "load", "load handoff"}
SKIP_TOKENS = {"跳过", "不加载", "跳过handoff", "跳过 handoff", "skip", "skip handoff"}


def log(message: str, cwd: str | Path | None = None) -> None:
    try:
        log_path = get_claude_dir(cwd) / "session-continuity" / "logs" / "hook.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8", errors="replace") as stream:
            stream.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def main() -> None:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return

    cwd = data.get("cwd")
    if not is_continuity_handler(cwd=cwd):
        return
    try:
        project_root = find_project_root(cwd)
    except RuntimeError:
        return

    prompt = str(data.get("prompt", "")).strip().lower()
    if prompt not in LOAD_TOKENS and prompt not in SKIP_TOKENS:
        return

    path = handoff_path(project_root)
    metadata = read_metadata(path) if path.exists() else None
    if metadata is None or metadata.size == 0:
        return

    if prompt in LOAD_TOKENS:
        action = "load"
        context = (
            "[Handoff 加载请求]\n"
            f"- 路径: {metadata.path}\n\n"
            "用户要求加载 Handoff。请直接 Read 当前项目 .claude/HANDOFF.md、展示内容，"
            "再将其移动到 .claude/session-continuity/history/。"
            "加载后只恢复状态，不自动执行其中的旧任务。"
        )
    else:
        action = "skip"
        context = (
            "[Handoff 跳过]\n"
            "用户选择跳过 Handoff。不得读取 .claude/HANDOFF.md 正文，继续处理用户原始需求。"
        )

    log(f"UserPromptSubmit: injected handoff {action} action", project_root)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
