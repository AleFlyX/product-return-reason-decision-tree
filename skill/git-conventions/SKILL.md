---
name: git-conventions
description: 本项目的 Git 分支、提交信息和模块协作规范。用于创建分支、提交代码或跨模块修改时保持一致的协作方式。
---

# Git 协作规范

## 分支模型

长期分支为 `main` 和 `develop`。功能开发从 `develop` 创建独立的 `feature/*` 分支，完成后通过代码评审合并回 `develop`，稳定版本再合并到 `main`。

推荐的功能分支命名：

```text
feature/data-clean
feature/feature-engineering
feature/decision-tree
feature/backend-fastapi
feature/frontend-vue3
```

分支名应使用小写英文、短横线分隔，并准确描述单一主题。修复问题可使用 `fix/<topic>`，文档变更可使用 `docs/<topic>`。

## Commit 信息

Commit 标题使用以下类型之一，并以冒号和简短祈使句说明变更：

```text
feat / fix / docs / refactor / test / chore
```

示例：

```text
feat: add returned label pipeline
fix: validate empty prediction payload
docs: clarify HBase row key contract
```

一次提交聚焦一个逻辑变更；不要把无关格式化、生成物或多个模块的独立功能混在同一提交中。提交前确认敏感数据、模型大文件和本地环境文件未被加入版本库。

## 模块协作与契约

数据处理、特征工程、模型、后端和前端之间通过清晰的数据文件或 API 契约交接。修改其他成员负责的核心契约（字段、标签、路径、请求/响应结构）前，先同步更新 `docs/` 中对应文档，并在提交信息或描述中注明影响范围。

交接时应同时说明数据/模型版本、批次号、输入字段和兼容性要求，确保变更可追溯、可复现。

## 日常检查

开始工作前同步 `develop`，确认工作区干净并查看待合并变更；提交前运行与模块相关的测试和静态检查。合并前由评审者检查分支目标、Commit 类型、契约文档和验收标准是否一致。
