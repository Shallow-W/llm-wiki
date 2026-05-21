---
id: concept-component-observability
date: 2026-05-21
aliases: [组件可观测性]
tags: [概念]
---

# 组件可观测性（Component Observability）

## 定义

[[Agentic-Harness-Engineering|AHE]] 的三种可观测性支柱之一。通过 [[NexAU-Framework|NexAU]] 框架将 Agent harness 解耦为 7 种正交组件类型，每种以文件形式暴露在固定挂载点，使演化 Agent 能观察、编辑、diff、rollback 任何组件。

## 关键属性

- **7 种组件类型**：System Prompt、Tools、Middleware、Skills、Sub-agent Configs、Long-term Memory、Workflow
- **文件化**：编辑 harness = 编辑文件，动作空间清晰
- **Git 原生**：每次变更有 diff，可回滚到任意版本
- **正交性**：组件类型之间互不依赖，独立演化

## 相关概念

- [[Experience-Observability|经验可观测性]] — 另一可观测性支柱
- [[Decision-Observability|决策可观测性]] — 另一可观测性支柱
- [[NexAU-Framework|NexAU]] — 实现组件可观测性的具体框架

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — §3.1
