"""PreCompact hook — 自动压缩前触发保存"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加 lib 目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from lib.paths import get_handoff_path, get_log_path


def log(msg: str) -> None:
    """写入日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = get_log_path()
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"[{ts}] {msg}\n")


def main():
    """主函数"""
    # 设置 stdout 编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # 读取 stdin
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    log(f"PreCompact fired | stdin={raw}")

    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    trigger = data.get("trigger", "unknown")

    if trigger != "auto":
        log(f"PreCompact: trigger={trigger}, skip injection")
        sys.exit(0)

    # HANDOFF.md 已存在时跳过自动保存 (保留用户手动 /save-state 的内容)
    handoff_path = get_handoff_path()
    if handoff_path.exists():
        log("PreCompact: HANDOFF.md exists, skip auto-save")
        sys.exit(0)

    instruction = (
        "[System: Context auto-compression detected]\n"
        "\n"
        "Please run `/save-state` immediately to save current session state before compression."
    )

    fallback_msg = (
        "HANDOFF auto-save may not have taken effect. Please run /save-state manually to save session state."
    )

    log("PreCompact: trigger=auto, injected auto-save instruction")

    print(
        json.dumps(
            {
                "systemMessage": fallback_msg,
                "hookSpecificOutput": {
                    "hookEventName": "PreCompact",
                    "additionalContext": instruction,
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
