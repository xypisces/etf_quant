## Why

当前系统仅有双均线交叉策略（MACross），属于纯趋势跟踪型策略，在震荡市容易产生频繁的虚假信号。需要增加一个基于 EMA20 回踩的"双支撑"策略，结合 MACD 动量确认和缩量验证，在趋势延续阶段精准入场，提升策略胜率和盈亏比。

## What Changes

- **新增** `EMA20PullbackStrategy` 策略类，继承现有 `Strategy` 基类
- **入场条件**（三条件同时满足）：
  1. 价格回踩 EMA20 附近后站稳，出现看涨信号（收盘价重返 EMA20 上方）
  2. MACD 柱状值在零轴上方（动量支撑）
  3. 回调期间成交量缩减（缩量回调确认是洗盘而非出货）
- **出场/止损条件**：
  1. 持仓期间：收盘价不破 EMA20，继续持有
  2. 收盘价跌破 EMA20 后，给予 1 个交易日的容忍期
  3. 若次日收盘价仍未回到 EMA20 上方 → 无条件卖出
- **集成** 到 `main.py`，能通过配置切换策略运行回测

## Capabilities

### New Capabilities
- `ema20-pullback-strategy`: EMA20 回踩双支撑策略的完整实现，包含 EMA20 计算、MACD 指标计算、成交量萎缩判断、入场信号生成、以及两日容忍止损逻辑

### Modified Capabilities
- `strategy-framework`: 在 `strategy/__init__.py` 中导出新策略，确保新策略可被 `main.py` 直接引用

## Impact

- **新增文件**: `src/strategy/ema20_pullback.py`
- **修改文件**: `src/strategy/__init__.py`（导出新策略）、`src/main.py`（切换策略配置）
- **依赖**: 无新外部依赖，所有技术指标（EMA、MACD）均使用内部逐 bar 计算实现
- **不影响**: 现有 `MACrossStrategy`、回测引擎、风控模块、报告模块均无需修改
