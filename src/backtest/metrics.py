"""
绩效指标模块 - 五维度专业回测分析

1. 核心收益指标 (Returns): 累计收益、年化收益、Alpha、Beta
2. 核心风险指标 (Risk): 最大回撤、回撤修复期、波动率
3. 风险收益效率 (Efficiency): 夏普比率、卡玛比率、索提诺比率
4. 交易统计 (Trade Stats): 胜率、盈亏比、交易频率、持仓周期、连亏次数
5. 综合报告: 文本输出
"""

import numpy as np
import pandas as pd


# ===== 全局配置 =====
RISK_FREE_RATE = 0.0
TRADING_DAYS_PER_YEAR = 252


# =====================================================================
# 1. 核心收益指标 (Returns)
# =====================================================================

def total_return(equity_curve: pd.Series) -> float:
    """累计收益率 = 最终净值 / 初始净值 - 1"""
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0
    return equity_curve.iloc[-1] / equity_curve.iloc[0] - 1


def annualized_return(total_ret: float, days: int) -> float:
    """年化收益率 (CAGR)"""
    if days <= 0:
        return 0.0
    return (1 + total_ret) ** (365 / days) - 1


def alpha_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> tuple[float, float]:
    """
    计算 Alpha 和 Beta

    Alpha: 超额收益（策略 - Beta × 基准）
    Beta: 策略与市场的相关性

    Returns:
        (alpha_annualized, beta)
    """
    if strategy_returns.empty or benchmark_returns.empty:
        return 0.0, 0.0

    # 对齐索引
    aligned = pd.DataFrame({
        "strategy": strategy_returns,
        "benchmark": benchmark_returns,
    }).dropna()

    if len(aligned) < 2:
        return 0.0, 0.0

    s = aligned["strategy"]
    b = aligned["benchmark"]

    # Beta = Cov(Rs, Rb) / Var(Rb)
    cov = s.cov(b)
    var_b = b.var()
    beta = cov / var_b if var_b > 0 else 0.0

    # Alpha (日) = E(Rs) - Beta * E(Rb) - Rf * (1 - Beta)
    daily_rf = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
    alpha_daily = s.mean() - beta * b.mean() - daily_rf * (1 - beta)

    # 年化 Alpha
    alpha_annual = alpha_daily * TRADING_DAYS_PER_YEAR

    return alpha_annual, beta


# =====================================================================
# 2. 核心风险指标 (Risk)
# =====================================================================

def max_drawdown(equity_curve: pd.Series) -> float:
    """最大回撤 = min((净值 - 历史最高净值) / 历史最高净值)"""
    if equity_curve.empty:
        return 0.0
    cum_max = equity_curve.cummax()
    drawdown = (equity_curve - cum_max) / cum_max
    return drawdown.min()


def drawdown_series(equity_curve: pd.Series) -> pd.Series:
    """回撤序列（用于水下回撤图）"""
    if equity_curve.empty:
        return pd.Series(dtype=float)
    cum_max = equity_curve.cummax()
    return (equity_curve - cum_max) / cum_max


def max_drawdown_recovery_days(equity_curve: pd.Series) -> int:
    """
    最大回撤修复期（从最大回撤低点到恢复创新高的交易日数）
    如果未恢复则返回 -1
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return 0

    cum_max = equity_curve.cummax()
    dd = (equity_curve - cum_max) / cum_max

    # 找到最大回撤的低点
    trough_idx = dd.idxmin()
    trough_pos = equity_curve.index.get_loc(trough_idx)

    # 回撤低点处的历史最高值
    peak_value = cum_max.iloc[trough_pos]

    # 从低点往后找恢复点
    after_trough = equity_curve.iloc[trough_pos:]
    recovered = after_trough[after_trough >= peak_value]

    if recovered.empty:
        return -1  # 未恢复

    recovery_idx = recovered.index[0]
    recovery_pos = equity_curve.index.get_loc(recovery_idx)
    return recovery_pos - trough_pos


def annual_volatility(daily_returns: pd.Series) -> float:
    """年化波动率 = 日标准差 × √252"""
    if daily_returns.empty:
        return 0.0
    return daily_returns.std() * (TRADING_DAYS_PER_YEAR ** 0.5)


# =====================================================================
# 3. 风险收益效率 (Efficiency)
# =====================================================================

def sharpe_ratio(daily_returns: pd.Series) -> float:
    """
    夏普比率 = (年化收益 - 无风险利率) / 年化波动率
    等价于: (日收益均值 - 日无风险利率) / 日标准差 × √252
    """
    if daily_returns.empty:
        return 0.0
    daily_std = daily_returns.std()
    if daily_std == 0:
        return 0.0
    daily_rf = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
    return (daily_returns.mean() - daily_rf) / daily_std * (TRADING_DAYS_PER_YEAR ** 0.5)


def calmar_ratio(annual_ret: float, mdd: float) -> float:
    """
    卡玛比率 = 年化收益 / |最大回撤|

    > 2 优秀（赚20%最多亏10%）
    """
    if mdd == 0:
        return 0.0
    return annual_ret / abs(mdd)


def sortino_ratio(daily_returns: pd.Series) -> float:
    """
    索提诺比率 — 只考虑下行波动的夏普比率
    公式: (日收益均值 - 日无风险利率) / 下行标准差 × √252
    """
    if daily_returns.empty:
        return 0.0
    daily_rf = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
    excess = daily_returns - daily_rf

    # 下行偏差: 只取负收益
    downside = excess[excess < 0]
    if downside.empty:
        return float("inf") if daily_returns.mean() > daily_rf else 0.0

    downside_std = np.sqrt((downside ** 2).mean())
    if downside_std == 0:
        return 0.0

    return (daily_returns.mean() - daily_rf) / downside_std * (TRADING_DAYS_PER_YEAR ** 0.5)


# =====================================================================
# 4. 交易统计 (Trade Statistics)
# =====================================================================

def win_rate(trades: list[dict]) -> float:
    """胜率 = 盈利交易数 / 总交易数"""
    if not trades:
        return 0.0
    winning = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return winning / len(trades)


def profit_loss_ratio(trades: list[dict]) -> float:
    """盈亏比 = 平均盈利 / |平均亏损|"""
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


def expectancy(trades: list[dict]) -> float:
    """
    期望值 = 胜率 × 盈亏比 - (1 - 胜率)

    黄金公式: 期望值 > 0 是盈利的数学基础
    """
    wr = win_rate(trades)
    plr = profit_loss_ratio(trades)
    if plr == float("inf"):
        return float("inf")
    return wr * plr - (1 - wr)


def trade_frequency(trades: list[dict], total_days: int) -> float:
    """交易频率: 平均几个交易日做一次交易"""
    if not trades or total_days <= 0:
        return 0.0
    return total_days / len(trades)


def avg_holding_period(trades: list[dict]) -> float:
    """平均持仓天数"""
    if not trades:
        return 0.0
    holding_days = []
    for t in trades:
        try:
            open_dt = pd.Timestamp(t["date_open"])
            close_dt = pd.Timestamp(t["date_close"])
            days = (close_dt - open_dt).days
            holding_days.append(max(days, 1))  # 至少 1 天
        except (KeyError, ValueError):
            continue
    return sum(holding_days) / len(holding_days) if holding_days else 0.0


def max_consecutive_losses(trades: list[dict]) -> int:
    """最大连续亏损次数"""
    if not trades:
        return 0
    max_streak = 0
    current_streak = 0
    for t in trades:
        if t.get("pnl", 0) < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def max_consecutive_wins(trades: list[dict]) -> int:
    """最大连续盈利次数"""
    if not trades:
        return 0
    max_streak = 0
    current_streak = 0
    for t in trades:
        if t.get("pnl", 0) > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


# =====================================================================
# 5. 月度/年度收益矩阵
# =====================================================================

def monthly_returns_table(daily_returns: pd.Series) -> pd.DataFrame:
    """
    生成月度收益矩阵（行=年，列=月）

    用于热力图展示
    """
    if daily_returns.empty:
        return pd.DataFrame()

    # 确保索引是 DatetimeIndex
    dr = daily_returns.copy()
    if not isinstance(dr.index, pd.DatetimeIndex):
        dr.index = pd.to_datetime(dr.index)

    # 计算月度收益: (1 + r1)(1 + r2)... - 1
    monthly = dr.resample("ME").apply(lambda x: (1 + x).prod() - 1)

    # 构建矩阵
    table = pd.DataFrame({
        "year": monthly.index.year,
        "month": monthly.index.month,
        "return": monthly.values,
    })

    pivot = table.pivot(index="year", columns="month", values="return")
    pivot.columns = [f"{m}月" for m in pivot.columns]

    # 添加年度总收益列
    yearly = dr.resample("YE").apply(lambda x: (1 + x).prod() - 1)
    pivot["全年"] = yearly.values[: len(pivot)]

    return pivot


# =====================================================================
# 综合报告
# =====================================================================

def format_report(
    equity_curve: pd.Series,
    daily_returns: pd.Series,
    trades: list[dict],
    benchmark_returns: pd.Series | None = None,
    symbol: str = "",
    strategy_name: str = "",
) -> str:
    """
    生成五维度专业回测报告（Markdown 格式字符串）

    Returns:
        Markdown 格式的报告字符串
    """
    total_ret = total_return(equity_curve)
    days = (equity_curve.index[-1] - equity_curve.index[0]).days if len(equity_curve) >= 2 else 0
    trading_days = len(equity_curve)
    annual_ret = annualized_return(total_ret, days)
    mdd = max_drawdown(equity_curve)

    # Alpha / Beta
    if benchmark_returns is not None and not benchmark_returns.empty:
        alpha_val, beta_val = alpha_beta(daily_returns, benchmark_returns)
    else:
        alpha_val, beta_val = 0.0, 0.0

    # 效率指标
    sharpe = sharpe_ratio(daily_returns)
    calmar = calmar_ratio(annual_ret, mdd)
    sortino = sortino_ratio(daily_returns)
    vol = annual_volatility(daily_returns)

    # 回撤修复
    recovery = max_drawdown_recovery_days(equity_curve)
    recovery_str = f"{recovery} 交易日" if recovery >= 0 else "未恢复"

    # 交易统计
    wr = win_rate(trades)
    plr = profit_loss_ratio(trades)
    exp = expectancy(trades)
    freq = trade_frequency(trades, trading_days)
    avg_hold = avg_holding_period(trades)
    max_loss_streak = max_consecutive_losses(trades)
    max_win_streak = max_consecutive_wins(trades)

    # 辅助
    def fp(v: float) -> str:
        return f"{v:.2%}"

    def ff(v: float, d: int = 2) -> str:
        return "∞" if v == float("inf") else f"{v:.{d}f}"

    date_start = equity_curve.index[0].strftime("%Y-%m-%d")
    date_end = equity_curve.index[-1].strftime("%Y-%m-%d")

    lines = [
        f"📅 {date_start} ~ {date_end}（{trading_days} 交易日）",
        "",
        "### 收益指标 (Returns)",
        "",
        "| 指标 | 值 |",
        "|------|------|",
        f"| 累计收益率 (Total Return) | {fp(total_ret)} |",
        f"| 年化收益率 (CAGR) | {fp(annual_ret)} |",
    ]
    if benchmark_returns is not None:
        lines.append(f"| Alpha (年化超额) | {fp(alpha_val)} |")
        lines.append(f"| Beta (市场相关性) | {ff(beta_val)} |")

    lines += [
        "",
        "### 风险指标 (Risk)",
        "",
        "| 指标 | 值 |",
        "|------|------|",
        f"| 最大回撤 (Max Drawdown) | {fp(mdd)} |",
        f"| 回撤修复期 (Recovery) | {recovery_str} |",
        f"| 年化波动率 (Volatility) | {fp(vol)} |",
        "",
        "### 效率指标 (Efficiency)",
        "",
        "| 指标 | 值 |",
        "|------|------|",
        f"| 夏普比率 (Sharpe) | {ff(sharpe)} |",
        f"| 卡玛比率 (Calmar) | {ff(calmar)} |",
        f"| 索提诺比率 (Sortino) | {ff(sortino)} |",
        "",
        "### 交易统计 (Trade Stats)",
        "",
        "| 指标 | 值 |",
        "|------|------|",
        f"| 交易次数 (Total Trades) | {len(trades)} |",
        f"| 胜率 (Win Rate) | {fp(wr)} |",
        f"| 盈亏比 (P/L Ratio) | {ff(plr)} |",
        f"| 期望值 (Expectancy) | {ff(exp)} |",
        f"| 交易频率 (每N日一笔) | {ff(freq, 1)} |",
        f"| 平均持仓 (Avg Hold Days) | {ff(avg_hold, 1)} |",
        f"| 最大连续亏损 (Max Loss) | {max_loss_streak} |",
        f"| 最大连续盈利 (Max Win) | {max_win_streak} |",
    ]

    return "\n".join(lines)


def format_monthly_table(daily_returns: pd.Series) -> str:
    """
    将月度收益矩阵格式化为 Markdown 表格字符串

    Returns:
        Markdown 格式的月度收益表
    """
    table = monthly_returns_table(daily_returns)
    if table.empty:
        return ""

    # 表头
    headers = ["年份"] + list(table.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["------"] * len(headers)) + " |",
    ]

    # 数据行
    for year, row in table.iterrows():
        cells = [str(year)]
        for val in row:
            cells.append(f"{val:.1%}" if not (val != val) else "—")
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)
