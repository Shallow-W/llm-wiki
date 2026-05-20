---
id: concept-episodic-memory-agent
date: 2026-05-20
aliases: [episodic memory, episode retention, 情节性记忆, 原始轨迹保留]
tags: [概念]
---

# 情节性记忆（Agent）

## 定义

LLM Agent 记忆系统中保留原始交互轨迹（raw episodes / trajectory rollouts）作为上下文示例的记忆形式，不进行跨轨迹的抽象或压缩。对应认知科学中的情节性记忆（episodic memory）。

## 关键属性

- **无损保留**：保留完整的观察、动作、中间失败和环境反馈
- **ICL 涌现**：Solver 可以从保留的实例中通过 in-context learning 涌现出 schema-like 行为
- **竞争力强**：在 ALFWorld、AppWorld、WebShop 上，不做整合的轨迹日志通常优于或持平所有整合方法
- **可管理**：Agent 可自主决定保留哪些 episode、删除哪些（Retain / Delete 操作）

## 实验证据

| 基准 | Traj Log vs 整合方法 | 结论 |
|------|---------------------|------|
| ALFWorld | 92% vs 最高 85% | 所有整合方法被击败 |
| AppWorld | 73% vs 最高 68% | 仅 AWM 在 Haiku 上胜出 |
| ARC-AGI Stream | Episodic Mgmt Only = 62% vs Force = 32% | 禁用整合更优 |

## 相关概念

- [[Agent记忆整合]] — 将情节性记忆压缩为抽象的对立过程
- [[记忆侵蚀]] — 整合导致退化，情节性记忆不受影响
- [[互补学习系统（Agent记忆）]] — 情节性存储 + 抽象存储的双系统架构

## 来源

- [[useful-memories-become-faulty-when-continuously-updated-by-llms]] — Table 2, 3; Figure 5, 9

## 参见

- [[文本记忆]] — 另一种记忆形式（抽象后的自然语言句子）
