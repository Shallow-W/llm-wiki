---
id: source-context-rot
date: 2026-05-06
source: raw/papers/context-rot-how-increasing-input-tokens-impacts-llm.pdf
type: 论文/报告
tags: [长上下文, LLM评估, 上下文退化, 注意力机制, Chroma, 技术报告]
---

# Context Rot: How Increasing Input Tokens Impacts LLM Performance

## 一句话总结

Chroma 团队对 18 个主流 LLM（包括 GPT-4.1、Claude 4、Gemini 2.5、Qwen3）的系统评估表明：**即使任务复杂度保持不变，仅增加输入 token 长度就会导致模型性能非均匀地退化**，揭示了"上下文腐烂"（Context Rot）现象——简单扩展上下文窗口并不能可靠地提升模型利用长上下文的能力。

## 基本信息

| 项目 | 内容 |
|------|------|
| **标题** | Context Rot: How Increasing Input Tokens Impacts LLM Performance |
| **作者** | Kelly Hong, Anton Troynikov, Jeff Huber |
| **机构** | Chroma |
| **日期** | July 14, 2025 |
| **类型** | 技术报告（Technical Report） |
| **URL** | https://trychroma.com/research/context-rot |
| **代码** | 完整复现代码已开源 |

## 研究背景与动机

### 核心问题

现代 LLM 的上下文窗口已扩展到百万级 token（Gemini 1.5 Pro 1M、GPT-4.1 1M、Llama 4 10M），业界普遍假设模型能**均匀地处理上下文**——第 10,000 个 token 应该和第 100 个 token 一样可靠。然而，这个假设在实践中并不成立。

### NIAH 的局限性

当前最广泛使用的长上下文基准测试 **Needle in a Haystack (NIAH)** 本质上是一个简单的**词汇匹配检索任务**：将一个已知句子（"针"）放入长文档（"草堆"）中，让模型检索它。虽然可扩展，但 NIAH 仅评估直接词汇匹配能力，不能代表需要灵活语义理解的真实场景。

由于模型在 NIAH 上通常取得接近完美的分数，这导致了一种错误认知：长上下文问题已经"基本解决"。

### Context Rot 是 δ-mem 的核心动机

本文是 [[delta-mem-efficient-online-memory|δ-mem]] 论文引用的核心动机文献之一。δ-mem 的作者明确指出：**简单扩展上下文窗口只是把记忆问题转化为长上下文处理问题，并没有从根本上解决记忆**。Context Rot 的实验证据直接支撑了这一论断——即使上下文窗口足够大，模型也无法可靠地利用其中的信息。

## 核心发现

### 实验设计原则

本报告的关键设计原则是**保持任务复杂度恒定，仅改变输入长度**，从而将输入长度本身作为唯一变量来测量其对性能的影响。这与许多现有基准不同——后者往往让任务复杂度随输入长度一起增长，导致无法区分性能下降是来自更长的输入还是更难的任务。

### 实验一：Needle-Question 相似度（语义匹配）

**实验设置**：
- 使用 Paul Graham  essays 和 arXiv 论文作为两种 haystack 主题
- 对每个主题，人工编写 8 个 needle，通过嵌入模型计算 needle-question 的余弦相似度
- 使用 5 个不同的嵌入模型取平均，确保鲁棒性
- 测试 8 个输入长度 × 11 个 needle 位置
- 评估 18 个模型（包括 thinking/non-thinking 模式）

**关键发现**：
- **相似度越低，退化越快**：随着 needle-question 相似度降低，模型性能随输入长度增加而退化得更显著
- 在短输入长度下，即使是低相似度配对，模型也能表现良好——说明模型**有能力**完成这类任务
- 性能退化**不是**因为 needle-question 配对本身的内在难度，而是因为输入长度增加
- needle 位置对性能没有显著影响（与某些先前研究的发现不同）

### 实验二：干扰项的影响（Distractors）

**实验设置**：
- 选取一个高相似度的 needle-question 配对作为基线
- 人工编写 4 个干扰项（distractors），每个都与 needle 主题相关但不能直接回答问题
- 三种测试条件：仅 needle（基线）、needle + 1 个随机干扰项、needle + 4 个随机干扰项

**关键发现**：
- **单个干扰项就会降低性能**，4 个干扰项进一步加剧退化
- **干扰项的影响是非均匀的**：不同干扰项造成的性能下降程度不同。例如，在 arXiv haystack + PG essay needle 组合中，distractor 3 造成的性能下降明显大于其他干扰项
- **干扰项的影响随输入长度增长而放大**
- **模型家族间存在行为差异**：
  - **Claude 家族**：幻觉率最低，尤其 Claude Sonnet 4 和 Opus 4 在不确定时会选择弃权（abstain），明确声明找不到答案
  - **GPT 家族**：幻觉率最高，在存在干扰项时经常生成自信但错误的回答

### 实验三：Needle-Haystack 相似度

**实验设置**：
- 使用 Paul Graham essays 和 arXiv 论文两种 haystack
- 为每种 haystack 编写对应的 needle，测量 needle 与 haystack 的语义相似度
- 将 PG essay needle 放入 arXiv haystack，反之亦然，形成"相似"与"不相似"的对比

**关键发现**：
- 结果**不一致且非均匀**：
  - 在 PG essay haystack 中，arXiv needle（不相似）表现显著优于 PG essay needle（相似）——即 needle 与 haystack 越不相似，模型表现越好
  - 但在 arXiv haystack 中，两种 needle 的性能差异很小
- 由于仅测试了两个主题，无法得出"高 needle-haystack 相似度必然导致性能下降"的一般性结论
- 但明确揭示了：即使任务结构和 needle-question 相似度保持不变，改变 needle 与 haystack 的语义相似度就能影响结果——这是长上下文基准测试中被忽视的重要维度

### 实验四：Haystack 结构（逻辑连贯性 vs 随机打乱）

**实验设置**：
- **Original**：保留 haystack 中每段摘录的自然逻辑流
- **Shuffled**：将 haystack 中所有句子随机重排，保持相同主题但消除逻辑连续性

**关键发现**（最反直觉的发现）：
- **结构连贯性一致地损害模型性能**
- 在所有 18 个模型和所有 needle-haystack 组合中，模型在**打乱的 haystack 上表现更好**
- 这与直觉相反：如果 haystack 由连贯的 essay 组成，随机插入的 needle 应该更容易被发现（因为它打断了逻辑流）；而在打乱的 haystack 中，needle 应该更容易"混入"
- 实际结果恰恰相反，暗示模型可能以**结构化、顺序敏感**的方式处理上下文，而逻辑连贯的 haystack 可能让模型"陷入"其叙事流中

### 实验五：LongMemEval（对话式问答）

**实验设置**：
- 使用 LongMemEval 基准（平均 113k token 的对话历史）
- 对比两种条件：
  1. **Focused input**（~300 tokens）：仅包含回答问题所需的相关部分
  2. **Full input**（~113k tokens）：完整对话历史，包含大量无关上下文
- 过滤后保留 306 个 prompt，涵盖知识更新、时序推理、多会话三种类型
- 使用 GPT-4.1 作为 LLM judge，对齐度 >99%

**关键发现**：
- **所有模型在 full input 上性能显著下降**
- **Claude 家族的差距最大**：Claude Opus 4 和 Sonnet 4 在 full input 下特别保守，经常因不确定性而弃权。这与它们在 NIAH 干扰项实验中的行为一致
- **Thinking 模式有提升但无法消除差距**：启用 thinking 后，focused 和 full input 的性能都有提升，但两者之间的差距依然存在
- **问题类型排序**（非 thinking 模式）：知识更新 > 多会话 > 时序推理
- **问题类型排序**（thinking 模式）：知识更新 > 时序推理 > 多会话（thinking 帮助时序推理最多）

### 实验六：Repeated Words（重复词复现）

**实验设置**：
- 最简任务：模型被要求**精确复现**一段重复词序列，其中插入一个唯一的不同词
- 7 种词组合（如 "apple" 重复中插入 "apples"）
- 12 个词数级别（25 ~ 10,000 词）
- 1090 种上下文长度 × 唯一词位置 的组合
- 评分使用归一化 Levenshtein 距离

**关键发现**：
- **即使是最简单的复制任务，性能也随上下文长度增加而退化**
- **位置效应**：唯一词出现在序列开头时准确率最高，越靠后越容易出错
- **词数差异**：随着长度增加，模型经常生成到输出 token 上限就停止，导致欠生成
- **模型特异性行为**：
  - **Claude Opus 4**：拒绝率 2.89%（唯一拒绝任务的 Claude 模型），常先观察再决定是否执行，典型拒绝理由包括"可能生成版权材料"
  - **GPT-4.1**：拒绝率 2.55%，从 2500 词开始出现"I'm sorry, but I can't help with that"
  - **Gemini 2.5 Pro**：从 500-750 词开始出现随机词生成（如 "I'-a-le-le-le..."）
  - **Qwen3-8B**：4.21% 非尝试率，从 5000 词开始出现无意义重复文本
  - **GPT-4.1 nano**：在 "San Francisco"/"sf" 组合中输出小写 "san"，在 "Golden Gate Bridge"/"Golden Gate Park" 组合中输出 "Golden Golden"、"Gate Gate" 等不存在于输入中的词

## 关键实验数据

### 评估模型列表（18 个）

| 家族 | 模型 |
|------|------|
| **Anthropic** | Claude Opus 4, Claude Sonnet 4, Claude Sonnet 3.7, Claude Sonnet 3.5, Claude Haiku 3.5 |
| **OpenAI** | o3, GPT-4.1, GPT-4.1 mini, GPT-4.1 nano, GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo |
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.0 Flash |
| **Alibaba** | Qwen3-235B-A22B, Qwen3-32B, Qwen3-8B |

### 实验条件汇总

| 实验 | 变量 | 条件数 | 关键控制 |
|------|------|--------|----------|
| Needle-Question 相似度 | 相似度（8 个 needle） | 8 长度 × 11 位置 | 任务复杂度恒定 |
| 干扰项 | 干扰项数量（0/1/4） | 3 条件 × 4 干扰项 | 高相似度 needle |
| Needle-Haystack 相似度 | haystack 主题 | 2 haystack × 2 needle 类型 | 相同 needle-question 对 |
| Haystack 结构 | 连贯 vs 打乱 | 2 条件 | 相同词汇集合 |
| LongMemEval | 输入长度（focused/full） | 2 条件 × 306 prompt | 相同问题 |
| Repeated Words | 词数（25~10,000） | 12 级别 × 多位置 | 完全相同的任务 |

### 评估方法

- **NIAH 实验**：GPT-4.1 作为 LLM judge，与人类判断对齐度 >99%
- **LongMemEval**：GPT-4.1 judge，同样 >99% 对齐
- **Repeated Words**：归一化 Levenshtein 距离 + 位置准确率 + 词数差异
- **模型调用**：temperature=0（除非不兼容，如 o3）；Qwen 使用 YaRN 扩展到 131,072 tokens

## 影响与启示

### 对 LLM 记忆机制设计的影响

1. **扩展上下文窗口 ≠ 解决记忆问题**：Context Rot 直接证明了即使上下文窗口足够大，模型也无法可靠利用其中的信息。这是 [[delta-mem-efficient-online-memory|δ-mem]] 等记忆机制的核心动机。

2. **上下文工程（Context Engineering）的重要性**：信息在上下文中的呈现方式（位置、结构、与干扰项的关系）比信息是否存在更重要。

3. **干扰项的放大效应**：在实际应用中（如 RAG、Agent 记忆），干扰项几乎不可避免。Context Rot 表明，随着上下文变长，干扰项的危害会被放大。

4. **模型选择需考虑长上下文行为**：不同模型家族在处理长上下文时的行为模式差异显著（Claude 保守弃权 vs GPT 自信幻觉），这会影响应用场景的选择。

### 对长上下文评估的启示

1. **NIAH 不足**：简单的词汇匹配基准不能代表真实的长上下文使用场景。
2. **隔离变量**：评估时必须将"输入长度"与"任务复杂度"分离，否则无法判断性能下降的真正原因。
3. **多维度评估**：需要同时考虑语义匹配、干扰项、上下文结构、对话历史等多个维度。

### 对实际应用的启示

1. **RAG 系统**：即使检索到了正确的文档片段，如果上下文中存在语义相似的干扰项，模型仍可能出错——且错误率随上下文长度增加。
2. **Agent 记忆**：简单地将完整对话历史塞入提示不是可靠的"记忆"方案。需要更智能的上下文管理（如 δ-mem 的在线状态压缩）。
3. **文本复制/生成任务**：即使是简单的文本复现，长序列也会导致可靠性下降——这对代码生成、文档处理等应用有直接影响。

## 提及的实体

- [[Kelly Hong]] — 第一作者，Chroma
- [[Anton Troynikov]] — 共同作者，Chroma
- [[Jeff Huber]] — 共同作者，Chroma
- [[Chroma]] — 向量数据库公司，本报告的发布机构
- [[OpenAI]] — GPT-4.1、o3、GPT-4o 等模型的开发者
- [[Anthropic]] — Claude 4、Claude 3.7/3.5 等模型的开发者
- [[Google]] — Gemini 2.5/2.0 的开发者
- [[Alibaba]] — Qwen3 系列的开发者

## 讨论的概念

- [[Context-Rot]] — 上下文腐烂现象：仅增加输入 token 长度就会导致 LLM 性能非均匀退化的现象
- [[Needle-in-a-Haystack]] — 经典的词汇匹配长上下文基准测试
- [[NoLiMa]] — 非词汇匹配的 NIAH 变体，需要模型推断潜在关联
- [[LongMemEval]] — 长上下文对话问答基准
- [[AbsenceBench]] — 测试模型识别文本缺失能力的基准
- [[Latent-List]] — 固定操作数、变化输入长度的 Python 列表操作任务
- [[Graphwalks]] — 图遍历任务，用于评估长上下文推理
- [[LLM-Judge]] — 使用对齐的 LLM 评估模型输出的方法
- [[YaRN]] — 上下文窗口扩展方法，本报告用于扩展 Qwen 模型

## 推荐参考文献

| # | 论文/资源 | 关联 |
|---|-----------|------|
| 1 | Kamradt (2023). Needle In A Haystack | 原始 NIAH 基准 |
| 2 | Wu et al. (2025). LongMemEval | 对话式长上下文评估 |
| 3 | Modarressi et al. (2025). NoLiMa | 非词汇匹配 NIAH 变体 |
| 4 | Fu et al. (2025). AbsenceBench | 文本缺失识别基准 |
| 5 | Vodrahalli et al. (2024). Michelangelo / Latent List | 固定复杂度、变化输入长度的评估 |
| 6 | Shi et al. (2023). Large Language Models Can Be Easily Distracted by Irrelevant Context | 干扰项对 LLM 的影响 |
| 7 | Peng et al. (2023). YaRN | 上下文窗口扩展 |

## 关联

- [[delta-mem-efficient-online-memory|δ-mem]] — 引用本文作为核心动机，论证简单扩展上下文窗口不能解决记忆问题
- [[LLMs-Get-Lost-in-Multi-turn]] — 互补工作，揭示多轮对话中 LLM 系统性"迷失"的问题
- [[Titans]] — 同样关注测试时记忆，提出将记忆作为模型架构的一等公民
- [[Memorizing-Transformers]] — 外部记忆方案，与 Context Rot 揭示的上下文不可靠性形成对比
