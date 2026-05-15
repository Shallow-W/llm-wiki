---
id: entity-mem0
date: 2026-05-06
aliases: [Mem0, Letta]
tags: [实体, 公司, AI记忆, Agent基础设施]
---

# Mem0（公司/产品）

## 概述

Mem0 是一家专注于 AI Agent 记忆基础设施的公司（后更名为 Letta），提供可扩展的长期记忆解决方案。其核心产品是一个开源的记忆层，允许 LLM 驱动的 Agent 在跨会话对话中保持连贯性和个性化。

## 关键事实

- **成立时间**：约 2023-2024
- **创始人**：Deshraj Yadav 等
- **核心产品**：Mem0 记忆平台（开源）
- **技术定位**：LLM 之上的记忆层，模型无关
- **更名**：后更名为 Letta，继续开发 Agent 记忆和操作系统技术
- **官网**：https://mem0.ai

## 核心团队

| 成员 | 角色 | 背景 |
|------|------|------|
| **Deshraj Yadav** | 联合创始人/CEO | 原 Facebook AI Research，视觉+语言方向 |
| **Prateek Chhikara** | 研究/工程 | 论文共同一作，Agent 记忆方向 |
| **Dev Khant** | 研究/工程 | 论文作者 |
| **Saket Aryan** | 研究/工程 | 论文作者 |
| **Taranjeet Singh** | 研究/工程 | 论文作者 |

## 技术贡献

1. **Mem0 架构**：文本级记忆提取 + 向量检索 + LLM 判断更新
2. **Mem0g 架构**：在 Mem0 基础上增加图记忆（Neo4j），显式建模实体关系
3. **LOCOMO 基准评估**：系统对比 6 类基线，全面领先
4. **生产级优化**：91% 延迟降低、90%+ token 成本节省

## 产品形态

- **开源库**：Python SDK，支持多种向量数据库
- **云平台**：托管记忆服务
- **集成**：与主流 LLM 框架（LangChain, LlamaIndex 等）兼容

## 在来源中的出现

- [[mem0-building-production-ready-ai-agents]] — 公司团队发表的研究论文
- [[delta-mem-efficient-online-memory]] — δ-mem 论文将 Mem0 作为文本记忆基线对比

## 关系

- [[Letta]] — 品牌更名后的实体
- [[OpenAI]] — 竞争对手（ChatGPT memory 功能）
- [[Zep]] — 竞争对手（商业记忆平台）
- [[LangChain]] — 生态合作伙伴
- [[Neo4j]] — 技术合作伙伴（图数据库）
