---
id: concept-policy-catalog
date: 2026-05-06
aliases: [策略目录, 策略编目, policy-population serving, 可寻址目录]
tags: [概念]
---

# Policy Catalog（策略目录/编目）

## 定义

Policy Catalog 是 [[mint-managed-infrastructure-training-serving-millions-llms|MinT]] 论文中描述的一种策略种群管理模式：将大量已导出的 LoRA 适配器修订版组织为一个可寻址目录（addressable catalog），通过分层缓存机制（持久目录 → CPU 缓存 → GPU batch）在可寻址性和执行性能之间取得平衡，使得单个服务集群能够管理百万级策略而每个引擎仅维护有界的活跃工作集。

## 关键属性

### 三层缓存架构

| 层级 | 规模 | 生命周期 | 提升/驱逐机制 |
|------|------|----------|--------------|
| **可寻址目录**（Addressable Catalog） | $10^3$–$10^6$ 条目 | 持久（控制平面） | 适配器导出时提升；手动退役 |
| **CPU 适配器缓存** | 每引擎数百个 | 每次 actor 运行 | 路由或缓存未命中加载时提升；内存压力下 LRU 驱逐 |
| **GPU batch** | $\leq 64$ 个不同适配器 | 一个解码步 | batch 调度器提升；步结束时释放 |

### 核心分离：可寻址性 ≠ 同时驻留

Policy Catalog 的关键设计洞察是**将"能命名多少策略"和"同时活跃多少策略"分离**：

- 目录规模（$10^6$）是**可寻址性**，不是同时 GPU 驻留
- CPU 缓存规模（数百）是**局部性吸收**
- GPU batch 规模（$\leq 64$）是**同时执行**

### 冷加载作为服务工作

当请求选择不在本地缓存的策略时：

1. 从共享存储获取适配器张量
2. 构建 loader 对象
3. 向引擎注册适配器
4. 激活后开始解码
5. 相同缺失策略的并发请求**共享一个加载**（去重）
6. 不同缺失策略**各自独立加载**（序列化，形成阶梯延迟）

MinT 将冷加载视为**带去重和有界反压的计划服务工作**，而非被动缓存未命中。

### 实测数据

| 资源层 | 实测边界 |
|--------|----------|
| 目录扫描 | 1K → 100K 条目，warm/cold 分裂持续存在 |
| CPU 缓存（重复 hotset） | 369 个加载适配器 @ 512-hotset，p95 37.13 s |
| CPU 缓存（弱局部性） | 550 个加载适配器 @ 2048-unique，p95 63.14 s |
| GPU batch | 64 个不同适配器 |
| 冷加载阶梯 | 1.375 s → 23.267 s（16 个不同适配器，约 1.35-1.40 s/适配器） |

### 集群规模容量规划

基于单引擎限制外推至 $10^6$ 策略目录：

- 2300 不同适配器活跃波 → 36 引擎（144 GPU）
- Warm 余量带 → 44-54 引擎（176-216 GPU）
- 冷加载率 38.3 cold LoRA/s → 55 引擎（220 GPU）

### 流量模式

- **强局部性**：租户变体、回滚点、个性化分支、近期评估候选经常重复出现 → 路由应保持 warm 复用
- **弱局部性**：广泛 rollout 波和实验扫描 → 缓存未命中频繁，需要冷加载管理

## 适用场景

- 多租户 LLM 服务：每个租户有自己的适配器
- 产品变体管理：A/B 测试、金丝雀发布、回滚
- 个性化分支：每个用户的个性化适配器
- 研究扫描：大量实验配置的批量评估
- [[Agent-RL]]：大量 Agent 策略版本的同时管理

## 相关概念

- [[Adapter-Revision Path]] — 目录中的每个条目都是一个适配器修订版
- [[Packed MoE LoRA Tensors]] — 优化冷加载路径的技术
- [[LoRA]] — 目录中策略的基本单元
- [[GRPO]] — 产生策略变体的训练算法
- [[metaclaw-continuous-evolution-in-production|MetaClaw]] — Cloud LoRA 的多策略管理与 Policy Catalog 互补
- [[openclaw-rl-turning-daily-usage-into-training-signals|OpenClaw-RL]] — 在线训练信号产生策略变体

## 来源

- [[mint-managed-infrastructure-training-serving-millions-llms|MinT]] — Section 4.3, Section 5.3, Appendix B
