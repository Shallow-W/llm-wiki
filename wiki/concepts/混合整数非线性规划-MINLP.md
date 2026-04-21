---
id: concept-minlp
date: 2026-04-21
aliases: [MINLP, Mixed-Integer Nonlinear Programming, 混合整数非线性规划]
tags: [概念]
---

# 混合整数非线性规划（MINLP）

## 定义

同时包含整数决策变量（如是否在某节点部署实例）和连续决策变量（如资源分配量）的非线性优化问题。NP-hard 问题，通常需要启发式算法求解。

## 关键属性

- **整数变量**：部署决策、路由选择等离散决策
- **连续变量**：资源分配、概率参数等
- **求解方法**：启发式算法（贪心、遗传算法）、分解方法（Lyapunov、ADMM）、匹配理论
- **常见形式**：三篇论文中的联合优化问题均建模为 MINLP

## 在论文中的应用

- [[gstc-zero-cost-proxy-nas|GSTC 论文]] — 全生命周期联合优化建模为 MINLP
- [[joint-deployment-request-routing-microservice-tpds|TPDS 2023]] — JMDRP 问题建模为 MINLP，使用两阶段启发式求解
- [[joint-task-offloading-resource-allocation-model-placement-6g|TSC 2024]] — 两时间尺度 MINLP，使用 Lyapunov 优化分解

## 相关概念

- [[Lyapunov 优化]] — 分解 MINLP 的方法之一
- [[微服务调用图]] — MINLP 的主要应用场景
