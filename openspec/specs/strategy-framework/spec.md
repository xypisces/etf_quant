## ADDED Requirements

### Requirement: 策略抽象基类 (Strategy Abstract Base Class)
系统必须（SHALL）提供 `Strategy` 抽象基类，定义标准化策略接口，所有策略实现必须（MUST）继承此基类。

#### Scenario: 定义标准接口
- **WHEN** 开发者创建新策略
- **THEN** 必须（MUST）继承 `Strategy` 基类并实现 `on_bar(bar)` 和 `generate_signal()` 两个方法
- **AND** `on_bar()` 接收一根 K 线数据（dict 格式，包含 open/high/low/close/volume）
- **AND** `generate_signal()` 返回交易信号（BUY/SELL/HOLD）

### Requirement: 禁止未来函数 (No Lookahead Bias)
策略实现中严禁（MUST NOT）使用未来数据。策略在 `on_bar()` 中只能访问当前及历史 bar 数据。

#### Scenario: 策略只能看到历史数据
- **WHEN** 引擎在第 N 根 bar 调用 `strategy.on_bar(bar_N)`
- **THEN** 策略内部状态只包含 bar_1 到 bar_N 的数据
- **AND** 不得使用 `shift(-1)` 等引用未来数据的操作

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

### Requirement: 策略参数可配置 (Configurable Strategy Parameters)
策略实例化时必须（SHALL）支持通过构造函数传入参数。

#### Scenario: 配置双均线参数
- **WHEN** 创建 `MACrossStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `short_window`（默认 5）和 `long_window`（默认 20）参数
