## Why

当前项目所有逻辑（数据获取、信号计算、绩效统计、报告绘图）都写在一个 185 行的脚本 `src/simple_backtest.py` 里，属于典型的"一坨代码"状态。这导致：
- **无法复用**：新增策略（海龟、网格、动量轮动）需要大量复制粘贴
- **无法扩展**：回测引擎和策略逻辑耦合，无法独立演进
- **缺少风控**：没有仓位管理、止损止盈、滑点/手续费模型
- **不适配实盘**：向量化计算使用了未来数据（如整列 rolling），与逐 bar 推送的实盘逻辑不可复用

现在需要在项目早期建立模块化架构，为后续扩展（多策略、Backtrader 适配、实盘对接）打下基础。

## What Changes

- **拆分数据层** (`src/data/loader.py`)：将 `fetch_data()` 抽取为独立数据加载模块，支持 CSV 缓存和 akshare API
- **建立策略抽象** (`src/strategy/`)：定义 `Strategy` 基类（`on_bar()`、`generate_signal()` 接口），实现 `MACrossStrategy` 双均线策略
- **事件驱动回测引擎** (`src/backtest/engine.py`)：将向量化回测重写为逐 bar 推送的事件驱动引擎，确保与实盘逻辑一致
- **绩效指标模块** (`src/backtest/metrics.py`)：抽取夏普比率、最大回撤、胜率、盈亏比为独立计算模块
- **风控与仓位管理** (`src/risk/`)：内置 `PositionSizer`（固定比例/ATR/Kelly）和 `RiskManager`（止损止盈、最大持仓限制），滑点与手续费模型
- **可视化工具** (`src/utils/plotting.py`)：抽取绘图逻辑为独立模块
- **入口脚本** (`src/main.py`)：重写为使用模块化组件的入口
- **更新 README.md**：补充项目说明、目录结构、快速上手指南

## Capabilities

### New Capabilities
- `data-loader`：统一数据加载接口，支持 CSV 缓存与 akshare API 获取，标准化 OHLCV 输出格式
- `strategy-framework`：策略基类与标准接口定义（`on_bar()`、`generate_signal()`），禁止未来函数，支持继承扩展新策略
- `event-driven-backtest`：逐 bar 推送的事件驱动回测引擎，支持单品种单策略，内置滑点与手续费模型
- `performance-metrics`：独立绩效指标计算模块（夏普比率、最大回撤、胜率、盈亏比、年化收益等）
- `risk-management`：仓位管理（固定比例/ATR/Kelly）与风控检查（止损止盈、最大持仓限制），下单前必过风控

### Modified Capabilities
- `vectorized-backtest`：回测方式从向量化改为事件驱动，原向量化回测代码将被替代。现有 spec 中的数据获取和信号计算需求迁移到新的 `data-loader` 和 `strategy-framework` 能力中

## Impact

- **代码结构**：`src/simple_backtest.py` 将被拆解到 5 个子模块中，原文件废弃
- **入口变更**：`main.py` 从空壳改为实际入口，调用模块化组件
- **依赖不变**：继续使用 `akshare`、`pandas`、`matplotlib`，无需新增第三方依赖
- **数据格式**：CSV 缓存保持兼容，`csv/` 目录继续使用
- **向后兼容**：这是全新架构，不存在向后兼容问题（现有代码仅为原型）
- **README.md**：从空白状态更新为完整项目文档
