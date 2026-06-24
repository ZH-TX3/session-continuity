"""SessionStart hook — 检测 Handoff，注入上下文"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加 lib 目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from lib.paths import get_handoff_path, get_insights_index_path, get_log_path
from lib.config import get_config_value
from lib.state import set_session_model

INJECT_SOURCES = {"startup", "clear"}


def log(msg: str) -> None:
    """写入日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = get_log_path()
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"[{ts}] {msg}\n")


def relative_time(mtime: float) -> str:
    """计算相对时间"""
    delta = datetime.now().timestamp() - mtime
    if delta < 60:
        return f"{int(delta)} seconds ago"
    if delta < 3600:
        return f"~{int(delta // 60)} minutes ago"
    if delta < 86400:
        return f"~{int(delta // 3600)} hours ago"
    return f"~{int(delta // 86400)} days ago"


def extract_topic(content: str) -> str:
    """从 HANDOFF.md 提取主题"""
    lines = content.splitlines()
    title = ""
    topic = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not title and stripped.startswith("# "):
            title = stripped.lstrip("# ").strip()
        if stripped.startswith("## 本会话主题") or stripped.startswith("## 主题"):
            for nxt in lines[i + 1 :]:
                if nxt.strip():
                    topic = nxt.strip()
                    break
            break
    if topic:
        return f"{title} — {topic}" if title else topic
    return title or "(no topic found)"


def main():
    """主函数"""
    # 设置 stdout 编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # 读取 stdin
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    log(f"SessionStart fired | stdin={raw}")

    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        log(f"SessionStart parse error: {e}")
        sys.exit(0)

    source = data.get("source", "unknown")
    model = data.get("model", "")

    # 保存模型信息
    if model:
        set_session_model(model)
        log(f"SessionStart: saved model={model}")

    if source not in INJECT_SOURCES:
        log(f"SessionStart: source={source}, skip injection")
        sys.exit(0)

    messages = []
    hook_output = {"hookEventName": "SessionStart"}

    # --- Handoff 检测 ---
    handoff_path = get_handoff_path()
    handoff_stale_seconds = get_config_value("handoff.staleDays", 3) * 86400
    handoff_prompt_mode = get_config_value("handoff.promptMode", "reply")

    if handoff_path.exists():
        content = handoff_path.read_text(encoding="utf-8").strip()
        if content:
            mtime = handoff_path.stat().st_mtime
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            rel_str = relative_time(mtime)
            topic = extract_topic(content)
            age_seconds = datetime.now().timestamp() - mtime

            if age_seconds > handoff_stale_seconds:
                # 陈旧 handoff
                stale_days = int(age_seconds // 86400)
                messages.append(
                    f"Found {stale_days}-day-old Handoff record (topic: {topic}).\n"
                    "Stale, ignored by default. Reply 'load handoff' to load it."
                )
                hook_output["additionalContext"] = (
                    f"[HANDOFF.md stale, silent]\n"
                    f"- Path: {handoff_path}\n"
                    f"- Time: {mtime_str} ({rel_str})\n"
                    f"- Topic: {topic}\n"
                    "\n"
                    "When user replies 'load handoff': Read .claude/HANDOFF.md -> show content -> mv to .consumed.md.\n"
                    "Otherwise: no action."
                )
                log(f"SessionStart: source={source}, handoff stale ({stale_days}d), silent (topic={topic})")
            else:
                mode = handoff_prompt_mode
                if mode == "ask":
                    mode = "ask-user-question"
                if mode not in {"reply", "ask-user-question"}:
                    mode = "reply"

                if mode == "ask-user-question":
                    messages.append(
                        f"Found previous session's Handoff record:\n"
                        f"- Topic: {topic}\n"
                        f"- Time: {mtime_str} ({rel_str})\n"
                        "\n"
                        "Send any message, then I will show load/skip options."
                    )
                    hook_output["additionalContext"] = (
                        f"[Pending HANDOFF.md]\n"
                        f"- Path: {handoff_path}\n"
                        f"- Time: {mtime_str} ({rel_str})\n"
                        f"- Topic: {topic}\n"
                        f"- Mode: ask-user-question\n"
                        "\n"
                        "Before replying to user's next message, call AskUserQuestion tool to ask whether to load this Handoff."
                        "The question MUST provide two options: 'Load' and 'Skip'."
                        "If user selects 'Load': Read .claude/HANDOFF.md, show content, then rename to .claude/HANDOFF.consumed.md."
                        "If user selects 'Skip': Do not read the file, continue processing user's original message."
                    )
                else:
                    messages.append(
                        f"Found previous session's Handoff record:\n"
                        f"- Topic: {topic}\n"
                        f"- Time: {mtime_str} ({rel_str})\n"
                        "\n"
                        "Reply 'load' to read and consume Handoff, or 'skip' to ignore."
                    )
                    hook_output["additionalContext"] = (
                        f"[Pending HANDOFF.md]\n"
                        f"- Path: {handoff_path}\n"
                        f"- Time: {mtime_str} ({rel_str})\n"
                        f"- Topic: {topic}\n"
                        f"- Mode: reply\n"
                        "\n"
                        "If user's next message is 'load', 'load handoff', 'yes', 'y': it means load the Handoff; "
                        "do not treat as normal chat, MUST Read .claude/HANDOFF.md, show content, then rename to .claude/HANDOFF.consumed.md.\n"
                        "If user's next message is 'skip', 'no', 'n': ignore the Handoff, do not read the file."
                    )
                log(f"SessionStart: source={source}, injected handoff mode={mode} (topic={topic})")

    # --- Insights 注入 ---
    insights_index_path = get_insights_index_path()
    try:
        if insights_index_path.exists():
            insights_text = insights_index_path.read_text(encoding="utf-8").strip()
            if insights_text:
                messages.append(insights_text)
    except Exception as e:
        log(f"SessionStart: insights injection error: {e}")

    # --- 输出 ---
    if messages:
        output = {
            "systemMessage": "\n\n".join(messages),
            "hookSpecificOutput": hook_output,
        }
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
