---
id: concept-mcp
date: 2026-04-21
aliases: [MCP, Model Context Protocol, 模型上下文协议]
tags: [概念]
---

# Model Context Protocol (MCP)

## 定义
Anthropic 提出的开放标准协议，为 AI 模型提供与外部工具、数据源的统一连接接口。类似于"AI 的 USB-C 接口"——一个模型可以连接任意 MCP 兼容的服务。

## 关键属性
- **有状态交互**：MCP 服务器维护环境状态（数据库、文件系统等），Agent 的每次调用可能改变状态
- **标准化接口**：每个 MCP Server 提供 JSON 格式的工具定义（schema）和可执行接口
- **可组合性**：一个 Agent 可以同时连接多个 MCP Server，形成复杂的工作流
- **生态丰富**：已有数千个开源 MCP Server 覆盖各类场景（数据库、项目管理、浏览器自动化等）

## 相关概念
- [[Agent RL]] — MCP 环境为 Agent RL 提供真实交互基础
- [[Tool Graph]] — 在 MCP 工具集上构建依赖图用于任务合成

## 来源
- [[agent-world]] — 核心环境生态基于 MCP Server 规范构建

## 参见
- [MCP 官方文档](https://modelcontextprotocol.io/)
- Smithery（MCP Server 市场）：smithery.ai
