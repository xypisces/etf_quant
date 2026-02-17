## ADDED Requirements

### Requirement: 事件驱动回测引擎 (Event-Driven Backtest Engine)
系统必须（SHALL）提供事件驱动的回测引擎，逐 bar 推送数据到策略，经过风控检查后执行交易。

#### Scenario: 回测核心循环
- **WHEN** 引擎接收历史数据 DataFrame 和策略实例启动回测
- **THEN** 引擎必须（SHALL）按时间顺序逐 bar 执行以下流程：
  1. 调用 `strategy.on_bar(bar)` 推送数据
  2. 调用 `strategy.generate_signal()` 获取信号
  3. 调用 `risk_manager.check(signal)` 进行风控检查
  4. 调用 `position_sizer.calculate(signal)` 计算仓位
  5. 执行订单（含滑点和手续费扣除）
  6. 更新持仓和净值记录

#### Scenario: 回测初始化
- **WHEN** 创建回测引擎实例
- **THEN** 必须（SHALL）支持配置初始资金（默认 100,000）、滑点比例（默认 0.01%）、手续费比例（默认 0.03%）

#### Scenario: 记录每日状态
- **WHEN** 每根 bar 处理完成后
- **THEN** 引擎必须（SHALL）记录当前日期、持仓状态、账户净值、现金余额

### Requirement: 滑点模型 (Slippage Model)
订单执行时必须（SHALL）模拟滑点对成交价格的影响。

#### Scenario: 买入时滑点
- **WHEN** 执行买入订单
- **THEN** 实际成交价格 = 当前价格 × (1 + 滑点比例)

#### Scenario: 卖出时滑点
- **WHEN** 执行卖出订单
- **THEN** 实际成交价格 = 当前价格 × (1 - 滑点比例)

### Requirement: 手续费模型 (Commission Model)
订单执行时必须（SHALL）从账户扣除手续费。

#### Scenario: 计算手续费
- **WHEN** 执行任意买入或卖出订单
- **THEN** 手续费 = 成交金额 × 手续费比例
- **AND** 手续费从账户现金余额中扣除

### Requirement: 回测结果输出 (Backtest Result Output)
回测完成后必须（SHALL）返回包含完整交易记录、每日净值和策略名称的结果对象。

#### Scenario: 返回回测结果
- **WHEN** 回测运行完成
- **THEN** 引擎必须（SHALL）返回包含以下信息的结果：每日净值序列、交易记录列表、最终资金、策略名称（`strategy_name`）
