# -*- coding: utf-8 -*-
"""
程序员③：决策树训练脚本
========================
功能：读取特征数据 → 参数网格实验 → 训练最优决策树 → 评估 → 导出模型产物
产出：return_decision_tree.joblib / metrics.json / feature_importance.json /
      rules.json / model_metadata.json / decision_tree.png / comparison_report.json
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from itertools import product

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

# ============================================================
# 配置
# ============================================================

CATEGORICAL_COLS = ["category", "season"]
NUMERIC_COLS = ["price", "is_promotion", "freight"]
FEATURE_COLS = CATEGORICAL_COLS + NUMERIC_COLS
TARGET_COL = "returned"

# 默认数据版本
DATA_VERSION = "return-model-v1"
MODEL_VERSION = f"dt-{datetime.now().strftime('%Y%m%d')}-002"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "saved")

# HDFS 路径
HDFS_TRAIN_PATH = "/project/product-return/data/feature-split/train/data_version=return-model-v1/part-0.csv"
HDFS_TEST_PATH = "/project/product-return/data/feature-split/test/data_version=return-model-v1/part-0.csv"

# 参数网格
PARAM_GRID = {
    "max_depth": [3, 4, 5, 6],
    "min_samples_leaf": [5, 10, 20],
    "class_weight": [None, "balanced"],
}


# ============================================================
# 1. 加载数据
# ============================================================

def load_data(train_path: str, test_path: str = None):
    df_train = pd.read_csv(train_path)

    if test_path and os.path.exists(test_path):
        df_test = pd.read_csv(test_path)
    else:
        from sklearn.model_selection import train_test_split
        df_train, df_test = train_test_split(
            df_train, test_size=0.3, random_state=42, stratify=df_train[TARGET_COL]
        )

    X_train = df_train[FEATURE_COLS].copy()
    y_train = df_train[TARGET_COL].copy()
    X_test = df_test[FEATURE_COLS].copy()
    y_test = df_test[TARGET_COL].copy()

    print(f"[数据] 训练集: {len(X_train)} 条, 测试集: {len(X_test)} 条")
    print(f"[数据] 训练集退货率: {y_train.mean():.2%}")
    print(f"[数据] 测试集退货率: {y_test.mean():.2%}")

    return X_train, X_test, y_train, y_test


# ============================================================
# 2. 构建 Pipeline（含缺失值处理）
# ============================================================

def build_pipeline(params: dict, imputation_config: dict = None) -> Pipeline:
    imputation_config = imputation_config or {}

    numeric_imputer = SimpleImputer(
        strategy="median",
        fill_value=imputation_config.get("numeric_median", {})
    )
    categorical_imputer = SimpleImputer(
        strategy="constant",
        fill_value=imputation_config.get("categorical_unknown", "UNKNOWN")
    )

    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                Pipeline([
                    ("imputer", categorical_imputer),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                CATEGORICAL_COLS,
            ),
            (
                "numeric",
                Pipeline([
                    ("imputer", numeric_imputer),
                    ("passthrough", "passthrough"),
                ]),
                NUMERIC_COLS,
            ),
        ]
    )

    classifier = DecisionTreeClassifier(random_state=42, **params)

    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("classifier", classifier),
    ])

    return pipeline


# ============================================================
# 3. 训练
# ============================================================

def train(pipeline: Pipeline, X_train, y_train) -> float:
    start = time.time()
    pipeline.fit(X_train, y_train)
    elapsed = time.time() - start
    print(f"[训练] 完成, 耗时 {elapsed:.2f}s")
    return elapsed


# ============================================================
# 4. 评估
# ============================================================

def evaluate(pipeline: Pipeline, X_train, y_train, X_test, y_test) -> dict:
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)

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

    print(f"[评估] 训练集准确率: {metrics['train_accuracy']}")
    print(f"[评估] 测试集准确率: {metrics['test_accuracy']}")
    print(f"[评估] 测试集精确率: {metrics['test_precision']}")
    print(f"[评估] 测试集召回率: {metrics['test_recall']}")
    print(f"[评估] 测试集 F1: {metrics['test_f1']}")

    return metrics


# ============================================================
# 5. 参数网格实验
# ============================================================

def run_grid_experiment(X_train, y_train, X_test, y_test, imputation_config):
    print("\n" + "=" * 70)
    print("  参数网格实验 (4 × 3 × 2 = 24 组)")
    print("=" * 70)

    results = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for max_depth, min_samples_leaf, class_weight in product(
        PARAM_GRID["max_depth"],
        PARAM_GRID["min_samples_leaf"],
        PARAM_GRID["class_weight"],
    ):
        params = {
            "max_depth": max_depth,
            "min_samples_leaf": min_samples_leaf,
            "class_weight": class_weight,
        }

        pipeline = build_pipeline(params, imputation_config)
        pipeline.fit(X_train, y_train)

        y_test_pred = pipeline.predict(X_test)
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1")

        test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
        test_recall = recall_score(y_test, y_test_pred, zero_division=0)
        test_precision = precision_score(y_test, y_test_pred, zero_division=0)
        test_accuracy = accuracy_score(y_test, y_test_pred)

        result = {
            "max_depth": max_depth,
            "min_samples_leaf": min_samples_leaf,
            "class_weight": str(class_weight),
            "cv_f1_mean": round(cv_scores.mean(), 4),
            "cv_f1_std": round(cv_scores.std(), 4),
            "test_accuracy": round(test_accuracy, 4),
            "test_precision": round(test_precision, 4),
            "test_recall": round(test_recall, 4),
            "test_f1": round(test_f1, 4),
        }
        results.append(result)

        print(f"  depth={max_depth} leaf={min_samples_leaf} weight={class_weight} "
              f"→ cv_f1={result['cv_f1_mean']:.4f} test_f1={test_f1:.4f} "
              f"recall={test_recall:.4f}")

    # 按 CV F1 降序排序，选出最优
    results.sort(key=lambda x: x["cv_f1_mean"], reverse=True)
    best = results[0]

    print("\n" + "=" * 70)
    print("  网格实验结果 Top 5")
    print("=" * 70)
    print(f"{'depth':>6} {'leaf':>5} {'weight':>10} {'cv_f1':>8} {'test_f1':>8} {'recall':>8}")
    print("-" * 55)
    for r in results[:5]:
        print(f"{r['max_depth']:>6} {r['min_samples_leaf']:>5} {r['class_weight']:>10} "
              f"{r['cv_f1_mean']:>8.4f} {r['test_f1']:>8.4f} {r['test_recall']:>8.4f}")

    print(f"\n[选择] 最优参数: depth={best['max_depth']} "
          f"leaf={best['min_samples_leaf']} weight={best['class_weight']} "
          f"(cv_f1={best['cv_f1_mean']:.4f})")

    best_params = {
        "max_depth": best["max_depth"],
        "min_samples_leaf": best["min_samples_leaf"],
        "class_weight": None if best["class_weight"] == "None" else best["class_weight"],
    }

    return best_params, results


# ============================================================
# 6. 导出特征重要性
# ============================================================

def export_feature_importance(pipeline: Pipeline) -> list:
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importances = pipeline.named_steps["classifier"].feature_importances_

    sorted_idx = np.argsort(importances)[::-1]

    result = []
    for idx in sorted_idx:
        feat = feature_names[idx]
        imp = round(float(importances[idx]), 4)

        source_field = feat
        if feat.startswith("categorical__"):
            rest = feat.replace("categorical__", "")
            for col in CATEGORICAL_COLS:
                if rest.startswith(f"{col}_"):
                    source_field = col
                    break
        elif feat.startswith("numeric__"):
            source_field = feat.replace("numeric__", "")

        clean_name = feat.replace("categorical__", "").replace("numeric__", "")
        result.append({
            "feature": clean_name,
            "importance": imp,
            "source_field": source_field,
        })

    print(f"[特征重要性] Top 3: {[r['feature'] for r in result[:3]]}")
    return result


# ============================================================
# 7. 导出规则（修复：n_node_samples + 可读规则）
# ============================================================

def export_rules(pipeline: Pipeline, X_train, y_train) -> list:
    tree = pipeline.named_steps["classifier"]
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    feature_names = [f.replace("categorical__", "").replace("numeric__", "") for f in feature_names]

    t = tree.tree_
    n_nodes = t.node_count
    children_left = t.children_left
    children_right = t.children_right
    feature = t.feature
    threshold = t.threshold
    n_node_samples = t.n_node_samples
    value = t.value

    # 构建 One-Hot 特征到原始字段+值的映射
    # 例: "category_食品生鲜" → ("category", "食品生鲜")
    #     "season_冬" → ("season", "冬")
    #     "price" → ("price", None)
    def parse_feature_name(name):
        for col in CATEGORICAL_COLS:
            if name.startswith(f"{col}_"):
                value = name[len(col) + 1:]
                return col, value
        return name, None

    rules = []
    leaf_id = 0

    def dfs(node_id, conditions):
        nonlocal leaf_id
        if children_left[node_id] == children_right[node_id]:
            # 叶子节点：使用 n_node_samples 获取真实样本数
            samples = int(n_node_samples[node_id])
            class_counts = value[node_id][0]
            total = class_counts.sum()
            class_idx = np.argmax(class_counts)

            if total > 0:
                prob_returned = round(float(class_counts[1] / total), 4)
            else:
                prob_returned = 0.0

            # 转换条件为可读格式
            readable = []
            for cond in conditions:
                col, val = parse_feature_name(cond["feature"])
                if val is not None:
                    # One-Hot 特征: category_食品生鲜 <= 0.5 → category != 食品生鲜
                    #              category_食品生鲜 > 0.5  → category = 食品生鲜
                    if cond["type"] == "le":
                        readable.append(f"{col} != {val}")
                    else:
                        readable.append(f"{col} = {val}")
                else:
                    # 数值特征: price <= 45.5
                    if cond["type"] == "le":
                        readable.append(f"{col} <= {cond['value']:.2f}")
                    else:
                        readable.append(f"{col} > {cond['value']:.2f}")

            rules.append({
                "rule_id": f"leaf-{leaf_id}",
                "conditions": readable,
                "predicted_returned": int(class_idx),
                "return_probability": prob_returned,
                "sample_count": samples,
                "model_version": MODEL_VERSION,
            })
            leaf_id += 1
            return

        feat_name = feature_names[feature[node_id]]
        # 左子树（<= threshold）
        dfs(children_left[node_id],
            conditions + [{"feature": feat_name, "type": "le", "value": threshold[node_id]}])
        # 右子树（> threshold）
        dfs(children_right[node_id],
            conditions + [{"feature": feat_name, "type": "gt", "value": threshold[node_id]}])

    dfs(0, [])

    rules.sort(key=lambda x: x["sample_count"], reverse=True)
    print(f"[规则] 共 {len(rules)} 条叶子规则")
    for r in rules[:3]:
        print(f"  {r['rule_id']}: {r['conditions']} → returned={r['predicted_returned']} "
              f"(samples={r['sample_count']}, prob={r['return_probability']})")
    return rules


# ============================================================
# 8. 画决策树
# ============================================================

def plot_decision_tree(pipeline: Pipeline, output_path: str):
    tree = pipeline.named_steps["classifier"]
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    feature_names = [f.replace("categorical__", "").replace("numeric__", "") for f in feature_names]

    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(24, 12))
    plot_tree(
        tree, filled=True, feature_names=feature_names,
        class_names=["未退货", "退货"], rounded=True, fontsize=8, ax=ax,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[可视化] 决策树图已保存: {output_path}")


# ============================================================
# 9. 获取 Git commit
# ============================================================

def get_git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=os.path.dirname(__file__)
        )
        return result.stdout.strip()[:12] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_dependency_versions():
    versions = {}
    for pkg in ["pandas", "numpy", "scikit-learn", "matplotlib", "joblib"]:
        try:
            mod = __import__(pkg.replace("-", "_"))
            versions[pkg] = mod.__version__
        except Exception:
            versions[pkg] = "unknown"
    versions["python"] = sys.version.split()[0]
    return versions


# ============================================================
# 10. 保存所有产物
# ============================================================

def save_all(pipeline, metrics, feature_importance, rules, train_time, params,
             grid_results, imputation_config, comparison_data):
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

    # 5. 网格实验结果
    with open(os.path.join(OUTPUT_DIR, "grid_experiment.json"), "w", encoding="utf-8") as f:
        json.dump(grid_results, f, ensure_ascii=False, indent=2)

    # 6. 对比报告
    with open(os.path.join(OUTPUT_DIR, "comparison_report.json"), "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)

    # 7. 模型元数据（补全）
    metadata = {
        "model_name": "decision-tree",
        "model_version": MODEL_VERSION,
        "data_version": DATA_VERSION,
        "model_type": "DecisionTreeClassifier",
        "pipeline_version": "1.0",
        "params": params,
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "train_time_seconds": round(train_time, 2),
        "train_samples": metrics["train_samples"],
        "test_samples": metrics["test_samples"],
        "created_at": datetime.now().isoformat(),
        "artifact_path": f"/project/product-return/model/model_name=decision-tree/model_version={MODEL_VERSION}/",
        "status": "ready",
        "hdfs_train_path": HDFS_TRAIN_PATH,
        "hdfs_test_path": HDFS_TEST_PATH,
        "git_commit": get_git_commit(),
        "dependency_versions": get_dependency_versions(),
        "feature_processing": {
            "categorical_features": CATEGORICAL_COLS,
            "numeric_features": NUMERIC_COLS,
            "encoding": "OneHotEncoder(handle_unknown='ignore')",
            "imputation": imputation_config,
            "scaling": "none",
        },
        "grid_experiment_best": grid_results[0] if grid_results else None,
    }
    with open(os.path.join(OUTPUT_DIR, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 8. 决策树图片
    plot_decision_tree(pipeline, os.path.join(OUTPUT_DIR, "decision_tree.png"))

    print(f"[完成] 所有产物已保存到: {OUTPUT_DIR}")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="决策树训练脚本")
    parser.add_argument("--train", required=True, help="训练集 CSV 路径")
    parser.add_argument("--test", default=None, help="测试集 CSV 路径")
    parser.add_argument("--data-version", default="return-model-v1", help="数据版本号")
    args = parser.parse_args()

    global DATA_VERSION
    DATA_VERSION = args.data_version

    print("=" * 70)
    print("  决策树训练开始")
    print(f"  模型版本: {MODEL_VERSION}")
    print(f"  数据版本: {DATA_VERSION}")
    print("=" * 70)

    # 1. 加载数据
    X_train, X_test, y_train, y_test = load_data(args.train, args.test)

    # 2. 读取 feature_schema.json 获取缺失值填补参数
    schema_path = os.path.join(
        os.path.dirname(__file__), "..",
        "data", "feature-split", "schema",
        "data_version=return-model-v1", "feature_schema.json"
    )
    imputation_config = {
        "numeric_median": {"price": 45.44, "is_promotion": 0.0, "freight": 6.1},
        "categorical_unknown": {"category": "UNKNOWN", "season": "UNKNOWN"},
    }
    if os.path.exists(schema_path):
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        imputation_config = schema.get("imputation_parameters", imputation_config)
        print(f"[配置] 缺失值填补参数: {imputation_config}")

    # 3. 参数网格实验
    best_params, grid_results = run_grid_experiment(
        X_train, y_train, X_test, y_test, imputation_config
    )

    # 4. 用最优参数训练最终模型
    print("\n" + "=" * 70)
    print("  最终模型训练")
    print("=" * 70)
    pipeline = build_pipeline(best_params, imputation_config)
    train_time = train(pipeline, X_train, y_train)
    metrics = evaluate(pipeline, X_train, y_train, X_test, y_test)
    feature_importance = export_feature_importance(pipeline)
    rules = export_rules(pipeline, X_train, y_train)

    # 5. 构建对比报告数据
    comparison_data = {
        "experiment": "parameter grid search (4×3×2=24 combinations)",
        "data_version": DATA_VERSION,
        "model_version": MODEL_VERSION,
        "dataset": {
            "train_samples": metrics["train_samples"],
            "test_samples": metrics["test_samples"],
            "return_rate_train": metrics["returned_rate_train"],
            "return_rate_test": metrics["returned_rate_test"],
        },
        "best_params": best_params,
        "best_metrics": {
            "test_accuracy": metrics["test_accuracy"],
            "test_precision": metrics["test_precision"],
            "test_recall": metrics["test_recall"],
            "test_f1": metrics["test_f1"],
            "confusion_matrix": metrics["confusion_matrix"],
        },
        "grid_results_top5": grid_results[:5],
        "conclusion": (
            f"选用 cv_f1 最高的参数组合: depth={best_params['max_depth']}, "
            f"leaf={best_params['min_samples_leaf']}, "
            f"class_weight={best_params['class_weight']}. "
            f"基于 5 折交叉验证 F1 选择，而非单独依赖测试集召回率。"
        ),
    }

    # 6. 保存所有产物
    save_all(pipeline, metrics, feature_importance, rules, train_time,
             best_params, grid_results, imputation_config, comparison_data)

    print("=" * 70)
    print("  训练完成 ✅")
    print("=" * 70)


if __name__ == "__main__":
    main()
