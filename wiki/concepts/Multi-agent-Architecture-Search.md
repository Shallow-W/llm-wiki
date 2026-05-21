---
id: concept-multi-agent-architecture-search
date: 2026-05-21
aliases: [MaAS]
tags: [概念]
---

# Multi-agent Architecture Search (MaAS)

## 定义

ICML 2025 提出的自动多 Agent 系统设计框架。核心思想是将 NAS 中的超网训练迁移到多 Agent 领域：不搜索单一最优多 Agent 系统，而是优化一个概率化的 Agent 架构分布（[[Agentic-Supernet|Agentic Supernet]]），让每个查询从中采样最适合自己的定制化子系统。

## 关键属性

- **范式转变**：从"搜索一个最优架构"到"优化一个架构分布"
- **查询相关**：不同难度的查询使用不同的算子组合和深度
- **资源感知**：优化目标同时考虑性能 U 和成本 C
- **双层优化**：蒙特卡洛梯度更新分布 π + 文本梯度更新算子 O
- **自演化能力**：算子可以通过文本梯度自我改进

## 核心结果

- 6 个基准全面领先（+0.54%~+16.89%）
- 训练成本仅为 AFlow 的 15%
- 跨模型迁移：llama-3.1-70b 上 MATH +11.04%
- 归纳能力：能泛化到训练时未见过的算子

## 相关概念

- [[Agentic-Supernet|Agentic Supernet]] — MaAS 的核心数据结构
- [[Textual-Gradient|文本梯度]] — MaAS 更新不可微算子的机制
- [[神经架构搜索 (NAS)]] — 方法论的灵感来源

## 来源

- [[multi-agent-architecture-search-via-agentic-supernet|MaAS]] — 提出该方法

## 参见

- [[agentic-harness-engineering|AHE]] — 互补方法（优化 harness 组件而非架构）
