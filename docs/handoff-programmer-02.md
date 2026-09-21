# 程序员② 交接说明：特征工程、数据集划分与预处理配置

## 一、交付性质声明（重要）

**本次为「本地开发交付」。**

项目文档要求 HDFS 作为正式批处理存储，并包含 `_SUCCESS`、`manifest.json`、行数、批次号、数据版本和校验摘要。
当前**无 Hadoop 集群环境**，该步骤未执行。所有划分数据落在仓库本地目录 `data/feature-split/`，
正式路径已在 `feature_report.json` 的 `hdfs_train_path` / `hdfs_test_path` / `hdfs_schema_path` 中记录，
待集群就绪后按下列规范执行上传：

```text
/project/product-return/feature-split/train/data_version=return-model-v1/
/project/product-return/feature-split/test/data_version=return-model-v1/
/project/product-return/feature-split/schema/data_version=return-model-v1/
```

每个目录需包含：`part-0.csv`、`part-0.parquet`、`_SUCCESS`、`manifest.json`
（manifest 至少含 `batch_id`、`data_version`、`row_count`、`split_seed`、`checksum`）。

## 二、已交付产物

| 文件 | 说明 |
| --- | --- |
| `preprocessing/config.py` | 全部业务口径参数（数据源、映射、标签口径、划分种子） |
| `preprocessing/adapter_return_model.py` | 把原始 CSV 适配为契约要求的 7 列训练表 |
| `preprocessing/feature_engineering.py` | 质量复核、泄漏扫描、分层划分、schema 与报告产出 |
| `preprocessing/requirements.txt` | 依赖清单 |
| `data/clean/return_model.csv` | 标准训练表，34500 行（**已入库，用于复现**） |
| `data/feature-split/train/data_version=return-model-v1/part-0.csv` + `part-0.parquet` | 训练集，24150 行 |
| `data/feature-split/test/data_version=return-model-v1/part-0.csv` + `part-0.parquet` | 测试集，10350 行 |
| `data/feature-split/schema/data_version=return-model-v1/feature_schema.json` | 特征 schema（版本化交付目录） |
| `data/reports/feature_schema.json` | 特征 schema、类别取值、预处理配置、编码后特征名 |
| `data/reports/feature_report.json` | 划分统计、标签分布、质量检查、泄漏检查、不平衡告警 |
| `data/reports/adapter_report.json` | 原始列到标准列的映射与派生字段说明 |

Parquet 为正式交付格式之一：`feature_engineering.py` 在生成 parquet 失败时**显式报错**，不再静默降级为 CSV。

## 三、标签口径（30 天观察窗口）

采用项目文档默认口径 **`window_30d`**，由 `config.py` 的 `LABEL_POLICY` 控制，对两个数据源分支均生效。

规则：原始 `returned == Yes` 且 `request_date` 距 `order_date` 在 **0 ~ 30 天**内才记为 `returned=1`，超期退货记为 `returned=0`。

| 口径 | 正样本 | 退货率 |
| --- | --- | --- |
| 原始 `returned` 字段 | 1903 | 5.52% |
| **30 天观察窗口（本次采用）** | **1599** | **4.63%** |

差异 304 条（占原正样本 16.0%）。对比数据见 `adapter_report.json` 的 `label_policy_comparison`
（`adopted` 字段标明实际采用的口径）。

## 四、给程序员③

- 训练/测试路径见 `feature_report.json` 的 `local_train_path` / `local_test_path`（集群就绪后改用 `hdfs_*_path`）。
- 特征固定为 `category, price, is_promotion, season, freight`，标签 `returned`。
- 预处理配置见 `feature_schema.json` 的 `preprocessor_config`：
  类别字段 `category`、`season` 用 `OneHotEncoder(handle_unknown="ignore")`；
  数值字段 `price`、`is_promotion`、`freight` 直通，**不做标准化**（决策树不需要，且规则阈值要保留元和 0/1 的业务单位）。
- 编码后共 14 个特征，名称见 `feature_schema.json` 的 `encoded_feature_names`。
- `encoded_feature_source_map` 给出 One-Hot 特征到原始字段的还原映射（如 `categorical__category_服饰 → category`），可直接用于特征重要性的 `source_field` 字段和规则还原。
- 模型版本需记录的 `data_version`（return-model-v1）、`split_seed`（42）、特征列表、标签分布均已在 `feature_report.json` 中。
- 数据格式为 CSV 与 parquet 各一份，parquet 可直接用 `pd.read_parquet` 读取。
- 完整 Pipeline（预处理器 + 决策树）由③在训练集上拟合并保存，②不交付已拟合 Pipeline。
- **缺失值填补参数已固化**：`feature_schema.json` 的 `imputation_parameters` 给出数值列中位数与类别列 UNKNOWN 填充值。参数只在训练集上拟合，测试集与线上请求必须复用，**不得重新计算**。

### ⚠️ 必须使用 class_weight='balanced'

少数类（退货）仅占 **4.63%**。②本地试跑结果：

| 配置 | Accuracy | AUC | Recall | Precision | F1 |
| --- | --- | --- | --- | --- | --- |
| depth=4，默认参数 | 0.9536 | 0.5767 | **0.0000** | 0.0000 | 0.0000 |
| depth=3，class_weight='balanced' | 0.4689 | 0.5929 | 0.6854 | 0.0580 | 0.1069 |
| depth=4，class_weight='balanced' | 0.4689 | 0.5788 | 0.6854 | 0.0580 | 0.1069 |

默认参数下决策树**全部预测为"不退货"**：accuracy 高达 95.4% 但 **recall = 0**，一个退货都没抓出来，
而多数类基线 accuracy 本身就是 0.9536——等于模型什么都没学到。
**本项目不能用 accuracy 作为主要结论**，必须同时汇报退货类的 Recall、Precision 和 F1（见 `docs/model.md` 第三节要求）。

## 五、给程序员④

- 在线预测输入字段（原始字段，非 One-Hot）：`category, price, is_promotion, season, freight`。
- 类别取值受控：`category` ∈ 服饰/电子产品/家居/玩具/运动户外/美妆/食品生鲜，`season` ∈ 春/夏/秋/冬。
- 未知类别策略为 `ignore`，不会导致接口崩溃，但需统计未知值数量。
- 加载③交付的完整 Pipeline 做预测，不要手工修改类别顺序。

## 六、数据说明与已验证的业务规律

数据源：Kaggle 电商订单数据集，34500 行 × 19 列，无重复 `order_id`，`order_date` 为 `DD/MM/YYYY`。

字段映射：`order_id` → order_id；`category` → category（英文转中文受控类目）；`price` → price；
`discount > 0` → is_promotion；`shipping_cost` → **freight（真实运费，非派生）**；
`order_date` → season；`returned`(Yes/No) → returned（按 30 天窗口过滤）。

已剔除字段：`request_date`、`return_reason`（退货后才产生，属泄漏）、`delivered_date`（下单时不可知）、
`customer_id`、`product_id`、`quantity`、`payment_method`、`region`、`total_amount`、`profit_margin`、
`customer_age`、`customer_gender`。

已验证的业务规律（可直接用于规则讲解）：

| 类目 | 退货率 |
| --- | --- |
| 服饰 | 6.86% |
| 电子产品 | 6.20% |
| 家居 | 4.79% |
| 运动户外 | 4.22% |
| 玩具 | 3.96% |
| 美妆 | 3.29% |
| 食品生鲜 | 1.11% |

即：**服饰类退货率是食品生鲜的 6.2 倍**；此外运费越高、价格越高的订单退货率越高。
折扣、季节、地区、支付方式、性别对退货率基本无影响。

## 七、运行与复现

依赖见 `preprocessing/requirements.txt`（pandas、numpy、scikit-learn、pyarrow）。

```bash
pip install -r preprocessing/requirements.txt

# 步骤 1：原始 CSV -> 契约 7 列训练表（需要原始数据源）
python preprocessing/adapter_return_model.py

# 步骤 2：质量复核、泄漏扫描、70/30 分层划分、产出 schema 与报告
python preprocessing/feature_engineering.py
```

**复现方式（两档）**：

- **完整复现**：需要原始数据 `Kaggle_Ecommerce Data.csv`（3.61 MB，由程序员①在群内提供）。
  三种指定方式任选其一，再执行上面两条命令：
  1. 放到仓库的 `data/raw/` 目录（推荐；①补传后全组可一键复现）；
  2. 设置环境变量 `RETURN_MODEL_RAW_CSV`（完整文件路径）或 `RETURN_MODEL_RAW_DIR`（文件所在目录）；
  3. 命令行显式指定：`python preprocessing/adapter_return_model.py --input <路径>`。

  未指定时脚本会打印上述三种方式的提示后退出，不会抛出开发机专属路径错误。
- **跳过步骤 1 的复现**：仓库内已包含 `data/clean/return_model.csv`（适配结果），
  直接执行步骤 2 即可复现全部划分产物与报告，无需原始数据。

所有业务口径（数据源路径、字段映射、标签口径、观察窗口天数、划分种子、数据版本）
集中在 `preprocessing/config.py`，改口径只需改配置。

## 八、遗留问题

1. **HDFS 未上传**：无集群环境。本次明确为**本地开发交付**，上传路径与 manifest 规范见第一节，待集群就绪后执行。
2. **原始数据未入库**：`Kaggle_Ecommerce Data.csv` 仅在群内传阅，建议①补传至 `data/raw/`。
