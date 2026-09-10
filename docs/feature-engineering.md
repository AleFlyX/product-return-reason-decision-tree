# 特征工程与数据预处理

## 一、目标

将订单级清洗数据转换为可供决策树训练和在线预测共同使用的特征 Pipeline，同时检查类别不一致、样本重复、类别不均衡和标签泄漏。

## 二、输入与输出

正式输入：

```text
/project/product-return/clean/return_model/batch_id=<batch_id>/
```

预测特征：

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

输出：

- 训练集和测试集；
- 预处理 Pipeline；
- 训练特征名称；
- 标签分布报告；
- 泄漏检查报告。
- HDFS train/test 特征目录和 `data_version`。

## 三、处理规则

### 1. 类别特征

`category` 和 `season` 使用 `OneHotEncoder(handle_unknown="ignore")`。`is_promotion` 若已经是 0/1，可以作为数值特征；如果输入仍为“是/否”，先在清洗阶段统一。

### 2. 数值特征

`price` 和 `freight` 转为数值类型，并检查：

```text
price > 0
freight >= 0
```

决策树对特征缩放不敏感，本项目默认不做标准化，以便规则阈值保持原始单位。

### 3. 缺失值

模型输入字段缺失的订单不能直接静默填补。项目应先统计缺失原因，再选择删除、使用训练集统计量填补或增加“未知”类别，并在报告中记录。

## 四、数据集划分

使用分层划分保持退货和未退货比例：

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    df[feature_cols],
    df[target_col],
    test_size=0.3,
    random_state=42,
    stratify=df[target_col],
)
```

如果同一用户或同一商品存在大量关联订单，后续可以按用户或商品分组划分，避免相似样本同时出现在训练集和测试集。

## 五、Pipeline 约束

预处理器只能在训练集上 `fit`，测试集和线上请求只能 `transform`：

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

preprocessor = ColumnTransformer(
    [
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            ["category", "season"],
        ),
        (
            "numeric",
            "passthrough",
            ["price", "is_promotion", "freight"],
        ),
    ]
)

pipeline = Pipeline(
    [
        ("preprocess", preprocessor),
        ("classifier", classifier),
    ]
)
```

由程序员③在训练阶段保存完整 Pipeline，而不是只保存分类器，否则线上输入无法复用训练时的编码方式。

## 六、标签泄漏检查

训练前扫描字段名和数据字典，禁止以下字段进入 `X`：

```text
return_reason
return_date
refund_amount
return_status
returned_at
售后处理字段
```

检查还应确认：

- 测试集没有参与预处理器拟合；
- 退货标签生成所需字段没有被误当成输入；
- 同一订单没有同时出现在训练集和测试集；
- `order_id` 没有被编码成模型特征。

## 七、交付物

```text
model/saved/preprocessor.joblib
model/saved/feature_names.json
data/reports/feature_report.json
```

`feature_report.json` 至少记录原始特征、编码后的特征名称、训练/测试数量、标签分布和泄漏检查结果。
