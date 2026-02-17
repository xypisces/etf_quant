"""
数据存储引擎 - SQLite 元数据 + Parquet 行情数据

提供品种元数据管理和行情数据持久化能力。
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd


class DataStorage:
    """
    本地数据存储引擎

    使用 SQLite 管理品种元数据（代码、最后更新日期等），
    使用 Parquet 格式存储行情数据（高压缩率、列式存储）。
    """

    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        self.parquet_dir = os.path.join(storage_dir, "parquet")
        self.db_path = os.path.join(storage_dir, "market.db")

        # 确保目录存在
        os.makedirs(self.parquet_dir, exist_ok=True)

        # 初始化 SQLite
        self._conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self) -> None:
        """创建元数据表（如不存在）"""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                symbol      TEXT PRIMARY KEY,
                name        TEXT DEFAULT '',
                first_date  TEXT,
                last_date   TEXT,
                updated_at  TEXT
            )
        """)
        self._conn.commit()

    # ===== 行情数据 (Parquet) =====

    def _parquet_path(self, symbol: str) -> str:
        """生成品种 Parquet 文件路径"""
        return os.path.join(self.parquet_dir, f"{symbol}.parquet")

    def save_bars(self, symbol: str, df: pd.DataFrame) -> None:
        """
        保存行情数据到 Parquet 文件

        如果文件已存在，将新数据与旧数据合并（按日期去重，保留最新）。
        同时更新 SQLite 元数据。

        Args:
            symbol: 品种代码
            df: 标准化 DataFrame（index 为 date，含 OHLCV）
        """
        if df.empty:
            return

        path = self._parquet_path(symbol)

        if os.path.exists(path):
            # 合并旧数据
            existing = pd.read_parquet(path)
            combined = pd.concat([existing, df])
            # 按日期去重，保留最后出现的
            combined = combined[~combined.index.duplicated(keep="last")]
            combined.sort_index(inplace=True)
            combined.to_parquet(path)
        else:
            df.sort_index(inplace=True)
            df.to_parquet(path)

        # 更新元数据
        all_data = pd.read_parquet(path)
        first_date = str(all_data.index.min().date())
        last_date = str(all_data.index.max().date())
        self.update_metadata(symbol, first_date, last_date)

    def load_bars(
        self, symbol: str, start_date: str | None = None, end_date: str | None = None
    ) -> pd.DataFrame:
        """
        从 Parquet 文件读取行情数据

        Args:
            symbol: 品种代码
            start_date: 起始日期（YYYYMMDD 或 YYYY-MM-DD）
            end_date: 结束日期

        Returns:
            DataFrame，文件不存在则返回空 DataFrame
        """
        path = self._parquet_path(symbol)
        if not os.path.exists(path):
            return pd.DataFrame()

        df = pd.read_parquet(path)

        # 日期过滤
        if start_date:
            start = pd.Timestamp(start_date)
            df = df[df.index >= start]
        if end_date:
            end = pd.Timestamp(end_date)
            df = df[df.index <= end]

        return df

    # ===== 品种元数据 (SQLite) =====

    def update_metadata(
        self, symbol: str, first_date: str, last_date: str, name: str = ""
    ) -> None:
        """更新品种元数据"""
        now = datetime.now().isoformat()
        self._conn.execute(
            """
            INSERT INTO symbols (symbol, name, first_date, last_date, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                first_date = ?,
                last_date = ?,
                updated_at = ?
            """,
            (symbol, name, first_date, last_date, now, first_date, last_date, now),
        )
        self._conn.commit()

    def get_last_date(self, symbol: str) -> str | None:
        """查询品种最后存储日期，不存在返回 None"""
        row = self._conn.execute(
            "SELECT last_date FROM symbols WHERE symbol = ?", (symbol,)
        ).fetchone()
        return row[0] if row else None

    def list_symbols(self) -> list[dict]:
        """返回所有已管理品种列表"""
        rows = self._conn.execute(
            "SELECT symbol, name, first_date, last_date, updated_at FROM symbols"
        ).fetchall()
        return [
            {
                "symbol": r[0],
                "name": r[1],
                "first_date": r[2],
                "last_date": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]

    def close(self) -> None:
        """关闭数据库连接"""
        self._conn.close()
