"""程序员②：特征工程、数据集划分的可配置口径。

所有与业务口径相关的决策都集中在本文件，修改参数即可重跑，不需要改动处理逻辑。
"""

from pathlib import Path

# ---------------------------------------------------------------- 目录约定
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
CLEAN_DIR = DATA_DIR / "clean"
REPORTS_DIR = DATA_DIR / "reports"
SPLIT_DIR = DATA_DIR / "feature-split"
PREPROCESSING_DIR = REPO_ROOT / "preprocessing"

# ---------------------------------------------------------------- 数据源
# synthetic_returns : 程序员①最初交付的 17 列合成宽表（随机生成，无可学信号）
# kaggle_ecommerce  : Kaggle 电商订单数据，34500 行，含真实运费，类目间退货率差异达 6 倍
DATASET_PROFILE = "kaggle_ecommerce"

SYNTHETIC_INPUT_CSV = REPO_ROOT.parents[1] / "ecommerce_returns_synthetic_data.csv"
KAGGLE_INPUT_CSV = REPO_ROOT.parents[1] / "archive (4)" / "Kaggle_Ecommerce Data.csv"
DEFAULT_INPUT_CSV = KAGGLE_INPUT_CSV if DATASET_PROFILE == "kaggle_ecommerce" else SYNTHETIC_INPUT_CSV

# ---------------------------------------------------------------- 版本与批次
BATCH_ID = "20260913-001"
DATA_VERSION = "return-model-v1"
SPLIT_SEED = 42
TEST_SIZE = 0.3

# 划分文件必须带版本目录：feature-split/<split>/data_version=<data_version>/
TRAIN_DIR = SPLIT_DIR / "train" / ("data_version=%s" % DATA_VERSION)
TEST_DIR = SPLIT_DIR / "test" / ("data_version=%s" % DATA_VERSION)
SCHEMA_DIR = SPLIT_DIR / "schema" / ("data_version=%s" % DATA_VERSION)

# ---------------------------------------------------------------- 特征契约
FEATURE_COLS = ["category", "price", "is_promotion", "season", "freight"]
TARGET_COL = "returned"
CATEGORICAL_FEATURES = ["category", "season"]
NUMERIC_FEATURES = ["price", "is_promotion", "freight"]

# 禁止进入 X 的字段（标签泄漏与无效标识）
FORBIDDEN_FIELDS = [
    "order_id",
    "return_reason",
    "return_date",
    "refund_amount",
    "return_status",
    "returned_at",
    "days_to_return",
    "product_id",
    "user_id",
]

# ---------------------------------------------------------------- 原始列 -> 标准列映射
COLUMN_MAP = {
    "Order_ID": "order_id",
    "Product_Category": "category",
    "Product_Price": "price",
    "Order_Date": "order_time",
    "Return_Status": "return_status_raw",
}

CATEGORY_MAP = {
    "Clothing": "服装",
    "Books": "图书",
    "Toys": "玩具",
    "Electronics": "电子产品",
    "Home": "家居",
}
CONTROLLED_CATEGORIES = sorted(set(CATEGORY_MAP.values()))

# Kaggle 电商数据集（archive (4)/Kaggle_Ecommerce Data.csv）的字段映射
KAGGLE_COLUMN_MAP = {
    "order_id": "order_id",
    "category": "category",
    "price": "price",
    "discount": "discount_raw",
    "shipping_cost": "freight",
    "order_date": "order_time",
    "returned": "returned_raw",
}
KAGGLE_CATEGORY_MAP = {
    "Fashion": "服饰",
    "Electronics": "电子产品",
    "Home": "家居",
    "Toys": "玩具",
    "Sports": "运动户外",
    "Beauty": "美妆",
    "Grocery": "食品生鲜",
}
KAGGLE_CONTROLLED_CATEGORIES = sorted(set(KAGGLE_CATEGORY_MAP.values()))
# Kaggle 数据集的 order_date 为 DD/MM/YYYY
KAGGLE_DATE_DAYFIRST = True
# Kaggle 数据集的 discount 是比率（0 ~ 0.3），大于 0 即视为促销
KAGGLE_PROMOTION_RATIO_MIN = 0.0

# freight 在原始数据中不存在，只能由配送方式派生（假设值，必须在报告中声明）
SHIPPING_FREIGHT = {"Standard": 0.0, "Express": 10.0, "Next-Day": 20.0}
FREIGHT_IS_DERIVED = True

# ---------------------------------------------------------------- 口径开关
# status      : 直接采信 Return_Status == "Returned"
# window_30d  : 在 status 基础上，要求 0 <= Days_to_Return <= OBSERVATION_WINDOW_DAYS
LABEL_POLICY = "status"
OBSERVATION_WINDOW_DAYS = 30
VALID_RETURN_STATUS = "Returned"

# is_promotion 二值化阈值：Discount_Applied 达到该金额记为促销
# 注意：原始数据中 9999/10000 条折扣大于 0，直接 "大于 0 即促销" 会退化成常量特征
PROMOTION_MIN_DISCOUNT = 30.0

# ---------------------------------------------------------------- 质量规则
QUALITY_RULES = {
    "order_id_not_null": "order_id 非空且唯一",
    "category_in_controlled_set": "category 属于受控类目集合",
    "price_positive": "price > 0",
    "is_promotion_binary": "is_promotion 只能为 0 或 1",
    "season_in_four": "season 只能为 春/夏/秋/冬",
    "freight_non_negative": "freight >= 0",
    "returned_binary": "returned 只能为 0 或 1",
}

# ---------------------------------------------------------------- 预处理配置（交给程序员③）
PREPROCESSOR_CONFIG = {
    "categorical_features": CATEGORICAL_FEATURES,
    "numeric_features": NUMERIC_FEATURES,
    "unknown_category_policy": "ignore",
    "scaling": "none",
    "imputation": {
        "numeric": "median",
        "categorical": "UNKNOWN",
    },
}

# ---------------------------------------------------------------- 路径（正式环境）
HDFS_CLEAN_PATH = "/project/product-return/clean/return_model/batch_id=%s/" % BATCH_ID
HDFS_TRAIN_PATH = "/project/product-return/feature-split/train/data_version=%s/" % DATA_VERSION
HDFS_TEST_PATH = "/project/product-return/feature-split/test/data_version=%s/" % DATA_VERSION
HDFS_SCHEMA_PATH = "/project/product-return/feature-split/schema/data_version=%s/" % DATA_VERSION
