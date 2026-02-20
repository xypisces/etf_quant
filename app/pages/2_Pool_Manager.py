import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from src.data.etf_catalog import ETFCatalog
from src.data.storage import DataStorage
from src.data.fetcher import DataFetcher

st.set_page_config(page_title="轮动池管理", page_icon="🔄", layout="wide")

st.title("ETF 全量动量排名")

# --- Initialize backend services ---
catalog = ETFCatalog(storage_dir="data")
storage = DataStorage(storage_dir="data")
fetcher = DataFetcher()

# --- Sidebar: ETF List Management ---
st.sidebar.header("ETF 列表管理")

if catalog.cache_exists:
    st.sidebar.caption(f"📅 本地缓存更新于: {catalog.cache_mtime}")
else:
    st.sidebar.warning("本地无 ETF 列表缓存，请先刷新。")

if st.sidebar.button("🔄 刷新 ETF 列表", help="从远程重新拉取全量 A 股 ETF 列表"):
    with st.spinner("正在从 akshare 获取全量 ETF 列表..."):
        try:
            df = catalog.load(force_refresh=True)
            st.sidebar.success(f"✅ 已刷新！共 {len(df)} 只 ETF")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"刷新失败: {e}")

# --- Load ETF catalog ---
try:
    etf_list_df = catalog.load()
except Exception as e:
    st.error(f"无法加载 ETF 列表: {e}。请点击侧边栏「刷新 ETF 列表」按钮。")
    st.stop()

st.caption(f"将对全部 **{len(etf_list_df)}** 只 A 股 ETF 基金进行动量排名计算")

st.markdown("---")
st.markdown("### 🏆 全量 ETF 动量排名")

# Momentum period parameter
momentum_days = st.slider("动量计算周期 (天)", min_value=10, max_value=250, value=20, step=5)

# Optional: limit top N for display
top_n = st.sidebar.number_input("显示前 N 名（0=全部）", min_value=0, max_value=len(etf_list_df), value=50, step=10)

if st.button("🚀 计算全量动量排名"):
    all_codes = etf_list_df["code"].tolist()
    all_names = dict(zip(etf_list_df["code"], etf_list_df["name"]))
    total = len(all_codes)
    ranking_data = []

    with st.status(f"正在处理 {total} 只 ETF...", expanded=True) as status:
        progress_bar = st.progress(0)

        for i, sym in enumerate(all_codes):
            name = all_names.get(sym, sym)

            # --- Data freshness check & incremental update ---
            last_date = storage.get_last_date(sym)

            try:
                new_data = fetcher.fetch_incremental(sym, last_date)
                if not new_data.empty:
                    storage.save_bars(sym, new_data)
            except Exception:
                pass  # Skip failed downloads silently

            # --- Load local data and calculate momentum ---
            df = storage.load_bars(sym)
            if not df.empty and len(df) >= 2:
                current_price = df.iloc[-1]["close"]
                past_idx = max(0, len(df) - momentum_days - 1)
                past_price = df.iloc[past_idx]["close"]
                momentum_score = (current_price / past_price) - 1

                ranking_data.append({
                    "代码": sym,
                    "名称": name,
                    "当前价格": round(current_price, 4),
                    "动量得分": round(momentum_score, 4),
                })

            # Update progress every 10 items to keep UI responsive
            if (i + 1) % 10 == 0 or (i + 1) == total:
                progress_bar.progress((i + 1) / total)
                st.write(f"已处理 {i+1}/{total}...")

        status.update(label="✅ 全量动量计算完成！", state="complete")

    if ranking_data:
        ranking_df = pd.DataFrame(ranking_data)
        ranking_df = ranking_df.sort_values(by="动量得分", ascending=False).reset_index(drop=True)

        # Apply top N filter
        display_df = ranking_df.head(top_n) if top_n > 0 else ranking_df

        st.markdown(f"**共计算 {len(ranking_df)} 只 ETF 的动量得分" + (f"，显示前 {top_n} 名**" if top_n > 0 else "**"))

        st.dataframe(
            display_df.style.background_gradient(subset=["动量得分"], cmap="RdYlGn"),
            use_container_width=True,
            hide_index=True,
        )

        top_etf = ranking_df.iloc[0]
        if top_etf["动量得分"] > 0:
            st.success(f"**当前最强标的**: {top_etf['名称']} ({top_etf['代码']}) — 动量得分: {top_etf['动量得分']:.4f}")
        else:
            st.warning("当前所有标的动量均为负，建议空仓观望。")
    else:
        st.warning("无法计算排名，可能是由于网络或数据源问题。")
