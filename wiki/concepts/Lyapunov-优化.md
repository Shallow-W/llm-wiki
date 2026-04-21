---
id: concept-lyapunov-optimization
date: 2026-04-21
aliases: [Lyapunov Optimization, Lyapunov优化]
tags: [概念]
---

# Lyapunov 优化

## 定义

一种将长期随机优化问题分解为一系列短期确定性子问题的方法。通过构建李雅普诺夫漂移函数，将队列稳定性约束转化为每时间步的漂移惩罚，从而避免对未来统计信息的依赖。

## 关键属性

- **长期问题**：模型放置、服务缓存等需要跨多个时间步决策
- **短期问题**：任务卸载、资源分配等需要在每个时间步即时决策
- **漂移最小化**：在漂移惩罚和目标函数之间取得权衡
- **在线优化**：无需未来信息的先验知识，适合动态场景

## 相关概念

- [[AI as a Service (AIaaS)]] — Lyapunov 优化用于分解 AIaaS 中的两时间尺度问题
- [[多臂老虎机 (MAB)]] — 与 Lyapunov 配合用于长期模型放置探索

## 来源

- [[joint-task-offloading-resource-allocation-model-placement-6g|TSC 2024]] — 使用 Lyapunov 优化分解长期模型放置与短期任务调度
