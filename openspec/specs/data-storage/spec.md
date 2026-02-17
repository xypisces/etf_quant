## ADDED Requirements

### Requirement: 行情数据持久化 (Market Data Persistence)
系统必须（SHALL）使用 Parquet 格式存储行情数据，提供高效的读写能力。

#### Scenario: 保存行情数据
- **WHEN** 清洗后的 DataFrame 需要持久化
- **THEN** 系统必须（SHALL）将数据以 Parquet 格式保存到 `{storage_dir}/parquet/{symbol}.parquet`
- **AND** 如果文件已存在，将新数据追加合并后覆写（去重保留最新）

#### Scenario: 读取行情数据
- **WHEN** 用户查询指定品种在指定日期范围内的行情数据
- **THEN** 系统必须（SHALL）从 Parquet 文件中读取数据
- **AND** 按日期范围过滤后返回 DataFrame
- **AND** 如果文件不存在，返回空 DataFrame

#### Scenario: 存储目录可配置
- **WHEN** 用户在 config.yaml 中指定 `data.storage_dir`
- **THEN** 系统必须（SHALL）使用指定目录存储数据文件

### Requirement: 品种元数据管理 (Symbol Metadata Management)
系统必须（SHALL）使用 SQLite 管理品种元数据信息。

#### Scenario: 记录品种信息
- **WHEN** 品种数据首次下载或更新后
- **THEN** 系统必须（SHALL）在 SQLite 中记录：品种代码(symbol)、品种名称(name)、数据起始日期(first_date)、数据结束日期(last_date)、最后更新时间(updated_at)

#### Scenario: 查询品种列表
- **WHEN** 用户请求已管理的品种列表
- **THEN** 系统必须（SHALL）返回所有已存储品种的代码和元数据信息

#### Scenario: 查询增量起点
- **WHEN** Fetcher 需要判断增量下载的起始日期
- **THEN** 系统必须（SHALL）返回该品种的 `last_date`
- **AND** 如果品种不存在则返回 None
