---
id: source-lora-low-rank-adaptation
date: 2026-05-06
source: raw/papers/lora-low-rank-adaptation.pdf
type: 论文
tags: [参数高效微调, 低秩分解, Transformer, 迁移学习, PEFT]
---

# LoRA: Low-Rank Adaptation of Large Language Models

## 一句话总结

提出 LoRA：冻结预训练模型权重，在每个 Transformer 层注入可训练的低秩分解矩阵 $B \in \mathbb{R}^{d \times r}$ 和 $A \in \mathbb{R}^{r \times k}$，将权重更新约束为 $\Delta W = BA$，以极少量可训练参数（GPT-3 175B 上仅 0.01%）实现与全量微调相当甚至更好的下游任务性能，且不引入额外推理延迟。

## 基本信息

| 项目 | 内容 |
|------|------|
| **标题** | LoRA: Low-Rank Adaptation of Large Language Models |
| **作者** | Edward J. Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, Weizhu Chen |
| **机构** | Microsoft Corporation |
| **日期** | 2021-10-16（arXiv v2） |
| **arXiv** | 2106.09685v2 |
| **代码** | [microsoft/LoRA](https://github.com/microsoft/LoRA) |
| **会议** | ICLR 2022 |

## 研究背景与动机

### 全量微调的困境

大规模预训练 + 下游适配是 NLP 的主流范式。但随着模型规模膨胀，全量微调（Fine-Tuning）面临严峻挑战：

1. **存储爆炸**：每个下游任务都需要存储一份完整的微调后模型。GPT-3 175B 的单个 checkpoint 约 350GB，100 个任务就需要 35TB。
2. **部署困难**：为每个任务部署独立实例在计算和 I/O 上都不现实。
3. **硬件门槛高**：全量微调需要存储所有参数的优化器状态（Adam 需要 2× 参数量的动量状态），GPT-3 175B 全量微调需要约 1.2TB VRAM。

### 现有方法的局限

论文系统分析了两种主流替代方案的问题：

**Adapter 层引入推理延迟**：Adapter（Houlsby et al., 2019）在 Transformer 块中插入瓶颈层，虽然参数量小，但增加了模型深度。由于必须顺序计算，在线推理（batch size = 1）时延迟增加可达 20-30%（Table 1）。模型并行时还会引入额外的同步操作（AllReduce/Broadcast）。

**Prefix-Tuning 优化困难**：Prefix-Tuning（Li & Liang, 2021）在输入前插入可训练的特殊 token。但论文观察到：(a) 优化困难，性能不随可训练参数单调提升；(b) 占用序列长度，减少了处理下游任务的可用空间。

### 核心洞察

受 Li et al. (2018a) 和 Aghajanyan et al. (2020) 启发——过参数化的预训练模型实际上驻留在一个低内在维度的子空间中——论文提出假设：

> **模型适配过程中的权重变化 $\Delta W$ 也具有低"内在秩"（intrinsic rank）。**

这意味着，即使原始权重矩阵的秩 $d$ 高达 12,288（如 GPT-3），适配所需的更新可能只需要秩 $r = 1$ 或 $2$ 就能充分表达。

## 核心方法

### 低秩参数化更新矩阵

对于预训练权重矩阵 $W_0 \in \mathbb{R}^{d \times k}$，LoRA 将其更新约束为低秩分解：

$$W = W_0 + \Delta W = W_0 + BA$$

其中：
- $B \in \mathbb{R}^{d \times r}$，$A \in \mathbb{R}^{r \times k}$
- 秩 $r \ll \min(d, k)$
- $W_0$ **冻结**，不接收梯度更新
- $A$ 和 $B$ 为**可训练参数**

前向传播变为：

$$h = W_0 x + \Delta W x = W_0 x + BAx$$

### 初始化策略

- $A$ 用**随机高斯初始化**：$A \sim \mathcal{N}(0, \sigma^2)$
- $B$ 初始化为**零矩阵**：$B = 0$

这样 $\Delta W = BA = 0$ 在训练开始时，确保模型从预训练状态平滑启动，不会破坏预训练知识。

### 缩放因子 $\alpha / r$

LoRA 引入缩放超参数 $\alpha$：

$$h = W_0 x + \frac{\alpha}{r} BAx$$

- $\alpha$ 是与 $r$ 无关的常数
- 当使用 Adam 优化器时，调节 $\alpha$ 大致等价于调节学习率（配合适当的初始化缩放）
- 实际做法：固定 $\alpha$ 为首次尝试的 $r$ 值，之后改变 $r$ 时无需重新调参
- 这大大减少了超参数搜索空间

### 全量微调的推广

LoRA 是全量微调的推广：如果将 LoRA 应用于所有权重矩阵并训练所有偏置，当 $r$ 等于预训练权重矩阵的秩时，LoRA 的表达能力大致恢复全量微调。随着可训练参数增加，LoRA 收敛到原始模型训练；而 Adapter 收敛到 MLP，Prefix 收敛到短序列模型。

### 无额外推理延迟

部署时，可以预计算并存储 $W = W_0 + BA$，然后像普通模型一样推理。切换任务时，只需减去当前 $BA$ 并加上新的 $B'A'$——一个快速的内存操作。这**从构造上保证了零推理延迟**。

### 应用于 Transformer

论文主要将 LoRA 应用于自注意力模块的四个权重矩阵：$W_q, W_k, W_v, W_o$。实践中，为简单和参数效率，大多数实验只适配 $W_q$ 和 $W_v$。MLP 模块、LayerNorm 和偏置被冻结。

可训练参数量：$|\Theta| = 2 \times \hat{L}_{\text{LoRA}} \times d_{\text{model}} \times r$

其中 $\hat{L}_{\text{LoRA}}$ 是应用 LoRA 的权重矩阵数量。

### 实际收益

| 指标 | 全量微调 | LoRA | 改善 |
|------|---------|------|------|
| 可训练参数（GPT-3 175B）| 175B | 4.7M | **10,000× 减少** |
| 训练 VRAM（GPT-3 175B）| 1.2TB | 350GB | **3× 减少** |
| Checkpoint 大小（r=4, q+v）| 350GB | 35MB | **10,000× 减少** |
| 训练吞吐量（tokens/s/GPU）| 32.5 | 43.1 | **25% 提升** |

## 实验结果

### RoBERTa / DeBERTa on GLUE

Table 2 显示 LoRA 在 NLU 任务上表现：

- **RoBERTa base**：LoRA (0.3M 参数) 平均 87.2，优于 AdapterD (0.3M 的 84.4 和 0.9M 的 85.4)，接近全量微调 (86.4)
- **RoBERTa large**：LoRA (0.8M 参数) 平均 89.0，与全量微调 (88.9) 持平，优于所有 Adapter 变体
- **DeBERTa XXL (1.5B)**：LoRA (4.7M 参数) 平均 91.3，**超过**全量微调 (91.1)

### GPT-2 on E2E NLG Challenge

Table 3 显示在生成任务上：

- **GPT-2 Medium**：LoRA (0.35M) BLEU 70.4，超过全量微调 (68.2) 和所有基线
- **GPT-2 Large**：LoRA (0.77M) BLEU 70.4，与 Prefix-Layer (0.77M) 持平，超过全量微调 (68.5)

### GPT-3 175B 大规模验证

Table 4 是论文最核心的实验，在三个数据集上：

| 方法 | 可训练参数 | WikiSQL | MNLI-m | SAMSum (R1/R2/RL) |
|------|-----------|---------|--------|-------------------|
| Fine-Tune | 175,255.8M | 73.8 | 89.5 | 52.0/28.0/44.5 |
| BitFit | 14.2M | 71.3 | 91.0 | 51.3/27.4/43.5 |
| PrefixEmbed | 3.2M | 63.1 | 88.6 | 48.3/24.2/40.5 |
| PrefixLayer | 20.2M | 70.1 | 89.5 | 50.8/27.3/43.5 |
| AdapterH | 7.1M | 71.9 | 89.8 | 53.0/28.9/44.8 |
| AdapterH | 40.1M | 73.2 | 91.5 | 53.2/29.0/45.1 |
| **LoRA** | **4.7M** | **73.4** | **91.7** | **53.8/29.8/45.9** |
| **LoRA** | **37.7M** | **74.0** | **91.6** | **53.4/29.2/45.1** |

**关键发现**：
- LoRA 在 WikiSQL 和 SAMSum 上**超过全量微调**
- 在 MNLI-m 上也达到最佳性能
- 4.7M 参数（仅 0.003%）即可达到强劲性能
- 可训练参数与性能并非单调关系（Prefix 方法随参数增加性能下降）

## 消融实验

### 7.1 应该适配哪些权重矩阵？

在固定参数预算（18M）下，比较不同注意力权重矩阵的适配效果（Table 5）：

| 权重类型 | WikiSQL | MultiNLI |
|---------|---------|----------|
| $W_q$ | 70.4 | 91.0 |
| $W_k$ | 70.0 | 90.8 |
| $W_v$ | 73.0 | 91.0 |
| $W_o$ | 73.2 | 91.3 |
| $W_q, W_k$ | 71.4 | 91.3 |
| **$W_q, W_v$** | **73.7** | **91.3** |
| $W_q, W_k, W_v, W_o$ | 73.7 | 91.7 |

**结论**：适配 $W_q$ 和 $W_v$ 的组合在参数效率上最优。与其用更大秩适配单一矩阵，不如用较小秩适配多个矩阵。

### 7.2 最优秩 $r$ 是多少？

Table 6 展示不同 $r$ 的效果：

| 权重类型 | $r=1$ | $r=2$ | $r=4$ | $r=8$ | $r=64$ |
|---------|-------|-------|-------|-------|--------|
| $W_q$ (WikiSQL) | 68.8 | 69.6 | 70.5 | 70.4 | 70.0 |
| $W_q, W_v$ (WikiSQL) | **73.4** | 73.3 | **73.7** | 73.8 | 73.5 |
| $W_q, W_v$ (MultiNLI) | 91.3 | 91.4 | 91.3 | **91.6** | 91.4 |

**惊人发现**：
- $r = 1$ 对 $\{W_q, W_v\}$ 就已经足够！
- 增大 $r$ 带来的收益非常有限，甚至有时下降
- 这强有力地支持了"更新矩阵具有极低内在秩"的假设

### 子空间相似性分析

论文通过 Grassmann 距离分析不同 $r$ 学到的子空间重叠：

$$\phi(A_{r=8}, A_{r=64}, i, j) = \frac{\|U_{A_{r=8}}^{i\top} U_{A_{r=64}}^j\|_F^2}{\min(i, j)} \in [0, 1]$$

Figure 3 显示：$r=8$ 和 $r=64$ 的**顶部奇异向量方向高度重叠**，而其他方向基本不重叠。这说明增大 $r$ 只是增加了随机噪声方向，而非有意义的新信息。

### 7.3 $\Delta W$ 与 $W$ 的关系

Table 7 通过 Frobenius 范数分析 $\Delta W$ 与 $W$ 的关系：

| $r$ | $\|\Delta W_q\|_F$ | $\|U_{\Delta W}^\top W_q V_{\Delta W}^\top\|_F$ | $\|W_q\|_F$ |
|-----|-------------------|-----------------------------------------------|-------------|
| 4 | 6.91 | 0.32 | 61.95 |
| 64 | 3.57 | 1.90 | 61.95 |

关键洞察：
1. $\Delta W$ 与 $W$ 的相关性**强于随机矩阵**（说明 $\Delta W$ 放大了 $W$ 中已有的某些特征）
2. $\Delta W$ **没有重复** $W$ 的顶部奇异方向，而是放大了 $W$ 中**未被强调**的方向
3. 放大因子巨大：$r=4$ 时约为 $6.91/0.32 \approx 21.5$ 倍

这意味着 LoRA 的低秩更新**不是**在重复预训练已经学到的内容，而是**放大**了对下游任务重要但在通用预训练中被抑制的特征。

## 与 δ-mem 的关联

LoRA 是 δ-mem 低秩修正接口的**直接灵感来源**。两者的数学形式高度相似：

| 维度 | LoRA | δ-mem |
|------|------|-------|
| 形式 | $\Delta W = BA$ | $\Delta q_t = W_q^\Delta r_t$，$\Delta o_t = W_o^\Delta r_t$ |
| $W_q^\Delta, W_o^\Delta$ 的性质 | 训练后**固定** | 训练后固定 |
| 修正信号的来源 | 静态低秩矩阵 | **动态在线状态** $S_{t-1}$ |
| 是否随序列演化 | 否 | 是（通过 delta-rule） |
| 应用场景 | 下游任务适配 | 在线记忆/持续学习 |

**关键区别**：
- **LoRA 的低秩更新是静态的**：训练完成后 $B$ 和 $A$ 固定不变，同一输入永远产生同样的修正
- **δ-mem 的低秩修正来自动态在线状态**：$W_q^\Delta$ 和 $W_o^\Delta$ 虽然是训练后固定的投影矩阵，但输入 $r_t = S_{t-1} q_t^m$ 来自随序列持续演化的状态矩阵 $S_{t-1}$。同一组参数在不同历史下产生不同的引导效果

这种"静态形式 + 动态语义"的转化是 δ-mem 的核心创新之一：它借用了 LoRA 已被验证有效的低秩修正形式，但将修正信号的来源从静态参数替换为运行时动态更新的在线记忆状态。

## 推荐参考文献

### 直接相关工作

| 论文 | 作者 | 关系 |
|------|------|------|
| **Intrinsic Dimensionality Explains the Effectiveness of Language Model Fine-Tuning** | Aghajanyan et al., 2020 | LoRA 的理论动机来源：预训练模型具有低内在维度 |
| **Measuring the Intrinsic Dimension of Objective Landscapes** | Li et al., 2018a | 低内在维度的早期实证研究 |
| **Parameter-Efficient Transfer Learning for NLP** | Houlsby et al., 2019 | Adapter 方法，LoRA 的主要对比基线 |
| **Prefix-Tuning: Optimizing Continuous Prompts for Generation** | Li & Liang, 2021 | Prefix-Tuning，另一主要对比基线 |

### 后续发展与变体

| 论文 | 关系 |
|------|------|
| **QLoRA** (Dettmers et al., 2023) | 量化 + LoRA，进一步降低显存 |
| **DoRA** (Liu et al., 2024) | 权重分解低秩适配，更稳定 |
| **LoRA-FA** (Zhang et al., 2023) | 冻结 A 只训练 B，减少显存 |
| **AdaLoRA** (Zhang et al., 2023) | 自适应秩分配，不同层不同 $r$ |
| **PiSSA** (Meng et al., 2024) | 主奇异分量适配，更好的初始化 |

### δ-mem 相关

| 论文 | 关系 |
|------|------|
| **δ-mem: Efficient Online Memory for LLMs** | 直接借鉴 LoRA 低秩形式，赋予动态语义 |
| **Context2LoRA** | 将上下文编码为 LoRA 权重，静态参数化记忆 |

## 关联

- [[LoRA]] — 本论文提出的方法
- [[δ-mem（在线关联记忆）]] — 借鉴了 LoRA 的低秩接口形式，但赋予动态语义
- [[delta-rule-learning]] — δ-mem 状态更新的核心学习规则
- [[参数高效微调]] — LoRA 所属的方法大类
- [[低秩分解]] — LoRA 的数学基础
- [[Adapter]] — LoRA 的主要对比方法之一
- [[Prefix-Tuning]] — LoRA 的另一主要对比方法
- [[Aghajanyan-2020-Intrinsic-Dimension]] — LoRA 的理论动机来源
