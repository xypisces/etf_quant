## ADDED Requirements

### Requirement: 统一数据加载接口 (Unified Data Loading Interface)
系统必须（SHALL）提供统一的数据加载接口，支持从本地 CSV 缓存或 akshare API 获取 ETF 历史数据，返回标准化的 OHLCV DataFrame。

#### Scenario: 从 CSV 缓存加载数据
- **WHEN** 用户指定标的代码（如 `510300`）和起止日期调用数据加载函数，且 `csv/` 目录下存在对应缓存文件
- **THEN** 系统必须（SHALL）直接读取 CSV 文件并返回包含 `date`, `open`, `high`, `low`, `close`, `volume` 列的 DataFrame
- **AND** 数据必须（MUST）按日期升序排列

#### Scenario: 从 akshare API 获取并缓存数据
- **WHEN** 用户指定标的代码和起止日期调用数据加载函数，且本地无缓存
- **THEN** 系统必须（SHALL）调用 akshare API 获取数据
- **AND** 将原始列名标准化为 `date`, `open`, `high`, `low`, `close`, `volume`
- **AND** 将数据保存到 `csv/` 目录作为缓存
- **AND** 返回标准化的 DataFrame

#### Scenario: 数据获取失败处理
- **WHEN** akshare API 调用失败（网络错误、无效代码等）
- **THEN** 系统必须（SHALL）捕获异常并返回空 DataFrame
- **AND** 在控制台输出错误信息

### Requirement: 数值类型保证 (Numeric Type Guarantee)
所有 OHLCV 数值列必须（MUST）为 `float` 类型，确保下游计算不会因为类型问题出错。

#### Scenario: 类型转换
- **WHEN** 从任何数据源加载数据后
- **THEN** `open`, `high`, `low`, `close`, `volume` 列必须（MUST）为 `float64` 类型
