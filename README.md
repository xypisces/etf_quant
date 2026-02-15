# ETF 量化交易系统 (etf-quant)

基于 Python 的 ETF 量化交易回测框架，采用事件驱动架构，支持策略开发、风控管理和绩效分析。

## 特性

- 🔄 **事件驱动回测** — 逐 bar 推送，与实盘逻辑一致
- 📊 **标准化策略接口** — 继承 `Strategy` 基类即可开发新策略
- 🛡️ **内置风控** — 止损止盈、最大持仓限制
- 💰 **仓位管理** — 支持固定比例 / ATR / Kelly 公式
- 📈 **五维度绩效报告** — 收益、风险、效率、交易统计、月度矩阵
- 🎨 **综合仪表板** — 资金曲线(log) + 水下回撤 + 月度热力图
- 📝 **Markdown 持久化报告** — 按标的分目录存储，多策略增量追加
- 🏆 **策略对比汇总** — 自动排名所有策略收益率（含买入持有基准）

## 项目结构

```
etf_quant/
├── src/
│   ├── data/
│   │   └── loader.py           # 统一数据加载接口 (CSV/akshare API)
│   ├── strategy/
│   │   ├── base.py             # Strategy 基类 + Signal 枚举
│   │   └── ma_cross.py         # 双均线交叉策略
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
├── csv/                        # 数据缓存
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

默认配置：
- 标的：600111
- 策略：双均线交叉 (MA5/MA20)
- 初始资金：¥100,000
- 止损/止盈：-5% / +10%

### 回测结果

运行后自动生成：
- `results/<symbol>/report.md` — 包含五维度报告、月度收益矩阵和策略对比汇总表
- `results/<symbol>/dashboard_<策略名>_<时间戳>.png` — 三合一仪表板图片

多次运行不同策略或参数后，报告会自动增量追加，对比表自动更新排名。

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

| 包         | 用途     |
| ---------- | -------- |
| pandas     | 数据处理 |
| akshare    | 数据获取 |
| matplotlib | 可视化   |
| numpy      | 数值计算 |