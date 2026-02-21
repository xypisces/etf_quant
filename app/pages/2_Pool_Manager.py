import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
from datetime import datetime

import streamlit as st
import pandas as pd

from src.data.etf_catalog import ETFCatalog
from src.data.storage import DataStorage
from src.data.fetcher import DataFetcher

st.set_page_config(page_title="轮动池管理", page_icon="🔄", layout="wide")

st.title("ETF 全量动量排名")

# --- Constants ---
CACHE_PATH = os.path.join("data", "momentum_ranking_cache.parquet")

# --- Initialize backend services ---
catalog = ETFCatalog(storage_dir="data")
storage = DataStorage(storage_dir="data")
fetcher = DataFetcher()


# ===== 排名缓存持久化函数 =====

def save_ranking_cache(ranking_df: pd.DataFrame, momentum_days: int, scope_type: str) -> None:
    """
    保存排名结果到本地 Parquet 文件。

    全量计算时仅保留前 50 名，筛选计算时保留全部。
    元信息（计算时间、动量周期、范围类型）作为额外列保存。
    """
    df = ranking_df.copy()

    # 全量计算时截取前 50 名
    if scope_type == "全量" and len(df) > 50:
        df = df.head(50)

    # 添加元信息列
    df["_计算时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["_动量周期"] = momentum_days
    df["_范围类型"] = scope_type

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    df.to_parquet(CACHE_PATH, index=False)


def load_ranking_cache() -> tuple[pd.DataFrame | None, dict | None]:
    """
    从本地 Parquet 文件读取缓存的排名数据和元信息。

    Returns:
        (ranking_df, meta_info) 文件不存在时返回 (None, None)
        ranking_df: 不含元信息列的排名数据
        meta_info: dict 包含 计算时间、动量周期、范围类型
    """
    if not os.path.exists(CACHE_PATH):
        return None, None

    df = pd.read_parquet(CACHE_PATH)
    if df.empty:
        return None, None

    # 提取元信息
    meta = {
        "计算时间": df["_计算时间"].iloc[0] if "_计算时间" in df.columns else "未知",
        "动量周期": int(df["_动量周期"].iloc[0]) if "_动量周期" in df.columns else 0,
        "范围类型": df["_范围类型"].iloc[0] if "_范围类型" in df.columns else "未知",
    }

    # 移除元信息列
    meta_cols = [c for c in df.columns if c.startswith("_")]
    ranking_df = df.drop(columns=meta_cols)

    return ranking_df, meta


def compute_momentum(codes: list[str], names_map: dict, momentum_days: int,
                     status_container=None, progress_bar=None) -> pd.DataFrame:
    """
    对给定标的列表计算动量得分。

    执行增量数据更新后计算动量。
    """
    total = len(codes)
    ranking_data = []

    for i, sym in enumerate(codes):
        name = names_map.get(sym, sym)

        # 增量数据更新
        last_date = storage.get_last_date(sym)
        try:
            new_data = fetcher.fetch_incremental(sym, last_date)
            if not new_data.empty:
                storage.save_bars(sym, new_data)
        except Exception:
            pass

        # 加载数据并计算动量
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

        # 更新进度
        if progress_bar is not None and ((i + 1) % 10 == 0 or (i + 1) == total):
            progress_bar.progress((i + 1) / total)
            if status_container is not None:
                status_container.write(f"已处理 {i+1}/{total}...")

    if ranking_data:
        result_df = pd.DataFrame(ranking_data)
        result_df = result_df.sort_values(by="动量得分", ascending=False).reset_index(drop=True)
        return result_df
    return pd.DataFrame()


def display_ranking(ranking_df: pd.DataFrame, top_n: int = 0) -> None:
    """展示排名结果表格及最强标的提示。"""
    display_df = ranking_df.head(top_n) if top_n > 0 else ranking_df

    st.markdown(
        f"**共计算 {len(ranking_df)} 只 ETF 的动量得分"
        + (f"，显示前 {top_n} 名**" if top_n > 0 else "**")
    )

    st.dataframe(
        display_df.style.background_gradient(subset=["动量得分"], cmap="RdYlGn"),
        use_container_width=True,
        hide_index=True,
    )

    if not ranking_df.empty:
        top_etf = ranking_df.iloc[0]
        if top_etf["动量得分"] > 0:
            st.success(f"**当前最强标的**: {top_etf['名称']} ({top_etf['代码']}) — 动量得分: {top_etf['动量得分']:.4f}")
        else:
            st.warning("当前所有标的动量均为负，建议空仓观望。")


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

# --- 页面加载时展示缓存的上次排名结果 ---
cached_df, cached_meta = load_ranking_cache()

if cached_df is not None and cached_meta is not None:
    st.markdown("### 📋 上次排名结果")
    col1, col2, col3 = st.columns(3)
    col1.metric("计算时间", cached_meta["计算时间"])
    col2.metric("动量周期", f"{cached_meta['动量周期']} 天")
    col3.metric("范围类型", cached_meta["范围类型"])
    display_ranking(cached_df)
    st.markdown("---")
else:
    st.info("📭 暂无缓存的排名结果，请执行一次动量排名计算。")

# --- Main Area ---
st.markdown("### 🏆 ETF 动量排名计算")

# 动量周期参数
momentum_days = st.slider("动量计算周期 (天)", min_value=10, max_value=250, value=20, step=5)

# 显示前 N 名
top_n = st.sidebar.number_input("显示前 N 名（0=全部）", min_value=0, max_value=len(etf_list_df), value=50, step=10)

# --- 下拉筛选器 ---
etf_options = [f"{row['code']} - {row['name']}" for _, row in etf_list_df.iterrows()]
selected_etfs = st.multiselect(
    "🔍 筛选标的（不选则计算全量）",
    options=etf_options,
    default=[],
    placeholder="搜索 ETF 代码或名称...",
    help="选择需要计算动量的 ETF 标的，留空则对全量 ETF 计算",
)

# 解析选中的标的代码
if selected_etfs:
    selected_codes = [s.split(" - ")[0] for s in selected_etfs]
    scope_type = "筛选"
    st.caption(f"将对选中的 **{len(selected_codes)}** 只 ETF 进行动量排名计算")
else:
    selected_codes = etf_list_df["code"].tolist()
    scope_type = "全量"
    st.caption(f"将对全部 **{len(selected_codes)}** 只 A 股 ETF 基金进行动量排名计算")

# 名称映射
all_names = dict(zip(etf_list_df["code"], etf_list_df["name"]))

# --- 计算动量排名按钮 ---
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    compute_clicked = st.button("🚀 计算动量排名")

with col_btn2:
    # 重新计算 Top50 按钮：仅在存在缓存时启用
    has_cache = cached_df is not None and not cached_df.empty
    recompute_top50 = st.button(
        "🔄 重新计算 Top50",
        disabled=not has_cache,
        help="基于上次排名前 50 名标的重新计算动量" if has_cache else "请先执行一次完整的动量排名计算",
    )

# --- 执行计算 ---
if compute_clicked:
    total = len(selected_codes)
    with st.status(f"正在处理 {total} 只 ETF...", expanded=True) as status:
        progress_bar = st.progress(0)
        ranking_df = compute_momentum(selected_codes, all_names, momentum_days,
                                      status_container=st, progress_bar=progress_bar)
        status.update(label="✅ 动量计算完成！", state="complete")

    if not ranking_df.empty:
        # 保存缓存
        save_ranking_cache(ranking_df, momentum_days, scope_type)
        display_ranking(ranking_df, top_n)
    else:
        st.warning("无法计算排名，可能是由于网络或数据源问题。")

elif recompute_top50:
    # 从缓存读取前 50 名标的
    top50_codes = cached_df["代码"].head(50).tolist()
    total = len(top50_codes)

    with st.status(f"正在重新计算 Top50（{total} 只 ETF）...", expanded=True) as status:
        progress_bar = st.progress(0)
        ranking_df = compute_momentum(top50_codes, all_names, momentum_days,
                                      status_container=st, progress_bar=progress_bar)
        status.update(label="✅ Top50 重新计算完成！", state="complete")

    if not ranking_df.empty:
        # 覆盖缓存（Top50 重算结果也保存前 50）
        save_ranking_cache(ranking_df, momentum_days, "Top50重算")
        display_ranking(ranking_df, top_n)
    else:
        st.warning("无法计算排名，可能是由于网络或数据源问题。")
