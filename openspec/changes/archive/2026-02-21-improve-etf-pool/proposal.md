## Why

目前仪表盘的轮动池管理页面仅使用了一个硬编码的少量 ETF 列表作为"自选池"，且每次计算动量排名时直接通过网络实时请求行情数据。这带来两个问题：一是用户无法看到 A 股市场中全部可用的 ETF 基金，选择范围受限；二是每次都通过 API 拉取数据耗时且不经济。改进方案是将全量 A 股 ETF 基金列表接入系统，并利用本地数据管理层（`src/data/`）进行行情数据的持久化与增量更新，在计算前自动检测数据新鲜度，仅在需要时才拉取增量。

## What Changes

- 新增一个**全量 ETF 基金列表获取模块**，通过 akshare 拉取 A 股市场中所有 ETF 基金的代码和名称，本地缓存为 Parquet 文件，并支持定期刷新。
- **改造轮动池管理页面**（`app/pages/2_Pool_Manager.py`），将自选池数据源从硬编码字典替换为从本地全量 ETF 列表中筛选，支持搜索和多选。
- 新增**行情数据本地管理与增量更新逻辑**：在用户计算动量排名前，自动检查本地行情数据是否覆盖到最新交易日，如果不是则通过 akshare 做增量更新后再计算。
- 复用并扩展现有 `src/data/storage.py` (DataStorage) 进行数据持久化管理。

## Capabilities

### New Capabilities

- `etf-catalog`: 全量 A 股 ETF 基金列表的获取、本地缓存与定期刷新能力。

### Modified Capabilities

- `pool-manager`: 自选池数据源从硬编码改为全量 ETF 列表筛选；计算动量排名前增加数据新鲜度检查和增量更新逻辑。

## Impact

- **修改文件**: `app/pages/2_Pool_Manager.py`（页面逻辑大幅改造）、`app/components/data_loader.py`（可能增加增量更新辅助函数）。
- **新增文件**: `src/data/etf_catalog.py`（ETF 列表管理模块）。
- **复用模块**: `src/data/storage.py`（DataStorage 类，用于行情 Parquet 读写）、`src/data/fetcher.py`（数据下载器）。
- **无新增依赖**: 所有功能基于已有的 akshare + pandas + pyarrow 实现。
