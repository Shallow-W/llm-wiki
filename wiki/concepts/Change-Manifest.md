---
id: concept-change-manifest
date: 2026-05-21
aliases: [Manifest]
tags: [概念]
---

# Change Manifest

## 定义

[[Agentic-Harness-Engineering|AHE]] 中实现 [[Decision-Observability|决策可观测性]] 的机制。要求演化 Agent 在每次编辑 harness 时同时声明两份预测清单：预期修复的任务列表和可能退化的任务列表。下一轮 rollout 后用实际结果验证，形成可审计的因果链。

## 关键属性

- **预期修复（Expected Fixes）**：声明"这个变更应该修复哪些任务"
- **风险回归（At-Risk Regressions）**：声明"这个变更可能导致哪些任务退化"
- **配对验证**：预测 vs 实际结果，量化自归因能力
- **不鼓励盲改**：强制预测声明迫使 Agent 基于证据做编辑

## 自归因精度

- 修复预测：precision 33.7%, recall 51.4%（~5x 随机基线）
- 回归预测：precision 11.8%, recall 11.1%（~2x 随机基线，接近随机）

## 相关概念

- [[Decision-Observability|决策可观测性]] — Change Manifest 实现的可观测性支柱
- [[Agentic-Harness-Engineering|AHE]] — 使用此机制的方法

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — §3.3
