---
id: concept-agent-rl
date: 2026-04-21
aliases: [Agent RL, Agentic Reinforcement Learning, Agent 强化学习]
tags: [概念]
---

# Agent 强化学习（Agent RL）

## 定义
让 LLM Agent 在可执行环境中通过"生成→执行→反馈"的闭环交互来学习策略的强化学习方法。与传统的静态 SFT 训练不同，Agent RL 利用环境的真实反馈信号来优化模型行为。

## 关键属性
- **闭环交互**：Agent 生成动作 → 环境执行 → 返回观测 → Agent 决定下一步
- **可验证奖励**：不同于 LLM-as-judge 的主观评分，使用沙箱执行、rubric 检查等可程序化验证的奖励
- **长链推理**：Agent 需要在多步交互中维护状态一致性，挑战远大于单轮问答
- **探索-利用平衡**：训练过程中需要平衡探索新工具组合和利用已知有效策略

## 相关概念
- [[GRPO]] — 常用的 Agent RL 策略优化算法
- [[POMDP]] — Agent 交互的理论建模框架
- [[Model Context Protocol (MCP)]] — 为 Agent RL 提供标准化环境接口

## 来源
- [[agent-world]] — 核心方法之一，多环境 Agent RL

## 参见
- [[微服务部署与路由优化概览]] — 优化方法对比（RL vs 启发式 vs Lyapunov）
