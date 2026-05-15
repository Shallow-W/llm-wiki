---
id: concept-adpo
date: 2026-05-06
aliases: [ADPO, Ambiguity-Dynamic Policy Optimization, 模糊感知动态策略优化]
tags: [概念, 强化学习, 策略优化, 自演化, GRPO]
---

# ADPO（模糊感知动态策略优化）

## 定义

ADPO 是 Agent0 论文提出的一种改进型策略优化算法，针对自演化场景中的两个核心问题——伪标签噪声和静态裁剪对探索的限制——通过**模糊感知优势缩放**和**动态信任区域调制**来增强标准 GRPO/PPO 的训练效果。

## 核心动机

在零数据自演化框架中，训练标签来自执行 Agent 自身的多数投票（伪标签），而非人工标注。这引入了两个标准 RL 算法未考虑的关键问题：

| 问题 | 根源 | 标准算法的缺陷 |
|------|------|--------------|
| **标签噪声** | 高模糊度任务的多数答案容易出错 | GRPO 对所有样本同等对待，会强化错误推理 |
| **探索受限** | 静态裁剪 $\epsilon$ 抑制低概率 token 增长 | 正确答案常位于策略分布尾部，需要大更新才能浮现 |

## 关键机制

### 机制一：模糊感知优势缩放（Ambiguity-Aware Advantage Scaling）

**直觉**：自洽度 $\hat{p}(x)$ 低的任务，其多数投票伪标签更不可靠，应降低这些样本的训练权重。

**公式**：

$$\tilde{A}_i(x) = \hat{A}_i \cdot s(x), \quad s(x) = f(\hat{p}(x))$$

其中 $f$ 是自洽度 $\hat{p}(x)$ 的增函数。高自洽度（$\hat{p} \to 1$）的任务获得接近 1 的缩放因子，低自洽度（$\hat{p} \to 0.5$）的任务被显著降权。

**效果**：防止模型过拟合到可能错误的伪标签，将训练重点放在置信度较高的样本上。

### 机制二：模糊调制信任区域（Ambiguity-Modulated Trust Regions）

**直觉**：标准 PPO/GRPO 的静态裁剪 $\epsilon$ 对策略更新施加了对称约束，但实证分析（Agent0 Figure 3）显示上裁剪界主要由低概率 token 触发。这对高模糊度任务尤其有害——正确答案往往位于当前策略分布的尾部，需要大幅更新才能"浮现"。

**公式**：

$$\epsilon_{\text{high}}(x) \propto \frac{1}{\hat{p}(x)}$$

即动态上裁剪界与自洽度成反比：
- **模糊任务**（$\hat{p}$ 低）：$\epsilon_{\text{high}}$ 大，允许更大的梯度步长，鼓励探索低概率解
- **自信任务**（$\hat{p}$ 高）：$\epsilon_{\text{high}}$ 小，保持紧约束，维持训练稳定性

下界 $\epsilon_{\text{low}}$ 保持固定，防止策略崩溃。

### ADPO 完整目标函数

$$\mathcal{L}_{\text{ADPO}}(\theta) = \mathbb{E}_{x \sim \mathcal{D}^{(t)}} \left[ -\frac{1}{G} \sum_{i=1}^{G} \min\left( r_i(\theta) \tilde{A}_i(x), \text{clip}\left(r_i(\theta), 1 - \epsilon_{\text{low}}, 1 + \epsilon_{\text{high}}(x)\right) \tilde{A}_i(x) \right) \right]$$

其中：
- $r_i(\theta) = \frac{\pi_\theta(x_i)}{\pi_{\text{old}}(x_i)}$：重要性采样比率
- $\tilde{A}_i(x) = \hat{A}_i \cdot s(x)$：模糊缩放优势
- $\epsilon_{\text{high}}(x) = g(\hat{p}(x))$：动态上界（$\hat{p}$ 的减函数）
- $\epsilon_{\text{low}}$：固定下界

## 与标准 GRPO 的对比

| 组件 | 标准 GRPO | ADPO |
|------|----------|------|
| 优势计算 | $\hat{A}_i$（组内 z-score 归一化） | $\tilde{A}_i = \hat{A}_i \cdot s(x)$（额外乘以自洽度缩放因子） |
| 裁剪界 | 对称：$[1-\epsilon, 1+\epsilon]$ | 非对称：$[1-\epsilon_{\text{low}}, 1+\epsilon_{\text{high}}(x)]$ |
| 样本权重 | 均等 | 按自洽度自适应 |
| 探索能力 | 静态限制 | 模糊任务动态放宽 |

## 实验效果

在 Agent0 的消融实验中，移除 ADPO（改用标准 GRPO）导致：
- Qwen3-8B：General AVG 从 36.7% 降至 34.9%（-1.8%）
- Qwen3-8B：Math AVG 从 58.2% 降至 56.2%（-2.0%）

虽然绝对降幅看似不大，但考虑到这是在不改变任何其他条件的情况下仅替换优化算法的结果，证明了 ADPO 在自演化场景中的稳定贡献。

## 适用场景

ADPO 特别适用于以下场景：
1. **伪标签训练**：标签来自模型自身投票或启发式规则而非人工标注
2. **自演化系统**：训练数据由系统自身生成，质量不均
3. **探索密集型任务**：需要在策略分布尾部发现新推理路径
4. **多轮交互**：长轨迹中不同步骤的可靠性差异大

## 局限

1. **缩放函数设计**：$s(x) = f(\hat{p}(x))$ 和 $\epsilon_{\text{high}}(x) = g(\hat{p}(x))$ 的具体函数形式需要调参
2. **仅验证于数学推理**：在其他领域（代码、对话、具身智能）的有效性待验证
3. **与标准 PPO 的兼容性**：ADPO 的修改可直接应用于 PPO，但论文仅在 GRPO 上验证
4. **计算开销**：需要为每个样本计算自洽度 $\hat{p}(x)$，增加了训练前的评估成本

## 相关概念

- [[GRPO]] — ADPO 的基础算法，ADPO 是对 GRPO 的两处关键修改
- [[Agent 强化学习（Agent RL）]] — ADPO 的应用领域
- [[经验驱动自演化（Experience-Driven Self-Evolution）]] — 同为自演化场景下的训练策略
- [[课程学习（Curriculum Learning）]] — ADPO 处理的伪标签问题在自适应课程中尤为突出
- [[PPO（Proximal Policy Optimization）]] — ADPO 的修改同样适用于 PPO 框架

## 来源

- [[agent0-bootstrapping-from-zero-data]] — 提出 ADPO 的原始论文

## 参见

- [[零数据自举（Zero-Data Bootstrapping）]] — ADPO 解决的核心问题场景
- [[自蒸馏（Agent策略自蒸馏）]] — 另一种处理伪标签质量的方法
