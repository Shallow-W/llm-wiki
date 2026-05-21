---
id: source-multi-agent-architecture-search-via-agentic-supernet
date: 2026-05-21
source: raw/papers/Multi-agent Architecture Search via Agentic Supernet.pdf
url: https://arxiv.org/abs/2502.04180
type: 论文
authors: [Guibin Zhang, Luyang Niu, Junfeng Fang, Kun Wang, Lei Bai, Xiang Wang]
venue: ICML 2025
tags: [Agent, 精读, NAS, 多Agent, 自动演化]
---

# Multi-agent Architecture Search via Agentic Supernet

## 一句话总结

将 NAS 中的超网思想迁移到多 Agent 系统，提出 Agentic Supernet——一种概率化、连续分布的 Agent 架构分布，通过查询感知采样为不同难度/领域的问题动态分配资源（LLM 调用、工具调用、token 成本），在 6 个基准上全面超越人工设计和自动搜索基线，训练成本仅为 AFlow 的 15%。

## 基本信息

- **作者**：Guibin Zhang*¹², Luyang Niu*², Junfeng Fang¹, Kun Wang³, Lei Bai⁴, Xiang Wang⁵
- **机构**：¹ 新加坡国立大学, ² 同济大学, ³ 南洋理工大学, ⁴ 上海人工智能实验室, ⁵ 中国科学技术大学
- **发表**：ICML 2025
- **链接**：[arXiv 2502.04180](https://arxiv.org/abs/2502.04180) | [GitHub](https://github.com/bingreeky/MaAS)

## 问题与动机

当前多 Agent 系统设计存在两个核心困境：

1. **Dilemma 1 — 资源浪费**：现有方法搜索一个单一的"大而全"多 Agent 系统，对所有查询都用同样的复杂流程。但简单的小学算术不需要多轮辩论和工具调用，只有博士级抽象代数才需要。
2. **Dilemma 2 — 跨域失效**：单一系统无法同时优化不同领域的任务。GAIA 基准中的文件读取和网络搜索需要完全不同的 Agent 架构。

核心洞察：**与其追求一个（可能根本不存在的）全局最优系统，不如优化一个架构分布，让每个查询从分布中采样最适合自己的子系统。**

## 核心方法

### 总体框架

```
┌──────────────────────────────────────────────────────────┐
│                    MaAS 训练循环                          │
│                                                          │
│  ① 输入查询 q → Controller Qϕ 从 Agentic Supernet 采样   │
│  ② 生成定制化多 Agent 系统 G（查询相关、DAG 结构）         │
│  ③ 执行 G，获得答案 ˜a 和环境反馈                         │
│  ④ 优化分布 π：蒙特卡洛梯度估计（性能 − λ·成本）          │
│  ⑤ 优化算子 O：文本梯度（prompt、温度、节点结构的 LLM 生成更新）│
│  ⑥ 重复直到收敛                                          │
└──────────────────────────────────────────────────────────┘
```

### 三个核心定义

#### Definition 3.1：Agentic Operator

一个算子 O 是一个复合 LLM-Agent 调用过程，包含：

```
O = {{Mi}ᵢ₌₁ᵐ, P, {Ti}ᵢ₌₁ⁿ}
```

其中 M 是 LLM 实例，P 是 prompt，T 是工具。例如：
- CoT：m=1, n=0
- Self-RAG：m=1, n=1（检索引擎）
- Multi-agent Debate：多 LLM、多轮调用

#### Definition 3.2：Agentic Supernet

```
A = {π, O} = {{πℓ(O)}O∈O}ℓ₌₁ᴸ
πℓ(O) = p(O | A₁:ℓ₋₁)
```

一个 L 层的概率化、连续架构分布。每层 ℓ 上每个算子 O 有一个条件概率 πℓ(O)，依赖于前面层的选择。这诱导了一个关于所有可能多层算子配置的联合分布 p(G)。

#### Definition 3.3：多 Agent 系统

```
G = {V, E}, V ⊂ O, E ∈ V × V
```

一个 DAG，节点是选中的算子，边是连接关系。

### Controller 网络：MoE 风格的查询条件采样

控制器 Qϕ 实现为一个 Mixture-of-Experts 风格网络：

```
πℓ: q → Vℓ
Si = FFN(v(q) ∥ Σ v(O∈V₁) ∥ ... ∥ Σ v(O∈Vℓ₋₁))
```

- v(·) 用 MiniLM/Sentence-BERT 做文本嵌入
- 算子按得分降序激活，累积得分超过阈值 thres=0.3 时停止
- **Early-exit 算子 Oexit**：如果某层采样到 Oexit，则提前终止，实现查询相关的深度

### 优化目标

```
max E(q,a)~D, G~P(G|q) [U(G; q, a) − λ·C(G; q)]
```

- U(·)：效用/性能（正确率、pass@1）
- C(·)：成本（token 数、API 费用）
- λ：权衡系数

### 双层梯度更新

**分布 π 的梯度**（可微）：

用经验贝叶斯蒙特卡洛估计：

```
∇πL ≈ 1/K Σ(q,a) Σk₌₁ᴷ mk ∇π p(Gk)
mk = p(a|q,Gk) / Σ p(a|q,Gi) − λ·C(Gk;q) / Σ C(Gi;q)
```

mk 是成本感知的重要性权重——高正确率且低成本的架构获得更高权重。

**算子 O 的梯度**（不可微，黑箱工具+自然语言）：

用文本梯度（Textual Gradient）近似反向传播：

```
∇OL = TP ⊕ TT ⊕ TN
```

- TP：prompt 的文本梯度（如"给 debate 算子添加过渡提示"）
- TT：温度的文本梯度（如"降低 ensemble LLM 的温度以提高稳定性"）
- TN：节点结构的文本梯度（如"合并/拆分/修改算子"）

文本梯度由 LLM 生成，作为自然语言形式的梯度分析。

### Algorithm 1：MaAS 外层循环

```
Input: 数据集 D (训练集 Dtrain + 测试集 Dtest),
       算子集 O, 初始分布 π, Controller Qϕ
Output: 优化后的 Agentic Supernet {π, O}

for (q, a) in Dtrain do
    for layer ℓ ← 1 to L do
        Vℓ ← πϕ(Vℓ | q, {Vh}h₌₁ˡ⁻¹)    // 条件采样
        if ℓ = L or Oexit ∈ Vℓ then break  // 提前退出
    G ← ⟨V₁, ..., Vℓ⟩                  // 构建多 Agent 系统
    ˜a ← e(a|G)                        // 执行
    ∇πL ← 蒙特卡洛估计                  // Eq. 11
    ∇OL ← 文本梯度估计                  // Eq. 12
    更新 π 和 O
end for
```

## 实验设置

- **基准（6 个）**：
  - 数学推理：GSM8K, MATH (617 题), MultiArith
  - 代码生成：HumanEval, MBPP
  - 工具使用：GAIA
- **基线（14+）**：
  - 单 Agent：CoT, ComplexCoT, Self-Consistency
  - 手工多 Agent：MultiPersona, LLM-Debate, LLM-Blender, DyLAN, AgentVerse, MacNet
  - 自动多 Agent：AutoAgents, GPTSwarm, ADAS, AgentSquare, AFlow
- **骨干模型**：gpt-4o-mini（主实验）, Qwen-2.5-72b, llama-3.1-70b
- **超参数**：L=4, λ∈{1e−3, 5e−3, 1e−2}, K=4, thres=0.3
- **训练/测试比例**：1:4
- **算子空间**：CoT, LLM-Debate, Self-Consistency, Self-Refine, Ensemble, Testing, ReAct, Early-exit

## 关键结果

### 主实验：6 个基准全面领先

| 方法 | GSM8K | MATH | MultiArith | HumanEval | MBPP | Avg. |
|------|-------|------|------------|-----------|------|------|
| Vanilla | 87.45 | 46.29 | 96.85 | 87.08 | 71.83 | 77.50 |
| AFlow (SOTA) | 91.16 | **51.28** | 96.22 | 90.93 | **81.67** | 82.25 |
| **MaAS (Ours)** | **92.30** | **51.82** | **98.80** | **92.85** | **82.17** | **83.59** |
| 相对提升 | +4.85 | +5.53 | +1.95 | +5.77 | +10.34 | — |

MaAS 在所有 5 个基准上达到最佳，平均超越手工方法 3.90~6.40%，超越自动方法 2.07~8.26%。

### GAIA 基准（工具使用）

| 方法 | Level 1 | Level 2 | Level 3 | Avg. |
|------|---------|---------|---------|------|
| AFlow | 10.75 | 8.81 | 4.08 | 8.00 |
| GPTSwarm | 23.66 | 16.35 | 2.04 | 16.33 |
| AgentSquare | 22.58 | 15.72 | 6.25 | 16.34 |
| **MaAS** | **25.91** | **22.01** | 6.25 | **20.69** |

GAIA 跨域特性使得单一系统基线（AFlow 仅 8.00%）表现很差，而 MaAS 通过查询相关采样在 Level 1/2 分别提升 18.38% 和 17.61%。

### 成本效率分析（MATH 基准）

| 维度 | AFlow | MaAS | 比率 |
|------|-------|------|------|
| 训练 token | 33.8M | 3.05M | **6.8× 更少** |
| 训练费用 | $22.50 | $3.38 | **6.8× 更便宜** |
| 训练时间 | 184 min | 53 min | **3.5× 更快** |
| 推理 token | 2.5M | 1.31M | **1.9× 更少** |
| 推理费用 | $1.66 | $0.42 | **4.0× 更便宜** |
| 推理时间 | 23 min | 19 min | **1.2× 更快** |
| **正确率** | **51.28%** | **51.82%** | **+0.54%** |

核心发现：MaAS 用 AFlow 15% 的训练成本、25% 的推理成本，实现了更高的正确率。

### 跨模型迁移

| 数据集 | 模型 | Vanilla | +MaAS | 提升 |
|--------|------|---------|-------|------|
| HumanEval | gpt-4o-mini | 87.08 | **92.85** | +5.77 |
| HumanEval | Qwen-2.5-72b | 85.60 | **90.14** | +4.54 |
| HumanEval | llama-3.1-70b | 80.06 | **85.26** | +5.20 |
| MATH | gpt-4o-mini | 46.29 | **51.82** | +5.53 |
| MATH | Qwen-2.5-70b | 63.80 | **69.35** | +5.55 |
| MATH | llama-3.1-70b | 31.93 | **42.97** | +11.04 |

llama-3.1-70b 上 MATH 提升最大（+11.04%），再次验证了**越不饱和的模型，架构优化收益越大**的规律。

### 跨数据集迁移

| 迁移方向 | GPTSwarm | AFlow | MaAS |
|----------|----------|-------|------|
| MATH→GSM8K | 89.96 | 91.95 | **92.80** |
| GSM8K→MATH | 45.18 | 49.39 | **51.02** |
| HumanEval→MATH | 47.92 | 47.15 | **50.27** |

### 消融实验

| 条件 | HumanEval pass@1 | HumanEval 成本 | MATH acc | MATH 成本 |
|------|------------------|----------------|----------|-----------|
| Vanilla MaAS | **92.85** | 1.01 | **51.82** | 0.86 |
| w/o ∇OL（无文本梯度） | 90.17 | 0.90 | 48.23 | 0.84 |
| w/o Oexit（无提前退出） | 91.44 | 1.67 | 51.53 | 1.04 |
| w/o C(·)（无成本约束） | 92.94 | 1.38 | 51.19 | 1.28 |

- **文本梯度最重要**：移除后性能最大下降（−2.68pp / −3.59pp），因为这是 MaAS 自演化能力的来源
- **Oexit 主要影响成本**：移除后成本显著上升但性能几乎不变
- **成本约束 C(·)**：移除后性能微升但成本大幅上升，说明 λ 的权衡有效

### 算子分布可视化（Case Study）

- **Easy 查询**（如"42! 末尾有几个零"）：第 2 层以 0.47 概率选择 early-exit，仅使用 I/O + CoT
- **Medium 查询**（如骰子期望）：使用到第 3 层，Ensemble + Self-Consistency 被激活
- **Hard 查询**（如复合分数运算）：使用全部 4 层，ReAct + Debate + Refine 等高成本算子被激活

### 归纳能力（Inductive Analysis）

将 Debate 算子作为 holdout（训练时不暴露），测试时引入。MaAS 仍能合理地在适当比例下选择该未见过算子，证明其泛化到新算子的能力。

## 局限性

- **算子空间依赖人工定义**：虽然 MaAS 可以演化算子的 prompt 和结构，但算子类型的初始集合（CoT, Debate, ReAct 等）仍由人类设计
- **文本梯度的不可控性**：算子更新依赖 LLM 生成的自然语言"梯度"，质量和一致性难以保证
- **基准规模有限**：训练集仅 33~264 个样本（1:4 比例），对于复杂算子演化可能不够
- **成本评估仅限 token/API 费用**：未考虑延迟、并发、缓存等实际部署因素
- **仅测试了文本模态**：多模态任务（视觉、音频）未验证
- **Early-exit 阈值固定**：thres=0.3 是超参数，未探索自适应阈值

## 提及的实体

- [[Guibin-Zhang]] — 新加坡国立大学 & 同济大学，MaAS 共同一作
- [[Luyang-Niu]] — 同济大学，MaAS 共同一作
- [[Junfeng-Fang]] — 新加坡国立大学，MaAS 共同作者
- [[Kun-Wang]] — 南洋理工大学，MaAS 通讯作者
- [[Lei-Bai]] — 上海人工智能实验室，MaAS 共同作者
- [[Xiang-Wang]] — 中国科学技术大学，MaAS 共同作者
- [[新加坡国立大学]] — MaAS 第一署名机构
- [[同济大学]] — MaAS 共同署名机构
- [[南洋理工大学]] — MaAS 第三署名机构，Kun Wang 所属
- [[上海人工智能实验室]] — MaAS 第四署名机构，Lei Bai 所属
- [[中国科学技术大学]] — MaAS 第五署名机构

## 讨论的概念

- [[Agentic-Supernet|Agentic Supernet]] — 概率化、连续的多 Agent 架构分布
- [[Multi-agent-Architecture-Search|Multi-agent Architecture Search (MaAS)]] — 本文核心方法
- [[Textual-Gradient|文本梯度]] — 用 LLM 生成自然语言形式的梯度来更新不可微算子
- [[Early-Exit-Operator|Early-exit Operator]] — 使 supernet 深度查询相关的提前退出机制
- [[Query-Dependent-Sampling|查询条件采样]] — 根据查询难度动态选择算子组合
- [[Controller-Network-Qphi|Controller Network Qϕ]] — MoE 风格的查询条件架构采样器

## 关联

- **与 [[agentic-harness-engineering|AHE]]**：AHE 优化 harness（提示、工具、中间件等文件），MaAS 优化多 Agent 架构（算子组合和连接）。两者互补——MaAS 解决"用什么样的 Agent 团队"，AHE 解决"Agent 用什么工具/提示"。
- **与 [[gstc-zero-cost-proxy-nas|GSTC]]**：两者都受 NAS 启发，但 GSTC 搜索神经网络架构，MaAS 搜索 Agent 系统架构。Agentic Supernet 的概念直接借鉴自 DARTS/SNAS 等权重共享超网。
- **与 [[agent0-bootstrapping-from-zero-data|Agent0]] / [[metaclaw-continuous-evolution-in-production|MetaClaw]]**：Agent0/MetaClaw 优化 LLM 权重或 LoRA adapter，MaAS 优化 Agent 系统的结构配置——正交的优化维度。
- **与 [[swarm-ide|Swarm-IDE]]**：Swarm-IDE 提供动态嵌套 Agent 的运行时基础设施，MaAS 提供自动发现最优嵌套/连接结构的搜索算法。两者结合可实现"自动发现 + 动态执行"的闭环。

## 个人笔记

MaAS 的核心创新是将 NAS 的"超网"思想迁移到多 Agent 系统领域。这个迁移非常自然但之前没人做过：

1. **从"搜索一个最优架构"到"优化一个架构分布"**：这是根本性的范式转变。DARTS 在 CNN 上做过同样的事（2018），MaAS 在 Agent 领域重现了这一转变。

2. **Early-exit 是关键设计**：没有 early-exit，所有查询都会走完整 L 层，失去了查询相关的意义。Early-exit 使得简单问题可以用简单架构，复杂问题才用复杂架构。

3. **文本梯度的巧妙与局限**：用 LLM 生成"梯度"来更新不可微算子是一个聪明的工程妥协，但它的质量高度依赖 LLM 的能力。对于代码生成算子（如 Testing），文本梯度可能有效；但对于需要精确数学变换的算子，可能不够可靠。

4. **与 AHE 的互补性**：AHE 的 NexAU 框架暴露 7 种组件类型，MaAS 的算子空间可以看作是这些组件的一种结构化编排。如果 MaAS 的算子定义与 NexAU 的组件对齐（如 ReAct 对应 Tools、Debate 对应 Sub-agents），两个框架可以无缝集成。

5. **实际部署的想象空间**：在生产环境中，MaAS 可以在用户查询到达时实时采样架构——简单查询用 1-2 个算子（低成本低延迟），复杂查询用 4 层完整架构（高质量）。这种细粒度资源分配在 API 计费场景下极具商业价值。
