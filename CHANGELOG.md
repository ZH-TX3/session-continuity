# Changelog

## 1.0.7 (2026-10-22)

### Added

- **确定性加载 Skill**：`skills/load-handoff/SKILL.md`，用户可调用。命令展开/技能结果走用户消息或工具结果通道，绕开 hook `additionalContext` 在非 Claude 模型链路上被忽略的问题。
- SessionStart 提示指向 `/load-handoff`，同时保留回复「跳过」与 `UserPromptSubmit` 兜底。

### Why

抓包确认 hook 注入内容确实进入了请求体，但位于用户消息之后的 `role: system` 消息中，且与 19–29 条其它 reminder 混在一起；`deepseek-v4.1-flash` 等模型不会读取该位置的指令。用户可调用的 Skill 走消息通道，可靠性更高。

## 1.0.6 (2026-10-22)

### Added

- **确定性加载命令**：新增 `/sc:load-handoff`。命令展开后作为用户消息下发，绕开 hook `additionalContext` 在非 Claude 模型链路上被忽略的问题。
- SessionStart 提示改为「输入 /sc:load-handoff 加载，或回复跳过」。

### Why

抓包确认 hook 注入内容确实进入了请求体，但位于用户消息之后的 `role: system` 消息中，且与 19–29 条其它 reminder 混在一起；`deepseek-v4.1-flash` 等模型不会读取该位置的指令。斜杠命令走用户消息通道，可靠性更高。

## 1.0.5 (2026-10-22)

### Changed

- **恢复 Handoff 主题锚点**：SessionStart 重新提取「## 本会话主题」第一行并写入 `systemMessage` 与 `additionalContext`，只读到该小节首个非空行，不注入正文。用于降低弱模型把「加载」误判为其它意图的概率。

## 1.0.4 (2026-10-15)

### Fixed

- **「加载」无上下文**：SessionStart 只在 `startup`/`clear` 注入指令；当会话来源为 `resume` 等时插件静默，模型收不到「加载 = 读取 HANDOFF.md」的说明，用户回复「加载」时不知所措。
- 新增 `UserPromptSubmit` 兜底 Hook：用户消息明确为「加载 / 跳过」且当前项目存在待处理 `HANDOFF.md` 时补注入指令，与 SessionStart 来源无关。
- 兜底仅在存在待处理 Handoff 时生效，普通消息与无 Handoff 场景保持静默；仍受 `handler` 项目归属约束。

## 1.0.3 (2026-07-18)

### Fixed

- **嵌套项目定位错误**：`find_project_root` 改为以事件 `cwd` 向上查找最近的项目，`CLAUDE_PROJECT_DIR` 降级为兜底。该环境变量固定为会话启动目录、不跟随工作目录切换，原先的优先级会让父仓库内含独立 `.claude` 的子项目把状态写到父项目，导致子项目的 `HANDOFF.md` 永远检测不到、新会话无任何提示且不写日志。
- **save-state 技能路径定位**：不再依赖可能缺失的 `CLAUDE_PLUGIN_ROOT` 环境变量，改为按磁盘路径搜索插件/项目的 `handoff.py`（marketplace → cache → 项目 hooks），找不到时内联原子写兜底，杜绝退化成普通文件覆盖。

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
