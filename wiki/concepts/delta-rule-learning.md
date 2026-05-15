---
id: concept-delta-rule-learning
date: 2026-05-15
aliases: [delta rule, delta-rule, δ-rule]
tags: [概念, 在线学习, 记忆更新]
---

# Delta-Rule Learning（δ 规则学习）

## 定义

Delta-rule 是一种基于预测误差的在线学习规则。它不是简单地累加新信息，而是先计算当前状态对新输入的"预测误差"，然后只将误差部分写入状态。这种"差分更新"使得已经学好的关联几乎不受影响，只有预测不足的部分才会被修正。

## 核心公式

给定记忆状态 $S$、记忆 key $k_t$ 和目标 value $v_t$：

$$\hat{v}_t = S_{t-1} k_t \quad \text{（旧状态预测）}$$

$$S_t = S_{t-1} + \beta_t (v_t - \hat{v}_t) k_t^\top \quad \text{（误差驱动更新）}$$

其中 $v_t - \hat{v}_t$ 就是**预测误差（delta）**，$\beta_t$ 是学习率/写入门控。

## 关键属性

- **误差驱动**：只有预测错误的部分才写入，已记住的几乎不变
- **在线学习**：逐 token/段 更新，不需要回顾全部历史
- **可加门控**：引入遗忘门 $\lambda_t$ 控制旧记忆的保留程度
- **与 SGD 的关系**：本质上是在线 SGD 一步，优化 $\frac{1}{2}\|Sk_t - v_t\|^2$

## 直觉理解

想象你在记笔记：
- **朴素方法**：每次遇到新信息就追加一条笔记 → 笔记本越来越厚，查找困难
- **Delta-rule**：先回忆"我记得什么"，对比新信息，只记下"我之前不知道/记错的" → 笔记本保持精简

## 在 δ-mem 中的应用

δ-mem 将 delta-rule 用于更新在线关联记忆状态矩阵 $S$，并引入维度级门控：

$$S_t = \text{Diag}(\lambda_t) S_{t-1} + \text{Diag}(\beta_t)(v_t^m - S_{t-1} k_t^m)(k_t^m)^\top$$

这使得每个记忆维度可以独立控制保留与写入的平衡。

## 来源

- [[delta-mem-efficient-online-memory]] — δ-mem 论文中的应用
- 受 Qwen-Next 的门控保留设计启发（Yang et al., 2025）
