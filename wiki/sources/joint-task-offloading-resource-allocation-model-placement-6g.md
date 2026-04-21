---
id: source-joint-task-offloading-resource-allocation-model-placement-6g
date: 2026-04-21
source: raw/articles/贪心分配异构资源，将服务实例部署在资源利用率最低的节点；路由时始终选择当前位置最近的节点转发请求，追求局部最优资源分配与路由效率。.pdf
type: 论文
tags: [6G网络, AIaaS, 任务卸载, 资源分配, 模型放置, Lyapunov优化]
---

# Joint Task Offloading, Resource Allocation and Model Placement for AI as a Service in 6G Network

## 一句话总结

提出边-网-云三层 AIaaS 框架下的两时间尺度优化方法，利用 Lyapunov 优化分解长期模型放置与短期任务卸载，通过 DA-MAB 策略实现低复杂度在线联合优化。

## 关键要点

- **核心问题**：6G 网络中 CPU 计算任务与 GPU AI 任务并存，模型放置（长期策略）与任务调度（短期策略）深度耦合
- **系统架构**：边-网-云三层 AIaaS 框架，包含服务分割管理器、任务卸载管理器、模型放置管理器等可配置功能单元
- **问题分解**：使用 Lyapunov 优化将长期系统稳定性问题分解为短期确定性子问题
- **DA-MAB 策略**：
  - 短期：延迟接受（DA）算法实现任务卸载 + 凸优化实现资源分配
  - 长期：多臂老虎机（MAB）定期评估模型放置策略
- **异构计算**：考虑 CPU/GPU 异构计算需求，支持模型剪枝、早退等不同变体的部署
- **实验效果**：在 Atlanta 拓扑（15 计算节点）和 ta2 拓扑（65 计算节点）上优于 Greedy、PSO、PPO 基线

## 提及的实体

- [[Yong Zhang]] — 通讯作者，北京邮电大学
- [[Yuhao Chai]] — 第一作者，北京邮电大学
- [[北京邮电大学]] — 主要研究机构
- [[中国移动研究院]] — 合作机构

## 讨论的概念

- [[AI as a Service (AIaaS)]] — 本文核心框架概念
- [[任务卸载 (Task Offloading)]] — 将任务从边缘节点卸载到计算节点
- [[Lyapunov 优化]] — 用于分解长期/短期优化问题
- [[延迟接受算法 (Deferred Acceptance)]] — 任务卸载决策
- [[多臂老虎机 (MAB)]] — 模型放置探索策略
- [[混合整数非线性规划 (MINLP)]] — 原始问题的建模形式

## 关联

- 被 [[gstc-zero-cost-proxy-nas|GSTC]] 引用，作为 AIaaS 领域相关工作
- 与其他两篇论文共享微服务/AI 服务部署优化的主题

## 状态

- 已发表：IEEE TSC, Vol. 17, No. 6, pp. 3830–, Nov/Dec 2024
- DOI: 10.1109/TSC.2024.3451170
- 有补充材料：https://doi.org/10.1109/TSC.2024.3451170
