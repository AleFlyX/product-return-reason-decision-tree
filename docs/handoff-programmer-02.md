# 程序员② 交接说明：特征工程、数据集划分与预处理配置

## 一、已交付产物

| 文件 | 说明 |
| --- | --- |
| `preprocessing/config.py` | 全部业务口径参数（数据源、映射、促销判定、划分种子） |
| `preprocessing/adapter_return_model.py` | 把①交付的原始 CSV 适配为契约要求的 7 列训练表 |
| `preprocessing/feature_engineering.py` | 质量复核、泄漏扫描、分层划分、schema 与报告产出 |
| `data/clean/return_model.csv` | 标准训练表，34500 行 |
| `data/feature-split/train/data_version=return-model-v1/part-0.csv` | 训练集，24150 行（同时产出 `part-0.parquet`） |
| `data/feature-split/test/data_version=return-model-v1/part-0.csv` | 测试集，10350 行（同时产出 `part-0.parquet`） |
| `data/feature-split/schema/data_version=return-model-v1/feature_schema.json` | 特征 schema（版本化交付目录） |
| `data/reports/feature_schema.json` | 特征 schema、类别取值、预处理配置、编码后特征名 |
| `data/reports/feature_report.json` | 划分统计、标签分布、质量检查、泄漏检查、不平衡告警 |
| `data/reports/adapter_report.json` | 原始列到标准列的映射与派生字段说明 |

## 二、给程序员③

- 训练/测试路径见 `feature_report.json` 的 `local_train_path` / `local_test_path`。
- 特征固定为 `category, price, is_promotion, season, freight`，标签 `returned`。
- 预处理配置见 `feature_schema.json` 的 `preprocessor_config`：
  类别字段 `category`、`season` 用 `OneHotEncoder(handle_unknown="ignore")`；
  数值字段 `price`、`is_promotion`、`freight` 直通，**不做标准化**（决策树不需要，且规则阈值要保留元和 0/1 的业务单位）。
- 编码后共 14 个特征，名称见 `feature_schema.json` 的 `encoded_feature_names`。
- `encoded_feature_source_map` 给出 One-Hot 特征到原始字段的还原映射（如 `categorical__category_服饰 → category`），可直接用于特征重要性的 `source_field` 字段和规则还原（见 `docs/programmer-03-decision-tree-model.md` 第六、七节）。
- 模型版本需记录的 `data_version`（return-model-v1）、`split_seed`（42）、特征列表、标签分布均已在 `feature_report.json` 中，可直接抄进 `model_metadata.json`。
- 本地数据路径（无 HDFS 时的降级方案）：`feature_report.json` 的 `local_train_path` / `local_test_path`，格式为 CSV 与 parquet 各一份。
- 完整 Pipeline（预处理器 + 决策树）由③在训练集上拟合并保存，②不交付已拟合 Pipeline。
- **缺失值填补参数已固化**：`feature_schema.json` 的 `imputation_parameters` 给出数值列中位数（price 45.645、is_promotion 0、freight 6.11）与类别列 UNKNOWN 填充值。参数只在训练集上拟合，测试集与线上请求必须复用，**不得重新计算**。本批数据实际缺失 0 条，故填补数为 0，但参数已就位，换数据源可直接生效。
- 划分种子 `split_seed=42`，`data_version=return-model-v1`，请勿覆盖已用于训练的划分版本。

### ⚠️ 必须使用 class_weight='balanced'

少数类（退货）仅占 **5.52%**。②本地试跑结果：

| 配置 | Accuracy | AUC | Recall | Precision |
| --- | --- | --- | --- | --- |
| depth=4，默认参数 | 0.9448 | 0.6035 | **0.0000** | 0.0000 |
| depth=4，class_weight='balanced' | 0.4939 | 0.6016 | 0.6760 | 0.0710 |

默认参数下决策树**全部预测为“不退货”**：accuracy 高达 94.5% 但 **recall = 0**，一个退货都没抓出来。多数类基线 accuracy 为 0.9448，因此**本项目不能用 accuracy 作为主要结论**，必须同时汇报退货类的 Recall、Precision 和 F1（见 `docs/model.md` 第三节要求）。

## 三、给程序员④

- 在线预测输入字段（原始字段，非 One-Hot）：`category, price, is_promotion, season, freight`。
- 类别取值受控：`category` ∈ 服饰/电子产品/家居/玩具/运动户外/美妆/食品生鲜，`season` ∈ 春/夏/秋/冬。
- 未知类别策略为 `ignore`，不会导致接口崩溃，但需统计未知值数量。
- 加载③交付的完整 Pipeline 做预测，不要手工修改类别顺序。

## 四、数据说明与已验证的业务规律

数据源：`Kaggle_Ecommerce Data.csv`，34500 行，19 列，无重复 `order_id`。

字段映射：`order_id` → order_id；`category` → category（英文转中文受控类目）；`price` → price；`discount > 0` → is_promotion；`shipping_cost` → **freight（真实运费，非派生）**；`order_date` → season；`returned`(Yes/No) → returned。

已剔除字段：`request_date`、`return_reason`（退货后才产生，属泄漏）、`delivered_date`（下单时不可知）、`customer_id`、`product_id`、`quantity`、`payment_method`、`region`、`total_amount`、`profit_margin`、`customer_age`、`customer_gender`。

已验证的业务规律（可直接用于规则讲解）：

| 分组 | 退货率 |
| --- | --- |
| 服饰 | 8.28% |
| 食品生鲜 | 1.31% |
| 运费 9~12 元 | 7.13% |
| 运费 0~3 元 | 3.15% |
| 价格 1172~1759 元 | 8.98% |

即：**服饰类退货率是食品生鲜的 6.3 倍，运费越高的订单越容易退货，高价商品退货率更高**。折扣、季节、地区、支付方式、性别对退货率基本无影响。

## 五、运行方式

依赖见 `preprocessing/requirements.txt`（pandas、numpy、scikit-learn；parquet 输出另需 pyarrow，缺失时自动降级为 CSV）。

```bash
pip install -r preprocessing/requirements.txt

# 步骤 1：把①交付的原始 CSV 适配为契约要求的 7 列训练表
python preprocessing/adapter_return_model.py

# 步骤 2：质量复核、泄漏扫描、70/30 分层划分、产出 schema 与报告
python preprocessing/feature_engineering.py
```

所有业务口径（数据源路径、字段映射、促销判定阈值、划分种子、数据版本）集中在 `preprocessing/config.py`，改口径只需改配置，不需要改代码。

## 六、遗留问题

1. **标签口径**：当前直接采信原始 `returned` 字段。若按文档默认的 30 天观察窗口重算，退货距下单天数为 4~40 天，会有部分样本被改判（见 `adapter_report.json` 的 `label_policy_comparison`），需团队确认采用哪种口径。
2. **HDFS 未上传**：`feature-split` 目录（含 csv 与 parquet）目前只落在本地，正式环境需上传至 `/project/product-return/feature-split/{train,test,schema}/data_version=return-model-v1/`。无集群环境，未执行，验收时需补。
