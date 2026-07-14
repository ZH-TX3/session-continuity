---
name: save-state
description: |
  USE WHEN: 上下文接近满、任务切换、结束当前会话前需要保存状态以便下个 session 无缝衔接。
  DO NOT USE WHEN: 任务还在进行中且上下文充足，或只需一次性临时备忘。
argument-hint: "下一个 session 的主要任务是什么？（可选）"
user-invocable: true
---

将当前会话状态原子写入当前项目 `.claude/HANDOFF.md`，供下一个 session 的 SessionStart hook 检测。

## 执行步骤

1. 解析项目路径：优先使用 `CLAUDE_PROJECT_DIR`；否则从当前目录向上查找 `.claude/`。所有状态和临时文件必须留在该项目 `.claude/` 内。
2. 运行 `git status --short` 和 `git log --oneline -5`，收集当前 Git 状态。
3. 根据当前会话生成完整内容，使用以下模板：

```markdown
---
type: handoff
source: save-state
quality: curated
updated_at: "{ISO 8601 当前时间}"
trigger: manual-save-state
---

# Handoff — {日期时间}

## 本会话主题
{一句话描述本次 session 的核心目标}

## 完成的工作
{本次 session 完成了什么，逐条列出}

## 下一步任务
{下个 session 应优先做什么；如果用户提供参数，以参数为准}

## 关键决策与约束
{重要决策和不能改变的约束}

## 相关文件
{本次涉及的主要文件路径}

## Git 状态
{当前分支、未提交变更摘要、最近提交}

## 注意事项
{下个 session 需要特别注意的背景或风险}
```

4. 优先调用 `hooks/handoff.py` 的 `atomic_write()` 原子替换项目 `.claude/HANDOFF.md`；不得普通覆盖写入。
5. 不删除旧归档，也不写入插件目录或系统临时目录。
6. 告知用户保存路径；说明下次 `/clear` 或同项目新会话会询问加载。

## 失败处理

- 临时文件写入或原子替换失败时，不得声称保存成功；原有 `HANDOFF.md` 应保持可用。
- 不在 Stop 或 PreCompact 中自动执行本 Skill；第一份正式 Handoff 只由用户手动调用本 Skill 创建。
- 加载由用户确认后的普通对话流程处理：直接读取并归档 Handoff；本 Skill 不读取或消费 Handoff。
