---
id: concept-jackson-queuing-network
date: 2026-04-21
aliases: [Jackson Queueing Network, Jackson排队网络, 开放Jackson网络]
tags: [概念]
---

# Jackson 排队网络

## 定义

一类可解析求解的开放排队网络，网络中每个节点为 M/M/C 排队站，请求可在节点间流动。Jackson 定理保证其稳态解具有乘积形式，使端到端延迟可分解为各节点延迟之和。

## 关键属性

- **开放网络**：外部请求可进入和离开网络
- **乘积形式解**：稳态分布可分解为各节点独立分布的乘积
- **服务依赖建模**：不同微服务节点间的数据依赖可通过路由概率刻画
- **可解析性**：相比一般排队网络，Jackson 网络可高效计算性能指标

## 相关概念

- [[M/M/C 排队模型]] — Jackson 网络的基本组成单元
- [[微服务调用图]] — Jackson 网络的主要建模对象

## 来源

- [[joint-deployment-request-routing-microservice-tpds|TPDS 2023]] — 使用开放 Jackson 排队网络建模微服务调用图的延迟
