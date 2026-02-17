"""
数据清洗器 - 标准化清洗流水线

按顺序执行：去重 → 排序 → 缺失值处理 → 列名标准化 → 类型统一
"""

import pandas as pd


# 列名映射：中文 → 英文
_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
}

# 标准 OHLCV 列
_NUMERIC_COLS = ["open", "high", "low", "close", "volume"]


class DataCleaner:
    """
    数据清洗器

    对原始行情 DataFrame 执行标准化清洗流程，
    确保输出数据格式统一、质量可靠。
    """

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        执行完整清洗流水线

        Args:
            df: 原始 DataFrame（可能含中文列名、缺失值、重复行）

        Returns:
            清洗后的标准化 DataFrame，index 为 date，含 OHLCV 列
        """
        if df.empty:
            return df

        df = df.copy()

        # 1. 列名标准化
        df = self._standardize_columns(df)

        # 2. 确保 date 为 index
        df = self._ensure_date_index(df)

        # 3. 去重（按日期去重，保留最后出现的）
        df = df[~df.index.duplicated(keep="last")]

        # 4. 排序
        df.sort_index(inplace=True)

        # 5. 缺失值处理（前值填充 + 后值填充）
        df[_NUMERIC_COLS] = df[_NUMERIC_COLS].ffill().bfill()

        # 6. 类型统一
        df = self._ensure_types(df)

        return df

    @staticmethod
    def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名：中文映射 + 小写"""
        df.rename(columns=_COLUMN_MAP, inplace=True)
        df.columns = [c.lower().strip() for c in df.columns]
        return df

    @staticmethod
    def _ensure_date_index(df: pd.DataFrame) -> pd.DataFrame:
        """确保 date 列为 DatetimeIndex"""
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df

    @staticmethod
    def _ensure_types(df: pd.DataFrame) -> pd.DataFrame:
        """确保 OHLCV 列为 float64"""
        for col in _NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        return df
