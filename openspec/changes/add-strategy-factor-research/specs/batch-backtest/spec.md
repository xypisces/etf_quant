## ADDED Requirements

### Requirement: 多品种多策略批量回测 (Batch Backtest)
系统必须（SHALL）提供批量回测能力，支持多品种 × 多策略的矩阵化回测。

#### Scenario: 矩阵化回测
- **WHEN** 用户指定品种列表和策略列表
- **THEN** 系统必须（SHALL）对所有 品种×策略 组合运行回测
- **AND** 返回汇总结果（含每个组合的收益率、夏普比、最大回撤等）

#### Scenario: 结果排序与对比
- **WHEN** 批量回测完成
- **THEN** 系统必须（SHALL）按指定指标（默认收益率）对结果排序
- **AND** 支持按品种或按策略分组查看

#### Scenario: 进度展示
- **WHEN** 批量回测正在运行
- **THEN** 系统必须（SHALL）在控制台展示当前进度（已完成/总数量）

### Requirement: 批量回测结果输出 (Batch Result Output)
系统必须（SHALL）将批量回测结果以结构化格式输出。

#### Scenario: 汇总 DataFrame
- **WHEN** 批量回测完成
- **THEN** 系统必须（SHALL）返回一个 DataFrame，包含列：symbol, strategy, total_return, sharpe_ratio, max_drawdown, trade_count
