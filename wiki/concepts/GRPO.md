---
id: concept-grpo
date: 2026-04-21
aliases: [GRPO, Group Relative Policy Optimization]
tags: [概念]
---

# GRPO（Group Relative Policy Optimization）

## 定义
DeepSeek 提出的一种无需 critic 模型的强化学习算法。对每个问题采样一组回答，在组内计算相对优势（advantage），用 clipped ratio + KL 惩罚更新策略。

## 关键属性
- **无需 value model / critic**：与传统 PPO 不同，GRPO 通过组内相对比较计算优势，省去 critic 网络
- **组相对优势**：对同一任务采样 G 个轨迹，每个 token 的优势 = 组内归一化（自身 reward - 组均值）/ 组标准差
- **clipped ratio**：类似 PPO，限制新旧策略的重要性比率在 [1-ε, 1+ε] 内，防止策略更新过大
- **KL 惩罚**：约束策略不要偏离参考模型太远

## 数学形式
$$GRPO(\pi) = \mathbb{E} \left[ \frac{1}{G} \sum_{g=1}^{G} \frac{1}{|\mathcal{Y}|} \sum_{i=1}^{|\mathcal{Y}|} \min\left( \frac{\pi_{\theta}(y_i)}{\pi_{old}(y_i)} \hat{A}_i, \text{clip}(\cdot, 1-\epsilon, 1+\epsilon) \hat{A}_i \right) - \beta \, KL(\pi_{\theta} \| \pi_{ref}) \right]$$

## 相关概念
- [[Agent RL]] — GRPO 是 Agent RL 训练中常用的策略优化算法
- [[Lyapunov 优化]] — 同为在线优化方法，但 Lyapunov 用于队列稳定性，GRPO 用于策略学习

## 来源
- [[agent-world]] — 使用 GRPO 作为 Agent RL 的策略优化算法
