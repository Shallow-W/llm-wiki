---
id: source-gstc-zero-cost-proxy-nas
date: 2026-04-21
source: raw/papers/GSTC(MMC)_1.23.pdf
type: 论文
tags: [NAS, 零成本代理, 微服务部署, M/M/C, 动态替换, 精读]
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

### GSTC 零成本代理数学模型

GSTC 基于信息量量化编码，假设有效信息随网络深度指数衰减，对路径连接和操作类型分别编码。编码值落在 $\left[2^{-(n-1)}, 2^{n-1}\right]$ 区间，输入/输出节点编码为 1。

四个核心维度：

**总路径信息量 $G$**：$G = \sum_{l=1}^{q} g_l$，其中 $g = \sum_{i=0}^{p-1} X_i \cdot 2^{n-s-i}$

**路径信息变异 $S$**：$S = \frac{1}{(q-1)!} \sum_{u,v} |g_u - g_v|$

**输出节点总信息量 $T$**：$T = \sum_{l=1}^{q} t_l$，其中 $t = X_p \cdot 2^{n-p+1}$

**输出节点信息变异 $C$**：$C = \frac{1}{2} \sum_{u,v} |t_u - t_v|$

最终代理分数：$\text{GSTC} = G + S + \frac{G_{\max}-G_{\min}}{T_{\max}-T_{\min}} \cdot T + \frac{G_{\max}-G_{\min}}{C_{\max}-C_{\min}} \cdot C$

### JCQDA 部署算法核心计算

最小实例数（含松弛因子 $\theta$）：$N_m = \lceil (1+\theta)\frac{\lambda_m}{\mu_m} \rceil$

服务-服务器亲和度：$A_m^v = \alpha \cdot \text{Avail}_m^v + \beta \cdot \text{PS}_m^v$

贪心部署：按 $N_m$ 降序排列服务，按 $A_m^v$ 降序排列服务器，逐服务器放置实例。

### LAMRA 动态替换计算流程

1. 根据当前负载计算最小推理速度 $\mu_m^{\min}$
2. 筛除不满足阈值的版本
3. Pareto 前沿筛选（服务速率、效率、GPU 消耗三维）
4. 加权评分：$\text{score}_{m,k} = \alpha\mu_{m,k} + \beta\cdot\text{GSTC}_{m,k} + \gamma C_{m,k}^{\text{GPU}}$

### 理论分析（Theorems 1-3）

三条核心假设：GSTC 相关性优势（$\tau_{\text{GSTC},P} > \tau_{\text{FLOPs},P}$）、相关性-性能映射、Slater 条件满足。

- **Theorem 1**：联合优化具有更高的资源利用率上界（$\bar{\eta}^* > \bar{\eta}_0^*$）
- **Theorem 2**：联合优化具有更低的延迟下界（$T_{\min,\text{joint}} < T_{\min,0}$），延迟分解为 $T_r = T_r^{\text{comp}} + T_r^{\text{que}} + T_r^{\text{comm}}$ 三部分分别证明
- **Theorem 3**：联合优化具有更高的服务质量上界（$Q_{\text{sys}}^* > Q_{\text{sys},0}^*$）
- **对偶间隙**：联合优化的 KKT 乘子更小，可行域更宽松，对偶间隙更窄

### 实验关键数据

**代理相关性（NAS-Bench-201 CIFAR-10）**：GSTC $\rho=0.77$ vs Synflow $0.73$ vs #Params $0.75$

**静态部署延迟（到达率 400）**：JCQDA $0.85$ vs CDRA $1.48$ vs MDSGA $3.14$

**动态大规模延迟**：LAMRA $0.37$ vs CDRA $3.21$（降低 88.5%）vs MDSGA $7.03$（降低 94.7%）

## 提及的实体

- [[Menglan Hu]] — 通讯作者，华中科技大学
- [[Kai Peng]] — 华中科技大学
- [[Yue Yang]] — 华中科技大学
- [[Jing Lu]] — 华中科技大学
- [[Xinyi Yang]] — 华中科技大学
- [[Yi Hu]] — 华中科技大学
- [[华中科技大学]] — 主要研究机构

## 讨论的概念

- [[神经架构搜索 (NAS)]] — 自动化模型设计的核心方法
- [[零成本代理]] — GSTC 的核心创新，无需训练评估架构
- [[JCQDA]] — 联合通信与队列感知部署算法
- [[LAMRA]] — 负载感知模型替换算法
- [[M/M/C 排队模型]] — JCQDA 算法用于延迟建模
- [[微服务调用图]] — AI 服务的部署单元组织方式
- [[混合整数非线性规划 (MINLP)]] — 问题的数学建模形式

## 关联

- 与 [[joint-deployment-request-routing-microservice-tpds|TPDS 2023]] 同一研究组，本文是其全生命周期扩展
- 引用了 [[joint-task-offloading-resource-allocation-model-placement-6g|TSC 2024]] 的 AIaaS 框架
- 三个算法（GSTC + JCQDA + LAMRA）构成"零成本评估 → 静态部署 → 动态调整"端到端流水线

## 精读报告

完整精读报告（含截图）位于 [[gstc-mmc-1-23/report|gstc-mmc-1-23 精读报告]]，包含 12 张论文截图覆盖标题、框架图、算法伪代码、定理证明和实验结果。
