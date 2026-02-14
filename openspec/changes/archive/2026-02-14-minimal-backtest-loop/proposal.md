<!-- Use this as the structure for your output file. Fill in the sections. -->
## 为什么 (Why)

我们需要一个极简、高效的方式来快速验证策略思路。传统的事件驱动框架对于简单的双均线等策略过于厚重。
这个变更将创建一个单脚本的向量化回测工具，直接使用 pandas 进行计算，追求极致的代码简洁和执行速度。

## 变更内容 (What Changes)

*   **实现方式**: 使用单一 Python 脚本，基于 Pandas 向量化计算。
*   **数据源**: 使用 `akshare` 直接获取历史数据。
*   **策略逻辑**: 实现双均线交叉策略作为示例。
*   **指标计算**: 使用向量化方式计算夏普比率、最大回撤。
*   **输出**: 打印文本报告（各项指标）并展示累计收益曲线。
*   **非目标 (Out of Scope)**:
    *   不构建复杂的面向对象框架 (OOP)。
    *   不使用数据库，数据即拿即用或存为临时 CSV。
    *   不处理实时行情。

## 能力 (Capabilities)

### 新增能力 (New Capabilities)

- `vectorized-backtest`: 基于 Pandas 的向量化回测脚本，包含数据获取、信号计算、绩效评估。

### 修改能力 (Modified Capabilities)
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
(无)

## 影响 (Impact)

- **新增文件**: `src/simple_backtest.py` (或类似命名)。
- **依赖**: 新增 `akshare`, `matplotlib` (用于绘图)。
