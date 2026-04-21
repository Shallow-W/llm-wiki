---
id: source-gstc-zero-cost-proxy-nas
date: 2026-04-21
source: raw/articles/GSTC(MMC)_1.23.pdf
type: 论文
tags: [NAS, 零成本代理, 微服务部署, M/M/C, 动态替换]
---

# Zero-Cost Proxy NAS-Driven Collaborative Deployment Optimization for the Full Lifecycle of AI Services

## 一句话总结

提出基于信息量量化编码的 GSTC 零成本代理模型，联合 JCQDA 部署算法与 LAMRA 动态替换算法，实现 AI 服务从架构设计到动态运行的全生命周期协同优化。

## 关键要点

- **核心问题**：现有 NAS 与实际部署脱节、零成本代理缺乏部署导向指标、模型缺乏动态场景适应能力
- **GSTC 代理**：从四个维度（G/S/T/C）量化神经网络信息传播效率，无需训练即可评估架构性能与部署需求
- **JCQDA 算法**：基于 M/M/C 排队模型精细刻画通信、排队、处理延迟，引入服务-服务器亲和机制平衡排队延迟与通信延迟
- **LAMRA 算法**：实时监控负载波动，结合 GSTC 预评估库和 Pareto 前沿分析进行模型动态替换
- **实验效果**：LAMRA 在小规模网络中 GPU 节省超过 55%（相比 MDSGA 达 82.5%），中规模 49.3%–75.4%，大规模 44.9%–72.9%

## 提及的实体

- [[Menglan Hu]] — 通讯作者，华中科技大学
- [[Kai Peng]] — 华中科技大学教授
- [[Yi Hu]] — 华中科技大学博士生
- [[华中科技大学]] — 主要研究机构

## 讨论的概念

- [[神经架构搜索 (NAS)]] — 自动化模型设计的核心方法
- [[零成本代理]] — GSTC 的核心创新，无需训练评估架构
- [[M/M/C 排队模型]] — JCQDA 算法用于延迟建模
- [[微服务调用图]] — AI 服务的部署单元组织方式
- [[混合整数非线性规划 (MINLP)]] — 问题的数学建模形式

## 关联

- 与 [[joint-deployment-request-routing-microservice-tpds|TPDS 2023]] 同一研究组，本文是其全生命周期扩展
- 引用了 [[joint-task-offloading-resource-allocation-model-placement-6g|TSC 2024]] 的 AIaaS 框架
- 三个算法（GSTC + JCQDA + LAMRA）构成"零成本评估 → 静态部署 → 动态调整"端到端流水线

## 状态

- 投稿中/预印本（根据文件名推断）
- 已完成理论分析（性能界、拉格朗日对偶间隙）和实验验证
