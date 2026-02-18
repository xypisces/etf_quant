## ADDED Requirements

### Requirement: 网格价格区间设定 (Grid Price Range)
系统必须（SHALL）实现网格交易策略，在指定价格区间内等分网格线进行交易。

#### Scenario: 自动计算网格线
- **WHEN** 创建 `GridStrategy` 实例并指定 `upper_price`、`lower_price`、`grid_num`
- **THEN** 系统必须（SHALL）自动计算等间距的网格线列表

#### Scenario: 基于历史数据自动确定区间
- **WHEN** 未指定 `upper_price` 和 `lower_price`
- **AND** 已接收足够的 bar 数据
- **THEN** 系统必须（SHALL）使用近期最高价和最低价自动确定区间

### Requirement: 网格交易信号 (Grid Trading Signals)
系统必须（SHALL）在价格触及网格线时生成交易信号。

#### Scenario: 价格下穿网格线买入
- **WHEN** 收盘价从上一格下穿到下一格
- **AND** 当前未持仓
- **THEN** 系统必须（SHALL）生成 BUY 信号

#### Scenario: 价格上穿网格线卖出
- **WHEN** 收盘价从下一格上穿到上一格
- **AND** 当前持仓
- **THEN** 系统必须（SHALL）生成 SELL 信号

#### Scenario: 价格超出区间
- **WHEN** 收盘价超出网格区间上界或下界
- **THEN** 系统必须（SHALL）返回 HOLD 信号（不追涨杀跌）

### Requirement: 网格策略参数可配置 (Grid Strategy Parameters)
系统必须（SHALL）支持通过构造函数配置网格策略参数。

#### Scenario: 参数配置
- **WHEN** 创建 `GridStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `grid_num`（网格数量，默认 10）、`upper_price`（上界，可选）、`lower_price`（下界，可选）、`lookback_period`（自动区间计算回看期，默认 60）
