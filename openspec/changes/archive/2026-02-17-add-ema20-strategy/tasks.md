## 1. 新建 `EMA20PullbackStrategy` 策略类

- [x] 1.1 创建 `src/strategy/ema20_pullback.py`，定义 `EMA20PullbackStrategy(Strategy)` 类，包含构造函数和所有可配置参数（`ema_period`、`macd_fast`、`macd_slow`、`macd_signal`、`volume_period`、`pullback_tolerance`）
- [x] 1.2 实现 `on_bar(bar)` 方法：逐 bar 更新 EMA20（递推公式）、EMA12/EMA26/DIF/DEA/MACD柱、成交量 deque
- [x] 1.3 实现 `generate_signal()` 方法：三条件入场逻辑（回踩确认 + MACD DIF > 0 + 缩量）
- [x] 1.4 实现两日容忍止损逻辑：`break_count` 状态机（0 → 1 → SELL）
- [x] 1.5 实现 `reset()` 方法：重置所有内部状态
- [x] 1.6 实现持仓状态追踪：`_in_position` 标志防止重复信号

## 2. 策略模块导出

- [x] 2.1 在 `src/strategy/__init__.py` 中导入并导出 `EMA20PullbackStrategy`

## 3. `main.py` 集成

- [x] 3.1 在 `main.py` 中导入 `EMA20PullbackStrategy`，替换或新增策略配置切换逻辑
- [x] 3.2 确保回测流程（引擎运行、报告生成、图表输出）与新策略兼容

## 4. 更新文档

- [x] 4.1 更新 `README.md`：新增 EMA20 回踩策略说明、参数配置指南、目录结构变化

## 5. 验证

- [x] 5.1 运行回测，验证策略能正确生成 BUY/SELL 信号
- [x] 5.2 检查报告输出：确认策略名称、收益指标、对比表正确生成
- [x] 5.3 对比 MACross 策略结果，确认两策略可独立运行
