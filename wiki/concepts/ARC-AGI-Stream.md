---
id: concept-arc-agi-stream
date: 2026-05-20
aliases: [ARC-AGI Stream, ARC Stream testbed]
tags: [概念]
---

# ARC-AGI Stream

## 定义

由 [[useful-memories-become-faulty-when-continuously-updated-by-llms]] 论文提出的受控 Agent 记忆测试台。基于 ARCGEN 构建，结合三个在现有 Agent 基准中缺失的属性：完全已知的潜在任务分类、程序化 ground-truth、暴露的结构化记忆操作词表。

## 关键属性

- **6 族 × 7 技能**：族（Family）= 选择哪些对象参与变换的规则；技能（Skill）= 对选中对象施加的固定变换
- **6 族**：detect_color_property, detect_largest_objects_select, detect_key_marker_rule, group_by_shape_then_select, detect_inside_frame_relation, compose_horizontal
- **7 技能**：keep, border, recolor, translate, flip_horizontal, mark_center, hollow
- **双存储**：Episodic Buffer（原始 episode）+ Abstract Store（整合经验）
- **三种控制循环**：Force（强制整合）、Auto（模型自选）、Episodic Management Only（仅管理原始 episode）
- **两种轨迹机制**：GT（ground-truth 解法流式输入）+ Running（Agent 自行求解）

## 记忆操作词表

- **Retain**：将原始 episode 保留到 Episodic Buffer
- **Delete**：删除一条记忆条目
- **Consolidate**：将 Buffer 中的 episode 压缩为 Abstract Store 中的抽象经验

## 设计优势

- 使抽象错误可归因：已知族分类 + GT 解 → 失败可定位到整合步骤
- 支持族级覆盖分析、误分类计数、Buffer 组成分析
- 可审计每一步的记忆操作

## 相关概念

- [[Agent记忆整合]] — 测试台研究的核心过程
- [[情节性记忆（Agent）]] — 测试台中的 Episodic Buffer
- [[互补学习系统（Agent记忆）]] — 测试台的双存储设计

## 来源

- [[useful-memories-become-faulty-when-continuously-updated-by-llms]] — Section 3, Appendix A/B
