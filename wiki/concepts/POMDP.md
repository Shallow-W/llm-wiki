---
id: concept-pomdp
date: 2026-04-21
aliases: [POMDP, Partially Observable Markov Decision Process, 部分可观测马尔可夫决策过程]
tags: [概念]
---

# POMDP（部分可观测马尔可夫决策过程）

## 定义
MDP 的扩展，Agent 无法直接观察环境的完整状态，只能通过部分观测来推断。五元组 $(\mathcal{I}, \mathcal{S}, \mathcal{A}, \mathcal{O}, \delta)$ 分别表示意图空间、状态空间、动作空间、观测空间和状态转移函数。

## 关键属性
- **意图空间 $\mathcal{I}$**：用户的潜在意图，Agent 从交互历史和环境反馈中逐步推断
- **状态分解**：$\mathcal{S} = \mathcal{S}^{env} \times \mathcal{S}^{dlg}$，环境状态（数据库、文件等）× 对话状态（历史、偏好）
- **动作双类型**：工具调用（tool）| 语言响应（resp）
- **部分可观测**：环境状态 $\mathcal{S}^{env}$ 不直接可见，必须从工具返回的结构化观测中间接推断

## 在 Agent 训练中的应用
- 将多轮 Agent-环境交互形式化为 POMDP，为 RL 训练提供理论基础
- 环境状态不可见性解释了为什么 Agent 需要学习状态追踪（state tracking）能力

## 相关概念
- [[M/M/C 排队模型]] — 同为随机过程建模方法，但排队论关注稳态性能分析，POMDP 关注序列决策
- [[Agent RL]] — POMDP 是 Agent RL 的理论框架

## 来源
- [[agent-world]] — 用 POMDP 建模多环境 Agent 交互
