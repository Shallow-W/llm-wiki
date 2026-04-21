---
id: source-agent-world
date: 2026-04-21
source: raw/papers/2604.18292.pdf
type: 论文
tags: [Agent, RL, MCP, 环境合成, 自我进化]
---

# Agent-World: Scaling Real-World Environment Synthesis for Evolving General Agent Intelligence

## 一句话总结
提出 Agent-World，一个通过大规模真实环境合成 + 持续自我进化训练来提升通用 Agent 智能的训练平台，用 8B/14B 模型在 23 个 Agent benchmark 上超越闭源模型。

## 关键要点

### 核心问题
- 现有 Agent 训练受限于**缺乏真实交互环境**和**缺乏持续进化机制**
- 模拟环境（LLM 当世界模型）容易产生幻觉，偏离真实动力学
- 已有真实环境要么规模太小，要么只做单轮训练，无法持续改进

### 方法（两大组件）

**组件一：Agentic Environment-Task Discovery（环境-任务发现）**
- 从 3 个来源收集环境主题：MCP Servers（~2.8K）、工具文档（~0.5K）、工业 PRD（~0.2K）
- **数据库挖掘**：用 deep-research agent 自动从 Web 采掘主题对齐的结构化数据库，并通过迭代复化（complexification）提升复杂度
- **工具生成与验证**：用 coding agent 为每个数据库生成可执行 Python 工具，通过沙箱交叉验证（编译检查 + 测试通过率 > 50%）筛选
- 最终产出：**1,978 个环境、19,822 个工具**，覆盖 20 个一级分类、50 个二级分类

**组件二：Continuous Self-Evolving Agent Training（持续自我进化训练）**
- 基于 GRPO 的**多环境 Agent RL**，在 agent-tool-database 闭环中训练
- **结构化可验证奖励**：图任务用 rubric-conditioned LLM judge，程序任务用沙箱执行验证脚本
- **自我进化竞技场**：每轮动态合成评估任务 → 诊断 agent 分析失败模式 → 针对性扩展弱项环境 → 继续 RL，形成 agent-环境协同进化闭环

### 任务合成（两种互补策略）
1. **图基合成（Graph-based）**：构建工具依赖图，随机游走生成调用序列，逆向工程出任务描述
2. **程序合成（Programmatic）**：直接生成包含循环/条件分支的 Python 解法脚本 + 验证脚本，支持非线性推理

### 关键实验结果
- **Agent-World-8B** 在 MCP-Mark 8.9%、BFCL V4 51.4%、2-Bench 61.8%
- **Agent-World-14B** 进一步提升，在 BFCL V4 上超越 DeepSeek-V3.2-685B（55.8% vs 54.1%）
- 环境规模缩放：0→2000 环境使平均分从 18.4% 提升到 38.5%（+20.1%）
- 自我进化：2 轮进化使 MCP-Mark 从 29.5% 提升到 38.1%（+8.6%）
- **23 个 benchmark 全面测试**，涵盖工具调用、AI 助手、软件工程、深度搜索、通用推理

## 提及的实体
- [[中国人民大学]] — 第一作者单位
- [[字节跳动 Seed]] — 合作单位
- [[董冠廷]] — 第一作者 / 通讯作者
- [[窦志成]] — 通讯作者

## 讨论的概念
- [[Model Context Protocol (MCP)]] — Agent 连接外部工具的统一协议，本文环境生态的核心标准
- [[GRPO]] — Group Relative Policy Optimization，本文使用的 RL 算法
- [[POMDP]] — 部分可观测马尔可夫决策过程，Agent 交互的数学建模框架
- [[Agent RL]] — Agent 强化学习，利用环境反馈优化 Agent 策略
- [[Tool Graph]] — 工具依赖图，用于图基任务合成中的随机游走

## 关联
- 与 [[微服务部署与路由优化概览]] 中的排队论建模不同，本文用 POMDP 建模 Agent-环境交互
- GRPO 优化方法与 [[Lyapunov 优化]] 同为在线优化技术，但应用场景不同（RL 策略优化 vs 稳定队列控制）

## 原始笔记

### 形式化定义
- 环境 = (数据库 D, 工具集 F)
- 状态 = 环境状态 × 对话状态
- 动作 = 工具调用 | 语言响应
- 观测 = 工具结构化输出 | 对话语境

### 缩放规律
- 环境数量 10→100→500→2000 对应性能三阶段：快速提升→稳定提升→边际递减
- 自我进化第一轮修复模式级错误，第二轮修复长链复杂交互残留问题
