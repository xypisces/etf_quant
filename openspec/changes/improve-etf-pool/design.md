## Context

轮动池管理页面目前仅有一个硬编码的 6 个 ETF 作为自选池，且行情数据每次通过网络实时请求。系统已有成熟的数据基础设施：`DataFetcher`（支持全量和增量下载）、`DataStorage`（SQLite 元数据 + Parquet 行情存储、支持增量合并与 `get_last_date()` 查询）。本次改进应最大限度复用这些已有组件。

## Goals / Non-Goals

**Goals:**
- 通过 akshare 获取 A 股市场全量 ETF 基金列表（代码+名称），本地缓存为 Parquet 文件，并支持手动刷新。
- 改造轮动池页面的自选池数据源，从全量 ETF 列表中搜索和多选。
- 计算动量排名前，利用已有的 `DataFetcher.fetch_incremental()` 和 `DataStorage` 自动检查数据新鲜度并做增量更新。

**Non-Goals:**
- 不涉及自动定时调度更新（无 crontab 或类似后台进程）。
- 不修改现有回测引擎或其他页面。

## Decisions

1. **新建 `src/data/etf_catalog.py` 模块管理 ETF 列表**
   - **Rationale**: 职责单一 — 与行情数据获取 (`DataFetcher`) 和行情存储 (`DataStorage`) 分离。ETF 列表本质是 "产品目录"，与 K 线行情是两种不同的数据。
   - **Alternatives Considered**: 在 `DataFetcher` 中加一个方法 — 会违反其 "只负责行情下载" 的职责定位。

2. **ETF 列表使用 `fund_etf_spot_em()` 获取**
   - **Rationale**: akshare 的 `fund_etf_spot_em()` 接口返回所有交易中的 ETF 基金实时行情，包含代码和名称字段，一次调用即可获取全量列表。
   - **Alternatives Considered**: `fund_etf_category_sina()` — 分类获取效率低；手动维护 CSV — 不可持续。

3. **行情增量更新复用已有 `DataFetcher` + `DataStorage`**
   - **Rationale**: 系统已有完整的增量下载 (`fetch_incremental`) 和增量存储 (`save_bars` 自动去重合并) 机制。直接调用即可，无需额外开发。

## Risks / Trade-offs

- **[Risk] `fund_etf_spot_em()` 可能因网络或 akshare API 变动而失败**
  - *Mitigation*: 加载 ETF 列表时使用 try/except，失败则回退到本地缓存版本，并提示用户。
- **[Risk] 全量 ETF 数量较多（~800+），批量增量更新耗时较长**
  - *Mitigation*: 仅对用户选入自选池的 ETF 执行增量更新，而非全量列表中的所有品种。
