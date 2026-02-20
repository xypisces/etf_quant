import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.data.etf_catalog import ETFCatalog
from components.data_loader import get_recent_market_data, calculate_period_return

st.set_page_config(page_title="行情看板", page_icon="📊", layout="wide")

st.title("ETF 行情监控看板")

# --- Load full ETF catalog ---
catalog = ETFCatalog(storage_dir="data")

try:
    etf_list_df = catalog.load()
except Exception as e:
    st.error(f"无法加载 ETF 列表: {e}。请先去「轮动池管理」页面点击「刷新 ETF 列表」。")
    st.stop()

# Build options sorted by market cap (already sorted from catalog)
etf_options = {
    row["code"]: f"{row['code']} - {row['name']}"
    for _, row in etf_list_df.iterrows()
}

st.sidebar.header("参数配置")
selected_symbols = st.sidebar.multiselect(
    "选择要对比的 ETF（按市值排序）",
    options=list(etf_options.keys()),
    default=[],
    format_func=lambda x: etf_options.get(x, x),
    help="从全量 A 股 ETF 列表中选择，下拉列表已按市值从大到小排序"
)

period_options = {"近1周": 7, "近1个月": 30, "近3个月": 90, "近半年": 180, "近1年": 365}
selected_period = st.sidebar.selectbox("选择时间范围", options=list(period_options.keys()), index=1)
days = period_options[selected_period]

st.markdown(f"### 📈 涨跌幅排行 ({selected_period})")

if not selected_symbols:
    st.info("👈 请在左侧从全量 ETF 列表中选择要对比的品种。")
else:
    returns_data = []
    historical_data = {}

    with st.spinner("正在获取行情数据..."):
        for sym in selected_symbols:
            df = get_recent_market_data(sym, period_days=days)
            if not df.empty:
                historical_data[sym] = df
                period_return = calculate_period_return(df)
                name = etf_options.get(sym, sym).split(" - ")[-1]
                returns_data.append({
                    "代码": sym,
                    "名称": name,
                    "区间收益率(%)": round(period_return, 2),
                    "最新收盘价": df.iloc[-1]['收盘']
                })

    if returns_data:
        returns_df = pd.DataFrame(returns_data).sort_values(by="区间收益率(%)", ascending=False)
        st.dataframe(
            returns_df.style.map(
                lambda val: f'color: {"red" if val > 0 else "green" if val < 0 else "black"}',
                subset=['区间收益率(%)']
            ),
            use_container_width=True,
            hide_index=True
        )

        # 2. 交互式走势叠加对比
        st.markdown("### 🎢 归一化走势对比")

        fig = go.Figure()

        for sym, df in historical_data.items():
            name = etf_options.get(sym, sym).split(" - ")[-1]
            base_price = df.iloc[0]['收盘']
            normalized_close = df['收盘'] / base_price

            fig.add_trace(go.Scatter(
                x=df.index,
                y=normalized_close,
                mode='lines',
                name=name
            ))

        fig.update_layout(
            title="相对净值曲线 (基准 = 1.0)",
            xaxis_title="日期",
            yaxis_title="归一化净值",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("未能获取到所选 ETF 的有效数据。")
