"""
批量回测器 - 多品种 × 多策略矩阵化回测

支持同时运行多个品种和多个策略组合的回测，
汇总结果并按指标排序对比。
"""

import pandas as pd
from tqdm import tqdm

from src.backtest.engine import BacktestEngine
from src.backtest.metrics import total_return, sharpe_ratio, max_drawdown
from src.config import create_strategy
from src.data.loader import DataLoader
from src.risk.risk_manager import RiskManager
from src.risk.position_sizer import PositionSizer, SizingMethod


class BatchRunner:
    """
    批量回测器

    对 品种列表 × 策略列表 运行矩阵化回测，返回汇总 DataFrame。
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        slippage: float = 0.0001,
        commission_rate: float = 0.0003,
        stop_loss: float = -0.05,
        take_profit: float = 0.10,
        sizing_method: str = "fixed_fraction",
        risk_fraction: float = 0.95,
        storage_dir: str = "data",
    ):
        self.initial_capital = initial_capital
        self.slippage = slippage
        self.commission_rate = commission_rate
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.sizing_method = sizing_method
        self.risk_fraction = risk_fraction
        self.storage_dir = storage_dir

    def run(
        self,
        symbols: list[str],
        strategies: list[dict],
        start_date: str,
        end_date: str,
        sort_by: str = "total_return",
    ) -> pd.DataFrame:
        """
        运行批量回测

        Args:
            symbols: 品种代码列表，如 ['510300', '512800']
            strategies: 策略配置列表，如 [{"name": "turtle", "params": {...}}, ...]
            start_date: 起始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            sort_by: 排序指标 (total_return / sharpe_ratio / max_drawdown)

        Returns:
            汇总 DataFrame，含 symbol, strategy, total_return, sharpe_ratio, max_drawdown, trade_count
        """
        loader = DataLoader(storage_dir=self.storage_dir)
        results = []
        total = len(symbols) * len(strategies)

        with tqdm(total=total, desc="批量回测") as pbar:
            for symbol in symbols:
                df = loader.load(symbol, start_date, end_date)
                if df.empty:
                    pbar.update(len(strategies))
                    continue

                for strat_cfg in strategies:
                    strategy = create_strategy(strat_cfg)

                    risk_manager = RiskManager(
                        stop_loss=self.stop_loss,
                        take_profit=self.take_profit,
                    )
                    position_sizer = PositionSizer(
                        method=SizingMethod(self.sizing_method),
                        risk_fraction=self.risk_fraction,
                    )

                    engine = BacktestEngine(
                        strategy=strategy,
                        risk_manager=risk_manager,
                        position_sizer=position_sizer,
                        initial_capital=self.initial_capital,
                        slippage=self.slippage,
                        commission_rate=self.commission_rate,
                    )

                    result = engine.run(df)

                    ret = total_return(result.equity_curve)
                    sr = sharpe_ratio(result.daily_returns)
                    mdd = max_drawdown(result.equity_curve)

                    results.append({
                        "symbol": symbol,
                        "strategy": result.strategy_name,
                        "total_return": round(ret, 4),
                        "sharpe_ratio": round(sr, 4) if sr else 0.0,
                        "max_drawdown": round(mdd, 4),
                        "trade_count": len(result.trades),
                    })
                    pbar.update(1)

        if not results:
            return pd.DataFrame()

        df_results = pd.DataFrame(results)
        ascending = sort_by == "max_drawdown"
        df_results.sort_values(sort_by, ascending=ascending, inplace=True)
        df_results.reset_index(drop=True, inplace=True)

        return df_results
