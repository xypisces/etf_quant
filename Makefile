.PHONY: dashboard backtest

## 启动 Streamlit 交互式仪表盘
dashboard:
	uv run streamlit run app/run_dashboard.py

## 运行命令行回测 (可追加参数, 例: make backtest ARGS="--config my.yaml")
backtest:
	uv run python -m src.main $(ARGS)
