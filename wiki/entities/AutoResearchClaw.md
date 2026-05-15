---
id: entity-autoresearchclaw
date: 2026-05-06
aliases: [AutoResearchClaw]
tags: [实体, 开源项目, 研究自动化, Agent流水线]
---

# AutoResearchClaw

## 概述
AutoResearchClaw 是一个完全自主的 23 阶段研究流水线，能将单个研究想法转化为会议级论文。覆盖文献搜索、假设生成、实验设计、代码合成、沙箱执行、结果分析、论文起草和多 Agent 同行评审。在 MetaClaw 论文中作为跨域泛化评估基准。

## 关键事实
- 类型：自主研究自动化流水线
- 阶段数：23 个阶段（其中 19 个可评分）
- 代码仓库：https://github.com/aiming-lab/AutoResearchClaw
- 核心能力：文献搜索 → 假设生成 → 实验设计 → 代码合成 → 沙箱执行 → 结果分析 → 论文起草 → 多 Agent 同行评审
- 评估指标：阶段重试率、精炼循环数、流水线阶段完成数、复合鲁棒性分数

## 在来源中的出现
- [[metaclaw-continuous-evolution-in-production]] — 作为跨域评估基准，验证 MetaClaw 技能注入在开放式多阶段 Agent 工作流上的泛化能力

## 关系
- [[OpenClaw]] — 同一生态系统的 Agent 平台
- [[UNC-Chapel-Hill]] — 主要研发机构
- [[Jiaqi-Liu]] — AutoResearchClaw 的主要作者
