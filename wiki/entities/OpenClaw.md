---
id: entity-openclaw
date: 2026-05-06
aliases: [OpenClaw]
tags: [实体, 开源项目, Agent平台]
---

# OpenClaw

## 概述
OpenClaw 是一个开源的个人 AI 助手/CLI Agent 平台，可连接 20+ 消息通道，支持多种 LLM 后端。是 MetaClaw 持续元学习框架的部署载体和实验平台。

## 关键事实
- 类型：开源 CLI Agent 平台
- 代码仓库：https://github.com/openclaw/openclaw
- 核心特性：连接 20+ 消息通道，支持多种 LLM 提供商（Claude、OpenAI、Gemini、Qwen、Kimi 等）
- 支持的 LLM 后端：Claude、OpenAI、Gemini、OpenRouter、Qwen、Kimi、MiniMax、Azure、vLLM、SGLang 等
- 支持的个人 Agent 变体：IronClaw、CoPaw、PicoClaw、ZeroClaw、NanoClaw、NemoClaw 等

## 在来源中的出现
- [[metaclaw-continuous-evolution-in-production]] — MetaClaw 的部署平台和生产环境；MetaClaw-Bench Part I 基于 OpenClaw 的真实 CLI 任务构建
- [[openclaw-rl-turning-daily-usage-into-training-signals|OpenClaw-RL]] — OpenClaw-RL 框架的主要实验平台。论文模拟了学生、TA、教师三种职业用户使用 OpenClaw 的场景，验证了约 10 个 session 即可通过日常交互实现对齐个人偏好的效果

## 关系
- [[AutoResearchClaw]] — 同一生态系统内的自主研究流水线工具
- [[UNC-Chapel-Hill]] — 主要研发机构（Aiming Lab）
- [[Peng-Xia]] — 核心贡献者
- [[Huaxiu-Yao]] — 项目负责人
- [[Gen-Verse]] — OpenClaw-RL 论文的发布组织
- [[Yinjie-Wang]] — OpenClaw-RL 共同第一作者
- [[Ling-Yang]] — OpenClaw-RL 通讯作者
- [[Mem0]] — 记忆框架对比基线（OpenClaw-RL 实验）
- [[Cognee]] — 知识图谱记忆对比基线（OpenClaw-RL 实验）
- [[Qwen]] — OpenClaw-RL 使用的基座模型族
