---
id: concept-jcqda
date: 2026-05-15
aliases: [Joint Communication and Queue-Aware Deployment Algorithm, 联合通信与队列感知部署算法]
tags: [概念]
---

# JCQDA

## 定义

Joint Communication and Queue-Aware Deployment Algorithm（联合通信与队列感知部署算法），是 [[gstc-zero-cost-proxy-nas|GSTC 论文]] 提出的静态部署启发式算法。在 M/M/C 排队理论框架下联合优化通信延迟和排队延迟，将 GSTC 筛选的架构与部署决策紧密耦合。

## 核心机制

1. **最小实例数计算**：基于 M/M/C 稳定性条件 $\rho_m^v < 1$，引入松弛因子 $\theta \geq 0$ 吸收突发流量
   $$N_m = \left\lceil (1+\theta)\frac{\lambda_m}{\mu_m} \right\rceil$$

2. **服务-服务器亲和度**：平衡同服务集中部署（降低排队延迟）与依赖服务共置（降低通信延迟）之间的冲突
   $$A_m^v = \alpha \cdot \text{Avail}_m^v + \beta \cdot \text{PS}_m^v$$

3. **贪心部署**：按 $N_m$ 降序排列服务，按亲和度降序排列服务器，逐服务器放置实例

## 关键属性

- 面向同构服务器集群的 NP-hard 部署问题
- 时间复杂度远低于精确求解，满足实时部署需求
- 与 [[LAMRA]] 形成"静态部署 → 动态调整"闭环

## 相关概念

- [[M/M/C 排队模型]] — JCQDA 的延迟建模基础
- [[零成本代理]] — GSTC 提供架构筛选输入
- [[LAMRA]] — 动态替换算法，与 JCQDA 互补
- [[微服务调用图]] — 服务链部署的目标结构

## 来源

- [[gstc-zero-cost-proxy-nas|GSTC 论文]] — Section 4.1
