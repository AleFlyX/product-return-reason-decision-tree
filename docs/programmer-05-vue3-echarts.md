# 程序员⑤：Vue 3、ECharts、页面交互和系统展示

## 一、岗位目标

程序员⑤负责把 FastAPI 返回的退货统计、预测结果、模型指标和规则，做成可演示、可操作、可解释的 Vue 3 页面。前端不直接连接 HDFS 或 HBase，只通过 FastAPI 获取数据和依赖状态。

## 二、当前工程约定

当前前端是 Vue 3 + Vite + TypeScript + Vue Router + Pinia 初始工程：

```text
frontend/src/
├── api/
├── components/
├── router/
├── stores/
├── views/
├── App.vue
└── main.ts
```

建议新增：

```text
frontend/src/
├── api/
│   ├── client.ts
│   ├── stats.ts
│   ├── orders.ts
│   └── model.ts
├── components/
│   ├── MetricCard.vue
│   ├── DependencyStatus.vue
│   ├── ReturnRateChart.vue
│   ├── FeatureImportanceChart.vue
│   ├── ConfusionMatrix.vue
│   ├── RuleList.vue
│   └── RequestState.vue
└── views/
    ├── OverviewView.vue
    ├── ReturnAnalysisView.vue
    ├── ReturnPredictionView.vue
    └── ModelExplanationView.vue
```

## 三、页面与接口

### 1. 概览页

调用：

```text
GET /api/health
GET /api/stats/overview
```

展示：

- 订单总数；
- 退货总数；
- 整体退货率；
- 商品类目数；
- 平均商品价格；
- HDFS 状态；
- HBase 状态；
- 当前模型版本；
- 是否处于降级模式。

### 2. 退货分析页

调用：

```text
GET /api/stats/by-category
GET /api/stats/by-promotion
GET /api/stats/by-price-range
```

使用 ECharts 展示：

- 各类目样本量和退货率；
- 促销与非促销退货率；
- 价格区间退货率；
- 退货/未退货数量对比。

图表同时显示数量和比例，避免小样本类目造成误导。

### 3. 退货预测页

请求字段：

```text
category
price
is_promotion
season
freight
```

提交到：

```text
POST /api/returns/predict
```

展示：

- 预测是否退货；
- 退货概率；
- 未退货概率；
- 模型版本；
- 请求是否成功写入预测记录。

不允许把 `return_reason`、`refund_amount` 或 `return_status` 放入表单。

### 4. 模型解释页

调用：

```text
GET /api/model/metrics
GET /api/model/features
GET /api/model/rules
```

展示：

- Accuracy、Precision、Recall、F1；
- 混淆矩阵；
- 特征重要性条形图；
- 规则条件；
- 叶节点样本量；
- 当前模型版本和数据版本。

## 四、API 封装

Axios 基础地址：

```text
VITE_API_BASE_URL=http://localhost:8000
```

`client.ts` 统一处理：

- 超时；
- 4xx 字段错误；
- 503 HDFS/HBase 不可用；
- 网络失败；
- 统一响应数据类型。

页面组件不能重复拼接 URL，也不能直接读取环境变量后各自实现错误解析。

## 五、交互状态

每个页面必须覆盖：

```text
加载中
成功
成功但无数据
HDFS/HBase 不可用
模型未加载
请求失败
表单校验失败
提交中
预测成功
```

后端依赖不可用时，页面要明确显示“数据服务不可用”，不能显示零值或空列表让用户误以为系统没有数据。

## 六、路由规划

```text
/                  → OverviewView
/analysis          → ReturnAnalysisView
/prediction        → ReturnPredictionView
/model             → ModelExplanationView
```

路由切换后图表必须销毁或复用实例，避免重复初始化 ECharts 造成内存泄漏。

## 七、ECharts 约定

- 退货率使用百分比格式；
- API 原始概率保持 0 到 1；
- 类目图按退货率降序；
- 特征重要性按重要性降序；
- 混淆矩阵标明行列含义；
- 空数组显示明确的无数据状态；
- 图表容器具有稳定高度，避免页面抖动。

## 八、联调顺序

```text
先调用 /api/health
  → 确认 HDFS/HBase 为 ok
  → 请求概览统计
  → 请求类目分析
  → 提交预测
  → 展示模型指标和规则
```

若 `/api/health` 返回 `degraded=true`，前端应显示降级标识，但仍可以在开发环境进行页面联调。

## 九、验收清单

- [ ] 使用 Vue 3 + TypeScript，路由和页面结构清晰。
- [ ] 所有数据来自 FastAPI，不直接连接 HDFS/HBase。
- [ ] 概览页显示 HDFS/HBase 和模型状态。
- [ ] 退货率图表同时显示样本量。
- [ ] 预测表单不包含标签泄漏字段。
- [ ] 模型页能展示混淆矩阵、特征重要性和规则。
- [ ] 503、网络失败、空数据和表单错误均有界面反馈。
- [ ] 前端构建和类型检查通过。
