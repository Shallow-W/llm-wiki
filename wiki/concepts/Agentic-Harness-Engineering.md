---
id: concept-agentic-harness-engineering
date: 2026-05-21
aliases: [AHE]
tags: [概念]
---

# Agentic Harness Engineering (AHE)

## 定义

一种通过三种可观测性（组件/经验/决策）驱动编码 Agent harness 自动闭环演化的框架。不修改 LLM 权重，而是优化 Agent 外部的可编辑组件集合（提示、工具、中间件、技能、子 Agent 配置、长期记忆）。

## 关键属性

- **三种可观测性支柱**：[[Component-Observability|组件可观测性]]、[[Experience-Observability|经验可观测性]]、[[Decision-Observability|决策可观测性]]
- **闭环流程**：rollout → clean → attribute → distill → evolve → commit（Algorithm 1）
- **仅推理，无训练**：不修改权重，只需 LLM 推理 + 文件编辑
- **可审计**：每次编辑附带 [[Change-Manifest|Change Manifest]] 预测声明
- **跨模型迁移**：在一个模型上演化的 harness 可直接迁移到其他模型（+5.1~+10.1pp）

## 核心结果

- Terminal-Bench 2：10 轮迭代从 27.0% → 34.3%（+7.3pp），超越所有人造和自演化基线
- 跨模型迁移：deepseek-v4-flash +10.1pp，gemini-3.1-flash-lite +5.1pp
- 跨基准迁移：SWE-bench-verified +3.6pp

## 相关概念

- [[Harness-Agent-Harness|Harness]] — AHE 的优化对象
- [[NexAU-Framework|NexAU]] — AHE 的 harness 基础设施
- [[Agent RL]] — 权重层面优化的互补方法
- [[LoRA]] — 另一种参数高效但权重层面的优化

## 来源

- [[agentic-harness-engineering|Agentic Harness Engineering]] — 提出该方法

## 参见

- [[agent0-bootstrapping-from-zero-data|Agent0]] — 权重层面的自演化
- [[metaclaw-continuous-evolution-in-production|MetaClaw]] — 生产环境持续进化
- [[evolver-from-trajectories-to-principles|EvolveR]] — 经验驱动自演化
