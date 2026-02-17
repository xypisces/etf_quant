"""
EMA20 回踩双支撑策略 - 继承 Strategy 基类

入场条件（三条件同时满足）：
  1. 价格回踩 EMA20 附近后站稳（收盘价重返 EMA20 上方），且回踩发生在最近 N 天内
  2. MACD DIF > 0（零轴上方动量支撑）
  3. 当前成交量低于近期均量（缩量回调，均量不含当天）

出场条件（两日容忍止损）：
  - 收盘价跌破 EMA20 → 进入观察期
  - 次日收盘仍在 EMA20 下方 → 无条件卖出

持仓状态同步：
  - 策略不内部追踪持仓，通过引擎 on_fill 回调同步成交状态
"""

from collections import deque
from src.strategy.base import Strategy, Signal


class EMA20PullbackStrategy(Strategy):
    """
    EMA20 回踩双支撑策略

    结合 EMA20 均线回踩、MACD 动量确认和缩量验证，
    在趋势延续的回调结束点精准入场。
    内部逐 bar 递推计算所有技术指标，杜绝未来函数。
    """

    def __init__(
        self,
        ema_period: int = 20,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        volume_period: int = 20,
        pullback_tolerance: float = 0.005,
        pullback_lookback: int = 5,
    ):
        super().__init__(name=f"EMA20Pullback({ema_period})")
        self.ema_period = ema_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.volume_period = volume_period
        self.pullback_tolerance = pullback_tolerance
        self.pullback_lookback = pullback_lookback

        # EMA 平滑系数
        self._ema_alpha = 2.0 / (ema_period + 1)
        self._macd_fast_alpha = 2.0 / (macd_fast + 1)
        self._macd_slow_alpha = 2.0 / (macd_slow + 1)
        self._macd_signal_alpha = 2.0 / (macd_signal + 1)

        # 初始化所有内部状态
        self._bar_count: int = 0
        self._last_close: float | None = None
        self._ema20: float | None = None

        # MACD 组件
        self._ema_fast_val: float | None = None
        self._ema_slow_val: float | None = None
        self._dif: float | None = None
        self._dea: float | None = None
        self._macd_hist: float | None = None

        # 成交量窗口（多留一根用于排除当天）
        self._volumes: deque[float] = deque(maxlen=volume_period + 1)

        # 策略状态
        self._pullback_bar: int = -999  # 最近一次回踩 EMA20 的 bar 序号
        self._break_count: int = 0      # 跌破 EMA20 的连续天数
        self._in_position: bool = False  # 持仓状态（由 on_fill 更新）

    def on_bar(self, bar: dict) -> None:
        """接收一根 bar 数据，更新 EMA20、MACD、成交量状态"""
        close = bar["close"]
        volume = bar["volume"]
        self._bar_count += 1
        self._last_close = close

        # === 1. 更新 EMA20 ===
        if self._ema20 is None:
            self._ema20 = close  # 首根 bar 用收盘价初始化
        else:
            self._ema20 = self._ema_alpha * close + (1 - self._ema_alpha) * self._ema20

        # === 2. 更新 MACD ===
        if self._ema_fast_val is None:
            self._ema_fast_val = close
            self._ema_slow_val = close
            self._dif = 0.0
            self._dea = 0.0
            self._macd_hist = 0.0
        else:
            self._ema_fast_val = (
                self._macd_fast_alpha * close
                + (1 - self._macd_fast_alpha) * self._ema_fast_val
            )
            self._ema_slow_val = (
                self._macd_slow_alpha * close
                + (1 - self._macd_slow_alpha) * self._ema_slow_val
            )
            self._dif = self._ema_fast_val - self._ema_slow_val
            self._dea = (
                self._macd_signal_alpha * self._dif
                + (1 - self._macd_signal_alpha) * self._dea
            )
            self._macd_hist = self._dif - self._dea

        # === 3. 更新成交量窗口 ===
        self._volumes.append(volume)

        # === 4. 更新回踩状态（仅在空仓时追踪） ===
        if not self._in_position:
            threshold = self._ema20 * (1 + self.pullback_tolerance)
            if close <= threshold:
                self._pullback_bar = self._bar_count  # 记录回踩时刻

    def generate_signal(self) -> Signal:
        """
        根据当前状态生成交易信号

        - 未持仓 + 三条件满足 → BUY
        - 持仓 + 连续两日跌破 EMA20 → SELL
        - 其他 → HOLD
        """
        # 数据不足
        if self._ema20 is None or self._dif is None or self._last_close is None:
            return Signal.HOLD

        if not self._in_position:
            return self._check_entry()

        return self._check_exit()

    def _check_entry(self) -> Signal:
        """检查三条件入场信号"""
        # 需要足够的成交量数据（至少 volume_period + 1 根，才能排除当天）
        if len(self._volumes) < self.volume_period + 1:
            return Signal.HOLD

        # 条件 1：最近 N 天内曾回踩 EMA20，且当前收盘价已重返上方
        bars_since_pullback = self._bar_count - self._pullback_bar
        if bars_since_pullback > self.pullback_lookback:
            return Signal.HOLD  # 回踩已过期

        if self._last_close <= self._ema20:
            return Signal.HOLD  # 还没站回 EMA20 上方

        # 条件 2：MACD DIF > 0（零轴上方）
        if self._dif is None or self._dif <= 0:
            return Signal.HOLD

        # 条件 3：缩量（当前量 < 过去 N 天均量，不含当天）
        past_volumes = list(self._volumes)[:-1]  # 排除当天
        avg_volume = sum(past_volumes) / len(past_volumes)
        if self._volumes[-1] >= avg_volume:
            return Signal.HOLD

        # 三条件同时满足 → 发出买入信号
        # 注意：不在此处修改 _in_position，由 on_fill 回调更新
        return Signal.BUY

    def _check_exit(self) -> Signal:
        """检查两日容忍止损"""
        if self._last_close < self._ema20:
            self._break_count += 1
            if self._break_count >= 2:
                # 连续两日跌破 → 发出卖出信号
                # 注意：不在此处修改 _in_position，由 on_fill 回调更新
                return Signal.SELL
            else:
                return Signal.HOLD  # 首日跌破，进入观察期
        else:
            # 回到 EMA20 上方，重置计数，继续持有
            self._break_count = 0
            return Signal.HOLD

    def on_fill(self, signal: Signal) -> None:
        """
        引擎通知：订单已成交，同步持仓状态

        - BUY 成交：标记持仓，重置回踩标记
        - SELL 成交：标记空仓，重置止损计数
        """
        if signal == Signal.BUY:
            self._in_position = True
            self._pullback_bar = -999  # 重置回踩标记，避免连续买入
            self._break_count = 0
        elif signal == Signal.SELL:
            self._in_position = False
            self._break_count = 0

    def reset(self) -> None:
        """重置所有策略状态（用于新一轮回测）"""
        self._bar_count = 0
        self._last_close = None
        self._ema20 = None
        self._ema_fast_val = None
        self._ema_slow_val = None
        self._dif = None
        self._dea = None
        self._macd_hist = None
        self._volumes.clear()
        self._pullback_bar = -999
        self._break_count = 0
        self._in_position = False
