---
id: source-agentic-harness-engineering
date: 2026-05-21
source: raw/papers/agentic-harness-engineering-observability-driven-automatic-evolution.pdf
url: https://arxiv.org/abs/2604.25850
type: 论文
authors: [Jiahang Lin, Shichun Liu, Chengjun Pan, Zhenhua Han, Tao Gui]
venue: arXiv preprint, 2025
tags: [Agent, 精读, 自动演化, 编码Agent, 可观测性, 系统工程]
---

# Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses

## 一句话总结

提出 AHE 框架，通过三种可观测性（组件/经验/决策）驱动编码 Agent 的 harness 自动闭环演化，在 Terminal-Bench 2 上 10 轮迭代从最小种子提升 7.3 个百分点，并具备跨模型/跨基准的迁移能力。

## 基本信息

- **作者**：Jiahang Lin¹, Shichun Liu¹, Chengjun Pan¹², Zhenhua Han¹², Tao Gui¹²
- **机构**：¹ 复旦大学自然语言处理实验室, ² 上海期智智峰科技有限公司
- **发表**：arXiv preprint, 2025
- **链接**：[arXiv 2604.25850](https://arxiv.org/abs/2604.25850)

## 问题与动机

编码 Agent（如 Claude Code、Codex CLI、Cursor）的性能不仅取决于底层 LLM，还强烈依赖于 **harness**——模型外部的可编辑组件集合（系统提示、工具、中间件、技能、子 Agent 配置、长期记忆）。然而：

1. **Harness 设计以人工为主**：当前编码 Agent 的 harness 几乎完全依赖人类专家手工调试，效率低且难以迁移。
2. **缺乏自动优化机制**：与 LLM 本身的训练（RLHF、SFT）形成鲜明对比，harness 侧缺乏系统化的自动改进闭环。
3. **缺乏可观测性**：现有框架将 harness 组件硬编码在代码中，无法被 Agent 自身观察、编辑、评估——这是自动化的前提。

AHE 的核心洞察：**如果 harness 的结构对演化 Agent 本身可观测，Agent 就能像工程师一样迭代优化自己的工具环境**。

## 核心方法

### 总体架构

AHE 是一个闭环演化框架，由三个可观测性支柱支撑：

```
┌─────────────────────────────────────────────────────┐
│                 AHE Outer Loop                       │
│                                                      │
│  ① Rollout: 在 benchmark 上运行当前 harness         │
│  ② Clean: 回滚 workspace，收集轨迹                   │
│  ③ Attribute: 验证上一轮 manifest 的预测              │
│  ④ Distill: Agent Debugger 生成根因分析              │
│  ⑤ Evolve: Evolve Agent 做证据驱动的编辑 + manifest  │
│  ⑥ Commit: git 提交所有变更                          │
└─────────────────────────────────────────────────────┘
```

### 三种可观测性

#### 1. 组件可观测性（Component Observability）

通过 [[NexAU-Framework|NexAU]] 框架将 harness 解耦为 **7 种正交组件类型**，每种以文件形式暴露在固定挂载点：

| 组件类型 | 说明 | 文件挂载点 |
| --- | --- | --- |
| System Prompt | 编码 Agent 的指令模板 | `config/prompt.md` |
| Tools | Agent 可调用的外部工具定义 | `tools/*.md` |
| Middleware | 请求/响应的预处理逻辑 | `middleware/*.md` |
| Skills | 注入特定能力的知识模块 | `skills/*.md` |
| Sub-agent Configs | 子 Agent 的配置文件 | `subagents/*.md` |
| Long-term Memory | 跨任务的持久记忆 | `memory/*.md` |
| Workflow | 编排逻辑 | `workflow/*.md` |

关键设计：每个组件就是一个文件，**编辑 harness = 编辑文件**。这带来了天然的 diff/rollback 能力（通过 git）和清晰的动作空间。

#### 2. 经验可观测性（Experience Observability）

**Agent Debugger** 是一个特殊的 Agent，它将海量原始轨迹（数百万 token）蒸馏为分层的、可下钻的证据语料：

- **任务级分析**：对每个失败任务，定位根因（工具缺失？提示不足？中间件 bug？）
- **基准级概览**：识别系统性模式（如"所有 shell 任务都因超时失败"）
- **基于文件的导航**：Agent Debugger 将轨迹视为可探索的文件环境，产出结构化分析报告

这一步将原始数据压缩为演化 Agent 可以有效消费的证据。

#### 3. 决策可观测性（Decision Observability）

**Change Manifest** 要求演化 Agent 在每次编辑时声明预测：

- **预期修复**（Expected Fixes）："这个工具修改应该能修复任务 X, Y, Z"
- **风险回归**（At-Risk Regressions）："这个提示变更可能导致任务 A, B 退化"

下一轮 rollout 后，通过实际任务结果验证预测，形成 **可审计的因果链**：每次变更 → 声明的预期 → 实际结果 → 偏差分析。

### Algorithm 1: AHE 外层循环

```
Input: Seed harness H₀, Benchmark B, LLM backbone L
Output: Evolved harness H*

1: for i = 1, 2, ..., N do
2:   Rᵢ ← Rollout(Hᵢ₋₁, B, L)           // 运行 benchmark
3:   Tᵢ ← Clean(Rᵢ)                       // 清理、回滚 workspace
4:   Aᵢ ← Attribute(Mᵢ₋₁, Tᵢ)            // 验证上一轮 manifest
5:   Eᵢ ← AgentDebugger(Tᵢ, Aᵢ)          // 证据蒸馏
6:   (Hᵢ, Mᵢ) ← EvolveAgent(Hᵢ₋₁, Eᵢ)  // 证据驱动编辑 + manifest
7:   GitCommit(Hᵢ, Mᵢ)                   // 提交到 git
8: end for
9: return H_N
```

### 设计约束

AHE 演化 Agent 的两个关键约束：

1. **Workspace-only Controllability**：Agent 只能编辑 harness 组件文件，不能修改 benchmark、LLM 或环境。这确保了变更的可归因性。
2. **Prediction-paired Manifest**：每次编辑必须附带预测声明，不鼓励"盲改"。

## 实验设置

- **主基准**：[[Terminal-Bench|Terminal-Bench 2]]（89 个终端任务：4 easy + 55 medium + 30 hard），每任务 1 小时超时
- **迁移基准**：SWE-bench-verified（500 个任务，跨 7 个仓库）
- **骨干模型**：Qwen-3.6-Plus（主实验）
- **对比方法**：
  - 人工设计：opencode, terminus-2, Codex-CLI
  - 自演化：ACE, TF-GRPO
- **种子 harness（NexAU0）**：刻意最小化——仅有单个 shell 执行工具，无中间件、无技能、无子 Agent
- **演化轮数**：10 轮（每轮包含完整的 rollout → distill → evolve 循环）
- **评估指标**：pass@1（任务通过率）

## 关键结果

### 主实验：Terminal-Bench 2 演化曲线

| Harness | Pass@1 | 相对基线 |
| --- | --- | --- |
| NexAU0（种子，迭代 0） | 27.0% | — |
| AHE（迭代 10） | 34.3% | **+7.3pp** |
| opencode（人工设计） | 27.0% | +0.0pp |
| terminus-2（人工设计） | 30.3% | +3.3pp |
| Codex-CLI（人工设计） | 32.6% | +5.6pp |
| ACE（自演化） | 30.3% | +3.3pp |
| TF-GRPO（自演化） | 29.2% | +2.2pp |

**核心发现**：AHE 从刻意最简化种子出发，10 轮后超越所有人工设计和自演化基线。

### 跨模型迁移

将 Qwen-3.6-Plus 上演化的 harness 直接迁移到其他模型：

| 模型 | 基线 | + AHE Harness | 提升 |
| --- | --- | --- | --- |
| deepseek-v4-flash | 24.7% | 34.8% | **+10.1pp** |
| qwen-3.6-plus | 27.0% | 34.3% | +7.3pp |
| gemini-3.1-flash-lite-preview | 19.1% | 24.2% | **+5.1pp** |

**发现**：越是不饱和的模型，harness 优化的边际收益越大（deepseek-v4-flash 提升最大）。

### 跨基准迁移

| 基准 | 基线 | + AHE Harness | 提升 |
| --- | --- | --- | --- |
| Terminal-Bench 2 | 27.0% | 34.3% | +7.3pp |
| SWE-bench-verified | 38.4% | 42.0% | **+3.6pp** |

AHE 在 Terminal-Bench 上演化的 harness 直接迁移到 SWE-bench 仍有 3.6pp 提升，说明演化学到的是通用编码策略而非过拟合特定任务。

### 组件消融

逐个移除演化产生的组件类型，观察影响：

| 消融条件 | Pass@1 | Δ vs 全 AHE |
| --- | --- | --- |
| 全 AHE | 34.3% | — |
| − Tools | 31.0% | −3.3pp |
| − Middleware | 32.1% | −2.2pp |
| − Long-term Memory | 28.7% | **−5.6pp** |
| − System Prompt | 36.6% | **+2.3pp**（回归！） |

关键洞察：

1. **长期记忆贡献最大**（−5.6pp），说明跨任务经验传递是核心。
2. **系统提示反向贡献**（+2.3pp），即演化出的系统提示反而有害——可能是过度拟合了训练分布或引入了与工具集冲突的指令。
3. **组件间非加性**：Tools（+3.3）+ Middleware（+2.2）+ LTM（+5.6）= +11.1pp，但全 AHE 只有 +7.3pp。冗余的重新验证（如工具和中间件都做安全检查）导致效率损失。

### 成本效率

| 方法 | 总推理 token | Pass@1 | 效率 |
| --- | --- | --- | --- |
| TF-GRPO | ~120M | 29.2% | 低（需要在线 RL 训练） |
| ACE | ~80M | 30.3% | 中（需要策略梯度） |
| AHE | ~50M | 34.3% | **高**（仅推理 + 文件编辑） |

AHE 不修改 LLM 权重，只需推理 + 文件编辑，成本远低于权重层面的自演化方法。

## 自归因分析

### 修复预测（Fix Predictions）

- **Precision**：33.7%（声明能修复的任务中，实际修复的比例）
- **Recall**：51.4%（实际修复的任务中，被正确预测的比例）
- 约为随机预测的 **5 倍**

### 回归预测（Regression Predictions）

- **Precision**：11.8%
- **Recall**：11.1%
- 仅约为随机的 **2 倍**

**洞察**：演化 Agent 对"什么会变好"有一定预测能力（证据驱动），但对"什么会变坏"的预测接近随机——这是 AHE 的主要风险来源。

## 消融 / 分析

### 案例研究

论文附录 C 提供了 4 个详细的演化轨迹案例：

1. **db-wal-recovery（迭代 2）**：Agent Debugger 发现种子 harness 缺少 SQLite WAL 模式知识 → Evolve Agent 在 skills/ 中注入 WAL 恢复技能文档 → 任务从失败转为成功。

2. **path-tracing（迭代 5）**：中间层 timeout 导致大型仓库的路径追踪超时 → Evolve Agent 添加增量式路径搜索中间件 → 修复。

3. **mcmc-sampling-stan（迭代 6）**：长期记忆中积累了"Stan 采样器需要 warmup 参数"的经验 → 新任务中 Agent 自动配置 warmup。

4. **configure-git-webserver（迭代 8）**：系统提示中的过度约束（"不要修改系统配置"）阻止了合法的 git webserver 配置 → Evolve Agent 放宽了约束条件。

### 演化过程中组件增长

| 迭代 | Tools | Middleware | Skills | LTM entries |
| --- | --- | --- | --- | --- |
| 0 | 1 | 0 | 0 | 0 |
| 2 | 2 | 1 | 1 | 3 |
| 5 | 3 | 2 | 3 | 8 |
| 10 | 4 | 3 | 5 | 15 |

组件数量随迭代稳步增长，但增速递减——演化 Agent 倾向于修改现有组件而非不断增加新组件。

## 局限性

- **单 benchmark 演化**：主实验仅在 Terminal-Bench 上演化，迁移到 SWE-bench 虽有提升但衰减明显。
- **固定骨干模型**：演化仅在 Qwen-3.6-Plus 上进行，对其他模型的迁移依赖跨模型迁移实验验证。
- **回归预测能力弱**：演化 Agent 无法可靠预测自己的变更会导致哪些任务退化。
- **组件交互的非加性**：单组件增益之和不等于全组件增益，提示组件间存在冗余和冲突。
- **系统提示的意外回归**：演化的系统提示反而有害，说明并非所有组件类型都适合自动化演化。
- **评估成本**：每轮需要完整的 benchmark rollout（89 任务 × 1 小时 = ~89 GPU 小时），10 轮总计 ~890 GPU 小时。

## 提及的实体

- [[Jiahang-Lin]] — 复旦大学，AHE 共同一作
- [[Shichun-Liu]] — 复旦大学，AHE 共同一作
- [[Chengjun-Pan]] — 复旦大学 & 上海期智智峰，AHE 共同作者
- [[Zhenhua-Han]] — 复旦大学 & 上海期智智峰，AHE 共同作者
- [[Tao-Gui]] — 复旦大学，AHE 通讯作者
- [[复旦大学]] — AHE 第一署名机构
- [[上海期智智峰]] — AHE 共同署名机构
- [[NexAU]] — AHE 提出的解耦 harness 框架
- [[Terminal-Bench]] — 主评估基准

## 讨论的概念

- [[Agentic-Harness-Engineering|Agentic Harness Engineering (AHE)]] — 本文核心方法
- [[Harness-Agent-Harness|Harness]] — 编码 Agent 的模型外部可编辑组件集合
- [[Component-Observability|组件可观测性]] — 7 种组件以文件形式暴露
- [[Experience-Observability|经验可观测性]] — Agent Debugger 蒸馏轨迹为证据
- [[Decision-Observability|决策可观测性]] — Change Manifest 配对预测
- [[NexAU-Framework|NexAU Framework]] — 解耦 harness 的具体实现框架
- [[Change-Manifest|Change Manifest]] — 编辑-预测配对的审计机制

## 关联

- **与 [[agent0-bootstrapping-from-zero-data|Agent0]]**：两者都是 Agent 自演化，但 Agent0 优化 LLM 权重（通过 RL），AHE 优化 harness 组件（通过文件编辑）。互补关系。
- **与 [[metaclaw-continuous-evolution-in-production|MetaClaw]]**：MetaClaw 在生产环境持续进化（技能库 + Cloud LoRA），AHE 在 benchmark 上离线演化。MetaClaw 的技能管理可借鉴 NexAU 的组件可观测性设计。
- **与 [[evolver-from-trajectories-to-principles|EvolveR]]**：EvolveR 从轨迹提取原则，AHE 的 Agent Debugger 从轨迹蒸馏根因分析——共享"经验→知识"的范式。
- **与 [[lora-low-rank-adaptation|LoRA]]**：LoRA 是权重层面的参数高效微调，AHE 是组件层面的结构高效优化——两个正交的优化维度。
- **与 [[Model Context Protocol (MSP)]]**：MCP 定义了工具接入标准，AHE 中的 NexAU 将工具定义为可编辑文件——两者都关注 Agent 工具生态，但层次不同。

## 个人笔记

AHE 的核心价值在于将"工程调参"从人力密集型任务转化为可自动化的闭环过程。三种可观测性的设计尤其精妙——它们分别解决了"改什么"（组件）、"为什么改"（经验）、"改了有什么效果"（决策）三个问题。

值得关注的设计选择：

1. **刻意最小化种子**（NexAU0）：这避免了人类先验知识的偏见，但也意味着演化起点低。实际部署中，从一个合理的人工 harness 开始可能会更快收敛。
2. **组件非加性**（+11.1pp vs +7.3pp）：这是系统工程中的经典问题——局部最优之和不等于全局最优。未来的工作需要考虑组件间的协调优化。
3. **系统提示的回归**（+2.3pp）：这是一个反直觉但重要的发现。可能原因是自然语言指令与精确的工具定义之间存在语义鸿沟。
4. **与权重优化的互补性**：AHE + LoRA/RL 的组合（先优化 harness 再优化权重，或交替进行）是一个有前景的方向。

AHE 框架的思想不限于编码 Agent——任何 Agent 系统（如研究 Agent、数据分析 Agent）都可以将"工具/提示/知识库"视为可演化的 harness。
