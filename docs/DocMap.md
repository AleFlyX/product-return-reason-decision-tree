# 文档地图

本项目主题为“商品退货原因分析”。文档按项目总览、需求架构、数据、模型、服务和交付计划组织。HDFS 与 HBase 是正式交付链路，五个程序员各自的详细任务书是实施入口。

| 文档 | 作用 | 主要负责人 |
| --- | --- | --- |
| [README.md](README.md) | 项目总规范、口径、目录和验收标准 | 项目经理 |
| [requirements.md](requirements.md) | 用户角色、功能需求和验收用例 | 产品经理 |
| [architecture.md](architecture.md) | 分层架构、数据流和边界 | 项目经理 |
| [data-dictionary.md](data-dictionary.md) | 订单、退货和模型字段定义 | 程序员① |
| [data-collection.md](data-collection.md) | 数据采集、清洗和标签构造 | 程序员① |
| [feature-engineering.md](feature-engineering.md) | 编码、划分、泄漏检查和 Pipeline | 程序员② |
| [handoff-programmer-02.md](handoff-programmer-02.md) | 特征工程实施结果、批次产物与给③④的交接说明 | 程序员② |
| [03-商品退货原因分析-决策树.md](03-商品退货原因分析-决策树.md) | 决策树项目方案和答辩重点 | 程序员③ |
| [model.md](model.md) | 训练、评估、规则导出和模型交付 | 程序员③ |
| [backend-hadoop.md](backend-hadoop.md) | FastAPI、HDFS/HBase 数据访问和服务链路 | 程序员④ |
| [api.md](api.md) | REST API 请求、响应和错误契约 | 程序员④ |
| [frontend.md](frontend.md) | Vue 3 页面、图表和状态处理 | 程序员⑤ |
| [development-plan.md](development-plan.md) | 阶段、依赖、里程碑和交付 | 项目经理 |
| [programmer-01-data-pipeline.md](programmer-01-data-pipeline.md) | 订单/退货采集、清洗、标签和 HDFS 入湖 | 程序员① |
| [programmer-02-feature-engineering.md](programmer-02-feature-engineering.md) | 特征工程、数据划分和 HDFS 训练数据 | 程序员② |
| [programmer-03-decision-tree-model.md](programmer-03-decision-tree-model.md) | 决策树训练、评估、规则和模型文件 | 程序员③ |
| [programmer-04-fastapi-hdfs-hbase.md](programmer-04-fastapi-hdfs-hbase.md) | FastAPI、HDFS/HBase 接入和服务化 | 程序员④ |
| [programmer-05-vue3-echarts.md](programmer-05-vue3-echarts.md) | Vue 3、ECharts、交互和联调 | 程序员⑤ |

## 阅读顺序

```text
README
  → requirements + architecture
  → data-dictionary + data-collection
  → feature-engineering
  → 03-商品退货原因分析-决策树 + model
  → programmer-04-fastapi-hdfs-hbase + backend-hadoop + api
  → programmer-05-vue3-echarts + frontend
  → development-plan
```

## 统一关键字

- 订单级样本：一个 `order_id` 对应一行训练数据；
- 标签：`returned`，`1` 为退货，`0` 为未退货；
- 预测特征：`category`、`price`、`is_promotion`、`season`、`freight`；
- 标签泄漏字段：退货发生后才产生的字段，不得进入预测输入；
- 观察窗口：用于判断订单是否退货的约定时间范围。
