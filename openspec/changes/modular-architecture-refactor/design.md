## Context

当前项目只有一个 185 行的脚本 `src/simple_backtest.py`，包含数据获取、均线信号计算、绩效统计和绘图四个功能，全部耦合在一起。项目需要从原型阶段演进为可扩展的模块化架构，支持多策略、风控、以及未来的实盘对接。

现有依赖：`akshare`（数据源）、`pandas`（数据处理）、`matplotlib`（绘图）。Python 3.12，使用 `uv` 管理依赖。

## Goals / Non-Goals

**Goals:**
- 将单文件脚本拆解为 5 个独立模块（data、strategy、backtest、risk、utils）
- 建立事件驱动回测引擎，逐 bar 推送，与实盘逻辑一致
- 定义标准化策略接口，新增策略只需继承实现
- 内置风控和仓位管理，下单前必过检查
- 内置滑点与手续费模型
- 支持单品种、单策略回测

**Non-Goals:**
- 多品种、多策略同时回测（后续迭代）
- 实盘交易对接（架构预留，本次不实现）
- Backtrader 适配器（后续迭代）
- 海龟/网格/动量轮动策略实现（本次只实现双均线迁移）
- Web UI 或前端界面

## Decisions

### 决策 1: 事件驱动 vs 向量化回测

**选择**：事件驱动（逐 bar 推送）

**理由**：
- 向量化回测虽然快，但天然可以使用"未来数据"（如 `shift(-1)`、全列 rolling），与实盘逻辑不一致
- 事件驱动模式下，策略在每个 bar 只能看到当前及历史数据，杜绝未来函数
- 未来对接实盘时，策略代码可以直接复用，无需重写

**替代方案**：保留向量化回测作为快速验证工具 → 拒绝，增加维护负担且鼓励"双套代码"

### 决策 2: 策略接口设计

**选择**：定义 `Strategy` 抽象基类，提供 `on_bar(bar_data)` 和 `generate_signal()` 接口

```python
class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: dict) -> None:
        """接收一根 bar 数据，更新策略内部状态"""
        pass

    @abstractmethod
    def generate_signal(self) -> Signal:
        """根据当前状态生成交易信号"""
        pass
```

**理由**：
- `on_bar()` 确保策略只能逐 bar 处理数据，防止未来函数
- `generate_signal()` 分离信号生成和执行，便于日志记录和风控介入
- 策略内部可自行维护 rolling window（如均线历史），不依赖外部计算

### 决策 3: 回测引擎核心循环

**选择**：引擎负责调度，策略无权直接下单

```
for each bar in data:
    1. strategy.on_bar(bar)           → 策略接收数据
    2. signal = strategy.generate_signal() → 策略产出信号
    3. risk_manager.check(signal)      → 风控检查
    4. position_sizer.calculate(signal) → 计算仓位
    5. engine.execute_order(...)        → 执行（含滑点/手续费）
    6. engine.update_portfolio()        → 更新持仓和净值
```

**理由**：策略、风控、仓位管理职责分离，每一层都可以独立替换和测试

### 决策 4: 数据加载层设计

**选择**：`DataLoader` 类，统一接口，CSV 缓存优先

**行为**：
1. 检查 `csv/` 目录下是否有缓存文件
2. 如有 → 直接读取 CSV
3. 如无 → 调用 akshare API 获取 → 标准化列名为 `date/open/high/low/close/volume` → 保存到 `csv/` 缓存
4. 返回标准化的 `pd.DataFrame`

**理由**：复用现有 `fetch_data()` 逻辑，减少 API 调用，保持与现有 CSV 数据兼容

### 决策 5: 风控模块架构

**选择**：`RiskManager` + `PositionSizer` 双组件模式

- **PositionSizer**：根据策略选择（固定比例 / ATR / Kelly）计算开仓数量
- **RiskManager**：止损止盈检查、最大持仓限制，返回 通过/拒绝/调整 结果

**理由**：仓位计算和风险控制是两个独立关注点，分离后可以独立配置和测试

### 决策 6: 滑点与手续费模型

**选择**：内置于引擎的订单执行阶段

- **滑点**：固定比例（默认 0.01%），应用到成交价格
- **手续费**：固定比例（默认 0.03%），从账户余额扣除

**理由**：在回测阶段模拟真实交易损耗，避免过于乐观的回测结果

### 决策 7: 目录结构

```
src/
├── data/
│   └── loader.py           # DataLoader 类
├── strategy/
│   ├── base.py             # Strategy ABC
│   └── ma_cross.py         # MACrossStrategy（从 simple_backtest 迁移）
├── backtest/
│   ├── engine.py           # BacktestEngine 核心循环
│   └── metrics.py          # 绩效指标计算函数集
├── risk/
│   ├── position_sizer.py   # PositionSizer（固定比例/ATR/Kelly）
│   └── risk_manager.py     # RiskManager（止损止盈/持仓限制）
├── utils/
│   └── plotting.py         # 结果可视化
└── main.py                 # 入口（组装组件、运行回测）
```

## Risks / Trade-offs

- **性能下降** → 事件驱动逐 bar 循环比向量化慢 10-100x。缓解：单品种单策略场景下数据量有限（ETF 日线几千条），性能可接受
- **过度设计** → 当前只有一个双均线策略，模块化架构可能显得过重。缓解：架构复杂度适中（~6 个文件），为后续扩展节省的重写成本远大于初始投入
- **策略迁移风险** → 从向量化迁移到事件驱动，结果可能有细微差异。缓解：使用相同数据和参数，对比新旧回测结果是否一致
- **无测试覆盖** → 本次重构不包含单元测试。缓解：后续迭代优先补测试
