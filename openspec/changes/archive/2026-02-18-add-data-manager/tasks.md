## 1. 基础设施准备

- [x] 1.1 在 `pyproject.toml` 中添加 `pyarrow` 依赖，运行 `uv sync` 安装
- [x] 1.2 在 `config.yaml` 中新增 `data.storage_dir`（默认 `data`）配置项

## 2. 数据存储层 (`src/data/storage.py`)

- [x] 2.1 创建 `DataStorage` 类，初始化 SQLite 数据库连接和品种元数据表结构
- [x] 2.2 实现 `save_bars(symbol, df)` 方法：将 DataFrame 以 Parquet 格式存储，已有文件则合并去重
- [x] 2.3 实现 `load_bars(symbol, start_date, end_date)` 方法：从 Parquet 文件读取指定范围数据
- [x] 2.4 实现 `update_metadata(symbol, first_date, last_date)` 方法：更新 SQLite 品种元数据
- [x] 2.5 实现 `get_last_date(symbol)` 方法：查询品种最后存储日期
- [x] 2.6 实现 `list_symbols()` 方法：返回所有已管理品种列表

## 3. 数据清洗器 (`src/data/cleaner.py`)

- [x] 3.1 创建 `DataCleaner` 类，实现 `clean(df)` 方法：按顺序执行去重、排序、缺失值处理、列名标准化、类型统一

## 4. 数据下载器 (`src/data/fetcher.py`)

- [x] 4.1 创建 `DataFetcher` 类，封装 akshare API 调用，实现 `fetch(symbol, start_date, end_date)` 方法
- [x] 4.2 实现增量下载逻辑：读取 Storage 的 `last_date`，仅下载缺失日期范围

## 5. 统一查询接口改造 (`src/data/loader.py`)

- [x] 5.1 重构 `DataLoader`：底层从 Storage 读取数据，数据不足时自动触发 Fetcher + Cleaner + Storage 流程
- [x] 5.2 新增 `update(symbol)` 方法：主动触发增量更新
- [x] 5.3 保持 `load(symbol, start_date, end_date)` 签名兼容，确保 `main.py` 无需修改

## 6. 集成与配置

- [x] 6.1 更新 `src/config.py`：加载 `data.storage_dir` 配置并传递给 DataLoader
- [x] 6.2 更新 `src/data/__init__.py`：导出新增模块

## 7. 验证

- [x] 7.1 运行回测，验证新 DataLoader 能正确加载数据并完成回测
- [x] 7.2 验证增量更新：首次全量下载后再次调用只下载新增数据
- [x] 7.3 验证 Parquet 文件和 SQLite 元数据正确生成
- [x] 7.4 更新 README.md：新增数据管理层说明
