---
id: concept-early-exit-operator
date: 2026-05-21
aliases: [Early-exit Operator]
tags: [概念]
---

# Early-exit Operator

## 定义

[[Multi-agent-Architecture-Search|MaAS]] 中的特殊算子，当在某层采样到该算子时，提前终止架构采样过程。这使得 Agentic Supernet 的深度可以根据查询难度动态调整——简单查询在第 2 层退出，复杂查询走完全部 L 层。

## 关键属性

- **查询相关深度**：不同查询使用不同深度的架构
- **资源节省**：简单查询不走冗余层
- **概率化退出**：以概率方式决定退出点，而非硬阈值
- **学习到的行为**：训练后 supernet 自动学会在适当层数退出

## 消融发现

移除 Early-exit 后：
- HumanEval 性能从 92.85% 降至 91.44%（−1.41pp）
- 但成本从 1.01 升至 1.67（+65%）
- 说明主要影响成本而非性能

## 相关概念

- [[Multi-agent-Architecture-Search|MaAS]] — 使用此算子的方法
- [[Agentic-Supernet|Agentic Supernet]] — Early-exit 所在的超网结构

## 来源

- [[multi-agent-architecture-search-via-agentic-supernet|MaAS]] — Definition 3.2, Eq. 8
