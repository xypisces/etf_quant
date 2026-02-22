import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import STRATEGY_REGISTRY, create_strategy
from src.backtest.engine import BacktestEngine
from src.risk.position_sizer import PositionSizer
from src.backtest.metrics import (
    format_report,
    format_monthly_table,
    total_return,
    annualized_return,
    max_drawdown,
    sharpe_ratio,
)
from src.utils.reporter import ReportWriter
from src.data.etf_catalog import ETFCatalog
from components.data_loader import get_recent_market_data

st.set_page_config(page_title="策略回测", page_icon="📈", layout="wide")

st.title("交互式策略回测面板")

# ── 辅助函数 ──────────────────────────────────────────────


@st.cache_data(ttl=3600 * 24)
def _load_etf_name_map() -> dict[str, str]:
    """加载 ETF code → 中文名 映射表（缓存 24h）"""
    catalog = ETFCatalog()
    try:
        df = catalog.load(force_refresh=False)
        return dict(zip(df["code"], df["name"]))
    except Exception:
        return {}


def _get_etf_name(symbol: str, name_map: dict[str, str]) -> str:
    return name_map.get(symbol, "")


# 策略中文名映射
STRATEGY_LABELS: dict[str, str] = {
    "ma_cross": "双均线交叉",
    "ema20_pullback": "EMA20 回踩",
    "turtle": "海龟策略",
    "grid": "网格交易",
    "momentum": "动量轮动",
    "mean_reversion": "均值回归",
}

# ── 侧边栏配置 ─────────────────────────────────────────────

name_map = _load_etf_name_map()

st.sidebar.header("回测配置")

# 1. 品种选择
symbol = st.sidebar.text_input("交易品种代码 (如: 510300)", value="510300")

# 显示中文名
etf_name = _get_etf_name(symbol, name_map)
if etf_name:
    st.sidebar.markdown(f"**{symbol}** — {etf_name}")
else:
    if symbol:
        st.sidebar.caption(f"⚠️ 未找到 {symbol} 的中文名称")

backtest_days = st.sidebar.select_slider(
    "数据时间范围 (天)", options=[30, 90, 180, 365, 730], value=365
)

st.sidebar.markdown("---")

# 2. 多策略选择
strategy_options = list(STRATEGY_REGISTRY.keys())
display_labels = [f"{STRATEGY_LABELS.get(k, k)} ({k})" for k in strategy_options]
label_to_key = dict(zip(display_labels, strategy_options))

selected_labels = st.sidebar.multiselect(
    "选择策略（可多选）",
    options=display_labels,
    default=[display_labels[0]],
)
selected_strategies = [label_to_key[lb] for lb in selected_labels]

# 3. 引擎参数
st.sidebar.markdown("---")
st.sidebar.subheader("引擎参数")
initial_capital = st.sidebar.number_input(
    "初始资金 (¥)", min_value=10000, value=100000, step=10000
)
commission_rate = st.sidebar.number_input(
    "手续费率", min_value=0.0, value=0.0003, step=0.0001, format="%.4f"
)

# 4. 运行按钮
run_clicked = st.sidebar.button("🚀 运行回测", use_container_width=True)

# ── 主区域 ─────────────────────────────────────────────────

if run_clicked:
    if not symbol:
        st.error("请输入有效的交易品种代码。")
    elif not selected_strategies:
        st.error("请至少选择一个策略。")
    else:
        # — 加载数据 —
        with st.spinner("正在加载行情数据..."):
            df = get_recent_market_data(symbol, period_days=backtest_days)

        if df.empty:
            st.error(f"无法获取 {symbol} 的行情数据，请检查代码或网络连接。")
        else:
            # 显示标题（含中文名）
            title_suffix = f" ({etf_name})" if etf_name else ""
            st.success(
                f"数据加载完成：{symbol}{title_suffix}  |  "
                f"{len(df)} 根 K 线  |  "
                f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}"
            )

            # — 循环回测所有策略 —
            all_results: list[dict] = []
            progress = st.progress(0, text="回测进行中...")

            for i, sname in enumerate(selected_strategies):
                progress.progress(
                    (i + 1) / len(selected_strategies),
                    text=f"正在回测: {STRATEGY_LABELS.get(sname, sname)}...",
                )
                try:
                    strategy = create_strategy({"name": sname, "params": {}})
                    engine = BacktestEngine(
                        strategy=strategy,
                        position_sizer=PositionSizer(risk_fraction=0.95),
                        initial_capital=initial_capital,
                        commission_rate=commission_rate,
                    )
                    result = engine.run(df)
                    all_results.append({
                        "name": sname,
                        "display_name": STRATEGY_LABELS.get(sname, sname),
                        "strategy_name": result.strategy_name,
                        "result": result,
                    })
                except Exception as e:
                    st.warning(f"策略 {sname} 回测失败: {e}")

            progress.empty()

            if not all_results:
                st.error("所有策略回测均失败。")
            else:
                # 存入 session_state
                st.session_state["backtest_results"] = all_results
                st.session_state["backtest_df"] = df
                st.session_state["backtest_symbol"] = symbol
                st.session_state["backtest_etf_name"] = etf_name

                # — 写入报告 —
                with st.spinner("正在写入报告..."):
                    writer = ReportWriter(symbol=symbol, save_dir="results")
                    for item in all_results:
                        r = item["result"]
                        report_md = format_report(
                            equity_curve=r.equity_curve,
                            daily_returns=r.daily_returns,
                            trades=r.trades,
                            benchmark_returns=r.benchmark_returns,
                            symbol=symbol,
                            strategy_name=r.strategy_name,
                        )
                        monthly_md = format_monthly_table(r.daily_returns)

                        benchmark_ret = None
                        if not r.benchmark_curve.empty:
                            benchmark_ret = total_return(r.benchmark_curve)

                        writer.write_report(
                            report_md=report_md,
                            monthly_table_md=monthly_md,
                            strategy_name=r.strategy_name,
                            total_ret=total_return(r.equity_curve),
                            benchmark_total_ret=benchmark_ret,
                        )

                st.toast(
                    f"📝 报告已写入 results/{symbol}/report.md",
                    icon="✅",
                )


# ── 结果展示 ────────────────────────────────────────────────

if "backtest_results" in st.session_state:
    all_results = st.session_state["backtest_results"]
    df = st.session_state["backtest_df"]
    symbol = st.session_state["backtest_symbol"]
    etf_name = st.session_state["backtest_etf_name"]

    title_suffix = f" ({etf_name})" if etf_name else ""
    st.markdown(f"## 📊 回测报告: {symbol}{title_suffix}")

    # ── KPI 对比表 ──
    st.markdown("### 🏆 策略对比")
    kpi_rows = []
    for item in all_results:
        r = item["result"]
        eq = r.equity_curve
        tr = total_return(eq)
        days = (eq.index[-1] - eq.index[0]).days if len(eq) > 1 else 1
        kpi_rows.append({
            "策略": item["strategy_name"],
            "最终净值": f"¥{r.final_equity:,.2f}",
            "累计收益率": f"{tr:.2%}",
            "年化收益率": f"{annualized_return(tr, days):.2%}",
            "最大回撤": f"{max_drawdown(eq):.2%}",
            "夏普比率": f"{sharpe_ratio(r.daily_returns):.2f}",
            "交易次数": len(r.trades),
        })

    kpi_df = pd.DataFrame(kpi_rows)
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)

    # ── 叠加净值曲线 ──
    st.markdown("### 📈 净值曲线对比")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 价格线
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["收盘"],
            mode="lines",
            name="价格",
            line=dict(color="rgba(180,180,180,0.5)", width=1),
        ),
        secondary_y=False,
    )

    # 各策略净值
    colors = [
        "#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800", "#00BCD4",
    ]
    for idx, item in enumerate(all_results):
        r = item["result"]
        color = colors[idx % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=r.equity_curve.index,
                y=r.equity_curve.values,
                mode="lines",
                name=item["strategy_name"],
                line=dict(color=color, width=2),
            ),
            secondary_y=True,
        )

    # 基准净值（取第一个结果的 benchmark）
    first_r = all_results[0]["result"]
    if not first_r.benchmark_curve.empty:
        bench_rebased = (
            first_r.benchmark_curve
            / first_r.benchmark_curve.iloc[0]
            * first_r.initial_capital
        )
        fig.add_trace(
            go.Scatter(
                x=bench_rebased.index,
                y=bench_rebased.values,
                mode="lines",
                name="基准 (买入持有)",
                line=dict(color="gray", dash="dash", width=1.5),
            ),
            secondary_y=True,
        )

    fig.update_layout(
        height=550,
        title="策略净值 vs 价格走势",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_yaxes(title_text="价格", secondary_y=False)
    fig.update_yaxes(title_text="净值 (¥)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    # ── 每策略详细报告（可展开） ──
    st.markdown("### 📑 各策略详细指标")
    for item in all_results:
        r = item["result"]
        with st.expander(f"📋 {item['strategy_name']}", expanded=len(all_results) == 1):
            detailed_report = format_report(
                equity_curve=r.equity_curve,
                daily_returns=r.daily_returns,
                trades=r.trades,
                benchmark_returns=r.benchmark_returns,
            )
            st.markdown(detailed_report)

            monthly_md = format_monthly_table(r.daily_returns)
            if monthly_md:
                st.markdown("#### 月度收益矩阵")
                st.markdown(monthly_md)

else:
    st.info("👈 请在左侧配置参数并点击「运行回测」开始计算。")
