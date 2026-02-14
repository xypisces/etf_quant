"""
双均线交叉策略 - 继承 Strategy 基类
"""

from collections import deque
from src.strategy.base import Strategy, Signal


class MACrossStrategy(Strategy):
    """
    双均线交叉策略

    短期均线上穿长期均线时买入，下穿时卖出。
    内部维护 rolling window，逐 bar 计算均线，杜绝未来函数。
    """

    def __init__(self, short_window: int = 5, long_window: int = 20):
        super().__init__(name=f"MACross({short_window},{long_window})")
        self.short_window = short_window
        self.long_window = long_window

        # 使用 deque 维护价格窗口，最大长度为长期均线周期
        self._prices: deque[float] = deque(maxlen=long_window)
        self._prev_short_ma: float | None = None
        self._prev_long_ma: float | None = None
        self._curr_short_ma: float | None = None
        self._curr_long_ma: float | None = None

    def on_bar(self, bar: dict) -> None:
        """接收一根 bar 数据，更新均线状态"""
        close = bar["close"]
        self._prices.append(close)

        # 保存上一次的均线值（用于判断交叉）
        self._prev_short_ma = self._curr_short_ma
        self._prev_long_ma = self._curr_long_ma

        # 计算当前均线
        prices_list = list(self._prices)
        if len(prices_list) >= self.short_window:
            self._curr_short_ma = sum(prices_list[-self.short_window :]) / self.short_window
        else:
            self._curr_short_ma = None

        if len(prices_list) >= self.long_window:
            self._curr_long_ma = sum(prices_list[-self.long_window :]) / self.long_window
        else:
            self._curr_long_ma = None

    def generate_signal(self) -> Signal:
        """
        根据均线交叉生成信号

        - 短期均线上穿长期均线 → BUY
        - 短期均线下穿长期均线 → SELL
        - 其他情况 → HOLD
        """
        # 数据不足，无法计算
        if (
            self._curr_short_ma is None
            or self._curr_long_ma is None
            or self._prev_short_ma is None
            or self._prev_long_ma is None
        ):
            return Signal.HOLD

        # 检测交叉
        prev_diff = self._prev_short_ma - self._prev_long_ma
        curr_diff = self._curr_short_ma - self._curr_long_ma

        # 上穿：前一周期 短 <= 长，当前 短 > 长
        if prev_diff <= 0 and curr_diff > 0:
            return Signal.BUY

        # 下穿：前一周期 短 >= 长，当前 短 < 长
        if prev_diff >= 0 and curr_diff < 0:
            return Signal.SELL

        return Signal.HOLD

    def reset(self) -> None:
        """重置策略状态"""
        self._prices.clear()
        self._prev_short_ma = None
        self._prev_long_ma = None
        self._curr_short_ma = None
        self._curr_long_ma = None
