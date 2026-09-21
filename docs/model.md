# 决策树模型训练与交付

## 一、模型目标

输入订单提交时可获得的字段，输出：

- `predicted_returned`：预测是否退货；
- `return_probability`：预测为退货的概率；
- `feature_importance`：模型使用特征的重要性；
- `rules`：从根节点到叶节点的可读条件。

模型不负责预测具体退货原因。退货原因属于退货发生后的结果分析字段。

## 二、训练配置

第一版候选配置：

```python
DecisionTreeClassifier(
    max_depth=4,
    min_samples_leaf=10,
    random_state=42,
    class_weight=None,  # 必须与 balanced 对照
)
```

配置不是固定结论，必须比较 `class_weight=None` 与 `balanced`，并通过训练集交叉验证和独立测试集结果选择。每次训练都要保存：

- 数据文件版本或校验值；
- 特征列表；
- 随机种子；
- 模型参数；
- 训练和测试样本数；
- 类别比例。
- 交叉验证比较结果。

## 三、评估指标

至少输出：

| 指标 | 说明 |
| --- | --- |
| Accuracy | 全部样本预测正确的比例 |
| Precision | 被预测为退货的样本中实际退货的比例 |
| Recall | 实际退货样本中被识别出来的比例 |
| F1 | Precision 和 Recall 的调和平均 |
| Confusion Matrix | 四类预测结果数量 |

退货比例不均衡时，Accuracy 不能作为唯一结论。汇报中应同时说明退货类的 Recall 和 F1。

## 四、模型选择

至少比较一组不同复杂度参数，例如：

```text
max_depth = 3, 4, 5, 6
min_samples_leaf = 5, 10, 20
```

选择原则：

1. 测试集指标稳定；
2. 退货类召回率满足业务演示要求；
3. 训练集与测试集差距不过大；
4. 规则数量和深度仍便于解释。

## 五、规则导出

规则导出结果统一为：

```json
{
  "rule_id": "leaf-3",
  "conditions": [
    "price <= 120.50",
    "category = 服饰"
  ],
  "predicted_returned": 1,
  "return_probability": 0.71,
  "sample_count": 86
}
```

规则需要保留叶节点样本量。样本量过小的规则不应单独作为业务结论。

## 六、模型文件

```text
/project/product-return/model/model_name=decision-tree/model_version=<model_version>/
├── return_decision_tree.joblib
├── metrics.json
├── feature_importance.json
├── rules.json
└── model_metadata.json
```

`return_decision_tree.joblib` 应保存完整的预处理和分类 Pipeline，使 API 可以直接接收原始字段。

## 七、模型验收

- [ ] 模型能被独立加载并完成一条预测。
- [ ] 输入字段与 API 文档一致。
- [ ] 指标来自未参与训练的测试集。
- [ ] 指标文件包含准确率、精确率、召回率、F1 和混淆矩阵。
- [ ] 特征重要性名称能映射回类别或原始字段。
- [ ] 规则中的类别名称可读，阈值保留原始单位。
- [ ] 训练配置和模型版本已记录。
- [ ] 模型产物已写入 HDFS，并在 HBase 模型注册表登记。
