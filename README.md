# 商品退货原因分析系统

本项目使用订单数据、商品属性和退货记录，分析哪些订单更容易发生退货，并使用可解释的决策树模型输出退货预测、特征重要性和可读的叶子规则。

项目当前以文档和接口契约为主，后续实现目录、数据口径和验收标准统一记录在 [`docs/README.md`](docs/README.md)。

## 文档入口

- [项目总览](docs/README.md)
- [项目需求](docs/requirements.md)
- [系统架构](docs/architecture.md)
- [接口说明](docs/api.md)
- [数据字典](docs/data-dictionary.md)
- [决策树专题方案](docs/03-商品退货原因分析-决策树.md)
- [五个程序员岗位详细交接文档](docs/DocMap.md)

## 当前模型

- 任务：二分类，预测订单是否退货
- 模型：`sklearn.tree.DecisionTreeClassifier`
- 标签：`returned`，`1` 表示退货，`0` 表示未退货
- 主要特征：`category`、`price`、`is_promotion`、`season`、`freight`
- 后端：FastAPI
- 前端：Vue 3 + ECharts
- HDFS：批处理数据主存储，项目必接入
- HBase：订单级在线查询和服务元数据存储，项目必接入
- Hive：可选分析层，不替代 HDFS 和 HBase
