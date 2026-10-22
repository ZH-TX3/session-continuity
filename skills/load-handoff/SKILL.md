---
name: load-handoff
description: |
  加载当前项目的 Handoff：读取 .claude/HANDOFF.md、展示内容，并归档到 .claude/session-continuity/history/。
  USE WHEN: 用户输入「加载」「加载Handoff」「/load-handoff」、要求恢复上一次会话状态，或在新会话中选择加载 Handoff。
argument-hint: ""
user-invocable: true
---

加载当前项目的 Handoff。

1. 定位项目根目录：优先使用环境变量 `CLAUDE_PROJECT_DIR`；否则使用当前工作目录。
2. 直接读取 `<项目根>/.claude/HANDOFF.md`。如果文件不存在，明确告知用户「当前项目没有 HANDOFF.md」，然后停止，不要到其它目录搜索。
3. 把文件内容展示给用户。
4. 将文件移动到 `<项目根>/.claude/session-continuity/history/`，命名为 `<YYYYMMDD-HHMMSS>--<source>--HANDOFF.md`；目录不存在时先创建。若同名文件已存在，追加 `--1`、`--2` 等后缀，不要覆盖。
5. 只恢复状态并简要总结，不要自动执行 Handoff 中列出的旧任务；等待用户的下一步指令。
