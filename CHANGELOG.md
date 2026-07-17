# Changelog

## 1.0.2 (2026-07-17)

### Changed

- **统一配置来源**：`handoff.promptMode` 由插件 `config/default.json` 提供默认值，项目 `.claude/session-continuity.json` 只按需覆盖。
- **显式项目定位**：插件 Hook 将事件对应项目路径传给配置加载器，避免依赖进程 cwd。
- **环境变量收敛**：Handoff 交互模式不再读取 `CLAUDE_HANDOFF_PROMPT_MODE`。

## 1.0.1 (2026-07-17)

### Fixed

- **处理器归属隔离**：改用当前项目 `.claude/session-continuity.json` 的 `handler`，不再读取会跨项目继承的 `CLAUDE_SESSION_CONTINUITY_HANDLER`。
- **插件默认接管**：未配置 `handler` 时默认由插件处理；保留项目 Hook 时显式设置 `{"handler": "project"}`。
- **SessionStart Handoff**：确认前只读取 frontmatter、mtime 和大小；加载后归档至项目 `.claude/session-continuity/history/`。
- **插件清单**：修正 `plugin.json` schema，并保留顶层中文描述。

### Changed

- **上下文预警**：70% 轻提示 `/save-state`，80% 强提示 `/save-state` 后 `/clear`，两级分别按 session 去重。
- **Insight 注入**：SessionStart 只注入 high/active 的前 3 条核心经验，约 200 token 预算。
- **状态布局**：统一为项目 `.claude/session-continuity/state.json`、`history/` 和 `logs/hook.log`。
- **PreCompact**：只提醒手动 `/save-state`，不自动创建 Handoff。

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
