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
from src.backtest.metrics import format_report, format_monthly_table, total_return
from src.utils.plotting import plot_dashboard
from src.utils.reporter import ReportWriter


def main():
    # ===== 参数配置 =====
    symbol = "600111"
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

    # ===== 6. 生成报告字符串 =====
    report_md = format_report(
        equity_curve=result.equity_curve, # 权益曲线
        daily_returns=result.daily_returns, # 日收益率
        trades=result.trades, # 交易记录
        benchmark_returns=result.benchmark_returns, # 基准收益率
        symbol=symbol, # 标的代码
        strategy_name=result.strategy_name, # 策略名称
    )
    monthly_md = format_monthly_table(result.daily_returns)

    # ===== 7. 计算基准收益率 =====
    benchmark_total_ret = None
    if not result.benchmark_curve.empty:
        benchmark_total_ret = total_return(result.benchmark_curve)

    # ===== 8. 写入 Markdown 报告（增量追加） =====
    writer = ReportWriter(symbol=symbol, save_dir="results")
    writer.write_report(
        report_md=report_md,    # 回测报告
        monthly_table_md=monthly_md, # 月度收益表
        strategy_name=result.strategy_name, # 策略名称
        total_ret=total_return(result.equity_curve), # 累计收益率
        benchmark_total_ret=benchmark_total_ret, # 基准累计收益率
    )

    # ===== 9. 综合仪表板（带时间戳命名） =====
    benchmark = result.benchmark_curve * result.initial_capital / result.benchmark_curve.iloc[0] if not result.benchmark_curve.empty else None
    plot_dashboard(
        equity_curve=result.equity_curve, # 权益曲线
        daily_returns=result.daily_returns, # 日收益率
        benchmark_curve=benchmark, # 基准收益率
        symbol=symbol, # 标的代码
        strategy_name=result.strategy_name, # 策略名称
        save_dir="results", # 保存路径
    )

    print(f"\n共完成 {len(result.trades)} 笔交易")
    print(f"最终权益: ¥{result.final_equity:,.2f}")


if __name__ == "__main__":
    main()
