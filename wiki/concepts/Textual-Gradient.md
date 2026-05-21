---
id: concept-textual-gradient
date: 2026-05-21
aliases: [文本梯度]
tags: [概念]
---

# 文本梯度（Textual Gradient）

## 定义

[[Multi-agent-Architecture-Search|MaAS]] 中用于更新不可微算子的机制。由于 Agent 算子包含黑箱工具调用和自然语言 prompt，无法用传统反向传播计算梯度。文本梯度用 LLM 生成自然语言形式的"梯度分析"，指导算子的更新。

## 关键属性

- **三层梯度**：
  - TP（Prompt Gradient）：更新 prompt 内容
  - TT（Temperature Gradient）：调整 LLM 温度参数
  - TN（Node Gradient）：修改算子节点结构（合并/拆分/替换）
- **LLM 生成**：由专门的 gradient agent 根据执行反馈生成梯度建议
- **不可微环境的梯度近似**：将数值梯度转化为语义上的改进方向

## 示例

- "给 debate 算子添加过渡提示以提高连贯性"
- "降低 ensemble LLM 的温度以提高稳定性"
- "将 testing 算子拆分为单元测试和集成测试两个节点"

## 相关概念

- [[Multi-agent-Architecture-Search|MaAS]] — 使用文本梯度的方法
- [[Agentic-Supernet|Agentic Supernet]] — 文本梯度更新的对象

## 来源

- [[multi-agent-architecture-search-via-agentic-supernet|MaAS]] — §3.3, Eq. 12
