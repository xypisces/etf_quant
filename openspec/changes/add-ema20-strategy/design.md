## Context

当前 ETF 量化系统已有事件驱动回测引擎和 `Strategy` 抽象基类。现有 `MACrossStrategy` 使用 `deque` 维护价格窗口，逐 bar 计算均线并生成交叉信号。本次需新增 `EMA20PullbackStrategy`，在同一架构下实现基于 EMA20 回踩的入场策略，结合 MACD 动量确认和缩量验证。

现有架构要点：
- `Strategy` 基类：`on_bar(bar)` 接收 OHLCV 数据 → `generate_signal()` 返回 BUY/SELL/HOLD
- 引擎按 bar 顺序调用策略，策略只能访问当前及历史数据
- 风控、仓位管理由独立模块处理，策略只负责信号生成

## Goals / Non-Goals

**Goals:**
- 实现 `EMA20PullbackStrategy`，继承 `Strategy` 基类
- 逐 bar 计算 EMA20、MACD（12/26/9）、成交量均值，杜绝未来函数
- 三条件入场：价格站回 EMA20 上方 + MACD > 0 + 缩量回调
- 两日容忍止损：跌破 EMA20 后观察 1 天，次日仍不回来则卖出
- 策略参数可配置（EMA 周期、MACD 参数、成交量回看窗口）

**Non-Goals:**
- 不修改回测引擎或风控模块
- 不引入外部技术指标库（如 TA-Lib）
- 不实现加仓/减仓逻辑（本策略为全仓进出）
- 不实现止盈逻辑（由外部风控模块控制）

## Decisions

### Decision 1: EMA 计算方式 — 使用递推公式

**选择**: 使用 EMA 递推公式 `EMA_t = α × price + (1 - α) × EMA_{t-1}`，其中 `α = 2 / (period + 1)`。

**理由**: EMA 是无限记忆指标，不适合用有限窗口 `deque` 计算。递推公式只需保存上一个 EMA 值，时间复杂度 O(1)，空间复杂度 O(1)，且完全精确。

**替代方案**: 使用 `deque` 取最近 N 个价格计算 SMA — 但 SMA 不是 EMA，指标含义不同，不采用。

### Decision 2: MACD 计算 — 内部逐 bar 递推

**选择**: 在策略内部逐 bar 计算 EMA12、EMA26、DIF、DEA（Signal Line, 9 期 EMA of DIF）、MACD柱（DIF - DEA）。

**理由**: 保持与现有模式一致（`MACrossStrategy` 也在内部计算），无外部依赖。MACD 的三个 EMA 都用递推公式实现。

**判定条件**: 使用 MACD 柱状值 > 0 作为"MACD 在零轴上方"的判定（即 DIF > DEA 且 DIF > 0）。更精确地说，采用 DIF > 0 作为零轴判定，这更符合技术分析中"MACD 在零轴上方"的标准含义。

### Decision 3: 缩量判定 — 成交量低于 N 日均量

**选择**: 当前 bar 的 volume < 过去 N 日（默认 20）成交量的简单移动平均值。

**理由**: 缩量回调的核心是"回调时量比前期缩小"。使用近期均量作为基准简单直观。N 日使用 `deque` 维护，与 `MACrossStrategy` 的模式一致。

### Decision 4: 入场信号触发逻辑

**选择**: 等待价格从下方触及 EMA20 后重返上方（回踩确认），而非任何时刻价格在 EMA20 上方都触发。

**具体实现**:
1. 追踪 `was_near_ema20` 标志：当价格曾跌至 EMA20 附近或下方时标记为 True
2. 当 `was_near_ema20 = True` 且当前收盘价重返 EMA20 上方 → 看涨确认
3. 同时满足 MACD DIF > 0 且 volume < avg_volume → 生成 BUY 信号
4. 信号触发后重置 `was_near_ema20`，避免连续重复买入

"附近" 的定义：收盘价 ≤ EMA20 × (1 + tolerance)，tolerance 默认 0.5%。

### Decision 5: 两日容忍止损 — 使用状态机

**选择**: 使用 `break_count` 状态计数器：
- 0 = 正常持有
- 1 = 今日收盘跌破 EMA20，进入观察期
- ≥2 = 第二次收盘仍在 EMA20 下方 → 生成 SELL 信号

**理由**: 简单的状态机实现，无需记录具体价格或日期。每个 bar 只需判断收盘价与 EMA20 的关系并更新计数。

回到 EMA20 上方时重置 `break_count = 0`。

### Decision 6: 持仓状态追踪

**选择**: 策略内部维护 `_in_position: bool` 标志，BUY 信号后设为 True，SELL 信号后设为 False。

**理由**: 避免在已持仓时重复生成 BUY 信号，或在空仓时生成 SELL 信号。与引擎的持仓管理解耦（引擎有自己的持仓逻辑），但策略本身需要知道当前状态来生成正确信号。

## Risks / Trade-offs

| 风险                                         | 缓解措施                                           |
| -------------------------------------------- | -------------------------------------------------- |
| EMA 冷启动期（前 N 个 bar 数据不足）         | 在数据不足时返回 HOLD，与 MACrossStrategy 行为一致 |
| 缩量判定的 N 日窗口期选择影响信号频率        | 将 `volume_period` 作为可配置参数暴露              |
| "附近 EMA20" 的 tolerance 参数敏感           | 默认 0.5%，允许用户调整                            |
| MACD 参数固定（12/26/9）可能不适配所有品种   | 作为构造函数参数暴露，默认值为经典参数             |
| 策略内部 `_in_position` 可能与引擎状态不一致 | 引擎风控有独立的持仓检查，不依赖策略内部状态       |
