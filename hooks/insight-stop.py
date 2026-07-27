"""Stop Insight 评估提醒 Hook。

独立于上下文告警逻辑，在满足特定信号时提示模型评估是否需要记录 Insight。
受 insight.enabled 配置控制。
"""

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
from lib.insight_state import get_last_insight_turn, get_session_model, set_last_insight_turn
from lib.paths import find_project_root, get_claude_dir

CONTEXT_LIMIT_DEFAULT = 200_000
CONTEXT_LIMIT_1M = 1_000_000
EARLY_THRESHOLD = 0.70

INSIGHT_TURN_INTERVAL = 10
_NOISE_RE = re.compile(r"^<[^>]+>", re.MULTILINE)
_EXIT_KEYWORDS = (
    "结束", "收工", "搞定", "先这样", "拜", "再见", "done", "thanks",
    "that's all", "总结一下", "今天到这", "辛苦",
)

INSIGHT_EVALUATION_PROMPT = (
    "[Insight Capture] 回顾本次会话，评估是否有值得记录的 insight：\n"
    "- 用户是否纠正了你的行为？\n"
    "- 用户是否确认了非显而易见的做法？\n"
    "- 是否找到任务失败的根因？\n"
    "- 是否有重复出现的模式？\n"
    "如有，按 .claude/rules/agent-evolution.md 的格式记录。如无，忽略此提示。"
)


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


def scan_transcript(transcript_path: str) -> tuple[int, str]:
    path = Path(transcript_path)
    if not path.exists():
        return 0, ""
    turns = 0
    last_user_text = ""
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            if entry.get("type") == "assistant" and message.get("role") == "assistant":
                turns += 1
            elif entry.get("type") == "user" and message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = "".join(block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text")
                else:
                    text = ""
                text = _NOISE_RE.sub("", text).strip()
                if text:
                    last_user_text = text
    return turns, last_user_text


def looks_like_exit(user_text: str) -> bool:
    return any(keyword in user_text.lower().strip() for keyword in _EXIT_KEYWORDS)


def main() -> None:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        print(json.dumps({"systemMessage": INSIGHT_EVALUATION_PROMPT}, ensure_ascii=False))
        return

    cwd = data.get("cwd")
    try:
        project_root = find_project_root(cwd)
    except RuntimeError:
        project_root = Path(cwd) if cwd else Path.cwd()

    if not get_config_value("insight.enabled", True, cwd):
        return

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path")

    ratio = 0.0
    if transcript_path:
        usage = read_last_usage(transcript_path)
        if usage:
            used = usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
            if used > 0:
                ratio = used / get_context_limit(session_id, cwd)

    turns, last_user_text = scan_transcript(transcript_path) if transcript_path else (0, "")
    is_early = ratio >= EARLY_THRESHOLD

    if (
        looks_like_exit(last_user_text)
        or is_early
        or turns - get_last_insight_turn(session_id, cwd) >= INSIGHT_TURN_INTERVAL
    ):
        set_last_insight_turn(session_id, turns, cwd)
        print(json.dumps({"systemMessage": INSIGHT_EVALUATION_PROMPT}, ensure_ascii=False))


if __name__ == "__main__":
    main()
