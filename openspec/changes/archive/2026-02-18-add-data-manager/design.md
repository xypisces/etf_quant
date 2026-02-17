## Context

当前系统使用 `DataLoader` 类（`src/data/loader.py`）管理数据，采用 CSV 文件作为缓存，按 `{symbol}_{start}_{end}.csv` 格式存储。该方案存在以下痛点：

1. **无增量更新**：每次修改日期范围都会重新下载全量数据
2. **无元数据管理**：无法查询已缓存的品种列表和时间覆盖范围
3. **无数据质量保证**：缺少缺失值/重复行/异常值检测
4. **CSV 效率低**：相比 Parquet，CSV 读写速度慢、占用空间大
5. **存储与获取耦合**：API 调用、列名映射、缓存逻辑全部混在一个类中

## Goals / Non-Goals

**Goals:**
- 将数据管理拆分为 fetcher → cleaner → storage → loader 四层职责清晰的模块
- 实现增量数据更新，避免重复下载
- 使用 SQLite 管理品种元数据，Parquet 存储行情数据
- 保持 `DataLoader.load()` 接口兼容，对上游调用者透明
- 支持多品种数据管理

**Non-Goals:**
- 不支持分钟级或 Tick 级数据（仅日线）
- 不引入异步/并发下载（保持简单）
- 不做数据重采样（日线→周线），留给后续阶段
- 不迁移旧 CSV 缓存（可并存）

## Decisions

### 1. 数据流水线架构：四层分离

```
Fetcher (下载) → Cleaner (清洗) → Storage (存储) → Loader (查询)
```

**理由**：单一职责原则。每层可独立测试和替换。Fetcher 只负责从 akshare 拉数据，不关心存储格式；Cleaner 只做数据质量保证；Storage 只管持久化读写；Loader 是面向用户的统一接口。

**替代方案**：在现有 `DataLoader` 中直接加功能 → 违反不做改理由：会导致类越来越膨胀，难以维护。

### 2. 存储方案：SQLite（元数据）+ Parquet（行情）

**理由**：
- SQLite：零部署、Python 内置、适合结构化元数据查询（如品种列表、最后更新日期）
- Parquet：列式存储、高压缩率（比 CSV 小 5-10x）、pandas 原生支持、读取速度快

**替代方案**：
- 纯 CSV → 无法做元数据查询，性能差
- 纯 SQLite → 不适合大规模行情数据的列式分析
- MySQL/PostgreSQL → 个人项目过重，需要额外部署

### 3. Fetcher 增量更新策略

从 SQLite 元数据中读取品种的 `last_date`（最后已存储日期），只下载 `last_date + 1` 到 `today` 的数据。首次下载时全量获取。

**理由**：最简单有效的增量方案，无需复杂的变更检测。

### 4. Cleaner 清洗流水线

按顺序执行：去重 → 排序 → 缺失值处理 → 列名标准化 → 类型统一 → 异常值检测。

异常值处理策略：标记但不删除（设置 `is_anomaly` 标志列），让用户自行决定是否过滤。

### 5. Loader 接口兼容

保持 `DataLoader.load(symbol, start_date, end_date) -> DataFrame` 签名不变。内部逻辑改为：从 Storage 查询 → 如果数据不足则调用 Fetcher 增量下载 → Cleaner 清洗 → Storage 存储 → 返回结果。

同时新增 `DataLoader.update(symbol)` 方法用于主动触发增量更新。

### 6. 目录结构

```
data/
├── market.db        # SQLite 数据库（元数据）
└── parquet/
    ├── 510300.parquet
    ├── 600111.parquet
    └── ...
```

默认存储在项目根目录的 `data/` 下，可通过 `config.yaml` 的 `data.storage_dir` 自定义。

## Risks / Trade-offs

- **[Parquet 依赖]** → 需要新增 `pyarrow` 依赖（约 80MB）。缓解：这是 pandas 生态标准组件，几乎所有数据项目都用
- **[SQLite 并发]** → SQLite 单写者限制。缓解：个人系统无并发写入需求，不是问题
- **[akshare API 变更]** → akshare 接口可能更新。缓解：Fetcher 层隔离了 API 调用，变更只需改一处
- **[旧缓存兼容]** → 旧 CSV 缓存不会自动迁移。缓解：旧缓存可继续使用，新旧系统并存
