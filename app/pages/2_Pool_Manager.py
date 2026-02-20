import streamlit as st
import pandas as pd
from components.data_loader import get_recent_market_data

st.set_page_config(page_title="轮动池管理", page_icon="🔄", layout="wide")

st.title("ETF 轮动池管理与动量排名")

# Simulate configuration reading for the pool
# In a real scenario, this could read from a JSON/YAML file or a database
if "etf_pool" not in st.session_state:
    st.session_state.etf_pool = {
        "510300": "沪深300ETF",
        "510500": "中证500ETF",
        "159915": "创业板ETF",
        "512100": "中证1000ETF",
        "512880": "证券ETF",
        "518880": "黄金ETF"
    }

st.sidebar.header("自选池操作")
new_symbol = st.sidebar.text_input("ETF代码 (如: 510300)")
new_name = st.sidebar.text_input("ETF名称 (如: 沪深300ETF)")

if st.sidebar.button("添加到轮动池"):
    if new_symbol and new_name:
        st.session_state.etf_pool[new_symbol] = new_name
        st.sidebar.success(f"已添加 {new_name}")
    else:
        st.sidebar.error("请同时提供代码和名称")

st.markdown("### 📋 当前自选 ETF 池配置")
# Convert session state to DataFrame for display
pool_df = pd.DataFrame(list(st.session_state.etf_pool.items()), columns=["代码", "名称"])
st.dataframe(pool_df)

st.markdown("---")
st.markdown("### 🏆 动量评分与排名")

# Momentum period parameter
momentum_days = st.slider("动量计算周期 (天)", min_value=10, max_value=250, value=20, step=5)

if st.button("🔌 计算动量排名"):
    with st.spinner(f"正在计算近 {momentum_days} 天动量评分..."):
        ranking_data = []
        for sym, name in st.session_state.etf_pool.items():
            df = get_recent_market_data(sym, period_days=momentum_days + 5) # Get a bit more data to ensure we have enough trading days
            
            if not df.empty and len(df) >= 2:
                # Simple momentum calculation: (Current Price / Price N days ago) - 1
                current_price = df.iloc[-1]['收盘']
                
                # Try to get the price from exactly momentum_days trading days ago
                past_idx = max(0, len(df) - momentum_days - 1)
                past_price = df.iloc[past_idx]['收盘']
                
                momentum_score = (current_price / past_price) - 1
                
                ranking_data.append({
                    "代码": sym,
                    "名称": name,
                    "当前价格": current_price,
                    "动量得分": round(momentum_score, 4)
                })
        
        if ranking_data:
            ranking_df = pd.DataFrame(ranking_data)
            # Sort by momentum score descending
            ranking_df = ranking_df.sort_values(by="动量得分", ascending=False).reset_index(drop=True)
            
            # Format dataframe for display
            st.dataframe(
                ranking_df.style.background_gradient(subset=['动量得分'], cmap='RdYlGn'),
                use_container_width=True
            )
            
            # Recommend the top 1 if positive
            top_etf = ranking_df.iloc[0]
            if top_etf['动量得分'] > 0:
                st.success(f"**当前最强标的推荐**: {top_etf['名称']} ({top_etf['代码']}) - 动量得分: {top_etf['动量得分']}")
            else:
                st.warning("当前所有标的动量均为负，建议空仓观望。")
        else:
            st.warning("无法计算排名，可能是由于网络或数据源问题。")
