# Session Continuity Plugin

会话连续性管理插件 — 为 Claude Code 提供 Handoff 保存/加载、上下文预警和 Insight 捕获功能。

## 功能特性

- **Handoff 检测**: 新会话开始时自动检测遗留的 HANDOFF.md，提示用户加载或跳过
- **上下文预警**: 当上下文使用达到阈值时警告用户，建议保存状态
- **自动保存提醒**: 上下文压缩前提醒手动执行 `/save-state`，避免丢失工作进度
- **Insight 捕获**: 会话结束时评估是否有值得记录的 insight
- **灵活配置**: 支持项目级配置，可自定义阈值和行为

## 安装

```bash
# 注册本地 marketplace 后安装
claude plugins marketplace add ./session-continuity
claude plugins install sc@sc
```

## 启用

```bash
claude plugins enable sc@sc
```

## 配置

在项目根目录创建 `.claude/session-continuity.json`:

```json
{
  "handler": "plugin",
  "handoff": {
    "promptMode": "reply",
    "staleDays": 3,
    "autoLoadMaxAge": 3600
  },
  "context": {
    "earlyWarningThreshold": 0.70,
    "criticalThreshold": 0.80,
    "forceSaveThreshold": 0.85
  },
  "insight": {
    "enabled": true,
    "minMessages": 10
  }
}
```

### 配置说明

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `handler` | `"plugin"` | 主处理器；保留项目级 Hook 时显式设为 `"project"` |
| `handoff.promptMode` | `"reply"` | Handoff 交互模式: `reply` 或 `ask-user-question` |
| `handoff.staleDays` | `3` | Handoff 陈旧阈值 (天) |
| `handoff.autoLoadMaxAge` | `3600` | 自动加载阈值 (秒) |
| `context.earlyWarningThreshold` | `0.70` | 早期预警阈值 |
| `context.criticalThreshold` | `0.80` | 严重警告阈值 |
| `context.forceSaveThreshold` | `0.85` | 强制保存阈值 |
| `insight.enabled` | `true` | 是否启用 insight 评估 |
| `insight.minMessages` | `10` | 最少消息数才触发 insight 评估 |

`handler` 只从当前项目配置读取；插件不使用 `CLAUDE_SESSION_CONTINUITY_HANDLER` 环境变量。这样父进程或其他项目的环境不会改变当前项目的处理器归属。

## 使用

### 自动功能

插件安装后自动生效：
- 新会话开始时检测 HANDOFF.md
- 上下文达到 70% 时轻提示保存，达到 80% 时强提示保存并 `/clear`
- 自动压缩前提醒手动执行 `/save-state`
- 会话结束时评估 insight

### 手动保存

执行 `/save-state` 手动保存当前会话状态。

## 工作流程

```
会话 A:
  1. 用户工作...
  2. 上下文 ≥70% → 提醒执行 `/save-state`
  3. 上下文 ≥80% → 强提示执行 `/save-state` 后 `/clear`
  4. 用户执行 /save-state
  5. 用户执行 /clear

会话 B:
  1. SessionStart 检测到 HANDOFF.md
  2. 提示用户加载或跳过
  3. 用户选择加载 → 展示正文并归档到 `.claude/session-continuity/history/`
```

## 文件结构

```
.claude/
├── session-continuity.json  # 插件配置 (可选)
├── HANDOFF.md               # 会话交接文件
├── session-continuity/
│   ├── state.json          # 按项目保存模型、去重和 Insight 节流状态
│   ├── history/            # 最近 10 份已加载 Handoff
│   └── logs/hook.log
└── insights/INDEX.md       # 可选的 Insight 索引
```

## 依赖

- Python 3.10+
- Claude Code

## 许可证

MIT
