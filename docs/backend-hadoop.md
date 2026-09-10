# 后端与可选大数据链路

## 一、后端职责

程序员④负责：

- 加载模型 Pipeline 和模型元数据；
- 提供订单统计、类目分析和分页查询；
- 校验退货预测请求；
- 返回模型指标、特征重要性和规则；
- 提供本地 CSV 与可选大数据存储的适配。

接口详细契约见 [`api.md`](api.md)。

## 二、FastAPI 分层

```text
backend/app/
├── main.py
├── schemas.py
├── routers/
│   ├── health.py
│   ├── stats.py
│   ├── orders.py
│   └── model.py
├── services/
│   ├── prediction_service.py
│   ├── statistics_service.py
│   └── model_service.py
├── repositories/
│   ├── csv_repository.py
│   └── bigdata_repository.py
└── core/
    ├── config.py
    ├── errors.py
    └── logging.py
```

路由只负责 HTTP 参数和响应，业务逻辑放在 service，文件或大数据访问放在 repository。

## 三、本地运行路径

默认使用：

```text
data/clean/return_model.csv
model/saved/return_decision_tree.joblib
model/saved/metrics.json
model/saved/feature_importance.json
model/saved/rules.json
```

没有 HDFS、Hive 或 HBase 时，服务必须仍能启动。文件不存在或模型未加载时，健康检查应明确返回状态，预测接口返回 503。

## 四、HDFS/Hive/HBase 可选扩展

### 1. HDFS

适合保存清洗后的大文件和训练输入：

```text
/project/product-return/raw/orders/
/project/product-return/raw/returns/
/project/product-return/clean/return_model.tsv
/project/product-return/reports/
```

### 2. Hive

可以建立订单和退货外部表，用于统计：

```sql
SELECT category,
       COUNT(*) AS sample_count,
       SUM(returned) AS returned_count,
       AVG(returned) AS return_rate
FROM return_model
GROUP BY category;
```

实际建表时要确认分隔符、字符编码和日期字段类型。

### 3. HBase

适合按 `order_id` 查询订单级明细和标签，建议：

```text
表：product_return_orders
RowKey：order_id
列族：order
列族：label
```

不建议把模型训练逻辑直接写入 HBase 访问代码；训练仍通过批量数据集完成。

## 五、配置约定

```text
DATA_BACKEND=csv
ORDERS_PATH=data/clean/orders_clean.csv
RETURNS_PATH=data/clean/returns_clean.csv
MODEL_PATH=model/saved/return_decision_tree.joblib
MODEL_VERSION=local
```

启用大数据链路时切换 `DATA_BACKEND`，不能改变 API 返回字段。

## 六、后端验收

- [ ] `/api/health` 能说明模型是否加载。
- [ ] CSV 模式无大数据环境可独立运行。
- [ ] 预测请求能复用训练时的完整 Pipeline。
- [ ] 非法数值和空类别返回 4xx。
- [ ] 模型未加载返回 503。
- [ ] 大数据适配器不改变业务层和 API 契约。
