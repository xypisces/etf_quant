"""
参数优化器 - Grid Search + Walk-forward 交叉验证

支持对策略参数进行穷举搜索，并通过 Walk-forward 验证防止过拟合。
"""

import itertools

import pandas as pd
from tqdm import tqdm

from src.backtest.engine import BacktestEngine
from src.backtest.metrics import total_return, sharpe_ratio, max_drawdown
from src.config import create_strategy
from src.risk.risk_manager import RiskManager
from src.risk.position_sizer import PositionSizer, SizingMethod


class ParameterOptimizer:
    """
    参数优化器

    Grid Search：对参数空间做笛卡尔积遍历。
    Walk-forward：数据分段训练+测试，防止过拟合。
    """

    def __init__(
        self,
        n_splits: int = 5,
        train_ratio: float = 0.7,
        target_metric: str = "sharpe_ratio",
        max_combinations: int = 1000,
        initial_capital: float = 100000,
        slippage: float = 0.0001,
        commission_rate: float = 0.0003,
        stop_loss: float = -0.05,
        take_profit: float = 0.10,
    ):
        self.n_splits = n_splits
        self.train_ratio = train_ratio
        self.target_metric = target_metric
        self.max_combinations = max_combinations
        self.initial_capital = initial_capital
        self.slippage = slippage
        self.commission_rate = commission_rate
        self.stop_loss = stop_loss
        self.take_profit = take_profit

    def grid_search(
        self,
        strategy_name: str,
        param_space: dict[str, list],
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        网格搜索参数优化

        Args:
            strategy_name: 策略名称（如 "turtle"）
            param_space: 参数空间，如 {"entry_period": [10, 20, 30], "exit_period": [5, 10]}
            df: 行情 DataFrame

        Returns:
            按目标指标排序的参数组合结果 DataFrame
        """
        keys = list(param_space.keys())
        values = list(param_space.values())
        combinations = list(itertools.product(*values))

        if len(combinations) > self.max_combinations:
            print(
                f"[Optimizer] 警告: 参数组合数 {len(combinations)} "
                f"超过上限 {self.max_combinations}，仍将执行"
            )

        results = []
        for combo in tqdm(combinations, desc="Grid Search"):
            params = dict(zip(keys, combo))
            strat_cfg = {"name": strategy_name, "params": params}
            metrics = self._run_single(strat_cfg, df)
            metrics["params"] = str(params)
            for k, v in params.items():
                metrics[k] = v
            results.append(metrics)

        df_results = pd.DataFrame(results)
        ascending = self.target_metric == "max_drawdown"
        df_results.sort_values(
            self.target_metric, ascending=ascending, inplace=True
        )
        df_results.reset_index(drop=True, inplace=True)

        return df_results

    def walk_forward(
        self,
        strategy_name: str,
        param_space: dict[str, list],
        df: pd.DataFrame,
    ) -> dict:
        """
        Walk-forward 交叉验证

        Args:
            strategy_name: 策略名称
            param_space: 参数空间
            df: 完整行情 DataFrame

        Returns:
            包含各段训练/测试结果和过拟合评估的字典
        """
        n = len(df)
        split_size = n // self.n_splits
        train_size = int(split_size * self.train_ratio)

        fold_results = []

        for i in range(self.n_splits):
            start = i * split_size
            end = min(start + split_size, n)
            if end - start < 30:
                continue  # 数据太少跳过

            train_df = df.iloc[start : start + train_size]
            test_df = df.iloc[start + train_size : end]

            if len(train_df) < 20 or len(test_df) < 10:
                continue

            # 训练期：Grid Search 找最优参数
            print(f"\n[Walk-forward] Fold {i + 1}/{self.n_splits}")
            train_results = self.grid_search(strategy_name, param_space, train_df)

            if train_results.empty:
                continue

            best_row = train_results.iloc[0]

            # 提取最优参数
            keys = list(param_space.keys())
            best_params = {k: best_row[k] for k in keys}

            # 测试期：用最优参数验证
            strat_cfg = {"name": strategy_name, "params": best_params}
            test_metrics = self._run_single(strat_cfg, test_df)

            fold_results.append({
                "fold": i + 1,
                "best_params": str(best_params),
                "train_return": best_row.get("total_return", 0),
                "train_sharpe": best_row.get("sharpe_ratio", 0),
                "test_return": test_metrics.get("total_return", 0),
                "test_sharpe": test_metrics.get("sharpe_ratio", 0),
            })

        # 汇总
        df_folds = pd.DataFrame(fold_results) if fold_results else pd.DataFrame()
        summary = self._evaluate_overfitting(df_folds)
        summary["folds"] = df_folds

        return summary

    def _run_single(self, strat_cfg: dict, df: pd.DataFrame) -> dict:
        """运行单次回测并返回指标"""
        strategy = create_strategy(strat_cfg)
        risk_manager = RiskManager(
            stop_loss=self.stop_loss,
            take_profit=self.take_profit,
        )
        position_sizer = PositionSizer(
            method=SizingMethod("fixed_fraction"),
            risk_fraction=0.95,
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

        return {
            "total_return": round(ret, 4),
            "sharpe_ratio": round(sr, 4) if sr else 0.0,
            "max_drawdown": round(mdd, 4),
            "trade_count": len(result.trades),
        }

    @staticmethod
    def _evaluate_overfitting(df_folds: pd.DataFrame) -> dict:
        """评估过拟合程度"""
        if df_folds.empty:
            return {"warning": "数据不足，无法评估", "overfitting": False}

        avg_train_ret = df_folds["train_return"].mean()
        avg_test_ret = df_folds["test_return"].mean()

        overfitting = False
        warning = None

        if avg_train_ret > 0:
            decay = 1 - (avg_test_ret / avg_train_ret)
            if decay > 0.5:
                overfitting = True
                warning = (
                    f"⚠️ 过拟合警告: 训练期平均收益 {avg_train_ret:.2%}, "
                    f"测试期平均收益 {avg_test_ret:.2%}, "
                    f"衰减率 {decay:.0%} > 50%"
                )

        return {
            "avg_train_return": round(avg_train_ret, 4),
            "avg_test_return": round(avg_test_ret, 4),
            "overfitting": overfitting,
            "warning": warning,
        }
