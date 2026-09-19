"""程序员②：数据质量复核、标签泄漏检查、训练/测试划分与特征 schema 固化。

职责边界（见 docs/programmer-02-feature-engineering.md）：
本岗位只交付预处理配置、特征 schema 和原始字段的训练/测试划分，
不拟合分类器，也不交付已拟合的完整 Pipeline；完整 Pipeline 由程序员③在训练阶段拟合并保存。
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

import config as cfg

STANDARD_COLUMNS = ["order_id", "category", "price", "is_promotion", "season", "freight", "returned"]


def controlled_categories() -> list[str]:
    if cfg.DATASET_PROFILE == "kaggle_ecommerce":
        return cfg.KAGGLE_CONTROLLED_CATEGORIES
    return cfg.CONTROLLED_CATEGORIES


def quality_check(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """按数据字典的质量规则复核，剔除不合格样本并记录数量。"""
    checks = {}
    valid = pd.Series(True, index=df.index)

    dup = df["order_id"].duplicated(keep="first")
    checks["order_id_not_null"] = {
        "rule": cfg.QUALITY_RULES["order_id_not_null"],
        "violations": int(dup.sum() + df["order_id"].isna().sum()),
        "action": "drop",
    }
    valid &= ~(dup | df["order_id"].isna())

    cat_bad = ~df["category"].isin(controlled_categories())
    checks["category_in_controlled_set"] = {
        "rule": cfg.QUALITY_RULES["category_in_controlled_set"],
        "violations": int(cat_bad.sum()),
        "action": "drop",
    }
    valid &= ~cat_bad

    price_bad = ~(df["price"] > 0)
    checks["price_positive"] = {
        "rule": cfg.QUALITY_RULES["price_positive"],
        "violations": int(price_bad.sum()),
        "action": "drop",
    }
    valid &= ~price_bad

    promo_bad = ~df["is_promotion"].isin([0, 1])
    checks["is_promotion_binary"] = {
        "rule": cfg.QUALITY_RULES["is_promotion_binary"],
        "violations": int(promo_bad.sum()),
        "action": "drop",
    }
    valid &= ~promo_bad

    season_bad = ~df["season"].isin(["春", "夏", "秋", "冬"])
    checks["season_in_four"] = {
        "rule": cfg.QUALITY_RULES["season_in_four"],
        "violations": int(season_bad.sum()),
        "action": "drop",
    }
    valid &= ~season_bad

    freight_bad = ~(df["freight"] >= 0)
    checks["freight_non_negative"] = {
        "rule": cfg.QUALITY_RULES["freight_non_negative"],
        "violations": int(freight_bad.sum()),
        "action": "drop",
    }
    valid &= ~freight_bad

    # 标签缺失：直接剔除并统计（数据字典要求，不参与填补）
    label_missing = df["returned"].isna()
    checks["returned_not_missing"] = {
        "rule": "标签缺失直接剔除并统计",
        "violations": int(label_missing.sum()),
        "action": "drop",
    }

    returned_bad = ~df["returned"].isin([0, 1])
    checks["returned_binary"] = {
        "rule": cfg.QUALITY_RULES["returned_binary"],
        "violations": int(returned_bad.sum()),
        "action": "drop",
    }
    valid &= ~returned_bad

    cleaned = df[valid].copy()
    checks["summary"] = {
        "input_rows": int(len(df)),
        "dropped_rows": int(len(df) - len(cleaned)),
        "output_rows": int(len(cleaned)),
    }
    return cleaned, checks


def leakage_scan(columns: list[str]) -> dict:
    """确认退货发生后的字段与标识字段没有进入特征。"""
    leaked = [c for c in cfg.FORBIDDEN_FIELDS if c in columns]
    return {
        "forbidden_fields": cfg.FORBIDDEN_FIELDS,
        "leakage_fields": leaked,
        "passed": len(leaked) == 0,
        "order_id_in_features": "order_id" in cfg.FEATURE_COLS,
    }


def fit_imputation(train_df: pd.DataFrame) -> dict:
    """只在训练集上拟合缺失值填补参数。

    数值字段取中位数，类别字段统一归入 UNKNOWN 类。
    参数必须固化并写入 schema，供测试集和线上请求复用，
    不允许在测试集或线上重新计算（见 docs/programmer-02-feature-engineering.md 第四节）。
    """
    params = {
        "fitted_on": "train",
        "numeric_median": {
            c: float(train_df[c].median()) for c in cfg.NUMERIC_FEATURES
        },
        "categorical_unknown": {c: "UNKNOWN" for c in cfg.CATEGORICAL_FEATURES},
    }
    return params


def apply_imputation(df: pd.DataFrame, params: dict, stats: dict) -> pd.DataFrame:
    """用训练集拟合出的参数填补缺失值，并记录实际填补数量。"""
    out = df.copy()
    for c in cfg.NUMERIC_FEATURES:
        n = int(out[c].isna().sum())
        stats["numeric_filled"][c] = n
        if n:
            out[c] = out[c].fillna(params["numeric_median"][c])
    for c in cfg.CATEGORICAL_FEATURES:
        n = int(out[c].isna().sum())
        stats["categorical_filled"][c] = n
        if n:
            out[c] = out[c].fillna(params["categorical_unknown"][c])
    return out


def source_map(encoded_names: list[str]) -> dict:
    """把 One-Hot 后的特征名还原到原始字段，供程序员③输出特征重要性和规则。

    例：categorical__category_服饰 -> category，numeric__price -> price
    """
    mapping = {}
    for name in encoded_names:
        tail = name.split("__", 1)[1] if "__" in name else name
        source = tail
        for col in cfg.CATEGORICAL_FEATURES + cfg.NUMERIC_FEATURES:
            if tail == col or tail.startswith(col + "_"):
                source = col
                break
        mapping[name] = source
    return mapping


def derived_field_notes() -> list[str]:
    """派生字段与口径声明，随数据源切换，避免报告文案与实际处理不一致。"""
    if cfg.DATASET_PROFILE == "kaggle_ecommerce":
        return [
            "数据源: Kaggle_Ecommerce Data.csv（34500 行 x 19 列）",
            "freight 取自原始 shipping_cost，为真实运费，非派生假设值",
            "is_promotion = (discount > 0)，discount 为折扣比率",
            "season 由 order_date（DD/MM/YYYY，已按 dayfirst 解析）月份派生",
            "returned 采信原始 returned 字段（Yes=1 / No=0）",
            "标签由宽表直接映射，无法由订单表与退货表按 order_id 重建（原始数据无两张独立表）",
        ]
    return [
        "数据源: ecommerce_returns_synthetic_data.csv（10000 行 x 17 列）",
        "freight 由 Shipping_Method 派生（Standard=0 / Express=10 / Next-Day=20），为假设值",
        "is_promotion 由 Discount_Applied >= %.2f 二值化" % cfg.PROMOTION_MIN_DISCOUNT,
        "season 由 Order_Date 月份派生",
        "returned 口径=%s，由合成宽表直接映射，无法由订单表与退货表重建" % cfg.LABEL_POLICY,
    ]


def build_preprocessor() -> ColumnTransformer:
    """预处理配置：类别字段 One-Hot，数值字段直通（决策树不做标准化）。"""
    return ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore"), cfg.CATEGORICAL_FEATURES),
            ("numeric", "passthrough", cfg.NUMERIC_FEATURES),
        ]
    )


def main() -> None:
    src = cfg.CLEAN_DIR / "return_model.csv"
    df = pd.read_csv(src)
    print("读取训练表: %s (%d 行)" % (src, len(df)))

    adapter_meta = {}
    adapter_path = cfg.REPORTS_DIR / "adapter_report.json"
    if adapter_path.exists():
        adapter_meta = json.loads(adapter_path.read_text(encoding="utf-8"))

    df, quality = quality_check(df)
    print("质量复核: 剔除 %d 行，剩余 %d 行" % (quality["summary"]["dropped_rows"], len(df)))

    leakage = leakage_scan(cfg.FEATURE_COLS)
    if not leakage["passed"]:
        raise SystemExit("标签泄漏检查未通过: %s" % leakage["leakage_fields"])

    X = df[cfg.FEATURE_COLS]
    y = df[cfg.TARGET_COL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=cfg.TEST_SIZE, random_state=cfg.SPLIT_SEED, stratify=y
    )

    order_train = set(df.loc[X_train.index, "order_id"])
    order_test = set(df.loc[X_test.index, "order_id"])
    overlap = order_train & order_test
    if overlap:
        raise SystemExit("训练集与测试集存在 %d 个重复 order_id" % len(overlap))

    train_df = df.loc[X_train.index, STANDARD_COLUMNS].reset_index(drop=True)
    test_df = df.loc[X_test.index, STANDARD_COLUMNS].reset_index(drop=True)

    # 缺失值：参数只在训练集上拟合，再套用到训练集和测试集（测试集不得重新计算）
    missing_before = {
        c: int(df[c].isna().sum()) for c in cfg.FEATURE_COLS + [cfg.TARGET_COL]
    }
    imputation_params = fit_imputation(train_df)
    train_fill = {"numeric_filled": {}, "categorical_filled": {}}
    test_fill = {"numeric_filled": {}, "categorical_filled": {}}
    train_df = apply_imputation(train_df, imputation_params, train_fill)
    test_df = apply_imputation(test_df, imputation_params, test_fill)

    cfg.TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    cfg.TEST_DIR.mkdir(parents=True, exist_ok=True)
    cfg.SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    train_path = cfg.TRAIN_DIR / "part-0.csv"
    test_path = cfg.TEST_DIR / "part-0.csv"
    train_df.to_csv(train_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")
    try:
        train_df.to_parquet(cfg.TRAIN_DIR / "part-0.parquet", index=False)
        test_df.to_parquet(cfg.TEST_DIR / "part-0.parquet", index=False)
    except Exception:
        pass

    # 自检：预处理器只在训练集上拟合，验证配置可用（产物不交付，仅供程序员③参考）
    pre = build_preprocessor()
    pre.fit(train_df[cfg.FEATURE_COLS])
    encoded_names = list(pre.get_feature_names_out())
    Xt = pre.transform(test_df[cfg.FEATURE_COLS])
    print("自检: 编码后特征数=%d，测试集矩阵形状=%s" % (len(encoded_names), getattr(Xt, "shape", None)))

    schema = {
        "batch_id": cfg.BATCH_ID,
        "data_version": cfg.DATA_VERSION,
        "feature_cols": cfg.FEATURE_COLS,
        "target_col": cfg.TARGET_COL,
        "categorical_features": cfg.CATEGORICAL_FEATURES,
        "numeric_features": cfg.NUMERIC_FEATURES,
        "category_values": {
            "category": sorted(df["category"].dropna().unique().tolist()),
            "season": sorted(df["season"].dropna().unique().tolist()),
        },
        "dtypes": {c: str(df[c].dtype) for c in cfg.FEATURE_COLS + [cfg.TARGET_COL]},
        "unknown_category_policy": cfg.PREPROCESSOR_CONFIG["unknown_category_policy"],
        "scaling": cfg.PREPROCESSOR_CONFIG["scaling"],
        "imputation": cfg.PREPROCESSOR_CONFIG["imputation"],
        "preprocessor_config": cfg.PREPROCESSOR_CONFIG,
        # 填补参数固化：测试集和线上请求必须复用，不得重新计算
        "imputation_parameters": imputation_params,
        "encoded_feature_names": encoded_names,
        # One-Hot 特征 -> 原始字段的还原映射，供程序员③做特征重要性和规则还原
        "encoded_feature_source_map": source_map(encoded_names),
        "online_input_fields": cfg.FEATURE_COLS,
        "split_seed": cfg.SPLIT_SEED,
        "test_size": cfg.TEST_SIZE,
    }
    schema_path = cfg.REPORTS_DIR / "feature_schema.json"
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    (cfg.SCHEMA_DIR / "feature_schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = {
        "batch_id": cfg.BATCH_ID,
        "data_version": cfg.DATA_VERSION,
        "feature_cols": cfg.FEATURE_COLS,
        "target_col": cfg.TARGET_COL,
        "train_samples": int(len(train_df)),
        "test_samples": int(len(test_df)),
        "train_return_rate": round(float(y_train.mean()), 4),
        "test_return_rate": round(float(y_test.mean()), 4),
        "train_class_counts": {str(k): int(v) for k, v in y_train.value_counts().items()},
        "test_class_counts": {str(k): int(v) for k, v in y_test.value_counts().items()},
        "split_seed": cfg.SPLIT_SEED,
        "test_size": cfg.TEST_SIZE,
        "order_id_overlap": len(overlap),
        "dataset_profile": cfg.DATASET_PROFILE,
        "missing_values": missing_before,
        "imputation": {
            "strategy": cfg.PREPROCESSOR_CONFIG["imputation"],
            "fitted_on": "train",
            "parameters": imputation_params,
            "train_filled_counts": train_fill,
            "test_filled_counts": test_fill,
        },
        "unknown_category_count": int(adapter_meta.get("unknown_category_count", 0)),
        "group_split_evaluation": {
            "evaluated": True,
            "adopted": False,
            "reason": (
                "契约要求订单级划分，且本数据集 order_id 无重复、训练/测试无订单交叉；"
                "product_id 共 24912 个（平均 1.4 单/商品）几乎无分组意义，"
                "customer_id 共 7903 个（人均 4.4 单）不在契约特征内，"
                "为避免样本量损失和跨集泄漏风险，采用分层随机划分而非 Group split"
            ),
        },
        "class_imbalance": {
            "minority_rate": round(float(min(y.mean(), 1 - y.mean())), 4),
            "warning": (
                "少数类占比低于 20%，决策树必须使用 class_weight='balanced'，"
                "否则会全部预测为多数类，accuracy 虚高但 recall 为 0"
                if min(y.mean(), 1 - y.mean()) < 0.2
                else "类别比例可接受"
            ),
        },
        "leakage_fields": leakage["leakage_fields"],
        "leakage_check_passed": leakage["passed"],
        "quality_checks": quality,
        "derived_field_notes": derived_field_notes(),
        "hdfs_train_path": cfg.HDFS_TRAIN_PATH,
        "hdfs_test_path": cfg.HDFS_TEST_PATH,
        "hdfs_schema_path": cfg.HDFS_SCHEMA_PATH,
        "local_train_path": str(train_path.relative_to(cfg.REPO_ROOT)).replace("\\", "/"),
        "local_test_path": str(test_path.relative_to(cfg.REPO_ROOT)).replace("\\", "/"),
    }
    report_path = cfg.REPORTS_DIR / "feature_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("写入划分: %s / %s" % (train_path, test_path))
    print("写入报告: %s / %s" % (schema_path, report_path))
    print(
        "训练集 %d 行(退货率 %.4f)，测试集 %d 行(退货率 %.4f)"
        % (len(train_df), y_train.mean(), len(test_df), y_test.mean())
    )


if __name__ == "__main__":
    main()
