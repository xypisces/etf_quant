## MODIFIED Requirements

### Requirement: 文本报告输出 (Text Report Output)
系统必须（SHALL）以格式化 Markdown 字符串方式输出绩效指标，而非直接打印到终端。

#### Scenario: 生成报告字符串
- **WHEN** 提供回测结果（净值序列、日收益率、交易记录）
- **THEN** 系统必须（SHALL）返回包含所有五维度指标的 Markdown 格式字符串
- **AND** 函数名称必须（SHALL）为 `format_report`（替代原 `print_report`）

#### Scenario: 生成月度收益矩阵字符串
- **WHEN** 提供日收益率序列
- **THEN** 系统必须（SHALL）返回 Markdown 格式的月度收益矩阵表格字符串
