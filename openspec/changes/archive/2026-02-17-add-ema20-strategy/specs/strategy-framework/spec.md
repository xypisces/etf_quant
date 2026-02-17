## MODIFIED Requirements

### Requirement: 双均线策略实现 (MA Cross Strategy)
系统必须（SHALL）提供 `MACrossStrategy` 作为第一个具体策略实现，继承 `Strategy` 基类。

#### Scenario: 生成买入信号
- **WHEN** 策略接收到足够的 bar 数据（≥ 长期均线窗口期）
- **AND** 短期均线上穿长期均线
- **THEN** `generate_signal()` 必须（SHALL）返回 BUY 信号

#### Scenario: 生成卖出信号
- **WHEN** 短期均线下穿长期均线
- **THEN** `generate_signal()` 必须（SHALL）返回 SELL 信号

#### Scenario: 持有信号
- **WHEN** 均线关系未发生交叉变化
- **THEN** `generate_signal()` 必须（SHALL）返回 HOLD 信号

#### Scenario: 数据不足时
- **WHEN** 接收的 bar 数量不足以计算长期均线
- **THEN** `generate_signal()` 必须（SHALL）返回 HOLD 信号

## ADDED Requirements

### Requirement: EMA20 回踩策略实现 (EMA20 Pullback Strategy)
系统必须（SHALL）提供 `EMA20PullbackStrategy` 作为第二个具体策略实现，继承 `Strategy` 基类。

#### Scenario: 策略可通过模块导出使用
- **WHEN** 从 `src.strategy` 包导入
- **THEN** 必须（SHALL）能直接导入 `EMA20PullbackStrategy` 类

### Requirement: 策略参数可配置 (Configurable Strategy Parameters)
策略实例化时必须（SHALL）支持通过构造函数传入参数。

#### Scenario: 配置双均线参数
- **WHEN** 创建 `MACrossStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `short_window`（默认 5）和 `long_window`（默认 20）参数

#### Scenario: 配置 EMA20 回踩策略参数
- **WHEN** 创建 `EMA20PullbackStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `ema_period`、`macd_fast`、`macd_slow`、`macd_signal`、`volume_period`、`pullback_tolerance` 参数
