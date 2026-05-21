---
id: source-openclaw-rl
date: 2026-05-06
source: raw/papers/openclaw-rl-turning-daily-usage-into-training-signals.pdf
type: 论文
tags: [Agent RL, 强化学习, 在线学习, 过程奖励模型, 自蒸馏, 个性化, 混合RL, GRPO, POMDP]
---

# OpenClaw-RL: Train Any Agent Simply by Talking

## 一句话总结

OpenClaw-RL 提出了一种将 Agent 日常交互中的 next-state 信号（用户回复、工具输出、终端/GUI 状态变化）实时转化为在线训练信号的框架，通过服务器-客户端架构实现零中断推理，并引入混合 RL 目标（evaluative + directive 信号）和 overlap-guided hint selection 稳定策略优化，首次统一了个人 Agent 个性化与通用 Agent（terminal/GUI/SWE/tool-call）的 RL 训练基础设施。

## 基本信息

| 项目 | 内容 |
|------|------|
| **标题** | OpenClaw-RL: Train Any Agent Simply by Talking |
| **作者** | Yinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang†, Ling Yang† |
| **机构** | Gen-Verse（GitHub: Gen-Verse/OpenClaw-RL） |
| **日期** | 2026-03（arXiv v2: 2026-05-11） |
| **arXiv** | 2603.10165 |
| **代码** | https://github.com/Gen-Verse/OpenClaw-RL |

## 研究背景与动机

### 核心问题

当前 LLM Agent 系统（如 Claude Code、OpenAI Codex、OpenClaw）已广泛部署，但一个根本性的浪费被忽视了：**每次 Agent 交互都会产生一个 next-state 信号**（用户回复、工具输出、终端状态变化、GUI 状态变化），这些信号蕴含了丰富的训练信息，却没有被任何现有 Agentic RL 系统回收为在线学习来源。

### 现有方法的局限

| 方法类型 | 代表 | 局限 |
|---------|------|------|
| 批处理离线 RL | RLHF, GRPO, DPO | 数据收集和训练分离，无法利用实时交互 |
| 记忆/技能演化 | Mem0, Cognee | 仅更新上下文/检索内容，不更新模型参数 |
| 纯标量奖励 RL | RLVR (DeepSeek-R1, DAPO) | 无法利用 next-state 中的 token-level 指令信息 |
| 固定数据集蒸馏 | Hindsight relabeling, OPD | 离线操作，无法在线学习 |
| 单环境 Agent RL | DigiRL, WebRL, SWE-agent | 各自为政，无统一基础设施 |

### 关键洞察

Next-state 信号包含两种互补的训练信号：
1. **Evaluative signal**（评估信号）：标量反馈，判断动作好坏（如用户重试=不满意，测试通过=成功）
2. **Directive signal**（指令信号）：token-level 的纠正信息（如用户说"你应该先检查文件"不仅指出错误，还说明如何改正）

现有 RLVR 方法只能消费前者，on-policy distillation 方法只能消费后者，**没有一个框架能同时利用两者**。

## 核心方法

### 一、基础设施：服务器-客户端架构

#### 架构概览

```
Personal Devices          Cloud Services
    · Confidential API      · Large Scale Environments
         ↓                          ↓
    OpenClaw (个人Agent)      Terminal/GUI/SWE/Tool-call Agent
         ↓                          ↓
         └──────────→ RL Server ←──────────┘
                        · Slime Async Framework
                        · Zero Serving Interruption
                        · Graceful Weight Update
                        
    RL Server 四组件（完全解耦异步）：
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ Policy      │  │ PRM/Judge   │  │ Megatron    │  │ SGLang      │
    │ Server      │  │ Server      │  │ Training    │  │ Serving     │
    │ (推理API)   │  │ (信号提取)  │  │ Engine      │  │ Engine      │
    └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

#### 关键设计

1. **无状态推理 API**：RL 服务器以 API 形式托管策略 $\pi_\theta$，用户终端通过 HTTP 查询并回传交互数据。用户端框架可任意演化、更换工具，无需重新配置服务器。

2. **主线/辅线分类**：
   - **Main-line turns**：Agent 主要响应和工具执行结果，构成可训练样本
   - **Side turns**：辅助查询、记忆组织、环境转换，不产训练数据

3. **四组件完全解耦异步**：
   - 策略服务（SGLang）
   - PRM/评判（独立推理服务器，可投票、可用更强模型）
   - 策略训练（Megatron）
   - 环境托管（个人设备或云端并行环境）

   模型服务下一个请求时，PRM 评判前一个响应，训练器应用梯度更新。权重更新在同步边界推送到推理引擎，**用户永远看不到不一致的策略，也无需等待训练**。

### 二、方法论：从 Next-State 信号学习

#### 3.1 两种互补信号与混合 RL 目标

**Evaluative Signal（评估信号）**

给定 $(a_t, s_{t+1})$，PRM 查询 $m$ 次，每次返回 $\{+1, -1, 0\}$ 中的投票。取多数 $r_t \in \{+1, -1, 0\}$ 作为步骤 $t$ 的标量奖励。

- 密度：每个被评分的 turn 都贡献一个样本
- 粒度：序列级（整个 turn 压缩为 1 个标量）
- 信息：1 个标量

**Directive Signal（指令信号）**

PRM 首先判断 $s_{t+1}$ 是否包含有意义的纠正信息。如果是，将 $s_{t+1}$ 蒸馏为简洁的 hint $h$，包裹在 `[HINT_START]...[HINT_END]` 中。Hint 被追加到 prompt：$s_t^h = s_t \oplus h$，然后查询同一模型获得 teacher 分布 $\pi_T(\cdot | s_t^h)$。

- 密度：稀疏（仅在有可提取纠正的 turn 上触发）
- 粒度：token-level（完整的下一个 token 分布）
- 信息：$|S_i|$ 个 log-prob 差距

**互补性分析**

| 属性 | Evaluative | Directive | Hybrid (Ours) |
|------|-----------|-----------|---------------|
| 来源 | 标量 PRM 投票 | Hint-conditioned teacher | 两者结合 |
| 粒度 | 序列级 | Token-level | 混合 |
| 每样本信息 | 1 标量 | $\|S_i\|$ 个 log-prob 差距 | 1 标量 + $\|S_i\|$ 差距 |
| 频率 | 每个评分 turn | 有有意义 hint 的 turn | 每个评分 turn |

**混合目标函数**

对 token $i$：

$$L_i^{\text{hybrid}} = w_{\text{RL}} L_i^{\text{GRPO}} + w_{\text{OPD}} L_i^{\text{OPD}}$$

默认 $w_{\text{RL}} = w_{\text{OPD}} = 1$。两项共享同一轨迹和同一策略更新，整合了两者在频率和信息密度上的互补优势。

#### 3.2 Overlap-Guided Hint Selection

**核心问题**：On-policy distillation 的 central failure mode 是 teacher-student 分布不匹配。当 teacher 分布 $\pi_T$ 在 student 接近零密度的 token 上放置质量时，off-policy 重要性比率爆炸，梯度不稳定。

**关键洞察**：Hint 的选择直接控制不匹配程度。模糊的 hint 会把 teacher 拉离 student，精确的 hint 保持两者在重要 token 上接近。

**Overlap Signal 定义**

给定 student 的生成响应 $y$，令：
- $S_i^q = \text{top-}k\{\pi_{\text{old}}(\cdot | s_t, y_{<i})\}$：student 在位置 $i$ 的 top-$k$ 词表
- $S_{i,h}^p = \text{top-}k\{\pi_T(\cdot | s_t^h, y_{<i})\}$：hint $h$ 条件下 teacher 在位置 $i$ 的 top-$k$ 词表

Overlap signal：

$$O[h, i] = |S_i^q \cap S_{i,h}^p|$$

计数 student 的高概率 token 中有多少在 hint-conditioned teacher 下仍保持高概率。

**两种选择方案**

$$h^\star(i) = \begin{cases} \arg\max_h \sum_i O[h, i] & \text{sequence-level} \\ \arg\max_h O[h, i] & \text{token-level} \end{cases}$$

- Sequence-level：每个轨迹选一个 hint（更稳定，推荐用于 general agentic RL）
- Token-level：每个位置选不同 hint（与 OPD 的 token-level 本质对齐）

**Top-$k$ OPD Loss with Log-Probability-Difference Clip**

选定 $h^\star$ 后，将蒸馏损失限制在词表子集 $S_i$（默认 $S_i = S_i^q$）。对每个 $v \in S_i$：

$$A_v = \Delta_v \cdot w_v$$

其中：
- $\ell_{\text{old}}(v) = \log \pi_{\text{old}}(v | s_t, y_{<i})$
- $\ell_{T,h^\star}(v) = \log \pi_T(v | s_t^{h^\star}, y_{<i})$
- $w_v = \text{softmax}_{v \in S_i}(\ell_{\text{old}}(v))$：将优势集中在 student 实际可能采样的 token 上
- $\Delta_v = \text{clip}(\ell_{T,h^\star}(v) - \ell_{\text{old}}(v), -C, +C)$：裁剪 log-prob 差距

Per-vocab ratio：$\rho_v = \exp(\ell_{\text{cur}}(v) - \ell_{\text{old}}(v))$

蒸馏损失（clipped-surrogate 形式）：

$$L_i^{\text{OPD}} = \sum_{v \in S_i} \max\left( -A_v \rho_v,\ -A_v \cdot \text{clip}(\rho_v, 1 - \varepsilon_{\text{lo}}, 1 + \varepsilon_{\text{hi}}) \right)$$

其中 $\varepsilon_{\text{lo}} = 0.2$, $\varepsilon_{\text{hi}} = 0.28$（标准 PPO 裁剪）。

**稳定性机制的双重保障**：
1. Overlap-guided hint 选择使 $\rho_v$ 在监督 token 上接近 1
2. $\Delta$-clip 限制优势幅度

两者共同约束 surrogate 的两个因子，产生稳定更新。

#### 3.3 Step-wise Reward for General Agentic RL

**为什么过程奖励对 Agentic 任务至关重要**

在长程 Agentic 任务中，outcome-only 奖励仅在终止步骤提供梯度信号，绝大多数 turn 无监督。PRM 基于 next-state 信号为每个 turn 分配奖励，提供贯穿轨迹的密集信用分配。

**Outcome + Process Reward 集成**

遵循 RLAnything (Wang et al., 2026)，简单相加：

$$\text{Reward for step } t = o + \frac{1}{m}\sum_{i=1}^{m} r_i$$

其中 $o$ 为 outcome reward，$r_i$ 为 PRM$(a_t, s_{t+1})$ 独立分配的 $m$ 个过程奖励。

**标准化方法**：由于状态不易聚类（如 terminal agent），直接按相同步骤索引分组进行标准化。

### 符号表

| 符号 | 含义 | 维度/说明 |
|------|------|----------|
| $\pi_\theta$ | 策略模型 | 参数为 $\theta$ 的 LLM |
| $s_t$ | 状态 | 步骤 $t$ 的环境状态（部分可观测） |
| $a_t$ | 动作 | Agent 在步骤 $t$ 的响应 |
| $s_{t+1}$ | Next-state | 执行 $a_t$ 后的观测（用户回复/工具输出/环境状态） |
| $r_t$ | 评估信号 | $\{+1, -1, 0\}$，PRM 多数投票 |
| $h$ | 指令 hint | PRM 从 $s_{t+1}$ 蒸馏的纠正信息 |
| $s_t^h$ | Hint-augmented prompt | $s_t \oplus h$ |
| $\pi_T$ | Teacher 分布 | $\pi_T(\cdot \| s_t^h)$，与 student 同模型，条件不同 |
| $S_i^q$ | Student top-$k$ | $\text{top-}k\{\pi_{\text{old}}(\cdot \| s_t, y_{<i})\}$ |
| $S_{i,h}^p$ | Teacher top-$k$ | $\text{top-}k\{\pi_T(\cdot \| s_t^h, y_{<i})\}$ |
| $O[h, i]$ | Overlap signal | $\|S_i^q \cap S_{i,h}^p\|$ |
| $h^\star$ | 最优 hint | 最大化 overlap 的候选 hint |
| $S_i$ | Support set | 默认 $S_i = S_i^q$（student top-$k$） |
| $w_v$ | Softmax 权重 | $\text{softmax}_{v \in S_i}(\ell_{\text{old}}(v))$ |
| $\Delta_v$ | Log-prob 差距 | $\text{clip}(\ell_{T,h^\star}(v) - \ell_{\text{old}}(v), -C, +C)$ |
| $A_v$ | 蒸馏优势 | $\Delta_v \cdot w_v$ |
| $\rho_v$ | 重要性比率 | $\exp(\ell_{\text{cur}}(v) - \ell_{\text{old}}(v))$ |
| $C$ | Log-prob 裁剪系数 | Personal: 1, General RL: 2 |
| $k$ | Top-$k$ 宽度 | 默认 4 |
| $M$ | 候选 hint 数 | 默认 3 |
| $\varepsilon_{\text{lo}}, \varepsilon_{\text{hi}}$ | PPO 裁剪边界 | 0.2, 0.28 |
| $w_{\text{RL}}, w_{\text{OPD}}$ | 混合权重 | 默认均为 1 |

## 实验结果

### 4.1 个人 Agent 设置

使用 LLM 模拟三种职业用户（学生、TA、教师）使用 OpenClaw 完成工作，评估模型学习对齐用户偏好的效率。

**优化目标定义**：模型对首条消息的响应连续 3 个 session 满足用户偏好即视为优化成功。

| 用户类型 | 偏好描述 |
|---------|---------|
| 学生 | 用 OpenClaw 做作业，不想被发现用 AI（避免粗体、编号列表、过度格式化） |
| TA | 用 OpenClaw 批改作业，希望评语具体详细（长度 >= 100 tokens） |
| 教师 | 用 OpenClaw 写评语，希望评语友好耐心（包含"well done!"等温暖短语） |

**主结果（达到优化效果所需最少 session 数，越小越好）**

| 设置 | 方法 | Student | TA | Teacher | Average |
|------|------|---------|-----|---------|---------|
| **联合优化** | **Hybrid RL (Ours)** | **11.6** | **8.2** | **11.4** | **10.3** |
| | GRPO | 15.4 | 12.0 | 14.8 | 14.1 |
| | OPD | 30.8 | 34.0 | 24.4 | 29.7 |
| | Mem0 | 13.6 | 15.8 | 14.2 | 14.5 |
| | Cognee | 14.6 | 15.4 | 14.8 | 14.9 |
| **单独优化** | **Hybrid RL (Ours)** | **19.2** | **11.8** | **14.0** | **15.0** |
| | GRPO | 22.8 | 22.4 | 18.0 | 21.1 |
| | OPD | 34.6 | 36.0 | 17.6 | 29.4 |
| | Mem0 | 13.4 | 16.0 | 15.8 | 15.1 |
| | Cognee | 15.6 | 14.8 | 15.0 | 15.1 |

**关键发现**：
- Hybrid RL 在联合优化下仅需约 **10.3 个 session** 即可对齐，比 GRPO 快 27%，比 OPD 快 65%
- **联合优化显著放大 RL 收益**：Hybrid RL 联合 vs 单独差距大（10.3 vs 15.0），而记忆/技能演化方法几乎不受联合优化影响
- 假设原因：三个优化目标对策略模型是内在耦合的

### 4.2 通用 Agent 设置

覆盖 terminal、GUI、SWE、tool-call 四种最常用 real-world Agent 部署场景：

| 设置 | 环境 | Next-state 信号 | 交互步数 |
|------|------|----------------|---------|
| Terminal | Shell 执行沙箱 | stdout/stderr, exit code | 长 |
| GUI | 屏幕状态 + 可访问性树 | 视觉状态差异, 任务进度 | 长 |
| SWE | 代码仓库 + 测试套件 | 测试判决, diff, lint 输出 | 长 |
| Tool-call | API/函数执行 | 返回值, 错误追踪 | 中 |

**大规模并行环境**：128 个并行 terminal 环境、64 个 GUI/SWE、32 个 tool-call。

**过程奖励的价值**：在 tool-call（250 步）和 GUI（120 步）长程设置中，集成 outcome + process reward 分别达到 0.25 和 0.33，而仅 outcome 为 0.19 和 0.31。

### 4.3 Hybrid RL 泛化到大规模设置

- **Multi-turn tool-call (ReTool)**：Hybrid RL 优于 outcome-only 和 PRM+Outcome 基线
- **RLVR (AIME 2024)**：Hybrid RL 同样优于 outcome-only 基线

### 4.4 Overlap-Guided Hint Selection 的效果

| 设置 | Hybrid RL sequence-optimal | Hybrid RL token-optimal | Hybrid RL random | GRPO | OPD |
|------|---------------------------|------------------------|-----------------|------|-----|
| Student | 14.0 | 13.8 | 18.6 | 17.2 | 34.4 |
| TA | 9.6 | 10.0 | 12.6 | 12.0 | 29.8 |
| Teacher | 13.8 | 13.4 | 17.0 | 18.2 | 25.6 |
| Average | **12.5** | **12.4** | 16.1 | 15.8 | 29.9 |

- Sequence-optimal 和 token-optimal 性能相近，均显著优于 random
- Sequence-optimal 在 general agentic RL 中更稳定

### 4.5 Log-Probability Difference Clip 的必要性

Token-level log-probability shift 分析显示，hint conditioning 可在某些 token 上产生极端的 log-prob 差异（图 7(3)）。无裁剪时：
- 平均响应长度持续增长
- 最终截断比率：0.5（无裁剪）vs 0.2（有裁剪）
- 说明裁剪通过抑制极端 log-prob 偏移和防止长度失控来提升稳定性

### 4.6 $k$ 和 Support Set $S_i$ 的消融

| $S_i = S_i^q$ (student top-$k$) | $k=2$ | $k=4$ | $k=8$ | $k=20$ |
|--------------------------------|-------|-------|-------|--------|
| Student | 30.4 | **11.6** | 12.8 | 11.4 |
| TA | 12.0 | **8.2** | 7.6 | 7.8 |
| Teacher | 17.2 | **11.4** | 10.0 | 10.2 |
| Average | 20.2 | **10.3** | 10.1 | 9.8 |

- $k \leq 4$ 时增大 $k$ 有收益，$k \geq 4$ 后收益很小
- 退化情况（token-level OPD）性能大幅下降
- 使用 top-$k$ overlap 作为 $S_i$ 性能轻微下降

### 4.7 不同策略和奖励模型的探索

使用 Qwen3-32B 作为策略（联合优化，表 4）：方法鲁棒性在大模型上得到验证，但大模型不保证比小模型优化更快。

使用 Qwen3-8B 作为 PRM teacher 指导 Qwen3-4B-Thinking 训练（表 7）：性能与使用同模型作为 teacher 非常接近。

## 消融实验

### 核心消融总结

| 消融维度 | 关键发现 |
|---------|---------|
| **Hybrid vs 单一目标** | Hybrid RL 显著优于 GRPO 或 OPD 单独使用，验证互补性 |
| **vs 记忆/技能演化** | Hybrid RL 比 Mem0/Cognee 更快，且不增加推理时上下文开销 |
| **Hint 选择策略** | Overlap-guided >> Random；Sequence-optimal ≈ Token-optimal |
| **Log-prob clip** | 必要：防止极端差异导致长度失控和训练不稳定 |
| **$k$ 值** | $k=4$ 为最佳平衡点 |
| **Support set** | Student top-$k$ 略优于 overlap top-$k$ |
| **PRM 模型规模** | 8B PRM 与 4B PRM 效果相近 |
| **联合 vs 单独优化** | 联合优化显著放大 RL 收益，对记忆方法无影响 |

## 优点与局限

### 优点

1. **首次实现实时个人 Agent 在线 RL**：将日常交互转化为训练信号，无需预收集数据
2. **混合目标整合互补信号**：evaluative（频繁、稀疏）+ directive（稀少、丰富）的统一
3. **稳定的蒸馏机制**：Overlap-guided hint selection + log-prob clip 双重保障 teacher-student 匹配
4. **首个统一通用 Agent RL 基础设施**：覆盖 terminal/GUI/SWE/tool-call 四种核心场景
5. **零中断服务**：四组件完全解耦异步，训练不阻塞推理
6. **实用性强**：约 10 个 session 即可对齐个人偏好

### 局限

1. **负面/对抗反馈风险**：恶意纠正或误导指令可能毒化模型，需要更强的训练数据过滤
2. **隐私与安全**：为个人使用优化的模型可能编码用户特定偏好和私人信息，成为攻击目标
3. **PRM 资源开销**： hosting PRM 需要额外计算资源（vs outcome-only）
4. **Hint 质量依赖 PRM**：低质量 hint 仍可能 destabilize，尽管 overlap 选择缓解了这一问题
5. **未验证跨用户泛化**：联合优化在共享模型上的多用户场景已验证，但真正的跨用户泛化未深入探讨

## 提及的实体

- [[OpenClaw]] — 开源个人 AI 助手，本文主要实验平台
- [[Mem0]] — 结构化记忆框架，对比基线
- [[Cognee]] — 知识图谱记忆框架，对比基线
- [[Qwen]] — 基座模型族（Qwen3-4B/8B/32B, Qwen3VL-8B）
- [[DeepSeek-R1]] — RLVR 代表方法
- [[DAPO]] — 大规模 RL 系统
- [[slime]] — RL 训练基础设施框架，OpenClaw-RL 基于此构建
- [[SGLang]] — 推理服务引擎
- [[Megatron]] — 训练引擎
- [[GSM8K]] — 个人 Agent 评估数据集
- [[SETA]] — Terminal Agent 训练数据
- [[OSWorld-Verified]] — GUI Agent 评估数据集
- [[SWE-Bench-Verified]] — SWE Agent 评估数据集
- [[AIME 2024]] — Tool-call/RLVR 评估数据集

## 讨论的概念

- [[Agent RL]] — Agent 强化学习，本文核心领域
- [[GRPO]] — 组相对策略优化，混合目标的 RL 分支基础
- [[POMDP]] — 部分可观测马尔可夫决策过程，Agent 交互的理论框架
- [[过程奖励模型 (PRM)]] — 步骤级奖励判断，本文信号提取核心
- [[经验驱动自演化]] — 与 EvolveR 等工作的关联：OpenClaw-RL 是在线信号驱动，EvolveR 是离线经验蒸馏
- [[自蒸馏 (Self-Distillation)]] — OPD 分支的本质：同模型在不同条件下的蒸馏
- [[On-Policy Distillation]] — 在 student 自己的 rollout 上评估 teacher
- [[Hindsight Relabeling]] — 事后纠正重标注，hint extraction 的理论基础
- [[混合RL (Hybrid RL)]] — 本文提出的核心方法论创新
- [[Overlap-Guided Hint Selection]] — 本文提出的 hint 选择机制
- [[Log-Probability-Difference Clip]] — 本文提出的稳定性机制
- [[Next-State Signal]] — 本文核心概念：交互中的下一个状态作为训练信号源

## 推荐参考文献

### 强烈推荐

1. **RLAnything** (Wang et al., 2026) — 过程奖励对长程 Agentic 任务至关重要的大规模证据，OpenClaw-RL 直接基于此洞察。arXiv: 2602.02488
2. **Rethinking On-Policy Distillation** (Li et al., 2026) — 系统分析 teacher-student 不匹配问题，OpenClaw-RL 的 overlap-guided 选择是对该问题的直接回应。arXiv: 2604.13016
3. **Aligning Language Models from User Interactions** (Buening et al., 2026) — 同期工作，用 next-state 信息直接 prompt 在线策略，但 hints 隐含而非显式信号。arXiv: 2603.12273

### 值得阅读

4. **Reinforcement Learning via Self-Distillation** (Hubotter et al., 2026) — 自蒸馏 RL 的理论基础， hindsight relabeling 形式化。arXiv: 2601.20802
5. **DAPO** (Yu et al., 2025a) — 大规模开源 RL 系统，OpenClaw-RL 的 RLVR 实验基于此。arXiv: 2503.14476
6. **DeepSeek-R1** (Guo et al., 2025) — RLVR 推理模型的里程碑，展示纯标量奖励的潜力与局限。arXiv: 2501.12948
7. **slime** (Zhu et al., 2025) — OpenClaw-RL 的基础设施基础，解耦 rollout 和训练引擎。GitHub: THUDM/slime

### 背景补充

8. **GRPO** (Shao et al., 2024) — 无需 critic 的 RL 算法，OpenClaw-RL 混合目标的 RL 分支基础。arXiv: 2402.03300
9. **Math-Shepherd** (Wang et al., 2024) — 自动化步骤级监督，PRM 自动化标注的早期工作。ACL 2024
10. **PPO** (Schulman et al., 2017) — 策略优化基础算法，clipped surrogate 的来源。arXiv: 1707.06347

## 关联

- [[Agent RL]] — OpenClaw-RL 是 Agent RL 的在线实时扩展，将批处理离线范式转为连续在线范式
- [[GRPO]] — 混合目标的 RL 分支基于 GRPO，但扩展了 token-level 蒸馏损失
- [[POMDP]] — Agent 交互可形式化为 POMDP，next-state 即为观测 $o_{t+1}$
- [[经验驱动自演化]] — 与 EvolveR 形成互补：EvolveR 是"离线蒸馏 + 在线检索"，OpenClaw-RL 是"在线实时学习"；两者共同指向 Agent 持续自我改进的方向
- [[evolver-from-trajectories-to-principles|EvolveR]] — 经验闭环自演化框架，OpenClaw-RL 可视为其在线实时化的补充
- [[自蒸馏-Agent策略自蒸馏]] — OPD 分支本质是自蒸馏，但增加了 hint-conditioned 和 overlap-guided 选择
- [[Mem0]] — 记忆基线对比，OpenClaw-RL 通过参数更新实现持久学习，Mem0 通过上下文检索
- [[过程奖励模型 (PRM)]] — 本文将 PRM 从离线数学推理扩展到在线异构 Agent 设置