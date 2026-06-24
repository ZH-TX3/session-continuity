# Hooks 优化 TODO

基于当前 Hooks + save-state 工作流的评估，以下为待优化项。

---

## P0 - 关键改进

### 1. PreCompact Hook 直接写 Handoff

**问题**: 当前依赖 Claude 执行 `/save-state`，存在竞态风险（上下文接近满时可能来不及执行）

**方案**: Hook 层直接从 transcript 提取摘要写入 HANDOFF.md

**改动文件**: `hooks/pre-compact.py`

**预期收益**: 消除竞态，确保压缩前必有 Handoff

---

### 2. 上下文 70% 自动保存

**问题**: 当前仅 80% 警告，预警太晚

**方案**:
- 70%: 早期预警 + Hook 层自动保存
- 80%: 严重警告 (保持现有)
- 85%: 强制保存 + 建议立即 /clear

**改动文件**: `hooks/stop-monitor.py`

**预期收益**: 更早兜底，减少丢失上下文的风险

---

## P1 - 体验优化

### 3. 智能 Insight 评估

**问题**: Stop hook 始终注入 Insight 提示，短会话无意义

**方案**:
- 会话 < 10 条消息 → 不提示
- 检测到错误/修正/失败信号 → 提示
- 否则 → 跳过

**改动文件**: `hooks/stop-monitor.py`

**预期收益**: 减少无意义 Insight 提示，节省 token

---

### 4. 1 小时内 Handoff 自动加载

**问题**: 每次新会话都问「加载/跳过」，频繁 /clear 场景下交互摩擦大

**方案**:
- Handoff < 1 小时: 自动加载，不询问
- 1 小时 ~ 3 天: 询问用户
- > 3 天: 静默提示 (保持现有)

**改动文件**: `hooks/session-start.py`

**预期收益**: 减少交互摩擦，提升连续工作流体验

---

## P2 - 细节完善

### 5. 自动清理 Consumed 文件

**问题**: HANDOFF.consumed.md 可能堆积

**方案**: SessionStart 时检查，超过 7 天自动删除

**改动文件**: `hooks/session-start.py`

**预期收益**: 文件整洁，避免历史文件堆积

---

### 6. Stop Hook 消息合并

**问题**: Stop hook 分别输出警告和 Insight 提示，多次 JSON 输出

**方案**: 合并为单条消息，减少 token 开销

**改动文件**: `hooks/stop-monitor.py`

**预期收益**: 节省输出 token

---

## 状态跟踪

| # | 优化项 | 优先级 | 状态 | 备注 |
|---|--------|--------|------|------|
| 1 | PreCompact 直接写 Handoff | P0 | 待实现 | |
| 2 | 70% 自动保存 | P0 | 待实现 | |
| 3 | 智能 Insight 评估 | P1 | 待实现 | |
| 4 | 1小时内自动加载 | P1 | 待实现 | |
| 5 | 自动清理 consumed | P2 | 待实现 | |
| 6 | Stop 消息合并 | P2 | 待实现 | |
