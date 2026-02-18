"""
动量轮动策略 - 基于 ROC 动量得分

计算 N 日收益率（Rate of Change）作为动量得分：
  - 正动量 → 买入（看多）
  - 负动量 → 卖出（看空/离场）

适用于单品种模式，多品种轮动在 batch_runner 层面实现。
"""

from collections import deque

from src.strategy.base import Strategy, Signal


class MomentumStrategy(Strategy):
    """
    动量轮动策略

    基于 N 日 ROC 动量得分，正动量入场、负动量离场。
    """

    def __init__(self, lookback_period: int = 20, **_kwargs):
        super().__init__(name=f"Momentum({lookback_period})")
        self.lookback_period = lookback_period

        self._closes: deque[float] = deque(maxlen=lookback_period + 1)
        self._last_close: float | None = None
        self._momentum: float | None = None
        self._in_position: bool = False

    def on_bar(self, bar: dict) -> None:
        close = bar["close"]
        self._closes.append(close)
        self._last_close = close

        # 计算 N 日 ROC
        if len(self._closes) > self.lookback_period:
            old_close = self._closes[0]
            if old_close > 0:
                self._momentum = (close - old_close) / old_close
            else:
                self._momentum = 0.0

    def generate_signal(self) -> Signal:
        if self._momentum is None:
            return Signal.HOLD

        if not self._in_position and self._momentum > 0:
            return Signal.BUY

        if self._in_position and self._momentum <= 0:
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
        self._momentum = None
        self._in_position = False
