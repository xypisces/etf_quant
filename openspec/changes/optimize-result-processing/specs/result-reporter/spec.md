## ADDED Requirements

### Requirement: 按标的创建结果目录 (Per-Symbol Result Directory)
系统必须（SHALL）在 `results/` 下为每个回测标的创建独立的子目录。

#### Scenario: 创建标的目录
- **WHEN** 执行回测生成报告时
- **THEN** 系统必须（SHALL）创建 `results/<symbol>/` 目录（如 `results/600938/`）
- **AND** 所有该标的的回测产物（报告、图片）必须存放在此目录中

### Requirement: 五维度报告写入 Markdown (Report to Markdown)
系统必须（SHALL）将五维度回测报告写入 Markdown 文件，而非打印到终端。

#### Scenario: 写入报告
- **WHEN** 回测完成后生成报告
- **THEN** 系统必须（SHALL）将报告写入 `results/<symbol>/report.md`
- **AND** 报告段落的标题必须（SHALL）包含策略名称和回测日期（如 `## MACross(5,20) — 2026-02-15`）
- **AND** 报告必须（SHALL）包含五维度指标和月度收益矩阵

#### Scenario: 增量追加
- **WHEN** 对同一标的使用不同策略再次运行回测
- **THEN** 系统必须（SHALL）将新策略的报告段落追加到已有的 `report.md` 文件中
- **AND** 不得覆盖或删除已有的策略报告段落

### Requirement: 策略对比汇总表 (Strategy Comparison Table)
系统必须（SHALL）在报告末尾自动生成策略对比汇总表。

#### Scenario: 生成对比表
- **WHEN** 报告中存在一个或多个策略的回测结果
- **THEN** 系统必须（SHALL）在报告末尾生成 Markdown 表格
- **AND** 表格必须（SHALL）包含每个策略的累计收益率
- **AND** 表格必须（SHALL）包含买入持有基准的累计收益率
- **AND** 表格必须（SHALL）按累计收益率降序排列并标记最佳策略

#### Scenario: 更新对比表
- **WHEN** 新策略追加到报告后
- **THEN** 系统必须（SHALL）重新生成对比汇总表，包含所有已有策略

### Requirement: 仪表板图片命名 (Dashboard Timestamped Naming)
系统必须（SHALL）为仪表板图片文件名加上时间戳以避免覆盖。

#### Scenario: 生成带时间戳的图片
- **WHEN** 生成仪表板图片
- **THEN** 文件名必须（SHALL）遵循格式 `dashboard_{策略名}_{YYYYMMDD}_{HHMMSS}.png`
- **AND** 图片必须（SHALL）保存到 `results/<symbol>/` 目录中
