---
name: save-state
description: |
  USE WHEN: 上下文接近满、任务切换、结束当前会话前需要保存状态以便下个 session 无缝衔接。
  DO NOT USE WHEN: 任务还在进行中且上下文充足，或仅需要临时备忘（用 mktemp handoff 即可）。
argument-hint: "下一个 session 的主要任务是什么？（可选）"
user-invocable: true
---

将当前会话状态写入 `.claude/HANDOFF.md`，供下一个 session 的 SessionStart hook 检测并提示用户。

## 执行步骤

1. **清理旧的 consumed 文件**：
   - 如果 `.claude/HANDOFF.consumed.md` 存在，先删除（避免历史 consumed 堆积）

2. 收集当前会话状态，按以下模板生成 HANDOFF.md 内容：

```markdown
# Handoff — {日期时间}

## 本会话主题
{一句话描述本次 session 的核心目标}

## 完成的工作
{本次 session 完成了什么，逐条列出}

## 下一步任务
{下个 session 应该优先做什么，越具体越好}
{如果用户提供了参数，以参数为准}

## 关键决策与约束
{本次做了哪些重要决策，有哪些不能改变的约束}

## 相关文件
{本次涉及的主要文件路径}

## Git 状态
{当前分支、未提交的变更摘要}

## 注意事项
{下个 session 需要特别注意的坑或背景}
```

3. 将内容写入 `.claude/HANDOFF.md`（覆盖写入）。

4. 运行 `git status --short` 和 `git log --oneline -5` 补充 Git 状态部分。

5. 告知用户：HANDOFF.md 已写入，下次 `/clear` 或新开会话时 SessionStart hook 会提示是否加载。

## 加载 handoff 流程（用户说"加载 handoff"时）

1. 读取 `.claude/HANDOFF.md` 全文
2. 把它重命名为 `.claude/HANDOFF.consumed.md`（消费标记）
3. 告知用户已加载哪些内容、下一步要做什么
