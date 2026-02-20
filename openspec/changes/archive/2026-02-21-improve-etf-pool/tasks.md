## 1. ETF 列表管理模块 (etf-catalog)

- [x] 1.1 新建 `src/data/etf_catalog.py`，实现 `ETFCatalog` 类：通过 akshare `fund_etf_spot_em()` 获取全量 A 股 ETF 列表（代码、名称），本地缓存为 Parquet 文件（`data/etf_catalog.parquet`），支持读取缓存和手动刷新
- [x] 1.2 在 `src/data/__init__.py` 中导出 `ETFCatalog` 类

## 2. 轮动池页面改造 (pool-manager)

- [x] 2.1 改造 `app/pages/2_Pool_Manager.py`：将自选池数据源从硬编码字典替换为从 `ETFCatalog` 加载全量 ETF 列表，提供搜索框和 `multiselect` 组件让用户从全量列表中筛选品种加入自选池
- [x] 2.2 在侧边栏增加"刷新 ETF 列表"按钮，点击后调用 `ETFCatalog` 从远程重新拉取列表并覆盖本地缓存

## 3. 行情数据增量更新 (data freshness)

- [x] 3.1 在 `app/pages/2_Pool_Manager.py` 的动量排名计算逻辑中，接入 `DataStorage` 和 `DataFetcher`：计算前检查本地行情数据最后日期，如果不是最新则调用 `fetch_incremental()` 做增量更新后再从本地读取数据计算
- [x] 3.2 在界面上添加增量更新过程的进度提示（如 Streamlit 的 `st.progress` 和 `st.status`），让用户知道哪些品种正在更新

## 4. 文档更新

- [x] 4.1 更新 `README.md` 中的项目结构说明和轮动池管理功能描述，反映新增的 ETF 列表管理能力
