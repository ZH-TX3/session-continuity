---
name: "Session: Save State"
description: 保存当前会话状态到 .claude/HANDOFF.md，供下个 session 加载
category: Session
tags: [session, handoff, continuity]
---

将当前会话状态写入 `.claude/HANDOFF.md`，供下一个 session 的 SessionStart hook 检测并提示用户。

## 执行步骤

1. **清理旧的 consumed 文件**：
   - 如果 `.claude/HANDOFF.consumed.md` 存在，先删除

2. 收集当前会话状态，按以下模板生成 HANDOFF.md：

```markdown
# Handoff — {日期时间}

## 本会话主题
{一句话描述本次 session 的核心目标}

## 完成的工作
{逐条列出}

## 下一步任务
{越具体越好}

## 关键决策与约束

## 相关文件

## Git 状态
{git status --short && git log --oneline -5}

## 注意事项
```

3. 写入 `.claude/HANDOFF.md`

4. 告知用户：HANDOFF.md 已写入，下次 /clear 时 SessionStart hook 会提示加载
