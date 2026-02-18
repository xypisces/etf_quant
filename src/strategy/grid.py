"""
网格交易策略 - 价格区间低吸高抛

在指定价格区间内等分 N 条网格线，
价格下穿网格线买入，上穿网格线卖出。
"""

from collections import deque

from src.strategy.base import Strategy, Signal


class GridStrategy(Strategy):
    """
    网格交易策略

    设定价格区间，等分网格线，触及下格买入、上格卖出。
    可自动根据历史数据确定价格区间。
    """

    def __init__(
        self,
        grid_num: int = 10,
        upper_price: float | None = None,
        lower_price: float | None = None,
        lookback_period: int = 60,
        **_kwargs,
    ):
        super().__init__(name=f"Grid({grid_num})")
        self.grid_num = grid_num
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.lookback_period = lookback_period

        self._prices: deque[float] = deque(maxlen=lookback_period)
        self._grid_lines: list[float] = []
        self._last_close: float | None = None
        self._prev_close: float | None = None
        self._in_position: bool = False
        self._grid_initialized: bool = False

    def _init_grid(self) -> None:
        """初始化网格线"""
        if self.upper_price and self.lower_price:
            upper = self.upper_price
            lower = self.lower_price
        elif len(self._prices) >= self.lookback_period:
            upper = max(self._prices)
            lower = min(self._prices)
        else:
            return

        if upper <= lower:
            return

        step = (upper - lower) / self.grid_num
        self._grid_lines = [lower + i * step for i in range(self.grid_num + 1)]
        self._grid_initialized = True

    def _get_grid_level(self, price: float) -> int:
        """获取价格所在的网格层级（0 = 最低，grid_num = 最高）"""
        for i in range(len(self._grid_lines) - 1):
            if price < self._grid_lines[i + 1]:
                return i
        return len(self._grid_lines) - 1

    def on_bar(self, bar: dict) -> None:
        close = bar["close"]
        self._prev_close = self._last_close
        self._last_close = close
        self._prices.append(close)

        if not self._grid_initialized:
            self._init_grid()

    def generate_signal(self) -> Signal:
        if not self._grid_initialized or self._prev_close is None or self._last_close is None:
            return Signal.HOLD

        # 超出网格区间 → HOLD
        if self._last_close < self._grid_lines[0] or self._last_close > self._grid_lines[-1]:
            return Signal.HOLD

        prev_level = self._get_grid_level(self._prev_close)
        curr_level = self._get_grid_level(self._last_close)

        if not self._in_position and curr_level < prev_level:
            # 价格下穿网格线 → 买入
            return Signal.BUY

        if self._in_position and curr_level > prev_level:
            # 价格上穿网格线 → 卖出
            return Signal.SELL

        return Signal.HOLD

    def on_fill(self, signal: Signal) -> None:
        if signal == Signal.BUY:
            self._in_position = True
        elif signal == Signal.SELL:
            self._in_position = False

    def reset(self) -> None:
        self._prices.clear()
        self._grid_lines = []
        self._last_close = None
        self._prev_close = None
        self._in_position = False
        self._grid_initialized = False
