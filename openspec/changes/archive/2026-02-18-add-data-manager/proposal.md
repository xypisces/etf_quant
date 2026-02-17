## Why

当前系统的数据管理方式存在明显短板：每次回测都依赖按日期范围命名的 CSV 缓存文件，无法增量更新、无法管理多品种元数据、无法保证数据质量。随着策略数量增加和数据规模扩大，需要一个完整的数据管理层来支撑后续的多品种回测、因子研究和实时行情对接。

## What Changes

- **新增数据下载器** (`src/data/fetcher.py`)：封装 akshare API 调用，支持增量数据更新（只下载缺失的日期范围），取代 DataLoader 中内嵌的 API 调用逻辑
- **新增数据清洗器** (`src/data/cleaner.py`)：标准化列名、处理缺失值/重复行/异常值、统一数值类型，确保数据质量
- **新增本地存储引擎** (`src/data/storage.py`)：使用 SQLite 管理品种元数据（代码、名称、最后更新日期），使用 Parquet 格式存储行情数据（列式存储、高压缩率）
- **改造现有 DataLoader** (`src/data/loader.py`)：升级为统一查询接口，底层从 storage 读取数据，不再直接操作 CSV/API
- **新增配置项**：在 `config.yaml` 中增加 `data.storage_dir`、`data.db_path` 等配置

## Capabilities

### New Capabilities
- `data-fetcher`：数据下载与增量更新能力
- `data-cleaner`：数据清洗与质量保证能力
- `data-storage`：本地持久化存储能力（SQLite 元数据 + Parquet 行情）

### Modified Capabilities
- `data-loader`：从 CSV 缓存模式升级为统一查询接口，底层对接 storage 层

## Impact

- **代码影响**：`src/data/` 目录下新增 3 个模块，改造 `loader.py`
- **配置影响**：`config.yaml` 新增存储相关配置
- **依赖影响**：新增 `pyarrow` 依赖（Parquet 读写）；SQLite 为 Python 内置，无需额外安装
- **兼容性**：`DataLoader.load()` 接口签名保持不变，对 `main.py` 和回测引擎透明
- **数据迁移**：现有 CSV 缓存可继续使用，新系统首次运行时可选择导入
