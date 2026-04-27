"""
解析仿真器（M/M/c模型）

基于排队论数学分析，计算稳态性能指标。
当前为占位实现，后续完善Erlang-C公式和流量方程。
"""

import math
from typing import List, Dict, Tuple
from src.core.interfaces import BaseSimulator
from src.core.dto import (
    NodeDTO, ServiceDTO, ChainDTO, RequestDTO,
    PlacementDecision, SimulationResult
)


class AnalyticalSimulator(BaseSimulator):
    """
    解析仿真器
    
    使用M/M/c排队模型进行数学分析，计算：
    - 端到端延迟（排队延迟 + 处理延迟 + 传输延迟）
    - 队列长度
    - 利用率
    - SLA满足情况
    """
    
    def __init__(self):
        super().__init__(name="Analytical")
    
    def simulate(self,
                 nodes: List[NodeDTO],
                 services: List[ServiceDTO],
                 chains: List[ChainDTO],
                 requests: List[RequestDTO],
                 decision: PlacementDecision) -> SimulationResult:
        """
        执行解析仿真
        
        当前为简化占位实现：
        1. 计算每个服务实例的利用率
        2. 使用简化公式估算延迟
        3. 汇总端到端延迟
        
        TODO: 完善Erlang-C公式和流量方程
        """
        result = SimulationResult()
        
        # 构建节点和服务映射
        node_map = {n.node_id: n for n in nodes}
        service_map = {s.service_id: s for s in services}
        
        # 计算每个部署实例的指标
        for (svc_id, node_id), variant_id in decision.X.items():
            svc = service_map[svc_id]
            node = node_map[node_id]
            variant = svc.get_variant(variant_id)
            
            # 获取实例数量
            n_instances = decision.N.get((svc_id, node_id), 1)
            
            # 计算到达率（简化：使用请求的到达率）
            arrival_rate = self._compute_arrival_rate(
                svc_id, node_id, requests, decision.P
            )
            
            # 计算处理速率（考虑节点速度因子）
            processing_rate = variant.processing_rate * node.speed_factor
            
            # 计算利用率
            if processing_rate * n_instances > 0:
                utilization = arrival_rate / (processing_rate * n_instances)
                utilization = min(utilization, 0.999)  # 防止溢出
            else:
                utilization = 0.0
            
            result.utilization[(svc_id, node_id)] = utilization
            
            # 计算排队延迟（简化M/M/1近似）
            if utilization < 1.0 and processing_rate > 0:
                # M/M/1: W = 1/(μ - λ)
                wait_time = 1.0 / (processing_rate * n_instances - arrival_rate)
                queue_length = arrival_rate * wait_time
            else:
                wait_time = float('inf')
                queue_length = float('inf')
            
            result.queue_lengths[(svc_id, node_id)] = queue_length
            
            # 计算处理延迟
            processing_delay = 1.0 / processing_rate if processing_rate > 0 else 0
            
            # 存储节点级延迟（用于后续汇总）
            self._store_delay(svc_id, node_id, wait_time + processing_delay)
        
        # 计算端到端延迟
        for chain in chains:
            e2e_delay = self._compute_e2e_delay(
                chain, decision, node_map
            )
            result.e2e_delays[chain.chain_id] = e2e_delay
            
            # 检查SLA
            request = next((r for r in requests if r.chain_id == chain.chain_id), None)
            if request:
                result.sla_satisfaction[chain.chain_id] = e2e_delay <= request.sla_ms
            else:
                result.sla_satisfaction[chain.chain_id] = e2e_delay <= chain.sla_ms
        
        # 计算成本（简化）
        result.cost = self._compute_cost(decision, nodes)
        
        # 计算精度（加权平均）
        result.accuracy = self._compute_accuracy(decision, services)
        
        return result
    
    def _compute_arrival_rate(self,
                              svc_id: str,
                              node_id: str,
                              requests: List[RequestDTO],
                              P: Dict[Tuple[str, str, str, str], float]) -> float:
        """
        计算服务实例的到达率
        
        简化实现：根据路由概率汇总到达率。
        TODO: 完善流量方程求解
        """
        total_rate = 0.0
        
        for request in requests:
            # 检查请求是否经过此服务
            # 简化：假设所有请求都经过所有服务
            # 实际应根据调用链和路由概率计算
            total_rate += request.arrival_rate
        
        # 根据路由概率分配
        # 简化：均匀分配
        return total_rate / max(len(P), 1)
    
    def _store_delay(self, svc_id: str, node_id: str, delay: float):
        """存储服务-节点延迟（内部缓存）"""
        if not hasattr(self, '_delay_cache'):
            self._delay_cache = {}
        self._delay_cache[(svc_id, node_id)] = delay
    
    def _compute_e2e_delay(self,
                           chain: ChainDTO,
                           decision: PlacementDecision,
                           node_map: Dict[str, NodeDTO]) -> float:
        """
        计算端到端延迟
        
        累加调用链上各服务的延迟和传输延迟。
        """
        total_delay = 0.0
        
        for i, svc_id in enumerate(chain.service_sequence):
            # 获取服务部署的节点
            node_id = None
            for (s, n) in decision.X.keys():
                if s == svc_id:
                    node_id = n
                    break
            
            if node_id is None:
                continue
            
            # 获取服务延迟
            delay = self._delay_cache.get((svc_id, node_id), 0.0)
            total_delay += delay * 1000  # 转换为ms
            
            # 添加传输延迟（简化：相邻服务间10ms）
            if i < len(chain.service_sequence) - 1:
                total_delay += 10.0
        
        return total_delay
    
    def _compute_cost(self,
                      decision: PlacementDecision,
                      nodes: List[NodeDTO]) -> float:
        """
        计算部署成本
        
        基于节点成本和实例数量。
        """
        node_cost = {n.node_id: n.cost_per_hour for n in nodes}
        total_cost = 0.0
        
        for (svc_id, node_id), n_instances in decision.N.items():
            total_cost += node_cost.get(node_id, 0.0) * n_instances
        
        return total_cost
    
    def _compute_accuracy(self,
                          decision: PlacementDecision,
                          services: List[ServiceDTO]) -> float:
        """
        计算平均精度
        
        加权平均各部署变体的精度。
        """
        service_map = {s.service_id: s for s in services}
        total_accuracy = 0.0
        total_weight = 0
        
        for (svc_id, node_id), variant_id in decision.X.items():
            svc = service_map[svc_id]
            variant = svc.get_variant(variant_id)
            
            n_instances = decision.N.get((svc_id, node_id), 1)
            total_accuracy += variant.accuracy * n_instances
            total_weight += n_instances
        
        return total_accuracy / total_weight if total_weight > 0 else 0.0
    
    def erlang_c(self, c: int, rho: float) -> float:
        """
        Erlang-C公式计算延迟概率
        
        C(c, rho) = (c * B(c, rho)) / (c - rho * (1 - B(c, rho)))
        
        其中B(c, rho)是Erlang-B公式。
        
        TODO: 实现完整的Erlang-C计算（含log-space和Hayward近似）
        
        Args:
            c: 服务器数量
            rho: 利用率（必须 < c）
        
        Returns:
            float: 延迟概率
        """
        if rho >= c:
            return 1.0
        
        # 简化占位：使用M/M/1近似
        # TODO: 实现完整的Erlang-B递归 + 转换
        return rho / c
