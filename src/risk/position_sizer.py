"""
仓位管理器 - 支持固定比例/ATR/Kelly 仓位计算
"""

from enum import Enum


class SizingMethod(Enum):
    """仓位计算方法"""
    FIXED_FRACTION = "fixed_fraction"
    ATR = "atr"
    KELLY = "kelly"


class PositionSizer:
    """
    仓位计算器

    根据选定策略计算每次开仓数量，确保不超过可用资金。
    """

    def __init__(
        self,
        method: SizingMethod = SizingMethod.FIXED_FRACTION,
        risk_fraction: float = 0.02,
        atr_multiplier: float = 2.0,
        kelly_fraction: float = 0.5,
    ):
        """
        Args:
            method: 仓位计算方法
            risk_fraction: 固定比例仓位的风险比例（默认 2%）
            atr_multiplier: ATR 仓位的乘数
            kelly_fraction: Kelly 分数（如半 Kelly = 0.5）
        """
        self.method = method
        self.risk_fraction = risk_fraction
        self.atr_multiplier = atr_multiplier
        self.kelly_fraction = kelly_fraction

    def calculate(
        self,
        total_equity: float,
        available_cash: float,
        price: float,
        atr: float | None = None,
        win_rate: float | None = None,
        profit_loss_ratio: float | None = None,
    ) -> int:
        """
        计算开仓数量

        Args:
            total_equity: 账户总权益
            available_cash: 可用现金
            price: 当前价格
            atr: ATR 值（ATR 方法必需）
            win_rate: 胜率（Kelly 方法必需）
            profit_loss_ratio: 盈亏比（Kelly 方法必需）

        Returns:
            开仓数量（整数，最少为 0）
        """
        if price <= 0 or available_cash <= 0:
            return 0

        if self.method == SizingMethod.FIXED_FRACTION:
            position_value = total_equity * self.risk_fraction
        elif self.method == SizingMethod.ATR:
            position_value = self._calculate_atr_size(total_equity, atr)
        elif self.method == SizingMethod.KELLY:
            position_value = self._calculate_kelly_size(
                total_equity, win_rate, profit_loss_ratio
            )
        else:
            position_value = total_equity * self.risk_fraction

        # 不超过可用现金
        position_value = min(position_value, available_cash)

        # 计算可购买数量（取整）
        quantity = int(position_value / price)
        return max(quantity, 0)

    def _calculate_atr_size(self, total_equity: float, atr: float | None) -> float:
        """ATR 仓位计算: 风险金额 / (ATR × 乘数)"""
        if atr is None or atr <= 0:
            return total_equity * self.risk_fraction

        risk_amount = total_equity * self.risk_fraction
        # ATR 方法返回的是基于风险的金额
        return risk_amount / (atr * self.atr_multiplier) if atr * self.atr_multiplier > 0 else 0

    def _calculate_kelly_size(
        self,
        total_equity: float,
        win_rate: float | None,
        profit_loss_ratio: float | None,
    ) -> float:
        """Kelly 公式: f = p - (1 - p) / b，使用 kelly_fraction 缩减"""
        if win_rate is None or profit_loss_ratio is None:
            return total_equity * self.risk_fraction

        if profit_loss_ratio <= 0:
            return 0

        kelly = win_rate - (1 - win_rate) / profit_loss_ratio

        # Kelly 为负时不开仓
        if kelly <= 0:
            return 0

        # 使用分数 Kelly（如半 Kelly）降低风险
        fraction = kelly * self.kelly_fraction
        return total_equity * fraction
