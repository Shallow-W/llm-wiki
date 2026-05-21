---
id: concept-nexau-framework
date: 2026-05-21
aliases: [NexAU]
tags: [概念]
---

# NexAU Framework

## 定义

[[Agentic-Harness-Engineering|AHE]] 论文提出的解耦 Agent harness 框架。将编码 Agent 的外部可编辑组件分为 7 种正交类型，每种以文件形式暴露在固定挂载点（如 `tools/*.md`、`middleware/*.md`），使 harness 对演化 Agent 可观察、可编辑、可版本控制。

## 关键属性

- **7 种组件类型**：System Prompt（`config/prompt.md`）、Tools（`tools/*.md`）、Middleware（`middleware/*.md`）、Skills（`skills/*.md`）、Sub-agent Configs（`subagents/*.md`）、Long-term Memory（`memory/*.md`）、Workflow（`workflow/*.md`）
- **文件化接口**：编辑 harness = 编辑文件
- **种子配置 NexAU0**：刻意最小化——仅 1 个 shell 执行工具，无中间件、技能、子 Agent
- **Git 原生**：diff、rollback、branch 均开箱可用

## 相关概念

- [[Harness-Agent-Harness|Harness]] — NexAU 管理的对象
- [[Component-Observability|组件可观测性]] — NexAU 实现的可观测性
- [[Model Context Protocol (MCP)]] — 同属工具接入标准，但 MCP 是运行时协议，NexAU 是设计时框架

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — §3.1
