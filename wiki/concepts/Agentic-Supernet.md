---
id: concept-agentic-supernet
date: 2026-05-21
aliases: [Agentic Supernet]
tags: [概念]
---

# Agentic Supernet

## 定义

一种概率化、连续分布的多 Agent 架构分布。由 L 层组成，每层 ℓ 上每个算子 O 有一个条件概率 πℓ(O) = p(O | A₁:ℓ₋₁)，表示在给定前面层选择的情况下该算子出现的概率。这诱导了一个关于所有可能多层算子配置的联合分布 p(G)。

## 关键属性

- **概率化**：不是确定性的架构，而是架构上的概率分布
- **连续**：通过 softmax/门控机制实现连续松弛
- **查询条件**：架构采样以输入查询 q 为条件
- **层间依赖**：每层的选择依赖于前面层
- **DAG 约束**：生成的多 Agent 系统是有向无环图

## 数学定义

```
A = {π, O} = {{πℓ(O)}O∈O}ᴸℓ=₁
p(G) = ∏ᴸℓ=₁ ∏O∈O πℓ(O)^I(O∈Vℓ)
```

## 相关概念

- [[Multi-agent-Architecture-Search|MaAS]] — 使用 Agentic Supernet 的方法
- [[神经架构搜索 (NAS)]] — 灵感来源，但 MaAS 搜索 Agent 系统而非神经网络
- [[Query-Dependent-Sampling|查询条件采样]] — Supernet 的采样方式

## 来源

- [[multi-agent-architecture-search-via-agentic-supernet|MaAS]] — Definition 3.2
