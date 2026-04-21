---
id: concept-mmc-queuing-model
date: 2026-04-21
aliases: [M/M/C Queue, M/M/C排队模型]
tags: [概念]
---

# M/M/C 排队模型

## 定义

经典排队论模型：到达过程服从泊松分布（M）、服务时间服从指数分布（M）、系统有 C 个并行服务台。用于刻画多服务台并行处理请求的排队行为。

## 关键属性

- **排队延迟**：请求在队列中等待服务的时间
- **处理延迟**：服务台处理请求的时间
- **通信延迟**：请求在不同服务台/节点间传输的时间
- **端到端延迟**：排队 + 处理 + 通信延迟之和
- **利用率**：服务台繁忙时间占总时间的比例

## 在论文中的应用

- [[gstc-zero-cost-proxy-nas|GSTC 论文]]：JCQDA 算法使用 M/M/C 模型精细刻画延迟，并引入服务-服务器亲和机制
- [[joint-deployment-request-routing-microservice-tpds|TPDS 2023]]：使用开放 Jackson 排队网络（M/M/C 的推广）建模微服务调用图

## 相关概念

- [[Jackson 排队网络]] — 开放式多节点排队网络
- [[微服务调用图]] — 排队模型的主要应用场景
- [[AI as a Service (AIaaS)]] — 6G 网络中用排队模型分析 AI 服务延迟
