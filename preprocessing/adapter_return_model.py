"""程序员②：把程序员①交付的 17 列合成宽表适配为契约要求的 7 列训练表。

原始 CSV 与 docs/data-dictionary.md 定义的训练表并不一致，本模块负责：
    Order_ID         -> order_id
    Product_Category -> category（英文类目映射为中文受控类目）
    Product_Price    -> price
    Order_Date       -> season（派生）
    Discount_Applied -> is_promotion（阈值二值化）
    Shipping_Method  -> freight（派生假设值）
    Return_Status    -> returned（按观察窗口口径）

同时剔除所有退货发生后才产生的字段，避免标签泄漏。
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import config as cfg


def load_source(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def derive_season(month: int) -> str:
    if 3 <= month <= 5:
        return "春"
    if 6 <= month <= 8:
        return "夏"
    if 9 <= month <= 11:
        return "秋"
    return "冬"


def build_return_model(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    report: dict = {
        "source_rows": int(len(df)),
        "source_columns": list(df.columns),
        "column_map": cfg.COLUMN_MAP,
        "derived_fields": [],
        "dropped_fields": [],
        "label_policy": cfg.LABEL_POLICY,
        "observation_window_days": cfg.OBSERVATION_WINDOW_DAYS,
    }

    out = pd.DataFrame()
    out["order_id"] = df["Order_ID"].astype(str).str.strip()
    out["category"] = df["Product_Category"].astype(str).str.strip().map(cfg.CATEGORY_MAP)
    out["price"] = pd.to_numeric(df["Product_Price"], errors="coerce")

    order_time = pd.to_datetime(df["Order_Date"], errors="coerce")
    out["season"] = order_time.dt.month.map(
        lambda m: derive_season(int(m)) if pd.notna(m) else None
    )

    discount = pd.to_numeric(df["Discount_Applied"], errors="coerce")
    out["is_promotion"] = (discount >= cfg.PROMOTION_MIN_DISCOUNT).astype("Int64")

    shipping = df["Shipping_Method"].astype(str).str.strip()
    out["freight"] = shipping.map(cfg.SHIPPING_FREIGHT)

    # ---------------- 标签构造 ----------------
    status = df["Return_Status"].astype(str).str.strip()
    days = pd.to_numeric(df["Days_to_Return"], errors="coerce")

    returned_by_status = (status == cfg.VALID_RETURN_STATUS).astype(int)
    returned_by_window = (
        (status == cfg.VALID_RETURN_STATUS)
        & days.notna()
        & (days >= 0)
        & (days <= cfg.OBSERVATION_WINDOW_DAYS)
    ).astype(int)

    out["returned"] = (
        returned_by_status if cfg.LABEL_POLICY == "status" else returned_by_window
    )

    report["label_policy_comparison"] = {
        "status": {
            "returned_1": int(returned_by_status.sum()),
            "returned_0": int((1 - returned_by_status).sum()),
        },
        "window_30d": {
            "returned_1": int(returned_by_window.sum()),
            "returned_0": int((1 - returned_by_window).sum()),
        },
        "diff_rows": int((returned_by_status != returned_by_window).sum()),
    }
    report["days_to_return_stats"] = {
        "count": int(days.notna().sum()),
        "min": float(days.min()) if days.notna().any() else None,
        "max": float(days.max()) if days.notna().any() else None,
        "negative_count": int((days < 0).sum()),
        "beyond_window_count": int((days > cfg.OBSERVATION_WINDOW_DAYS).sum()),
    }

    # ---------------- 派生与剔除说明 ----------------
    report["derived_fields"] = [
        {
            "field": "season",
            "source": "Order_Date",
            "rule": "3-5月春 / 6-8月夏 / 9-11月秋 / 12-2月冬",
            "is_assumption": False,
        },
        {
            "field": "is_promotion",
            "source": "Discount_Applied",
            "rule": "Discount_Applied >= %.2f 记为 1" % cfg.PROMOTION_MIN_DISCOUNT,
            "is_assumption": True,
            "note": "原始数据中 9999/10000 条折扣大于 0，直接按大于 0 判定会退化为常量特征",
        },
        {
            "field": "freight",
            "source": "Shipping_Method",
            "rule": json.dumps(cfg.SHIPPING_FREIGHT, ensure_ascii=False),
            "is_assumption": True,
            "note": "原始数据无真实运费字段，该值为按配送方式的假设值",
        },
        {
            "field": "returned",
            "source": "Return_Status / Days_to_Return",
            "rule": "口径=%s，观察窗口=%d 天" % (cfg.LABEL_POLICY, cfg.OBSERVATION_WINDOW_DAYS),
            "is_assumption": True,
            "note": "原始数据为合并宽表，标签无法由订单表与退货表按 order_id 重建",
        },
    ]
    report["dropped_fields"] = [
        f for f in df.columns if f not in set(cfg.COLUMN_MAP) 
    ] + ["Return_Reason", "Return_Date", "Days_to_Return", "Product_ID", "User_ID"]

    # 未知类目统计
    unmapped = df["Product_Category"].astype(str).str.strip()
    unknown_mask = ~unmapped.isin(cfg.CATEGORY_MAP.keys())
    report["unknown_category_count"] = int(unknown_mask.sum())
    report["unknown_category_values"] = sorted(set(unmapped[unknown_mask].unique()))[:20]

    # 剔除标签无法确定的行
    valid_status = status.isin([cfg.VALID_RETURN_STATUS, "Not Returned"])
    report["rows_dropped_invalid_status"] = int((~valid_status).sum())
    out = out[valid_status.values].copy()

    out = out[["order_id", "category", "price", "is_promotion", "season", "freight", "returned"]]
    out = out.reset_index(drop=True)
    report["output_rows"] = int(len(out))
    return out, report


def build_from_kaggle(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Kaggle 电商数据集 -> 标准 7 列训练表。

    该数据集自带真实运费 shipping_cost，不需要派生假设值。
    discount 为比率（0 ~ 0.3），大于 0 记为促销。
    """
    report: dict = {
        "source_rows": int(len(df)),
        "source_columns": list(df.columns),
        "column_map": cfg.KAGGLE_COLUMN_MAP,
        "derived_fields": [],
        "dropped_fields": [],
        "label_policy": "returned_field",
        "observation_window_days": cfg.OBSERVATION_WINDOW_DAYS,
    }

    out = pd.DataFrame()
    out["order_id"] = df["order_id"].astype(str).str.strip()
    out["category"] = df["category"].astype(str).str.strip().map(cfg.KAGGLE_CATEGORY_MAP)
    out["price"] = pd.to_numeric(df["price"], errors="coerce")

    order_time = pd.to_datetime(
        df["order_date"], dayfirst=cfg.KAGGLE_DATE_DAYFIRST, errors="coerce"
    )
    out["season"] = order_time.dt.month.map(
        lambda m: derive_season(int(m)) if pd.notna(m) else None
    )

    discount = pd.to_numeric(df["discount"], errors="coerce")
    out["is_promotion"] = (discount > cfg.KAGGLE_PROMOTION_RATIO_MIN).astype("Int64")

    out["freight"] = pd.to_numeric(df["shipping_cost"], errors="coerce")

    returned_raw = df["returned"].astype(str).str.strip()
    out["returned"] = (returned_raw == "Yes").astype(int)

    request_date = pd.to_datetime(
        df["request_date"], dayfirst=cfg.KAGGLE_DATE_DAYFIRST, errors="coerce"
    )
    days = (request_date - order_time).dt.days

    window_mask = (out["returned"] == 1) & (days <= cfg.OBSERVATION_WINDOW_DAYS)
    report["label_policy_comparison"] = {
        "returned_field": {
            "returned_1": int(out["returned"].sum()),
            "returned_0": int(len(out) - out["returned"].sum()),
        },
        "window_30d": {
            "returned_1": int(window_mask.sum()),
            "returned_0": int(len(out) - window_mask.sum()),
        },
    }
    report["days_to_return_stats"] = {
        "count": int(days.notna().sum()),
        "min": float(days.min()) if days.notna().any() else None,
        "max": float(days.max()) if days.notna().any() else None,
        "negative_count": int((days < 0).sum()),
        "beyond_window_count": int((days > cfg.OBSERVATION_WINDOW_DAYS).sum()),
    }

    report["derived_fields"] = [
        {
            "field": "season",
            "source": "order_date",
            "rule": "3-5月春 / 6-8月夏 / 9-11月秋 / 12-2月冬（DD/MM/YYYY 解析）",
            "is_assumption": False,
        },
        {
            "field": "is_promotion",
            "source": "discount",
            "rule": "discount > 0 记为 1",
            "is_assumption": False,
        },
        {
            "field": "freight",
            "source": "shipping_cost",
            "rule": "直接使用原始运费字段，无需派生",
            "is_assumption": False,
        },
        {
            "field": "returned",
            "source": "returned",
            "rule": "Yes -> 1，No -> 0",
            "is_assumption": False,
        },
    ]
    # request_date / return_reason 为退货发生后的字段；delivered_date 在下单时不可知
    report["dropped_fields"] = [
        "request_date",
        "return_reason",
        "delivered_date",
        "customer_id",
        "product_id",
        "quantity",
        "payment_method",
        "region",
        "total_amount",
        "profit_margin",
        "customer_age",
        "customer_gender",
    ]

    unmapped = df["category"].astype(str).str.strip()
    unknown_mask = ~unmapped.isin(cfg.KAGGLE_CATEGORY_MAP.keys())
    report["unknown_category_count"] = int(unknown_mask.sum())
    report["unknown_category_values"] = sorted(set(unmapped[unknown_mask].unique()))[:20]

    valid_status = returned_raw.isin(["Yes", "No"])
    report["rows_dropped_invalid_status"] = int((~valid_status).sum())
    out = out[valid_status.values].copy()

    out = out[["order_id", "category", "price", "is_promotion", "season", "freight", "returned"]]
    out = out.reset_index(drop=True)
    report["output_rows"] = int(len(out))
    return out, report


def main(input_csv: Path | None = None) -> pd.DataFrame:
    src = Path(input_csv) if input_csv else cfg.DEFAULT_INPUT_CSV
    df = load_source(src)

    if cfg.DATASET_PROFILE == "kaggle_ecommerce":
        model_df, report = build_from_kaggle(df)
    else:
        model_df, report = build_return_model(df)

    report["dataset_profile"] = cfg.DATASET_PROFILE
    report["source_path"] = str(src)

    cfg.CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    out_csv = cfg.CLEAN_DIR / "return_model.csv"
    model_df.to_csv(out_csv, index=False, encoding="utf-8")

    report_path = cfg.REPORTS_DIR / "adapter_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("写入训练表: %s (%d 行)" % (out_csv, len(model_df)))
    print("写入适配报告: %s" % report_path)
    print("标签口径对比: %s" % json.dumps(report["label_policy_comparison"], ensure_ascii=False))
    return model_df


if __name__ == "__main__":
    main()
