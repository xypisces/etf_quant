"""
ETF 量化交易系统 - 入口脚本

组装各模块组件，运行回测并输出专业报告。
"""

from datetime import datetime

from src.data.loader import DataLoader
from src.strategy.ma_cross import MACrossStrategy
from src.backtest.engine import BacktestEngine
from src.risk.risk_manager import RiskManager
from src.risk.position_sizer import PositionSizer, SizingMethod
from src.backtest.metrics import print_report, monthly_returns_table
from src.utils.plotting import plot_dashboard


def main():
    # ===== 参数配置 =====
    symbol = "601318"                    # 招商银行
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
    strategy = MACrossStrategy(short_window=5, long_window=20) # 5日均线和20日均线的交叉策略

    # ===== 3. 创建风控组件 =====
    risk_manager = RiskManager(
        stop_loss=-0.05, # 止损
        take_profit=0.10, # 止盈
        max_position=1, # 最大持仓
    )

    position_sizer = PositionSizer(
        method=SizingMethod.FIXED_FRACTION,
        risk_fraction=0.95,
    )

    # ===== 4. 创建回测引擎 =====
    engine = BacktestEngine(
        strategy=strategy,
        risk_manager=risk_manager,
        position_sizer=position_sizer,
        initial_capital=100_000.0, # 初始资金
        slippage=0.0001, # 滑点
        commission_rate=0.0003, # 手续费
    )

    # ===== 5. 运行回测 =====
    print(f"\n运行回测: {strategy.name}")
    result = engine.run(df)

    # ===== 6. 五维度专业报告 =====
    print_report(
        equity_curve=result.equity_curve, # 资金曲线
        daily_returns=result.daily_returns, # 日收益率
        trades=result.trades, # 交易记录
        benchmark_returns=result.benchmark_returns, # 基准收益率
        symbol=symbol, # 标的代码
    )

    # ===== 7. 月度收益表 =====
    table = monthly_returns_table(result.daily_returns)
    if not table.empty:
        print("\n📅 月度收益矩阵:")
        print(table.map(lambda x: f"{x:.1%}" if not (x != x) else "—").to_string())

    # ===== 8. 综合仪表板（三图合一） =====
    benchmark = result.benchmark_curve * result.initial_capital / result.benchmark_curve.iloc[0] if not result.benchmark_curve.empty else None
    plot_dashboard(
        equity_curve=result.equity_curve, # 资金曲线
        daily_returns=result.daily_returns, # 日收益率
        benchmark_curve=benchmark, # 基准收益率
        symbol=symbol, # 标的代码
        save_dir="results", # 保存目录
    )

    print(f"\n共完成 {len(result.trades)} 笔交易")
    print(f"最终权益: ¥{result.final_equity:,.2f}")


if __name__ == "__main__":
    main()
