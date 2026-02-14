"""
ETF 量化交易系统 - 入口脚本

组装各模块组件，运行回测并输出结果。
"""

from datetime import datetime

from src.data.loader import DataLoader
from src.strategy.ma_cross import MACrossStrategy
from src.backtest.engine import BacktestEngine
from src.risk.risk_manager import RiskManager
from src.risk.position_sizer import PositionSizer, SizingMethod
from src.backtest.metrics import print_report
from src.utils.plotting import plot_equity_curve


def main():
    # ===== 参数配置 =====
    symbol = "510300"                    # 沪深300 ETF
    start_date = "20200101"
    end_date = datetime.now().strftime("%Y%m%d")

    # ===== 1. 数据加载 =====
    loader = DataLoader(cache_dir="csv")
    df = loader.load(symbol, start_date, end_date)
    if df.empty:
        print("数据加载失败，退出")
        return

    print(f"加载数据: {len(df)} 条 ({df.index[0].date()} ~ {df.index[-1].date()})")

    # ===== 2. 创建策略 =====
    strategy = MACrossStrategy(short_window=5, long_window=20)

    # ===== 3. 创建风控组件 =====
    risk_manager = RiskManager(
        stop_loss=-0.05,       # 止损 -5%
        take_profit=0.10,      # 止盈 +10%
        max_position=1,        # 单品种最大持仓 1
    )

    position_sizer = PositionSizer(
        method=SizingMethod.FIXED_FRACTION,
        risk_fraction=0.95,     # 使用 95% 资金
    )

    # ===== 4. 创建回测引擎 =====
    engine = BacktestEngine(
        strategy=strategy,
        risk_manager=risk_manager,
        position_sizer=position_sizer,
        initial_capital=100_000.0,
        slippage=0.0001,        # 滑点 0.01%
        commission_rate=0.0003, # 手续费 0.03%
    )

    # ===== 5. 运行回测 =====
    print(f"\n运行回测: {strategy.name}")
    result = engine.run(df)

    # ===== 6. 输出结果 =====
    print_report(
        equity_curve=result.equity_curve,
        daily_returns=result.daily_returns,
        trades=result.trades,
        symbol=symbol,
    )

    # ===== 7. 绘图 =====
    # 构建基准净值（买入并持有）
    benchmark = df["close"] / df["close"].iloc[0] * result.initial_capital
    plot_equity_curve(
        equity_curve=result.equity_curve,
        benchmark_curve=benchmark,
        symbol=symbol,
        save_dir="results",
    )

    print(f"\n共完成 {len(result.trades)} 笔交易")
    print(f"最终权益: ¥{result.final_equity:,.2f}")


if __name__ == "__main__":
    main()
