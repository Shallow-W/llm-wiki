# Plan: Edge Computing Service Deployment & Routing Experiment (v2)

## Summary

本实验聚焦于**边缘计算场景下的微服务部署与请求路由联合优化**问题。以论文2（TPDS 2023）的微服务部署+概率路由为核心框架，**适配**论文3（TSC 2024）的双时间尺度优化机制处理动态负载，**适配**论文1（GSTC）的零成本评估思想用于多模型变体选择。

**核心定位**：不是"融合"三篇论文，而是在统一的微服务部署路由问题下，借鉴三篇论文的各自优势。

---

## 1. 核心问题定义

### 1.1 问题域

**微服务部署与请求路由联合优化（JDR）**

给定：
- 边缘-云网络拓扑（节点、链路延迟/带宽）
- 微服务调用链集合（有向无环图 DAG）
- 请求到达过程（泊松过程，动态变化）
- 每个微服务的资源需求（CPU/GPU）
- 每个微服务的**多模型变体**（不同精度-延迟权衡）

决策：
- **部署决策**：每个微服务在每个节点部署多少个容器实例
- **路由决策**：请求在每个微服务节点如何转发到下一跳
- **模型选择**：每个实例使用哪个模型变体
- **资源分配**：每个实例分配多少 CPU/GPU 资源

目标：
- 最小化端到端平均延迟
- 最小化部署成本
- 最大化 SLA 满足率

### 1.2 为什么这样定位

| 论文 | 原问题 | 本实验适配方式 |
|------|--------|---------------|
| 论文2 TPDS | 微服务部署+路由 | **直接继承**：核心问题一致，作为基础框架 |
| 论文3 TSC | 任务卸载+资源+模型放置 | **适配**：将"任务卸载"映射为"请求路由"，"模型放置"映射为"服务部署"，"资源分配"保留 |
| 论文1 GSTC | NAS 架构搜索 | **适配**：将"架构搜索"改为"模型变体选择"，零成本评估用于快速筛选模型变体 |

---

## 2. 实验场景设计

### 2.1 网络拓扑

```
                    [Cloud Node]
                         ↑
                    (50ms, 500Mbps)
                         ↓
    [Edge 1] ←(5ms)→ [Edge 2] ←(5ms)→ [Edge 3]
       ↑                  ↑                  ↑
   (2ms,100M)        (2ms,100M)        (2ms,100M)
       ↓                  ↓                  ↓
   [Users 1-3]      [Users 4-6]      [Users 7-10]
```

- **边缘节点**：5个，异构配置（见参数表）
- **云节点**：1个，高算力
- **用户组**：10个，每个边缘节点服务 2-3 组
- **链路**：有向，带延迟和带宽约束

### 2.2 微服务调用链

采用**有向无环图（DAG）**，支持分支和合并：

```
Chain 1 (图像识别):
  User → [A:预处理] → [B:特征提取] → [C:AI推理] → [D:后处理] → Return
                          ↓
Chain 2 (质量检测):
  User → [A:预处理] → [B:特征提取] → [E:质量判断] → [D:后处理] → Return
                          ↑ (复用 B)
Chain 3 (轻量分类):
  User → [A:预处理] → [C:AI推理] → Return
```

- **服务复用**：B 被 Chain 1 和 Chain 2 共享
- **分支结构**：Chain 1 中 B 之后可选择 C 或 E（根据请求类型）
- **每个微服务有多个模型变体**（见 2.4）

### 2.3 请求模型

- **到达过程**：泊松过程，速率 λ 动态变化
- **请求类型**：3 种，分别对应 3 条调用链
- **请求大小**：服从指数分布，均值 100KB
- **SLA**：
  - Chain 1: 150ms
  - Chain 2: 200ms
  - Chain 3: 100ms

### 2.4 微服务多模型变体（论文1 GSTC 的适配）

每个 AI 推理微服务（如 C）有多个预训练模型变体：

| 变体 | 精度 | 处理时间 | 模型大小 | GPU需求 |
|------|------|---------|---------|---------|
| C_light | 85% | 20ms | 5MB | 0.5 GPU |
| C_medium | 90% | 40ms | 20MB | 1.0 GPU |
| C_heavy | 95% | 80ms | 100MB | 2.0 GPU |

**零成本评估**：使用轻量级代理（如 FLOPs、参数量、内存占用）快速评估每个变体的延迟，无需实际运行。

---

## 3. 排队模型（修正版）

### 3.1 为什么不用简单 M/M/C

Reviewer A 指出：微服务调用链是 DAG，不是简单串联。使用 **Fork-Join 排队网络** 或 **离散事件仿真** 更准确。

### 3.2 采用离散事件仿真（DES）

使用 **SimPy** 或自定义 DES：

```python
# 核心事件类型
EVENT_ARRIVAL      # 请求到达
EVENT_SERVICE_START # 服务开始处理
EVENT_SERVICE_END   # 服务处理完成
EVENT_ROUTING       # 请求路由到下一跳
EVENT_DEPLOYMENT    # 部署决策更新（长时间尺度）
```

### 3.3 节点内排队模型

每个微服务实例建模为 **M/G/1 或 M/G/c** 队列：
- **到达**：泊松过程（来自上游路由）
- **服务时间**：一般分布（取决于模型变体和资源分配）
- **服务率**：μ = f(cpu_freq, gpu_freq, model_complexity)
- **排队规则**：FIFO

### 3.4 端到端延迟计算

```
T_end2end = T_comm(user→first) + Σ(T_queue_i + T_proc_i + T_comm_i→i+1)
```

其中：
- T_queue：排队等待时间（通过排队模型或仿真统计）
- T_proc：实际处理时间（模型变体决定）
- T_comm：通信时间 = 数据大小 / 带宽 + 链路延迟

---

## 4. 核心算法设计（修正版）

### 4.1 算法1: JDR-Static（论文2 直接复现）

**来源**：论文2 TPDS 2023 的 GMDA + RMPR

**特点**：静态部署 + 固定路由，单时间尺度

```python
def JDR_Static():
    # Stage 1: GMDA 贪心部署
    for m in sorted_microservices(by_resource_demand, descending=True):
        best_node = argmin(nodes, lambda v: 
            estimated_queue_delay(m, v) + estimated_comm_delay(m, v))
        deploy(m, best_node, required_instances)
    
    # Stage 2: RMPR 概率路由
    for flow in request_flows:
        for (mi, mj) in flow.adjacent_pairs:
            # 求解最优转发概率 P(mi_vi → mj_vj)
            # 目标：最小化期望端到端延迟
            optimize_forwarding_probabilities(flow)
```

**适用场景**：负载稳定的静态环境

### 4.2 算法2: JDR-Adaptive（论文3 适配）

**来源**：论文3 TSC 2024 的双时间尺度 + Lyapunov 优化

**特点**：长时间尺度部署调整 + 短时间尺度路由+资源分配

#### 长时间尺度（每 T0=100 个时隙）

```python
def Long_Term_Deployment():
    # 基于过去 T0 个时隙的负载统计
    avg_load = statistics(last_T0_slots)
    
    # 使用 MAB 探索-利用选择部署方案
    # 臂（arm）：每个节点的服务部署组合
    # 奖励（reward）：-平均延迟（负延迟作为奖励）
    new_deployment = MAB_select_deployment(avg_load)
    apply_deployment(new_deployment)
```

#### 短时间尺度（每个时隙）

```python
def Short_Term_Scheduling():
    for task in arriving_tasks:
        # 1. 任务卸载：延迟接受算法（DA）匹配任务到节点
        assigned_node = DA_match(task, candidate_nodes)
        
        # 2. 资源分配：凸优化求解最优 CPU/GPU 频率
        cpu_freq, gpu_freq = convex_optimize(
            task, assigned_node, 
            objective=min_latency + energy_weight*energy)
        
        # 3. 模型选择：选择已部署的模型变体
        model_variant = select_variant(assigned_node, task.qos_requirement)
```

**Lyapunov 优化**：定义虚拟队列约束长期平均性能，将长期问题转化为每个时隙的确定性子问题。

**适用场景**：负载缓慢变化的动态环境

### 4.3 算法3: JDR-NAS（论文1 适配）

**来源**：论文1 GSTC 的零成本评估 + 负载感知替换

**特点**：每个微服务预定义多个模型变体，运行时根据负载动态选择

```python
def JDR_NAS():
    # 离线阶段：零成本代理评估所有模型变体
    for service in microservices:
        for variant in service.variants:
            # 使用轻量级代理评估（FLOPs, 参数量, 内存）
            proxy_score = zero_cost_evaluate(variant)
            # proxy_score 与实测延迟的相关性通过小规模标定确定
    
    # 在线阶段：负载感知动态模型替换
    while system_running:
        current_load = monitor_load()
        
        for service in microservices:
            # 根据当前负载选择最优变体
            # 高负载 → 选轻量变体（减少排队）
            # 低负载 → 选重量变体（提高精度）
            optimal_variant = select_variant_by_load(service, current_load)
            
            if optimal_variant != current_variant:
                # 热切换：新请求使用新变体，旧请求继续用旧变体
                gradual_switch(service, optimal_variant)
```

**零成本评估代理**：
- 不直接使用 GSTC 的 G+S+T+C（那是针对神经网络架构的）
- 改用更通用的代理：**FLOPs × 内存占用 / 峰值算力**
- 通过小规模标定实验确定代理分数与实测延迟的映射关系

**适用场景**：需要精度-延迟权衡的动态环境

### 4.4 算法关系

```
JDR-Static（基础）
    ↓ 增加双时间尺度
JDR-Adaptive（动态部署+路由）
    ↓ 增加模型变体选择
JDR-NAS（动态部署+路由+模型选择）
```

---

## 5. Baseline 设计（修正版）

| Baseline | 描述 | 来源 |
|----------|------|------|
| **Random** | 随机部署 + 随机路由 | 通用基线 |
| **Greedy-Local** | 每个请求优先本地处理，本地资源不足时卸载到最近节点 | 论文3 对比方法 |
| **K8s-Default** | 模拟 Kubernetes 默认调度（资源匹配 + 均匀分布）+ 最短路径路由 | 工业基线 |
| **SPH** | 最短路径启发式：固定部署，路由始终走延迟最短路径 | 替换原 Dijkstra |
| **GMDA-Only** | 仅论文2的 GMDA 部署，固定路由（验证 RMPR 价值） | 论文2 消融 |
| **Lyapunov-Only** | 仅论文3的 Lyapunov 优化，无模型选择（验证 MAB 价值） | 论文3 消融 |
| **Oracle** | 假设已知未来负载的最优静态部署（理论上界） | 通用上界 |

**移除**：原 Dijkstra（不适用于部署问题）、模糊的 RL-based

---

## 6. 评价指标（修正版）

### 6.1 主要指标

| 指标 | 符号 | 定义 | 来源 |
|------|------|------|------|
| **平均端到端延迟** | E[T_resp] | 所有成功请求的响应时间均值 | 论文2,3 |
| **P99 延迟** | T_p99 | 99% 分位延迟 | 新增 |
| **部署成本** | Cost_deploy | 使用的容器实例数 × 单位成本 | 论文2 |
| **SLA 满足率** | η_SLA | 延迟 ≤ SLA 的请求比例 | 替换原"成功率" |
| **SLA 违反率** | ρ_SLA | 1 - η_SLA | 新增 |

### 6.2 次要指标

| 指标 | 符号 | 定义 |
|------|------|------|
| **排队延迟** | E[T_queue] | 请求在队列中的平均等待时间 |
| **通信延迟** | E[T_comm] | 服务间数据传输的平均延迟 |
| **处理延迟** | E[T_proc] | 实际计算的平均时间 |
| **资源利用率** | U_res | CPU/GPU 平均利用率 |
| **决策时间** | T_decision | 算法做出部署/路由决策的平均时间 | 新增 |
| **能耗** | Energy | 总能耗（CPU + GPU） | 新增 |
| **能耗-延迟积** | EDP | Energy × Delay | 新增 |

---

## 7. 实验参数（修正版）

### 7.1 网络参数

```python
NETWORK_CONFIG = {
    "num_edge_nodes": 5,
    "num_cloud_nodes": 1,
    "num_user_groups": 10,
    
    "edge_nodes": [
        {"id": 0, "cpu_cores": 8, "gpu_cards": 2, "cpu_freq_ghz": 2.5, "gpu_freq_ghz": 1.5, "mem_gb": 32},
        {"id": 1, "cpu_cores": 4, "gpu_cards": 1, "cpu_freq_ghz": 2.0, "gpu_freq_ghz": 1.0, "mem_gb": 16},
        {"id": 2, "cpu_cores": 16, "gpu_cards": 4, "cpu_freq_ghz": 3.0, "gpu_freq_ghz": 2.0, "mem_gb": 64},
        {"id": 3, "cpu_cores": 8, "gpu_cards": 0, "cpu_freq_ghz": 2.5, "gpu_freq_ghz": 0, "mem_gb": 32},
        {"id": 4, "cpu_cores": 4, "gpu_cards": 1, "cpu_freq_ghz": 2.0, "gpu_freq_ghz": 1.0, "mem_gb": 16},
    ],
    
    "cloud_nodes": [
        {"id": 5, "cpu_cores": 64, "gpu_cards": 8, "cpu_freq_ghz": 3.5, "gpu_freq_ghz": 2.5, "mem_gb": 256},
    ],
    
    # 链路延迟 (ms)
    "edge_edge_delay_ms": 5,
    "edge_cloud_delay_ms": 100,  # 修正：从50ms改为100ms（更真实）
    "user_edge_delay_ms": 2,
    
    # 链路带宽 (Mbps)
    "edge_edge_bw_mbps": 1000,
    "edge_cloud_bw_mbps": 500,
    "user_edge_bw_mbps": 100,
}
```

### 7.2 服务参数

```python
SERVICE_CONFIG = {
    "microservices": {
        "A": {"name": "preprocess", "cpu_req": 0.5, "gpu_req": 0, 
              "base_proc_time_ms": 10, "input_size_kb": 100, "output_size_kb": 50},
        "B": {"name": "feature_extract", "cpu_req": 1.0, "gpu_req": 0.5,
              "base_proc_time_ms": 30, "input_size_kb": 50, "output_size_kb": 20},
        "C": {"name": "ai_inference", "cpu_req": 2.0, "gpu_req": 1.0,
              "base_proc_time_ms": 50, "input_size_kb": 20, "output_size_kb": 10,
              # 多模型变体
              "variants": [
                  {"name": "C_light", "accuracy": 0.85, "proc_time_ms": 20, "model_size_mb": 5, "gpu_req": 0.5},
                  {"name": "C_medium", "accuracy": 0.90, "proc_time_ms": 40, "model_size_mb": 20, "gpu_req": 1.0},
                  {"name": "C_heavy", "accuracy": 0.95, "proc_time_ms": 80, "model_size_mb": 100, "gpu_req": 2.0},
              ]},
        "D": {"name": "postprocess", "cpu_req": 0.5, "gpu_req": 0,
              "base_proc_time_ms": 15, "input_size_kb": 10, "output_size_kb": 200},
        "E": {"name": "quality_check", "cpu_req": 1.0, "gpu_req": 0,
              "base_proc_time_ms": 25, "input_size_kb": 20, "output_size_kb": 5},
    },
    
    "chains": [
        {"id": 1, "services": ["A", "B", "C", "D"], "sla_ms": 150},
        {"id": 2, "services": ["A", "B", "E", "D"], "sla_ms": 200},
        {"id": 3, "services": ["A", "C"], "sla_ms": 100},
    ],
    
    "container_cost_per_instance": 1.0,
}
```

### 7.3 请求参数

```python
REQUEST_CONFIG = {
    # 请求到达率 (req/s)，动态变化模式
    "arrival_patterns": {
        "static_low":    {"chain1": 5, "chain2": 3, "chain3": 2},
        "static_medium": {"chain1": 15, "chain2": 10, "chain3": 8},
        "static_high":   {"chain1": 30, "chain2": 25, "chain3": 20},
        
        # 动态模式1: 渐进变化
        "gradual": {"type": "linear", "start": "static_low", "end": "static_high", "duration_slots": 6000},
        
        # 动态模式2: 突发负载
        "burst": {"type": "burst", "base": "static_medium", 
                  "burst_multiplier": 3, "burst_duration_slots": 300, "interval_slots": 2000},
        
        # 动态模式3: 周期性变化
        "periodic": {"type": "sinusoidal", "base": "static_medium", 
                     "amplitude": 10, "period_slots": 2000},
    },
    
    # 仿真参数
    "simulation_duration_slots": 10000,
    "slot_duration_ms": 10,  # 每个时隙 10ms
    "warmup_slots": 500,     # 预热时隙（不计入统计）
    
    # 重复实验
    "random_seed": 42,
    "num_repetitions": 10,   # 每个实验重复10次，取均值±95%置信区间
}
```

---

## 8. 实验阶段（修正版）

### Phase 1: 基础实验（静态负载）

| 负载 | 到达率 | 目的 |
|------|--------|------|
| Low | 5/3/2 req/s | 验证算法在轻负载下的行为 |
| Medium | 15/10/8 req/s | 主要对比场景 |
| High | 30/25/20 req/s | 验证算法在重负载下的表现 |

**对比维度**：所有算法在 3 种负载下的延迟、成本、SLA满足率

### Phase 2: 动态负载实验

| 模式 | 描述 | 目的 |
|------|------|------|
| Gradual | 线性变化 | 测试算法对缓慢负载变化的适应性 |
| Burst | 突发高负载 | 测试算法对突发流量的响应 |
| Periodic | 正弦波变化 | 测试算法的周期性适应能力 |

**关键观察**：
- JDR-Adaptive 的重配置频率和触发条件
- JDR-NAS 的模型切换频率和开销
- 各算法的 SLA 违反率随时间变化曲线

### Phase 3: 规模扩展实验

| 维度 | 扩展范围 | 目的 |
|------|---------|------|
| 节点数 | 5 → 10 → 20 | 测试算法可扩展性 |
| 请求率 | 50 → 100 → 200 req/s | 测试高并发处理能力 |
| 服务链数 | 3 → 6 → 10 | 测试复杂场景处理能力 |

### Phase 4: 消融实验（详细版）

| 消融对象 | 对比组 | 目的 |
|----------|--------|------|
| RMPR 路由 | GMDA-Only vs JDR-Static | 验证概率路由的价值 |
| 双时间尺度 | JDR-Static vs JDR-Adaptive | 验证动态调整的价值 |
| MAB 模型放置 | Lyapunov-Only vs JDR-Adaptive | 验证 MAB 的价值 |
| 模型变体选择 | JDR-Adaptive vs JDR-NAS | 验证模型选择的增益 |
| 联合优化 | 独立优化 vs 联合优化 | 验证联合优化的必要性 |

---

## 9. 代码框架结构

```
edge-deployment-routing/
├── main.py                      # 实验入口
├── config.py                    # 参数配置
├── requirements.txt             # 依赖
├── simulator/
│   ├── __init__.py
│   ├── network.py               # 网络拓扑建模
│   ├── node.py                  # 边缘/云节点（含队列）
│   ├── service.py               # 微服务定义（含多模型变体）
│   ├── request.py               # 请求生成与到达
│   └── des_engine.py            # 离散事件仿真引擎（SimPy 或自定义）
├── algorithms/
│   ├── __init__.py
│   ├── baseline/
│   │   ├── random.py
│   │   ├── greedy_local.py
│   │   ├── kubernetes_default.py
│   │   └── shortest_path.py
│   ├── jdr_static.py            # 算法1: GMDA+RMPR
│   ├── jdr_adaptive.py          # 算法2: 双时间尺度
│   └── jdr_nas.py               # 算法3: 模型变体选择
├── metrics/
│   ├── __init__.py
│   └── evaluator.py             # 指标计算与统计
├── utils/
│   ├── __init__.py
│   └── helpers.py               # 辅助函数
├── visualization/
│   ├── __init__.py
│   └── plot_results.py          # 结果可视化
├── results/                     # 实验结果输出
│   ├── raw_data/                # 原始数据
│   └── figures/                 # 图表
└── README.md                    # 实验说明
```

---

## 10. 可复现性保证

| 项目 | 说明 |
|------|------|
| **仿真平台** | Python 3.9+，使用 SimPy 4.0+ 进行离散事件仿真 |
| **随机种子** | 固定种子 42，每次实验使用 seed + repetition_id |
| **重复次数** | 每个实验配置重复 10 次，报告均值 ± 95% 置信区间 |
| **代码开源** | 完整代码 + 配置文件 + 运行脚本 |
| **数据生成** | 提供调用链生成脚本，支持自定义参数 |
| **文档** | README 包含运行步骤、参数说明、结果解读 |

---

## 11. Definition of Done

- [ ] 离散事件仿真引擎实现（基于 SimPy）
- [ ] 网络拓扑、节点、服务、请求模型实现
- [ ] 微服务多模型变体机制实现
- [ ] 7 个 Baseline 算法实现完成
- [ ] 3 个核心算法实现完成
- [ ] 指标计算模块实现（含置信区间）
- [ ] Phase 1 基础实验完成，有对比图表
- [ ] Phase 2 动态负载实验完成（3种模式）
- [ ] Phase 3 规模扩展实验完成
- [ ] Phase 4 消融实验完成
- [ ] 实验报告（含统计分析）撰写完成

---

## 12. Open Questions

1. **是否使用真实 trace 数据**？（如 Alibaba cluster trace）还是纯合成数据？
2. **是否实现 RL baseline**？如果需要，具体用哪种算法（PPO/DQN）？
3. **SimPy vs 自定义 DES**：SimPy 更易用但可能较慢，自定义更灵活但开发成本高
4. **代码仓库位置**：放在 llm-wiki 下新建 `experiments/` 目录？
