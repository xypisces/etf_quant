## MODIFIED Requirements

### Requirement: 统一数据加载接口 (Unified Data Loading Interface)
系统必须（SHALL）提供统一的数据加载接口，底层对接 Storage 层读取数据，并在数据不足时自动触发增量下载。

#### Scenario: 从本地存储加载数据
- **WHEN** 用户指定标的代码和起止日期调用 `load()` 方法
- **AND** Storage 中已有该品种在指定范围内的完整行情数据
- **THEN** 系统必须（SHALL）从 Parquet 存储中读取数据并返回标准化 DataFrame
- **AND** 数据必须（MUST）按日期升序排列

#### Scenario: 数据不足时自动增量下载
- **WHEN** Storage 中该品种的数据不覆盖请求的日期范围
- **THEN** 系统必须（SHALL）自动调用 Fetcher 下载缺失数据
- **AND** 经 Cleaner 清洗后存入 Storage
- **AND** 返回完整的请求范围数据

#### Scenario: 数据获取失败处理
- **WHEN** 增量下载失败
- **THEN** 系统必须（SHALL）返回已有的部分数据（如有）
- **AND** 在控制台输出警告信息

#### Scenario: 主动更新接口
- **WHEN** 用户调用 `update(symbol)` 方法
- **THEN** 系统必须（SHALL）触发该品种的增量数据更新
- **AND** 返回新增的数据行数

### Requirement: 数值类型保证 (Numeric Type Guarantee)
所有 OHLCV 数值列必须（MUST）为 `float64` 类型，确保下游计算不会因为类型问题出错。

#### Scenario: 类型转换
- **WHEN** 从任何数据源加载数据后
- **THEN** `open`, `high`, `low`, `close`, `volume` 列必须（MUST）为 `float64` 类型
