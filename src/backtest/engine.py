"""
事件驱动回测引擎 - 逐 bar 推送，与实盘逻辑一致
"""

from dataclasses import dataclass, field
import pandas as pd

from src.strategy.base import Strategy, Signal
from src.risk.risk_manager import RiskManager, RiskAction
from src.risk.position_sizer import PositionSizer


@dataclass
class Trade:
    """交易记录"""
    date_open: str
    date_close: str
    side: str           # "BUY"
    quantity: int
    entry_price: float
    exit_price: float
    pnl: float          # 盈亏金额
    pnl_pct: float       # 盈亏百分比
    commission: float    # 总手续费


@dataclass
class BacktestResult:
    """回测结果"""
    equity_curve: pd.Series = field(default_factory=pd.Series)
    daily_returns: pd.Series = field(default_factory=pd.Series)
    benchmark_returns: pd.Series = field(default_factory=pd.Series)
    benchmark_curve: pd.Series = field(default_factory=pd.Series)
    trades: list[dict] = field(default_factory=list)
    final_equity: float = 0.0
    initial_capital: float = 0.0
    strategy_name: str = ""


class BacktestEngine:
    """
    事件驱动回测引擎

    核心循环：逐 bar 推送 → 信号生成 → 风控检查 → 仓位计算 → 订单执行
    """

    def __init__(
        self,
        strategy: Strategy,
        risk_manager: RiskManager | None = None,
        position_sizer: PositionSizer | None = None,
        initial_capital: float = 100_000.0,
        slippage: float = 0.0001,       # 0.01%
        commission_rate: float = 0.0003, # 0.03%
    ):
        self.strategy = strategy
        self.risk_manager = risk_manager or RiskManager()
        self.position_sizer = position_sizer or PositionSizer()
        self.initial_capital = initial_capital
        self.slippage = slippage
        self.commission_rate = commission_rate

        # 账户状态
        self._cash = initial_capital
        self._position = 0          # 持仓数量
        self._entry_price = 0.0     # 开仓均价
        self._entry_date = ""       # 开仓日期
        self._equity_history: list[dict] = []
        self._trades: list[dict] = []

    def run(self, data: pd.DataFrame) -> BacktestResult:
        """
        运行回测

        Args:
            data: 包含 open, high, low, close, volume 列的 DataFrame，index 为日期

        Returns:
            BacktestResult 包含净值曲线、交易记录等
        """
        self._reset()

        for date, row in data.iterrows():
            bar = {
                "date": str(date),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            current_price = bar["close"]

            # 1. 策略接收数据
            self.strategy.on_bar(bar)

            # 2. 风控检查现有持仓（止损/止盈）
            if self._position > 0:
                risk_result = self.risk_manager.check(
                    signal=Signal.HOLD,
                    current_position=self._position,
                    entry_price=self._entry_price,
                    current_price=current_price,
                )
                if risk_result.should_close:
                    self._execute_sell(current_price, bar["date"], risk_result.reason)

            # 3. 策略生成信号
            signal = self.strategy.generate_signal()

            # 4. 风控检查新信号
            if signal != Signal.HOLD:
                risk_result = self.risk_manager.check(
                    signal=signal,
                    current_position=self._position,
                    entry_price=self._entry_price if self._position > 0 else None,
                    current_price=current_price,
                )

                if risk_result.should_close:
                    self._execute_sell(current_price, bar["date"], risk_result.reason)
                elif risk_result.passed:
                    if signal == Signal.BUY and self._position == 0:
                        self._execute_buy(current_price, bar["date"])
                    elif signal == Signal.SELL and self._position > 0:
                        self._execute_sell(current_price, bar["date"], "策略卖出信号")

            # 5. 记录每日状态
            equity = self._cash + self._position * current_price
            self._equity_history.append(
                {
                    "date": date,
                    "equity": equity,
                    "cash": self._cash,
                    "position": self._position,
                    "price": current_price,
                }
            )

        return self._build_result(data)

    def _execute_buy(self, price: float, date: str) -> None:
        """执行买入"""
        # 应用滑点
        actual_price = price * (1 + self.slippage)

        # 计算仓位
        quantity = self.position_sizer.calculate(
            total_equity=self._cash + self._position * price,
            available_cash=self._cash,
            price=actual_price,
        )

        if quantity <= 0:
            return

        # 成交金额和手续费
        trade_value = quantity * actual_price
        commission = trade_value * self.commission_rate

        # 扣除资金
        total_cost = trade_value + commission
        if total_cost > self._cash:
            # 资金不足，调减数量
            quantity = int((self._cash / (1 + self.commission_rate)) / actual_price)
            if quantity <= 0:
                return
            trade_value = quantity * actual_price
            commission = trade_value * self.commission_rate
            total_cost = trade_value + commission

        self._cash -= total_cost
        self._position = quantity
        self._entry_price = actual_price
        self._entry_date = date
        self.strategy.on_fill(Signal.BUY)

    def _execute_sell(self, price: float, date: str, reason: str = "") -> None:
        """执行卖出"""
        if self._position <= 0:
            return

        # 应用滑点
        actual_price = price * (1 - self.slippage)

        # 成交金额和手续费
        trade_value = self._position * actual_price
        commission = trade_value * self.commission_rate

        # 计算盈亏
        pnl = (actual_price - self._entry_price) * self._position - commission
        entry_commission = self._position * self._entry_price * self.commission_rate
        pnl -= entry_commission  # 减去买入时的手续费（记录到交易中）
        pnl_pct = (actual_price - self._entry_price) / self._entry_price if self._entry_price > 0 else 0

        # 记录交易
        self._trades.append(
            {
                "date_open": self._entry_date or date,
                "date_close": date,
                "side": "LONG",
                "quantity": self._position,
                "entry_price": self._entry_price,
                "exit_price": actual_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "commission": commission + entry_commission,
                "reason": reason,
            }
        )

        # 更新账户
        self._cash += trade_value - commission
        self._position = 0
        self._entry_price = 0.0
        self._entry_date = ""
        self.strategy.on_fill(Signal.SELL)

    def _reset(self) -> None:
        """重置引擎状态"""
        self._cash = self.initial_capital
        self._position = 0
        self._entry_price = 0.0
        self._entry_date = ""
        self._equity_history.clear()
        self._trades.clear()
        self.strategy.reset()

    def _build_result(self, data: pd.DataFrame | None = None) -> BacktestResult:
        """构建回测结果"""
        if not self._equity_history:
            return BacktestResult(initial_capital=self.initial_capital)

        df = pd.DataFrame(self._equity_history)
        df.set_index("date", inplace=True)

        equity_curve = df["equity"]
        daily_returns = equity_curve.pct_change().fillna(0)

        # 构建基准数据
        benchmark_returns = pd.Series(dtype=float)
        benchmark_curve = pd.Series(dtype=float)
        if data is not None and "close" in data.columns:
            benchmark_curve = data["close"].reindex(equity_curve.index)
            benchmark_returns = benchmark_curve.pct_change().fillna(0)

        return BacktestResult(
            equity_curve=equity_curve,
            daily_returns=daily_returns,
            benchmark_returns=benchmark_returns,
            benchmark_curve=benchmark_curve,
            trades=self._trades.copy(),
            final_equity=equity_curve.iloc[-1],
            initial_capital=self.initial_capital,
            strategy_name=self.strategy.name,
        )
