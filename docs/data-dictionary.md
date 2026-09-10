# 商品退货分析数据字典

## 一、数据集关系

```text
orders_raw.csv
    └── order_id ──┐
                   ├── 订单级关联与标签构造 ──→ return_model.csv
returns_raw.csv
```

训练表以订单表为主表，一个 `order_id` 最终只能有一行。退货表可以有多条明细，但只要在观察窗口内存在有效退货，就将订单标签设为 `returned=1`。

## 二、订单表字段

| 字段 | 类型 | 必填 | 单位/取值 | 说明 |
| --- | --- | --- | --- | --- |
| `order_id` | string | 是 | 唯一字符串 | 订单标识，建议使用脱敏编号 |
| `category` | string | 是 | 受控类目集合 | 商品类目 |
| `price` | float | 是 | 元，`>0` | 商品成交单价 |
| `is_promotion` | int | 是 | `0/1` | 下单时是否参与促销 |
| `order_time` | datetime | 是 | ISO 8601 | 下单时间，用于派生季节 |
| `season` | string | 否 | 春/夏/秋/冬 | 若原始数据没有，可由 `order_time` 派生 |
| `freight` | float | 是 | 元，`>=0` | 订单运费 |
| `quantity` | int | 否 | 正整数 | 商品数量，若纳入项目需同步修改模型特征 |

## 三、退货表字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `return_id` | string | 是 | 退货记录唯一标识 |
| `order_id` | string | 是 | 关联订单编号 |
| `return_date` | datetime | 是 | 退货申请或确认时间 |
| `return_status` | string | 是 | 退货状态 |
| `return_reason` | string | 否 | 退货原因，结果分析字段 |
| `refund_amount` | float | 否 | 退款金额，结果分析字段 |

退货表中的 `return_reason`、`return_date`、`refund_amount` 和售后状态字段不得进入下单时的预测特征。

## 四、训练表字段

| 字段 | 类型 | 来源 | 用途 |
| --- | --- | --- | --- |
| `order_id` | string | 订单表 | 追溯，不进模型 |
| `category` | string | 订单表 | 特征 |
| `price` | float | 订单表 | 特征 |
| `is_promotion` | int | 订单表 | 特征 |
| `season` | string | 订单表或派生 | 特征 |
| `freight` | float | 订单表 | 特征 |
| `returned` | int | 关联退货表 | 标签 |

## 五、质量规则

| 检查项 | 规则 | 处理 |
| --- | --- | --- |
| 主键 | `order_id` 非空且唯一 | 重复订单按数据源规则保留，无法判断时进入异常报告 |
| 类目 | 非空且属于受控集合 | 清理空格、统一别名，无法识别的进入异常报告 |
| 价格 | `price > 0` | 删除明显错误值并记录数量 |
| 促销 | 只能为 `0/1` | 统一“是/否”等原始值 |
| 季节 | 只能为四季之一 | 优先由订单时间派生 |
| 运费 | `freight >= 0` | 负数视为异常 |
| 标签 | `returned` 只能为 `0/1` | 按观察窗口重建，不直接相信原始混合字段 |
| 关联 | 退货 `order_id` 必须能在订单表找到 | 无主退货单独统计，不加入训练表 |
