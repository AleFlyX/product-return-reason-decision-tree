# -*- coding: utf-8 -*-
"""
程序员③：决策树训练脚本
========================
功能：读取特征数据 → 训练决策树 → 评估 → 导出模型产物
产出：return_decision_tree.joblib / metrics.json / feature_importance.json / rules.json / model_metadata.json / decision_tree.png
"""

import os
import json
import time
import argparse
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

# ============================================================
# 配置
# ============================================================

# 特征列定义（与程序员②约定一致）
CATEGORICAL_COLS = ["category", "season"]
NUMERIC_COLS = ["price", "is_promotion", "freight"]
FEATURE_COLS = CATEGORICAL_COLS + NUMERIC_COLS
TARGET_COL = "returned"

# 模型默认参数（基线配置）
DEFAULT_PARAMS = {
    "max_depth": 4,
    "min_samples_leaf": 10,
    "random_state": 42,
    "class_weight": None,
}

# 平衡类权重参数（处理类别不均衡）
BALANCED_PARAMS = {
    "max_depth": 4,
    "min_samples_leaf": 10,
    "random_state": 42,
    "class_weight": "balanced",
}

# 模型版本号
MODEL_VERSION = f"dt-{datetime.now().strftime('%Y%m%d')}-001"
DATA_VERSION = "mock-v1"  # TODO: 接入真实数据后替换

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "saved")


# ============================================================
# 1. 加载数据
# ============================================================

def load_data(train_path: str, test_path: str = None):
    """加载训练集和测试集。

    如果只传 train_path，则按 7:3 分层划分。
    """
    df_train = pd.read_csv(train_path)

    if test_path and os.path.exists(test_path):
        df_test = pd.read_csv(test_path)
    else:
        # 分层划分
        df_train, df_test = train_test_split(
            df_train,
            test_size=0.3,
            random_state=42,
            stratify=df_train[TARGET_COL],
        )

    X_train = df_train[FEATURE_COLS]
    y_train = df_train[TARGET_COL]
    X_test = df_test[FEATURE_COLS]
    y_test = df_test[TARGET_COL]

    print(f"[数据] 训练集: {len(X_train)} 条, 测试集: {len(X_test)} 条")
    print(f"[数据] 训练集退货率: {y_train.mean():.2%}")
    print(f"[数据] 测试集退货率: {y_test.mean():.2%}")

    return X_train, X_test, y_train, y_test


# ============================================================
# 2. 构建 Pipeline
# ============================================================

def build_pipeline(params: dict = None) -> Pipeline:
    """构建 预处理 + 决策树 的完整 Pipeline。"""
    params = params or DEFAULT_PARAMS

    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_COLS,
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_COLS,
            ),
        ]
    )

    classifier = DecisionTreeClassifier(**params)

    pipeline = Pipeline(
        [
            ("preprocess", preprocessor),
            ("classifier", classifier),
        ]
    )

    return pipeline


# ============================================================
# 3. 训练
# ============================================================

def train(pipeline: Pipeline, X_train, y_train) -> float:
    """训练模型，返回训练耗时（秒）。"""
    start = time.time()
    pipeline.fit(X_train, y_train)
    elapsed = time.time() - start
    print(f"[训练] 完成, 耗时 {elapsed:.2f}s")
    return elapsed


# ============================================================
# 4. 评估
# ============================================================

def evaluate(pipeline: Pipeline, X_train, y_train, X_test, y_test) -> dict:
    """评估模型，返回指标字典。"""
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)
    y_test_proba = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "train_accuracy": round(accuracy_score(y_train, y_train_pred), 4),
        "test_accuracy": round(accuracy_score(y_test, y_test_pred), 4),
        "test_precision": round(precision_score(y_test, y_test_pred, zero_division=0), 4),
        "test_recall": round(recall_score(y_test, y_test_pred, zero_division=0), 4),
        "test_f1": round(f1_score(y_test, y_test_pred, zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y_test, y_test_pred).tolist(),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "returned_rate_train": round(y_train.mean(), 4),
        "returned_rate_test": round(y_test.mean(), 4),
    }

    print("[评估] 训练集准确率:", metrics["train_accuracy"])
    print("[评估] 测试集准确率:", metrics["test_accuracy"])
    print("[评估] 测试集精确率:", metrics["test_precision"])
    print("[评估] 测试集召回率:", metrics["test_recall"])
    print("[评估] 测试集 F1:", metrics["test_f1"])
    print("[评估] 混淆矩阵:", metrics["confusion_matrix"])

    return metrics


# ============================================================
# 5. 导出特征重要性
# ============================================================

def export_feature_importance(pipeline: Pipeline) -> list:
    """导出特征重要性，还原 One-Hot 编码对应的原始字段。"""
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importances = pipeline.named_steps["classifier"].feature_importances_

    # 按重要性降序
    sorted_idx = np.argsort(importances)[::-1]

    result = []
    for idx in sorted_idx:
        feat = feature_names[idx]
        imp = round(float(importances[idx]), 4)

        # 还原原始字段名
        # One-Hot 编码格式: categorical__category_服饰 → category
        # 数值透传格式: numeric__price → price
        source_field = feat
        if feat.startswith("categorical__"):
            rest = feat.replace("categorical__", "")
            for col in CATEGORICAL_COLS:
                if rest.startswith(f"{col}_"):
                    source_field = col
                    break
        elif feat.startswith("numeric__"):
            source_field = feat.replace("numeric__", "")

        result.append({
            "feature": feat.replace("categorical__", "").replace("numeric__", ""),
            "importance": imp,
            "source_field": source_field,
        })

    print(f"[特征重要性] Top 3: {result[:3]}")
    return result


# ============================================================
# 6. 导出规则（叶子节点）
# ============================================================

def export_rules(pipeline: Pipeline, X_train, y_train) -> list:
    """导出决策树叶子节点的结构化规则。"""
    tree = pipeline.named_steps["classifier"]
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    feature_names = [f.replace("categorical__", "").replace("numeric__", "") for f in feature_names]

    n_nodes = tree.tree_.node_count
    children_left = tree.tree_.children_left
    children_right = tree.tree_.children_right
    feature = tree.tree_.feature
    threshold = tree.tree_.threshold
    value = tree.tree_.value

    # 遍历所有节点，找到叶子节点
    rules = []
    leaf_id = 0

    def dfs(node_id, conditions):
        nonlocal leaf_id
        if children_left[node_id] == children_right[node_id]:
            # 叶子节点
            samples = int(value[node_id].sum())
            class_idx = np.argmax(value[node_id])
            prob = round(float(value[node_id][0][class_idx] / samples), 4) if samples > 0 else 0

            # 把 One-Hot 特征名还原成可读条件
            readable_conditions = []
            for cond in conditions:
                feat_name = cond["feature"]
                if cond["type"] == "le":
                    readable_conditions.append(f"{feat_name} <= {cond['value']:.2f}")
                else:
                    readable_conditions.append(f"{feat_name} > {cond['value']:.2f}")

            rules.append({
                "rule_id": f"leaf-{leaf_id}",
                "conditions": readable_conditions,
                "predicted_returned": int(class_idx),
                "return_probability": prob if class_idx == 1 else round(1 - prob, 4),
                "sample_count": samples,
                "model_version": MODEL_VERSION,
            })
            leaf_id += 1
            return

        # 左子树（<= threshold）
        feat_name = feature_names[feature[node_id]]
        dfs(children_left[node_id], conditions + [{"feature": feat_name, "type": "le", "value": threshold[node_id]}])

        # 右子树（> threshold）
        dfs(children_right[node_id], conditions + [{"feature": feat_name, "type": "gt", "value": threshold[node_id]}])

    dfs(0, [])

    # 按样本量降序
    rules.sort(key=lambda x: x["sample_count"], reverse=True)
    print(f"[规则] 共 {len(rules)} 条叶子规则")
    return rules


# ============================================================
# 7. 画决策树
# ============================================================

def plot_decision_tree(pipeline: Pipeline, output_path: str):
    """画决策树并保存为图片。"""
    tree = pipeline.named_steps["classifier"]
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    feature_names = [f.replace("categorical__", "").replace("numeric__", "") for f in feature_names]

    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(20, 10))
    plot_tree(
        tree,
        filled=True,
        feature_names=feature_names,
        class_names=["未退货", "退货"],
        rounded=True,
        fontsize=9,
        ax=ax,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[可视化] 决策树图已保存: {output_path}")


# ============================================================
# 8. 保存所有产物
# ============================================================

def save_all(pipeline, metrics, feature_importance, rules, train_time, params):
    """保存模型和所有元数据文件。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. 模型 Pipeline
    model_path = os.path.join(OUTPUT_DIR, "return_decision_tree.joblib")
    joblib.dump(pipeline, model_path)
    print(f"[保存] 模型: {model_path}")

    # 2. 评估指标
    with open(os.path.join(OUTPUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # 3. 特征重要性
    with open(os.path.join(OUTPUT_DIR, "feature_importance.json"), "w", encoding="utf-8") as f:
        json.dump(feature_importance, f, ensure_ascii=False, indent=2)

    # 4. 规则
    with open(os.path.join(OUTPUT_DIR, "rules.json"), "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    # 5. 模型元数据
    metadata = {
        "model_name": "decision-tree",
        "model_version": MODEL_VERSION,
        "data_version": DATA_VERSION,
        "model_type": "DecisionTreeClassifier",
        "params": params,
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "train_time_seconds": round(train_time, 2),
        "train_samples": metrics["train_samples"],
        "test_samples": metrics["test_samples"],
        "created_at": datetime.now().isoformat(),
        "artifact_path": f"/project/product-return/model/model_name=decision-tree/model_version={MODEL_VERSION}/",
        "status": "ready",
    }
    with open(os.path.join(OUTPUT_DIR, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 6. 决策树图片
    plot_decision_tree(pipeline, os.path.join(OUTPUT_DIR, "decision_tree.png"))

    print(f"[完成] 所有产物已保存到: {OUTPUT_DIR}")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="决策树训练脚本")
    parser.add_argument("--train", required=True, help="训练集 CSV 路径")
    parser.add_argument("--test", default=None, help="测试集 CSV 路径（可选）")
    parser.add_argument("--data-version", default="mock-v1", help="数据版本号")
    parser.add_argument("--class-weight", default=None,
                        help="类权重: None / balanced (默认 None)")
    parser.add_argument("--compare", action="store_true",
                        help="对比 baseline vs balanced 两种配置")
    args = parser.parse_args()

    global DATA_VERSION
    DATA_VERSION = args.data_version

    print("=" * 60)
    print("  决策树训练开始")
    print(f"  模型版本: {MODEL_VERSION}")
    print(f"  数据版本: {DATA_VERSION}")
    print("=" * 60)

    # 1. 加载数据
    X_train, X_test, y_train, y_test = load_data(args.train, args.test)

    # 对比模式：跑 baseline 和 balanced 两组
    if args.compare:
        print("\n" + "=" * 60)
        print("  对比实验: baseline vs balanced")
        print("=" * 60)

        results = {}
        for name, params in [("baseline", DEFAULT_PARAMS), ("balanced", BALANCED_PARAMS)]:
            print(f"\n--- {name} ---")
            pipeline = build_pipeline(params)
            train_time = train(pipeline, X_train, y_train)
            metrics = evaluate(pipeline, X_train, y_train, X_test, y_test)
            results[name] = metrics

        print("\n" + "=" * 60)
        print("  对比总结")
        print("=" * 60)
        print(f"{'指标':<15} {'baseline':>10} {'balanced':>10}")
        print("-" * 40)
        for key in ["test_accuracy", "test_precision", "test_recall", "test_f1"]:
            print(f"{key:<15} {results['baseline'][key]:>10.4f} {results['balanced'][key]:>10.4f}")

        # 用 balanced 模型作为最终产物
        print("\n[决策] 使用 balanced 模型作为最终产出（召回率更高）")
        final_params = BALANCED_PARAMS
    else:
        # 单次训练模式
        params = dict(DEFAULT_PARAMS)
        if args.class_weight == "balanced":
            params = dict(BALANCED_PARAMS)
        final_params = params

    # 最终训练（产出所有文件）
    print("\n" + "=" * 60)
    print("  最终模型训练")
    print("=" * 60)
    pipeline = build_pipeline(final_params)
    train_time = train(pipeline, X_train, y_train)
    metrics = evaluate(pipeline, X_train, y_train, X_test, y_test)
    feature_importance = export_feature_importance(pipeline)
    rules = export_rules(pipeline, X_train, y_train)
    save_all(pipeline, metrics, feature_importance, rules, train_time, final_params)

    print("=" * 60)
    print("  训练完成 ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
