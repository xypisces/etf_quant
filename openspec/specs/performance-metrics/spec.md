## ADDED Requirements

### Requirement: 夏普比率计算 (Sharpe Ratio Calculation)
系统必须（SHALL）计算年化夏普比率。

#### Scenario: 标准夏普比率计算
- **WHEN** 提供策略每日收益率序列
- **THEN** 系统必须（SHALL）按公式计算：`(日收益率均值 - 无风险日利率) / 日收益率标准差 × √252`
- **AND** 无风险利率默认为 0

#### Scenario: 零波动处理
- **WHEN** 策略日收益率标准差为 0
- **THEN** 夏普比率必须（SHALL）返回 0

### Requirement: 最大回撤计算 (Max Drawdown Calculation)
系统必须（SHALL）计算历史最大回撤幅度。

#### Scenario: 计算最大回撤
- **WHEN** 提供累计净值序列
- **THEN** 系统必须（SHALL）计算 `(净值 - 历史最高净值) / 历史最高净值` 的最小值
- **AND** 返回最大回撤幅度（负数百分比）

### Requirement: 总收益率和年化收益率 (Total and Annualized Returns)
系统必须（SHALL）计算总收益率和年化收益率。

#### Scenario: 计算总收益率
- **WHEN** 提供策略净值序列
- **THEN** 总收益率 = `最终净值 / 初始净值 - 1`

#### Scenario: 计算年化收益率
- **WHEN** 已有总收益率和回测天数
- **THEN** 年化收益率 = `(1 + 总收益率) ^ (365 / 天数) - 1`

### Requirement: 胜率计算 (Win Rate Calculation)
系统必须（SHALL）计算策略的交易胜率。

#### Scenario: 计算胜率
- **WHEN** 提供交易记录列表
- **THEN** 胜率 = 盈利交易数 / 总交易数
- **AND** 无交易时胜率返回 0

### Requirement: 盈亏比计算 (Profit/Loss Ratio)
系统必须（SHALL）计算平均盈亏比。

#### Scenario: 计算盈亏比
- **WHEN** 提供交易记录列表
- **THEN** 盈亏比 = 平均盈利金额 / 平均亏损金额（取绝对值）
- **AND** 无亏损交易时返回正无穷
- **AND** 无盈利交易时返回 0

### Requirement: 文本报告输出 (Text Report Output)
系统必须（SHALL）以格式化 Markdown 字符串方式输出绩效指标，而非直接打印到终端。

#### Scenario: 生成报告字符串
- **WHEN** 提供回测结果（净值序列、日收益率、交易记录）
- **THEN** 系统必须（SHALL）返回包含所有五维度指标的 Markdown 格式字符串
- **AND** 函数名称必须（SHALL）为 `format_report`（替代原 `print_report`）

#### Scenario: 生成月度收益矩阵字符串
- **WHEN** 提供日收益率序列
- **THEN** 系统必须（SHALL）返回 Markdown 格式的月度收益矩阵表格字符串
