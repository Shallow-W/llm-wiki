---
id: entity-nexau
date: 2026-05-21
aliases: []
tags: [实体, 框架, Agent系统]
---

# NexAU

## 概述

Agentic Harness Engineering (AHE) 论文提出的解耦 Agent harness 框架。将编码 Agent 的外部可编辑组件解耦为 7 种正交类型，每种以文件形式暴露在固定挂载点，使 harness 对演化 Agent 可观察、可编辑、可版本控制。

## 关键事实

- 来源论文：[[agentic-harness-engineering|AHE]]
- 组件类型：System Prompt、Tools、Middleware、Skills、Sub-agent Configs、Long-term Memory、Workflow
- 设计原则：编辑 harness = 编辑文件，天然支持 git diff/rollback
- 种子配置（NexAU0）：刻意最小化——仅 1 个 shell 执行工具

## 在来源中的出现

- [[agentic-harness-engineering]] — AHE 的 harness 基础设施层

## 关系

- [[Agentic-Harness-Engineering|AHE]] — 使用 NexAU 作为 harness 框架
- [[Model Context Protocol (MCP)]] — 同属 Agent 工具生态标准，但层次不同
