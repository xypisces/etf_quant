## MODIFIED Requirements

### Requirement: 获取历史数据 (Fetch Historical Data)
数据获取功能已迁移至独立的 `data-loader` 能力模块。原 `vectorized-backtest` 中的数据获取需求不再由本模块承担。

#### Scenario: 获取 ETF 数据
- **WHEN** 用户需要获取历史数据
- **THEN** 必须（SHALL）通过 `data-loader` 模块的 `DataLoader` 类获取

### Requirement: 计算双均线策略信号 (Calculate Dual MA Strategy Signals)
策略信号计算已迁移至独立的 `strategy-framework` 能力模块。使用事件驱动的 `on_bar()` 接口代替向量化信号计算。

#### Scenario: 生成买入信号
- **WHEN** 需要计算双均线信号
- **THEN** 必须（SHALL）通过 `strategy-framework` 模块的 `MACrossStrategy` 类，在 `on_bar()` 逐 bar 模式下计算

### Requirement: 向量化回测计算 (Vectorized Backtest Calculation)
回测计算已迁移至独立的 `event-driven-backtest` 能力模块。向量化计算方式被事件驱动方式替代。

#### Scenario: 计算策略收益
- **WHEN** 需要执行回测
- **THEN** 必须（SHALL）通过 `event-driven-backtest` 模块的 `BacktestEngine` 类逐 bar 驱动

### Requirement: 绩效指标计算 (Calculate Performance Metrics)
绩效指标计算已迁移至独立的 `performance-metrics` 能力模块，并新增胜率和盈亏比指标。

#### Scenario: 计算绩效指标
- **WHEN** 回测完成
- **THEN** 必须（SHALL）通过 `performance-metrics` 模块的计算函数获取

### Requirement: 结果展示 (Result Visualization)
结果展示功能已迁移至独立的 `utils/plotting.py` 可视化模块。

#### Scenario: 绘制收益曲线
- **WHEN** 回测完成
- **THEN** 必须（SHALL）通过 `utils/plotting.py` 模块的绘图函数展示
