---
id: concept-controller-network-qphi
date: 2026-05-21
aliases: [Controller Network Qϕ]
tags: [概念]
---

# Controller Network Qϕ

## 定义

[[Multi-agent-Architecture-Search|MaAS]] 中的查询条件架构采样器。以查询 q、参数化分布 π 和可用算子集 O 为输入，输出采样得到的多 Agent 系统 G。实现为 MoE 风格网络，通过文本嵌入和门控机制决定每层激活哪些算子。

## 关键属性

- **参数 ϕ**：可学习的门控参数
- **文本嵌入 v(·)**：用 MiniLM/Sentence-BERT 编码查询和算子
- **门控机制**：FFN(v(q) ∥ Σv(V₁) ∥ ... ∥ Σv(Vℓ₋₁)) → 算子分数
- **阈值激活**：累积分数超过 thres 后停止激活
- **Early-exit 支持**：采样到 Oexit 时终止

## 相关概念

- [[Multi-agent-Architecture-Search|MaAS]] — 使用此 controller 的方法
- [[Query-Dependent-Sampling|查询条件采样]] — Controller 的功能
- [[Agentic-Supernet|Agentic Supernet]] — Controller 采样的对象

## 来源

- [[multi-agent-architecture-search-via-agentic-supernet|MaAS]] — §3.2, Eq. 7-9
