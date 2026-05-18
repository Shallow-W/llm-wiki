---
id: concept-lamra
date: 2026-05-15
aliases: [Load-Aware Model Replacement Algorithm, 负载感知模型替换算法]
tags: [概念]
---

# LAMRA

## 定义

Load-Aware Model Replacement Algorithm（负载感知模型替换算法），是 [[gstc-zero-cost-proxy-nas|GSTC 论文]] 提出的动态模型替换算法。在负载波动时，从 GSTC 预评估的架构库中选择合适的模型版本进行替换，同步更新 [[JCQDA]] 部署方案。

## 核心计算流程

1. **推理速度阈值筛选**：根据当前部署实例数和实时系统负载计算满足目标 QoS 的最小推理速度 $\mu_m^{\min}$，筛除不满足的版本
2. **Pareto 前沿选择**：对剩余版本按服务速率 $\mu_{m,k}$、服务效率 $q_{m,k}$ 和 GPU 内存消耗 $C_{m,k}^{\text{GPU}}$ 三维进行 Pareto 最优筛选
3. **加权评分替换**：
   $$\text{score}_{m,k} = \alpha \mu_{m,k} + \beta \cdot \text{GSTC}_{m,k} + \gamma C_{m,k}^{\text{GPU}}$$
   选择评分最高的版本替换当前部署版本

## 关键属性

- 每个逻辑服务支持多版本共存和可替换性
- GSTC 预评估库的存在使版本选择无需训练
- 部署参数同步更新，避免替换带来的部署不当延迟
- 在大规模网络中延迟比基线降低 88.5%-94.7%

## 相关概念

- [[JCQDA]] — 静态部署算法，为 LAMRA 提供部署基础
- [[零成本代理]] — GSTC 提供预评估架构库
- [[M/M/C 排队模型]] — 排队稳定性约束

## 来源

- [[gstc-zero-cost-proxy-nas|GSTC 论文]] — Section 4.2
