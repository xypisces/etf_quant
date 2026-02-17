## ADDED Requirements

### Requirement: 数据下载 (Data Fetching)
系统必须（SHALL）提供数据下载器，支持从 akshare API 获取 ETF 历史日线数据。

#### Scenario: 全量下载
- **WHEN** 品种在本地无任何历史数据
- **AND** 用户调用下载功能指定品种代码
- **THEN** 系统必须（SHALL）从 akshare 下载该品种的全部可用日线数据
- **AND** 返回标准化的 DataFrame（含 date, open, high, low, close, volume）

#### Scenario: 增量更新
- **WHEN** 品种在本地已有历史数据
- **AND** 最后已存储日期为 `last_date`
- **THEN** 系统必须（SHALL）仅下载 `last_date + 1` 至今日的新增数据
- **AND** 将新数据与现有数据合并

#### Scenario: 下载失败处理
- **WHEN** akshare API 调用失败（网络错误、无效代码等）
- **THEN** 系统必须（SHALL）抛出明确异常，包含错误原因
- **AND** 不影响已存储的数据

#### Scenario: 数据已是最新
- **WHEN** 品种的最后存储日期等于最近一个交易日
- **THEN** 系统必须（SHALL）跳过下载并返回空 DataFrame
