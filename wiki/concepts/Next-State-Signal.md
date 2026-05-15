---
id: concept-next-state-signal
date: 2026-05-06
aliases: [Next-State Signal, Next State Signal, 下一状态信号]
tags: [概念]
---

# Next-State Signal（下一状态信号）

## 定义

Next-State Signal 是指在 Agent 执行动作 $a_t$ 后，环境返回的下一个状态 $s_{t+1}$ 中所蕴含的、可用于训练策略模型的信息。在 LLM Agent 的语境下，$s_{t+1}$ 可以是用户回复、工具执行输出、终端状态变化、GUI 状态变化等。该信号包含两种互补的训练信息：evaluative（评估性）和 directive（指令性）。

由 OpenClaw-RL (Wang et al., 2026) 系统性地形式化为在线学习框架的核心概念。

## 形式化

在 POMDP 框架中：
- Agent 在状态 $s_t$ 下执行动作 $a_t \sim \pi_\theta(\cdot | s_t)$
- 环境返回观测 $o_{t+1}$（即 next-state $s_{t+1}$）
- $s_{t+1}$ 包含关于 $a_t$ 质量的丰富信息

## 两种信号类型

### Evaluative Signal（评估信号）

**定义**：从 $s_{t+1}$ 中提取的标量反馈，判断 $a_t$ 的好坏。

**来源示例**：
| Next-State 类型 | Evaluative Signal |
|----------------|-------------------|
| 用户回复"谢谢，很好" | $+1$（正面） |
| 用户回复"不对，你应该..." | $-1$（负面） |
| 用户重述/重问同一问题 | $-1$（暗示未理解） |
| 测试通过 | $+1$（成功） |
| 错误追踪/异常输出 | $-1$（失败） |
| 模糊跟进（无关话题） | $0$（中性） |

**提取方式**：PRM（Process Reward Model）查询 $m$ 次，取多数投票 $r_t \in \{+1, -1, 0\}$。

**特点**：
- 频率高：每个被评分的 turn 都有
- 信息稀疏：整个 turn 压缩为 1 个标量
- 隐式：用户不一定会明确说"好"或"坏"

### Directive Signal（指令信号）

**定义**：从 $s_{t+1}$ 中提取的 token-level 纠正信息，不仅指出 $a_t$ 的错误，还说明如何改正。

**来源示例**：
| Next-State 类型 | Directive Signal |
|----------------|------------------|
| "你应该先检查文件再修改" | Hint: "在修改前先验证文件状态" |
| 错误追踪指向第 42 行 | Hint: "注意边界条件的处理" |
| 用户要求"写得更详细些" | Hint: "增加逐步推理的细节" |
| "谢谢，看起来不错" | 无 directive（纯 evaluative） |
| 测试通过 | 无 directive（纯 evaluative） |

**提取方式**：PRM 判断 $s_{t+1}$ 是否包含有意义的纠正信息。如果是，蒸馏为简洁 hint $h$ 包裹在 `[HINT_START]...[HINT_END]` 中。

**特点**：
- 频率低：仅在有可提取纠正的 turn 上触发
- 信息丰富：完整的下一个 token 分布
- 显式：需要 next-state 包含具体的纠正内容

## 信号互补性

| 维度 | Evaluative | Directive |
|------|-----------|-----------|
| 频率 | 高 | 低 |
| 粒度 | 序列级 | Token-level |
| 信息密度 | 稀疏（1 标量） | 丰富（完整分布） |
| 覆盖范围 | 所有评分 turn | 有纠正内容的 turn |
| 利用方式 | RLVR/GRPO | On-policy distillation |

**关键洞察**：两者单独使用都无法充分利用 $s_{t+1}$ 的全部信息。只有结合使用（Hybrid RL）才能最大化 next-state 信号的价值。

## 与现有概念的关系

### 与传统 RL 观测的区别

传统 RL 中，观测 $o_{t+1}$ 主要用于状态更新，奖励 $r_t$ 由独立的环境奖励函数提供。在 Next-State Signal 框架中：
- $s_{t+1}$ **本身就是奖励信号的来源**
- 无需独立的奖励函数，PRM 从 $s_{t+1}$ 中推断奖励
- 特别适用于无法程序化定义奖励的开放域交互

### 与 Hindsight Experience Replay 的关系

HER 将失败轨迹的目标状态替换为实际达到的状态，使失败变为成功。Next-State Signal 是 HER 思想的在线扩展：
- HER：离线，替换目标
- Next-State Signal：在线，从实际 next-state 中提取纠正信息

### 与 POMDP 的关系

Next-State Signal 框架将 Agent 交互自然地映射到 POMDP：
- 状态 $s_t$：Agent 的历史上下文
- 动作 $a_t$：Agent 的响应/工具调用
- 观测 $o_{t+1}$：next-state（用户回复/工具输出）
- 奖励：从 $o_{t+1}$ 中提取的 evaluative + directive 信号

## 应用场景

| 场景 | Next-State 示例 | 信号类型 |
|------|----------------|---------|
| 个人对话 Agent | 用户回复 | Evaluative + Directive |
| Terminal Agent | stdout/stderr, exit code | Evaluative |
| GUI Agent | 视觉状态差异 | Evaluative + Directive |
| SWE Agent | 测试判决, diff | Evaluative + Directive |
| Tool-call Agent | 工具返回值, 错误追踪 | Evaluative + Directive |

## 提取流程

```
(a_t, s_{t+1})
    ↓
PRM 评估
    ↓
┌─────────────────┐    ┌─────────────────┐
│ Evaluative      │    │ Directive       │
│ m 次投票        │    │ 是否含纠正？    │
│ 取多数 r_t      │    │ 是 → 蒸馏 hint  │
│ ∈ {+1,-1,0}     │    │ 否 → 无信号     │
└─────────────────┘    └─────────────────┘
    ↓                        ↓
标量奖励              Token-level 监督
    ↓                        ↓
    └────────→ Hybrid RL ←───────┘
```

## 相关概念

- [[混合RL (Hybrid RL)]] — 利用两种信号的统一训练框架
- [[过程奖励模型 (PRM)]] — 信号提取的核心组件
- [[POMDP]] — Next-State Signal 的理论框架
- [[Agent RL]] — 应用场景

## 来源

- [[openclaw-rl-turning-daily-usage-into-training-signals|OpenClaw-RL]] — 首次系统提出

## 参见

- [[经验驱动自演化]] — 另一种利用交互历史的学习范式
- [[Hindsight Relabeling]] — 离线纠正重标注方法