---
id: concept-overlap-guided-hint-selection
date: 2026-05-06
aliases: [Overlap-Guided Hint Selection, OGHS, 重叠引导Hint选择]
tags: [概念]
---

# Overlap-Guided Hint Selection

## 定义

Overlap-Guided Hint Selection（重叠引导 Hint 选择）是一种在 hint-conditioned on-policy distillation 中选择最优纠正 hint 的准则。核心思想是：从候选 hint 中选择那个使得 hint-conditioned teacher 分布与 student 分布的**top-$k$ 词表重叠最大**的 hint，从而最小化 teacher-student 分布不匹配，稳定蒸馏训练。

由 OpenClaw-RL (Wang et al., 2026) 提出，用于解决 on-policy distillation 中 teacher-student 分布 mismatch 导致的训练不稳定问题。

## 问题背景

### On-Policy Distillation 的不稳定性

On-policy distillation 训练 student 在 student 自己的 rollout 上从 teacher 获取 token-level 监督。当 teacher 分布在 student 接近零密度的 token 上放置质量时：
- Off-policy 重要性比率 $\rho$ 爆炸
- 梯度方差增大
- 训练不稳定甚至发散

### Hint 质量的影响

在 hint-conditioned 自蒸馏中，teacher 通过在 prompt 后追加纠正 hint 获得。Hint 的选择直接控制 mismatch 程度：
- 模糊/偏题的 hint $\rightarrow$ teacher 远离 student $\rightarrow$ 不稳定
- 精确/相关的 hint $\rightarrow$ teacher 接近 student $\rightarrow$ 稳定

## 方法

### 符号定义

给定 student 的生成响应 $y = (y_1, \ldots, y_T)$：

- $S_i^q = \text{top-}k\{\pi_{\text{old}}(\cdot | s_t, y_{<i})\}$：student（旧策略）在位置 $i$ 的 top-$k$ 词表
- $S_{i,h}^p = \text{top-}k\{\pi_T(\cdot | s_t^h, y_{<i})\}$：hint $h$ 条件下 teacher 在位置 $i$ 的 top-$k$ 词表

### Overlap Signal

$$O[h, i] = |S_i^q \cap S_{i,h}^p|$$

计数 student 的高概率 token 中有多少在 hint-conditioned teacher 下仍保持高概率。

### 选择方案

**Sequence-level**（序列级，推荐）：

$$h^\star = \arg\max_h \sum_i O[h, i]$$

每个轨迹选择一个最优 hint，在整个序列上最大化总重叠。

**Token-level**（token 级）：

$$h^\star(i) = \arg\max_h O[h, i]$$

每个位置独立选择最优 hint，与 OPD 的 token-level 本质对齐。

### 直觉解释

高 overlap 意味着 teacher 和 student 在"响应应该长什么样"的词汇层面已经达成一致。此时蒸馏可以将 student 推向 teacher，但**是在 student 自己的高密度区域内移动**，而非推向陌生的 token。这保持了 off-policy 重要性比率接近 1，同时保留了 hint 携带的方向性信息。

## 实验验证

在 OpenClaw-RL 中的消融结果：

| 方法 | Student | TA | Teacher | Average |
|------|---------|-----|---------|---------|
| Sequence-optimal | 14.0 | 9.6 | 13.8 | 12.5 |
| Token-optimal | 13.8 | 10.0 | 13.4 | 12.4 |
| Random | 18.6 | 12.6 | 17.0 | 16.1 |

- 两种 optimal 方案性能相近，均显著优于 random
- Sequence-optimal 在 general agentic RL（大 batch）中更稳定

## 与相关方法的区别

| 方法 | 选择依据 | 适用场景 |
|------|---------|---------|
| Random selection | 无 | 基线，不稳定 |
| Teacher confidence | Teacher 分布的熵/峰值 | 未考虑 student 分布 |
| Hint length | 越短越好 | 启发式，无理论保证 |
| **Overlap-guided** | **Top-$k$ 词表交集大小** | **直接最小化 mismatch** |

## 相关概念

- [[混合RL (Hybrid RL)]] — Overlap-guided 是 Hybrid RL 稳定性的核心机制之一
- [[自蒸馏-Agent策略自蒸馏]] — 方法的应用场景
- [[过程奖励模型 (PRM)]] — 负责生成候选 hints

## 来源

- [[openclaw-rl-turning-daily-usage-into-training-signals|OpenClaw-RL]] — 首次提出并验证

## 参见

- [[Log-Probability-Difference Clip]] — 与 overlap-guided 配合使用的另一稳定性机制