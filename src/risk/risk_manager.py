"""
风控管理器 - 止损止盈、最大持仓限制
"""

from enum import Enum
from src.strategy.base import Signal


class RiskAction(Enum):
    """风控动作"""
    PASS = "pass"           # 通过，允许交易
    REJECT = "reject"       # 拒绝信号
    FORCE_CLOSE = "close"   # 强制平仓


class RiskCheckResult:
    """风控检查结果"""

    def __init__(self, action: RiskAction, reason: str = ""):
        self.action = action
        self.reason = reason

    @property
    def passed(self) -> bool:
        return self.action == RiskAction.PASS

    @property
    def should_close(self) -> bool:
        return self.action == RiskAction.FORCE_CLOSE


class RiskManager:
    """
    风控管理器

    在下单前进行风险检查：止损、止盈、最大持仓限制。
    """

    def __init__(
        self,
        stop_loss: float = -0.05,
        take_profit: float = 0.10,
        max_position: int = 1,
    ):
        """
        Args:
            stop_loss: 止损阈值（默认 -5%，负数）
            take_profit: 止盈阈值（默认 +10%，正数）
            max_position: 最大持仓数量（默认 1）
        """
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_position = max_position

    def check(
        self,
        signal: Signal,
        current_position: int,
        entry_price: float | None = None,
        current_price: float | None = None,
    ) -> RiskCheckResult:
        """
        风控检查

        Args:
            signal: 策略产出的交易信号
            current_position: 当前持仓数量
            entry_price: 开仓价格（持仓时需要）
            current_price: 当前价格（持仓时需要）

        Returns:
            RiskCheckResult 包含动作和原因
        """
        # 先检查持仓的止损止盈
        if current_position > 0 and entry_price and current_price:
            pnl_pct = (current_price - entry_price) / entry_price

            # 止损触发
            if pnl_pct <= self.stop_loss:
                return RiskCheckResult(
                    RiskAction.FORCE_CLOSE,
                    f"止损触发: 亏损 {pnl_pct:.2%} <= {self.stop_loss:.2%}",
                )

            # 止盈触发
            if pnl_pct >= self.take_profit:
                return RiskCheckResult(
                    RiskAction.FORCE_CLOSE,
                    f"止盈触发: 盈利 {pnl_pct:.2%} >= {self.take_profit:.2%}",
                )

        # 检查买入信号的持仓限制
        if signal == Signal.BUY and current_position >= self.max_position:
            return RiskCheckResult(
                RiskAction.REJECT,
                f"持仓已达上限: {current_position} >= {self.max_position}",
            )

        # 卖出信号但无持仓
        if signal == Signal.SELL and current_position <= 0:
            return RiskCheckResult(
                RiskAction.REJECT,
                "无持仓，忽略卖出信号",
            )

        return RiskCheckResult(RiskAction.PASS)
