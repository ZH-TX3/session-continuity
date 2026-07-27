"""SessionStart Insight 注入 Hook。

独立于 session-continuity，在 startup/clear 来源时
从 INDEX.md 注入已确认的高优先级 Insight 摘要。
"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from lib.insight_state import set_session_model
from lib.insights import get_injection_text
from lib.paths import find_project_root, get_claude_dir

INJECT_SOURCES = {"startup", "clear"}


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
    try:
        project_root = find_project_root(cwd)
    except RuntimeError:
        return

    session_id = data.get("session_id", "")
    model = data.get("model", "")
    if model and session_id:
        set_session_model(session_id, model, cwd)

    source = data.get("source", "unknown")
    if source not in INJECT_SOURCES:
        log(f"InsightStart: source={source}, silent", cwd)
        return

    messages = []

    try:
        insights_text = get_injection_text(project_root / ".claude" / "insights" / "INDEX.md")
        if insights_text:
            messages.append(insights_text)
    except Exception as error:
        log(f"InsightStart: injection error: {error}", cwd)

    if messages:
        print(json.dumps({"systemMessage": "\n\n".join(messages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
