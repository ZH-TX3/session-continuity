"""SessionStart hook — 检测 Handoff，仅注入元数据。"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from handoff import handoff_path, read_metadata
from lib.config import get_config_value
from lib.insights import get_injection_text
from lib.paths import get_claude_dir, find_project_root, is_continuity_handler
from lib.state import is_session_prompted, mark_session_prompted, set_session_model

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


def relative_time(mtime: float) -> str:
    delta = max(0, datetime.now().timestamp() - mtime)
    if delta < 60:
        return f"{int(delta)} 秒前"
    if delta < 3600:
        return f"约 {int(delta // 60)} 分钟前"
    if delta < 86400:
        return f"约 {int(delta // 3600)} 小时前"
    return f"约 {int(delta // 86400)} 天前"


def build_handoff_message(metadata, mode: str) -> tuple[str, str]:
    mtime = datetime.fromtimestamp(metadata.mtime).strftime("%Y-%m-%d %H:%M")
    relative = relative_time(metadata.mtime)
    source_label = "手动保存" if metadata.source == "save-state" else "旧版格式"
    details = f"- 时间：{mtime}（{relative}）\n- 来源：{source_label}\n- 大小：{metadata.size} bytes"

    if mode == "ask-user-question":
        message = f"检测到待加载的 Handoff：\n{details}\n\n请发送任意消息后选择加载或跳过。"
        instruction = (
            "在回复用户下一条消息前，调用 AskUserQuestion 询问是否加载。"
            "若用户选择加载，直接 Read 当前项目 .claude/HANDOFF.md、展示内容，"
            "再将其移动到 .claude/session-continuity/history/；"
            "若选择跳过，不得读取正文，继续处理用户原始消息。"
        )
    else:
        message = f"检测到待加载的 Handoff：\n{details}\n\n请回复「加载」或「跳过」。"
        instruction = (
            "用户回复加载/load/yes/y 时，直接 Read 当前项目 .claude/HANDOFF.md、展示内容，"
            "再将其移动到 .claude/session-continuity/history/。"
            "用户回复跳过/不加载/skip/no/n 时，不得读取正文，继续当前会话。"
        )

    context = (
        "[待处理 HANDOFF.md]\n"
        f"- 路径: {metadata.path}\n"
        f"- 时间: {mtime}（{relative}）\n"
        f"- 来源: {metadata.source}\n"
        f"- 交互模式: {mode}\n\n"
        f"{instruction} 加载后只恢复状态，不自动执行旧任务。"
    )
    return message, context


def main() -> None:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return

    cwd = data.get("cwd")
    if not is_continuity_handler(cwd=cwd):
        log("SessionStart: plugin handler disabled", cwd)
        return
    try:
        project_root = find_project_root(cwd)
    except RuntimeError as error:
        log(f"SessionStart: {error}", cwd)
        return

    session_id = data.get("session_id", "")
    model = data.get("model", "")
    if model and session_id:
        set_session_model(session_id, model, project_root)

    source = data.get("source", "unknown")
    if source not in INJECT_SOURCES:
        log(f"SessionStart: source={source}, silent", project_root)
        return

    messages = []
    hook_output = {"hookEventName": "SessionStart"}
    path = handoff_path(project_root)
    metadata = read_metadata(path) if path.exists() else None
    if metadata and metadata.size > 0 and not (session_id and is_session_prompted(session_id, project_root)):
        stale_seconds = get_config_value("handoff.staleDays", 3, project_root) * 86400
        age_seconds = datetime.now().timestamp() - metadata.mtime
        if age_seconds > stale_seconds:
            stale_days = int(age_seconds // 86400)
            messages.append(f"存在 {stale_days} 天前的 Handoff，默认忽略；如需加载请回复「加载 handoff」。")
            hook_output["additionalContext"] = (
                f"[陈旧 HANDOFF.md]\n- 路径: {metadata.path}\n"
                "仅当用户明确要求加载时，才 Read 当前项目 .claude/HANDOFF.md 并移至 "
                ".claude/session-continuity/history/；否则不得读取正文。"
            )
        else:
            configured = get_config_value("handoff.promptMode", "reply", project_root)
            mode = "ask-user-question" if configured in {"ask", "ask-user-question"} else "reply"
            message, context = build_handoff_message(metadata, mode)
            messages.append(message)
            hook_output["additionalContext"] = context
        if session_id:
            mark_session_prompted(session_id, project_root)

    try:
        insights_text = get_injection_text(project_root / ".claude" / "insights" / "INDEX.md")
        if insights_text:
            messages.append(insights_text)
    except Exception as error:
        log(f"SessionStart: insights injection error: {error}", project_root)

    if messages:
        print(json.dumps({"systemMessage": "\n\n".join(messages), "hookSpecificOutput": hook_output}, ensure_ascii=False))


if __name__ == "__main__":
    main()
