## ADDED Requirements

### Requirement: 数据清洗流水线 (Data Cleaning Pipeline)
系统必须（SHALL）提供数据清洗器，对原始行情数据执行标准化清洗流程。

#### Scenario: 去除重复行
- **WHEN** 数据中存在相同日期的重复记录
- **THEN** 系统必须（SHALL）按日期去重，保留最后出现的记录

#### Scenario: 日期排序
- **WHEN** 数据未按日期升序排列
- **THEN** 系统必须（SHALL）按日期升序排序

#### Scenario: 缺失值处理
- **WHEN** OHLCV 中存在缺失值（NaN）
- **THEN** 系统必须（SHALL）使用前值填充（forward fill）处理缺失数据
- **AND** 对于首行无前值的缺失值，使用后值填充（backward fill）

#### Scenario: 列名标准化
- **WHEN** 原始数据的列名不符合标准（如中文列名 "日期"、"开盘"）
- **THEN** 系统必须（SHALL）将列名映射为标准名：date, open, high, low, close, volume

#### Scenario: 数值类型统一
- **WHEN** OHLCV 数据列不是 float64 类型
- **THEN** 系统必须（SHALL）将 open, high, low, close, volume 列转换为 float64
