"""
抽象接口层：所有模块的契约定义

所有具体实现必须继承这些基类。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .dto import (
    NodeDTO, ServiceDTO, ChainDTO, RequestDTO,
    PlacementDecision, SimulationResult
)


class BasePlacementPolicy(ABC):
    """
    部署策略抽象基类
    
    所有部署算法（包括随机占位）必须继承此类。
    """
    
    def __init__(self, name: str = None):
        self._name = name or self.__class__.__name__
    
    @abstractmethod
    def select(self, 
               request: RequestDTO,
               nodes: List[NodeDTO],
               services: List[ServiceDTO],
               chains: List[ChainDTO]) -> PlacementDecision:
        """
        选择最优部署方案
        
        Args:
            request: 请求信息
            nodes: 可用节点列表
            services: 服务列表
            chains: 调用链列表
        
        Returns:
            PlacementDecision: 部署决策
        """
        pass
    
    def get_name(self) -> str:
        """返回策略名称"""
        return self._name
    
    def validate_decision(self,
                         decision: PlacementDecision,
                         nodes: List[NodeDTO],
                         services: List[ServiceDTO]) -> bool:
        """
        验证部署决策的合法性
        
        Args:
            decision: 部署决策
            nodes: 节点列表
            services: 服务列表
        
        Returns:
            bool: 是否合法
        """
        is_valid, _ = decision.validate(nodes, services)
        return is_valid


class BaseSimulator(ABC):
    """
    仿真器抽象基类
    
    支持解析仿真（M/M/c）和DES仿真。
    """
    
    def __init__(self, name: str = None):
        self._name = name or self.__class__.__name__
    
    @abstractmethod
    def simulate(self,
                 nodes: List[NodeDTO],
                 services: List[ServiceDTO],
                 chains: List[ChainDTO],
                 requests: List[RequestDTO],
                 decision: PlacementDecision) -> SimulationResult:
        """
        执行仿真
        
        Args:
            nodes: 节点列表
            services: 服务列表
            chains: 调用链列表
            requests: 请求列表
            decision: 部署决策
        
        Returns:
            SimulationResult: 仿真结果
        """
        pass
    
    def get_name(self) -> str:
        """返回仿真器名称"""
        return self._name


class BaseExperimentRunner(ABC):
    """
    实验运行器抽象基类
    
    管理实验配置、执行和结果收集。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.results: List[SimulationResult] = []
        self.policies: List[BasePlacementPolicy] = []
        self.simulator: Optional[BaseSimulator] = None
    
    def register_policy(self, policy: BasePlacementPolicy):
        """注册部署策略"""
        self.policies.append(policy)
    
    def set_simulator(self, simulator: BaseSimulator):
        """设置仿真器"""
        self.simulator = simulator
    
    @abstractmethod
    def run(self) -> Dict[str, List[SimulationResult]]:
        """
        运行实验
        
        Returns:
            Dict[str, List[SimulationResult]]: {policy_name: [results]}
        """
        pass
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载实验配置
        
        Args:
            config_path: 配置文件路径
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        pass


class BaseMetricCollector(ABC):
    """
    指标收集器抽象基类
    
    负责收集和汇总仿真指标。
    """
    
    @abstractmethod
    def collect(self, result: SimulationResult) -> Dict[str, float]:
        """
        收集指标
        
        Args:
            result: 仿真结果
        
        Returns:
            Dict[str, float]: 指标字典
        """
        pass
    
    @abstractmethod
    def summarize(self, results: List[SimulationResult]) -> Dict[str, Any]:
        """
        汇总多次实验结果
        
        Args:
            results: 多次仿真结果
        
        Returns:
            Dict[str, Any]: 汇总统计
        """
        pass


class BaseLogger(ABC):
    """
    日志记录器抽象基类
    """
    
    @abstractmethod
    def log_experiment_start(self, experiment_id: str, config: Dict[str, Any]):
        """记录实验开始"""
        pass
    
    @abstractmethod
    def log_simulation_result(self, policy_name: str, result: SimulationResult):
        """记录仿真结果"""
        pass
    
    @abstractmethod
    def log_experiment_end(self, experiment_id: str, summary: Dict[str, Any]):
        """记录实验结束"""
        pass
