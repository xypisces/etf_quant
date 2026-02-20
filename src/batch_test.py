"""批量回测脚本 - 多品种 × 多策略矩阵化回测"""

from src.research import BatchRunner

runner = BatchRunner(storage_dir="data")

results = runner.run(
    symbols=["512800", "510300", "510500"],
    strategies=[
        {"name": "ma_cross", "params": {"short_window": 5, "long_window": 20}},
        {"name": "ema20_pullback", "params": {}},
        {"name": "turtle", "params": {"entry_period": 20, "exit_period": 10}},
        {"name": "grid", "params": {"grid_num": 10}},
        {"name": "momentum", "params": {"lookback_period": 20}},
        {"name": "mean_reversion", "params": {"bb_period": 20, "rsi_period": 14}},
    ],
    start_date="20200101",
    end_date="20260219",
    sort_by="total_return",
)

print("\n===== 批量回测结果 =====\n")
print(results.to_string(index=False))

# 导出 CSV
results.to_csv("results/batch_results.csv", index=False)
print("\n结果已导出: results/batch_results.csv")
