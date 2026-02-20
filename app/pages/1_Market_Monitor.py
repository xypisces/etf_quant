import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.data_loader import get_recent_market_data, calculate_period_return

st.set_page_config(page_title="行情看板", page_icon="📊", layout="wide")

st.title("ETF 行情监控看板")

# Predefined list of popular ETFs for demonstration
DEFAULT_ETFS = {
    "159915": "创业板ETF", 
    "510300": "沪深300ETF", 
    "510500": "中证500ETF", 
    "512100": "中证1000ETF",
    "512880": "证券ETF",
    "512000": "券商ETF"
}

st.sidebar.header("参数配置")
selected_symbols = st.sidebar.multiselect(
    "选择要对比的ETF",
    options=list(DEFAULT_ETFS.keys()),
    default=["510300", "510500", "159915"],
    format_func=lambda x: f"{x} - {DEFAULT_ETFS[x]}"
)

period_options = {"近1周": 7, "近1个月": 30, "近3个月": 90, "近半年": 180, "近1年": 365}
selected_period = st.sidebar.selectbox("选择时间范围", options=list(period_options.keys()), index=1)
days = period_options[selected_period]

st.markdown(f"### 📈 涨跌幅排行 ({selected_period})")

if not selected_symbols:
    st.info("请至少选择一个 ETF 进行对比。")
else:
    # 1. 涨跌幅排行榜表格展示
    returns_data = []
    historical_data = {}
    
    with st.spinner("正在获取行情数据..."):
        for sym in selected_symbols:
            df = get_recent_market_data(sym, period_days=days)
            if not df.empty:
                historical_data[sym] = df
                period_return = calculate_period_return(df)
                returns_data.append({
                    "代码": sym,
                    "名称": DEFAULT_ETFS.get(sym, "未知"),
                    "区间收益率(%)": round(period_return, 2),
                    "最新收盘价": df.iloc[-1]['收盘']
                })
    
    if returns_data:
        returns_df = pd.DataFrame(returns_data).sort_values(by="区间收益率(%)", ascending=False)
        # Use Streamlit's native dataframe displaying with coloring
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
            name = DEFAULT_ETFS.get(sym, sym)
            # Normalize to 1.0 based on the first available closing price in the period
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
        
        st.plotly_chart(fig)
    else:
        st.warning("未能获取到所选 ETF 的有效数据。")
