# ETF 量化交易系统 (etf-quant)

基于 Python 的 ETF 量化交易回测框架，采用事件驱动架构，支持策略开发、风控管理和绩效分析。

## 特性

- 🔄 **事件驱动回测** — 逐 bar 推送，与实盘逻辑一致
- 📊 **标准化策略接口** — 继承 `Strategy` 基类即可开发新策略
- 📈 **6 种内置策略** — 双均线交叉、EMA20 回踩、海龟、网格交易、动量轮动、均值回归
- 🔬 **研究工具** — 批量回测 (多品种×多策略)、参数优化 (Grid Search + Walk-forward)
- 🛡️ **内置风控** — 止损止盈、最大持仓限制
- 💰 **仓位管理** — 支持固定比例 / ATR / Kelly 公式
- 💾 **数据管理层** — SQLite 元数据 + Parquet 行情存储，支持增量更新
- 📈 **五维度绩效报告** — 收益、风险、效率、交易统计、月度矩阵
- 🎨 **综合仪表板** — 资金曲线(log) + 水下回撤 + 月度热力图
- 📝 **Markdown 持久化报告** — 按标的分目录存储，多策略增量追加
- 🏆 **策略对比汇总** — 自动排名所有策略收益率（含买入持有基准）

## 项目结构

```
etf_quant/
├── src/
│   ├── data/
│   │   ├── loader.py           # 统一数据加载接口
│   │   ├── storage.py          # 本地存储 (SQLite元数据 + Parquet行情)
│   │   ├── fetcher.py          # 数据下载器 (akshare, 增量更新)
│   │   └── cleaner.py          # 数据清洗器 (去重/排序/缺失值/类型)
│   ├── strategy/
│   │   ├── base.py             # Strategy 基类 + Signal 枚举
│   │   ├── ma_cross.py         # 双均线交叉策略
│   │   ├── ema20_pullback.py   # EMA20 回踩双支撑策略
│   │   ├── turtle.py           # 海龟策略 (唐奇安通道+ATR)
│   │   ├── grid.py             # 网格交易策略
│   │   ├── momentum.py         # 动量轮动策略 (ROC)
│   │   └── mean_reversion.py   # 均值回归策略 (布林带+RSI)
│   ├── research/
│   │   ├── batch_runner.py     # 批量回测 (多品种×多策略)
│   │   └── optimizer.py        # 参数优化 (Grid+Walk-forward)
│   ├── backtest/
│   │   ├── engine.py           # 事件驱动回测引擎
│   │   └── metrics.py          # 五维度绩效指标计算 + Markdown 格式化
│   ├── risk/
│   │   ├── position_sizer.py   # 仓位管理 (固定比例/ATR/Kelly)
│   │   └── risk_manager.py     # 止损止盈、持仓限制
│   ├── utils/
│   │   ├── plotting.py         # 综合仪表板 (三图合一)
│   │   └── reporter.py         # Markdown 报告写入 + 策略对比汇总
│   └── main.py                 # 入口脚本
├── data/                       # 数据存储目录
│   ├── market.db               # SQLite 品种元数据
│   └── parquet/                # Parquet 行情文件
│       └── <symbol>.parquet
├── results/                    # 回测结果输出 (按标的分目录)
│   └── <symbol>/
│       ├── report.md           # 五维度报告 (多策略增量追加)
│       └── dashboard_*.png     # 仪表板图片 (带时间戳)
└── doc/
    └── backtest.md             # 回测报告维度说明
```

## 快速上手

### 环境要求

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) 包管理器

### 安装依赖

```bash
uv sync
```

### 运行回测

```bash
uv run python -m src.main
```

可通过 `--config` 指定配置文件（默认读取项目根目录 `config.yaml`）：

```bash
uv run python -m src.main --config my_config.yaml
```

### 配置文件

所有参数在 `config.yaml` 中集中管理，无需修改代码：

```yaml
data:
  symbol: "600111"         # 标的代码
  start_date: "20200101"   # 回测起始日期

strategy:
  name: "ema20_pullback"   # 策略名: ma_cross / ema20_pullback / turtle / grid / momentum / mean_reversion
  params:
    ema_period: 20

risk:
  stop_loss: -0.05
  take_profit: 0.10

engine:
  initial_capital: 100000
```

**EMA20 回踩策略参数说明：**

| 参数                 | 默认值 | 说明                         |
| -------------------- | ------ | ---------------------------- |
| `ema_period`         | 20     | EMA 均线周期                 |
| `macd_fast`          | 12     | MACD 快线周期                |
| `macd_slow`          | 26     | MACD 慢线周期                |
| `macd_signal`        | 9      | MACD 信号线周期              |
| `volume_period`      | 20     | 成交量均值回看窗口           |
| `pullback_tolerance` | 0.005  | 回踩 EMA20 的容忍偏差 (0.5%) |

### 回测结果

运行后自动生成：
- `results/<symbol>/report.md` — 包含五维度报告、月度收益矩阵和策略对比汇总表
- `results/<symbol>/dashboard_<策略名>_<时间戳>.png` — 三合一仪表板图片

多次运行不同策略或参数后，报告会自动增量追加，对比表自动更新排名。

### 批量回测

```python
from src.research import BatchRunner

runner = BatchRunner(storage_dir='data')
results = runner.run(
    symbols=['510300', '512800'],
    strategies=[
        {'name': 'turtle', 'params': {'entry_period': 20}},
        {'name': 'momentum', 'params': {'lookback_period': 20}},
    ],
    start_date='20200101',
    end_date='20260101',
)
print(results)  # DataFrame: symbol, strategy, total_return, sharpe_ratio, ...
```

### 参数优化

```python
from src.research import ParameterOptimizer

opt = ParameterOptimizer(n_splits=5, target_metric='sharpe_ratio')

# Grid Search
results = opt.grid_search(
    strategy_name='turtle',
    param_space={'entry_period': [10, 20, 30], 'exit_period': [5, 10, 15]},
    df=df,
)

# Walk-forward 交叉验证
summary = opt.walk_forward('turtle', param_space, df)
print(summary['warning'])  # 过拟合警告
```

### 自定义策略

继承 `Strategy` 基类，实现 `on_bar()` 和 `generate_signal()` 方法：

```python
from src.strategy.base import Strategy, Signal

class MyStrategy(Strategy):
    def on_bar(self, bar: dict) -> None:
        # 接收 K 线数据，更新内部状态
        pass

    def generate_signal(self) -> Signal:
        # 返回 BUY / SELL / HOLD
        return Signal.HOLD
```

## 依赖

| 包         | 用途           |
| ---------- | -------------- |
| pandas     | 数据处理       |
| akshare    | 数据获取       |
| pyarrow    | Parquet 读写   |
| matplotlib | 可视化         |
| numpy      | 数值计算       |
| pyyaml     | 配置文件解析   |
| tqdm       | 批量回测进度条 |