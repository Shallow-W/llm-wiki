---
id: concept-experience-observability
date: 2026-05-21
aliases: [经验可观测性]
tags: [概念]
---

# 经验可观测性（Experience Observability）

## 定义

[[Agentic-Harness-Engineering|AHE]] 的三种可观测性支柱之一。通过 Agent Debugger 将海量原始轨迹（数百万 token）蒸馏为分层的、可下钻的证据语料，解决"原始数据太多、有效信号太少"的问题。

## 关键属性

- **Agent Debugger**：特殊 Agent，将轨迹视为可探索的文件环境
- **分层蒸馏**：任务级根因分析 + 基准级系统性模式识别
- **压缩比**：数百万 token 轨迹 → 可消费的结构化分析报告
- **可下钻**：从概览到具体任务的逐层深入

## 相关概念

- [[Component-Observability|组件可观测性]] — 解决"改什么"
- [[Decision-Observability|决策可观测性]] — 解决"改了有什么效果"
- 本概念解决"为什么改"

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — §3.2
