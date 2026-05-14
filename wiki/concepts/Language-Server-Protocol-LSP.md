---
id: concept-language-server-protocol
date: 2026-05-14
aliases: [LSP]
tags: [概念, 开发工具, 协议]
---

# Language Server Protocol (LSP)

## 定义

Language Server Protocol（LSP）是一个开放的、基于 JSON-RPC 的通信协议，用于标准化**代码编辑器/IDE**（客户端）与**语言服务器**（服务端）之间的交互。它将语言智能功能（如代码补全、跳转定义、诊断、重构等）从编辑器中解耦出来，使"写一次语言服务器，所有编辑器通用"成为可能。

LSP 由 Microsoft 于 2016 年随 Visual Studio Code 首次提出，随后与 Red Hat、Codenvy（现 Eclipse Che）共同推进标准化，目前在 GitHub 上维护规范，最新版本为 3.17。

## 核心架构：解耦的 M×N 问题

在 LSP 出现之前，语言支持面临一个 **M × N 问题**：

- M 种编程语言 × N 种编辑器 = 需要 M × N 套适配实现
- 每个编辑器都要为每种语言写一套插件，每种语言也要为每个编辑器做适配

LSP 通过引入标准协议将其简化为 **M + N 问题**：

- M 种语言各实现一个 Language Server
- N 种编辑器各实现一个 LSP Client
- 双方通过统一的 LSP 协议通信

```
┌─────────────┐     LSP (JSON-RPC)     ┌──────────────────┐
│             │ ◄────────────────────► │                  │
│  编辑器/IDE  │    请求 / 响应 / 通知    │  Language Server  │
│  (Client)   │ ◄────────────────────► │  (Server)        │
│             │                        │                  │
└─────────────┘                        └──────────────────┘
     VS Code                                TypeScript LS
     Neovim                                 Rust Analyzer
     Emacs                                  gopls (Go)
     JetBrains                              pylsp (Python)
     ...
```

## 通信机制

### 消息格式

LSP 使用 **JSON-RPC 2.0** 作为消息格式，消息前缀类似 HTTP 的 header。三类消息：

| 类型 | 方向 | 说明 | 示例 |
|------|------|------|------|
| **Request** | Client → Server | 客户端请求，服务端必须回复 | `textDocument/completion` |
| **Response** | Server → Client | 对 Request 的响应 | 返回补全列表 |
| **Notification** | 双向 | 单向通知，无需回复 | `textDocument/didChange` |

### 生命周期

1. **初始化**（`initialize`）：客户端发送初始化请求，声明自身能力和项目根路径（workspace root）；服务端回复自身支持的功能列表。
2. **运行中**：客户端同步文档变更（`didOpen`、`didChange`、`didClose`），并向服务端请求语言服务；服务端主动推送诊断信息（`textDocument/publishDiagnostics`）。
3. **关闭**（`shutdown` + `exit`）：客户端通知服务端清理并退出。

### 传输方式

协议本身不规定传输机制。常见方式：

- **stdio**：最常用，编辑器作为父进程启动 Language Server，通过标准输入/输出通信。
- **Socket**：TCP/UNIX socket，适用于远程场景。
- **Node.js IPC**：VS Code 常用方式。

## 核心语言功能

LSP 覆盖的语言智能功能远不止"高亮"，主要分为以下几类：

### 编辑辅助

| 功能 | LSP 方法 | 说明 |
|------|----------|------|
| 代码补全 | `textDocument/completion` | 根据上下文提供候选补全项 |
| 悬停信息 | `textDocument/hover` | 光标处符号的文档、类型签名 |
| 签名帮助 | `textDocument/signatureHelp` | 函数调用时的参数提示 |

### 导航

| 功能 | LSP 方法 | 说明 |
|------|----------|------|
| 跳转定义 | `textDocument/definition` | 跳转到符号的定义位置 |
| 跳转类型定义 | `textDocument/typeDefinition` | 跳转到类型定义 |
| 跳转实现 | `textDocument/implementation` | 跳转到接口/抽象类的实现 |
| 查找引用 | `textDocument/references` | 查找符号在整个项目中的所有引用 |
| 符号搜索 | `workspace/symbol` | 在整个工作区搜索符号 |

### 诊断与修复

| 功能 | LSP 方法 | 说明 |
|------|----------|------|
| 错误/警告诊断 | `textDocument/publishDiagnostics` | 服务端主动推送语法和语义错误 |
| 代码操作 | `textDocument/codeAction` | 提供快速修复建议（如自动导入、修复错误） |
| 代码镜头 | `textDocument/codeLens` | 在代码行内显示可操作的提示（如"显示引用数"） |

### 重构

| 功能 | LSP 方法 | 说明 |
|------|----------|------|
| 重命名 | `textDocument/rename` | 安全地重命名符号，自动处理所有引用 |
| 格式化 | `textDocument/formatting` | 按规则格式化整个文档或选定范围 |
| 组织导入 | `textDocument/codeAction` | 自动排序、删除未使用的 import |

### 语义级功能

| 功能 | LSP 方法 | 说明 |
|------|----------|------|
| 语义高亮 | `textDocument/semanticTokens/full` | 基于语义的精确着色（区分同名的不同实体） |
| 文档符号 | `textDocument/documentSymbol` | 文档的符号大纲（函数、类、变量） |
| 折叠范围 | `textDocument/foldingRange` | 代码折叠区域 |

> [!note] 语法高亮 vs 语义高亮
> **基础语法高亮**（keywords、strings、comments 的着色）通常由编辑器通过 TextMate Grammar 或 tree-sitter 完成，**不经过 LSP**。
> LSP 的 `semanticTokens` 提供的是**语义级高亮**——例如区分同名的局部变量和全局变量、区分类型引用和函数调用等。这是更精确但更耗时的功能。

## 与 MCP 的类比

| 维度 | LSP | MCP（Model Context Protocol） |
|------|-----|------|
| 连接对象 | 编辑器 ↔ 语言服务器 | AI 助手 ↔ 外部工具/数据源 |
| 核心目的 | 提供语言智能服务 | 为 AI 提供上下文和工具调用能力 |
| 协议格式 | JSON-RPC | JSON-RPC |
| 发起方 | Microsoft | Anthropic |
| 本质 | 解耦编辑器与语言分析 | 解耦 AI 模型与外部世界 |

参见 [[Model-Context-Protocol-MCP]]

## 关键属性

- **语言无关**：不限于编程语言，也适用于 DSL、配置文件、规格说明等任何文本语言。
- **编辑器无关**：一个 Language Server 可以同时服务 VS Code、Neovim、Emacs、JetBrains 等。
- **渐进增强**：服务器不需要实现所有功能，通过 `capabilities` 声明自己支持哪些特性。
- **增量同步**：文档变更以增量方式传递（类似 diff），而非每次发送全文，减少通信开销。
- **工作区级别**：Language Server 可以理解整个项目结构，而不仅仅是单个文件。

## 常见 Language Server 实现举例

| 语言 | Language Server | 说明 |
|------|----------------|------|
| TypeScript/JS | `tsserver` (内置) / `typescript-language-server` | VS Code 内置，最成熟的实现之一 |
| Rust | `rust-analyzer` | 社区公认最优秀的 LS 实现之一 |
| Go | `gopls` | 官方维护 |
| Python | `pylsp` / `pyright` / `ruff-lsp` | 多个竞争实现 |
| C/C++ | `clangd` | LLVM 项目维护 |
| Java | `jdtls` (Eclipse) | Eclipse 基金会维护 |
| CSS/HTML | `vscode-css-languageserver` / `vscode-html-languageserver` | VS Code 团队维护 |

## 局限性

- **性能瓶颈**：大型项目中，Language Server 需要索引全部代码，启动时间和内存占用可能较高。
- **协议复杂度**：规范庞大（3.17 版本已非常复杂），实现完整规范的工作量不小。
- **实时性挑战**：编辑过程中需要快速响应，但完整语义分析可能耗时，需要增量解析和缓存策略。
- **非文本信息有限**：LSP 主要面向文本文件，对可视化、调试等场景支持有限（调试有单独的 DAP——Debug Adapter Protocol）。
- **跨文件一致性**：多文件编辑时，不同 Language Server 之间的协作没有统一规范。

## 来源

- [Language Server Protocol 官方规范（Microsoft）](https://microsoft.github.io/language-server-protocol/)
- [Language Server Protocol - Wikipedia](https://en.wikipedia.org/wiki/Language_Server_Protocol)

## 参见

- [[Model-Context-Protocol-MCP]] — 同样基于 JSON-RPC 的协议，用于 AI 与外部工具通信
- [Debug Adapter Protocol (DAP)](https://microsoft.github.io/debug-adapter-protocol/) — Microsoft 推出的类似思路的调试协议
