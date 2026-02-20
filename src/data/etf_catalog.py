"""
ETF 基金目录管理 - 全量 A 股 ETF 列表的获取与本地缓存

职责单一：只负责管理 ETF 品种目录（代码+名称），不处理行情数据。
"""

import os
from datetime import datetime

import akshare as ak
import pandas as pd


class ETFCatalog:
    """
    A 股 ETF 基金目录管理器

    通过 akshare 获取全量 ETF 列表，本地缓存为 Parquet 文件，
    支持读取缓存和手动刷新。
    """

    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        self._cache_path = os.path.join(storage_dir, "etf_catalog.parquet")
        os.makedirs(storage_dir, exist_ok=True)

    def load(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        加载 ETF 目录列表

        优先读取本地缓存，如果缓存不存在或 force_refresh=True 则从远程拉取。

        Args:
            force_refresh: 是否强制从远程重新拉取

        Returns:
            DataFrame，包含 'code' (代码) 和 'name' (名称) 列
        """
        if not force_refresh and os.path.exists(self._cache_path):
            return self._read_cache()

        # 远程拉取
        try:
            df = self._fetch_remote()
            self._save_cache(df)
            return df
        except Exception as e:
            # 远程失败时回退到本地缓存
            if os.path.exists(self._cache_path):
                print(f"[ETFCatalog] 远程拉取失败 ({e})，回退到本地缓存")
                return self._read_cache()
            raise RuntimeError(f"无法获取 ETF 列表且无本地缓存: {e}") from e

    def _fetch_remote(self) -> pd.DataFrame:
        """从 akshare 获取全量 ETF 列表"""
        print("[ETFCatalog] 正在从远程获取全量 A 股 ETF 列表...")
        raw = ak.fund_etf_spot_em()

        if raw is None or raw.empty:
            raise RuntimeError("akshare fund_etf_spot_em() 返回空数据")

        # 提取代码、名称和市值
        df = pd.DataFrame({
            "code": raw["代码"].astype(str),
            "name": raw["名称"].astype(str),
            "market_cap": pd.to_numeric(raw["总市值"], errors="coerce").fillna(0),
        })

        # 仅保留场内可实时交易的 ETF（过滤掉场外基金）
        # 上交所: 51xxxx, 56xxxx, 58xxxx  深交所: 15xxxx, 16xxxx
        exchange_prefixes = ("51", "56", "58", "15", "16")
        df = df[df["code"].str[:2].isin(exchange_prefixes)]

        # 去重并按市值降序排序
        df = df.drop_duplicates(subset=["code"]).sort_values("market_cap", ascending=False).reset_index(drop=True)
        print(f"[ETFCatalog] 获取到 {len(df)} 只场内 ETF 基金")
        return df

    def _save_cache(self, df: pd.DataFrame) -> None:
        """保存缓存到本地 Parquet 文件"""
        df.to_parquet(self._cache_path, index=False)
        print(f"[ETFCatalog] 已缓存至 {self._cache_path}")

    def _read_cache(self) -> pd.DataFrame:
        """读取本地缓存"""
        df = pd.read_parquet(self._cache_path)
        print(f"[ETFCatalog] 从本地缓存加载 {len(df)} 只 ETF")
        return df

    @property
    def cache_exists(self) -> bool:
        """本地缓存是否存在"""
        return os.path.exists(self._cache_path)

    @property
    def cache_mtime(self) -> str | None:
        """本地缓存的最后修改时间"""
        if not self.cache_exists:
            return None
        ts = os.path.getmtime(self._cache_path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
