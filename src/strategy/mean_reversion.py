"""
均值回归策略 - 布林带 + RSI 超买超卖

入场：收盘价触及布林带下轨 + RSI < 超卖阈值
出场：收盘价触及布林带上轨 + RSI > 超买阈值，或回归中轨止盈
"""

from collections import deque

from src.strategy.base import Strategy, Signal


class MeanReversionStrategy(Strategy):
    """
    均值回归策略

    基于布林带超买超卖区间 + RSI 辅助过滤。
    """

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        **_kwargs,
    ):
        super().__init__(name=f"MeanRev({bb_period},{rsi_period})")
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

        self._closes: deque[float] = deque(maxlen=max(bb_period, rsi_period + 1))
        self._last_close: float | None = None

        # 布林带
        self._bb_mid: float | None = None
        self._bb_upper: float | None = None
        self._bb_lower: float | None = None

        # RSI
        self._gains: deque[float] = deque(maxlen=rsi_period)
        self._losses: deque[float] = deque(maxlen=rsi_period)
        self._rsi: float | None = None

        self._in_position: bool = False

    def on_bar(self, bar: dict) -> None:
        close = bar["close"]

        # RSI 计算
        if self._last_close is not None:
            change = close - self._last_close
            self._gains.append(max(change, 0.0))
            self._losses.append(max(-change, 0.0))

            if len(self._gains) >= self.rsi_period:
                avg_gain = sum(self._gains) / len(self._gains)
                avg_loss = sum(self._losses) / len(self._losses)
                if avg_loss == 0:
                    self._rsi = 100.0
                else:
                    rs = avg_gain / avg_loss
                    self._rsi = 100.0 - (100.0 / (1.0 + rs))

        self._closes.append(close)
        self._last_close = close

        # 布林带计算
        if len(self._closes) >= self.bb_period:
            recent = list(self._closes)[-self.bb_period:]
            mean = sum(recent) / len(recent)
            variance = sum((x - mean) ** 2 for x in recent) / len(recent)
            std = variance ** 0.5

            self._bb_mid = mean
            self._bb_upper = mean + self.bb_std * std
            self._bb_lower = mean - self.bb_std * std

    def generate_signal(self) -> Signal:
        if self._bb_lower is None or self._rsi is None or self._last_close is None:
            return Signal.HOLD

        if not self._in_position:
            # 超卖买入：触及下轨 + RSI 低
            if self._last_close <= self._bb_lower and self._rsi < self.rsi_oversold:
                return Signal.BUY
        else:
            # 超买卖出：触及上轨 + RSI 高
            if self._last_close >= self._bb_upper and self._rsi > self.rsi_overbought:
                return Signal.SELL
            # 回归中轨止盈
            if self._last_close >= self._bb_mid:
                return Signal.SELL

        return Signal.HOLD

    def on_fill(self, signal: Signal) -> None:
        if signal == Signal.BUY:
            self._in_position = True
        elif signal == Signal.SELL:
            self._in_position = False

    def reset(self) -> None:
        self._closes.clear()
        self._last_close = None
        self._bb_mid = None
        self._bb_upper = None
        self._bb_lower = None
        self._gains.clear()
        self._losses.clear()
        self._rsi = None
        self._in_position = False
