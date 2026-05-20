---
id: concept-complementary-learning-systems-agent
date: 2026-05-20
aliases: [CLS, Complementary Learning Systems, 互补学习系统]
tags: [概念]
---

# 互补学习系统（Agent 记忆）

## 定义

源自认知科学（McClelland et al., 1995），主张记忆系统应保持两个架构上分离的子系统：快速情节性存储（fast episodic store）和慢速抽象形成存储（slow schema-forming store）。[[useful-memories-become-faulty-when-continuously-updated-by-llms]] 将此原则应用于 LLM Agent 记忆设计。

## 关键属性

- **快速学习不覆盖慢速学习**：Episodic store 的快速积累不应通过强制整合覆盖 Abstract store 中的稳定知识
- **整合应由 schema fit 门控**：只在已有抽象框架能容纳新证据时才触发整合，而非每次交互都触发
- **强制整合 = 灾难性干扰**：Force 模式将双系统合并为单一重写循环，重现了连接主义中的灾难性遗忘问题（McCloskey & Cohen, 1989）

## 实验证据

| 策略 | ARC-AGI 成功率 | 设计原则 |
|------|---------------|---------|
| Auto（双存储，自主门控） | 43.2% | CLS 原则 |
| Episodic Only（无抽象） | 62% | 快速系统独立 |
| Force（强制整合） | 26.0% | 违反 CLS |

## 相关概念

- [[Agent记忆整合]] — 慢速系统的核心操作
- [[情节性记忆（Agent）]] — 快速系统
- [[记忆侵蚀]] — 违反 CLS 原则时的退化现象

## 来源

- [[useful-memories-become-faulty-when-continuously-updated-by-llms]] — Section 5, 7

## 参见

- [[δ-mem（在线关联记忆）]] — 另一种受 CLS 启发的 LLM 记忆设计
