## Context

随着 ETF 量化交易系统底层引擎（回测、策略逻辑）的逐步完善，目前面临的主要瓶颈是缺乏一个直观的用户界面。研究人员和交易员需要通过修改代码或配置文件来运行回测并查看结果，这不仅效率低下，而且不便于进行多策略、多参数的对比分析。

为解决这一问题，本项目计划引入 Streamlit 作为前端框架，构建一个纯 Python 的轻量级 Web 仪表盘。Streamlit 能够快速将现有的数据分析脚本转化为交互式 Web 应用，非常适合当前重后台分析、轻前端交互的量化系统现状。

## Goals / Non-Goals

**Goals:**
- 提供一个无需编写代码即可进行策略回测、参数配置的交互式界面。
- 实现回测结果（净值曲线、持仓变化、绩效指标）的直观可视化。
- 提供 ETF 行情监控和轮动池的实时状态查看界面。
- 确保前端展示层与现有的量化引擎高度解耦，通过函数调用或 API 的方式进行数据交互。

**Non-Goals:**
- 本阶段不涉及任何实盘交易接口的对接和订单执行。
- 不构建复杂的用户认证和多租户权限系统（目前定位为个人/内部研究工具）。
- 不重构现有的底层回测引擎核心逻辑，仅作为其调用者。

## Decisions

1. **选择 Streamlit 作为前端框架**
   - **Rationale**: 团队以 Python 栈为主，Streamlit 允许完全使用 Python 编写 Web 界面，无需学习 HTML/CSS/JavaScript 或 React/Vue 等前端框架。开发速度极快，与现有的 Pandas、Matplotlib/Plotly 数据科学栈天然兼容。
   - **Alternatives Considered**: 
     - *Dash (Plotly)*: 虽然也是纯 Python，但回调机制较为复杂，学习曲线较陡，对于快速搭建内部工具而言偏重。
     - *Gradio*: 更偏向于机器学习模型的简单演示，对于复杂的包含多个交互组件的量化仪表盘灵活性不足。
     - *前后端分离 (FastAPI + React)*: 架构最正规，但开发成本高，对于当前的需求来说是 over-engineering。

2. **采用 Plotly 进行高亮交互式图表绘制**
   - **Rationale**: 相比于 Matplotlib 的静态图片，Plotly 提供了丰富的交互功能（缩放、平移、悬停提示），这对于查看 K 线图和资金曲线至关重要。Streamlit 原生良好支持 Plotly。
   - **Alternatives Considered**: 
     - *Matplotlib/Seaborn*: 虽然系统目前可能正在使用，但在 Web 端缺乏交互性。
     - *Pyecharts*: 同样渲染美观且支持交互，但与 Streamlit 的集成不如 Plotly 原生和顺滑。

3. **目录结构与模块划分**
   - **Rationale**: 在项目根目录（或同级逻辑目录）创建 `app/` 或 `dashboard/` 文件夹。内部再按功能划分页面或组件（例如 `app/pages/1_backtest.py`, `app/components/charts.py`）。这样清晰地隔离了前后端代码。
   - **Alternatives Considered**: 将 UI 代码直接混杂在 `engine` 或 `strategy` 模块中（极度不推荐，会导致严重的耦合）。

## Risks / Trade-offs

- **[Risk] Streamlit 的重绘机制可能导致性能问题** 
  - *Mitigation*: Streamlit 的工作原理是每次用户交互都会从上到下重新运行脚本。对于耗时的回测计算，**必须**使用 `@st.cache_data` 或 `@st.cache_resource` 装饰器来缓存中间结果和数据加载过程，避免重复计算。
- **[Risk] 随着页面增多，单应用代码臃肿**
  - *Mitigation*: 采用 Streamlit 的多页面应用（Multipage Apps）架构，将不同的功能模块（回测面板、行情看板、历史记录）拆分到独立的文件中。

## Migration Plan

1. 在项目中创建 `app/` 目录并配置初始的 `run_dashboard.py` 入口。
2. 开发测试并发布 0.1 版本的基础界面。
3. 后续通过 `streamlit run app/run_dashboard.py` 命令即可启动服务，无需复杂的数据迁移或线上部署流程（当前主要为本地运行）。
4. 使用入本地数据库（如 SQLite 或 JSON 文件）来持久化保存用户在界面上的回测配置和“历史记录”。