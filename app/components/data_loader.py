"""
Dashboard 数据加载组件 - 复用 src/data 数据管理层

统一使用 DataLoader 获取数据，自动增量下载并本地缓存（Parquet + SQLite）。
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.loader import DataLoader


@st.cache_data(ttl=3600)
def get_recent_market_data(symbol: str, period_days: int = 30) -> pd.DataFrame:
    """
    获取最近 N 天的行情数据。

    底层使用 DataLoader (Parquet + SQLite 缓存 + akshare 增量下载)，
    与 CLI 共享同一份本地数据。

    Args:
        symbol: 品种代码（如 '510300' 或 '601318'）
        period_days: 时间窗口（天）

    Returns:
        标准化 DataFrame，index 为日期，含 open/close/high/low/volume 等列
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    try:
        loader = DataLoader(storage_dir="data")
        df = loader.load(symbol, start_str, end_str)

        if df is not None and not df.empty:
            # 添加中文列别名（兼容 Streamlit 页面中使用中文列名的代码）
            col_map = {
                "open": "开盘",
                "close": "收盘",
                "high": "最高",
                "low": "最低",
                "volume": "成交量",
            }
            for en, cn in col_map.items():
                if en in df.columns and cn not in df.columns:
                    df[cn] = df[en]
            return df

        return pd.DataFrame()
    except Exception as e:
        st.warning(f"数据获取失败 ({symbol}): {e}")
        return pd.DataFrame()


def calculate_period_return(df: pd.DataFrame) -> float:
    """计算区间内的简单收益率（百分比）"""
    if df.empty or len(df) < 2:
        return 0.0

    col = "close" if "close" in df.columns else "收盘"
    start_price = df.iloc[0][col]
    end_price = df.iloc[-1][col]

    return (end_price - start_price) / start_price * 100
