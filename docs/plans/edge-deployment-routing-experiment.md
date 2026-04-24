# Plan: Edge Computing Service Deployment & Routing Experiment

## Summary

设计一个边缘计算场景下的**服务部署与请求路由联合优化**实验。该实验融合三篇论文的核心思想：
- **论文1 (GSTC)**：零成本代理评估 + 负载感知动态模型替换
- **论文2 (TPDS 2023)**：基于排队网络的微服务部署与概率路由联合优化
- **论文3 (TSC 2024)**：双时间尺度优化 + 异构资源分配 + 任务卸载

实验目标：在模拟的边缘-网络-云三层架构中，实现服务部署、请求路由、资源分配的联合优化，最小化端到端延迟和部署成本。

---

## 1. 实验场景设计

### 1.1 网络拓扑

```
┌─────────────────────────────────────────────────────────────┐
│                        Cloud Layer                           │
│  (高算力 GPU/CPU 节点，高延迟，低成本)                        │
│         ↑                                                    │
│    骨干网 (高带宽，高延迟 ~50-100ms)                          │
│         ↓                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  Edge Node 1│←──→│  Edge Node 2│←──→│  Edge Node 3│      │
│  │  (中等算力)  │    │  (中等算力)  │    │  (中等算力)  │      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘      │
│         ↑                    ↑                    ↑           │
│    接入网 (中带宽，低延迟 ~5-20ms)                            │
│         ↓                    ↓                    ↓           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  User Group 1│    │  User Group 2│    │  User Group 3│      │
│  │  (请求源)    │    │  (请求源)    │    │  (请求源)    │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

- **边缘节点数**: 5-10 个（可扩展）
- **每个边缘节点**: CPU cores + 可选 GPU
- **云节点**: 1-2 个（高算力）
- **用户组**: 每个边缘节点服务 1-3 个用户组

### 1.2 服务模型

采用**微服务调用图**（Microservice Call Graph）:

```
用户请求 → [前置处理] → [特征提取] → [AI推理] → [后处理] → 返回
              ↓              ↓           ↓           ↓
           Service A     Service B   Service C   Service D
```

- **服务链数量**: 3-5 条不同的调用链
- **每个服务链**: 3-6 个微服务节点
- **服务复用**: 不同调用链共享部分微服务（如 Service B 被链1和链2共用）
- **服务实例**: 每个微服务可在多个节点部署多个容器实例

### 1.3 请求模型

- **到达过程**: 泊松过程（Poisson arrival）
- **请求类型**: 3-5 种，每种对应一条服务调用链
- **请求速率**: 动态变化（模拟负载波动）
- **SLA**: 每种请求有最大可容忍延迟

---

## 2. 核心算法设计

### 2.1 算法1: 基于排队理论的部署与路由联合优化 (JDR-Joint)

**灵感来源**: 论文2 (TPDS 2023) 的 GMDA + RMPR

**两阶段启发式算法**:

#### Stage 1: 贪心微服务部署算法 (GMDA-Edge)

```python
def GMDA_Edge():
    # Step 1: 计算每个微服务的总计算资源需求
    for m in microservices:
        Nm = sum(Nm(f) for f in flows if m in f.chain)
        # Nm(f): 满足流f最大延迟所需的资源
    
    # Step 2: 按资源需求降序排序
    sorted_services = sort(microservices, key=Nm, descending=True)
    
    # Step 3: 贪心部署
    for m in sorted_services:
        # 选择能使"通信延迟+排队延迟"最小的节点
        best_node = argmin(nodes, 
            lambda v: comm_delay(m, v) + queue_delay(m, v, Nm))
        deploy(m, best_node, Nm)
```

**关键创新点**:
- 考虑边缘节点的**异构性**（CPU/GPU 能力不同）
- 引入**服务亲和性**：相关服务尽量部署在同一节点减少通信
- 资源约束：每个节点的 CPU/GPU cores 上限

#### Stage 2: 请求匹配与分区映射路由 (RMPR-Edge)

```python
def RMPR_Edge():
    # 基于 Open Jackson 排队网络建模
    for flow in request_flows:
        # 为流中的每个微服务对确定转发概率
        for (mi, mj) in flow.adjacent_pairs:
            # P(mi_vi → mj_vj): 从节点vi的mi路由到节点vj的mj的概率
            # 目标：最小化 E[T_resp] = E[T_queue] + E[T_comm]
            optimize_routing_probabilities(flow)
```

**关键创新点**:
- **概率路由**：同一请求流可在多条路径间分配
- **容器共享**：不同流共享同一微服务实例
- **负载均衡**：根据各节点排队长度动态调整转发概率

### 2.2 算法2: 双时间尺度联合优化 (TS-Joint)

**灵感来源**: 论文3 (TSC 2024) 的双时间尺度 + Lyapunov 优化

#### 长时间尺度 (每隔 T0 个时隙): 模型/服务放置

```python
def Long_Term_Placement():
    # 基于历史负载信息，决定每个节点部署哪些服务模型
    for node in edge_nodes:
        # 多臂老虎机 (MAB) 探索-利用
        # 平衡：部署多样性 vs 命中率
        selected_models = MAB_select(node, historical_load)
        deploy_models(node, selected_models)
```

#### 短时间尺度 (每个时隙): 任务卸载 + 资源分配

```python
def Short_Term_Scheduling():
    for task in arriving_tasks:
        # 1. 任务卸载：选择处理节点（延迟接受算法 DA）
        best_node = DA_match(task, available_nodes)
        
        # 2. 资源分配：凸优化求解最优 CPU/GPU 频率
        cpu_freq, gpu_freq = convex_optimize(task, best_node)
        
        # 3. 执行
        execute(task, best_node, cpu_freq, gpu_freq)
```

**Lyapunov 优化**: 将长期稳定性问题转化为每个时隙的确定性子问题

### 2.3 算法3: 零成本代理驱动的动态调整 (GSTC-Dynamic)

**灵感来源**: 论文1 (GSTC) 的零成本评估 + 动态替换

```python
def GSTC_Dynamic():
    # 预评估阶段：零成本代理评分
    for architecture in candidate_architectures:
        score = GSTC_evaluate(architecture)  # 无需训练
        # GSTC = G + S + T + C (信息量化编码)
    
    # 运行时：负载感知模型替换
    while system_running:
        if load_changes_detected():
            # 从预评估库中选择适合当前负载的架构
            new_arch = select_best_architecture(current_load)
            # 同步更新部署方案
            update_deployment(new_arch)
```

**关键创新点**:
- **零成本评估**：无需训练即可预测架构性能
- **动态替换**：根据负载变化实时切换服务架构
- **部署感知**：评估指标直接关联部署需求

---

## 3. Baseline 算法

| Baseline | 描述 | 来源 |
|----------|------|------|
| **Random** | 随机部署 + 随机路由 | 通用基线 |
| **Greedy-Local** | 每个请求本地处理，资源不足时卸载到最近节点 | 论文3 对比方法 |
| **Dijkstra** | 固定部署 + Dijkstra 最短路径路由 | 论文2 对比方法 |
| **Kubernetes-Default** | 默认调度策略（资源均衡）+ 最短路径路由 | 工业基线 |
| **RL-based** | 强化学习（PPO/DQN）端到端优化 | 论文3 对比方法 |

---

## 4. 评价指标

### 4.1 主要指标

| 指标 | 符号 | 定义 |
|------|------|------|
| **平均端到端延迟** | E[T_resp] | 所有成功请求的平均响应时间 |
| **部署成本** | Cost_deploy | 使用的节点数 × 单位成本 |
| **请求成功率** | η_F | 满足 SLA 的请求比例 |
| **资源利用率** | U_res | CPU/GPU 平均利用率 |

### 4.2 次要指标

| 指标 | 符号 | 定义 |
|------|------|------|
| **排队延迟** | E[T_queue] | 请求在队列中的平均等待时间 |
| **通信延迟** | E[T_comm] | 服务间数据传输的平均延迟 |
| **处理延迟** | E[T_proc] | 实际计算的平均时间 |
| **能耗** | Energy | 总能耗（可选） |

---

## 5. 实验参数设置

### 5.1 网络参数

```python
NETWORK_CONFIG = {
    "num_edge_nodes": 5,           # 边缘节点数
    "num_cloud_nodes": 1,          # 云节点数
    "num_user_groups": 10,         # 用户组数
    
    # 边缘节点配置（异构）
    "edge_nodes": [
        {"id": 0, "cpu_cores": 8, "gpu_cores": 2, "cpu_freq": 2.5, "gpu_freq": 1.5},
        {"id": 1, "cpu_cores": 4, "gpu_cores": 1, "cpu_freq": 2.0, "gpu_freq": 1.0},
        {"id": 2, "cpu_cores": 16, "gpu_cores": 4, "cpu_freq": 3.0, "gpu_freq": 2.0},
        {"id": 3, "cpu_cores": 8, "gpu_cores": 0, "cpu_freq": 2.5, "gpu_freq": 0},
        {"id": 4, "cpu_cores": 4, "gpu_cores": 1, "cpu_freq": 2.0, "gpu_freq": 1.0},
    ],
    
    # 云节点配置
    "cloud_nodes": [
        {"id": 5, "cpu_cores": 64, "gpu_cores": 8, "cpu_freq": 3.5, "gpu_freq": 2.5},
    ],
    
    # 链路延迟 (ms)
    "edge_edge_delay": 5,          # 边缘-边缘
    "edge_cloud_delay": 50,        # 边缘-云
    "user_edge_delay": 2,          # 用户-边缘
    
    # 链路带宽 (Mbps)
    "edge_edge_bw": 1000,
    "edge_cloud_bw": 500,
    "user_edge_bw": 100,
}
```

### 5.2 服务参数

```python
SERVICE_CONFIG = {
    "num_service_chains": 3,       # 服务链数量
    "services_per_chain": [4, 5, 3],  # 每条链的服务数
    
    # 微服务定义
    "microservices": [
        {"id": "A", "name": "preprocess", "cpu_demand": 0.5, "gpu_demand": 0, "data_size": 100},
        {"id": "B", "name": "feature_extract", "cpu_demand": 1.0, "gpu_demand": 0.5, "data_size": 50},
        {"id": "C", "name": "ai_inference", "cpu_demand": 2.0, "gpu_demand": 2.0, "data_size": 20},
        {"id": "D", "name": "postprocess", "cpu_demand": 0.5, "gpu_demand": 0, "data_size": 200},
        {"id": "E", "name": "quality_check", "cpu_demand": 1.0, "gpu_demand": 0, "data_size": 10},
    ],
    
    # 服务链定义
    "chains": [
        ["A", "B", "C", "D"],      # 链1: 标准AI推理
        ["A", "B", "E", "D"],      # 链2: 质量检测
        ["A", "C", "D"],           # 链3: 轻量推理
    ],
    
    # 容器成本
    "container_cost": 1.0,         # 每个容器单位成本
}
```

### 5.3 请求参数

```python
REQUEST_CONFIG = {
    # 请求到达率 (请求/秒)，动态变化
    "arrival_rates": {
        "low": [5, 3, 2],          # 低负载
        "medium": [15, 10, 8],     # 中负载
        "high": [30, 25, 20],      # 高负载
        "burst": [50, 40, 35],     # 突发负载
    },
    
    # SLA 最大延迟 (ms)
    "sla_deadline": [100, 150, 80],
    
    # 仿真时长
    "simulation_time": 10000,      # 时隙数
    "slot_duration": 1,            # 每个时隙 1ms
}
```

---

## 6. 代码框架结构

```
edge-deployment-routing/
├── main.py                      # 实验入口
├── config.py                    # 参数配置
├── simulator/
│   ├── __init__.py
│   ├── network.py               # 网络拓扑建模
│   ├── node.py                  # 边缘/云节点
│   ├── service.py               # 微服务定义
│   ├── request.py               # 请求生成与到达
│   └── queue_model.py           # M/M/C 排队模型
├── algorithms/
│   ├── __init__.py
│   ├── baseline/
│   │   ├── random.py
│   │   ├── greedy_local.py
│   │   ├── dijkstra.py
│   │   └── kubernetes_default.py
│   ├── jdr_joint.py             # 算法1: 部署+路由联合优化
│   ├── ts_joint.py              # 算法2: 双时间尺度优化
│   └── gstc_dynamic.py          # 算法3: 零成本代理动态调整
├── metrics/
│   ├── __init__.py
│   └── evaluator.py             # 指标计算与统计
├── visualization/
│   ├── __init__.py
│   └── plot_results.py          # 结果可视化
└── results/                     # 实验结果输出
    ├── latency_comparison.png
    ├── cost_comparison.png
    └── success_rate_comparison.png
```

---

## 7. 实验流程

### Phase 1: 基础实验
1. 固定负载（中负载）下，比较所有算法的**延迟、成本、成功率**
2. 分析各算法在不同指标上的 trade-off

### Phase 2: 负载变化实验
1. 设计**动态负载场景**：低→中→高→突发→中
2. 测试算法的**动态适应性**
3. 重点观察 GSTC-Dynamic 和 TS-Joint 的响应能力

### Phase 3: 规模扩展实验
1. 改变节点数量（5→10→20）
2. 改变服务链复杂度
3. 测试算法的**可扩展性**

### Phase 4: 消融实验
1. JDR-Joint 去掉联合优化（部署和路由独立）
2. TS-Joint 去掉双时间尺度
3. GSTC-Dynamic 去掉动态替换

---

## 8. 预期结果

| 场景 | 预期最优算法 | 理由 |
|------|-------------|------|
| 静态中负载 | JDR-Joint | 联合优化找到全局最优 |
| 动态负载 | TS-Joint / GSTC-Dynamic | 双时间尺度/动态替换适应变化 |
| 大规模 | JDR-Joint | 启发式算法可扩展性好 |
| 资源受限 | GSTC-Dynamic | 零成本评估选择轻量架构 |

---

## 9. Definition of Done

- [ ] 网络拓扑、节点、服务、请求模型实现完成
- [ ] M/M/C 排队模型正确建模并验证
- [ ] 5 个 Baseline 算法实现完成
- [ ] 3 个核心算法实现完成
- [ ] 指标计算模块实现完成
- [ ] Phase 1 基础实验完成，有对比图表
- [ ] Phase 2 动态负载实验完成
- [ ] Phase 3 规模扩展实验完成
- [ ] Phase 4 消融实验完成
- [ ] 实验报告（含分析）撰写完成

---

## 10. Open Questions

1. **是否使用真实数据集**？（如 Alibaba cluster trace）还是纯合成数据？
2. **是否实现 RL baseline**？需要额外训练时间
3. **是否考虑能耗指标**？会增加模型复杂度
4. **Python 仿真 vs 离散事件仿真**（SimPy）？
5. **代码放在哪个 repo**？llm-wiki 下新建目录？
