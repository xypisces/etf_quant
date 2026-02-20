import streamlit as st
import os
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="历史记录", page_icon="🗄️", layout="wide")

st.title("回测历史记录查看室")

RESULTS_DIR = "results"
# Ensure directory exists just in case
os.makedirs(RESULTS_DIR, exist_ok=True)

def scan_history_files() -> list[dict]:
    """Scan the results directory for saved backtest reports."""
    history_records = []
    
    # We walk through the directories inside the results folder.
    # Assuming typical structure results/SYMBOL/REPORT.json
    for root, _, files in os.walk(RESULTS_DIR):
        for file in files:
            # We look for json files that look like backtest reports
            if file.endswith(".json") and "report" in file.lower():
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Extract basic metadata. The exact structure depends on how we saved it
                        # but let's assume standard keys
                        metadata = data.get("metadata", {})
                        
                        record = {
                            "file": filepath,
                            "filename": file,
                            "date": metadata.get("timestamp", datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")),
                            "symbol": metadata.get("symbol", os.path.basename(root)),
                            "strategy": metadata.get("strategy_name", "Unknown Strategy")
                        }
                        history_records.append(record)
                except Exception as e:
                    # Silently skip unparseable files
                    pass
                
    # Sort by date descending
    history_records.sort(key=lambda x: x["date"], reverse=True)
    return history_records

# --- Sidebar: Select Record ---
st.sidebar.header("选择历史记录")

records = scan_history_files()

if not records:
    st.sidebar.info("暂无历史记录。请先去「策略回测」面板运行并保存回测结果。")
    st.info("💡 目前您的 `results/` 目录下没有任何保存的回测记录（JSON 格式）。")
else:
    # Format options for the selectbox
    options = [f"{r['date']} | {r['symbol']} | {r['strategy']}" for r in records]
    
    selected_option = st.sidebar.selectbox("选择要查看的回测报告", options=options)
    
    # Find the corresponding record
    selected_idx = options.index(selected_option)
    selected_record = records[selected_idx]
    
    file_path = selected_record["file"]
    
    # Load and display the selected record
    with st.spinner("正在加载历史报告数据..."):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                
            st.markdown(f"### 📄 报告信息: `{selected_record['filename']}`")
            
            # 1. Show Parameters if available
            params = report_data.get("parameters", {})
            if params:
                st.write("**策略参数:**")
                # Format parameters as a nice pill/tag layout or simple JSON
                st.json(params)
                
            # 2. Extract metrics to display from saved text report or structured data
            metrics_text = report_data.get("metrics_report", "")
            
            if metrics_text:
                st.markdown("---")
                st.markdown(metrics_text)
            else:
                st.warning("⚠️ 此报告中没有找到详细的性能指标文本。")
                
            # 3. Can potentially load the equity curve if saved as structured data
            # Assuming it might be saved under "equity_curve" as a dict mapping dates to values
            curve_data = report_data.get("equity_curve", {})
            if curve_data:
                st.markdown("---")
                st.markdown("### 📈 历史净值曲线")
                
                s = pd.Series(curve_data)
                # s.index is expected to be string dates
                s.index = pd.to_datetime(s.index)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=s.index, y=s.values, mode='lines', name='策略净值', line=dict(color='blue')))
                fig.update_layout(height=400, title="保存的回测序列", hovermode="x unified")
                st.plotly_chart(fig)
            
        except Exception as e:
            st.error(f"无法读取或解析历史报告文件: {e}")
