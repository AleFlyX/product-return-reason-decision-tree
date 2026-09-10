# 程序员②：特征工程、数据集划分和预处理 Pipeline

## 一、岗位目标

程序员②将程序员①交付的订单级训练表转换为可供程序员③训练、程序员④推理和程序员⑤展示的统一特征数据。

```text
HDFS return_model
  → 数据质量复核
  → 标签分布检查
  → 训练/测试划分
  → 类别编码和数值特征处理
  → Pipeline 固化
  → HDFS feature 区
```

## 二、输入与输出

输入：

```text
/project/product-return/clean/return_model/batch_id=<batch_id>/
```

输出：

```text
/project/product-return/feature/train/batch_id=<batch_id>/
/project/product-return/feature/test/batch_id=<batch_id>/
/project/product-return/feature/schema/batch_id=<batch_id>/
/project/product-return/reports/feature_report/batch_id=<batch_id>/
```

本地调试可以同步生成：

```text
model/saved/preprocessor.joblib
model/saved/feature_names.json
data/reports/feature_report.json
```

## 三、特征契约

原始特征：

```python
feature_cols = [
    "category",
    "price",
    "is_promotion",
    "season",
    "freight",
]
```

标签：

```python
target_col = "returned"
```

不允许进入 `X` 的字段：

```text
order_id
return_reason
return_date
refund_amount
return_status
returned_at
任何售后处理字段
```

## 四、预处理策略

### 1. 类别字段

`category` 和 `season` 使用：

```python
OneHotEncoder(handle_unknown="ignore")
```

未知类别不能导致在线预测接口崩溃，但必须在特征报告中统计未知值数量。

### 2. 数值字段

`price`、`is_promotion`、`freight` 保持数值类型。决策树不要求标准化，因此默认不做 StandardScaler，保证规则阈值仍然使用元和 0/1 的业务单位。

### 3. 缺失值

缺失值策略必须在训练集上拟合：

- 数值字段：中位数填补或剔除；
- 类别字段：增加 `UNKNOWN` 类别；
- 标签缺失：直接剔除并统计。

测试集和线上请求不能重新计算填补参数。

## 五、数据集划分

默认配置：

```python
train_test_split(
    X,
    y,
    test_size=0.3,
    random_state=42,
    stratify=y,
)
```

要求：

- 训练集和测试集不能有相同 `order_id`；
- 保留 `batch_id`、`data_version` 和 `split_seed`；
- 退货类比例在训练集和测试集之间保持可比；
- 如果数据有用户或商品分组，优先评估 Group split 是否更合理。

## 六、Pipeline 固化

必须保存完整 Pipeline，而不是只保存编码器：

```python
Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("classifier", classifier),
    ]
)
```

程序员③训练时使用这一份 Pipeline；程序员④在线预测时加载同一份 Pipeline。任何手工修改类别顺序的做法都必须禁止。

## 七、特征报告

至少生成：

```json
{
  "batch_id": "20260910-001",
  "feature_cols": ["category", "price", "is_promotion", "season", "freight"],
  "target_col": "returned",
  "encoded_feature_count": 12,
  "train_samples": 700,
  "test_samples": 300,
  "train_return_rate": 0.18,
  "test_return_rate": 0.18,
  "split_seed": 42,
  "leakage_fields": [],
  "hdfs_train_path": "正式路径",
  "hdfs_test_path": "正式路径"
}
```

## 八、HDFS 交付

特征文件要带版本目录：

```text
/project/product-return/feature/train/data_version=<data_version>/part-*.parquet
/project/product-return/feature/test/data_version=<data_version>/part-*.parquet
```

禁止覆盖已用于训练的特征版本。程序员③必须能够通过 `data_version` 复现同一训练输入。

## 九、交接关系

交给程序员③：

- HDFS 训练集和测试集路径；
- 完整预处理 Pipeline；
- 编码后特征名称；
- 标签分布；
- 泄漏检查报告；
- 数据版本和划分随机种子。

交给程序员④：

- 在线预测所需原始字段；
- Pipeline 文件或 HDFS 路径；
- 未知类别处理规则；
- 特征 schema 版本。

## 十、验收清单

- [ ] 训练/测试集来自同一批次且没有订单交叉。
- [ ] 测试集没有参与预处理器拟合。
- [ ] 退货发生后的字段未进入特征。
- [ ] HDFS feature train/test 目录可读取。
- [ ] Pipeline 可独立加载并转换一条 API 请求。
- [ ] 特征名称、版本、随机种子和标签分布均已记录。
