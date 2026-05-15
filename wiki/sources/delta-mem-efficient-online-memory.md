---
id: source-delta-mem-efficient-online-memory
date: 2026-05-15
source: raw/papers/δ-mem-EfficientOnlineMemoryforLarge.pdf
type: 论文
tags: [LLM记忆, 在线学习, 注意力机制, delta-rule, 低秩修正]
---

# δ-mem: Efficient Online Memory for Large Language Models

## 一句话总结

提出 δ-mem：在冻结的全注意力骨干网络上，用一个极其紧凑（8×8）的在线关联记忆状态矩阵，通过 delta-rule 学习持续更新，并以低秩修正的方式直接参与注意力计算，实现轻量高效的 LLM 在线记忆。

## 基本信息

| 项目 | 内容 |
|------|------|
| **标题** | δ-mem: Efficient Online Memory for Large Language Models |
| **作者** | Jingdi Lei†, Di Zhang†, Junxian Li, Weida Wang, Kaixuan Fan, Xiang Liu, Qihan Liu, Xiaoteng Ma, Baian Chen, Soujanya Poria |
| **机构** | 南洋理工大学、复旦大学、Mind Lab、上海交通大学、香港中文大学、香港科技大学（广州） |
| **日期** | 2026-05-13 |
| **arXiv** | 2605.12357v1 |
| **代码** | [Declare-lab & MindLab-Research](https://github.com/Declare-lab/MindLab-Research) |
| **骨干模型** | Qwen3-4B-Instruct、Qwen3-8B、SmolLM3-3B |

## 研究背景与动机

### LLM 的记忆困境

随着 LLM 被部署到长期助手和 Agent 系统中，模型需要**持续积累、更新和复用历史信息**。当前的主流方案——简单扩展上下文窗口——存在三大问题：

1. **计算开销大**：标准注意力的计算量随上下文长度呈二次增长。
2. **上下文退化/腐烂（Context Rot）**：即使上下文窗口扩展到百万 token，模型也不一定能有效利用这些额外信息（Hong et al., 2025; Du et al., 2025）。
3. **多轮对话中的迷失**：LLM 在多轮交互中容易丢失关键信息（Laban et al., 2025）。

> **核心洞察**：扩展上下文窗口只是把记忆问题转化为长上下文处理问题，并没有从根本上解决记忆。

### 现有记忆机制的三类范式

论文从两个维度——**记忆状态**（如何存储）和**记忆引导**（如何影响推理）——统一分析现有方法：

| 范式 | 代表方法 | 原理 | 局限 |
|------|----------|------|------|
| **文本记忆（TMM）** | BM25 RAG、LLMLingua-2、MemoryBank | 将记忆存为文本，通过输入上下文注入 | 受上下文窗口限制、检索噪声、压缩信息损失 |
| **外部通道记忆（OMM）** | Memorizing Transformers、MLP Memory | 在外部模块存储记忆，通过检索/编码回传 | 额外开销、融合复杂、与骨干不匹配 |
| **参数化记忆（PMM）** | LoRA、Prefix-Tuning、ROME/MEMIT | 将记忆编码到参数中 | 静态的，无法随序列动态演化 |

**δ-mem 的定位**：参数化记忆的低秩接口 + 在线动态状态 = 既紧凑又可演化。

## 核心方法

### 设计哲学

δ-mem 的核心思路可以概括为一句话：

> **将历史信息压缩到一个固定大小的在线状态矩阵中，通过 delta-rule 不断更新，然后在生成时用状态的读出信号对注意力计算做低秩修正。**

这个过程不修改骨干网络参数，不添加额外的上下文 token，不依赖外部检索模块。

### 计算流程

每个位置 t 的计算按以下顺序执行：**读 → 引导注意力 → 写**。

#### 第一步：记忆投影（Memory Projections）

给定隐藏状态 $x_t \in \mathbb{R}^d$，投影到低维关联记忆空间（维度 $r$）：

$$q_t^m = \text{L2-norm}(\tanh(W_q^m x_t))$$
$$k_t^m = \text{L2-norm}(\tanh(W_k^m x_t))$$
$$v_t^m = W_v^m x_t$$

其中 $q_t^m$ 用于查询旧状态，$k_t^m$ 和 $v_t^m$ 描述如何写入。L2 归一化可减少长序列递推中的尺度漂移。

门控信号也由隐藏状态决定：

$$\beta_t = \sigma(W_\beta x_t + b), \quad \lambda_t = 1 - \beta_t$$

这允许每个维度独立控制"保留多少旧记忆"和"写入多少新信息"。

#### 第二步：从在线状态中读取（Reading）

$$r_t = S_{t-1} q_t^m$$

读取向量 $r_t$ 是用当前输入查询记忆状态的结果。由于 $S_{t-1}$ 大小固定，这一步的代价**与历史长度无关**。

#### 第三步：通过低秩修正引导注意力（Steering）

读取信号通过两个轻量线性映射，生成 query 侧和 output 侧的修正：

$$\Delta q_t = W_q^\Delta r_t, \quad \Delta o_t = W_o^\Delta r_t$$

修正后的注意力计算：

$$\tilde{q}_t = q'_t + \frac{\alpha}{r} \Delta q_t$$
$$\tilde{y}_t = \text{Attn}(\tilde{q}_t, K_{\leq t}, V_{\leq t}) + \frac{\alpha}{r} \Delta o_t$$

> **关键区别**：虽然 $W_q^\Delta$ 和 $W_o^\Delta$ 训练后固定，但输入 $r_t$ 来自动态状态 $S_{t-1}$。同一组参数在不同历史下产生不同的引导效果——这不是静态 adapter，而是**状态条件化的动态修正**。

#### 第四步：通过 Delta-Rule 写入状态（Writing）

当前信息通过门控 delta-rule 更新状态：

$$S_t = \text{Diag}(\lambda_t) S_{t-1} + \text{Diag}(\beta_t)(v_t^m - S_{t-1} k_t^m)(k_t^m)^\top$$

三项的物理含义：
1. **保留项**：$\lambda_t$ 控制旧状态的保留程度
2. **擦除项**：沿当前 key 方向移除旧预测
3. **写入项**：沿当前 key 方向写入新值

> **与 LoRA 的本质区别**：LoRA 的低秩更新是静态的（训练后固定），δ-mem 的低秩修正来自运行时动态演化的在线状态。

### 三种写入粒度策略

| 策略 | 缩写 | 粒度 | 特点 |
|------|------|------|------|
| **Token-State Write** | TSW | 每个 token 写入一次 | 最细粒度，但容易受格式符号和噪声影响 |
| **Sequence-State Write** | SSW | 每个消息/段写入一次（平均隐藏状态） | 减少冗余写入，平滑状态演化 |
| **Multi-State Write** | MSW | 多个并行子状态分别写入，读出拼接 | 减少不同类型信息之间的互相覆盖和干扰 |

### 训练目标

标准 SFT 交叉熵损失。训练时，上下文先写入状态产生 $S_C$，但**不作为显式骨干输入回放**。冻结骨干只接收 query 和 response，通过状态引导注意力：

$$\mathcal{L}_{SFT} = -\sum_{j=1}^{|Y|} \log p_{\phi,\theta}(y_j | Q, y_{<j}, S_C)$$

## 实验结果

### 主实验：不同记忆机制对比（Qwen3-4B-Instruct 骨干）

| 方法 | IFEval | HotpotQA EM | GPQA-D | MemAgent Avg | LoCoMo Avg | 总平均 |
|------|--------|-------------|--------|-------------|------------|--------|
| 骨干（无记忆） | 81.89 | 42.35 | 39.39 | 29.54 | 40.79 | 46.79 |
| + BM25 RAG | - | 40.35 | - | 24.49 | 38.12 | 44.56 |
| + LLMLingua-2 | - | 36.93 | - | 15.63 | 39.07 | 42.96 |
| + MemoryBank | - | - | - | 17.65 | 37.88 | 43.88 |
| + Context2LoRA | 76.71 | 37.85 | 29.29 | 32.53 | 37.95 | 44.90 |
| + MemGen | 39.37 | 5.36 | 38.89 | 29.61 | 32.93 | 30.66 |
| + MLP Memory | 24.95 | 10.94 | 22.73 | 28.80 | 32.87 | 22.85 |
| **+ δ-Mem (SSW)** | **81.70** | **49.22** | **41.41** | **37.84** | **47.05** | **51.44** |
| **+ δ-Mem (TSW)** | **82.99** | **49.41** | **40.40** | **36.48** | **46.53** | **51.66** |
| **+ δ-Mem (MSW)** | **81.52** | **46.86** | **37.37** | **38.85** | **49.12** | **50.74** |

**关键发现**：
- TSW 变体总平均 51.66%，比骨干提升 +4.87 分，比最强基线 Context2LoRA 提升 +6.76 分
- 在记忆密集型任务上提升更大：MemoryAgentBench **1.31×**，LoCoMo **1.20×**
- TTL（Test-time Learning）子任务从 26.14 提升到 **50.50**，接近翻倍
- 通用能力（IFEval、GPQA-D）基本保持不降

### 跨骨干模型验证

| 骨干 | 无记忆平均 | + δ-Mem 最佳 | 提升 | 最佳策略 |
|------|-----------|-------------|------|----------|
| Qwen3-4B-Instruct | 46.79% | 51.66% | +4.87 | TSW |
| Qwen3-8B | 47.20% | 50.86% | +3.66 | SSW |
| SmolLM3-3B | 26.08% | 36.96% | +10.88 | MSW |

**规律**：
- **小模型（3B）**：MSW 效果最好（+10.88），多状态分离减少了信息干扰
- **大模型（8B）**：SSW 效果最好，段级写入平滑了噪声
- **中等模型（4B）**：TSW 最优，token 级粒度捕捉到了足够的细节

### 消融实验

#### 上下文恢复（Context Recovery）

在完全移除历史上下文、仅注入压缩记忆状态的极端设置下：
- HotpotQA Overall EM：0.08% → **6.48%**（F1: 8.27% → 15.20%）
- LoCoMo Overall：3.49% → **8.05%**
- 证明即使没有显式上下文，8×8 的记忆状态仍能恢复有用的历史信息

#### 注意力头注入位置（Head Ablation）

| 注入位置 | 平均分 |
|----------|--------|
| 仅 q | 44.51 |
| 仅 o | 47.05 |
| qo（默认） | **47.97** |
| qkvo（全注入） | 48.05 |

- qo 已足够强劲，qkvo 的边际增益不值得额外参数开销
- output 侧单独注入优于其他单分支

#### 插入深度（Layer Depth）

| 深度 | 平均分 |
|------|--------|
| 前 12 层 | 44.39 |
| 中 12 层 | 46.66 |
| 后 12 层 | 44.06 |
| 全部层 | **47.97** |

- 全层注入最优
- 中间层是部分注入的最佳选择（平衡语义抽象和任务特定计算）

### 效率分析

| 指标 | δ-Mem (TSW) | Context2LoRA | MemGen | MLP Memory |
|------|-------------|-------------|--------|------------|
| 可训练参数 | **4.87M (0.12%)** | 5.90M (0.15%) | 46.20M (1.13%) | 3078M (76.40%) |
| GPU 显存 | ≈ Vanilla | ≈ Vanilla | 高 | 极高 |
| 解码速度 | 略慢于 Vanilla | ≈ Vanilla | 最慢 | 较慢 |

## 提及的实体

- [[Jingdi-Lei]] — 共同一作，南洋理工大学，通讯作者
- [[Di-Zhang]] — 共同一作，复旦大学
- [[Soujanya-Poria]] — 通讯作者，南洋理工大学
- [[Mind-Lab]] — 核心研究团队
- [[Qwen3]] — 骨干模型（Qwen3-4B-Instruct、Qwen3-8B）
- [[SmolLM3]] — 小规模骨干模型（3B）

## 讨论的概念

- [[δ-mem-在线关联记忆]] — 本论文提出的记忆机制
- [[delta-rule-learning]] — 状态更新的核心学习规则
- [[低秩注意力修正]] — 通过低秩矩阵动态修正注意力计算
- [[LLM记忆机制分类]] — TMM/OMM/PMM 三类范式
- [[Context-Rot]] — 上下文退化/腐烂现象

## 优点与局限

### 优点

1. **极致紧凑**：8×8 状态矩阵（仅 4.87M 可训练参数，0.12%）即可实现有效记忆
2. **骨干冻结**：不需要修改或替换骨干网络，兼容任意全注意力 Transformer
3. **在线演化**：状态随序列动态更新，而非训练后固定
4. **通用保持**：在增强记忆的同时基本不损害通用能力
5. **与注意力深度耦合**：记忆直接参与前向计算，而非通过外部检索路径

### 局限与开放问题

1. **状态容量有限**：8×8 矩阵的容量有上限，超长历史如何处理？
2. **训练数据依赖**：仅在 QASPER 的 2,219 样本上微调一个 epoch，泛化性有待进一步验证
3. **写入策略选择**：TSW/SSW/MSW 的最优选择依赖骨干模型大小，缺乏统一的自动选择机制
4. **仅实验了 SFT 训练**：是否可以与 RLHF/DPO 等对齐方法结合？
5. **与长上下文窗口的互补性**：论文没有探索 δ-mem 与长上下文窗口的联合使用效果

## 原始笔记

### 论文的方法-直觉映射

理解 δ-mem 的一个好类比是"**带有遗忘机制的快速缓存**"：
- 就像 CPU 的 L1 缓存不需要存储所有内存数据一样，δ-mem 不需要存储所有历史 token
- 它存储的是"**关联**"（key→value 的映射），而非原始文本
- Delta-rule 本质上是"**预测误差驱动的学习**"：已经记住的不重复存储，只有预测错误的部分才写入
- 遗忘门（λ）类似于缓存替换策略，控制哪些旧信息需要淘汰

### 与 MCP/LSP 的关联思考

δ-mem 解决的是 LLM 内部的"记忆"问题，而 [[Model-Context-Protocol-MCP|MCP]] 解决的是 LLM 与外部世界的"交互"问题。两者互补：
- δ-mem：LLM 如何在内部压缩和复用历史信息
- MCP：LLM 如何获取外部工具和数据
- 如果 Agent 同时需要内部记忆和外部工具，δ-mem + MCP 可能是一个强大的组合

### 数学优雅性

Delta-rule update 的形式 $S_t = \lambda_t S_{t-1} + \beta_t(v_t - S_{t-1}k_t)k_t^\top$ 非常优雅：
- 当 $S_{t-1}k_t \approx v_t$ 时（已记住），更新趋近于零
- 当 $S_{t-1}k_t \neq v_t$ 时（预测错误），更新量正比于误差
- 这本质上是在线 SGD 一步，优化的是 $\|Sk_t - v_t\|^2$

## 关联

- 与 [[Context2LoRA]] 的对比：都是低秩修正，但 δ-mem 是动态的，Context2LoRA 是静态的
- 与 [[Memorizing-Transformers]] 的对比：都用外部记忆，但 δ-mem 用固定大小状态，而非无限增长的 kNN 存储
- 与 [[Titans]] 的对比：都关注测试时记忆，但 δ-mem 不替换骨干，而是附加在冻结骨干上
- 与 [[mem0-building-production-ready-ai-agents|Mem0]] 的对比：δ-mem 是参数级内部记忆（8×8 状态矩阵），Mem0 是文本级外部记忆（向量检索+图结构）；两者互补——δ-mem 解决"怎么记"，Mem0 解决"存什么"和"怎么找"
- [[Context-Rot]] 解释了为什么简单扩展上下文窗口不够
- [[LLMs-Get-Lost-in-Multi-turn]] 说明了多轮对话中记忆退化的现象

---

## 推荐参考文献

以下按兴趣分类，整理自论文参考文献中的有趣工作：

### 🔥 强烈推荐

| #   | 论文                                                                                       | 推荐理由                                                    |
| --- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | **Titans: Learning to Memorize at Test Time** (Behrouz et al., 2024)                     | δ-mem 的核心灵感来源之一。提出在测试时让模型学习记忆，思路前瞻。探讨了如何将记忆作为模型架构的一等公民。 |
| 2   | **Context Rot: How Increasing Input Tokens Impacts LLM Performance** (Hong et al., 2025) | 解释了"上下文腐烂"现象——简单增加上下文长度不仅不帮记忆，反而损害性能。δ-mem 的核心动机来源。     |
| 3   | **LLMs Get Lost in Multi-turn Conversation** (Laban et al., 2025)                        | 揭示了 LLM 在多轮对话中系统性"迷失"的问题，量化了性能退化。理解为什么需要记忆机制。           |
| 4   | **Memorizing Transformers** (Wu et al., 2022)                                            | 开创性的外部记忆工作，用 kNN 检索过去的 KV 对。与 δ-mem 的"固定状态"方案形成鲜明对比。    |

### 📚 值得一读

| #   | 论文                                                                                                   | 推荐理由                                                               |
| --- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 5   | **MemGPT: Towards LLMs as Operating Systems** (Packer et al., 2023)                                  | 将 LLM 类比操作系统的记忆管理（虚拟内存、分页），思路新颖。文本记忆方法的代表。                         |
| 6   | **Generative Agents: Interactive Simulacra of Human Behavior** (Park et al., 2023)                   | 斯坦福经典工作，模拟小镇中 25 个 AI Agent 的社会行为。其记忆系统（记忆流+反思+检索）是 Agent 记忆的典范设计。 |
| 7   | **LoRA: Low-rank Adaptation** (Hu et al., 2022)                                                      | δ-mem 的低秩修正接口直接借鉴 LoRA 的形式，但赋予了动态语义。理解 δ-mem 需要先理解 LoRA。           |
| 8   | **ROME & MEMIT** (Meng et al., 2022a,b)                                                              | 将模型参数视为可写入的记忆基底，通过局部权重编辑注入事实。参数化记忆的前沿探索。                           |
| 9   | **Kimi Linear: An Expressive, Efficient Attention Architecture** (Team et al., 2025)                 | 线性注意力架构的最新进展，δ-mem 的遗忘门设计受其启发。                                     |
| 10  | **Mem0: Building Production-ready AI Agents with Scalable Long-term Memory** (Chhikara et al., 2025) | 工业级的 Agent 记忆系统，从工程实践角度解决记忆问题，与 δ-mem 的学术角度互补。                     |

### 🎯 背景补充

| # | 论文 | 推荐理由 |
|---|------|----------|
| 11 | **ReAct: Synergizing Reasoning and Acting** (Yao et al., 2022) | Agent 系统的经典框架，推理+行动交替执行。δ-mem 的应用场景。 |
| 12 | **Reflexion: Language Agents with Verbal Reinforcement Learning** (Shinn et al., 2023) | Agent 通过语言反思来改进决策，记忆是反思的基础。 |
| 13 | **Qwen3 Technical Report** (Yang et al., 2025) | δ-mem 使用的骨干模型，了解模型能力有助于理解实验结果。 |
| 14 | **MemoryBank: Enhancing LLMs with Long-term Memory** (Zhong et al., 2024) | 文本记忆方法的代表，也是 δ-mem 的对比基线之一。 |
| 15 | **M+: Extending MemoryLLM with Scalable Long-term Memory** (Wang et al., 2025) | 持续扩展记忆的参数化方案，探索了记忆的另一种可扩展路径。 |
