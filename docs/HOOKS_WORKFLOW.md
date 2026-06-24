# Hooks + save-state 工作流体系

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        会话生命周期 (Session Lifecycle)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ SessionStart │───▶│   用户交互    │───▶│   PreCompact │───▶│    Stop    │ │
│  │   (开始)     │    │   (进行中)    │    │  (自动压缩)  │    │   (结束)   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                    │                 │        │
│         ▼                   ▼                    ▼                 ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ 检测 HANDOFF │    │ 手动保存状态  │    │ 自动保存提示  │    │ 上下文警告 │ │
│  │ 检测 Insights│    │  /save-state │    │   + Insight  │    │ + Insight  │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细流转链路

### 1️⃣ SessionStart (会话开始)

**触发时机**: 新会话、/clear、resume
**触发源过滤**: 仅 `source ∈ {"startup", "clear"}` 时注入

```
┌─────────────────────────────────────────────────────────┐
│  1. 保存模型信息到 .hooks-state.json                      │
│     → set_session_model(model)                          │
│                                                          │
│  2. 检测 .claude/HANDOFF.md                             │
│     ├─ 不存在 → 跳过                                    │
│     ├─ 存在但陈旧 (>3天) → 静默提示，不强制交互           │
│     └─ 存在且新鲜 (<3天) → 根据模式注入                   │
│                                                          │
│  3. 检测 .claude/insights/INDEX.md                     │
│     └─ 存在 → 注入 insights 到上下文                    │
└─────────────────────────────────────────────────────────┘
```

**注入方式** (`handoff.promptMode` 配置控制):

| 模式 | 值 | 行为 |
|------|-----|------|
| reply | `reply` (默认) | systemMessage 显示主题时间，提示回复「加载/跳过」；additionalContext 指令 Claude 将用户回复映射为动作 |
| ask-user-question | `ask-user-question` 或别名 `ask` | systemMessage 提示用户先发任意消息；additionalContext 指令 Claude 在下条消息前弹出 AskUserQuestion 工具 |

**陈旧 Handoff 处理** (超过 `handoff.staleDays` 天):
- 静默提示，不强制 AskUserQuestion，避免长期打扰
- 用户可手动回复「加载 handoff」触发加载

---

### 2️⃣ 用户交互 (会话进行中)

**手动触发 `/save-state`**:

```
┌─────────────────────────────────────────────────────────┐
│  1. 删除旧的 HANDOFF.consumed.md (避免堆积)             │
│  2. 收集会话状态 (主题/工作/任务/决策/文件/Git)          │
│  3. 写入 .claude/HANDOFF.md                            │
│  4. 告知用户: 下次 /clear 时 SessionStart 会提示加载     │
└─────────────────────────────────────────────────────────┘
```

**HANDOFF.md 模板**:

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

---

### 3️⃣ PreCompact (自动压缩)

**触发时机**: 上下文自动压缩 (`trigger=auto`)
**前置条件**: `HANDOFF.md` 不存在时才注入

```
┌─────────────────────────────────────────────────────────┐
│  注入 additionalContext:                                 │
│    "[系统检测：上下文即将自动压缩]"                        │
│    "请立即执行 /save-state 保存当前会话状态"              │
│                                                          │
│  为什么检查 HANDOFF.md 是否存在?                         │
│    → 避免覆盖用户手动 /save-state 的内容                 │
│    → 保留用户意图                                        │
└─────────────────────────────────────────────────────────┘
```

---

### 4️⃣ Stop (会话结束)

**触发时机**: 会话停止

```
┌─────────────────────────────────────────────────────────┐
│  1. 读取 transcript 最后一条消息的 usage                  │
│     ├─ 无 transcript → 跳过上下文检查                     │
│     ├─ usage=0 → 跳过上下文检查                          │
│     └─ usage>0 → 计算使用比例                            │
│                                                          │
│  2. 上下文警告逻辑 (仅警告一次)                           │
│     └─ if used/context_limit >= context.criticalThreshold│
│        → 注入警告: "建议执行 /save-state + /clear"        │
│        → 标记 session 为已警告 (warned_sessions)         │
│                                                          │
│  3. 始终追加 Insight 评估提示 (如果 insight.enabled)      │
│     → 检查是否有值得记录的 insight                       │
│     → 引导 Claude 按 agent-evolution.md 格式记录        │
└─────────────────────────────────────────────────────────┘
```

**上下文限制判断**:
- 默认 200K tokens
- 模型名含 `[1M]` 时使用 1M tokens
- 阈值: 通过 `context.criticalThreshold` 配置 (默认 0.80)

---

### 5️⃣ Handoff 加载 (下个会话)

**触发条件**: 用户回复「加载」或通过 AskUserQuestion 选择「加载」

```
┌─────────────────────────────────────────────────────────┐
│  1. Read .claude/HANDOFF.md                            │
│  2. 展示内容给用户                                       │
│  3. mv .claude/HANDOFF.md → .claude/HANDOFF.consumed.md│
│  4. 继续执行下一步任务                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 数据流与状态管理

### 文件结构

```
.claude/
├── session-continuity.json  ← 插件配置 (可选)
├── HANDOFF.md               ← save-state 写入，SessionStart 读取
├── HANDOFF.consumed.md      ← 加载后重命名，避免重复加载
├── .hooks-state.json        ← 共享状态 (session_model, prompted_sessions, warned_sessions)
│
└── insights/
    └── INDEX.md             ← Insights 索引，SessionStart 注入
```

### 状态文件 (.hooks-state.json)

```json
{
  "session_model": "claude-opus-4-8[1M]",
  "prompted_sessions": ["session-id-1"],
  "warned_sessions": ["session-id-2", "session-id-3"]
}
```

| 字段 | 用途 |
|------|------|
| `session_model` | 当前 session 的模型名称，用于判断上下文大小 (200K vs 1M) |
| `prompted_sessions` | 已提示过 handoff 的 session ID 列表 (去重) |
| `warned_sessions` | 已警告过上下文超限的 session ID 列表 (去重) |

---

## 配置说明

### 配置文件位置

`.claude/session-continuity.json` (项目级，可选)

### 配置项

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `handoff.promptMode` | `"reply"` | Handoff 交互模式: `reply` 或 `ask-user-question` |
| `handoff.staleDays` | `3` | Handoff 陈旧阈值 (天) |
| `handoff.autoLoadMaxAge` | `3600` | 自动加载阈值 (秒) |
| `context.earlyWarningThreshold` | `0.70` | 早期预警阈值 |
| `context.criticalThreshold` | `0.80` | 严重警告阈值 |
| `context.forceSaveThreshold` | `0.85` | 强制保存阈值 |
| `insight.enabled` | `true` | 是否启用 insight 评估 |
| `insight.minMessages` | `10` | 最少消息数才触发 insight 评估 |

---

## 关键设计点

| 组件 | 核心职责 | 注入方式 |
|------|---------|---------|
| **SessionStart** | 检测 HANDOFF，引导用户决策 | `additionalContext` + `systemMessage` |
| **PreCompact** | 自动压缩前触发保存 | `additionalContext` |
| **Stop** | 上下文警告 + Insight 评估 | `systemMessage` |
| **save-state skill** | 手动保存会话状态 | 写文件 + 通知用户 |

**核心机制**: 不依赖 `systemMessage` 驱动模型行为，改用 `additionalContext`（以 `<system-reminder>` 呈现给 Claude），确保指令被正确执行。

---

## 完整生命周期示例

```
会话 A:
  1. 用户开始工作...
  2. 上下文接近满 → Stop hook 警告 (≥context.criticalThreshold)
  3. 用户执行 /save-state
     → 写入 .claude/HANDOFF.md
  4. 用户执行 /clear

会话 B:
  1. SessionStart hook 触发
     → 检测到 HANDOFF.md (新鲜 <handoff.staleDays 天)
     → 注入 additionalContext (模式: handoff.promptMode)
  2. 用户发送第一条消息
     → Claude 弹出 AskUserQuestion: 加载 / 跳过
  3. 用户选择「加载」
     → Claude 读取 HANDOFF.md
     → 重命名为 HANDOFF.consumed.md
     → 展示内容，继续执行任务
  4. 会话正常进行...
  5. 自动压缩触发 → PreCompact hook
     → 检测 HANDOFF.md 不存在 → 注入 /save-state 提示
     → 用户执行 /save-state → 写入新 HANDOFF.md
  6. 会话结束 → Stop hook
     → 追加 Insight 评估提示
```

---

## 故障排查

| 现象 | 可能原因 | 解决方案 |
|------|---------|---------|
| SessionStart 未注入 HANDOFF | source 不在 {"startup", "clear"} | 检查 hook.log，确认 source 值 |
| 用户选择「加载」后 Claude 未读取 | additionalContext 被吞掉 | 检查运行环境是否支持 `<system-reminder>` |
| PreCompact 未触发保存 | HANDOFF.md 已存在 | 符合预期，避免覆盖用户手动保存 |
| Stop 未警告上下文 | usage=0 或 transcript 不存在 | 检查 hook.log 中的 usage 值 |
| 陈旧 Handoff 一直提示 | handoff.staleDays 设置过短 | 调整配置文件中的 staleDays |
| 配置未生效 | 配置文件路径错误 | 确认 `.claude/session-continuity.json` 存在 |

---

## 相关文件

- `hooks/session-start.py` — SessionStart hook 实现
- `hooks/stop-monitor.py` — Stop hook 实现
- `hooks/pre-compact.py` — PreCompact hook 实现
- `hooks/lib/paths.py` — 路径查找逻辑
- `hooks/lib/config.py` — 配置加载
- `hooks/lib/state.py` — 状态管理
- `config/default.json` — 默认配置
- `skills/save-state/SKILL.md` — /save-state skill 定义
- `commands/save-state.md` — /save-state 命令定义
