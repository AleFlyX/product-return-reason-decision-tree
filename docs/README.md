# 商品退货原因分析系统

## 一、项目基本信息

### 1. 项目定位

本项目是一个“数据处理 + 机器学习建模 + 后端服务 + 前端可视化”的综合实践项目。系统以电商订单和退货记录为数据基础，构造订单是否退货的标签，使用决策树分析影响退货的主要因素，并将预测结果和规则通过 Web 页面展示。

决策树适合本项目的原因是：

- 结果容易解释，可以还原为“如果……那么……”的业务规则；
- 可以同时处理数值特征和类别特征；
- 可以输出特征重要性，支持答辩和业务分析；
- 通过限制树深度、叶节点最小样本数等参数控制过拟合。

### 2. 技术栈

| 模块 | 技术 |
| --- | --- |
| 数据处理 | Python、Pandas、NumPy |
| 特征工程 | scikit-learn `ColumnTransformer`、`OneHotEncoder` |
| 机器学习 | scikit-learn `DecisionTreeClassifier` |
| 数据存储 | HDFS 必接入；HBase 必接入；Hive 可选；CSV/TSV 仅作本地开发交换格式 |
| 后端 | Python、FastAPI、Pydantic、Uvicorn |
| 前端 | Vue 3、Vite、Vue Router、Axios、ECharts |
| 工程协作 | Git、GitHub |

### 3. 项目目标

1. 建立订单与退货数据的采集、清洗、关联和质量检查流程。
2. 训练可复现的退货二分类决策树。
3. 输出准确率、精确率、召回率、F1、混淆矩阵和特征重要性。
4. 将决策树规则转换为前端可展示的文本或 JSON。
5. 使用 FastAPI 提供概览、预测、指标、特征重要性和规则接口。
6. 使用 Vue 3 + ECharts 展示退货率、类别对比和模型分析结果。
7. 完成 HDFS 批处理链路和 HBase 在线查询链路的部署、联调和验收。

## 二、业务边界与标签口径

### 1. 预测时点

预测发生在订单提交后、退货发生前。因此模型输入只能使用下单时已经知道的字段，例如商品类目、商品价格、是否促销、季节和运费。

以下字段只能用于生成标签或离线分析，不能作为预测特征：

- `return_reason`：退货原因；
- `return_date`：退货发生时间；
- `refund_amount`：退款金额；
- `return_status`：退货流程状态；
- 任何由客服、仓储或售后处理产生的字段。

### 2. 标签定义

以订单表为主表，将退货表按 `order_id` 关联：

```text
returned = 1：在退货观察窗口内存在有效退货记录
returned = 0：观察窗口结束前没有有效退货记录
```

本项目默认观察窗口为 `order_time` 起 30 个自然日。有效退货记录是状态映射为“已确认退货”的记录；原始状态必须通过数据源映射表归一化，明确拒绝、取消和测试记录不计入标签。若最终数据源的业务定义不同，应在清洗报告中记录覆盖默认规则的配置。

同一个订单多次退货记录仍只生成一条订单样本。观察窗口、状态映射和去重规则必须记录在清洗报告中。

## 三、系统总体流程

```text
订单表 + 退货表
        ↓
原始数据 data/raw/
        ↓
字段统一、去重、缺失和异常处理
        ↓
标准数据 data/clean/
        ↓
订单与退货关联，生成 returned 标签
        ↓
One-Hot 编码、分层划分训练集和测试集
        ↓
决策树训练、评估、规则导出
        ↓
模型文件、指标 JSON、规则 JSON
        ↓
FastAPI REST API
        ↓
Vue 3 + ECharts 分析页面
```

HDFS 和 HBase 是本项目的必需基础设施。HDFS 负责原始数据、清洗数据、训练集和模型产物的批量存储；HBase 负责订单级明细、标签、预测结果和服务元数据的在线查询。Hive 可以作为统计分析层，但不能替代 HDFS 或 HBase。没有大数据组件时只能进行本地开发，不能视为最终验收通过。

## 四、核心数据约定

| 字段 | 类型 | 含义 | 是否用于预测 |
| --- | --- | --- | --- |
| `order_id` | string | 订单唯一标识 | 否 |
| `category` | string | 商品类目 | 是 |
| `price` | float | 商品成交单价，元 | 是 |
| `is_promotion` | int | 是否促销，1/0 | 是 |
| `season` | string | 下单季节 | 是 |
| `freight` | float | 运费，元 | 是 |
| `returned` | int | 是否退货，1/0 | 标签 |

完整字段、单位、校验范围和来源见 [`data-dictionary.md`](data-dictionary.md)。

## 五、主要功能

### 1. 数据概览

展示订单数、退货数、整体退货率、商品类目数、平均价格和数据更新时间。

### 2. 退货预测

用户输入订单在预测时点可获得的字段，调用 `POST /api/returns/predict`，返回退货概率、预测类别和模型版本。

### 3. 退货分析

展示各商品类目退货率、促销与非促销退货率、价格区间退货率及样本量。

### 4. 模型分析

展示准确率、精确率、召回率、F1、混淆矩阵、特征重要性和决策树规则。

## 六、计划目录结构

```text
product-return-analysis/
├── README.md
├── docs/
│   ├── README.md
│   ├── DocMap.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── api.md
│   ├── data-dictionary.md
│   ├── development-plan.md
│   ├── feature-engineering.md
│   ├── model.md
│   ├── backend-hadoop.md
│   ├── frontend.md
│   ├── data-collection.md
│   ├── programmer-01-data-pipeline.md
│   ├── programmer-02-feature-engineering.md
│   ├── programmer-03-decision-tree-model.md
│   ├── programmer-04-fastapi-hdfs-hbase.md
│   ├── programmer-05-vue3-echarts.md
│   └── 03-商品退货原因分析-决策树.md
├── data/
│   ├── raw/
│   │   ├── orders_raw.csv
│   │   └── returns_raw.csv
│   ├── clean/
│   │   ├── orders_clean.csv
│   │   ├── returns_clean.csv
│   │   └── return_model.csv
│   └── reports/
│       └── cleaning_report.json
├── scripts/
│   ├── collect_data.py
│   └── clean_return_data.py
├── preprocessing/
│   └── feature_engineering.py
├── model/
│   ├── train.py
│   ├── evaluate.py
│   └── saved/
├── backend/
│   └── app/
├── frontend/
│   └── src/
├── hadoop/
│   ├── hdfs/
│   ├── hive/
│   └── hbase/
└── tests/
```

当前仓库仍以文档为主，上述代码目录是实现计划，不代表文件已经全部创建。

## 七、团队职责

| 角色 | 主要职责 |
| --- | --- |
| 总经理 | 项目方向、成果验收和最终汇报 |
| 项目经理 | 计划、任务分配、进度和版本整合 |
| 产品经理 | 用户场景、需求、页面流程和产品验收 |
| 程序员① | 订单/退货数据采集、清洗和标签构造 |
| 程序员② | 特征工程、数据集划分和预处理 Pipeline |
| 程序员③ | 决策树训练、评估、规则和模型文件 |
| 程序员④ | FastAPI、HDFS/HBase 数据访问和可选 Hive |
| 程序员⑤ | Vue 3、ECharts、页面交互和系统展示 |

## 八、验收标准

- [ ] 订单表和退货表字段、编码和观察窗口有明确说明。
- [ ] 清洗过程可重复执行，并输出清洗前后数量和异常处理报告。
- [ ] `returned` 标签可由订单与退货表按 `order_id` 重建。
- [ ] 模型训练固定随机种子，并使用分层划分保持类别比例。
- [ ] 测试集输出准确率、精确率、召回率和 F1。
- [ ] 能输出特征重要性和至少一组可读决策树规则。
- [ ] FastAPI 能返回健康检查、概览、预测、指标和规则。
- [ ] 前端能处理加载中、空数据、接口失败和模型未加载状态。
- [ ] 未将退货发生后的字段泄漏到预测特征。
- [ ] 原始、清洗、训练和模型文件已写入 HDFS，并能通过路径或版本追溯。
- [ ] 订单级明细、`returned` 标签和预测结果已写入 HBase，并能按 `order_id` 查询。
- [ ] FastAPI 在 HDFS/HBase 可用时走正式数据链路，健康检查能报告依赖状态。
- [ ] Hive 若启用，只作为分析查询层，不替代 HDFS 或 HBase。

## 九、Git 规范

Git 分支、Commit 信息和模块协作规则已独立维护在 [`skill/git-conventions/SKILL.md`](../skill/git-conventions/SKILL.md)，提交或跨模块修改前请遵循该 skill。

## 十、当前已确定事项

- [x] 项目主题为商品退货原因分析。
- [x] 模型使用 scikit-learn 决策树分类器。
- [x] 标签字段使用 `returned`，取值为 0/1。
- [x] 后端使用 FastAPI。
- [x] 前端使用 Vue 3 + ECharts。
- [x] 预测特征不包含退货发生后的字段。
- [ ] 最终数据源和脱敏方式。
- [x] HDFS 作为批处理主存储。
- [x] HBase 作为在线查询和服务元数据存储。
- [ ] 是否增加 Hive 分析层。
