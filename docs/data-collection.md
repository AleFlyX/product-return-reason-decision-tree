# 程序员①工作任务书：订单与退货数据采集、清洗

## 一、岗位定位

负责项目的数据入口，完成：

```text
数据源确定
  → 原始订单/退货数据采集
  → 字段整理
  → 数据清洗
  → 订单与退货关联
  → returned 标签构造
  → 数据质量检查
  → 标准训练数据交付
```

交付对象包括程序员②（特征工程）、程序员③（模型）、程序员④（数据访问）和程序员⑤（前端分析）。

## 二、数据源选择

优先使用经过授权的公开数据集、课程提供数据或项目自行生成的脱敏测试数据。若必须网络采集，应遵守目标网站的服务条款、`robots.txt` 和课程要求，不绕过登录、验证码等访问控制，不采集姓名、手机号、地址等不必要的个人信息。

推荐保留两张原始表：

```text
data/raw/orders_raw.csv
data/raw/returns_raw.csv
```

原始文件只读保存，清洗过程必须输出新文件，不能直接覆盖原始数据。

## 三、原始数据与标准字段

### 1. 订单表

至少整理为：

```text
order_id, category, price, is_promotion, order_time, season, freight
```

### 2. 退货表

至少整理为：

```text
return_id, order_id, return_date, return_status, return_reason, refund_amount
```

字段含义、类型、单位和质量规则见 [`data-dictionary.md`](data-dictionary.md)。

## 四、清洗流程

```text
读取原始 CSV
  ↓
统一列名、编码和空白字符
  ↓
订单和退货表分别去重
  ↓
数值字段类型转换
  ↓
类别、促销标记和季节归一化
  ↓
过滤明显异常值，记录处理数量
  ↓
按 order_id 关联退货记录
  ↓
依据观察窗口生成 returned
  ↓
输出清洗文件和质量报告
```

### 1. 去重

- 订单表以 `order_id` 检查重复；
- 退货表以 `return_id` 检查重复；
- 无法判断哪条记录正确时，不静默覆盖，保留一条进入训练数据并在报告中记录处理规则。

### 2. 缺失值

- `order_id`、`category`、`price` 为空的订单不能进入训练表；
- `is_promotion` 缺失时不能默认填成促销或非促销，应按数据源规则处理；
- `season` 优先由有效的 `order_time` 派生；
- 退货表缺少 `order_id` 的记录计入无主退货统计。

### 3. 类型和格式

```text
“299元”       → 299
“是/否”        → 1/0
“2026-07-01”  → datetime
前后空格       → 去除
同义类目名称   → 映射为统一类目
```

### 4. 异常值

至少检查：

```text
price <= 0
freight < 0
is_promotion 不属于 0/1
order_time 无法解析
return_date 早于 order_time
```

异常值的删除、修正或保留都必须有理由并写入清洗报告，不能为了提升模型指标随意删除样本。

## 五、标签构造

本项目默认使用 `order_time` 起 30 个自然日作为退货观察窗口。若数据源提供更可靠的完成时间，应在清洗配置中明确改用该字段，并在报告中记录实际窗口起点。

```text
有效退货记录存在且 return_date 在观察窗口内 → returned = 1
否则                                             → returned = 0
```

有效退货记录必须先由原始 `return_status` 映射得到。默认只接受数据源映射为“已确认退货”的状态，拒绝、取消和测试记录不计入标签。一个订单的多条有效退货记录只生成一个 `returned=1`。退货原因、退款金额和退货状态保留在分析数据中，但不得进入模型输入。

## 六、输出文件

```text
data/
├── raw/
│   ├── orders_raw.csv
│   └── returns_raw.csv
├── clean/
│   ├── orders_clean.csv
│   ├── returns_clean.csv
│   └── return_model.csv
└── reports/
    └── cleaning_report.json
```

如果需要进入 HDFS，再额外输出：

```text
data/clean/return_model.tsv
```

训练表 `return_model.csv` 至少包含：

```text
order_id, category, price, is_promotion, season, freight, returned
```

## 七、清洗报告

报告至少记录：

```json
{
  "orders_before": 0,
  "orders_after": 0,
  "returns_before": 0,
  "returns_after": 0,
  "duplicate_orders": 0,
  "duplicate_returns": 0,
  "missing_rows_removed": 0,
  "invalid_rows_removed": 0,
  "orphan_returns": 0,
  "returned_count": 0,
  "not_returned_count": 0,
  "observation_window_days": 30,
  "observation_window_start": "order_time",
  "valid_return_statuses": ["已确认退货"]
}
```

示例中的数量 `0` 只是格式示意，不能当作最终实验数据；状态名称应替换为数据源的实际映射结果。

## 八、交付验收

- [ ] 原始订单和退货文件来源合法且可追溯。
- [ ] 订单和退货字段与数据字典一致。
- [ ] 清洗过程不覆盖原始数据。
- [ ] `order_id` 在训练表中唯一。
- [ ] 缺失、重复、异常和无主退货数量已统计。
- [ ] `returned` 可以按观察窗口重新生成。
- [ ] 退货发生后的字段没有进入训练表。
- [ ] 已输出 CSV；若启用大数据链路，已输出 TSV。
- [ ] 程序员②可以直接读取 `return_model.csv`。

## 九、与其他模块的协作

- 与产品经理确认观察窗口、类目粒度和数据权限；
- 与程序员②确认特征是否足够、类别是否统一；
- 与程序员③确认标签分布和训练表行级粒度；
- 与程序员④确认 CSV/TSV 字段顺序和分隔符；
- 与程序员⑤确认概览接口需要的统计字段。
