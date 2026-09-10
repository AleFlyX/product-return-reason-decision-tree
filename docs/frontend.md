# Vue 3 前端与可视化

## 一、页面结构

```text
frontend/src/
├── api/
│   ├── stats.js
│   ├── orders.js
│   └── model.js
├── views/
│   ├── Overview.vue
│   ├── ReturnAnalysis.vue
│   ├── ReturnPrediction.vue
│   └── ModelExplanation.vue
├── components/
│   ├── MetricCard.vue
│   ├── ReturnRateChart.vue
│   ├── FeatureImportanceChart.vue
│   ├── RuleList.vue
│   └── RequestState.vue
└── router/
    └── index.js
```

## 二、页面功能

### 1. 概览页

展示：

- 订单总数；
- 退货数；
- 整体退货率；
- 类目数；
- 平均商品价格；
- 数据更新时间。

### 2. 退货分析页

使用 ECharts 展示：

- 各类目样本量和退货率；
- 促销与非促销退货率；
- 价格区间退货率；
- 退货和未退货数量对比。

图表必须同时标注样本量，避免小样本类目因为比例高而产生误导。

### 3. 退货预测页

表单字段：

```text
category
price
is_promotion
season
freight
```

提交后展示：

- 预测类别；
- 退货概率；
- 模型版本；
- 输入摘要。

不能在页面上展示退货原因作为预测输入。

### 4. 模型解释页

展示：

- Accuracy、Precision、Recall、F1；
- 混淆矩阵；
- 特征重要性；
- 决策树规则；
- 模型参数和版本。

## 三、交互状态

每个接口和图表都要覆盖：

- 加载中；
- 请求成功但无数据；
- 请求失败；
- 模型未加载；
- 表单校验失败；
- 预测提交中；
- 预测成功。

后端不可用时，页面显示错误提示和重试入口，不能渲染成空白页面。

## 四、接口封装

Axios 基础地址通过：

```text
VITE_API_BASE_URL=http://localhost:8000
```

统一封装错误处理，组件只关心成功数据和状态，不在多个页面重复拼接 URL 或解析错误文本。

## 五、可视化约束

- 退货率使用百分比展示，API 原值仍保持 `0` 到 `1`；
- 金额统一显示元；
- 特征重要性按降序排列；
- 规则列表显示叶节点样本量；
- 颜色和图例要区分退货与未退货；
- 空数组时显示明确的无数据状态。

## 六、前端验收

- [ ] 页面能调用文档中声明的 API。
- [ ] 预测字段与 API 请求体完全一致。
- [ ] 图表的单位、样本量和更新时间清晰可见。
- [ ] 错误、加载和空数据状态完整。
- [ ] 模型解释页能展示特征重要性和规则。
- [ ] 后端关闭时页面不会崩溃或白屏。
