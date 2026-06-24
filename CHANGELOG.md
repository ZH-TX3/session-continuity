# Changelog

## 1.0.0 (2026-06-24)

### Features

- **SessionStart hook**: 检测 HANDOFF.md，支持 reply 和 ask-user-question 两种交互模式
- **Stop hook**: 上下文预警 (可配置阈值) + Insight 评估
- **PreCompact hook**: 自动压缩前触发保存
- **配置系统**: 支持 `.claude/session-continuity.json` 项目级配置
- **路径查找**: 自动查找 .claude 目录，兼容跨平台
- **状态管理**: 统一状态文件 `.claude/.hooks-state.json`
- **save-state skill**: 手动保存会话状态
- **save-state command**: /save-state 命令定义

### Configuration

- `handoff.promptMode`: Handoff 交互模式 (reply/ask-user-question)
- `handoff.staleDays`: Handoff 陈旧阈值 (天)
- `handoff.autoLoadMaxAge`: 自动加载阈值 (秒)
- `context.earlyWarningThreshold`: 早期预警阈值
- `context.criticalThreshold`: 严重警告阈值
- `context.forceSaveThreshold`: 强制保存阈值
- `insight.enabled`: 是否启用 insight 评估
- `insight.minMessages`: 最少消息数才触发 insight 评估
