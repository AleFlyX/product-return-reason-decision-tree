# -*- coding: utf-8 -*-
import os

"""
生成模拟退货订单数据（用于验证训练脚本）
========================================
500 条模拟数据，5 个特征 + 1 个标签：
- category: 商品类目（家电/服饰/食品/图书/数码）
- price: 价格（50-500 元）
- is_promotion: 是否促销（0/1）
- season: 季节（春/夏/秋/冬）
- freight: 运费（0-20 元）
- returned: 是否退货（0/1）
"""

import random
import pandas as pd

random.seed(42)

CATEGORIES = ["家电", "服饰", "食品", "图书", "数码"]
SEASONS = ["春", "夏", "秋", "冬"]

def generate_sample():
    category = random.choice(CATEGORIES)
    price = round(random.uniform(50, 500), 2)
    is_promotion = random.choice([0, 1])
    season = random.choice(SEASONS)
    freight = round(random.uniform(0, 20), 2)

    # 退货逻辑：低价 + 促销 + 服饰类目 → 退货率高
    return_prob = 0.1  # 基础退货率 10%

    if category == "服饰":
        return_prob += 0.15
    if price < 150:
        return_prob += 0.1
    if is_promotion == 1:
        return_prob += 0.12
    if category == "图书":
        return_prob -= 0.05

    return_prob = max(0.02, min(0.7, return_prob))
    returned = 1 if random.random() < return_prob else 0

    return {
        "category": category,
        "price": price,
        "is_promotion": is_promotion,
        "season": season,
        "freight": freight,
        "returned": returned,
    }


def main():
    samples = [generate_sample() for _ in range(500)]
    df = pd.DataFrame(samples)

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "clean", "return_model_mock.csv"
    )
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"生成 {len(df)} 条模拟数据")
    print(f"退货率: {df['returned'].mean():.2%}")
    print(f"保存到: {output_path}")
    print(f"\n前 5 行:")
    print(df.head())


if __name__ == "__main__":
    main()
