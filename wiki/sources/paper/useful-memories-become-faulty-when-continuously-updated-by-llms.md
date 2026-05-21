---
id: source-useful-memories-become-faulty-when-continuously-updated-by-llms
date: 2026-05-20
source: raw/papers/useful-memories-become-faulty-when-continuously-updated-by-llms.pdf
url: https://arxiv.org/abs/2605.12978
type: 论文
authors: [Dylan Zhang, Yanshan Lin, Zhengkun Wu, Yihang Sun, Bingxuan Li, Dianqi Li, Hao Peng]
venue: arXiv preprint (2026)
tags: [Agent记忆, 记忆整合, LLM, 记忆退化, 精读]
---

# Useful Memories Become Faulty When Continuously Updated by LLMs

## 一句话总结

LLM Agent 反复将经验轨迹整合（consolidate）为文本记忆时，记忆效用呈现先升后降的倒 U 型曲线——即使输入是 ground-truth 解法，GPT-5.4 也能在先前 100% 正确的 ARC-AGI 题目上丢失 47% 的准确率；保留原始 episode 远比强制抽象更有效。

## 基本信息

- **作者**：Dylan Zhang¹, Yanshan Lin², Zhengkun Wu², Yihang Sun¹, Bingxuan Li¹, Dianqi Li, Hao Peng¹
- **机构**：¹ UIUC (University of Illinois Urbana-Champaign), ² IIIS, Tsinghua University
- **发表**：arXiv:2605.12978v1, 2026-05-13
- **链接**：[arXiv](https://arxiv.org/abs/2605.12978) · [PDF](https://arxiv.org/pdf/2605.12978)
- **通讯作者**：Dylan Zhang (shizhuo2@illinois.edu)

## 问题与动机

**核心问题**：当前 LLM Agent 记忆系统（CLIN、AWM、Dynamic Cheatsheet、ACE 等）普遍采用"每次交互后强制整合"的设计范式——将原始轨迹压缩为文本经验存入记忆库，并持续更新。这种设计隐含一个未经验证的假设：**每次整合至少是无害的（at worst neutral）**。

**为什么重要**：
- Agent 记忆被视为通向自我进化 Agent 的实用路径（无需参数更新）
- 如果整合本身就是有害的，整个范式的可靠性就存疑
- 该问题在现有文献中缺乏系统性研究

## 核心方法

本文是 **诊断性/分析性** 工作，不提出新方法，而是系统性地揭示现有记忆整合方法中的失败模式。

**三种记忆构建条件**（仅区别于轨迹呈现方式，轨迹池固定）：
1. **Static-All**：一次性从全部轨迹池整合 → 模拟离线构建
2. **Static-Group**：按任务类型分组整合后拼接 → 离线构建的改进版
3. **Stream**：按批次流式更新 → 模拟持续学习的 Agent

**ARC-AGI Stream 测试台**（本文新建）：
- 基于 ARCGEN 构建，具有完全已知的潜在任务分类（6 族 × 7 技能）
- 提供程序化 ground-truth 解
- 暴露结构化的记忆操作词表（Retain / Delete / Consolidate）
- 维护双存储：Episodic Buffer（原始片段）+ Abstract Store（整合经验）
- 三种控制循环：Force（强制整合）、Auto（模型自选）、Episodic Management Only（仅管理原始片段）

## 实验设置

### 基准 / 数据集

| 基准 | 任务类型 | 训练数据 | 评估 |
|------|---------|---------|------|
| ALFWorld | 文本交互（6 种家务任务） | gpt-4.1/gpt-5-nano 生成轨迹（384–768 条） | 48 episode eval set |
| ScienceWorld | 科学实验模拟 | 15 个中等难度任务，485 条 rollout | 44 case test set |
| WebShop | 网购交互 | 128 条 AgentGym/gpt-5.4-mini 轨迹 | 50 session test set |
| AppWorld | 应用编程 | 140 条 GPT-4o/Qwen3.5-27B 轨迹 | TGC% |
| ARC-AGI Stream | 视觉推理 | 6 族 × 7 技能，有 GT 解 | 族级准确率追踪 |

### 对比方法

- **CLIN** (Majumder et al., 2023)：因果抽象记忆
- **Agent Workflow Memory (AWM)** (Wang et al., 2024)：工作流记忆
- **Dynamic Cheatsheet (DC)** (Suzgun et al., 2026)：动态速查表
- **ACE** (Zhang et al., 2025)：演进式上下文工程
- **Trajectory Log**：append-only 原始轨迹（不做整合的基线）

### 骨干模型

- GPT-5.4, GPT-5.4-Mini, GPT-5-Mini, GPT-5 Nano
- Qwen3.5-27B, Qwen3.5-9B, Qwen3.5-4B
- Claude-Haiku-4.5

### 评估指标

- ALFWorld：Task Success Rate（二值）
- WebShop：Mean Reward ×100 + Wins/50
- AppWorld：TGC%（Task Goal Completion）
- ARC-AGI Stream：Success % per problem / cumulative success
- ScienceWorld：Score per step

## 关键结果

### 1. 记忆整合导致效用退化（Figure 1, 2）

**ScienceWorld + CLIN**（Fig. 1a）：记忆效用随更新步数呈倒 U 型——先升后降，最终可降至无记忆基线以下。不同记忆容量（\|M\|=16, 50, ∞）均呈现相同趋势。

**WebShop + AWM**（Fig. 1b）：AWM 记忆从 8 样本时的 0.64 降至 128 样本时的 0.20，而 no-memory 基线也是 0.20——**规模化整合抹除了自身的收益**。

**ARC-AGI Stream + GPT-5.4**（Fig. 2）— 最干净的证据：

| 条件 | GPT-5.4 准确率 | 变化 |
|------|---------------|------|
| 无记忆基线 | **100%** (19/19) | — |
| Static R=10 | **94.7%** | −5.3 |
| Static R=50 | **94.7%** | −5.3 |
| Stream R=1 | **73.7%** | −26.3 |
| Stream R=10 | **52.6%** | **−47.4** |

> 所有输入均为 ground-truth 解法。Static（一次性整合）保持接近天花板；Stream（流式更新）暴跌至 52.6%。同一批轨迹，不同更新策略，结果天壤之别。

### 2. 流式整合全面崩溃（Figure 3）

| 模型 | No Memory | Static-All | Static-Group | Stream | Stream 降幅 |
|------|-----------|-----------|-------------|--------|-----------|
| GPT-5 Nano | 30.7 | 51.1 | **61.1** | 43.9 | **−17.2** |
| Qwen3.5-27B | 37.5 | **85.4** | 84.3 | 65.7 | **−18.6** |
| Qwen3.5-9B | 44.6 | 86.4 | **82.1** | 43.6 | **−38.5** |
| Qwen3.5-4B | 55.4 | **83.2** | 73.2 | 48.6 | **−34.6** |

> 流式更新 vs 一次性整合，损失 17–38 个百分点。

### 3. 原始轨迹是强力基线——整合方法普遍不如不整合（Table 2, 3）

**ALFWorld**（Task Success %）：

| 骨干模型 | NoMem | Traj Log (All) | ACE-GT | ACE | AWM | DC |
|---------|-------|---------------|--------|-----|-----|-----|
| GPT-5.4-Mini | 54 | **92** | 85(–) | 79(–) | 65(–) | 58(–) |
| GPT-5-Mini | 52 | **81** | 56(–) | 60(–) | 48(–) | 50(–) |
| Claude-Haiku-4.5 | 79 | **92** | 83(–) | 73(–) | 81(–) | 81(–) |

**AppWorld**（TGC %）：

| 骨干模型 | NoMem | Traj Log (All) | ACE | AWM | DC |
|---------|-------|---------------|-----|-----|-----|
| Qwen3.5-27B | 66 | **73** | 65(–) | 68(–) | 68(–) |
| GPT-5.4-Mini | 52 | **59** | 57(–) | 52(–) | 52(–) |
| Claude-Haiku-4.5 | 68 | 70 | 60(–) | **74** | 68(–) |

> (–) 标记表示该整合方法被至少一个轨迹日志基线击败。绝大多数整合方法 **不如直接保留原始轨迹**。

### 4. 保留 Episode > 强制整合（Figure 5, 9）

**ARC-AGI Stream 400 步训练**（累计成功率）：

| 策略 | GPT-5.4 | Haiku |
|------|---------|-------|
| No Memory | 22.0% | 23.8% |
| Force（强制整合每步） | 26.0% | 35.0% |
| Auto（\|Episodic\|=50） | 35.5% | 37.8% |
| Auto（\|Episodic\|=100） | **43.2%** | — |

> Auto 模式允许 Agent 保留原始 Episode，比强制整合高出 ~17pp。

**Episodic Management Only = 禁用整合，仅管理原始轨迹**（Fig. 9a）：
- Auto + Episodic: **62%**（\|E\|=100）
- Auto + Episodic: **54%**（\|E\|=50）
- Auto（Abstract Only）: **32%**
- No memory: **38%**

> **禁用整合（仅保留原始轨迹）匹配或超过所有含整合的策略**。

### 5. 记忆覆盖与诊断（Figure 7, Table 4）

| 指标 | Auto (\|B\|=1) | Force (\|B\|=1) | Auto (\|B\|=8) | Force (\|B\|=8) |
|------|--------------|--------------|--------------|--------------|
| 平均覆盖族数 | 1.33 | 1.67 | 2.17 | 5.00 |
| 平均错误融合 | 1.00 | 1.04 | 1.06 | 1.20 |
| Buffer 大小 | 3.33 | — | 50.00 | — |

> Agent 被允许自主管理时，默认行为是：**优先填充 Episodic Buffer，少做或不做抽象**（Fig. 7b）。更大的 Buffer 使 Compress 操作减半、Keep 操作增加（Fig. 7c）。

### 6. ScienceWorld 任务切换遗忘（Figure 10）

- **Fresh**（仅整合当前任务）vs **Cumulative**（累积整合所有已见任务）
- 15 任务序列中，Cumulative 比 Fresh 落后 **+203 分**
- LLM Judge 标注：Cumulative 的过度泛化记忆 ~5× Fresh，垃圾记忆 ~20× Fresh

## 消融 / 分析

### 三大失败模式（Section 6）

**1. 错误分组（Misgrouping）**
- Agent 把不同族的 episode 混在一起抽象
- 原因：Agent 有分类能力（Auto 模式最终覆盖全部 6 族），但强制整合打断了正确的分段
- Force 模式下误分类计数显著高于 Auto（Fig. 7a）
- 瓶颈不在识别族结构，而在 **保留族结构通过跨 episode 抽象**

**2. 过度泛化导致的干扰（Interference）**
- 抽象抹除了适用条件（precondition），一条"经验"误导相近任务
- 例：ALFWorld 中 Pick&Place 与 Pick-Clean-Place 的经验互相干扰（Fig. 8c）
- 在同一任务上反复精馏会干扰另一个任务类型：从 70.4% 降到 22.2%（GPT-5-Nano）和从 37.0% 到 11.1%（Qwen3.5-27B）（Fig. 8c）
- 类似人类记忆的"语义化"——反复复述使细节流失（Bartlett, 1932）

**3. 窄流过拟合（Overfit）**
- 输入分布变窄时，记忆过拟合到已见实例的表面特征
- ID 准确率维持，但 OOD 准确率急剧下降（Fig. 11）
- 例：GPT-5.4 ID 0.80 vs OOD 0.55（OOD gap 0.25）；Qwen3.5-27B ID 0.65 vs OOD 0.45（OOD gap 0.30）

### 异构批次加速退化（Figure 4）

- 即使必须流式更新，**同质批次 > 异构批次**
- 异构批次导致模型在单次更新中合并不兼容的经验
- 不同 Solver（Qwen3.5-27B/9B/4B）均观察到相同趋势

### 记忆手术消融（Section I.1）

- 从 WebShop AWM 整合记忆中移除单条 workflow（W8）即可提升 pass rate
- W8 使 Agent 倾向于 `click[Next >]` 死循环，牺牲 `click[Buy Now]`

## 局限性

**作者承认的局限**：
1. 仅评估文本基准（ALFWorld, ScienceWorld, WebShop, AppWorld, Mind2Web），未涵盖具身/多模态/工具密集的生产环境
2. 仅研究自然语言抽象（当前 LLM 实现），参数化记忆（权重更新/蒸馏）和非文本结构化表示不在范围内
3. 整合器和求解器都是 LLM，能力随模型改进可能变化
4. 受 API 成本限制，报告点估计而非正式误差条——通过多模型/多基准交叉验证缓解

**读者视角的额外局限**：
5. ARC-AGI Stream 是合成测试台，问题族数量有限（6 族），与真实 Agent 部署的多样性有差距
6. 未深入探讨"何时应该触发整合"的门控机制设计——只验证了"不应每次都整合"
7. Episodic-only 方案在长部署中的上下文窗口溢出问题未充分讨论

## 提及的实体

- [[Dylan-Zhang]] — UIUC，共同一作/通讯作者
- [[Hao-Peng]] — UIUC 教授，资深作者
- [[UIUC]] — 第一署名机构，University of Illinois Urbana-Champaign
- [[Tsinghua-IIIS]] — 第二署名机构，清华大学交叉信息研究院
- [[Mem0]] — 记忆基础设施公司，相关工作引用
- [[Google-Research]] — 相关工作引用（Titans 等）

## 讨论的概念

- [[Agent记忆整合]] — 核心研究对象：LLM 将经验轨迹压缩为文本记忆的过程
- [[记忆侵蚀]] — 整合后记忆效用随更新次数先升后降的倒 U 型现象
- [[情节性记忆（Agent）]] — 保留原始 episode 的记忆形式，论文证明其优于抽象记忆
- [[ARC-AGI-Stream]] — 本文新建的受控记忆测试台
- [[互补学习系统（Agent记忆）]] — 快速情节存储 + 慢速抽象存储的双系统设计原则
- [[错误分组]] — 整合时将不同类型经验混在一起
- [[过度泛化]] — 抽象抹除适用条件导致跨任务干扰
- [[窄流过拟合]] — 窄输入分布下记忆过拟合到表面特征

## 关联

- 与 [[mem0-building-production-ready-ai-agents|Mem0]] 的关系：Mem0 属于"每次交互后更新记忆"的设计范式，本文直接挑战了该假设
- 与 [[titans-learning-to-memorize-at-test-time|Titans]] 的关系：Titans 采用参数化记忆（神经长期记忆），本文聚焦文本记忆，两者互补
- 与 [[delta-mem-efficient-online-memory|δ-mem]] 的关系：δ-mem 通过 delta-rule 在线更新关联记忆状态，是参数化路线的另一种方案
- 与 [[llms-get-lost-in-multi-turn-conversation|LLMs Get Lost]] 的关系：两者都揭示了 LLM 在累积交互中性能退化的现象，但机制不同（记忆整合退化 vs 多轮对话迷失）
- 与 [[context-rot-how-increasing-input-tokens-impacts-llm|Context Rot]] 的关系：Context Rot 揭示输入长度导致退化，本文揭示记忆整合操作本身导致退化

## 个人笔记

**关键洞察**：
1. "每次整合至少无害"是错误的。整合是 **有损重写**，错误会随更新复合放大。
2. 原始 episode 作为一等公民的证据价值被严重低估。当前 ICL 能力已经可以从保留的实例中涌现出 schema-like 行为。
3. 分组/分段（segmentation）是整合的前提条件——先分对组再抽象。强制整合打断了模型原本有的分段能力。
4. 论文实际指向的设计原则：**延迟抽象、显式门控、保留可恢复的原始证据**。

**与自身研究的关联**：
- 该论文对 Agent 记忆系统设计有直接指导意义：优先使用 Episodic 策略，仅在确认收益时才触发整合
- ARC-AGI Stream 的设计思路（暴露记忆操作、族级追踪）可借鉴为 Agent 记忆评估的标准方法
- 三大失败模式（错误分组、过度泛化、过拟合）可作为 Agent 记忆系统的诊断检查清单

**开放问题**：
- 什么样的门控机制能决定"何时应该整合"？
- 更强的模型（如未来 GPT 版本）是否能成为更可靠的整合器？
- Episodic + Abstract 双存储的最佳容量分配比例？
