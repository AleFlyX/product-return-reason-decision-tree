# 程序员④：FastAPI、HDFS/HBase 数据访问和服务化

## 一、岗位目标

程序员④负责把 HDFS、HBase 和模型文件接入 FastAPI，为前端提供统一 API。HDFS 和 HBase 是正式环境必需依赖，不允许在生产配置中静默退回内存假数据。

```text
HDFS：批量文件、模型产物、报告
HBase：订单明细、returned 标签、预测结果、模型注册
FastAPI：统一校验、聚合、预测和健康检查
```

## 二、服务目录

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

路由层不能直接拼 HDFS 路径、写 HBase 连接代码或读取模型文件；这些逻辑必须在 repository/service 层完成。

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

服务端只读取已登记的 `data_version` 和 `model_version`，不能默认读取目录下最新但未验收的文件。

## 四、HBase 表设计

### 1. 订单表：`pr_orders`

| 项目 | 约定 |
| --- | --- |
| RowKey | `order_id` |
| 列族 `o` | `category`、`price`、`is_promotion`、`season`、`freight`、`order_time` |
| 列族 `r` | `returned`、`return_count`、`last_return_date` |
| 列族 `meta` | `batch_id`、`data_version`、`updated_at` |

### 2. 模型注册表：`pr_model_registry`

| 项目 | 约定 |
| --- | --- |
| RowKey | `decision-tree#<model_version>` |
| 列族 `m` | `hdfs_path`、`metrics_path`、`rules_path`、`data_version`、`status` |
| 当前指针 | `decision-tree#CURRENT` |

只有 `status=ready` 的模型可以成为当前模型。

### 3. 统计表：`pr_stats`

```text
create 'pr_stats', 's', 'meta'
```

统计批处理由程序员④负责：从 HDFS 清洗区或报告读取指定 `data_version`，计算聚合结果并写入 HBase。API 只读取已登记版本的统计行，不在请求线程中扫描 HDFS 全量数据。

| RowKey | 用途 |
| --- | --- |
| `overview` | 全局订单数、退货数、退货率、平均价格、平均运费 |
| `category#<category>` | 类目样本量、退货数、退货率 |
| `promotion#0` / `promotion#1` | 促销状态样本量、退货数、退货率 |
| `price_range#<range>` | 价格区间样本量、退货数、退货率 |

列族 `s` 保存统计值，列族 `meta` 保存 `data_version`、`updated_at` 和统计口径。

### 4. 预测结果表：`pr_predictions`

| 项目 | 约定 |
| --- | --- |
| RowKey | `<model_version>#<request_id>` |
| 列族 `p` | `predicted_returned`、`return_probability`、`created_at` |
| 列族 `i` | 输入字段 JSON 或脱敏摘要 |

预测请求若关联已有订单，可在列族 `i` 写入 `order_id`，但不能存储不必要的个人敏感信息。

## 五、配置

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
HBASE_STATS_TABLE=pr_stats
HBASE_PREDICTIONS_TABLE=pr_predictions
MODEL_NAME=decision-tree
MODEL_VERSION=dt-20260910-001
```

本地开发可以设置 `DATA_BACKEND=csv_fallback`，但 `/api/health` 必须明确返回 `degraded=true`，正式验收配置必须是 `hdfs_hbase`。

## 六、健康检查

`GET /api/health` 至少返回：

```json
{
  "status": "ok",
  "service": "product-return-analysis-api",
  "model_loaded": true,
  "model_version": "dt-20260910-001",
  "dependencies": {
    "hdfs": {"status": "ok", "root": "/project/product-return"},
    "hbase": {"status": "ok", "tables": ["pr_orders", "pr_model_registry", "pr_stats", "pr_predictions"]}
  },
  "degraded": false
}
```

HDFS 或 HBase 连接失败时：

- 正式环境健康检查不能返回完整 `ok`；
- 订单查询、模型查询或预测接口返回明确 503；
- 不能用空列表伪装成没有数据。

## 七、接口实现责任

| 接口 | 数据来源 |
| --- | --- |
| `/api/stats/overview` | HBase `pr_stats`, RowKey `overview` |
| `/api/stats/by-category` | HBase `pr_stats`, RowKey 前缀 `category#` |
| `/api/stats/by-promotion` | HBase `pr_stats`, RowKey 前缀 `promotion#` |
| `/api/stats/by-price-range` | HBase `pr_stats`, RowKey 前缀 `price_range#` |
| `/api/orders` | HBase `pr_orders` |
| `/api/returns/predict` | HBase 模型注册 + HDFS 模型文件 |
| `/api/model/metrics` | HDFS 指标 JSON或 HBase 模型注册 |
| `/api/model/features` | HDFS 特征重要性 JSON |
| `/api/model/rules` | HDFS 规则 JSON |

## 八、启动与联调顺序

```text
启动 HDFS
  → 检查项目目录和权限
  → 启动 HBase
  → 创建 pr_orders/pr_model_registry/pr_stats/pr_predictions
  → 写入订单数据和模型注册信息
  → 启动 FastAPI
  → 访问 /api/health
  → 再联调预测和订单查询
```

## 九、验收清单

- [ ] FastAPI 正式配置使用 HDFS/HBase。
- [ ] HDFS 读写和 HBase 读写均有集成测试。
- [ ] 订单可按 `order_id` 查询。
- [ ] 当前模型只能从 HBase 注册表选择。
- [ ] 模型文件从 HDFS 加载。
- [ ] 健康检查能区分 HDFS、HBase、模型和降级状态。
- [ ] HDFS/HBase 失败时不会返回伪造空数据。
- [ ] API 响应字段与 `api.md` 一致。
