## ADDED Requirements

### Requirement: 仓位计算器 (Position Sizer)
系统必须（SHALL）提供仓位计算器，根据选定策略计算每次开仓数量。

#### Scenario: 固定比例仓位
- **WHEN** 使用固定比例策略且设定风险比例（如 2%）
- **THEN** 开仓金额 = 账户总资金 × 风险比例
- **AND** 开仓数量 = 开仓金额 / 当前价格（取整）

#### Scenario: ATR 仓位计算
- **WHEN** 使用 ATR 策略且提供 ATR 值和风险金额
- **THEN** 开仓数量 = 风险金额 / (ATR × 乘数)
- **AND** 仓位不得超过账户总资金

#### Scenario: Kelly 公式仓位计算
- **WHEN** 使用 Kelly 策略且提供胜率和盈亏比
- **THEN** Kelly 比例 = 胜率 - (1 - 胜率) / 盈亏比
- **AND** 实际使用 Kelly 比例的分数（如半 Kelly）以降低风险

#### Scenario: 资金不足
- **WHEN** 计算的开仓金额超过可用现金
- **THEN** 仓位必须（SHALL）限制为可用现金可购买的最大数量

### Requirement: 风控管理器 (Risk Manager)
系统必须（SHALL）提供风控管理器，在下单前进行风险检查。

#### Scenario: 止损检查
- **WHEN** 持仓亏损达到止损阈值（如 -5%）
- **THEN** 风控管理器必须（SHALL）生成强制平仓信号

#### Scenario: 止盈检查
- **WHEN** 持仓盈利达到止盈阈值（如 +10%）
- **THEN** 风控管理器必须（SHALL）生成平仓信号

#### Scenario: 最大持仓限制
- **WHEN** 收到买入信号但当前已持仓
- **THEN** 风控管理器必须（SHALL）拒绝该信号（单品种模式下只允许一个方向持仓）

#### Scenario: 信号通过检查
- **WHEN** 信号未触发任何风控规则
- **THEN** 风控管理器必须（SHALL）返回通过结果，允许下单

### Requirement: 风控参数可配置 (Configurable Risk Parameters)
风控参数必须（SHALL）支持通过构造函数配置。

#### Scenario: 自定义风控参数
- **WHEN** 创建 RiskManager 实例
- **THEN** 必须（SHALL）支持配置止损比例（默认 -5%）、止盈比例（默认 +10%）、最大持仓限制（默认 1）
