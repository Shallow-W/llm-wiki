---
id: source-agent0
date: 2026-05-06
source: raw/papers/agent0-bootstrapping-from-zero-data.pdf
type: 论文
tags: [Agent, 强化学习, 自演化, 课程学习, 工具集成推理, GRPO, 零数据, 协同进化]
---

# Agent0: Unleashing Self-Evolving Agents from Zero Data via Tool-Integrated Reasoning

## 一句话总结

Agent0 提出了一种完全自主的双 Agent 协同进化框架：课程 Agent（Curriculum Agent）与执行 Agent（Executor Agent）从同一基座 LLM 初始化，通过多轮工具增强的共生竞争，在零人工数据条件下实现 Agent 能力的持续自举提升——Qwen3-8B-Base 在数学推理上提升 18%，通用推理提升 24%。

## 基本信息

| 项目 | 内容 |
|------|------|
| **标题** | Agent0: Unleashing Self-Evolving Agents from Zero Data via Tool-Integrated Reasoning |
| **作者** | Peng Xia, Kaide Zeng, Jiaqi Liu, Can Qin, Fang Wu, Yiyang Zhou, Caiming Xiong, Huaxiu Yao |
| **机构** | UNC-Chapel Hill, Salesforce Research, Stanford University |
| **日期** | 2025-11-20（arXiv v1） |
| **arXiv** | 2511.16043 |
| **代码** | https://github.com/aiming-lab/Agent0 |

## 研究背景与动机

### 现有方法的瓶颈

当前 LLM Agent 的训练严重依赖人工标注数据，无论是 RLHF 还是 RLVR（Reinforcement Learning from Verifiable Rewards），都需要大规模、高质量的人类策划数据集。这带来了三个根本性问题：

1. **可扩展性瓶颈**：数据收集耗时、耗力、耗财
2. **能力天花板**：AI 潜力被人类知识和标注速度所束缚
3. **知识停滞**：模型无法超越人类已知的知识边界

### 自演化方法的局限

现有自演化框架（如 R-Zero、Absolute Zero、SPIRAL）虽然摆脱了对人工数据的依赖，但面临两个关键限制：

| 限制 | 具体表现 | 后果 |
|------|---------|------|
| **能力上限** | 生成任务复杂度受限于模型固有知识 | 课程停滞（curriculum stagnation），任务很少超越当前复杂度 |
| **单轮交互** | 仅在单轮对话中操作 | 无法捕捉真实世界问题的动态、上下文依赖本质 |

这些限制不仅制约了自生成课程的复杂度，更关键的是阻碍了模型掌握需要复杂工具使用或多步推理的基本技能。

### Agent0 的核心洞察

**外部工具是打破能力天花板的关键杠杆。** 将代码解释器集成到进化循环中，执行 Agent 的问题解决能力得到增强，这反过来迫使课程 Agent 生成更复杂、更依赖工具的课程任务。工具使用与课程生成形成正反馈循环，驱动能力螺旋上升。

## 核心方法

### 总体架构：双 Agent 协同进化

Agent0 从同一基座 LLM $\pi_{\text{base}}$ 初始化两个功能不同的 Agent：

```
基座 LLM π_base
    ├──→ 课程 Agent π_θ（生成前沿任务）
    └──→ 执行 Agent π_φ（学习解决任务）

协同进化循环（迭代 t = 1, ..., T）：
    ┌─────────────────────────────────────────┐
    │  阶段1: 课程进化（训练 π_θ）              │
    │  · π_θ 生成任务池 X                     │
    │  · 对每个 x_i，π_φ 采样 k=10 个回答      │
    │  · 计算复合奖励 R_C（不确定性+工具使用）  │
    │  · 用 GRPO 更新 π_θ → π_θ^(t)          │
    └─────────────────────────────────────────┘
                    ↓ 冻结 π_θ^(t)
    ┌─────────────────────────────────────────┐
    │  阶段2: 执行进化（训练 π_φ）              │
    │  · π_θ^(t) 生成大量候选任务 X_pool       │
    │  · 过滤：保留自洽度 0.3 ≤ p̂(x) ≤ 0.8    │
    │  · 构建挑战性数据集 D^(t)                │
    │  · 用 ADPO 训练 π_φ → π_φ^(t)          │
    └─────────────────────────────────────────┘
                    ↓ π_φ^(t) 能力增强
                    └────────→ 下一轮迭代
```

### 符号表

| 符号 | 含义 | 说明 |
|------|------|------|
| $\pi_{\text{base}}$ | 基座 LLM | 初始化两个 Agent 的共享起点 |
| $\pi_\theta$ | 课程 Agent | 参数 $\theta$，专门生成挑战性任务 |
| $\pi_\phi$ | 执行 Agent | 参数 $\phi$，学习解决生成的任务 |
| $x$ | 任务提示 | 课程 Agent 生成的数学问题 |
| $y$ | 模型回答 | 执行 Agent 的完整输出 |
| $k$ | 采样数 | 每个任务采样 $k=10$ 个回答计算自洽度 |
| $\hat{p}(x; \pi_\phi)$ | 自洽度分数 | 投票给多数答案的比例，作为不确定性代理 |
| $\tilde{y}$ | 伪标签 | 多数投票确定的答案，作为训练目标 |
| $\delta$ | 过滤阈值 | 控制课程难度，默认 $\delta = 0.25$ |
| $N_{\text{tool}}(y)$ | 工具调用次数 | 回答中 ` ```output ` 标记的计数 |
| $G$ | GRPO 组大小 | 每个提示采样的回答数 |
| $\epsilon_{\text{norm}}$ | 归一化常数 | 数值稳定性小常数 |

### 3.2 课程 Agent 训练（Curriculum Agent Training）

课程 Agent $\pi_\theta$ 的目标是学习生成"恰到好处地挑战"当前执行 Agent 的任务。其优化目标是通过 GRPO 最大化复合奖励 $R_C$。

#### 不确定性奖励 $R_{\text{unc}}$

核心直觉：最难学习的任务是执行 Agent 最"困惑"的任务——既不太简单（所有人都能答对），也不太难（所有人都答错）。

$$R_{\text{unc}}(x; \pi_\phi) = 1 - 2 \left| \hat{p}(x; \pi_\phi) - 0.5 \right|$$

其中 $\hat{p}(x; \pi_\phi)$ 是执行 Agent 对任务 $x$ 的自洽度（majority vote 比例）。该函数在 $\hat{p} = 0.5$ 时取最大值 1，在 $\hat{p} \to 1$（太简单）或 $\hat{p} \to 0$（太难）时趋于 0。

#### 工具使用奖励 $R_{\text{tool}}$

这是驱动"良性循环"的关键机制。显式奖励促使执行 Agent 使用工具的任务：

$$R_{\text{tool}}(x; \pi_\phi) = \gamma \cdot \min(N_{\text{tool}}(y), C)$$

其中 $N_{\text{tool}}(y)$ 是回答 $y$ 中工具响应标记（` ```output `）的计数，$\gamma$ 是缩放超参数，$C$ 是上限防止过度奖励虚假工具使用。

#### 重复惩罚 $R_{\text{rep}}$

鼓励批次内多样性，防止课程 Agent 生成重复或相似的任务：

$$R_{\text{rep}}(x_i) = \lambda_{\text{rep}} \frac{|C_k|}{B}$$

其中 $C_k$ 是任务 $x_i$ 所属的聚类（基于 BLEU 相似度 $d_{ij} = 1 - \text{BLEU}(x_i, x_j)$，阈值 $\tau_{\text{BLEU}}$），$B$ 是批次大小。

#### 复合奖励

$$R_C(x_i) = R_{\text{format}}(x_i) \cdot \max\left(0, \left(\lambda_{\text{unc}} R_{\text{unc}} + \lambda_{\text{tool}} R_{\text{tool}}\right) - R_{\text{rep}}(x_i)\right)$$

$R_{\text{format}}$ 是格式检查门控（确保输出符合预期格式）。

### 3.3 执行 Agent 训练（Executor Agent Training）

#### 挑战性数据集构建

冻结训练后的课程 Agent $\pi_\theta^{(t)}$，生成大量候选任务 $X_{\text{pool}}$。对每个任务，当前执行 Agent $\pi_\phi^{(t-1)}$ 采样 $k$ 个回答，计算自洽度：

$$\hat{p}(x) = \frac{1}{k} \sum_{i=1}^{k} \mathbb{I}(o_i = \tilde{y}), \quad \tilde{y} = \arg\max_y \sum_{i=1}^{k} \mathbb{I}(o_i = y)$$

过滤保留"能力前沿"任务：

$$\mathcal{D}^{(t)} = \left\{ x \in X_{\text{pool}} \mid \left| \hat{p}(x; \pi_\phi^{(t-1)}) - 0.5 \right| \leq \delta \right\}$$

默认 $\delta = 0.25$，即保留自洽度在 $[0.25, 0.75]$ 之间的任务。

#### 多轮工具集成 Rollout

取代标准单轮生成，采用多步工具集成 rollout：

1. 策略 $\pi_\phi$ 先生成文本推理 $t_1$
2. 当策略发出工具调用触发器（` ```python...``` `）时，暂停生成
3. 代码 $c_1$ 在沙箱中执行，返回结果或错误 $f_1$
4. 执行结果（前缀 ` ```output...``` `）反馈给策略
5. 策略基于历史 $[t_1 \oplus c_1 \oplus f_1 \oplus \dots]$ 继续生成
6. 重复直到生成最终答案 $o$（在 `\boxed{}` 中）

这种动态、交错反馈机制允许 Agent 迭代修正推理和纠正错误，模拟"顿悟时刻"的自我修正。

#### 伪标签优势（Pseudo-Label Advantage）

生成 $k$ 条完整轨迹后，使用多数答案 $\tilde{y}$ 作为伪标签。每条轨迹的终端奖励：

$$R_i = \mathbb{I}(o_i = \tilde{y})$$

该结果奖励用于计算整条多步轨迹的优势 $A_i$。

### 3.3.2 ADPO：模糊感知动态策略优化

标准 GRPO 将所有训练样本同等对待，但在自演化设置中存在两个关键问题：

**问题1：标签噪声。** 高模糊度任务（低 $\hat{p}(x)$）的多数答案容易出错，直接优化会强化错误推理。

**解决方案：模糊感知优势缩放。** 定义缩放因子 $s(x) = f(\hat{p}(x))$，其中 $f$ 是自洽度的增函数。修改后的优势：

$$\tilde{A}_i(x) = \hat{A}_i \cdot s(x)$$

这成比例地降低来自不可靠、低自洽度样本的训练信号。

**问题2：静态裁剪限制探索。** 标准 PPO/GRPO 的静态裁剪 $\epsilon$ 对低概率 token 的增长施加了不对称障碍。实证分析（Figure 3）显示，上裁剪界主要由低概率 token 触发，这抑制了新推理路径的出现——对高模糊度任务尤其有害，因为正确答案往往位于当前策略分布的尾部。

**解决方案：模糊调制信任区域。** 定义动态上裁剪界 $\epsilon_{\text{high}}(x)$ 为 $\hat{p}(x)$ 的减函数：

$$\epsilon_{\text{high}}(x) \propto \frac{1}{\hat{p}(x)}$$

对模糊输入放松约束，允许更大的梯度步长提升潜在低概率解；对自信样本保持紧约束以维持稳定性。

#### ADPO 目标函数

$$\mathcal{L}_{\text{ADPO}}(\theta) = \mathbb{E}_{x \sim \mathcal{D}^{(t)}} \left[ -\frac{1}{G} \sum_{i=1}^{G} \min\left( r_i(\theta) \tilde{A}_i(x), \text{clip}\left(r_i(\theta), 1 - \epsilon_{\text{low}}, 1 + \epsilon_{\text{high}}(x)\right) \tilde{A}_i(x) \right) \right]$$

其中 $r_i(\theta) = \frac{\pi_\theta(x_i)}{\pi_{\text{old}}(x_i)}$ 是重要性采样比率，$\tilde{A}_i(x)$ 是模糊缩放优势，$\epsilon_{\text{high}}(x)$ 是与 $\hat{p}(x)$ 成反比的动态上界。

### 完整算法（Algorithm 1）

```
Require: 基座 LLM π_base; 迭代次数 T; 采样数 k
1: 初始化 π_θ^(0) ← π_base, π_φ^(0) ← π_base
2: for t = 1, ..., T do
3:   ▷ 课程进化（训练 π_θ）
4:   初始化 π_θ ← π_θ^(t-1)
5:   生成任务批次 X = {x_i} ~ π_θ
6:   for x_i ∈ X do
7:     采样 k 个回答 {y_j}_{j=1}^k ~ π_φ^(t-1)(x_i)
8:     用公式 (5) 计算 R_C(x_i)
9:   end for
10:  用 L_GRPO 和 (X, R_C) 更新 π_θ → π_θ^(t)
11:  ▷ 执行进化（训练 π_φ）
12:  生成 X_pool ~ π_θ^(t)，过滤得 D^(t) = {(x, p̂, ỹ)}，其中 |p̂(x) - 0.5| ≤ δ
13:  初始化 π_φ ← π_φ^(t-1)
14:  for 批次 B_D = {(x, p̂(x), ỹ)} ~ D^(t) do
15:    初始化 T_batch, Ã_batch, P_batch
16:    for (x, p̂(x), ỹ) ∈ B_D do
17:      采样 k 条轨迹 {τ_i}_{i=1}^k ~ π_φ(x)
18:      计算奖励 R_i = I(o_i = ỹ)
19:      计算缩放优势 Ã_i ← A_i · f(p̂(x))
20:      将 {τ_i} 加入 T_batch，{Ã_i} 加入 Ã_batch，p̂(x) 加入 P_batch
21:    end for
22:    用 L_ADPO（公式 8）在收集的批次上更新 π_φ
23:  end for
24:  π_φ^(t) ← π_φ
25: end for
```

## 实验结果

### 4.1 实验设置

- **基座模型**：Qwen3-4B-Base, Qwen3-8B-Base
- **框架**：基于 VeRL 实现
- **工具**：沙箱化 Python 代码解释器（VeRL-Tool）
- **超参数**：$k=10$，$\delta=0.25$，$\lambda_{\text{tool}}=0.6$，$C=4$

**评估基准**：
- **数学推理**：AMC, Minerva, MATH, GSM8K, Olympiad-Bench, AIME25, AIME24
- **通用推理**：SuperGPQA, MMLU-Pro, BBEH

**对比基线**：Base Model, Base Model w/ tool, Absolute Zero, SPIRAL, R-Zero, Socratic-Zero

### 4.2 主结果

#### 数学推理（Table 1）

| 模型 | 工具 | 多轮 | AVG | AMC | Minerva | MATH | GSM8K | Olympiad | AIME25 | AIME24 |
|------|------|------|-----|-----|---------|------|-------|----------|--------|--------|
| Qwen3-4B-Base | ✗ | ✗ | 42.6 | 45.7 | 38.2 | 68.2 | 87.8 | 41.0 | 6.15 | 10.9 |
| + Base w/ tool | ✓ | ✗ | 44.2 | 46.3 | 39.6 | 71.0 | 88.6 | 43.7 | 7.71 | 12.3 |
| + Absolute Zero | ✓ | ✗ | 46.4 | 50.0 | 41.9 | 76.2 | 89.3 | 41.5 | 13.4 | 12.2 |
| + SPIRAL | ✗ | ✗ | 47.0 | 57.5 | 42.4 | 76.4 | 91.0 | 38.4 | 10.0 | 13.3 |
| + R-Zero | ✗ | ✗ | 49.1 | 57.3 | 52.9 | 79.6 | 92.1 | 44.6 | 4.27 | 12.7 |
| **+ Agent0** | **✓** | **✗** | **52.5** | **60.6** | **55.6** | **80.5** | **92.6** | **46.7** | **14.1** | **17.4** |
| Qwen3-8B-Base | ✗ | ✗ | 49.2 | 52.0 | 50.0 | 78.0 | 89.1 | 44.7 | 16.7 | 13.9 |
| + Base w/ tool | ✓ | ✗ | 53.2 | 60.3 | 54.9 | 79.2 | 90.7 | 47.9 | 18.7 | 20.9 |
| + Absolute Zero | ✓ | ✗ | 52.6 | 62.5 | 52.9 | 76.6 | 92.0 | 47.8 | 18.2 | 18.4 |
| + R-Zero | ✗ | ✗ | 54.7 | 61.7 | 60.7 | 82.0 | 94.1 | 48.9 | 19.2 | 16.4 |
| + Socratic-Zero | ✗ | ✓ | 56.1 | 63.7 | 52.4 | 81.2 | 87.3 | 55.1 | 24.5 | 28.4 |
| **+ Agent0** | **✓** | **✗** | **58.2** | **62.4** | **61.3** | **82.4** | **94.5** | **54.0** | **24.8** | **28.0** |

**关键发现**：
- Qwen3-8B 上，Agent0 超越 R-Zero（无工具）6.4%，超越 Absolute Zero（有工具验证）10.6%
- 甚至超过依赖外部 OpenAI API 的 Socratic-Zero 3.7%
- Qwen3-4B 上平均提升 9.9 个百分点（相对提升 23.2%）

#### 通用域推理（Table 2）

| 模型 | 工具 | 多轮 | Overall AVG | MATH AVG | SuperGPQA | MMLU-Pro | BBEH |
|------|------|------|-------------|----------|-----------|----------|------|
| Qwen3-4B-Base | ✗ | ✗ | 27.1 | 42.6 | 20.9 | 37.4 | 7.57 |
| + Agent0 | ✓ | ✗ | **37.6** | **52.5** | **29.9** | **55.9** | **12.0** |
| Qwen3-8B-Base | ✗ | ✗ | 34.5 | 49.2 | 28.3 | 51.8 | 8.6 |
| + Agent0 | ✓ | ✗ | **42.1** | **58.2** | **33.0** | **63.4** | **13.7** |

通用域上同样取得最高平均分，证明数学推理中培养的复杂多步推理能力可有效迁移。

## 消融实验

### 组件消融（Table 3，Qwen3-8B）

| 方法 | General AVG | Math AVG |
|------|------------|----------|
| Agent0（完整） | 36.7 | 58.2 |
| Curriculum w/o Training | 29.5 | 46.8 |
| Curriculum w/o Tool Reward | 31.8 | 48.7 |
| Curriculum w/o Repetition Penalty | 31.3 | 47.9 |
| Executor w/o ADPO | 34.9 | 56.2 |
| Executor w/o Multi-turn | 35.3 | 55.9 |

**关键结论**：
- 课程 Agent 训练至关重要：移除训练导致 General -7.2%，Math -11.4%
- 工具奖励 $R_{\text{tool}}$ 是核心假设：移除后 General -4.9%，Math -9.5%
- 重复惩罚 $R_{\text{rep}}$ 对多样性至关重要：移除后 General -5.4%，Math -10.3%
- ADPO 有效应对伪标签噪声：移除后 General -1.8%，Math -2.0%
- 多轮推理对复杂数学推理贡献显著：移除后 General -1.4%，Math -2.3%

### 协同进化的迭代提升（Figure 4）

Qwen3-8B-Base 在 3 次迭代中的数学平均分：55.1（Iter 1）→ 56.5（Iter 2）→ 58.2（Iter 3）。通用域每轮迭代平均提升约 2%。

### 任务难度与工具使用的进化（Table 5）

用 Iteration 1 的固定执行 Agent 评估不同迭代生成的任务：

| 数据集 | 通过率（Executor_Iter1） | 平均工具调用次数 |
|--------|------------------------|----------------|
| D_Iter 1 | 64.0% | 1.65 |
| D_Iter 2 | 58.5% | 2.10 |
| D_Iter 3 | 51.0% | 2.60 |

直接证明：课程 Agent 生成的任务难度逐步增加，工具依赖度稳步上升，$R_{\text{tool}}$ 奖励成功驱动了良性循环。

### 交互轮数消融（Appendix Table 9）

| 轮数 | Overall AVG | Math AVG | General AVG |
|------|------------|----------|-------------|
| 1 | 35.5 | 50.4 | 30.8 |
| 2 | 35.8 | 50.7 | 31.1 |
| 3 | 36.1 | 51.2 | 31.3 |
| 4 | 36.7 | 51.9 | 31.6 |

从单轮到 4 轮，Overall 提升 3.4%，Math 提升 3.0%，General 提升 2.6%。多轮交互促使课程 Agent 生成更长上下文依赖和渐进难度的任务。

### 工具集成策略对比（Table 4，Qwen3-4B）

| 模型 | MATH | General |
|------|------|---------|
| w/o Tool + SPIRAL | 47.0 | 30.0 |
| w/o Tool + R-Zero | 49.1 | 29.8 |
| w/ Tool + TIR | 44.2 | 25.7 |
| w/ Tool + Absolute Zero | 46.4 | 29.3 |
| **w/ Tool + Agent0** | **52.5** | **32.6** |

Agent0 的优势不仅在于"有工具"，更在于"学会如何使用工具"。课程 Agent 通过 $R_{\text{tool}}$ 显式激励生成需要工具使用的复杂任务，远胜于仅用工具验证的方法（Absolute Zero）或完全不使用工具的方法（R-Zero）。

## 优点与局限

### 优点

1. **完全零数据**：不依赖任何人工标注或外部数据集，彻底摆脱人类知识边界限制
2. **工具驱动的能力突破**：通过代码解释器引入客观问题解决能力，打破模型固有知识天花板
3. **协同进化正反馈**：课程 Agent 与执行 Agent 形成共生竞争，任务复杂度与解决能力同步螺旋上升
4. **ADPO 的创新**：模糊感知优势缩放 + 动态信任区域，有效应对自演化中的伪标签噪声和探索限制
5. **模型无关性**：在 Qwen3-4B 和 Qwen3-8B 上均取得显著提升，证明框架的通用性
6. **强泛化性**：数学推理训练带来的能力可迁移到通用域推理任务

### 局限

1. **评估域有限**：仅在数学和通用推理基准上验证，未在代码生成、具身智能、创意写作等更广泛的 Agent 任务上测试
2. **工具单一**：仅使用 Python 代码解释器，未探索搜索引擎、API 调用、多模态工具等更丰富的工具生态
3. **迭代次数有限**：仅展示 3 次迭代结果，长期进化（10+ 轮）的稳定性和收益递减情况未知
4. **伪标签质量瓶颈**：虽然 ADPO 缓解了问题，但多数投票伪标签在极难任务上仍可能不可靠
5. **计算成本**：双 Agent 协同训练需要大量计算资源（每轮需生成、评估、过滤大量任务）
6. **安全与对齐**：完全自主的 Agent 自演化可能产生未预期的行为模式，需要与价值对齐技术配合

## 提及的实体

- [[Peng-Xia]] — 第一作者，UNC-Chapel Hill
- [[Huaxiu-Yao]] — 通讯作者，UNC-Chapel Hill
- [[Caiming-Xiong]] — 作者，Salesforce Research
- [[UNC-Chapel-Hill]] — 第一作者机构
- [[Salesforce-Research]] — 合作机构
- [[Stanford-University]] — 合作机构
- [[Qwen]] — 基座模型族（Qwen3-4B/8B-Base）
- [[VeRL]] — 实现框架
- [[OpenAI]] — Socratic-Zero 基线使用其 API

## 讨论的概念

- [[Agent 强化学习（Agent RL）]] — Agent0 的双 Agent 训练基于 RL 范式
- [[GRPO]] — 课程 Agent 的标准策略优化算法
- [[POMDP]] — 多轮 Agent-环境交互的理论框架
- [[经验驱动自演化（Experience-Driven Self-Evolution）]] — 与 EvolveR 的对比：Agent0 是双 Agent 协同进化，EvolveR 是单 Agent 经验闭环
- [[自蒸馏（Agent策略自蒸馏）]] — Agent0 使用多数投票伪标签，EvolveR 使用原则自蒸馏
- [[课程学习（Curriculum Learning）]] — Agent0 的核心机制：课程 Agent 自动生成自适应课程
- [[工具集成推理（Tool-Integrated Reasoning, TIR）]] — Agent0 将代码解释器融入训练和推理
- [[协同进化（Co-Evolution）]] — 课程 Agent 与执行 Agent 的共生竞争关系
- [[ADPO（Ambiguity-Dynamic Policy Optimization）]] — 本文提出的模糊感知动态策略优化
- [[零数据自举（Zero-Data Bootstrapping）]] — 完全摆脱人工数据的学习范式

## 推荐参考文献

1. **R-Zero** (Huang et al., 2025) — 直接竞争者，同样零数据自演化但无工具。arXiv: 2508.05004
2. **Absolute Zero** (Zhao et al., 2025) — 使用代码执行器验证的自演化方法，工具仅用于验证而非课程生成。arXiv: 2505.03335
3. **SPIRAL** (Liu et al., 2025a) — 基于零和博弈的自演化，无工具。arXiv: 2506.24119
4. **Socratic-Zero** (Wang et al., 2025d) — 依赖外部 OpenAI API 的协同进化方法。arXiv: 2509.24726
5. **EvolveR** (Wu et al., 2025b) — 单 Agent 经验驱动自演化，与 Agent0 的双 Agent 范式形成对比。arXiv: 2510.16079
6. **DeepSeekMath** (Shao et al., 2024) — GRPO 的原始提出者。arXiv: 2402.03300
7. **Search-R1** (Jin et al., 2025) — 工具增强的 RL 训练 Agent 搜索能力。arXiv: 2503.09516
8. **SimpleTIR** (Xue et al., 2025) — 多轮工具集成推理的端到端 RL。arXiv: 2509.02479
9. **ASPO** (Lin & Xu, 2025) — 工具集成推理的理论保证。arXiv: 2508.19201
10. **Self-Challenging Agents** (Zhou et al., 2025a) — 自挑战语言模型 Agent。arXiv: 2506.01716

## 关联

- [[Agent RL]] — Agent0 是 Agent RL 在零数据场景下的重要进展
- [[GRPO]] — 课程 Agent 使用标准 GRPO，执行 Agent 使用改进的 ADPO
- [[POMDP]] — 多轮工具交互可形式化为 POMDP
- [[经验驱动自演化（Experience-Driven Self-Evolution）]] — 与 EvolveR 对比：Agent0 是双 Agent 协同进化，EvolveR 是单 Agent 经验闭环
- [[evolver-from-trajectories-to-principles|EvolveR]] — 同为自演化框架，但范式不同
- [[自蒸馏（Agent策略自蒸馏）]] — Agent0 使用多数投票伪标签作为自监督信号
- [[课程学习（Curriculum Learning）]] — Agent0 的课程 Agent 自动生成自适应课程
- [[工具集成推理（Tool-Integrated Reasoning, TIR）]] — Agent0 的核心技术组件
- [[ADPO（Ambiguity-Dynamic Policy Optimization）]] — 本文提出的新算法
- [[零数据自举（Zero-Data Bootstrapping）]] — Agent0 的核心贡献
