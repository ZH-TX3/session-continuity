"""Stop hook — 上下文预警 + Insight 评估"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加 lib 目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from lib.paths import get_log_path
from lib.config import get_config_value
from lib.state import get_session_model, is_session_warned, mark_session_warned

CONTEXT_LIMIT_DEFAULT = 200_000
CONTEXT_LIMIT_1M = 1_000_000

INSIGHT_EVALUATION_PROMPT = (
    "[Insight Capture] 回顾本次会话，评估是否有值得记录的 insight：\n"
    "- 用户是否纠正了你的行为？\n"
    "- 用户是否确认了非显而易见的做法？\n"
    "- 是否找到任务失败的根因？\n"
    "- 是否有重复出现的模式？\n"
    "如有，按 .claude/rules/agent-evolution.md 的格式记录。如无，忽略此提示。"
)


def log(msg: str) -> None:
    """写入日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = get_log_path()
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"[{ts}] {msg}\n")


def read_last_usage(transcript_path: str) -> dict | None:
    """读取 transcript 最后一条消息的 usage"""
    p = Path(transcript_path)
    if not p.exists():
        return None
    last_line = None
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                last_line = line
    if not last_line:
        return None
    try:
        d = json.loads(last_line)
        return d.get("message", {}).get("usage")
    except Exception:
        return None


def get_context_limit() -> int:
    """从状态文件读取 model，判断上下文大小"""
    model = get_session_model()
    return CONTEXT_LIMIT_1M if "[1M]" in model else CONTEXT_LIMIT_DEFAULT


def main():
    """主函数"""
    # 设置 stdout 编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # 读取 stdin
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    log(f"Stop fired | stdin_keys={list(json.loads(raw).keys()) if raw.strip() else []}")

    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        log(f"Stop parse error: {e}")
        print(json.dumps({"systemMessage": INSIGHT_EVALUATION_PROMPT}, ensure_ascii=False))
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path")

    messages = []

    # --- 上下文预警逻辑 ---
    if transcript_path:
        usage = read_last_usage(transcript_path)
        if usage:
            CONTEXT_LIMIT = get_context_limit()
            used = (
                usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
            )
            if used > 0:
                ratio = used / CONTEXT_LIMIT
                log(f"Stop: session={session_id}, used={used:,}/{CONTEXT_LIMIT:,} ({ratio:.2%})")

                critical_threshold = get_config_value("context.criticalThreshold", 0.80)

                if ratio >= critical_threshold:
                    if not is_session_warned(session_id):
                        mark_session_warned(session_id)
                        pct = int(ratio * 100)
                        messages.append(
                            f"[WARNING] Context at {pct}% ({used:,} / {CONTEXT_LIMIT:,} tokens).\n"
                            "Suggestion: Run /save-state then /clear to start a new session.\n"
                            "This warning will not repeat in this session."
                        )
                        log(f"Stop: session={session_id}, warned at {pct}%")
                    else:
                        log(f"Stop: session={session_id} already warned, skip warning")
            else:
                log(f"Stop: usage sum=0, skip context check ({usage})")
        else:
            log(f"Stop: no usage in transcript {transcript_path}, skip context check")
    else:
        log("Stop: no transcript_path, skip context check")

    # --- Insight 评估 ---
    insight_enabled = get_config_value("insight.enabled", True)
    if insight_enabled:
        messages.append(INSIGHT_EVALUATION_PROMPT)

    # --- 输出 ---
    output = "\n\n".join(messages)
    log(f"Stop: outputting {len(messages)} message(s)")

    print(
        json.dumps(
            {
                "systemMessage": output,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
