"""Stop hook — 上下文预警。"""

import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from lib.config import get_config_value
from lib.paths import get_claude_dir, find_project_root, is_continuity_handler
from lib.state import (
    get_session_model,
    is_session_warned,
    is_session_warned_early,
    mark_session_warned,
    mark_session_warned_early,
)

CONTEXT_LIMIT_DEFAULT = 200_000
CONTEXT_LIMIT_1M = 1_000_000


def log(message: str, cwd: str | Path | None = None) -> None:
    try:
        log_path = get_claude_dir(cwd) / "session-continuity" / "logs" / "hook.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8", errors="replace") as stream:
            stream.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def read_last_usage(transcript_path: str) -> dict | None:
    path = Path(transcript_path)
    if not path.exists():
        return None
    last_line = None
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.strip():
                last_line = line.strip()
    if not last_line:
        return None
    try:
        return json.loads(last_line).get("message", {}).get("usage")
    except json.JSONDecodeError:
        return None


def get_context_limit(session_id: str, cwd: str | Path | None = None) -> int:
    return CONTEXT_LIMIT_1M if re.search(r"1m\b", get_session_model(session_id, cwd).lower()) else CONTEXT_LIMIT_DEFAULT


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
        project_root = cwd
    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path")
    messages = []

    if transcript_path:
        usage = read_last_usage(transcript_path)
        if usage:
            used = usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
            if used > 0:
                limit = get_context_limit(session_id, project_root)
                ratio = used / limit
                early_threshold = get_config_value("context.earlyWarningThreshold", 0.70, project_root)
                critical_threshold = get_config_value("context.criticalThreshold", 0.80, project_root)
                if ratio >= early_threshold and not is_session_warned_early(session_id, project_root):
                    mark_session_warned_early(session_id, project_root)
                    messages.append(
                        f"💡 上下文已用 {int(ratio * 100)}%（{used:,} / {limit:,} tokens）。\n"
                        "建议：执行 /save-state 保存当前状态。\n"
                        "本会话不再重复提示。"
                    )
                if ratio >= critical_threshold and not is_session_warned(session_id, project_root):
                    mark_session_warned(session_id, project_root)
                    messages.append(
                        f"⚠️ 上下文已用 {int(ratio * 100)}%（{used:,} / {limit:,} tokens）。\n"
                        "建议：执行 /save-state 保存当前状态后 /clear 开新会话。\n"
                        "本会话不再重复提示。"
                    )

    if messages:
        print(json.dumps({"systemMessage": "\n\n".join(messages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

