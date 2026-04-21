---
id: concept-ai-aas
date: 2026-04-21
aliases: [AIaaS, AI as a Service, AI即服务]
tags: [概念]
---

# AI as a Service（AIaaS）

## 定义

在 6G 网络中提供 AI 服务的基础设施模式，用户无需自建 AI 系统即可获得延迟有保障的 AI 推理/训练服务。通过边-网-云三层架构统一调度通信、计算、数据和模型资源。

## 关键属性

- **延迟**：由通信延迟 + 排队延迟 + 计算延迟组成
- **能耗**：数据传输和 AI 计算产生显著能耗，需与延迟做权衡
- **异构计算**：不同任务需要不同类型的计算资源（CPU/GPU/TPU）
- **模型需求**：AI 任务需要将计算委托给具备充足资源的节点，涉及模型放置和选择
- **QoAIS**：AI 服务质量评估体系，补充传统 QoS 指标

## 相关概念

- [[任务卸载 (Task Offloading)]] — 将任务从边缘卸载到计算节点
- [[Lyapunov 优化]] — 分解 AIaaS 中的长期/短期优化问题
- [[M/M/C 排队模型]] — 分析 AIaaS 中的排队延迟

## 来源

- [[joint-task-offloading-resource-allocation-model-placement-6g|TSC 2024]] — 提出 6G 网络 AIaaS 框架
- [[gstc-zero-cost-proxy-nas|GSTC 论文]] — 引用 AIaaS 概念
