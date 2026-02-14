## 1. 项目目录结构搭建

- [x] 1.1 创建模块目录结构：`src/data/`、`src/strategy/`、`src/backtest/`、`src/risk/`、`src/utils/`，以及各目录的 `__init__.py`
- [x] 1.2 将 `main.py` 移动到 `src/main.py`，更新为模块化入口

## 2. 数据加载模块 (`src/data/loader.py`)

- [x] 2.1 实现 `DataLoader` 类：统一接口，支持标的代码和日期参数
- [x] 2.2 实现 CSV 缓存读取逻辑（优先从 `csv/` 目录加载）
- [x] 2.3 实现 akshare API 数据获取逻辑，列名标准化为 `date/open/high/low/close/volume`
- [x] 2.4 实现自动缓存：首次获取后保存到 `csv/` 目录
- [x] 2.5 确保所有 OHLCV 列为 `float64` 类型

## 3. 策略框架 (`src/strategy/`)

- [x] 3.1 实现 `Strategy` 抽象基类（`src/strategy/base.py`）：定义 `on_bar()` 和 `generate_signal()` 接口，定义 `Signal` 枚举（BUY/SELL/HOLD）
- [x] 3.2 实现 `MACrossStrategy`（`src/strategy/ma_cross.py`）：继承 `Strategy`，内部维护短期/长期均线的 rolling window
- [x] 3.3 支持通过构造函数配置 `short_window`（默认 5）和 `long_window`（默认 20）

## 4. 风控与仓位管理 (`src/risk/`)

- [x] 4.1 实现 `PositionSizer`（`src/risk/position_sizer.py`）：支持固定比例仓位计算，处理资金不足情况
- [x] 4.2 实现 ATR 和 Kelly 公式仓位计算方法
- [x] 4.3 实现 `RiskManager`（`src/risk/risk_manager.py`）：止损检查（默认 -5%）、止盈检查（默认 +10%）
- [x] 4.4 实现最大持仓限制检查（单品种模式下只允许一个方向持仓）
- [x] 4.5 支持通过构造函数配置风控参数

## 5. 事件驱动回测引擎 (`src/backtest/engine.py`)

- [x] 5.1 实现 `BacktestEngine` 类：支持配置初始资金、滑点比例（默认 0.01%）、手续费比例（默认 0.03%）
- [x] 5.2 实现核心回测循环：逐 bar 推送 → 信号生成 → 风控检查 → 仓位计算 → 订单执行
- [x] 5.3 实现滑点模型：买入价 = 价格 × (1 + 滑点比例)，卖出价 = 价格 × (1 - 滑点比例)
- [x] 5.4 实现手续费扣除：成交金额 × 手续费比例
- [x] 5.5 实现每日状态记录：日期、持仓、净值、现金余额
- [x] 5.6 返回回测结果对象：每日净值序列、交易记录列表、最终资金

## 6. 绩效指标模块 (`src/backtest/metrics.py`)

- [x] 6.1 实现夏普比率计算函数（年化，处理零波动情况）
- [x] 6.2 实现最大回撤计算函数
- [x] 6.3 实现总收益率和年化收益率计算函数
- [x] 6.4 实现胜率和盈亏比计算函数
- [x] 6.5 实现文本报告输出函数（打印所有核心指标）

## 7. 可视化工具 (`src/utils/plotting.py`)

- [x] 7.1 实现收益曲线绘图函数：策略收益 vs 基准收益对比
- [x] 7.2 支持保存图表到 `results/` 目录
- [x] 7.3 配置中文字体支持

## 8. 入口与文档

- [x] 8.1 实现 `src/main.py` 入口脚本：组装 DataLoader、Strategy、RiskManager、PositionSizer、BacktestEngine，运行回测并输出结果
- [x] 8.2 更新 `README.md`：项目说明、目录结构、快速上手指南、依赖安装说明

## 9. 清理与验证

- [x] 9.1 废弃 `src/simple_backtest.py`（保留备份或删除）
- [x] 9.2 使用相同数据和参数运行新模块化回测，对比旧脚本结果验证正确性
