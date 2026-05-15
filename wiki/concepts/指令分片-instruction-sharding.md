---
id: concept-instruction-sharding
date: 2026-05-06
aliases: [分片, sharding, sharded instruction, sharded simulation]
tags: [概念, LLM评估, 多轮对话, 方法论]
---

# 指令分片（Instruction Sharding）

## 定义

指令分片是一种将完全指定的单轮指令拆分为一组较小指令单元（称为"分片"或 shards）的方法，使得这些分片的并集等价于原始指令的信息内容。分片用于模拟多轮欠规范对话——每轮对话最多揭示一个分片，从而实现信息在对话中的渐进式披露。

这一方法由 Laban, Hayashi, Zhou & Neville (2025) 在论文 [[llms-get-lost-in-multi-turn-conversation|LLMs Get Lost in Multi-turn Conversation]] 中提出，作为研究 [[对话迷失现象（lost-in-conversation）]] 的核心实验工具。

## 关键属性

### 五个必须满足的属性

| 属性 | 编号 | 说明 |
|------|------|------|
| 信息保持 | P1 | 分片联合不丢失原始指令的任何必要信息 |
| 明确初始意图 | P2 | 第一个分片定义高层目标（如"写一个 Python 函数"） |
| 顺序无关 | P3 | 除首分片外，其余分片可任意排列而不改变信息 |
| 最大分片 | P4 | 尽可能细粒度——每个分片只引入一条信息 |
| 最小变换 | P5 | 尽量保持原始用语，不过度解读或简化 |

### 数学定义

设 q 为原始完全指定指令，其原子内容单元为：

```
I(q) = [I, (c1, ..., cm)]
```

其中 I 是主要意图，(c1, ..., cm) 是充分说明细节。分片过程旨在构造：

```
q' = [s1, ..., sk] 使得 I(q) = I(q')
```

### 示例

原始指令（GSM8K）：
> Jay is making snowballs to prepare for a snowball fight with his sister. He can build 20 snowballs in an hour, but 2 melt every 15 minutes. How long will it take before he has 60 snowballs?

等效分片指令：
- Shard 1：How long before Jay's ready for the snowball fight?
- Shard 2：He's preparing for a snowball fight with his sister.
- Shard 3：He can make 20 snowballs per hour.
- Shard 4：He's trying to get to 60 total.
- Shard 5：The problem is that 2 melt every 15 minutes.

## 半自动分片流程

1. **分割**（Segmentation）：LLM 将原始指令拆分为非重叠的信息片段
2. **重述**（Rephrasing）：LLM 将每个片段重写为独立的、自然的对话单元
3. **验证**（Verification）：通过模拟实验验证 CONCAT 和 SHUFFLE-CONCAT 性能不低于 FULL 的 80%
4. **人工审核**（Inspect & Edit）：作者通过网页标注界面审核和编辑

每个任务平均需 3 小时人工审核，可产出约 100 条高质量分片指令。

## 五种对话模拟类型

| 类型 | 简写 | 信息披露方式 | 用途 |
|------|------|-------------|------|
| Fully-Specified | FULL | 单轮全部给出 | 基线 |
| Concatenated | CONCAT | 单轮但用分片拼接 | 验证重述无损 |
| Sharded | SHARDED | 多轮逐轮揭示 | 核心实验 |
| Recap | RECAP | SHARDED + 末轮总结 | 缓解策略评估 |
| Snowball | SNOWBALL | 每轮重复所有已揭示分片 + 新增一个 | 缓解策略评估 |

## 相关概念

- [[对话迷失现象（lost-in-conversation）]] — 分片方法揭示的核心现象
- [[能力-可靠性分解（aptitude-reliability）]] — 用于分析分片实验结果
- [[δ-mem（在线关联记忆）]] — 分片实验暴露的问题可由记忆机制缓解

## 来源

- [[llms-get-lost-in-multi-turn-conversation|LLMs Get Lost in Multi-turn Conversation]] — 提出此方法的原始论文
