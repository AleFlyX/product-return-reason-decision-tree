# FastAPI 接口说明

## 一、基础信息

- 本地地址：`http://localhost:8000`
- OpenAPI：`GET /openapi.json`
- Swagger UI：`GET /docs`
- 返回格式：JSON
- 认证：本期不设置登录认证
- 模型任务：商品订单是否退货二分类

## 二、通用约定

### 1. 标签

`returned` 取值为 `0` 或 `1`，分别表示未退货和退货。

### 2. 通用错误格式

```json
{
  "detail": "price must be greater than 0"
}
```

### 3. 分页

列表接口使用 `page` 和 `page_size`，均从 1 开始。服务端应限制 `page_size` 的最大值，避免一次返回过多数据。

## 三、接口定义

### 1. 健康检查

`GET /api/health`

响应：

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

### 2. 数据概览

`GET /api/stats/overview`

响应：

```json
{
  "sample_count": 1000,
  "returned_count": 183,
  "return_rate": 0.183,
  "category_count": 8,
  "average_price": 299.5,
  "average_freight": 8.2,
  "updated_at": "2026-09-10T12:00:00Z"
}
```

示例数值仅用于说明格式，不能作为项目最终实验结果。

### 3. 类目退货分析

`GET /api/stats/by-category`

响应：

```json
{
  "items": [
    {
      "category": "服饰",
      "sample_count": 320,
      "returned_count": 74,
      "return_rate": 0.23125
    }
  ]
}
```

### 4. 订单列表

`GET /api/orders?page=1&page_size=20&category=服饰&returned=1`

响应：

```json
{
  "items": [
    {
      "order_id": "order_000001",
      "category": "服饰",
      "price": 299,
      "is_promotion": 1,
      "season": "夏",
      "freight": 0,
      "returned": 1
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 183
}
```

### 5. 退货预测

`POST /api/returns/predict`

请求：

```json
{
  "category": "服饰",
  "price": 299,
  "is_promotion": 1,
  "season": "夏",
  "freight": 0
}
```

响应：

```json
{
  "predicted_returned": 1,
  "return_probability": 0.72,
  "class_probabilities": {
    "not_returned": 0.28,
    "returned": 0.72
  },
  "model": "decision-tree",
  "model_version": "2026-09-10"
}
```

校验规则：

- `category` 和 `season` 不能为空；
- `price > 0`；
- `is_promotion` 只能为 `0` 或 `1`；
- `freight >= 0`。

### 6. 模型指标

`GET /api/model/metrics`

响应：

```json
{
  "model": "decision-tree",
  "model_version": "2026-09-10",
  "accuracy": 0.84,
  "precision": 0.63,
  "recall": 0.58,
  "f1": 0.60,
  "confusion_matrix": [[145, 19], [23, 13]],
  "train_samples": 800,
  "test_samples": 200,
  "returned_rate_test": 0.18
}
```

真实项目必须返回实际实验结果；示例数值不能直接用于汇报。

### 7. 特征重要性

`GET /api/model/features`

响应：

```json
{
  "items": [
    {
      "feature": "category_服饰",
      "importance": 0.31
    },
    {
      "feature": "price",
      "importance": 0.24
    }
  ]
}
```

### 8. 决策树规则

`GET /api/model/rules?limit=20`

响应：

```json
{
  "items": [
    {
      "rule_id": "leaf-3",
      "conditions": [
        "price <= 120.50",
        "is_promotion = 1",
        "category = 服饰"
      ],
      "predicted_returned": 1,
      "return_probability": 0.71,
      "sample_count": 86
    }
  ]
}
```

### 9. 测试集预测结果

`GET /api/model/predictions?limit=200`

响应：

```json
{
  "items": [
    {
      "index": 1,
      "actual_returned": 1,
      "predicted_returned": 1,
      "return_probability": 0.72
    }
  ]
}
```

## 四、接口约定

- 金额字段统一使用元，概率和退货率使用 `0` 到 `1` 的小数。
- 数值保留位数由前端展示层控制，API 返回计算结果。
- 前端不得依赖未在本文档声明的字段。
- 接口变更必须同步修改 Pydantic schema、前端 API 封装和本文件。
- 模型未加载时，预测和模型分析接口应返回明确的 503 错误，而不是空数据。
- HDFS 或 HBase 不可用时，相关接口应返回明确的 503 或降级状态，不得用空数组伪装正常响应。
