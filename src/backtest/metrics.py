"""
绩效指标模块 - 夏普比率、最大回撤、胜率、盈亏比等
"""

import pandas as pd


# 全局配置
RISK_FREE_RATE = 0.0
TRADING_DAYS_PER_YEAR = 252


def sharpe_ratio(daily_returns: pd.Series) -> float:
    """
    计算年化夏普比率

    公式: (日收益率均值 - 无风险日利率) / 日收益率标准差 × √252

    Args:
        daily_returns: 策略每日收益率序列

    Returns:
        年化夏普比率，无波动时返回 0
    """
    if daily_returns.empty:
        return 0.0
    daily_std = daily_returns.std()
    if daily_std == 0:
        return 0.0
    daily_rf = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
    return (daily_returns.mean() - daily_rf) / daily_std * (TRADING_DAYS_PER_YEAR ** 0.5)


def max_drawdown(equity_curve: pd.Series) -> float:
    """
    计算最大回撤

    公式: min((净值 - 历史最高净值) / 历史最高净值)

    Args:
        equity_curve: 累计净值序列

    Returns:
        最大回撤幅度（负数百分比），无数据时返回 0
    """
    if equity_curve.empty:
        return 0.0
    cum_max = equity_curve.cummax()
    drawdown = (equity_curve - cum_max) / cum_max
    return drawdown.min()


def total_return(equity_curve: pd.Series) -> float:
    """
    计算总收益率

    Args:
        equity_curve: 累计净值序列

    Returns:
        总收益率 = 最终净值 / 初始净值 - 1
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0
    return equity_curve.iloc[-1] / equity_curve.iloc[0] - 1


def annualized_return(total_ret: float, days: int) -> float:
    """
    计算年化收益率

    Args:
        total_ret: 总收益率
        days: 回测天数

    Returns:
        年化收益率
    """
    if days <= 0:
        return 0.0
    return (1 + total_ret) ** (365 / days) - 1


def win_rate(trades: list[dict]) -> float:
    """
    计算胜率

    Args:
        trades: 交易记录列表，每条记录包含 'pnl' 字段

    Returns:
        胜率 = 盈利交易数 / 总交易数，无交易时返回 0
    """
    if not trades:
        return 0.0
    winning = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return winning / len(trades)


def profit_loss_ratio(trades: list[dict]) -> float:
    """
    计算盈亏比

    Args:
        trades: 交易记录列表，每条记录包含 'pnl' 字段

    Returns:
        盈亏比 = 平均盈利 / 平均亏损（绝对值），
        无亏损返回 float('inf')，无盈利返回 0
    """
    if not trades:
        return 0.0

    profits = [t["pnl"] for t in trades if t.get("pnl", 0) > 0]
    losses = [t["pnl"] for t in trades if t.get("pnl", 0) < 0]

    if not profits:
        return 0.0
    if not losses:
        return float("inf")

    avg_profit = sum(profits) / len(profits)
    avg_loss = abs(sum(losses) / len(losses))

    return avg_profit / avg_loss if avg_loss > 0 else float("inf")


def print_report(
    equity_curve: pd.Series,
    daily_returns: pd.Series,
    trades: list[dict],
    symbol: str = "",
) -> None:
    """
    打印文本绩效报告

    Args:
        equity_curve: 净值序列
        daily_returns: 每日收益率序列
        trades: 交易记录列表
        symbol: 标的代码
    """
    total_ret = total_return(equity_curve)

    if len(equity_curve) >= 2:
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
    else:
        days = 0

    annual_ret = annualized_return(total_ret, days)
    sharpe = sharpe_ratio(daily_returns)
    mdd = max_drawdown(equity_curve)
    wr = win_rate(trades)
    plr = profit_loss_ratio(trades)

    print("-" * 40)
    print(f"  回测报告: {symbol}")
    print("-" * 40)
    print(f"  总收益率 (Total Return):     {total_ret:>10.2%}")
    print(f"  年化收益率 (Annualized):     {annual_ret:>10.2%}")
    print(f"  夏普比率 (Sharpe Ratio):     {sharpe:>10.2f}")
    print(f"  最大回撤 (Max Drawdown):     {mdd:>10.2%}")
    print(f"  胜率 (Win Rate):             {wr:>10.2%}")
    plr_str = f"{plr:.2f}" if plr != float("inf") else "∞"
    print(f"  盈亏比 (P/L Ratio):          {plr_str:>10}")
    print(f"  交易次数 (Total Trades):     {len(trades):>10}")
    print("-" * 40)
