---
id: concept-delta-mem
date: 2026-05-15
aliases: [δ-mem, delta-mem]
tags: [概念, LLM记忆, 在线学习, 注意力机制]
---

# δ-mem（在线关联记忆）

## 定义

δ-mem 是一种轻量级的 LLM 记忆机制，在冻结的全注意力 Transformer 骨干网络上附加一个紧凑的**在线关联记忆状态**（Online State of Associative Memory, OSAM）。该状态通过 delta-rule 学习持续更新，并在推理时以低秩修正的方式直接参与注意力计算。

## 核心思想

传统方法要么把历史塞进上下文（代价高、效果差），要么用外部模块检索（与骨干脱节）。δ-mem 走了第三条路：

> **把历史压缩进一个固定大小的矩阵，让这个矩阵的读出信号直接修正注意力的 query 和 output。**

这就像给模型的注意力机制装了一个"记忆透镜"——透镜本身很小，但能根据历史信息动态调整焦距，让模型"看到"原本看不到的历史关联。

## 关键属性

### 状态矩阵 S

- **大小**：固定为 $r \times r$（论文中 $r=8$，即 8×8 = 64 个浮点数）
- **更新规则**：门控 delta-rule
  $$S_t = \text{Diag}(\lambda_t) S_{t-1} + \text{Diag}(\beta_t)(v_t - S_{t-1} k_t) k_t^\top$$
- **三项分解**：保留旧状态 → 擦除旧预测 → 写入新值

### 三步循环

1. **读（Read）**：$r_t = S_{t-1} q_t^m$ — 用当前输入查询记忆状态，代价与历史长度无关
2. **引导（Steer）**：将 $r_t$ 投影为 query 侧和 output 侧的低秩修正，直接加到注意力计算中
3. **写（Write）**：用当前 token 的 key-value 信息通过 delta-rule 更新状态

### 三种写入策略

| 策略 | 粒度 | 适用场景 |
|------|------|----------|
| TSW（Token-State Write） | 每 token | 中等模型，需捕捉细粒度变化 |
| SSW（Sequence-State Write） | 每消息/段 | 大模型，平滑噪声效果更好 |
| MSW（Multi-State Write） | 多个并行子状态 | 小模型，减少信息干扰 |

## 关键属性

- **极致轻量**：仅 4.87M 可训练参数（骨干的 0.12%）
- **骨干冻结**：不修改原始模型参数
- **在线演化**：状态随序列动态更新，非静态 adapter
- **与注意力耦合**：记忆直接参与前向计算，不经过外部检索路径
- **通用保持**：在增强记忆的同时基本不损害通用能力（IFEval 基本不降）

## 性能表现

| 场景 | 提升幅度 |
|------|----------|
| 总平均分 | 1.10× 骨干、1.15× 最强基线 |
| MemoryAgentBench | 1.31× |
| LoCoMo | 1.20× |
| TTL（Test-time Learning） | 26.14 → 50.50（近翻倍） |

## 相关概念

- [[delta-rule-learning]] — 状态更新的核心学习规则
- [[低秩注意力修正]] — δ-mem 引导注意力的机制
- [[LLM记忆机制分类]] — TMM/OMM/PMM 三类范式
- [[LoRA]] — 同为低秩修正，但 LoRA 是静态的，δ-mem 是动态的
- [[Context-Rot]] — 解释了为什么需要更好的记忆机制

## 来源

- [[delta-mem-efficient-online-memory]] — δ-mem 的原始论文

## 参见

- [[Titans]] — 同为测试时记忆，但 Titans 是架构级创新（深度 MLP 记忆替换骨干），δ-mem 是插件级创新（8×8 矩阵附加在冻结骨干上）。两者共享 delta-rule + 遗忘的核心思想
- [[mem0-building-production-ready-ai-agents|Mem0]] — 文本级外部记忆的代表，与 δ-mem 的参数级内部记忆形成互补。Mem0 解决"存什么"和"怎么找"，δ-mem 解决"怎么记"和"怎么用"
- [[Memorizing-Transformers]] — 外部 kNN 记忆
- [[Model-Context-Protocol-MCP]] — 解决 LLM 与外部世界的交互问题，与 δ-mem 的内部记忆互补
