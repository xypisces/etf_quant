"""
策略抽象基类 - 定义标准化策略接口
"""

from abc import ABC, abstractmethod
from enum import Enum


class Signal(Enum):
    """交易信号枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):
    """
    策略抽象基类

    所有策略必须继承此类并实现 on_bar() 和 generate_signal() 方法。
    策略在 on_bar() 中只能访问当前及历史 bar 数据，严禁使用未来函数。
    """

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name

    @abstractmethod
    def on_bar(self, bar: dict) -> None:
        """
        接收一根 K 线数据，更新策略内部状态

        Args:
            bar: 字典格式，包含 open, high, low, close, volume 字段
        """
        pass

    @abstractmethod
    def generate_signal(self) -> Signal:
        """
        根据当前状态生成交易信号

        Returns:
            Signal.BUY / Signal.SELL / Signal.HOLD
        """
        pass

    def reset(self) -> None:
        """重置策略状态（用于新一轮回测）"""
        pass

    def on_fill(self, signal: "Signal") -> None:
        """
        通知策略：订单已成交

        由回测引擎在买入/卖出成功执行后调用，用于同步策略内部状态。
        子类可重写此方法以更新持仓标记等内部状态。

        Args:
            signal: 已成交的信号类型 (BUY / SELL)
        """
        pass
