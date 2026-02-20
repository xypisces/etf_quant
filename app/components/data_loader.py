import streamlit as st
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def get_recent_market_data(symbol: str, period_days: int = 30) -> pd.DataFrame:
    """
    Fetch recent market data for a given ETF symbol using akshare.
    Caches the result for 1 hour to prevent redundant API calls.
    """
    # For akshare, ETF symbols typically hold a prefix, e.g., sh510300
    # In this simple implementation, we assume the user passes the correct format
    # or we handle standard 6-digit codes.
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    try:
        # Example fetching raw ETF data; might need adjustment based on specific akshare API
        # Using fund_etf_hist_em for general ETF historical data
        df = ak.fund_etf_hist_em(
            symbol=symbol, 
            period="daily", 
            start_date=start_str, 
            end_date=end_str, 
            adjust="qfq"
        )
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            # Add English column aliases for the backtest engine
            col_map = {
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
            }
            for cn, en in col_map.items():
                if cn in df.columns:
                    df[en] = df[cn]
            return df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_period_return(df: pd.DataFrame) -> float:
    """Calculate the simple return over the period provided in the dataframe."""
    if df.empty or len(df) < 2:
        return 0.0
    
    start_price = df.iloc[0]['收盘']
    end_price = df.iloc[-1]['收盘']
    
    return (end_price - start_price) / start_price * 100
