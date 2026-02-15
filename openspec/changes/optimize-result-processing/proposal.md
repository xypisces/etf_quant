## Why

当前回测结果通过 `print()` 输出到终端，无法持久化保存，也无法跨策略对比。每次运行回测后，之前的报告即丢失。同时，仪表板图片保存在统一的 `results/` 目录下且无时间戳，多次运行或多策略运行会互相覆盖。

需要将回测结果写入结构化的 Markdown 文件，按标的代码分目录存储，支持多策略增量追加和自动对比，使回测结果具备**可追溯性**和**可对比性**。

## What Changes

- 在 `results/` 下按标的代码创建子目录（如 `results/600938/`），所有该标的的回测产物集中存放
- 五维度专业报告和月度收益表**不再打印到终端**，改为写入 Markdown 文件（`results/<symbol>/report.md`）
- 报告 Markdown 中每次回测以**回测日期 + 策略名称**为标题，支持多策略增量追加
- 报告底部自动生成**策略对比汇总表**，收集所有策略的累计收益率进行排名，包含"买入持有"基准收益率
- 综合仪表板图片保存到标的目录，文件名包含**日期时间戳**（如 `dashboard_MACross_20260215_110245.png`），避免覆盖
- `main.py` 入口脚本适配新的结果处理流程

## Capabilities

### New Capabilities

- `result-reporter`: 负责将回测结果写入结构化 Markdown 文件，包括五维度报告、月度收益表、策略对比汇总表的格式化输出，以及增量追加逻辑

### Modified Capabilities

- `performance-metrics`: `print_report` 函数改为返回格式化字符串而非直接打印，`monthly_returns_table` 增加 Markdown 格式化输出方法
- `event-driven-backtest`: `BacktestResult` 需携带策略名称信息，便于报告标题标识

## Impact

- **代码影响**: `src/backtest/metrics.py`（报告函数重构）、`src/utils/plotting.py`（保存路径逻辑）、`src/main.py`（结果处理流程重构）、新增 `src/utils/reporter.py`
- **目录结构**: `results/` 目录从扁平结构改为按标的分层
- **向后兼容**: 终端不再自动打印报告，改为写入文件（破坏性变更但仅影响开发体验）
