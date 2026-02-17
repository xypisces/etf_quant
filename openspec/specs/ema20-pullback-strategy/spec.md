## ADDED Requirements

### Requirement: EMA20 计算 (EMA20 Calculation)
策略必须（SHALL）使用递推公式逐 bar 计算 20 周期指数移动平均线。

#### Scenario: EMA 递推计算
- **WHEN** 策略接收一根新的 bar 数据
- **THEN** 策略必须（SHALL）使用公式 `EMA_t = α × close + (1 - α) × EMA_{t-1}` 计算当前 EMA20
- **AND** 平滑系数 `α = 2 / (period + 1)`
- **AND** EMA 周期默认为 20，必须（SHALL）支持通过构造函数配置

#### Scenario: EMA 冷启动
- **WHEN** 接收的 bar 数量不足以计算 EMA（< 1 根 bar）
- **THEN** `generate_signal()` 必须（SHALL）返回 HOLD 信号

#### Scenario: 首根 bar 的 EMA 初始化
- **WHEN** 策略接收第一根 bar 数据
- **THEN** EMA 初始值必须（SHALL）设为第一根 bar 的收盘价

### Requirement: MACD 指标计算 (MACD Calculation)
策略必须（SHALL）逐 bar 计算 MACD 指标（DIF、DEA、MACD 柱）。

#### Scenario: 计算 MACD 各组件
- **WHEN** 策略接收一根新的 bar 数据
- **THEN** 策略必须（SHALL）计算：
  1. EMA12（快线，默认 12 周期）
  2. EMA26（慢线，默认 26 周期）
  3. DIF = EMA12 - EMA26
  4. DEA = DIF 的 9 周期 EMA（信号线）
  5. MACD 柱 = DIF - DEA

#### Scenario: MACD 参数可配置
- **WHEN** 创建策略实例
- **THEN** 必须（SHALL）支持配置 `macd_fast`（默认 12）、`macd_slow`（默认 26）、`macd_signal`（默认 9）参数

### Requirement: 缩量回调判定 (Volume Contraction Detection)
策略必须（SHALL）判断当前 bar 的成交量是否低于近期平均水平。

#### Scenario: 缩量判定
- **WHEN** 策略已积累足够的成交量历史数据（≥ `volume_period` 根 bar）
- **AND** 当前 bar 的成交量 < 过去 `volume_period` 日的简单成交量均值（不含当天）
- **THEN** 系统必须（SHALL）判定为"缩量"

#### Scenario: 成交量数据不足
- **WHEN** 积累的成交量数据不足 `volume_period` 根
- **THEN** 缩量条件必须（SHALL）判定为不满足（返回 False）

#### Scenario: 成交量窗口可配置
- **WHEN** 创建策略实例
- **THEN** 必须（SHALL）支持配置 `volume_period` 参数，默认为 20

### Requirement: 三条件入场信号 (Triple-Condition Entry Signal)
策略必须（SHALL）在三个条件同时满足时生成 BUY 信号。

#### Scenario: 生成买入信号
- **WHEN** 价格在最近 `pullback_lookback` 天内曾回踩 EMA20 附近（收盘价 ≤ EMA20 × (1 + tolerance)）后重返 EMA20 上方
- **AND** MACD 的 DIF 值 > 0（零轴上方）
- **AND** 当前成交量为缩量状态
- **AND** 策略当前未持仓
- **THEN** `generate_signal()` 必须（SHALL）返回 BUY 信号

#### Scenario: 条件不完全满足
- **WHEN** 三个入场条件中任意一个不满足
- **THEN** `generate_signal()` 必须（SHALL）返回 HOLD 信号（不买入）

#### Scenario: 回踩容忍度和有效期可配置
- **WHEN** 创建策略实例
- **THEN** 必须（SHALL）支持配置 `pullback_tolerance`（默认 0.005）和 `pullback_lookback`（默认 5）参数

#### Scenario: 避免连续买入
- **WHEN** 策略已生成 BUY 信号且当前持仓中
- **THEN** 即使三条件再次满足，也必须（SHALL）返回 HOLD 信号

### Requirement: 两日容忍止损 (Two-Day Tolerance Stop Loss)
策略必须（SHALL）在收盘价连续两日跌破 EMA20 后生成 SELL 信号。

#### Scenario: 首日跌破 EMA20
- **WHEN** 策略持仓中
- **AND** 当前 bar 收盘价 < EMA20
- **THEN** 策略必须（SHALL）进入"观察期"，不立即生成 SELL 信号
- **AND** 返回 HOLD 信号

#### Scenario: 连续第二日跌破
- **WHEN** 策略处于"观察期"（已有一日跌破）
- **AND** 当前 bar 收盘价仍然 < EMA20
- **THEN** `generate_signal()` 必须（SHALL）返回 SELL 信号（无条件卖出）

#### Scenario: 观察期内回到 EMA20 上方
- **WHEN** 策略处于"观察期"
- **AND** 当前 bar 收盘价 ≥ EMA20
- **THEN** 系统必须（SHALL）退出观察期，重置跌破计数
- **AND** 返回 HOLD 信号（继续持有）

#### Scenario: 正常持有
- **WHEN** 策略持仓中
- **AND** 收盘价 ≥ EMA20
- **THEN** `generate_signal()` 必须（SHALL）返回 HOLD 信号（继续持有）

### Requirement: 策略参数可配置 (Configurable Strategy Parameters)
策略实例化时必须（SHALL）支持通过构造函数传入所有可调参数。

#### Scenario: 默认参数创建
- **WHEN** 使用 `EMA20PullbackStrategy()` 创建实例（不传参数）
- **THEN** 必须（SHALL）使用以下默认值：
  - `ema_period`: 20
  - `macd_fast`: 12
  - `macd_slow`: 26
  - `macd_signal`: 9
  - `volume_period`: 20
  - `pullback_tolerance`: 0.005
  - `pullback_lookback`: 5

#### Scenario: 自定义参数创建
- **WHEN** 传入自定义参数创建实例
- **THEN** 必须（SHALL）使用传入的参数值

### Requirement: 策略状态重置 (Strategy State Reset)
策略必须（SHALL）支持完整的状态重置，用于新一轮回测。

#### Scenario: 重置所有状态
- **WHEN** 调用 `reset()` 方法
- **THEN** 必须（SHALL）重置所有内部状态，包括：EMA 值、MACD 各组件值、成交量历史、回踩标记、跌破计数、持仓状态

### Requirement: 持仓状态同步 (Position State Synchronization)
策略必须（SHALL）通过引擎 `on_fill` 回调同步持仓状态，而非内部自行管理。

#### Scenario: 买入成交通知
- **WHEN** 引擎调用 `on_fill(Signal.BUY)`
- **THEN** 策略必须（SHALL）将内部持仓标记设为 True，并重置回踩标记

#### Scenario: 卖出成交通知
- **WHEN** 引擎调用 `on_fill(Signal.SELL)`
- **THEN** 策略必须（SHALL）将内部持仓标记设为 False，并重置跌破计数
