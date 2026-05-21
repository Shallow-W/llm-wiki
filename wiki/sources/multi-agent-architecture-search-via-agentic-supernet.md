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

### 3.1 核心概念：从单系统到分布

MaAS 的根本思想转变：**不在所有查询上搜索一个统一的大而全系统，而是维护一个"系统池"（即 Supernet），让每个查询从这个池子里取出最适合自己的那个子系统**。

打个比方：传统方法相当于给所有病人开同一种药（不管感冒还是骨折），而 MaAS 相当于建了一个药房，根据病人症状自动配药——感冒只开感冒药（简单系统），重病才上全套检查（复杂系统）。

### 3.2 Agentic Operator（算子）—— 基本构建块

**定义**（Definition 3.1）：

一个算子 O 是一个复合 LLM-Agent 调用过程：

```
O = {{Mi}ᵢ₌₁ᵐ, P, {Ti}ᵢ₌₁ⁿ}
```

- **Mi**：LLM 实例（如 GPT-4o-mini），m 是调用的 LLM 数量
- **P**：自然语言 prompt（指导 LLM 如何执行任务）
- **Ti**：工具（如代码解释器、网络搜索），n 是工具数量

**论文初始化的 8 种算子**：

| 算子 | m (LLM数) | n (工具数) | 说明 |
|------|-----------|-----------|------|
| CoT (O_CoT) | 1 | 0 | 单 LLM 逐步推理，零工具 |
| Self-Consistency | 1 | 0 | 5 条 CoT 路径 + 多数投票 |
| Self-Refine | 1 | 0 | CoT 生成 + 最多 5 轮自我反思迭代 |
| LLM-Debate (O_Debate) | 3 | 0 | 3 个 LLM 辩论，最多 2 轮 |
| Ensemble | 3 | 0 | 3 个不同 LLM 分别回答 + pairwise ranking 聚合 |
| Testing | 1 | 1 | 生成测试用例（代码生成专用） |
| ReAct | 1 | 多个 | 代码解释器、网络搜索、知识库等工具 |
| Early-exit (O_exit) | 0 | 0 | 特殊算子，终止采样过程 |

关键理解：**大多数现有的单 Agent 或多 Agent 工作流都可以被视为一个算子**。CoT 是最简单的算子（1 个 LLM + 0 工具），Multi-agent Debate 是复杂算子（多 LLM + 多轮交互），ReAct 是带工具的算子。算子是"黑箱"——输入查询，输出答案，内部可以有任意复杂的逻辑。

### 3.3 Agentic Supernet（Agent 超网）—— 架构分布

**直觉理解**：

想象一个 L 层的"流水线"。每层有 8 个"插槽"，分别对应 8 种算子。Supernet 不是确定性地选择"第 1 层用 CoT、第 2 层用 Debate"，而是给每个选择赋予一个**概率**。就像一个多臂老虎机——每层有多个摇臂，以不同的概率拉动不同的臂。

一个从 Supernet 中采样出的多 Agent 系统，就是每层选出的算子按顺序串联起来形成的 DAG：

```
Supernet (L=4 层):
Layer 1: [CoT:0.35] [Debate:0.10] [ReAct:0.15] [Ensemble:0.05] [Self-Refine:0.10] [Testing:0.05] [Self-Consistency:0.08] [Early-exit:0.12]
Layer 2: [CoT:0.15] [Debate:0.20] [ReAct:0.10] [Ensemble:0.05] [Self-Refine:0.05] [Testing:0.10] [Self-Consistency:0.05] [Early-exit:0.30]
Layer 3: ...
Layer 4: ...

采样一次 → 得到一个具体的 4 层多 Agent 系统 G:
Layer 1: CoT + ReAct
Layer 2: Debate + Early-exit → 停止！
结果: G = [CoT → ReAct → Debate]（3 个算子的 DAG）
```

**形式化定义**（Definition 3.2）：

```
Agentic Supernet: A = {π, O}
  - π = {πℓ(O)}O∈O,ℓ₌₁ᴸ  — 参数化的条件概率分布
  - O = {O₁, ..., O₈}      — 可用算子集合
  - πℓ(O) = p(O | A₁:ℓ₋₁) — 第 ℓ 层选择算子 O 的概率，条件依赖于前 ℓ-1 层的选择
```

Supernet 诱导出所有可能的多 Agent 系统的**联合分布**：

```
p(G) = ∏ᴸℓ₌₁ ∏O∈O πℓ(O)^I(O∈Vℓ)
```

其中 Vℓ 是第 ℓ 层实际被选中的算子集合，I(·) 是指示函数。

**关键属性**：
- **概率化**：不是"选哪个"，而是"以多大比例选哪个"。训练的过程就是调整这些比例。
- **层间条件依赖**：第 2 层的选择取决于第 1 层选了什么。比如第 1 层选了 ReAct（已有工具），第 2 层可能更需要 Refine 而非另一个 ReAct。
- **DAG 约束**：采样出的系统 G = {V, E} 必须是有向无环图，保证执行顺序。
- **指数级候选空间**：每层可选多个算子 × L 层，候选架构数量巨大。但 Supernet 用参数化分布高效编码了整个空间。

### 3.4 查询条件采样 —— "看菜下碟"

Supernet 本身只是个分布，关键在于**如何根据输入查询从中采出一个合适的子系统**。这是 Controller 网络 Qϕ 的工作。

**问题**：同样的 Supernet，面对"2+3=?"和"证明费马大定理"应该采出完全不同的架构。

**Controller 的设计**：

```
输入: 查询 q（自然语言问题）+ 前面层已选的算子 {V₁, ..., Vℓ₋₁}
输出: 当前层选中的算子集合 Vℓ

计算过程:
1. 编码查询:     v(q) = Embedding(q)           // 用 MiniLM/Sentence-BERT 编码
2. 编码已有算子: v(Vₖ) = Σ v(O) for O∈Vₖ      // 对每层已选算子嵌入取平均
3. 拼接上下文:   context = v(q) ∥ v(V₁) ∥ v(V₂) ∥ ... ∥ v(Vℓ₋₁)
4. 计算激活分数: S = FFN(context)               // S ∈ R^|O|，每个算子一个分数
5. 排序激活:     S↓ = sort(S, descending)       // 按分数降序排列
6. 贪心选择:     选前 t 个算子，使得 Σⱼ₌₁ᵗ S↓[j] > thres  // thres=0.3
```

**每层选几个算子是动态的**：如果第一个算子的分数已经 > 0.3，则只选 1 个；如果分散，则选多个。thres=0.3 控制了每层的"开销"——越大则每层选的算子越多。

**Early-exit 的作用**：

Oexit 也是 8 个算子之一。如果某层采样到了 Oexit，整个采样过程提前终止：

```
Layer 1: [CoT: 选, ReAct: 选]   ← 2 个算子
Layer 2: [Early-exit: 选]        ← 命中提前退出！
结果: G = CoT → ReAct（2 层系统，简单便宜）
```

```
Layer 1: [Debate: 选, Self-Consistency: 选]
Layer 2: [ReAct: 选, Ensemble: 选]
Layer 3: [Self-Refine: 选, Testing: 选]
Layer 4: [CoT: 选, Early-exit: 选]
结果: G = 完整 4 层系统（复杂但强大）
```

这就是论文的核心卖点——**查询相关的资源分配**：简单问题自动用浅层简单架构（省 token），复杂问题自动用深层复杂架构（保质量）。

### 3.5 优化目标 —— 性能与成本的权衡

**形式化**（Eq. 5）：

```
max_P(G|q) E(q,a)~D, G~P(G|q) [U(G; q, a) − λ · C(G; q)]
```

- **U(G; q, a)**：效用/性能函数——系统 G 对查询 q 产生答案 a 的质量（正确率、pass@1）
- **C(G; q)**：成本函数——系统 G 处理查询 q 的 token 消耗 / API 费用
- **λ**：成本惩罚系数（λ ∈ {1e−3, 5e−3, 1e−2}）
- **P(G|q)**：要优化的条件分布——给定查询 q，生成系统 G 的概率

注意目标不是找到一个最优 G，而是优化**分布 P(G|q)** 本身。这就是"优化超网"而非"优化架构"的含义。

### 3.6 双层梯度更新 —— 如何训练超网

训练需要同时更新两样东西：**分布参数 π**（每层选哪个算子的概率）和**算子 O**（算子内部的 prompt、温度、结构）。两者性质截然不同，需要不同的优化策略。

#### 层 1：分布 π 的梯度（可微，蒙特卡洛估计）

由于执行系统 G 涉及外部 API 调用，e(a|G) 不可微。论文用经验贝叶斯蒙特卡洛方法近似梯度：

```
∇πL ≈ (1/K) Σ(q,a)∈D Σk₌₁ᴷ mk · ∇π p(Gk)
```

其中 K=4 是采样次数（对同一查询采样 K 个不同架构），mk 是**成本感知的重要性权重**：

```
mk = [p(a|q,Gk) / Σᵢ p(a|q,Gi)] − λ · [C(Gk;q) / Σᵢ C(Gi;q)]
```

直观理解：**正确率高 + token 成本低的架构得到正权重，正确率低或成本高的架构得到负权重**。梯度更新会让 π 偏向那些"又好又便宜"的架构。

为什么采样 K=4 次？消融实验表明 K=2 时方差太大性能不稳定，K=4 达到满意低方差估计，再大边际收益递减。

#### 层 2：算子 O 的梯度（不可微，文本梯度）

算子包含自然语言 prompt 和黑箱工具调用，无法用数值梯度更新。论文引入**文本梯度**（Textual Gradient），用 LLM 生成自然语言形式的"梯度分析"：

```
∇OL = TP ⊕ TT ⊕ TN
```

三种文本梯度分别更新算子的不同层面：

| 梯度类型 | 目标 | 示例更新 |
|----------|------|----------|
| TP（Prompt Gradient） | 算子的 prompt 文本 | "给 Debate 算子的 debater 之间添加过渡提示'请基于以上观点反驳'" |
| TT（Temperature Gradient） | LLM 的温度参数 | "降低 Ensemble 中第三个 LLM 的温度到 0.3，以提高输出稳定性" |
| TN（Node Structure Gradient） | 算子的代码结构 | "将 Testing 算子拆分为 UnitTest + IntegrationTest 两个子节点" |

**文本梯度的实现**：一个专门的 gradient agent 接收"当前算子代码 + 执行结果 + 环境反馈"，输出 JSON 格式的改进建议（thought + description + code）。这与 ADAS 和 AgentSquare 的 textual feedback 机制类似。

**消融实验验证**：移除文本梯度后性能下降最大（HumanEval −2.68pp, MATH −3.59pp），说明算子的自我演化能力是 MaAS 的核心贡献之一。

### 3.7 完整算法流程

```
Algorithm 1: MaAS
─────────────────────────────────────────────────
Input:  数据集 D (训练集 Dtrain + 测试集 Dtest)
        算子集 O = {CoT, Debate, Self-Consistency, 
                    Self-Refine, Ensemble, Testing, 
                    ReAct, Early-exit}
        初始分布 π（随机初始化）
        Controller 网络 Qϕ
Output: 优化后的 Agentic Supernet {π, O}

for (q, a) in Dtrain do
    ▸ Step 1: 查询条件采样
    for layer ℓ ← 1 to L (=4) do
        Vℓ ← Qϕ(Vℓ | q, {V₁,...,Vℓ₋₁})   // MoE 风格条件采样
        if ℓ = L or O_exit ∈ Vℓ then break  // 提前退出
    end
    G ← ⟨V₁, V₂, ..., Vℓ⟩                  // 得到定制化 DAG

    ▸ Step 2: 执行采样出的系统
    ˜a ← Execute(G, q)                       // 实际运行多 Agent 系统

    ▸ Step 3: 双层优化
    ∇πL ← MonteCarlo(q, a, {G₁,...,GK})     // 蒙特卡洛估计分布梯度
    ∇OL ← TextualGradient(G, q, ˜a, a)      // LLM 生成算子梯度
    Update π via ∇πL                          // 更新选择概率
    Update O via ∇OL                          // 更新算子内部

    ▸ Step 4: 记录到 Archive（供后续文本梯度参考）
    Archive.append(G, ˜a, feedback)
end
```

### 3.8 与 NAS 中 DARTS 的类比

MaAS 的思想直接借鉴自神经架构搜索中的 DARTS (Liu et al., 2018)：

| 维度 | DARTS (NAS) | MaAS (Agent NAS) |
|------|-------------|-------------------|
| 搜索空间 | CNN 单元中的卷积操作 | 多 Agent 系统中的算子 |
| 搜索对象 | 最优网络拓扑 | 最优 Agent 架构 |
| 参数化 | 每条边上的 softmax 权重 | 每层上的算子概率分布 π |
| 优化方式 | 梯度下降 | 蒙特卡洛 + 文本梯度 |
| 输出 | 一个确定性网络 | 一个查询条件分布 |
| 额外机制 | 无 | Early-exit + 成本约束 |

核心区别：DARTS 优化后得到一个确定性的最优网络，而 MaAS 优化后得到一个**分布**——每次查询都可以从中采样不同的架构。这使得 MaAS 天然支持不同难度的查询使用不同复杂度的系统。

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
