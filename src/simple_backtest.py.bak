
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# 配置：无风险利率
RISK_FREE_RATE = 0.0

def fetch_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取历史数据，优先读取本地缓存
    """
    cache_file = f"{symbol}_{start_date}_{end_date}.csv"
    if os.path.exists(cache_file):
        print(f"Loading data from cache: {cache_file}")
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    else:
        print(f"Fetching data for {symbol} from akshare...")
        # akshare 的 symbol 格式处理，这里假设输入 sh510300
        # 实际 akshare.stock_zh_a_hist 需要 6 位代码
        code = symbol[-6:]
        # adjust="qfq" 前复权
        try:
            # 尝试使用 ETF 专用接口 (东方财富)
            # code 不需要带 sh/sz 前缀
            # print(f"Fetching ETF data for {code}...")
            df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            # 列名映射
            rename_dict = {
                '日期': 'date', '开盘': 'open', '收盘': 'close', 
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            }
            df.rename(columns=rename_dict, inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # 确保数值列为 float
            numeric_cols = ['open', 'close', 'high', 'low', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 保存缓存
            df.to_csv(cache_file)
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
            
    return df

def calculate_signals(df: pd.DataFrame, short_window: int = 5, long_window: int = 20) -> pd.DataFrame:
    """
    计算双均线策略信号
    """
    # 避免 SettingWithCopyWarning
    df = df.copy()
    
    # 计算均线
    df['MA_Short'] = df['close'].rolling(window=short_window).mean()
    df['MA_Long'] = df['close'].rolling(window=long_window).mean()
    
    # 生成持仓信号：短期 > 长期 = 1 (买入/持有), 否则 0 (空仓/卖出)
    df['signal'] = 0
    df.loc[df['MA_Short'] > df['MA_Long'], 'signal'] = 1
    
    # 处理信号滞后：T 日的信号只能在 T+1 日执行
    # position 表示 T+1 日的实际持仓
    df['position'] = df['signal'].shift(1)
    
    # 填充 NaN (主要是因为 rolling 和 shift 导致的)
    df['position'] = df['position'].fillna(0)
    
    return df

def calculate_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算策略绩效
    """
    df = df.copy()
    
    # 计算标的日收益率
    df['pct_change'] = df['close'].pct_change()
    
    # 计算策略日收益率 = 持仓 * 标的收益率
    # 这里忽略了交易成本
    df['strategy_ret'] = df['position'] * df['pct_change']
    
    # 计算累计净值 (Cumulative Returns)
    df['equity_curve'] = (1 + df['strategy_ret']).cumprod()
    df['benchmark_curve'] = (1 + df['pct_change']).cumprod()
    
    return df

def report(df: pd.DataFrame, symbol: str):
    """
    打印绩效报告并绘图
    """
    # 移除空数据（前几天因为均线计算可能是 NaN）
    df = df.dropna()
    
    if df.empty:
        print("无有效回测数据")
        return

    # 计算总收益
    total_ret = df['equity_curve'].iloc[-1] - 1
    
    # 计算年化收益 (假设一年 252 个交易日)
    days = (df.index[-1] - df.index[0]).days
    if days <= 0:
        annual_ret = 0
    else:
        annual_ret = (1 + total_ret) ** (365 / days) - 1
    
    # 计算夏普比率
    # 年化 Sharpe = (日收益率均值 - 无风险利率) / 日收益率标准差 * sqrt(252)
    daily_std = df['strategy_ret'].std()
    if daily_std == 0:
        sharpe = 0
    else:
        sharpe = (df['strategy_ret'].mean() - RISK_FREE_RATE/252) / daily_std * (252 ** 0.5)
    
    # 计算最大回撤
    # 历史最高净值
    cum_max = df['equity_curve'].cummax()
    drawdown = (df['equity_curve'] - cum_max) / cum_max
    max_drawdown = drawdown.min()
    
    print("-" * 30)
    print(f"回测报告: {symbol}")
    print("-" * 30)
    print(f"总收益率 (Total Return):    {total_ret:.2%}")
    print(f"年化收益率 (Annualized):    {annual_ret:.2%}")
    print(f"夏普比率 (Sharpe Ratio):    {sharpe:.2f}")
    print(f"最大回撤 (Max Drawdown):    {max_drawdown:.2%}")
    print("-" * 30)
    
    # 绘图设置中文字体 (尝试适配常见系统)
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC', 'Heiti TC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['equity_curve'], label='策略收益 (Strategy)')
    plt.plot(df.index, df['benchmark_curve'], label='基准收益 (Benchmark)', alpha=0.6)
    plt.title(f'回测结果: 双均线策略 - {symbol}')
    plt.xlabel('日期 (Date)')
    plt.ylabel('累计净值 (Cumulative Returns)')
    plt.legend()
    plt.grid(True)
    
    # 保存图片
    filename = f'backtest_result_{symbol}.png'
    plt.savefig(filename)
    print(f"结果图表已保存至 {filename}")
    # 如果是在本地运行，可能会弹窗
    # plt.show()

def main():
    # 参数设置
    symbol = "sh510300" # 沪深300ETF
    start_date = "20200101"
    end_date = datetime.now().strftime("%Y%m%d")
    
    # 1. 获取数据
    df = fetch_data(symbol, start_date, end_date)
    if df.empty:
        print("Failed to fetch data.")
        return
        
    # 2. 计算信号
    df = calculate_signals(df)
    
    # 3. 计算绩效
    df = calculate_performance(df)
    
    # 4. 生成报告
    report(df, symbol)

if __name__ == "__main__":
    main()
