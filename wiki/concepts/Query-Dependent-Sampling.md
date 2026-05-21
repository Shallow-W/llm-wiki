---
id: concept-query-dependent-sampling
date: 2026-05-21
aliases: [查询条件采样]
tags: [概念]
---

# 查询条件采样（Query-dependent Sampling）

## 定义

[[Multi-agent-Architecture-Search|MaAS]] 的核心机制。Controller 网络 Qϕ 以输入查询 q 为条件，从 [[Agentic-Supernet|Agentic Supernet]] 中采样定制化的多 Agent 系统 G。采样过程是查询感知的——不同难度、领域、特征的查询会激活不同的算子组合和层数。

## 关键属性

- **MoE 风格实现**：使用 Mixture-of-Experts 网络计算每个算子的激活分数
- **阈值门控**：累积分数超过阈值 thres=0.3 时停止激活该层算子
- **文本嵌入**：用 MiniLM/Sentence-BERT 编码查询和算子描述
- **条件依赖**：每层选择依赖于查询和前面层的选择

## 可视化发现

- Easy 查询（如"42! 末尾有几个零"）：I/O + CoT，第 2 层 early-exit
- Medium 查询（如骰子期望）：加入 Ensemble + Self-Consistency
- Hard 查询（如复合分数运算）：全部 4 层，ReAct + Debate + Refine

## 相关概念

- [[Multi-agent-Architecture-Search|MaAS]] — 使用此采样的方法
- [[Controller-Network-Qphi|Controller Network Qϕ]] — 实现采样的网络

## 来源

- [[multi-agent-architecture-search-via-agentic-supernet|MaAS]] — §3.2, Eq. 7-9
