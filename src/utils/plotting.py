"""
可视化工具 - 专业回测报告图表

包含:
1. 资金曲线 (Equity Curve) — 对数坐标 + 基准对比
2. 水下回撤图 (Underwater Plot) — 回撤深度区域图
3. 月度收益热力图 (Monthly Heatmap) — 年/月盈亏百分比
4. 综合仪表板 (Dashboard) — 以上三图合一
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd

from src.backtest.metrics import drawdown_series, monthly_returns_table


def setup_chinese_font():
    """配置中文字体支持"""
    plt.rcParams["font.sans-serif"] = [
        "Arial Unicode MS",
        "SimHei",
        "PingFang SC",
        "Heiti TC",
        "sans-serif",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def _save_fig(fig: plt.Figure, save_dir: str, filename: str) -> str:
    """保存图表"""
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[Plotting] 已保存: {filepath}")
    return filepath


def plot_equity_curve(
    equity_curve: pd.Series,
    benchmark_curve: pd.Series | None = None,
    symbol: str = "",
    save_dir: str = "results",
    log_scale: bool = True,
) -> str | None:
    """
    绘制资金曲线图（对数坐标 + 基准对比）

    Args:
        equity_curve: 策略净值序列
        benchmark_curve: 基准净值序列（可选）
        symbol: 标的代码
        save_dir: 保存目录
        log_scale: 是否使用对数坐标

    Returns:
        保存路径
    """
    if equity_curve.empty:
        print("无数据可绘图")
        return None

    setup_chinese_font()

    # 归一化（从 1 开始）
    norm_equity = equity_curve / equity_curve.iloc[0]

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(
        norm_equity.index, norm_equity,
        label="策略收益 (Strategy)", linewidth=1.5, color="#2196F3",
    )

    if benchmark_curve is not None and not benchmark_curve.empty:
        norm_bench = benchmark_curve / benchmark_curve.iloc[0]
        ax.plot(
            norm_bench.index, norm_bench,
            label="基准收益 (Benchmark)", linewidth=1.2, color="#9E9E9E", alpha=0.7,
        )

    if log_scale:
        ax.set_yscale("log")
        ax.set_ylabel("累计净值 (对数坐标)")
    else:
        ax.set_ylabel("累计净值")

    ax.set_title(f"资金曲线 — {symbol}", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    return _save_fig(fig, save_dir, f"equity_{symbol}.png")


def plot_underwater(
    equity_curve: pd.Series,
    symbol: str = "",
    save_dir: str = "results",
) -> str | None:
    """
    水下回撤图 — 回撤深度区域图

    直观展示策略大部分时间是在"水下"煎熬还是在创新高
    """
    if equity_curve.empty:
        return None

    setup_chinese_font()
    dd = drawdown_series(equity_curve)

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.fill_between(dd.index, dd.values, 0, color="#E53935", alpha=0.5, label="回撤")
    ax.plot(dd.index, dd.values, color="#C62828", linewidth=0.5)
    ax.set_ylabel("回撤幅度")
    ax.set_title(f"水下回撤图 — {symbol}", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.grid(True, alpha=0.3)
    ax.legend()

    return _save_fig(fig, save_dir, f"underwater_{symbol}.png")


def plot_monthly_heatmap(
    daily_returns: pd.Series,
    symbol: str = "",
    save_dir: str = "results",
) -> str | None:
    """
    月度/年度收益热力图

    行=年，列=月，颜色表示盈亏
    """
    if daily_returns.empty:
        return None

    setup_chinese_font()
    table = monthly_returns_table(daily_returns)
    if table.empty:
        return None

    fig, ax = plt.subplots(figsize=(16, max(3, len(table) * 0.6 + 1)))

    # 构建颜色映射：红=亏损，绿=盈利
    max_abs = max(abs(table.values[~np.isnan(table.values)].min()),
                  abs(table.values[~np.isnan(table.values)].max()),
                  0.01)
    norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)
    cmap = plt.cm.RdYlGn  # 红-黄-绿

    im = ax.imshow(table.values, cmap=cmap, norm=norm, aspect="auto")

    # 坐标标签
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels(table.columns, fontsize=10)
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels(table.index, fontsize=10)

    # 在每个单元格中标注百分比
    for i in range(len(table.index)):
        for j in range(len(table.columns)):
            val = table.values[i, j]
            if np.isnan(val):
                continue
            text_color = "white" if abs(val) > max_abs * 0.6 else "black"
            ax.text(j, i, f"{val:.1%}", ha="center", va="center",
                    fontsize=9, color=text_color, fontweight="bold")

    ax.set_title(f"月度收益热力图 — {symbol}", fontsize=14, fontweight="bold", pad=12)
    fig.colorbar(im, ax=ax, format=plt.FuncFormatter(lambda x, _: f"{x:.0%}"),
                 shrink=0.8, label="月收益率")

    return _save_fig(fig, save_dir, f"heatmap_{symbol}.png")


def plot_dashboard(
    equity_curve: pd.Series,
    daily_returns: pd.Series,
    benchmark_curve: pd.Series | None = None,
    symbol: str = "",
    strategy_name: str = "",
    save_dir: str = "results",
) -> str | None:
    """
    综合仪表板 — 三图合一（资金曲线 + 水下回撤 + 月度热力图）

    图片保存到 results/<symbol>/ 目录，文件名含时间戳
    """
    if equity_curve.empty:
        return None

    setup_chinese_font()

    # 准备数据
    norm_equity = equity_curve / equity_curve.iloc[0]
    dd = drawdown_series(equity_curve)
    table = monthly_returns_table(daily_returns)

    has_heatmap = not table.empty
    nrows = 3 if has_heatmap else 2
    height_ratios = [3, 1.5, 2] if has_heatmap else [3, 1.5]

    fig, axes = plt.subplots(
        nrows, 1, figsize=(16, 5 * nrows),
        gridspec_kw={"height_ratios": height_ratios},
    )
    title = f"回测仪表板 — {symbol}"
    if strategy_name:
        title += f" ({strategy_name})"
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.98)

    # ----- 1. 资金曲线 -----
    ax1 = axes[0]
    ax1.plot(norm_equity.index, norm_equity, label="策略", linewidth=1.5, color="#2196F3")
    if benchmark_curve is not None and not benchmark_curve.empty:
        norm_bench = benchmark_curve / benchmark_curve.iloc[0]
        ax1.plot(norm_bench.index, norm_bench, label="基准",
                 linewidth=1.2, color="#9E9E9E", alpha=0.7)
    ax1.set_yscale("log")
    ax1.set_ylabel("累计净值 (log)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.set_title("资金曲线", fontsize=12)

    # ----- 2. 水下回撤 -----
    ax2 = axes[1]
    ax2.fill_between(dd.index, dd.values, 0, color="#E53935", alpha=0.5)
    ax2.plot(dd.index, dd.values, color="#C62828", linewidth=0.5)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax2.set_ylabel("回撤幅度")
    ax2.grid(True, alpha=0.3)
    ax2.set_title("水下回撤", fontsize=12)

    # ----- 3. 月度热力图 -----
    if has_heatmap:
        ax3 = axes[2]
        max_abs = max(
            abs(table.values[~np.isnan(table.values)].min()),
            abs(table.values[~np.isnan(table.values)].max()),
            0.01,
        )
        norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)
        im = ax3.imshow(table.values, cmap=plt.cm.RdYlGn, norm=norm, aspect="auto")
        ax3.set_xticks(range(len(table.columns)))
        ax3.set_xticklabels(table.columns, fontsize=9)
        ax3.set_yticks(range(len(table.index)))
        ax3.set_yticklabels(table.index, fontsize=9)
        for i in range(len(table.index)):
            for j in range(len(table.columns)):
                val = table.values[i, j]
                if np.isnan(val):
                    continue
                text_color = "white" if abs(val) > max_abs * 0.6 else "black"
                ax3.text(j, i, f"{val:.1%}", ha="center", va="center",
                         fontsize=8, color=text_color, fontweight="bold")
        ax3.set_title("月度收益热力图", fontsize=12)
        fig.colorbar(im, ax=ax3, format=plt.FuncFormatter(lambda x, _: f"{x:.0%}"),
                     shrink=0.8)

    fig.tight_layout(rect=[0, 0, 1, 0.96])

    # 保存到 results/<symbol>/ 目录，文件名含时间戳
    from datetime import datetime
    symbol_dir = os.path.join(save_dir, symbol)
    os.makedirs(symbol_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = strategy_name.replace("(", "").replace(")", "").replace(",", "_") if strategy_name else "strategy"
    filename = f"dashboard_{safe_name}_{ts}.png"
    return _save_fig(fig, symbol_dir, filename)

