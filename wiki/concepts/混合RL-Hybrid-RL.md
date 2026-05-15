---
id: concept-hybrid-rl
date: 2026-05-06
aliases: [Hybrid RL, 混合强化学习, 混合RL]
tags: [概念]
---

# 混合强化学习（Hybrid RL）

## 定义

混合强化学习是一种将**标量奖励驱动的策略优化**与**token-level 监督信号（如蒸馏损失）**统一在单一更新中的强化学习范式。核心思想是利用两种互补训练信号的各自优势：标量奖励信号频率高但信息稀疏，token-level 信号信息丰富但出现频率低，两者结合实现更高效、更稳定的策略学习。

该概念由 OpenClaw-RL (Wang et al., 2026) 正式提出并系统验证，但其思想根源可追溯至 RL 与模仿学习的结合（如 DQfD、RL+BC）。

## 关键属性

- **双信号源**：
  - **Evaluative signal（评估信号）**：标量反馈，判断动作好坏（如 PRM 投票 $r_t \in \{+1, -1, 0\}$）
  - **Directive signal（指令信号）**：token-level 的纠正/指导信息（如 hint-conditioned teacher 分布）

- **互补性**：
  | 维度 | Evaluative | Directive |
  |------|-----------|-----------|
  | 频率 | 高（每个评分步骤） | 低（仅含可提取纠正的步骤） |
  | 信息密度 | 低（1 标量） | 高（完整 token 分布） |
  | 粒度 | 序列级 | Token-level |

- **统一更新**：两种信号共享同一轨迹，在同一策略更新步骤中联合优化

## 数学形式

在 OpenClaw-RL 中的实现：

对 token $i$ 的混合损失：

$$L_i^{\text{hybrid}} = w_{\text{RL}} L_i^{\text{GRPO}} + w_{\text{OPD}} L_i^{\text{OPD}}$$

其中：
- $L_i^{\text{GRPO}}$：标准 PPO/GRPO clipped surrogate，由标量优势 $A_i^{\text{grpo}}$ 驱动
- $L_i^{\text{OPD}}$：On-policy distillation 损失，由 teacher-student log-prob 差距驱动
- $w_{\text{RL}}, w_{\text{OPD}}$：权重，通常设为 1

## 与相关概念的区别

| 方法 | 信号类型 | 更新方式 | 关键局限 |
|------|---------|---------|---------|
| 纯 RLVR (GRPO/DAPO) | 标量奖励 | 策略梯度 | 无法利用 token-level 指令 |
| 纯 OPD (On-Policy Distillation) | Token-level 蒸馏 | 监督学习 | 稀疏，teacher-student 不匹配 |
| **Hybrid RL** | **两者结合** | **统一更新** | **需要精心设计稳定性机制** |
| RL + BC (如 DQfD) | 奖励 + 演示 | 并行损失 | BC 数据需人工标注，非自动提取 |

## 稳定性挑战与解决方案

Hybrid RL 的核心挑战是 teacher-student 分布不匹配导致的训练不稳定：

1. **Overlap-guided hint selection**：选择使 teacher top-$k$ 与 student top-$k$ 重叠最大的 hint
2. **Log-probability-difference clip**：裁剪 teacher-student log-prob 差距，防止极端更新
3. **Support set 限制**：仅在 student 的高概率词表子集上计算蒸馏损失

## 相关概念

- [[GRPO]] — 混合目标的 RL 分支基础
- [[自蒸馏-Agent策略自蒸馏]] — OPD 分支的理论基础
- [[过程奖励模型 (PRM)]] — Evaluative signal 的提取器
- [[Agent RL]] — Hybrid RL 的应用领域

## 来源

- [[openclaw-rl-turning-daily-usage-into-training-signals|OpenClaw-RL]] — 首次系统提出并验证混合 RL

## 参见

- [[经验驱动自演化]] — 另一种利用交互信号的持续学习范式，与 Hybrid RL 互补