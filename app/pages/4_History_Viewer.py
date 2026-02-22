import streamlit as st
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.etf_catalog import ETFCatalog

st.set_page_config(page_title="历史记录", page_icon="🗄️", layout="wide")

st.title("回测历史记录查看")

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── 辅助函数 ──────────────────────────────────────────────


@st.cache_data(ttl=3600 * 24)
def _load_etf_name_map() -> dict[str, str]:
    catalog = ETFCatalog()
    try:
        df = catalog.load(force_refresh=False)
        return dict(zip(df["code"], df["name"]))
    except Exception:
        return {}


def _scan_report_symbols() -> list[str]:
    """扫描 results 目录下所有包含 report.md 的股票代码文件夹"""
    symbols = []
    if not os.path.isdir(RESULTS_DIR):
        return symbols
    for entry in sorted(os.listdir(RESULTS_DIR)):
        report_path = os.path.join(RESULTS_DIR, entry, "report.md")
        if os.path.isfile(report_path):
            symbols.append(entry)
    return symbols


def _parse_strategies(content: str) -> list[str]:
    """从 report.md 中解析出所有策略段落标题"""
    return re.findall(r"^## (.+? — \d{4}-\d{2}-\d{2})", content, re.MULTILINE)


def _extract_strategy_section(content: str, title: str) -> str:
    """提取单个策略段落的内容（从标题到下一个 ## 或对比表）"""
    escaped = re.escape(title)
    pattern = re.compile(
        r"## " + escaped + r"\n(.*?)(?=\n## |\n<!-- COMPARISON_TABLE_START -->|\Z)",
        re.DOTALL,
    )
    m = pattern.search(content)
    return m.group(1).strip() if m else ""


def _extract_comparison_table(content: str) -> str:
    """提取策略对比汇总表"""
    pattern = re.compile(
        r"<!-- COMPARISON_TABLE_START -->\n(.*?)<!-- COMPARISON_TABLE_END -->",
        re.DOTALL,
    )
    m = pattern.search(content)
    return m.group(1).strip() if m else ""


# ── 侧边栏 ─────────────────────────────────────────────────

name_map = _load_etf_name_map()
symbols = _scan_report_symbols()

st.sidebar.header("选择历史记录")

if not symbols:
    st.sidebar.info("暂无报告。请先在「策略回测」面板运行回测。")
    st.info("💡 `results/` 目录下没有找到任何 `report.md` 文件。")
else:
    # 构建带中文名的选项
    display_options = []
    for s in symbols:
        etf_name = name_map.get(s, "")
        label = f"{s} — {etf_name}" if etf_name else s
        display_options.append(label)

    label_to_symbol = dict(zip(display_options, symbols))

    selected_label = st.sidebar.selectbox("选择品种", options=display_options)
    selected_symbol = label_to_symbol[selected_label]

    report_path = os.path.join(RESULTS_DIR, selected_symbol, "report.md")
    mtime = os.path.getmtime(report_path)
    from datetime import datetime

    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    st.sidebar.caption(f"📄 最后更新: {mtime_str}")

    # 读取报告
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析策略列表
    strategy_titles = _parse_strategies(content)

    # ── 主区域 ─────────────────────────────────────────────

    etf_name = name_map.get(selected_symbol, "")
    title_suffix = f" ({etf_name})" if etf_name else ""
    st.markdown(f"## 📊 {selected_symbol}{title_suffix} 回测报告")

    # 1. 策略对比汇总表（优先展示）
    comparison = _extract_comparison_table(content)
    if comparison:
        st.markdown(comparison)
        st.markdown("---")

    # 2. 各策略详细报告
    if strategy_titles:
        # 侧边栏可筛选策略
        st.sidebar.markdown("---")
        selected_strategies = st.sidebar.multiselect(
            "筛选策略（留空显示全部）",
            options=strategy_titles,
            default=[],
        )
        show_titles = selected_strategies if selected_strategies else strategy_titles

        st.markdown("### 📑 策略详细报告")
        for title in show_titles:
            section = _extract_strategy_section(content, title)
            if section:
                with st.expander(f"📋 {title}", expanded=len(show_titles) == 1):
                    st.markdown(section)
    else:
        # 无法解析段落，直接渲染整个文件
        st.markdown(content)
