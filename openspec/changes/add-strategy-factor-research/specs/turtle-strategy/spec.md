## ADDED Requirements

### Requirement: 唐奇安通道突破入场 (Donchian Channel Breakout Entry)
系统必须（SHALL）实现海龟策略，基于唐奇安通道突破信号入场。

#### Scenario: 突破上轨买入
- **WHEN** 收盘价突破近 N 日最高价（唐奇安通道上轨）
- **AND** 当前未持仓
- **THEN** 系统必须（SHALL）生成 BUY 信号

#### Scenario: 数据不足时保持观望
- **WHEN** 已接收的 bar 数量不足以计算唐奇安通道
- **THEN** 系统必须（SHALL）返回 HOLD 信号

### Requirement: ATR 动态止损出场 (ATR-Based Exit)
系统必须（SHALL）使用 ATR 倍数作为止损条件。

#### Scenario: ATR 止损触发
- **WHEN** 持仓期间收盘价低于入场价减去 N 倍 ATR
- **THEN** 系统必须（SHALL）生成 SELL 信号

#### Scenario: 唐奇安下轨出场
- **WHEN** 持仓期间收盘价跌破近 M 日最低价（唐奇安通道下轨，M < N）
- **THEN** 系统必须（SHALL）生成 SELL 信号

### Requirement: 海龟策略参数可配置 (Turtle Strategy Parameters)
系统必须（SHALL）支持通过构造函数配置海龟策略参数。

#### Scenario: 参数配置
- **WHEN** 创建 `TurtleStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `entry_period`（入场通道周期，默认 20）、`exit_period`（出场通道周期，默认 10）、`atr_period`（ATR 周期，默认 14）、`atr_multiplier`（止损 ATR 倍数，默认 2.0）
