## Why

当前系统仅有两套策略（双均线交叉、EMA20 回踩），且缺乏策略研发和评估的系统化能力。新策略想法只能手动编码、逐个回测、目视对比，无法高效验证。需要扩展策略库并建立研究基础设施，让策略开发从"手工作坊"进化为"流水线研发"。

## What Changes

**新增策略：**
- **海龟策略** (`src/strategy/turtle.py`)：基于唐奇安通道突破 + ATR 动态止损/仓位管理
- **网格交易** (`src/strategy/grid.py`)：设定价格区间，低吸高抛
- **动量轮动** (`src/strategy/momentum.py`)：多品种动量评分，定期轮动持有强势品种
- **均值回归** (`src/strategy/mean_reversion.py`)：基于布林带/RSI 的超买超卖信号

**新增研究能力：**
- **多品种多策略批量回测** (`src/research/batch_runner.py`)：同时运行多个策略对多个品种的回测，自动汇总对比
- **参数优化器** (`src/research/optimizer.py`)：网格搜索 + Walk-forward 交叉验证，防止过拟合
- **因子分析** (`src/research/factor_analysis.py`)：因子 IC 计算、分组回测，用于策略因子筛选

**配置扩展：**
- `config.yaml` 支持批量策略和品种配置

## Capabilities

### New Capabilities
- `turtle-strategy`：海龟策略（唐奇安通道突破 + ATR 动态止损）
- `grid-strategy`：网格交易策略（区间低吸高抛）
- `momentum-strategy`：动量轮动策略（多品种动量评分轮动）
- `mean-reversion-strategy`：均值回归策略（布林带/RSI 超买超卖）
- `batch-backtest`：多品种多策略批量回测与对比能力
- `parameter-optimizer`：参数优化（Grid Search + Walk-forward 交叉验证）

### Modified Capabilities
- `strategy-framework`：策略注册表需新增 4 个策略映射；策略基类可能需要扩展以支持多品种轮动场景

## Impact

- **代码影响**：`src/strategy/` 新增 4 个策略模块；新建 `src/research/` 目录，含 3 个研究模块
- **配置影响**：`config.yaml` 扩展批量回测配置
- **依赖影响**：可能需要 `scipy`（优化器）和 `tqdm`（进度条）
- **兼容性**：所有新策略继承 `Strategy` 基类，与现有回测引擎兼容。新增研究模块独立于回测主流程，不影响现有功能
