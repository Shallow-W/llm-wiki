---
id: concept-harness
date: 2026-05-21
aliases: [Harness]
tags: [概念]
---

# Harness（Agent Harness）

## 定义

编码 Agent 中**模型外部的可编辑组件集合**，包括系统提示、工具定义、中间件、技能模块、子 Agent 配置和长期记忆。Harness 是 Agent 与环境交互的中介层——它决定了 Agent "怎么做事"，而 LLM 决定"想什么"。

## 关键属性

- **7 种组件类型**：System Prompt、Tools、Middleware、Skills、Sub-agent Configs、Long-term Memory、Workflow
- **可编辑性**：通过 [[NexAU-Framework|NexAU]] 框架，每种组件以文件形式暴露
- **可版本控制**：文件化设计天然支持 git diff/rollback
- **非加性**：单组件改进之和（+11.1pp）不等于全组件改进（+7.3pp），存在冗余和冲突

## 组件消融发现

| 组件 | 单独移除影响 |
| --- | --- |
| Long-term Memory | −5.6pp（贡献最大） |
| Tools | −3.3pp |
| Middleware | −2.2pp |
| System Prompt | +2.3pp（反向！移除反而提升） |

## 相关概念

- [[Agentic-Harness-Engineering|AHE]] — 自动优化 harness 的方法
- [[NexAU-Framework|NexAU]] — harness 的文件化框架

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — 提出此概念的形式化定义
