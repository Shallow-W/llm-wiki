"""
DTO层：模块间交互的数据结构

所有DTO支持to_dict()和from_dict()序列化，使用dataclass实现。
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime


@dataclass
class ResourceRequirements:
    """服务变体的资源需求"""
    cpu_cores: float = 0.0
    gpu_cards: float = 0.0
    memory_gb: float = 0.0
    
    def __le__(self, other: 'ResourceRequirements') -> bool:
        """检查是否满足资源约束"""
        return (self.cpu_cores <= other.cpu_cores and
                self.gpu_cards <= other.gpu_cards and
                self.memory_gb <= other.memory_gb)
    
    def __add__(self, other: 'ResourceRequirements') -> 'ResourceRequirements':
        """资源累加"""
        return ResourceRequirements(
            cpu_cores=self.cpu_cores + other.cpu_cores,
            gpu_cards=self.gpu_cards + other.gpu_cards,
            memory_gb=self.memory_gb + other.memory_gb
        )
    
    def __mul__(self, scalar: float) -> 'ResourceRequirements':
        """资源缩放"""
        return ResourceRequirements(
            cpu_cores=self.cpu_cores * scalar,
            gpu_cards=self.gpu_cards * scalar,
            memory_gb=self.memory_gb * scalar
        )


@dataclass
class NodeDTO:
    """边缘节点数据传输对象"""
    node_id: str
    cpu_cores: int = 0
    gpu_cards: int = 0
    memory_gb: int = 0
    speed_factor: float = 1.0
    cost_per_hour: float = 0.0
    node_type: str = 'edge'  # 'edge' | 'cloud'
    
    def get_capacity(self) -> ResourceRequirements:
        """获取节点资源容量"""
        return ResourceRequirements(
            cpu_cores=float(self.cpu_cores),
            gpu_cards=float(self.gpu_cards),
            memory_gb=float(self.memory_gb)
        )


@dataclass
class ServiceVariantDTO:
    """服务模型变体"""
    variant_id: str
    service_id: str
    resource_req: ResourceRequirements = field(default_factory=ResourceRequirements)
    processing_rate: float = 0.0  # 请求/秒
    accuracy: float = 0.0  # [0,1]
    model_size_mb: float = 0.0


@dataclass
class ServiceDTO:
    """微服务数据传输对象"""
    service_id: str
    name: str
    variants: List[ServiceVariantDTO] = field(default_factory=list)
    
    def get_variant(self, variant_id: str) -> ServiceVariantDTO:
        """获取指定变体"""
        for v in self.variants:
            if v.variant_id == variant_id:
                return v
        raise ValueError(f"变体 {variant_id} 不存在于服务 {self.service_id}")
    
    def get_default_variant(self) -> ServiceVariantDTO:
        """获取默认变体（第一个）"""
        if not self.variants:
            raise ValueError(f"服务 {self.service_id} 没有变体")
        return self.variants[0]


@dataclass
class ChainDTO:
    """服务调用链数据传输对象"""
    chain_id: str
    name: str
    service_sequence: List[str] = field(default_factory=list)
    sla_ms: float = 0.0
    arrival_rate: float = 0.0  # 请求/秒
    parallel_branches: Optional[List[Tuple[List[str], str]]] = None
    
    def get_critical_path(self) -> List[str]:
        """获取关键路径上的服务列表（简化版：返回顺序列表）"""
        return self.service_sequence.copy()


@dataclass
class RequestDTO:
    """请求流数据传输对象"""
    request_id: str
    chain_id: str
    arrival_rate: float = 0.0
    sla_ms: float = 0.0
    # MMPP参数（动态负载）
    mmpp_states: Optional[List[float]] = None
    mmpp_transitions: Optional[List[List[float]]] = None


@dataclass
class PlacementDecision:
    """部署策略输出决策"""
    # 部署矩阵: {(service_id, node_id): variant_id}
    X: Dict[Tuple[str, str], str] = field(default_factory=dict)
    # 实例数量: {(service_id, node_id): int}
    N: Dict[Tuple[str, str], int] = field(default_factory=dict)
    # 路由概率: {(src_s, src_n, dst_s, dst_n): prob}
    P: Dict[Tuple[str, str, str, str], float] = field(default_factory=dict)
    # 策略名称
    policy_name: str = "unknown"
    # 决策时间戳
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()
    
    def validate(self, nodes: List[NodeDTO], services: List[ServiceDTO]) -> Tuple[bool, str]:
        """
        验证决策合法性
        
        Returns:
            (is_valid, error_message)
        """
        # 检查资源约束
        node_capacity = {n.node_id: n.get_capacity() for n in nodes}
        node_usage = {n.node_id: ResourceRequirements() for n in nodes}
        
        service_map = {s.service_id: s for s in services}
        
        for (svc_id, node_id), var_id in self.X.items():
            if node_id not in node_capacity:
                return False, f"节点 {node_id} 不存在"
            if svc_id not in service_map:
                return False, f"服务 {svc_id} 不存在"
            
            svc = service_map[svc_id]
            try:
                var = svc.get_variant(var_id)
            except ValueError as e:
                return False, str(e)
            
            n_instances = self.N.get((svc_id, node_id), 1)
            usage = var.resource_req * n_instances
            node_usage[node_id] = node_usage[node_id] + usage
        
        for node_id, usage in node_usage.items():
            if not usage <= node_capacity[node_id]:
                return False, f"节点 {node_id} 资源不足"
        
        # 检查路由概率归一化
        from collections import defaultdict
        outgoing_probs = defaultdict(float)
        for (src_s, src_n, dst_s, dst_n), prob in self.P.items():
            outgoing_probs[(src_s, src_n)] += prob
        
        for key, total in outgoing_probs.items():
            if abs(total - 1.0) > 1e-6:
                return False, f"路由概率未归一化: {key} = {total}"
        
        return True, "OK"


@dataclass
class SimulationResult:
    """单次仿真实验结果"""
    # 端到端延迟: {chain_id: float}，单位ms
    e2e_delays: Dict[str, float] = field(default_factory=dict)
    # 队列长度: {(service_id, node_id): float}
    queue_lengths: Dict[Tuple[str, str], float] = field(default_factory=dict)
    # 利用率: {(service_id, node_id): float}，范围[0,1]
    utilization: Dict[Tuple[str, str], float] = field(default_factory=dict)
    # SLA满足情况: {chain_id: bool}
    sla_satisfaction: Dict[str, bool] = field(default_factory=dict)
    # 部署成本
    cost: float = 0.0
    # 平均精度
    accuracy: float = 0.0
    # 额外指标
    extra_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SimulationResult':
        """从字典反序列化"""
        return cls(**data)
    
    def get_avg_e2e_delay(self) -> float:
        """获取平均端到端延迟"""
        if not self.e2e_delays:
            return 0.0
        return sum(self.e2e_delays.values()) / len(self.e2e_delays)
    
    def get_sla_violation_rate(self) -> float:
        """获取SLA违反率"""
        if not self.sla_satisfaction:
            return 0.0
        violations = sum(1 for v in self.sla_satisfaction.values() if not v)
        return violations / len(self.sla_satisfaction)
