<!-- Use this as the structure for your output file. Fill in the sections. -->
## 1. 环境准备 (Environment Setup)

- [x] 1.1 初始化 `uv` 项目 (uv init)
- [x] 1.2 使用 `uv` 安装依赖库 `akshare`, `pandas`, `matplotlib`

## 2. 核心实现 (Core Implementation)

- [x] 2.1 创建 `src/simple_backtest.py` 脚本框架
- [x] 2.2 实现 `fetch_data` 函数：使用 akshare 获取历史日线数据
- [x] 2.3 实现 `calculate_signals` 函数：计算双均线并生成买卖信号
- [x] 2.4 实现 `calculate_performance` 函数：向量化计算策略收益、净值、回撤
- [x] 2.5 实现 `report` 函数：计算夏普比率并打印文本报告
- [x] 2.6 实现绘图逻辑：绘制累计收益对比曲线

## 3. 验证与调试 (Verification)

- [x] 3.1 使用 `uv run` 运行脚本测试完整流程
- [x] 3.2 验证无未来函数（检查信号 shift 逻辑）
