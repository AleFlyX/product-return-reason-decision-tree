# FastAPI、HDFS 与 HBase 集成说明

## 一、集成结论

本项目要求正式接入 HDFS 和 HBase：

- HDFS：原始数据、清洗数据、特征数据、模型文件和报告的批量存储；
- HBase：订单级明细、退货标签、预测记录和模型注册信息的在线存储；
- FastAPI：唯一对前端暴露的数据服务边界；
- Hive：可选分析层，可以读取 HDFS 数据做聚合，但不替代 HDFS/HBase。

CSV 只用于本地开发和故障排查，不能作为正式环境的唯一数据源。

## 二、后端目录

```text
backend/app/
├── main.py
├── schemas.py
├── core/
│   ├── config.py
│   ├── health.py
│   ├── logging.py
│   └── errors.py
├── repositories/
│   ├── hdfs_repository.py
│   ├── hbase_repository.py
│   └── csv_fallback_repository.py
├── services/
│   ├── model_service.py
│   ├── order_service.py
│   ├── statistics_service.py
│   └── prediction_service.py
└── routers/
    ├── health.py
    ├── stats.py
    ├── orders.py
    └── model.py
```

路由层不能直接拼 HDFS 路径、创建 HBase 连接或读取模型文件。路径、表名和版本选择必须由配置与 service 层管理。

## 三、HDFS 目录规范

```text
/project/product-return/
├── raw/
│   ├── orders/batch_id=<batch_id>/
│   └── returns/batch_id=<batch_id>/
├── clean/
│   ├── orders/batch_id=<batch_id>/
│   ├── returns/batch_id=<batch_id>/
│   └── return_model/batch_id=<batch_id>/
├── feature/
│   ├── train/data_version=<data_version>/
│   ├── test/data_version=<data_version>/
│   └── schema/data_version=<data_version>/
├── model/
│   └── model_name=decision-tree/model_version=<model_version>/
└── reports/
    └── batch_id=<batch_id>/
```

每个批次目录至少保留：

```text
_SUCCESS
manifest.json
data files
```

`manifest.json` 要记录文件数量、行数、批次号、数据版本、生成时间和校验摘要。已经验收的目录禁止覆盖。

## 四、HBase 表设计

### 1. 订单表：`pr_orders`

```text
create 'pr_orders', 'o', 'r', 'meta'
```

| RowKey | 列族 | 列 |
| --- | --- | --- |
| `order_id` | `o` | `category`、`price`、`is_promotion`、`season`、`freight`、`order_time` |
| `order_id` | `r` | `returned`、`return_count`、`last_return_date` |
| `order_id` | `meta` | `batch_id`、`data_version`、`updated_at` |

### 2. 模型注册表：`pr_model_registry`

```text
create 'pr_model_registry', 'm'
```

RowKey：

```text
decision-tree#<model_version>
decision-tree#CURRENT
```

列族 `m` 至少保存：

```text
hdfs_path
metrics_path
features_path
rules_path
data_version
status
created_at
```

只有 `status=ready` 的模型允许被预测接口加载。

### 3. 预测结果表：`pr_predictions`

```text
create 'pr_predictions', 'p', 'i'
```

RowKey：

```text
<model_version>#<request_id>
```

列族 `p` 保存预测结果，列族 `i` 保存脱敏后的输入摘要和可选 `order_id`。

## 五、配置约定

```text
APP_ENV=production
DATA_BACKEND=hdfs_hbase
HDFS_URL=hdfs://namenode:8020
HDFS_ROOT=/project/product-return
HBASE_HOST=hbase
HBASE_PORT=9090
HBASE_NAMESPACE=product_return
HBASE_ORDERS_TABLE=pr_orders
HBASE_MODEL_TABLE=pr_model_registry
HBASE_PREDICTIONS_TABLE=pr_predictions
MODEL_NAME=decision-tree
MODEL_VERSION=dt-20260910-001
```

本地开发可以使用：

```text
DATA_BACKEND=csv_fallback
```

但健康检查必须返回 `degraded=true`。正式验收必须使用 `hdfs_hbase`。

## 六、FastAPI 数据来源

| 接口 | 正式数据来源 |
| --- | --- |
| `/api/health` | HDFS、HBase、模型注册表 |
| `/api/stats/overview` | HBase 预聚合结果或 HDFS 报告 |
| `/api/stats/by-category` | HBase 统计结果或 HDFS 聚合结果 |
| `/api/orders` | HBase `pr_orders` |
| `/api/returns/predict` | HBase 当前模型注册 + HDFS 模型文件 |
| `/api/model/metrics` | HDFS 指标 JSON + HBase 模型版本 |
| `/api/model/features` | HDFS 特征重要性 JSON |
| `/api/model/rules` | HDFS 规则 JSON |

## 七、健康检查

`GET /api/health` 必须返回：

```json
{
  "status": "ok",
  "service": "product-return-analysis-api",
  "model_loaded": true,
  "model_version": "dt-20260910-001",
  "dependencies": {
    "hdfs": {
      "status": "ok",
      "root": "/project/product-return"
    },
    "hbase": {
      "status": "ok",
      "tables": [
        "pr_orders",
        "pr_model_registry",
        "pr_predictions"
      ]
    }
  },
  "degraded": false
}
```

HDFS 或 HBase 失败时，相关接口返回 503，不能返回空数组伪装成“没有数据”。

## 八、启动与联调

```text
启动 HDFS
  → 创建项目目录和权限
  → 上传原始、清洗、特征和模型文件
  → 启动 HBase
  → 创建三张业务表
  → 写入订单和模型注册信息
  → 启动 FastAPI
  → 访问 /api/health
  → 再联调订单、统计、预测和模型接口
```

## 九、后端验收

- [ ] HDFS 读写集成测试通过。
- [ ] HBase 建表、写入、按 RowKey 查询测试通过。
- [ ] 当前模型只能从 HBase 注册表选择。
- [ ] 模型文件从 HDFS 加载。
- [ ] 健康检查能区分 HDFS、HBase、模型和降级状态。
- [ ] 依赖失败时不会返回伪造空数据。
- [ ] API 响应字段与 [`api.md`](api.md) 一致。
