"""Insight 注入工具 — 从 INDEX.md 筛选高质量条目。"""

from pathlib import Path

CATEGORY_LABELS = {
    "coding-patterns": "编码模式",
    "debugging-heuristics": "调试启发",
    "workflow-optimizations": "工作流",
    "domain-knowledge": "领域知识",
}

DOMAIN_FILES = ["coding-patterns.md", "debugging-heuristics.md", "workflow-optimizations.md", "domain-knowledge.md"]


def parse_index_rows(text: str) -> list:
    """解析 INDEX.md 的7列表格，跳过表头和分隔行。"""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = cells[1:-1]
        if len(cells) < 7:
            continue
        if cells[0] == "ID" or all(c.replace("-", "") == "" for c in cells[0]):
            continue
        rows.append({
            "id": cells[0],
            "summary": cells[1],
            "confidence": cells[2],
            "status": cells[3],
            "file": cells[4],
            "times_confirmed": cells[5],
            "last_seen": cells[6],
        })
    return rows


def get_injection_text(index_path) -> str:
    """从 INDEX.md 筛选注入文本。

    只取 confidence=high、status=active 的条目，
    按 times_confirmed 降序排列取 top 3，
    总 token 预算 200（len//4）。
    """
    index_path = Path(index_path)
    if not index_path.exists():
        return ""

    text = index_path.read_text(encoding="utf-8")
    rows = parse_index_rows(text)

    candidates = [r for r in rows if r["confidence"] == "high" and r["status"] == "active"]
    if not candidates:
        return ""

    candidates.sort(key=lambda r: (int(r["times_confirmed"] or "0"), r["last_seen"]), reverse=True)
    top = candidates[:3]

    lines = []
    for r in top:
        domain = Path(r["file"]).stem
        label = CATEGORY_LABELS.get(domain, domain)
        lines.append(f"- {r['summary']} [{label}]")

    result = f"[Insights] {len(lines)} 条核心经验：\n" + "\n".join(lines)

    while len(result) // 4 > 200 and lines:
        lines.pop()
        if lines:
            result = f"[Insights] {len(lines)} 条核心经验：\n" + "\n".join(lines)
        else:
            return ""

    return result
