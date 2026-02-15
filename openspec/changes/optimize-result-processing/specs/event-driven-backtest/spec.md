## MODIFIED Requirements

### Requirement: 回测结果输出 (Backtest Result Output)
回测完成后必须（SHALL）返回包含完整交易记录、每日净值和策略名称的结果对象。

#### Scenario: 返回回测结果
- **WHEN** 回测运行完成
- **THEN** 引擎必须（SHALL）返回包含以下信息的结果：每日净值序列、交易记录列表、最终资金、策略名称（`strategy_name`）
