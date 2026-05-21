---
id: concept-decision-observability
date: 2026-05-21
aliases: [决策可观测性]
tags: [概念]
---

# 决策可观测性（Decision Observability）

## 定义

[[Agentic-Harness-Engineering|AHE]] 的三种可观测性支柱之一。通过 [[Change-Manifest|Change Manifest]] 要求演化 Agent 在每次编辑时声明预期修复和风险回归，下一轮用实际结果验证，形成可审计的因果链。

## 关键属性

- **Change Manifest**：每次编辑配对预测声明
- **预期修复（Expected Fixes）**：声明"这个变更应该修复任务 X, Y, Z"
- **风险回归（At-Risk Regressions）**：声明"这个变更可能导致任务 A, B 退化"
- **自归因验证**：修复预测 precision 33.7%（~5x 随机），回归预测 precision 11.8%（~2x 随机）

## 自归因数据

| 预测类型 | Precision | Recall | vs 随机 |
| --- | --- | --- | --- |
| Fix Predictions | 33.7% | 51.4% | ~5x |
| Regression Predictions | 11.8% | 11.1% | ~2x |

## 相关概念

- [[Component-Observability|组件可观测性]] — 另一可观测性支柱
- [[Experience-Observability|经验可观测性]] — 另一可观测性支柱
- [[Change-Manifest|Change Manifest]] — 实现决策可观测性的机制

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — §3.3
