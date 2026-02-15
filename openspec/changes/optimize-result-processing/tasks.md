## 1. `metrics.py` 重构: `print_report` → `format_report`

- [x] 1.1 将 `print_report` 重命名为 `format_report`，返回 Markdown 格式字符串而非直接打印
- [x] 1.2 新增 `format_monthly_table` 函数，将月度收益矩阵格式化为 Markdown 表格字符串

## 2. `BacktestResult` 增加 `strategy_name` 字段

- [x] 2.1 在 `BacktestResult` dataclass 中添加 `strategy_name: str` 字段
- [x] 2.2 在 `_build_result` 中自动从 `self.strategy.name` 获取策略名称填入

## 3. 新增 `src/utils/reporter.py` 模块

- [x] 3.1 创建 `ReportWriter` 类，支持传入 `symbol` 和 `save_dir` 参数
- [x] 3.2 实现 `write_report` 方法：将五维度报告和月度收益表以 Markdown 格式写入文件
- [x] 3.3 实现增量追加逻辑：新策略段落追加到已有报告中（以 `## 策略名 — 日期` 为标题）
- [x] 3.4 实现 `_build_comparison_table` 方法：扫描报告中所有策略的累计收益率，生成对比汇总表
- [x] 3.5 对比表须包含买入持有基准收益率，按累计收益率降序排列并标记最佳策略

## 4. `plotting.py` 修改保存路径和命名

- [x] 4.1 `plot_dashboard` 支持传入 `strategy_name` 参数
- [x] 4.2 图片保存路径改为 `results/<symbol>/`，命名为 `dashboard_{策略名}_{YYYYMMDD}_{HHMMSS}.png`

## 5. `main.py` 适配新流程

- [x] 5.1 调用 `format_report` 获取报告字符串（不再直接打印）
- [x] 5.2 使用 `ReportWriter` 写入报告到 `results/<symbol>/report.md`
- [x] 5.3 传入基准收益率数据到 `ReportWriter`
- [x] 5.4 更新 `plot_dashboard` 调用，传入策略名和新保存路径

## 6. 验证

- [x] 6.1 运行回测，检查 `results/<symbol>/report.md` 是否正确生成
- [x] 6.2 更换策略或参数再次运行，验证增量追加和对比表更新
- [x] 6.3 检查仪表板图片命名是否包含时间戳且不覆盖
