# 数据结构文档

## 一、DTO 层（模块间交互）

### 1.1 SimulationResult — 仿真结果

```python
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, List

@dataclass
class SimulationResult:
    """
    单次仿真实验的结果。
    
    包含端到端延迟、队列长度、利用率、SLA满足情况、成本和精度。
    """
    # 端到端延迟: {chain_id: float}，单位ms
    e2e_delays: Dict[str, float]
    
    # 队列长度: {(service_id, node_id): float}
    queue_lengths: Dict[Tuple[str, str], float]
    
    # 利用率: {(service_id, node_id): float}，范围[0,1]
    utilization: Dict[Tuple[str, str], float]
    
    # SLA满足情况: {chain_id: bool}
    sla_satisfaction: Dict[str, bool]
    
    # 部署成本
    cost: float
    
    # 平均精度
    accuracy: float
    
    # 额外指标（可选）
    extra_metrics: Dict[str, float] = None
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SimulationResult':
        """从字典反序列化"""
        return cls(**data)
```

### 1.2 ResourceRequirements — 资源需求

```python
from dataclasses import dataclass

@dataclass
class ResourceRequirements:
    """
    服务变体的资源需求。
    
    用于部署决策时的资源约束检查。
    """
    cpu_cores: float      # CPU核数需求
    gpu_cards: float      # GPU卡数需求
    memory_gb: float      # 内存需求(GB)
    
    def __le__(self, other: 'ResourceRequirements') -> bool:
        """检查是否满足资源约束"""
        return (self.cpu_cores <= other.cpu_cores and
                self.gpu_cards <= other.gpu_cards and
                self.memory_gb <= other.memory_gb)
```

### 1.3 NodeDTO — 节点数据传输对象

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class NodeDTO:
    """
    边缘节点的数据传输对象。
    
    包含节点ID、资源容量、速度因子和成本。
    """
    node_id: str          # 节点唯一标识
    cpu_cores: int        # CPU总核数
    gpu_cards: int        # GPU卡数
    memory_gb: int        # 内存(GB)
    speed_factor: float   # 速度因子(相对于基准)
    cost_per_hour: float  # 每小时成本
    
    # 节点类型: 'edge' | 'cloud'
    node_type: str = 'edge'
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NodeDTO':
        return cls(**data)
```

### 1.4 ServiceDTO — 服务数据传输对象

```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ServiceVariantDTO:
    """
    服务模型变体。
    
    如light/medium/heavy变体。
    """
    variant_id: str           # 变体ID
    service_id: str           # 所属服务ID
    resource_req: ResourceRequirements  # 资源需求
    processing_rate: float    # 处理速率(请求/秒)
    accuracy: float           # 精度[0,1]
    model_size_mb: float      # 模型大小(MB)

@dataclass
class ServiceDTO:
    """
    微服务的数据传输对象。
    
    包含服务ID、名称、可用变体列表。
    """
    service_id: str                    # 服务唯一标识
    name: str                          # 服务名称
    variants: List[ServiceVariantDTO]  # 可用变体列表
    
    def get_variant(self, variant_id: str) -> ServiceVariantDTO:
        """获取指定变体"""
        for v in self.variants:
            if v.variant_id == variant_id:
                return v
        raise ValueError(f"变体{variant_id}不存在")
```

### 1.5 ChainDTO — 调用链数据传输对象

```python
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ChainDTO:
    """
    服务调用链的数据传输对象。
    
    描述服务的调用顺序和依赖关系。
    """
    chain_id: str              # 调用链ID
    name: str                  # 调用链名称
    service_sequence: List[str]  # 服务调用顺序
    sla_ms: float              # SLA延迟约束(ms)
    arrival_rate: float        # 到达率(请求/秒)
    
    # 并行分支: [(branch_services, merge_service), ...]
    parallel_branches: List[Tuple[List[str], str]] = None
    
    def get_critical_path(self) -> List[str]:
        """获取关键路径上的服务列表"""
        # 实现关键路径计算
        pass
```

### 1.6 RequestDTO — 请求数据传输对象

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class RequestDTO:
    """
    请求流的数据传输对象。
    
    描述请求的到达特性和约束。
    """
    request_id: str         # 请求流ID
    chain_id: str           # 所属调用链
    arrival_rate: float     # 到达率(请求/秒)
    sla_ms: float           # SLA延迟约束(ms)
    
    # MMPP参数（动态负载）
    mmpp_states: Optional[List[float]] = None  # 状态到达率
    mmpp_transitions: Optional[List[List[float]]] = None  # 状态转移矩阵
```

### 1.7 PlacementDecision — 部署决策

```python
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class PlacementDecision:
    """
    部署策略的输出决策。
    
    包含部署矩阵X、实例数量N、路由概率P。
    """
    # 部署矩阵: {(service_id, node_id): variant_id}
    X: Dict[Tuple[str, str], str]
    
    # 实例数量: {(service_id, node_id): int}
    N: Dict[Tuple[str, str], int]
    
    # 路由概率: {(src_s, src_n, dst_s, dst_n): prob}
    P: Dict[Tuple[str, str, str, str], float]
    
    # 策略名称
    policy_name: str
    
    # 决策时间戳
    timestamp: float = None
    
    def validate(self) -> bool:
        """验证决策的合法性"""
        # 检查资源约束
        # 检查概率归一化
        # 检查实例数量正整数
        pass
```

---

## 二、配置数据结构

### 2.1 ExperimentConfig — 实验配置

```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ExperimentConfig:
    """
    实验配置。
    
    使用Hydra管理，支持分层配置和覆盖。
    """
    # 实验标识
    experiment_id: str
    name: str
    description: str
    
    # 网络规模
    scale: str  # 'small' | 'medium' | 'large'
    
    # 节点配置
    nodes: List[NodeDTO]
    
    # 服务配置
    services: List[ServiceDTO]
    
    # 调用链配置
    chains: List[ChainDTO]
    
    # 请求配置
    requests: List[RequestDTO]
    
    # 算法列表
    algorithms: List[str]
    
    # 仿真参数
    simulation:
        warmup_period: int      # 预热期(秒)
        run_length: int         # 运行长度(秒)
        num_replications: int   # 重复次数
    
    # 输出配置
    output:
        results_dir: str
        log_level: str
        save_intermediate: bool
    
    # 扩展参数
    extra: Optional[Dict] = None
```

### 2.2 NetworkConfig — 网络配置

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class NetworkConfig:
    """
    网络拓扑配置。
    
    包含节点和链路信息。
    """
    nodes: List[NodeDTO]
    
    # 链路延迟: {(node_id1, node_id2): delay_ms}
    link_delays: Dict[Tuple[str, str], float]
    
    # 链路带宽: {(node_id1, node_id2): bandwidth_mbps}
    link_bandwidths: Dict[Tuple[str, str], float]
```

---

## 三、内部数据结构

### 3.1 TrafficMatrix — 流量矩阵

```python
from typing import Dict, Tuple

# 到达率矩阵: {(service_id, node_id): arrival_rate}
TrafficMatrix = Dict[Tuple[str, str], float]

# 利用率矩阵: {(service_id, node_id): utilization}
UtilizationMatrix = Dict[Tuple[str, str], float]

# 延迟矩阵: {(service_id, node_id): delay_ms}
DelayMatrix = Dict[Tuple[str, str], float]
```

### 3.2 ErlangCResult — Erlang-C计算结果

```python
from dataclasses import dataclass

@dataclass
class ErlangCResult:
    """
    Erlang-C公式计算结果。
    """
    delay_prob: float      # 延迟概率 C(c, ρ)
    avg_queue_length: float  # 平均队列长度 L_q
    avg_wait_time: float   # 平均等待时间 W_q
    utilization: float     # 利用率 ρ
    
    # 计算方法
    method: str  # 'stable' | 'log-space' | 'hayward'
```

---

## 四、序列化规范

### 4.1 JSON序列化

所有DTO必须支持 `to_dict()` 和 `from_dict()` 方法。

```python
import json

# 序列化
result = SimulationResult(...)
json_str = json.dumps(result.to_dict(), indent=2)

# 反序列化
data = json.loads(json_str)
result = SimulationResult.from_dict(data)
```

### 4.2 YAML配置

实验配置使用YAML格式，支持Hydra的分层配置。

```yaml
# base.yaml
defaults:
  - _self_

experiment:
  name: "base_experiment"
  scale: "medium"
  
nodes:
  - node_id: "edge-1"
    cpu_cores: 8
    gpu_cards: 1
    memory_gb: 32
    speed_factor: 1.0
    cost_per_hour: 0.5
    
services:
  - service_id: "svc-1"
    name: "object-detection"
    variants:
      - variant_id: "light"
        resource_req:
          cpu_cores: 2
          gpu_cards: 0.5
          memory_gb: 4
        processing_rate: 50.0
        accuracy: 0.75
        model_size_mb: 100
      - variant_id: "medium"
        resource_req:
          cpu_cores: 4
          gpu_cards: 1.0
          memory_gb: 8
        processing_rate: 20.0
        accuracy: 0.85
        model_size_mb: 300
      - variant_id: "heavy"
        resource_req:
          cpu_cores: 8
          gpu_cards: 2.0
          memory_gb: 16
        processing_rate: 5.0
        accuracy: 0.92
        model_size_mb: 1000

chains:
  - chain_id: "chain-1"
    name: "video-analytics"
    service_sequence: ["svc-1", "svc-2"]
    sla_ms: 200.0
    arrival_rate: 10.0

simulation:
  warmup_period: 300
  run_length: 3600
  num_replications: 30

output:
  results_dir: "./results"
  log_level: "INFO"
  save_intermediate: true
```

---

## 五、接口规范

### 5.1 BasePlacementPolicy

```python
from abc import ABC, abstractmethod
from typing import List

class BasePlacementPolicy(ABC):
    """
    部署策略抽象基类。
    
    所有部署算法必须继承此类。
    """
    
    @abstractmethod
    def select(self, request: RequestDTO, nodes: List[NodeDTO],
               services: List[ServiceDTO]) -> PlacementDecision:
        """
        选择最优部署方案。
        
        Args:
            request: 请求信息
            nodes: 可用节点列表
            services: 服务列表
        
        Returns:
            PlacementDecision: 部署决策
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """返回策略名称"""
        pass
    
    def validate_decision(self, decision: PlacementDecision,
                         nodes: List[NodeDTO],
                         services: List[ServiceDTO]) -> bool:
        """
        验证部署决策的合法性。
        
        检查资源约束和概率归一化。
        """
        pass
```

### 5.2 BaseSimulator

```python
from abc import ABC, abstractmethod

class BaseSimulator(ABC):
    """
    仿真器抽象基类。
    
    支持解析仿真和DES仿真。
    """
    
    @abstractmethod
    def simulate(self, network: NetworkConfig,
                 decision: PlacementDecision) -> SimulationResult:
        """
        执行仿真。
        
        Args:
            network: 网络配置
            decision: 部署决策
        
        Returns:
            SimulationResult: 仿真结果
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """返回仿真器名称"""
        pass
```

---

## 六、数据验证规则

### 6.1 资源约束验证

```python
def validate_resource_constraints(
    decision: PlacementDecision,
    nodes: List[NodeDTO],
    services: List[ServiceDTO]
) -> bool:
    """
    验证部署决策是否满足资源约束。
    
    对每个节点，检查总资源需求不超过容量。
    """
    for node in nodes:
        total_cpu = 0
        total_gpu = 0
        total_mem = 0
        
        for (svc_id, node_id), var_id in decision.X.items():
            if node_id == node.node_id:
                svc = next(s for s in services if s.service_id == svc_id)
                var = svc.get_variant(var_id)
                n_instances = decision.N.get((svc_id, node_id), 1)
                
                total_cpu += var.resource_req.cpu_cores * n_instances
                total_gpu += var.resource_req.gpu_cards * n_instances
                total_mem += var.resource_req.memory_gb * n_instances
        
        if (total_cpu > node.cpu_cores or
            total_gpu > node.gpu_cards or
            total_mem > node.memory_gb):
            return False
    
    return True
```

### 6.2 概率归一化验证

```python
def validate_routing_probabilities(decision: PlacementDecision) -> bool:
    """
    验证路由概率是否归一化。
    
    对每个源节点-服务对，出边概率之和为1。
    """
    from collections import defaultdict
    
    probs = defaultdict(float)
    for (src_s, src_n, dst_s, dst_n), prob in decision.P.items():
        probs[(src_s, src_n)] += prob
    
    for key, total in probs.items():
        if abs(total - 1.0) > 1e-6:
            return False
    
    return True
```
