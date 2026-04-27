# 边缘计算服务部署与路由优化实验框架 — 架构简介

## 项目概述

本项目是一个基于**解析仿真**（数学公式直接计算，非事件驱动）的边缘计算服务部署与路由联合优化实验框架。

**核心创新**: AMS (Adaptive Model Selection) 自适应模型选择算法 — 在异构边缘节点网络中，根据负载动态选择最适合的模型变体（light/medium/heavy），而 baseline 使用固定模型。

**技术栈**: Python 3.9+, Hydra (配置管理), NumPy/SciPy (数值计算), Matplotlib (可视化), SimPy (DES验证)

---

## 整体架构（7层）

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 7: 完善层                                                │
│  ├─ 剩余Baseline (FixedLight/Heavy, Random, CloudOnly, EdgeOnly)│
│  ├─ Oracle上界 (小规模穷举)                                      │
│  ├─ 主程序 (main.py)                                             │
│  └─ README.md + 论文图表复现检查                                  │
├─────────────────────────────────────────────────────────────────┤
│  Phase 6: 验证统计层                                             │
│  ├─ QNA验证 (DES对比5个配置)                                     │
│  ├─ 统计检验 (置信区间 + Wilcoxon + Cohen's d)                   │
│  ├─ 绘图脚本 (延迟/成本/热力图/Pareto前沿)                        │
│  └─ 日志模块 (AMS决策上下文记录)                                  │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: 实验编排层                                             │
│  ├─ ExperimentRunner (通用实验框架)                               │
│  ├─ 实验1-8 YAML配置文件                                         │
│  └─ 实验执行与结果收集                                           │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 算法策略层                                             │
│  ├─ BasePlacementPolicy (抽象接口)                               │
│  ├─ AMS算法 (自适应模型选择)                                     │
│  ├─ 8个Baseline算法                                              │
│  └─ Oracle上界                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 核心引擎层                                             │
│  ├─ Erlang-C计算 (稳定递推 + log-space + Hayward近似)            │
│  ├─ 流量方程求解器 (Gauss-Seidel + 稳定性检查)                   │
│  ├─ 端到端延迟计算器 (关键路径法)                                │
│  └─ 单元测试                                                     │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: 数据模型层                                             │
│  ├─ 节点模型 (Node) — 异构资源 + ResourceCapacity                │
│  ├─ 服务模型 (Service) — 多模型变体 + ResourceRequirements       │
│  ├─ 调用链模型 (Chain) — DAG结构 + critical_path()               │
│  ├─ 请求模型 (Request) — 泊松到达 + SLA约束                      │
│  └─ 服务注册表 (ServiceRegistry)                                 │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: 基础设施层                                             │
│  ├─ 项目骨架 (目录结构 + pyproject.toml + Hydra配置)             │
│  ├─ 核心DTO (SimulationResult + ResourceRequirements)            │
│  └─ 抽象接口 (BasePlacementPolicy + ExperimentConfig)            │
├─────────────────────────────────────────────────────────────────┤
│  Phase 0: 算法预验证层                                           │
│  ├─ AMS原型快速实现                                              │
│  └─ Baseline对比验证                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心数据流

```
输入配置 (YAML)
    ↓
数据模型层 (Node/Service/Chain/Request) → DTO
    ↓
核心引擎层 (Erlang-C + 流量方程 + 延迟计算)
    ↓
算法策略层 (AMS/Baseline) → PlacementDecision
    ↓
实验编排层 (ExperimentRunner) → 结果收集
    ↓
验证统计层 (QNA验证 + 统计检验 + 绘图)
    ↓
输出 (图表 + 数据 + 论文)
```

---

## 关键设计文件索引

| 文件 | 路径 | 说明 |
|------|------|------|
| **实验框架总设计** | `docs/plans/iterations/experiment-framework-v4-final.md` | v4最终版框架设计 |
| **TODO清单** | 当前对话上下文 | 31项任务，7个Phase |
| **Git工作流规范** | `docs/WORKFLOW.md` | Git开发管理规范 |
| **开发指引** | `docs/GUIDE.md` | 开发指引文件 |
| **数据结构文档** | `docs/DATA_STRUCTURES.md` | DTO和接口定义 |
| **核心公式速查** | `docs/plans/iterations/experiment-framework-v4-final.md` 第9节 | 所有关键公式 |
| **参数配置表** | `docs/plans/iterations/experiment-framework-v4-final.md` 第6节 | 20+参数完整表格 |

---

## 模块依赖规则

```
算法策略层 ──→ 核心引擎层 ──→ 数据模型层(DTO)
    │              │              │
    └──────────────┴──────────────┘
                   │
              基础设施层（所有层可依赖）
```

**禁止**: 核心引擎层依赖算法策略层；数据模型层依赖核心引擎层。

---

## 核心接口

### BasePlacementPolicy (抽象基类)
```python
class BasePlacementPolicy(ABC):
    @abstractmethod
    def select(self, request: Request, nodes: List[Node], 
               services: List[Service]) -> PlacementDecision:
        """选择部署方案"""
        pass
```

### SimulationResult (DTO)
```python
@dataclass
class SimulationResult:
    e2e_delays: Dict[str, float]      # 端到端延迟
    queue_lengths: Dict[Tuple[str,str], float]  # 队列长度
    utilization: Dict[Tuple[str,str], float]    # 利用率
    sla_satisfaction: Dict[str, bool] # SLA满足情况
    cost: float                       # 部署成本
    accuracy: float                   # 平均精度
```

---

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 配置管理 | Hydra | 分层配置，支持实验参数覆盖 |
| 数值计算 | NumPy/SciPy | 标准科学计算库 |
| 统计检验 | SciPy.stats | Wilcoxon + t-test |
| 可视化 | Matplotlib | 脚本化绘图，投稿级质量 |
| DES验证 | SimPy | 与解析仿真对比验证 |
| 单元测试 | pytest | 标准Python测试框架 |

---

## 关键约束

1. **解析仿真**: 数学公式直接计算，非事件驱动仿真
2. **异构节点**: 不同节点有不同CPU/GPU/内存/速度因子
3. **硬资源约束**: CPU/GPU/内存不可超售
4. **M/M/c假设**: 泊松到达 + 指数服务时间
5. **QNA近似**: 独立M/M/c + 流量方程，ρ>0.7时误差>15%
