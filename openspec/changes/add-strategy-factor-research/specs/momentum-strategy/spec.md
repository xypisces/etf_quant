## ADDED Requirements

### Requirement: 动量得分计算 (Momentum Scoring)
系统必须（SHALL）实现动量轮动策略，计算品种的动量得分。

#### Scenario: 计算 ROC 动量得分
- **WHEN** 接收到足够的 bar 数据（≥ 动量回看期）
- **THEN** 系统必须（SHALL）计算当前品种的 N 日收益率（Rate of Change）作为动量得分

### Requirement: 动量信号生成 (Momentum Signal Generation)
系统必须（SHALL）基于动量得分生成交易信号。

#### Scenario: 正动量买入
- **WHEN** 当前品种动量得分 > 0（正动量）
- **AND** 当前未持仓
- **THEN** 系统必须（SHALL）生成 BUY 信号

#### Scenario: 负动量卖出
- **WHEN** 当前品种动量得分 ≤ 0
- **AND** 当前持仓
- **THEN** 系统必须（SHALL）生成 SELL 信号

#### Scenario: 数据不足
- **WHEN** 接收的 bar 数量不足以计算动量
- **THEN** 系统必须（SHALL）返回 HOLD 信号

### Requirement: 动量策略参数可配置 (Momentum Strategy Parameters)
系统必须（SHALL）支持通过构造函数配置动量策略参数。

#### Scenario: 参数配置
- **WHEN** 创建 `MomentumStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `lookback_period`（动量回看期，默认 20）
