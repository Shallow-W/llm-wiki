---
id: source-llms-get-lost
date: 2026-05-06
source: raw/papers/llms-get-lost-in-multi-turn-conversation.pdf
type: 论文
tags: [LLM评估, 多轮对话, 欠规范, 可靠性, 对话迷失, 生成任务]
---

# LLMs Get Lost in Multi-turn Conversation

## 一句话总结

通过大规模模拟实验（20万+对话）系统揭示：所有主流 LLM 在多轮欠规范对话中性能平均下降 39%，表现为轻微的能力下降（-15%）和剧烈的可靠性恶化（+112%），且一旦"走错路"就无法自我修正——即"对话迷失"现象。

## 基本信息

| 项目 | 内容 |
|------|------|
| **标题** | LLMs Get Lost in Multi-turn Conversation |
| **作者** | Philippe Laban (Microsoft Research), Hiroaki Hayashi (Salesforce Research), Yingbo Zhou (Salesforce Research), Jennifer Neville (Microsoft Research) |
| **日期** | 2025-05-09 (arXiv) |
| **arXiv** | 2505.06120v1 |
| **机构** | Microsoft Research, Salesforce Research |
| **代码/数据** | Microsoft/lost_in_conversation, datasets/Microsoft/lost_in_conversation |

## 研究背景与动机

LLM 作为对话界面（如 ChatGPT、Gemini、Claude），承诺帮助用户不仅能在任务完全明确时提供帮助，还能在用户需求不明确时通过多轮对话来探索和细化需求。然而存在一个根本性矛盾：

1. **评估与现实脱节**：对话日志分析已证实用户指令中的欠规范（underspecification）非常普遍，但 LLM 评估几乎全部集中在单轮、完全指定的指令设置上。
2. **情景式评估的局限**：现有的多轮评估（如 MT-bench）大多将对话视为情景式（episodic）——每一轮引入可独立评估的子任务——这偏离了人类对话中常见的欠规范特性。
3. **缺乏系统性比较**：缺乏在相同任务上直接比较单轮与多轮性能的受控实验。

本文的核心理念是：**将欠规范（underspecification）作为评估的核心要素**，而非回避它。

## 核心发现

### 1. 性能大幅下降：平均 -39%

所有 15 个测试的 LLM（从 Llama-3.1-8B 到 Gemini 2.5 Pro）在多轮欠规范对话中均表现显著下降：
- 单轮完全指定平均得分：**90%**
- 多轮欠规范平均得分：**65%**
- 平均下降：**25 个百分点（约 39%）**
- 即使仅两轮对话也能观察到显著下降

### 2. 性能下降的双分量分解

论文提出将性能退化分解为两个正交维度（参见 [[能力-可靠性分解（aptitude-reliability）]]）：

- **能力下降（Aptitude Loss）**：平均下降 **15%**——即最佳情况下的表现也变差了
- **可靠性恶化（Unreliability Increase）**：平均增加 **112%**——即最佳与最差情况之间的差距剧烈扩大

关键观察：在单轮设置中，高能力的模型往往也更可靠（如 GPT-4.1、Gemini 2.5 Pro）；但在多轮设置中，**所有模型（无论能力高低）都表现出极高的不可靠性**。

### 3. "对话迷失"现象

论文最核心的发现——**当 LLM 在多轮对话中走了错误的方向，它们就会迷路且无法恢复**（when LLMs take a wrong turn, they get lost and do not recover）。具体表现为四个行为模式：

1. **过早尝试回答**（Premature Answer Attempts）：LLM 在信息不足时就尝试生成完整解答，做出错误假设。首次回答尝试越早，性能越低——在前 20% 轮次就尝试回答的平均得分仅 30.9，而在最后 20% 轮次才回答的平均得分达 64.4。

2. **答案膨胀**（Answer Bloat）：后续回答尝试的长度逐轮增长，最终答案比单轮等价答案长 20-300%。即便最终答案正确，多轮解答也比单轮解答平均长 14-27%。

3. **过度依赖最后一轮**（Loss-in-Middle-Turns）：在摘要任务中，LLM 更倾向于引用首轮或末轮引入的文档，中间轮次的文档被引用的概率显著降低（比首末轮低 150%）。这是 [[lost-in-the-middle]] 现象在多轮对话中的体现。

4. **过度冗长的回复**（Overly Verbose Responses）：在六个任务中的五个，回复越短性能越高——最短回复组的性能比最长回复组高 10-50%。冗长的回复引入更多假设，分散注意力。

## 实验设计与方法

### 指令分片（Instruction Sharding）

论文的核心方法论创新——参见 [[指令分片（instruction-sharding）]]。将完全指定的指令拆分为一组"分片"（shards），每个分片只引入一条信息。然后在多轮对话中逐轮揭示分片，模拟用户逐步提供信息的场景。

分片指令需满足五个属性：
- P1 信息保持：不丢失原始信息
- P2 明确初始意图：第一分片定义高层目标
- P3 顺序无关：非首分片可任意排列
- P4 最大分片：尽可能细粒度
- P5 最小变换：尽量保持原始用语

### 五种对话模拟类型

| 模拟类型 | 简写 | 说明 |
|----------|------|------|
| Fully-Specified | FULL | 单轮完全指定（基线） |
| Sharded | SHARDED | 多轮欠规范（核心实验） |
| Concatenated | CONCAT | 单轮但用分片拼接（验证基线） |
| Recap | RECAP | SHARDED + 末轮总结全部信息 |
| Snowball | SNOWBALL | 每轮都重复已揭示的所有分片 |

### 六项任务

| 任务 | 领域 | 来源 | 指令数 | 评估方式 |
|------|------|------|--------|----------|
| Code | 编程 | HumanEval + LiveCodeBench | 145 | 功能准确性 |
| Database | 编程 | Spider | 107 | SQL 执行匹配 |
| Actions | 编程 | BFCL V3 | 105 | API 语义等价 |
| Math | 编程 | GSM8K | 103 | 数值精确匹配 |
| Data-to-Text | 自然语言 | ToTTo | 120 | BLEU |
| Summary | 自然语言 | Summary of a Haystack | 92 | 覆盖度+引用准确性 |

### 15 个测试模型

涵盖从小型开源到 SOTA 的完整谱系：Llama-3.1-8B, OLMo2-13B, Phi-4, Claude 3 Haiku, Claude 3.7 Sonnet, GPT-4o-mini, GPT-4o, GPT-4.1, o3, Llama-3.3-70B, Llama-4-Scout, Command-A, Deepseek-R1, Gemini 2.5 Flash, Gemini 2.5 Pro。

## 关键实验数据

### 主实验结果（200,000+ 对话）

| 指标 | FULL（单轮） | SHARDED（多轮） | 变化 |
|------|-------------|----------------|------|
| 平均性能 P | ~90% | ~65% | -25pp |
| 能力 A90 | ~92% | ~77% | -15pp |
| 不可靠性 U | ~12% | ~25% | +112% |

### 缓解策略效果

| 策略 | 效果 |
|------|------|
| RECAP（末轮总结） | 部分改善但仍远低于 FULL |
| SNOWBALL（逐轮重复） | 缓解 FULL→SHARDED 退化的 15-20% |
| 降低温度至 T=0 | 单轮改善 50-80%，多轮几乎无效（不可靠性仍约 30%） |

### 翻译任务的反例

翻译任务在 SHARDED 设置下**未观察到性能退化**，因为翻译可以在句子级别独立完成——这验证了论文的假设：**当任务本质上是情景式（可分解为独立子任务）时，模型不会迷失**。导致迷失的三个任务属性：生成性（非抽取式）、足够复杂（多规格）、解答不可分解。

## 影响与启示

### 对 LLM 构建者的呼吁

论文明确呼吁 LLM 开发者在优化能力（aptitude）的同时**优先考虑可靠性（reliability）**，并提出可操作的挑战目标：
1. 单轮和多轮设置下应达到相近能力
2. 多轮设置下不可靠性 U < 15
3. 以上目标应在默认温度 T=1.0 下达成

这对 [[δ-mem（在线关联记忆）]] 等 LLM 记忆机制的设计具有直接启示——需要能够有效管理和整合多轮对话中逐步揭示的信息，避免上下文丢失和错误累积。

### 对用户的建议

1. **如果时间允许，重新开始**：开新对话比继续迷失的对话更有效
2. **重试前先整合**：让 LLM "请整合到目前为止我告诉你的所有内容"，然后把整合结果带入新对话

### 对 NLP 研究者的启示

论文鼓励研究者为自己的任务创建分片版本，以评估模型在多轮欠规范场景下的表现，并提供了可复用的分片工具和流程。

## 推荐参考文献

- Herlihy et al. (2024) — LLM 在欠规范查询下的响应模式分类
- Liu et al. (2024) — "Lost in the Middle"：LLM 对长上下文中间部分的注意力衰减
- Laban et al. (2024) — Summary of a Haystack：长文档摘要评估基准
- Zipf (1949) — "最小努力原则"：人类语言沟通中欠规范的理论基础

## 关联

- [[δ-mem（在线关联记忆）]] — δ-mem 论文引用本文作为动机文献之一，LLM 在多轮对话中的信息丢失问题正是记忆机制需要解决的核心挑战
- [[对话迷失现象（lost-in-conversation）]] — 本文提出的核心概念
- [[指令分片（instruction-sharding）]] — 本文提出的评估方法
- [[能力-可靠性分解（aptitude-reliability）]] — 本文提出的性能分析框架
- [[lost-in-the-middle]] — 本研究发现其在多轮对话中的延伸表现
