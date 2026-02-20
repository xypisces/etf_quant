## ADDED Requirements

### Requirement: 布林带计算 (Bollinger Bands Calculation)
系统必须（SHALL）实现均值回归策略，基于布林带判断超买超卖。

#### Scenario: 逐 bar 计算布林带
- **WHEN** 接收到足够的 bar 数据（≥ 布林带周期）
- **THEN** 系统必须（SHALL）计算中轨（SMA）、上轨（中轨 + N 倍标准差）、下轨（中轨 - N 倍标准差）

### Requirement: RSI 辅助过滤 (RSI Filter)
系统必须（SHALL）计算 RSI 指标辅助过滤信号。

#### Scenario: 逐 bar 计算 RSI
- **WHEN** 接收到足够的 bar 数据（≥ RSI 周期）
- **THEN** 系统必须（SHALL）计算当日 RSI 值

### Requirement: 均值回归信号生成 (Mean Reversion Signal Generation)
系统必须（SHALL）基于布林带和 RSI 生成交易信号。

#### Scenario: 超卖买入
- **WHEN** 收盘价触及或跌破布林带下轨
- **AND** RSI < 超卖阈值（默认 30）
- **AND** 当前未持仓
- **THEN** 系统必须（SHALL）生成 BUY 信号

#### Scenario: 超买卖出
- **WHEN** 收盘价触及或突破布林带上轨
- **AND** RSI > 超买阈值（默认 70）
- **AND** 当前持仓
- **THEN** 系统必须（SHALL）生成 SELL 信号

#### Scenario: 回归中轨止盈
- **WHEN** 持仓期间收盘价回归至布林带中轨上方
- **THEN** 系统必须（SHALL）生成 SELL 信号

### Requirement: 均值回归策略参数可配置 (Mean Reversion Parameters)
系统必须（SHALL）支持通过构造函数配置均值回归策略参数。

#### Scenario: 参数配置
- **WHEN** 创建 `MeanReversionStrategy` 实例
- **THEN** 必须（SHALL）支持指定 `bb_period`（布林带周期，默认 20）、`bb_std`（标准差倍数，默认 2.0）、`rsi_period`（RSI 周期，默认 14）、`rsi_oversold`（超卖阈值，默认 30）、`rsi_overbought`（超买阈值，默认 70）
