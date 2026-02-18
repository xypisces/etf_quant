## 1. 基础设施

- [x] 1.1 在 `pyproject.toml` 中添加 `tqdm` 依赖（批量回测进度条），运行 `uv sync`
- [x] 1.2 创建 `src/research/` 目录和 `__init__.py`

## 2. 海龟策略 (`src/strategy/turtle.py`)

- [x] 2.1 实现 `TurtleStrategy` 类：唐奇安通道上轨突破买入、下轨/ATR 止损卖出
- [x] 2.2 在 `src/config.py` 的 `STRATEGY_REGISTRY` 中注册 `turtle` → `TurtleStrategy`
- [x] 2.3 运行回测验证海龟策略

## 3. 网格交易策略 (`src/strategy/grid.py`)

- [x] 3.1 实现 `GridStrategy` 类：自动/手动设定网格区间，下穿买入、上穿卖出
- [x] 3.2 在 `STRATEGY_REGISTRY` 中注册 `grid` → `GridStrategy`
- [x] 3.3 运行回测验证网格策略

## 4. 动量轮动策略 (`src/strategy/momentum.py`)

- [x] 4.1 实现 `MomentumStrategy` 类：计算 N 日 ROC 动量得分，正动量买入、负动量卖出
- [x] 4.2 在 `STRATEGY_REGISTRY` 中注册 `momentum` → `MomentumStrategy`
- [x] 4.3 运行回测验证动量策略

## 5. 均值回归策略 (`src/strategy/mean_reversion.py`)

- [x] 5.1 实现 `MeanReversionStrategy` 类：布林带超买超卖 + RSI 过滤
- [x] 5.2 在 `STRATEGY_REGISTRY` 中注册 `mean_reversion` → `MeanReversionStrategy`
- [x] 5.3 运行回测验证均值回归策略

## 6. 批量回测器 (`src/research/batch_runner.py`)

- [x] 6.1 实现 `BatchRunner` 类：接受品种列表×策略列表，运行矩阵化回测，返回汇总 DataFrame
- [x] 6.2 验证多品种多策略批量回测并输出排序结果

## 7. 参数优化器 (`src/research/optimizer.py`)

- [x] 7.1 实现 `ParameterOptimizer` 类：Grid Search 参数遍历
- [x] 7.2 实现 Walk-forward 交叉验证，输出训练/测试期对比和过拟合警告
- [x] 7.3 验证优化器功能

## 8. 集成与文档

- [x] 8.1 更新 `config.yaml` 添加新策略配置示例
- [x] 8.2 更新 `README.md` 新增策略说明和研究工具使用文档
