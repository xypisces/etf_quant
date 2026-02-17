"""
统一数据加载接口 - 对接 Storage/Fetcher/Cleaner 数据管理层

提供 load() 和 update() 两个核心方法：
- load(): 从本地 Storage 加载数据，不足时自动增量下载
- update(): 主动触发增量更新
"""

import pandas as pd

from src.data.cleaner import DataCleaner
from src.data.fetcher import DataFetcher
from src.data.storage import DataStorage


class DataLoader:
    """
    统一数据加载器

    底层使用 DataStorage(Parquet+SQLite) 存储数据，
    数据不足时自动通过 DataFetcher 增量下载并经 DataCleaner 清洗后入库。
    """

    def __init__(self, storage_dir: str = "data"):
        self._storage = DataStorage(storage_dir=storage_dir)
        self._fetcher = DataFetcher()
        self._cleaner = DataCleaner()

    def load(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载历史数据

        优先从本地 Storage 读取，数据不足时自动增量下载。

        Args:
            symbol: 标的代码，如 '510300'
            start_date: 起始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'

        Returns:
            标准化 DataFrame，含 date(index), open, high, low, close, volume
        """
        # 1. 尝试从 Storage 加载
        df = self._storage.load_bars(symbol, start_date, end_date)

        # 2. 检查是否需要增量下载
        if self._needs_update(symbol, start_date, end_date):
            try:
                self._do_incremental_update(symbol, end_date)
                # 重新加载（现在应该有完整数据了）
                df = self._storage.load_bars(symbol, start_date, end_date)
            except Exception as e:
                print(f"[DataLoader] 增量下载失败: {e}")
                if df.empty:
                    print("[DataLoader] 无本地数据可用")

        if not df.empty:
            df = self._ensure_types(df)
            print(
                f"[DataLoader] 已加载 {symbol}: "
                f"{len(df)} 条记录 ({df.index.min().date()} ~ {df.index.max().date()})"
            )

        return df

    def update(self, symbol: str, end_date: str | None = None) -> int:
        """
        主动触发增量更新

        Args:
            symbol: 品种代码
            end_date: 结束日期，None 则取当天

        Returns:
            新增数据行数
        """
        last_date = self._storage.get_last_date(symbol)

        try:
            new_data = self._fetcher.fetch_incremental(symbol, last_date, end_date)
        except RuntimeError as e:
            print(f"[DataLoader] 更新失败: {e}")
            return 0

        if new_data.empty:
            return 0

        cleaned = self._cleaner.clean(new_data)
        self._storage.save_bars(symbol, cleaned)
        print(f"[DataLoader] 增量更新: {symbol} 新增 {len(cleaned)} 条记录")
        return len(cleaned)

    def _needs_update(self, symbol: str, start_date: str, end_date: str) -> bool:
        """判断是否需要增量下载"""
        last_date = self._storage.get_last_date(symbol)
        if last_date is None:
            return True  # 没有任何数据

        # 比较 end_date 与 last_date
        end_ts = pd.Timestamp(end_date)
        last_ts = pd.Timestamp(last_date)
        return end_ts > last_ts

    def _do_incremental_update(self, symbol: str, end_date: str) -> None:
        """执行增量下载 + 清洗 + 存储"""
        last_date = self._storage.get_last_date(symbol)
        new_data = self._fetcher.fetch_incremental(symbol, last_date, end_date)

        if not new_data.empty:
            cleaned = self._cleaner.clean(new_data)
            self._storage.save_bars(symbol, cleaned)

    @staticmethod
    def _ensure_types(df: pd.DataFrame) -> pd.DataFrame:
        """确保所有 OHLCV 列为 float64 类型"""
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        return df
