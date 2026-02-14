"""
统一数据加载接口 - 支持 CSV 缓存和 akshare API
"""

import os
import pandas as pd
import akshare as ak


class DataLoader:
    """统一数据加载器，优先读取 CSV 缓存，否则从 akshare API 获取"""

    def __init__(self, cache_dir: str = "csv"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, symbol: str, start_date: str, end_date: str) -> str:
        """生成缓存文件路径"""
        return os.path.join(self.cache_dir, f"{symbol}_{start_date}_{end_date}.csv")

    def load(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载历史数据

        Args:
            symbol: 标的代码，如 '510300'
            start_date: 起始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'

        Returns:
            标准化的 DataFrame，包含 date(index), open, high, low, close, volume 列
            失败时返回空 DataFrame
        """
        cache_file = self._cache_path(symbol, start_date, end_date)

        # 优先从本地缓存加载
        if os.path.exists(cache_file):
            print(f"[DataLoader] 从缓存加载: {cache_file}")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return self._ensure_types(df)

        # 从 akshare API 获取
        return self._fetch_from_api(symbol, start_date, end_date, cache_file)

    def _fetch_from_api(
        self, symbol: str, start_date: str, end_date: str, cache_file: str
    ) -> pd.DataFrame:
        """从 akshare API 获取数据"""
        # 提取 6 位纯代码
        code = symbol[-6:] if len(symbol) > 6 else symbol
        print(f"[DataLoader] 从 akshare 获取数据: {code} ...")

        try:
            df = ak.fund_etf_hist_em(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            # 标准化列名
            rename_dict = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            }
            df.rename(columns=rename_dict, inplace=True)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)

            # 确保数值类型
            df = self._ensure_types(df)

            # 保存到缓存
            df.to_csv(cache_file)
            print(f"[DataLoader] 数据已缓存到: {cache_file}")

            return df

        except Exception as e:
            print(f"[DataLoader] 数据获取失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def _ensure_types(df: pd.DataFrame) -> pd.DataFrame:
        """确保所有 OHLCV 列为 float64 类型"""
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        return df
