"""
报告写入模块 - 将回测结果写入结构化 Markdown 文件

功能:
- 按标的代码分目录存储 (results/<symbol>/)
- 五维度报告 + 月度收益表写入 Markdown
- 多策略增量追加（以 策略名 — 日期 为标题）
- 自动生成策略对比汇总表（含买入持有基准）
"""

import os
import re
from datetime import datetime

from src.backtest.metrics import (
    format_report,
    format_monthly_table,
    total_return,
)


# HTML 注释锚点，用于解析和替换对比表
_COMPARISON_START = "<!-- COMPARISON_TABLE_START -->"
_COMPARISON_END = "<!-- COMPARISON_TABLE_END -->"


class ReportWriter:
    """
    回测报告写入器

    将五维度报告、月度收益表写入 Markdown 文件，
    支持增量追加和策略对比汇总。
    """

    def __init__(self, symbol: str, save_dir: str = "results"):
        self.symbol = symbol
        self.save_dir = os.path.join(save_dir, symbol)
        self.report_path = os.path.join(self.save_dir, "report.md")
        os.makedirs(self.save_dir, exist_ok=True)

    def write_report(
        self,
        report_md: str,
        monthly_table_md: str,
        strategy_name: str,
        total_ret: float,
        benchmark_total_ret: float | None = None,
    ) -> str:
        """
        将一次回测的报告写入 Markdown 文件（增量追加）

        Args:
            report_md: format_report 返回的报告字符串
            monthly_table_md: format_monthly_table 返回的月度收益表字符串
            strategy_name: 策略名称
            total_ret: 该策略的累计收益率
            benchmark_total_ret: 买入持有基准的累计收益率

        Returns:
            报告文件路径
        """
        today = datetime.now().strftime("%Y-%m-%d")
        section_title = f"## {strategy_name} — {today}"

        # 构建本次策略段落
        section_lines = [
            section_title,
            "",
            report_md,
            "",
        ]

        if monthly_table_md:
            section_lines += [
                "### 月度收益矩阵",
                "",
                monthly_table_md,
                "",
            ]

        section_lines.append("---")
        section_lines.append("")
        section_content = "\n".join(section_lines)

        # 读取或创建报告文件
        if os.path.exists(self.report_path):
            with open(self.report_path, "r", encoding="utf-8") as f:
                existing = f.read()
        else:
            existing = f"# 回测报告: {self.symbol}\n\n"

        # 移除旧的对比表（如果存在）
        existing = self._remove_comparison_table(existing)

        # 追加新策略段落
        content = existing.rstrip("\n") + "\n\n" + section_content

        # 重新生成对比表
        comparison = self._build_comparison_table(content, benchmark_total_ret)
        content = content.rstrip("\n") + "\n\n" + comparison + "\n"

        # 写入文件
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[Report] 报告已写入: {self.report_path}")
        return self.report_path

    def _remove_comparison_table(self, content: str) -> str:
        """移除已有的对比汇总表"""
        pattern = re.compile(
            re.escape(_COMPARISON_START) + r".*?" + re.escape(_COMPARISON_END),
            re.DOTALL,
        )
        return pattern.sub("", content).rstrip("\n")

    def _build_comparison_table(
        self,
        content: str,
        benchmark_total_ret: float | None = None,
    ) -> str:
        """
        扫描报告内容，提取所有策略的累计收益率，生成对比汇总表

        解析逻辑: 找到 ## 标题行获取策略名，然后在其段落内找
        "累计收益率 (Total Return)" 行提取数值
        """
        entries: list[tuple[str, float]] = []

        # 按 ## 标题分割段落
        sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)

        for section in sections:
            # 匹配 ## 策略名 — 日期
            title_match = re.match(r"^## (.+?) — (\d{4}-\d{2}-\d{2})", section)
            if not title_match:
                continue

            strategy = title_match.group(1)
            date = title_match.group(2)

            # 提取累计收益率
            ret_match = re.search(
                r"\|\s*累计收益率.*?\|\s*(-?\d+\.\d+%)\s*\|", section
            )
            if ret_match:
                ret_str = ret_match.group(1).replace("%", "")
                ret_val = float(ret_str) / 100
                entries.append((f"{strategy} ({date})", ret_val))

        # 添加基准
        if benchmark_total_ret is not None:
            entries.append(("📊 买入持有 (Benchmark)", benchmark_total_ret))

        if not entries:
            return ""

        # 按收益率降序排列
        entries.sort(key=lambda x: x[1], reverse=True)

        # 生成 Markdown 表格
        lines = [
            _COMPARISON_START,
            "## 📈 策略对比汇总",
            "",
            "| 排名 | 策略 | 累计收益率 | 备注 |",
            "|------|------|-----------|------|",
        ]

        best_ret = entries[0][1]
        for i, (name, ret) in enumerate(entries, 1):
            mark = "🏆 **最佳**" if ret == best_ret else ""
            lines.append(f"| {i} | {name} | {ret:.2%} | {mark} |")

        lines.append("")
        lines.append(_COMPARISON_END)
        return "\n".join(lines)
