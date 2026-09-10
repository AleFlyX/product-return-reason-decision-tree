# 程序员①：订单/退货数据采集、清洗和标签构造

## 一、岗位目标

程序员①负责把经授权的订单数据和退货数据整理成可追溯、可复现、可训练的数据产品，并将批处理文件写入 HDFS。

```text
数据源
  → 原始数据登记
  → HDFS 原始区
  → 字段统一与质量清洗
  → 订单-退货关联
  → returned 标签构造
  → HDFS 清洗区
  → 交接给程序员②和程序员④
```

本岗位不负责模型训练和 FastAPI 业务接口，但必须为它们提供稳定的数据契约。

## 二、输入与输出

### 输入

```text
data/raw/orders_raw.csv
data/raw/returns_raw.csv
```

原始文件必须记录：

- 数据来源和授权说明；
- 下载或生成时间；
- 文件大小和 SHA-256；
- 字符编码和分隔符；
- 字段版本；
- 数据批次号 `batch_id`。

### 输出

```text
data/clean/orders_clean.csv
data/clean/returns_clean.csv
data/clean/return_model.csv
data/reports/cleaning_report.json
```

正式环境还必须写入 HDFS：

```text
/project/product-return/raw/orders/batch_id=<batch_id>/
/project/product-return/raw/returns/batch_id=<batch_id>/
/project/product-return/clean/orders/batch_id=<batch_id>/
/project/product-return/clean/returns/batch_id=<batch_id>/
/project/product-return/clean/return_model/batch_id=<batch_id>/
/project/product-return/reports/batch_id=<batch_id>/
```

## 三、标准字段

订单表至少包含：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `order_id` | string | 非空，订单级唯一 |
| `category` | string | 统一类目名称 |
| `price` | float | 大于 0，单位元 |
| `is_promotion` | int | 只能为 0 或 1 |
| `order_time` | datetime | ISO 8601 或统一时区 |
| `season` | string | 春、夏、秋、冬 |
| `freight` | float | 大于等于 0，单位元 |

退货表至少包含：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `return_id` | string | 非空，退货记录唯一 |
| `order_id` | string | 能关联订单表 |
| `return_date` | datetime | 不早于订单时间 |
| `return_status` | string | 映射为标准状态 |
| `return_reason` | string | 结果分析字段，不进模型 |
| `refund_amount` | float | 结果分析字段，不进模型 |

## 四、清洗规则

### 1. 标识和去重

- 订单表以 `order_id` 检查重复；
- 退货表以 `return_id` 检查重复；
- 同一订单存在多条有效退货记录时，训练表仍只保留一行；
- 无法判断重复记录哪一条正确时，不能静默覆盖，要写入异常报告。

### 2. 格式归一化

```text
“299元”       → 299
“是/否”        → 1/0
“2026-07-01”  → 标准 datetime
“服装/服饰”   → 统一类目映射
前后空格       → 删除
```

### 3. 异常和缺失

以下记录不能直接进入训练表：

```text
order_id 为空
category 为空
price <= 0
freight < 0
order_time 无法解析
is_promotion 不属于 0/1
```

异常记录可以删除、修正或单独隔离，但必须记录：

```json
{
  "reason": "price <= 0",
  "count": 12,
  "action": "quarantine"
}
```

## 五、标签构造

默认观察窗口为订单时间起 30 个自然日。有效退货状态先通过配置映射为“已确认退货”，拒绝、取消和测试记录不计入标签。

```text
return_date >= order_time
且 return_date <= order_time + 30 days
且 return_status = 已确认退货
→ returned = 1

否则
→ returned = 0
```

训练表字段固定为：

```text
order_id, category, price, is_promotion, season, freight, returned
```

严禁把 `return_reason`、`return_date`、`refund_amount`、`return_status` 作为模型输入。

## 六、HDFS 入湖要求

### 1. 上传顺序

```text
本地原始文件校验
  → 上传 HDFS raw 区
  → 运行清洗
  → 上传 HDFS clean 区
  → 上传 cleaning_report.json
```

### 2. HDFS 文件要求

- 路径必须包含 `batch_id`；
- 不覆盖已经验收的批次；
- 同一个批次的文件使用统一字符编码和分隔符；
- 上传后检查文件大小、行数和校验摘要；
- 失败时不能只打印错误后继续标记批次成功。

### 3. 交接元数据

```json
{
  "batch_id": "20260910-001",
  "source_version": "orders-v1",
  "row_count": 1000,
  "hdfs_path": "/project/product-return/clean/return_model/batch_id=20260910-001/",
  "sha256": "实际摘要",
  "observation_window_days": 30,
  "valid_return_statuses": ["已确认退货"]
}
```

## 七、交接关系

### 交给程序员②

- HDFS 清洗表路径；
- `return_model` 字段顺序；
- 标签分布；
- 异常和缺失处理报告；
- 观察窗口和状态映射配置。

### 交给程序员④

- HDFS 批次路径；
- `orders_clean` 和 `returns_clean` 字段说明；
- HBase 写入所需的 RowKey 和列族建议；
- 批次号、数据版本和数据质量状态。

## 八、验收清单

- [ ] 原始文件来源可追溯。
- [ ] HDFS raw、clean、reports 路径均已生成。
- [ ] 训练表一个 `order_id` 只有一行。
- [ ] `returned` 可按照观察窗口重新计算。
- [ ] 退货发生后的字段没有进入训练表。
- [ ] 清洗报告包含行数、重复、缺失、异常、无主退货和标签分布。
- [ ] 上传失败不会被标记为成功。
- [ ] 程序员②可以直接从 HDFS 读取训练表。
