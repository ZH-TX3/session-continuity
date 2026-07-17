"""PreCompact hook — 只提醒手动保存，不自动创建 Handoff。"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from handoff import handoff_path
from lib.paths import get_claude_dir, find_project_root, is_continuity_handler


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
        data = {}

    cwd = data.get("cwd")
    if not is_continuity_handler(cwd=cwd):
        log("PreCompact: plugin handler disabled", cwd)
        return
    if data.get("trigger", "unknown") != "auto":
        log("PreCompact: non-auto trigger, silent", cwd)
        return
    try:
        project_root = find_project_root(cwd)
    except RuntimeError as error:
        log(f"PreCompact: {error}", cwd)
        return
    if handoff_path(project_root).exists():
        log("PreCompact: HANDOFF.md already exists, silent", project_root)
        return

    message = "上下文即将自动压缩；当前没有 Handoff。如需跨会话续接，请现在手动执行 /save-state。"
    log("PreCompact: reminded manual /save-state", project_root)
    print(json.dumps({"systemMessage": message}, ensure_ascii=False))


if __name__ == "__main__":
    main()
