"""
海龟策略 - 唐奇安通道突破 + ATR 动态止损

入场：收盘价突破 N 日最高价（唐奇安通道上轨）
出场：收盘价跌破 M 日最低价（唐奇安通道下轨）或 ATR 倍数止损
"""

from collections import deque

from src.strategy.base import Strategy, Signal


class TurtleStrategy(Strategy):
    """
    海龟策略

    基于唐奇安通道突破入场，ATR 倍数止损或通道下轨出场。
    """

    def __init__(
        self,
        entry_period: int = 20,
        exit_period: int = 10,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        **_kwargs,
    ):
        super().__init__(name=f"Turtle({entry_period},{exit_period})")
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

        self._highs: deque[float] = deque(maxlen=entry_period)
        self._lows: deque[float] = deque(maxlen=exit_period)
        self._closes: deque[float] = deque(maxlen=atr_period + 1)
        self._tr_values: deque[float] = deque(maxlen=atr_period)

        self._last_close: float | None = None
        self._atr: float | None = None
        self._entry_price: float | None = None
        self._in_position: bool = False

    def on_bar(self, bar: dict) -> None:
        high = bar["high"]
        low = bar["low"]
        close = bar["close"]

        # 计算 True Range
        if self._closes:
            prev_close = self._closes[-1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            self._tr_values.append(tr)

        self._highs.append(high)
        self._lows.append(low)
        self._closes.append(close)
        self._last_close = close

        # 计算 ATR
        if len(self._tr_values) >= self.atr_period:
            self._atr = sum(self._tr_values) / len(self._tr_values)

    def generate_signal(self) -> Signal:
        if self._last_close is None or self._atr is None:
            return Signal.HOLD

        if len(self._highs) < self.entry_period:
            return Signal.HOLD

        if not self._in_position:
            # 突破入场通道上轨
            channel_high = max(list(self._highs)[:-1]) if len(self._highs) > 1 else self._highs[0]
            if self._last_close > channel_high:
                return Signal.BUY
        else:
            # 跌破出场通道下轨
            channel_low = min(self._lows)
            if self._last_close < channel_low:
                return Signal.SELL

            # ATR 止损
            if self._entry_price and self._last_close < self._entry_price - self.atr_multiplier * self._atr:
                return Signal.SELL

        return Signal.HOLD

    def on_fill(self, signal: Signal) -> None:
        if signal == Signal.BUY:
            self._in_position = True
            self._entry_price = self._last_close
        elif signal == Signal.SELL:
            self._in_position = False
            self._entry_price = None

    def reset(self) -> None:
        self._highs.clear()
        self._lows.clear()
        self._closes.clear()
        self._tr_values.clear()
        self._last_close = None
        self._atr = None
        self._entry_price = None
        self._in_position = False
