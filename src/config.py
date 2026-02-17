"""
配置管理模块 - 加载 YAML 配置并创建组件实例

用法:
    from src.config import load_config, create_strategy

    cfg = load_config("config.yaml")
    strategy = create_strategy(cfg["strategy"])
"""

from pathlib import Path

import yaml

from src.strategy.base import Strategy
from src.strategy.ma_cross import MACrossStrategy
from src.strategy.ema20_pullback import EMA20PullbackStrategy


# 策略注册表: name -> class
# 新增策略时只需在此添加一行映射
STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    "ma_cross": MACrossStrategy,
    "ema20_pullback": EMA20PullbackStrategy,
}


def load_config(path: str | Path = "config.yaml") -> dict:
    """
    加载 YAML 配置文件

    Args:
        path: 配置文件路径，默认为项目根目录下的 config.yaml

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML 解析失败
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def create_strategy(strategy_cfg: dict) -> Strategy:
    """
    根据配置创建策略实例

    Args:
        strategy_cfg: 策略配置字典，包含 name 和 params

    Returns:
        策略实例

    Raises:
        ValueError: 未知的策略名称

    Example:
        >>> cfg = {"name": "ema20_pullback", "params": {"ema_period": 20}}
        >>> strategy = create_strategy(cfg)
    """
    name = strategy_cfg["name"]
    params = strategy_cfg.get("params", {}) or {}

    if name not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(f"未知策略: '{name}'。可用策略: {available}")

    strategy_class = STRATEGY_REGISTRY[name]
    return strategy_class(**params)
