# 向量化回测 (Vectorized Backtest)

本模块提供基于 Pandas 的向量化回测能力，支持快速验证交易策略。

## 需求 (Requirements)

### 需求: 获取历史数据 (Fetch Historical Data)
系统必须能够使用 `akshare` 库获取指定标的的历史 K 线数据。

#### 场景: 获取 ETF 数据 (Scenario: Fetch ETF Data)
- **当 (WHEN)** 用户指定标的代码（如 `510300`）和起止日期调用数据获取函数
- **那么 (THEN)** 系统应返回包含 `date`, `open`, `high`, `low`, `close`, `volume` 列的 pandas DataFrame
- **并且 (AND)** 数据应按日期升序排列

### 需求: 计算双均线策略信号 (Calculate Dual MA Strategy Signals)
系统必须能够根据收盘价计算短期和长期移动平均线，并生成交易信号。

#### 场景: 生成买入信号 (Scenario: Generate Buy Signal)
- **当 (WHEN)** 短期均线（如 MA5）上穿长期均线（如 MA20）
- **那么 (THEN)** 对应的信号值应为 1（持有/买入）

#### 场景: 生成卖出信号 (Scenario: Generate Sell Signal)
- **当 (WHEN)** 短期均线下穿长期均线
- **那么 (THEN)** 对应的信号值应为 0（空仓/卖出）

### 需求: 向量化回测计算 (Vectorized Backtest Calculation)
系统必须使用 pandas 向量化操作计算策略收益，不得使用 Python `for` 循环遍历行。

#### 场景: 计算策略收益 (Scenario: Calculate Strategy Returns)
- **当 (WHEN)** 已有信号序列和标的日收益率序列
- **那么 (THEN)** 策略日收益率应为 ` 昨日信号 * 今日标的收益率`（假设次日开盘成交或收盘对收盘）

#### 场景: 计算累计收益 (Scenario: Calculate Cumulative Returns)
- **当 (WHEN)** 已有策略日收益率序列
- **那么 (THEN)** 系统应计算累计净值曲线

### 需求: 绩效指标计算 (Calculate Performance Metrics)
系统必须计算并输出关键绩效指标。

#### 场景: 计算夏普比率 (Scenario: Calculate Sharpe Ratio)
- **当 (WHEN)** 提供策略日收益率序列
- **那么 (THEN)** 系统应计算年化夏普比率（假设无风险利率为 0 或固定值）

#### 场景: 计算最大回撤 (Scenario: Calculate Max Drawdown)
- **当 (WHEN)** 提供累计净值序列
- **那么 (THEN)** 系统应计算历史最大回撤幅度和回撤期间

### 需求: 结果展示 (Result Visualization)
系统必须以文本和图表形式展示回测结果。

#### 场景: 打印文本报告 (Scenario: Print Text Report)
- **当 (WHEN)** 回测完成
- **那么 (THEN)** 控制台应打印总收益率、年化收益率、夏普比率、最大回撤等指标

#### 场景: 绘制收益曲线 (Scenario: Plot Equity Curve)
- **当 (WHEN)** 回测完成
- **那么 (THEN)** 系统应使用 `matplotlib` 绘制并展示策略累计收益与基准累计收益的对比图
