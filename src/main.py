"""
ETF 量化交易系统 - 入口脚本

从配置文件加载参数，组装各模块组件，运行回测并输出专业报告。
"""

import argparse
from datetime import datetime

from src.config import load_config, create_strategy
from src.data.loader import DataLoader
from src.backtest.engine import BacktestEngine
from src.risk.risk_manager import RiskManager
from src.risk.position_sizer import PositionSizer, SizingMethod
from src.backtest.metrics import format_report, format_monthly_table, total_return
from src.utils.plotting import plot_dashboard
from src.utils.reporter import ReportWriter


def main():
    # ===== 解析命令行参数 =====
    parser = argparse.ArgumentParser(description="ETF 量化回测系统")
    parser.add_argument(
        "--config", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    args = parser.parse_args()

    # ===== 加载配置 =====
    cfg = load_config(args.config)
    data_cfg = cfg["data"]
    risk_cfg = cfg["risk"]
    sizer_cfg = cfg["position_sizer"]
    engine_cfg = cfg["engine"]
    output_cfg = cfg["output"]

    symbol = data_cfg["symbol"]
    start_date = data_cfg["start_date"]
    end_date = data_cfg.get("end_date") or datetime.now().strftime("%Y%m%d")

    # ===== 1. 数据加载 =====
    loader = DataLoader(storage_dir=data_cfg.get("storage_dir", "data"))
    df = loader.load(symbol, start_date, end_date)
    if df.empty:
        print("数据加载失败，退出")
        return

    print(f"加载数据: {len(df)} 条 ({df.index[0].date()} ~ {df.index[-1].date()})")

    # ===== 2. 创建策略 =====
    strategy = create_strategy(cfg["strategy"])

    # ===== 3. 创建风控组件 =====
    risk_manager = RiskManager(
        stop_loss=risk_cfg["stop_loss"],
        take_profit=risk_cfg["take_profit"],
        max_position=risk_cfg["max_position"],
    )

    sizing_method = SizingMethod(sizer_cfg["method"])
    position_sizer = PositionSizer(
        method=sizing_method,
        risk_fraction=sizer_cfg.get("risk_fraction", 0.02),
    )

    # ===== 4. 创建回测引擎 =====
    engine = BacktestEngine(
        strategy=strategy,
        risk_manager=risk_manager,
        position_sizer=position_sizer,
        initial_capital=engine_cfg["initial_capital"],
        slippage=engine_cfg["slippage"],
        commission_rate=engine_cfg["commission_rate"],
    )

    # ===== 5. 运行回测 =====
    print(f"\n运行回测: {strategy.name}")
    result = engine.run(df)

    # ===== 6. 生成报告字符串 =====
    save_dir = output_cfg.get("save_dir", "results")
    report_md = format_report(
        equity_curve=result.equity_curve,
        daily_returns=result.daily_returns,
        trades=result.trades,
        benchmark_returns=result.benchmark_returns,
        symbol=symbol,
        strategy_name=result.strategy_name,
    )
    monthly_md = format_monthly_table(result.daily_returns)

    # ===== 7. 计算基准收益率 =====
    benchmark_total_ret = None
    if not result.benchmark_curve.empty:
        benchmark_total_ret = total_return(result.benchmark_curve)

    # ===== 8. 写入 Markdown 报告（增量追加） =====
    writer = ReportWriter(symbol=symbol, save_dir=save_dir)
    writer.write_report(
        report_md=report_md,
        monthly_table_md=monthly_md,
        strategy_name=result.strategy_name,
        total_ret=total_return(result.equity_curve),
        benchmark_total_ret=benchmark_total_ret,
    )

    # ===== 9. 综合仪表板（带时间戳命名） =====
    benchmark = (
        result.benchmark_curve * result.initial_capital / result.benchmark_curve.iloc[0]
        if not result.benchmark_curve.empty
        else None
    )
    plot_dashboard(
        equity_curve=result.equity_curve,
        daily_returns=result.daily_returns,
        benchmark_curve=benchmark,
        symbol=symbol,
        strategy_name=result.strategy_name,
        save_dir=save_dir,
    )

    print(f"\n共完成 {len(result.trades)} 笔交易")
    print(f"最终权益: ¥{result.final_equity:,.2f}")


if __name__ == "__main__":
    main()
