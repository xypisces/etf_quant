"""
可视化工具 - 回测结果绘图
"""

import os
import matplotlib.pyplot as plt
import pandas as pd


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


def plot_equity_curve(
    equity_curve: pd.Series,
    benchmark_curve: pd.Series | None = None,
    symbol: str = "",
    save_dir: str = "results",
) -> str | None:
    """
    绘制策略收益 vs 基准收益对比曲线

    Args:
        equity_curve: 策略净值序列
        benchmark_curve: 基准净值序列（可选）
        symbol: 标的代码
        save_dir: 保存目录

    Returns:
        保存的文件路径，或 None
    """
    if equity_curve.empty:
        print("无数据可绘图")
        return None

    setup_chinese_font()

    # 归一化为净值曲线（从 1 开始）
    normalized_equity = equity_curve / equity_curve.iloc[0]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(normalized_equity.index, normalized_equity, label="策略收益 (Strategy)", linewidth=1.5)

    if benchmark_curve is not None and not benchmark_curve.empty:
        normalized_benchmark = benchmark_curve / benchmark_curve.iloc[0]
        ax.plot(
            normalized_benchmark.index,
            normalized_benchmark,
            label="基准收益 (Benchmark)",
            alpha=0.6,
            linewidth=1.5,
        )

    ax.set_title(f"回测结果 - {symbol}")
    ax.set_xlabel("日期 (Date)")
    ax.set_ylabel("累计净值 (Cumulative Returns)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 保存图表
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"backtest_{symbol}.png")
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[Plotting] 图表已保存至 {filename}")

    return filename
