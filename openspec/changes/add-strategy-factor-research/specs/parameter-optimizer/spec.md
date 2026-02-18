## ADDED Requirements

### Requirement: 网格搜索参数优化 (Grid Search Optimization)
系统必须（SHALL）提供参数优化器，支持对策略参数进行网格搜索。

#### Scenario: 运行网格搜索
- **WHEN** 用户指定策略类、品种、数据范围和参数空间（每个参数的候选值列表）
- **THEN** 系统必须（SHALL）遍历参数空间的笛卡尔积
- **AND** 对每组参数运行完整回测
- **AND** 按目标指标（默认夏普比）排序返回所有参数组合的回测结果

#### Scenario: 参数空间上限
- **WHEN** 参数组合数量超过 `max_combinations`（默认 1000）
- **THEN** 系统必须（SHALL）抛出警告但仍然执行

### Requirement: Walk-forward 交叉验证 (Walk-forward Validation)
系统必须（SHALL）提供 Walk-forward 交叉验证，防止参数过拟合。

#### Scenario: 数据分段
- **WHEN** 用户指定 `n_splits` 段数
- **THEN** 系统必须（SHALL）将数据按时间顺序分为 N 段，每段分为训练期和测试期

#### Scenario: 训练-测试循环
- **WHEN** Walk-forward 验证运行时
- **THEN** 对每段数据：在训练期运行网格搜索找到最优参数，然后在测试期验证该参数的表现
- **AND** 汇总所有测试期的结果作为最终评估

#### Scenario: 过拟合检测
- **WHEN** Walk-forward 验证完成
- **THEN** 系统必须（SHALL）输出训练期和测试期的绩效对比
- **AND** 如果测试期表现显著差于训练期（衰减率 > 50%），输出过拟合警告

### Requirement: 优化器参数可配置 (Optimizer Parameters)
系统必须（SHALL）支持通过构造函数配置优化器参数。

#### Scenario: 参数配置
- **WHEN** 创建 `ParameterOptimizer` 实例
- **THEN** 必须（SHALL）支持指定 `n_splits`（Walk-forward 段数，默认 5）、`train_ratio`（训练期占比，默认 0.7）、`target_metric`（优化目标，默认 "sharpe_ratio"）、`max_combinations`（最大参数组合数，默认 1000）
