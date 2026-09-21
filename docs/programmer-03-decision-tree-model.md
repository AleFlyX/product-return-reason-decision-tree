# 程序员③：决策树训练、评估、规则和模型文件

## 一、岗位目标

程序员③从 HDFS 读取程序员②交付的原始字段训练集和测试集，负责拟合预处理器与决策树，输出评估指标、特征重要性、规则和可被 FastAPI 加载的完整模型文件。

## 二、输入与输出

输入：

```text
/project/product-return/feature-split/train/data_version=<data_version>/
/project/product-return/feature-split/test/data_version=<data_version>/
/project/product-return/feature-split/schema/data_version=<data_version>/
```

输出：

```text
/project/product-return/model/model_name=decision-tree/model_version=<model_version>/
├── return_decision_tree.joblib
├── metrics.json
├── feature_importance.json
├── rules.json
├── model_metadata.json
└── decision_tree.png
```

## 三、训练约束

第一版候选配置：

```python
DecisionTreeClassifier(
    max_depth=4,
    min_samples_leaf=10,
    random_state=42,
    class_weight=None,  # 与 balanced 一起比较
)
```

必须同时比较 `class_weight=None` 和 `class_weight="balanced"`，并依据训练集交叉验证及独立测试集的 Recall、Precision、F1 和混淆矩阵选择，不能凭感觉打开。

每个模型版本必须记录：

- `data_version`；
- HDFS 训练集和测试集路径；
- Pipeline 版本；
- 特征列表；
- 随机种子；
- 模型参数；
- 训练时间；
- 代码版本或 Git commit；
- 依赖版本。

## 四、评估指标

必须输出：

```text
accuracy
precision
recall
f1
confusion_matrix
train_samples
test_samples
returned_rate_test
```

退货样本比例较低时，不能只汇报 Accuracy。答辩和 API 必须同时展示退货类 Recall、F1 和混淆矩阵。

## 五、模型选择

至少比较：

```text
max_depth: 3, 4, 5, 6
min_samples_leaf: 5, 10, 20
class_weight: None, balanced
```

选择原则：

1. 测试集指标稳定；
2. 退货类 Recall 和 F1 可接受；
3. 训练集和测试集差距不明显过大；
4. 规则数量和树深度适合人工解释；
5. 运行成本满足 API 加载和预测需求。

## 六、特征重要性

One-Hot 后必须通过预处理器取出真实特征名称：

```python
feature_names = pipeline.named_steps[
    "preprocess"
].get_feature_names_out()
importances = pipeline.named_steps[
    "classifier"
].feature_importances_
```

输出排序后的：

```json
{
  "feature": "category_服饰",
  "importance": 0.31,
  "source_field": "category"
}
```

要提醒使用者：特征重要性表示模型使用程度，不代表业务因果关系。

## 七、规则导出

`export_text()` 可以用于调试，但 API 规则必须结构化。遍历树节点时要把 One-Hot 特征还原：

```text
category_服饰 > 0.5
→ category = 服饰

category_服饰 <= 0.5
→ category != 服饰
```

规则 JSON：

```json
{
  "rule_id": "leaf-3",
  "conditions": [
    "category = 服饰",
    "price <= 120.50",
    "is_promotion = 1"
  ],
  "predicted_returned": 1,
  "return_probability": 0.71,
  "sample_count": 86,
  "model_version": "dt-20260910-001"
}
```

叶节点样本量过小时，前端应标注“低样本规则”，不把它当作稳定业务结论。

## 八、HDFS 模型注册

模型文件写入 HDFS 后，向程序员④交付：

```json
{
  "model_name": "decision-tree",
  "model_version": "dt-20260910-001",
  "data_version": "20260910-001",
  "artifact_path": "/project/product-return/model/model_name=decision-tree/model_version=dt-20260910-001/",
  "status": "ready"
}
```

程序员④负责把这份元数据写入 HBase 模型注册表。未写入注册表的模型不得被 API 标记为当前生产模型。

## 九、交接关系

交给程序员④：

- 完整 Pipeline 文件；
- 指标、混淆矩阵和特征重要性；
- 规则 JSON；
- HDFS 模型目录；
- 当前模型版本和回滚版本；
- 输入 schema。

交给程序员⑤：

- `/api/model/metrics` 字段；
- `/api/model/features` 字段；
- `/api/model/rules` 字段；
- 指标单位和版本展示规则。

## 十、验收清单

- [ ] 模型从 HDFS 训练数据生成。
- [ ] 本地开发时可从 `data/feature-split/` 的 CSV/Parquet 生成同样产物；正式验收仍需 HDFS。
- [ ] 完整 Pipeline 由程序员③拟合并保存，可直接接收 API 原始字段。
- [ ] 指标来自独立测试集。
- [ ] 模型文件、指标、规则和元数据在 HDFS 同一版本目录。
- [ ] 规则中的类别可读，数值阈值保留原始单位。
- [ ] 版本元数据已交给程序员④写入 HBase。
- [ ] 能回滚到上一份已登记模型。
