## ADDED Requirements

### Requirement: 全量 ETF 基金列表获取
系统必须能够通过 akshare 的 `fund_etf_spot_em()` 接口获取 A 股市场中当前所有可交易 ETF 基金的代码和名称。

#### Scenario: 首次获取 ETF 列表
- **WHEN** 本地不存在 ETF 列表缓存文件
- **THEN** 系统从远程 API 拉取全量 ETF 列表并保存至本地 Parquet 文件

### Requirement: ETF 列表本地缓存与刷新
系统必须将获取到的 ETF 列表保存为本地 Parquet 文件。当用户手动触发刷新时，系统重新从远程获取并覆盖本地缓存。

#### Scenario: 用户手动刷新 ETF 列表
- **WHEN** 用户在轮动池页面点击"刷新 ETF 列表"按钮
- **THEN** 系统从 akshare 重新拉取最新的全量 ETF 列表，覆盖本地缓存文件，并刷新页面展示

#### Scenario: 加载本地缓存
- **WHEN** 本地缓存文件已存在且用户未触发刷新
- **THEN** 系统直接读取本地 Parquet 文件作为 ETF 列表数据源，不发起网络请求
