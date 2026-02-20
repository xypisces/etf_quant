## MODIFIED Requirements

### Requirement: 策略参数可配置 (Configurable Strategy Parameters)
策略实例化时必须（SHALL）支持通过构造函数传入参数。

#### Scenario: 配置双均线参数
- **WHEN** 创建 `MACrossStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `short_window`（默认 5）和 `long_window`（默认 20）参数

#### Scenario: 配置 EMA20 回踩策略参数
- **WHEN** 创建 `EMA20PullbackStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `ema_period`、`macd_fast`、`macd_slow`、`macd_signal`、`volume_period`、`pullback_tolerance`、`pullback_lookback` 参数

#### Scenario: 配置海龟策略参数
- **WHEN** 创建 `TurtleStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `entry_period`、`exit_period`、`atr_period`、`atr_multiplier` 参数

#### Scenario: 配置网格策略参数
- **WHEN** 创建 `GridStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `grid_num`、`upper_price`、`lower_price`、`lookback_period` 参数

#### Scenario: 配置动量轮动策略参数
- **WHEN** 创建 `MomentumStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `lookback_period` 参数

#### Scenario: 配置均值回归策略参数
- **WHEN** 创建 `MeanReversionStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `bb_period`、`bb_std`、`rsi_period`、`rsi_oversold`、`rsi_overbought` 参数

## ADDED Requirements

### Requirement: 策略注册表扩展 (Strategy Registry Extension)
策略注册表必须（SHALL）包含所有已实现的策略映射。

#### Scenario: 新增策略注册
- **WHEN** 系统加载配置
- **THEN** `STRATEGY_REGISTRY` 必须（SHALL）包含以下策略映射：`turtle` → `TurtleStrategy`、`grid` → `GridStrategy`、`momentum` → `MomentumStrategy`、`mean_reversion` → `MeanReversionStrategy`
