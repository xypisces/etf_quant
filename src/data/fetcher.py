"""
数据下载器 - 封装 akshare API，支持增量更新

职责单一：只负责从远程 API 拉取数据，不做存储和清洗。
"""

from datetime import datetime, timedelta

import akshare as ak
import pandas as pd


class DataFetcher:
    """
    数据下载器

    封装 akshare API 调用，支持全量下载和增量更新。
    """

    def fetch(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        从 akshare 下载 ETF 日线数据

        Args:
            symbol: 品种代码（如 '510300'）
            start_date: 起始日期（YYYYMMDD），None 则不限
            end_date: 结束日期（YYYYMMDD），None 则取当天

        Returns:
            标准化 DataFrame（含 date, open, high, low, close, volume）

        Raises:
            RuntimeError: API 调用失败
        """
        code = symbol[-6:] if len(symbol) > 6 else symbol
        end_date = end_date or datetime.now().strftime("%Y%m%d")

        print(f"[Fetcher] 下载数据: {code} ({start_date or '最早'} ~ {end_date})")

        try:
            kwargs = {
                "symbol": code,
                "period": "daily",
                "end_date": end_date,
                "adjust": "qfq",
            }
            if start_date:
                kwargs["start_date"] = start_date

            df = ak.fund_etf_hist_em(**kwargs)

            if df.empty:
                print(f"[Fetcher] 无新增数据")
                return pd.DataFrame()

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

            print(f"[Fetcher] 下载完成: {len(df)} 条记录")
            return df

        except Exception as e:
            raise RuntimeError(f"数据下载失败 ({code}): {e}") from e

    def fetch_incremental(
        self, symbol: str, last_date: str | None, end_date: str | None = None
    ) -> pd.DataFrame:
        """
        增量下载：从 last_date + 1 天开始下载

        Args:
            symbol: 品种代码
            last_date: 最后已存储日期（YYYY-MM-DD），None 则全量下载
            end_date: 结束日期

        Returns:
            新增数据的 DataFrame，无新增则返回空 DataFrame
        """
        if last_date is None:
            # 无历史数据，全量下载
            return self.fetch(symbol, end_date=end_date)

        # 计算增量起始日期 = last_date + 1
        dt = datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1)
        start_date = dt.strftime("%Y%m%d")

        today = end_date or datetime.now().strftime("%Y%m%d")
        if start_date > today:
            print(f"[Fetcher] 数据已是最新 ({last_date})")
            return pd.DataFrame()

        return self.fetch(symbol, start_date=start_date, end_date=end_date)
