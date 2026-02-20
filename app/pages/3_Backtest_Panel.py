import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import STRATEGY_REGISTRY, create_strategy
from src.backtest.engine import BacktestEngine
from components.data_loader import get_recent_market_data

st.set_page_config(page_title="策略回测", page_icon="📈", layout="wide")

st.title("交互式策略回测面板")

# --- Sidebar Configuration ---
st.sidebar.header("回测配置")

# 1. Symbol Selection (simplified)
symbol = st.sidebar.text_input("交易品种代码 (如: 510300)", value="510300")
backtest_days = st.sidebar.select_slider("数据时间范围 (天)", options=[30, 90, 180, 365, 730], value=365)

st.sidebar.markdown("---")

# 2. Strategy Selection
strategy_name = st.sidebar.selectbox("选择策略", options=list(STRATEGY_REGISTRY.keys()))

# 3. Dynamic Strategy Parameters Form
st.sidebar.subheader("策略参数")
params = {}
with st.sidebar.form(key="strategy_params_form"):
    if strategy_name == "ma_cross":
        params["short_window"] = st.number_input("短期均线窗口", min_value=1, max_value=250, value=10)
        params["long_window"] = st.number_input("长期均线窗口", min_value=1, max_value=250, value=30)
    elif strategy_name == "ema20_pullback":
        params["ema_period"] = st.number_input("EMA 周期", min_value=1, value=20)
    elif strategy_name == "turtle":
        params["entry_window"] = st.number_input("入场通道 (天)", min_value=10, value=20)
        params["exit_window"] = st.number_input("出场通道 (天)", min_value=5, value=10)
    elif strategy_name == "grid":
        params["grid_num"] = st.number_input("网格数量", min_value=2, value=10)
        params["grid_size"] = st.number_input("网格间距 (%)", min_value=0.1, value=1.0, format="%.2f") / 100.0
    elif strategy_name == "momentum":
        params["lookback"] = st.number_input("动量回溯期", min_value=5, value=20)
    elif strategy_name == "mean_reversion":
        params["window"] = st.number_input("回归窗口", min_value=5, value=20)
        params["z_score_threshold"] = st.number_input("Z-Score 阈值", min_value=0.5, value=2.0)
    
    submit_button = st.form_submit_button(label="🚀 运行回测")

# --- Main Area Execution ---

if submit_button:
    if not symbol:
        st.error("请输入有效的交易品种代码。")
    else:
        with st.spinner("正在加载数据并运行回测..."):
            # 1. Fetch Data
            df = get_recent_market_data(symbol, period_days=backtest_days)
            
            if df.empty:
                st.error(f"无法获取 {symbol} 的行情数据，请检查代码或网络连接。")
            else:
                # 2. Initialize Engine & Strategy
                try:
                    strategy = create_strategy({"name": strategy_name, "params": params})
                    engine = BacktestEngine(
                        strategy=strategy,
                        initial_capital=100000.0,
                        commission_rate=0.0003
                    )
                    
                    # 3. Run Backtest
                    result = engine.run(df)
                    st.success("回测执行完成！")
                    
                    # --- Presentation ---
                    
                    # Store result in session state to persist it during other interactions
                    st.session_state['latest_result'] = result
                    st.session_state['latest_data'] = df
                    st.session_state['run_info'] = f"{symbol} | {strategy.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                except Exception as e:
                    st.error(f"回测运行出错: {e}")

# Display the latest result if it exists in session state
if 'latest_result' in st.session_state:
    result = st.session_state['latest_result']
    df = st.session_state['latest_data']
    
    st.markdown(f"### 📊 回测报告: `{st.session_state['run_info']}`")
    
    # KPIs Layout
    from src.backtest.metrics import total_return, annualized_return, max_drawdown, sharpe_ratio
    
    eq_curve = result.equity_curve
    days = (eq_curve.index[-1] - eq_curve.index[0]).days if len(eq_curve) > 1 else 1
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最终净值", f"¥{result.final_equity:,.2f}")
    
    tr = total_return(eq_curve)
    col2.metric("累计收益率", f"{tr:.2%}")
    
    mdd = max_drawdown(eq_curve)
    col3.metric("最大回撤", f"{mdd:.2%}")
    
    sharpe = sharpe_ratio(result.daily_returns)
    col4.metric("夏普比率", f"{sharpe:.2f}")
    
    st.markdown("---")
    
    # Main Plot (Equity Curve + Trades)
    st.markdown("### 📈 净值曲线与交易标记")
    
    fig = go.Figure()
    
    # Equity curve
    fig.add_trace(go.Scatter(x=eq_curve.index, y=eq_curve.values, mode='lines', name='策略净值', line=dict(color='blue')))
    
    # If we have a benchmark
    if not result.benchmark_curve.empty:
        # Rebase benchmark to initial capital
        bench_rebased = (result.benchmark_curve / result.benchmark_curve.iloc[0]) * result.initial_capital
        fig.add_trace(go.Scatter(x=bench_rebased.index, y=bench_rebased.values, mode='lines', name='基准净值 (持股)', line=dict(color='gray', dash='dash')))
        
    trades_df = pd.DataFrame(result.trades)
    if not trades_df.empty:
        # Mark entries (Buy) and exits (Sell)
        # Note: Depending on engine logic, we might only have "round turn" trades recorded in result.trades
        # For a more detailed plot, we use date_open for entry and date_close for exit
        
        # Prepare entry points (green triangles)
        entries = trades_df.copy()
        entries['date'] = pd.to_datetime(entries['date_open'])
        entries = entries.dropna(subset=['date']).set_index('date')
        
        # We need to map the Y coordinate to the equity curve at that date (or price)
        # We'll plot on secondary Y axis if we want price, but for simplicity we'll just plot price 
        # below or create a subplots. Let's create a combined chart with Price on Y1 and Equity on Y2
        
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Price
        fig.add_trace(go.Scatter(x=df.index, y=df['收盘'], mode='lines', name='价格', line=dict(color='lightgray')), secondary_y=False)
        
        # Equity
        fig.add_trace(go.Scatter(x=eq_curve.index, y=eq_curve.values, mode='lines', name='策略净值', line=dict(color='blue')), secondary_y=True)
        
        # Entries
        for _, row in trades_df.iterrows():
            # Buy marker
            dt_open = pd.to_datetime(row['date_open'])
            if dt_open in df.index:
                price = row['entry_price']
                fig.add_trace(go.Scatter(x=[dt_open], y=[price], mode='markers', marker=dict(symbol='triangle-up', color='green', size=10), name='Buy', showlegend=False), secondary_y=False)
            
            # Sell marker
            dt_close = pd.to_datetime(row['date_close'])
            if dt_close in df.index:
                price = row['exit_price']
                color = 'green' if row['pnl'] > 0 else 'red'
                fig.add_trace(go.Scatter(x=[dt_close], y=[price], mode='markers', marker=dict(symbol='triangle-down', color=color, size=10), name='Sell/Close', showlegend=False), secondary_y=False)

    fig.update_layout(height=500, title="策略执行明细", hovermode="x unified")
    st.plotly_chart(fig)
    
    # Detailed text report
    st.markdown("### 📑 详细指标与统计")
    from src.backtest.metrics import format_report
    detailed_report = format_report(
        equity_curve=result.equity_curve,
        daily_returns=result.daily_returns,
        trades=result.trades,
        benchmark_returns=result.benchmark_returns
    )
    # format_report returns markdown, we can render it directly
    st.markdown(detailed_report)
    
else:
    st.info("👈 请在左侧配置参数并点击「运行回测」开始计算。")
