"""
随机部署策略（占位实现）

用于基建阶段验证系统流程，后续会被AMS算法替换。
"""

import random
from typing import List, Dict, Tuple
from src.core.interfaces import BasePlacementPolicy
from src.core.dto import (
    NodeDTO, ServiceDTO, ChainDTO, RequestDTO,
    PlacementDecision, ResourceRequirements
)


class RandomPlacementPolicy(BasePlacementPolicy):
    """
    随机部署策略
    
    随机选择节点和服务变体进行部署，确保满足资源约束。
    用于系统基建验证和基线对比。
    """
    
    def __init__(self, seed: int = 42):
        super().__init__(name="Random")
        self.rng = random.Random(seed)
    
    def select(self,
               request: RequestDTO,
               nodes: List[NodeDTO],
               services: List[ServiceDTO],
               chains: List[ChainDTO]) -> PlacementDecision:
        """
        随机选择部署方案
        
        策略：
        1. 对每个服务，随机选择一个节点
        2. 随机选择一个变体
        3. 检查资源约束，不满足则重试
        4. 生成均匀路由概率
        """
        decision = PlacementDecision(policy_name=self._name)
        
        # 初始化节点资源跟踪
        node_capacity = {n.node_id: n.get_capacity() for n in nodes}
        node_usage = {n.node_id: ResourceRequirements() for n in nodes}
        
        # 获取请求对应的调用链
        chain = next((c for c in chains if c.chain_id == request.chain_id), None)
        if chain is None:
            raise ValueError(f"调用链 {request.chain_id} 不存在")
        
        # 对调用链上的每个服务进行部署
        for svc_id in chain.service_sequence:
            svc = next((s for s in services if s.service_id == svc_id), None)
            if svc is None:
                raise ValueError(f"服务 {svc_id} 不存在")
            
            # 尝试随机部署
            placed = False
            max_attempts = 100
            
            for _ in range(max_attempts):
                # 随机选择节点
                node = self.rng.choice(nodes)
                
                # 随机选择变体
                variant = self.rng.choice(svc.variants)
                
                # 检查资源约束
                new_usage = node_usage[node.node_id] + variant.resource_req
                if new_usage <= node_capacity[node.node_id]:
                    # 满足约束，执行部署
                    decision.X[(svc_id, node.node_id)] = variant.variant_id
                    decision.N[(svc_id, node.node_id)] = 1
                    node_usage[node.node_id] = new_usage
                    placed = True
                    break
            
            if not placed:
                raise RuntimeError(f"无法为服务 {svc_id} 找到满足资源约束的部署方案")
        
        # 生成路由概率（均匀分布）
        decision.P = self._generate_uniform_routing(
            chain.service_sequence, nodes, decision.X
        )
        
        return decision
    
    def _generate_uniform_routing(self,
                                  service_sequence: List[str],
                                  nodes: List[NodeDTO],
                                  X: Dict[Tuple[str, str], str]) -> Dict[Tuple[str, str, str, str], float]:
        """
        生成均匀路由概率
        
        对每个服务的每个实例，均匀路由到下一个服务的所有实例。
        """
        P = {}
        node_ids = [n.node_id for n in nodes]
        
        for i in range(len(service_sequence) - 1):
            curr_svc = service_sequence[i]
            next_svc = service_sequence[i + 1]
            
            # 获取当前服务和下一个服务的部署节点
            curr_nodes = [n for n in node_ids if (curr_svc, n) in X]
            next_nodes = [n for n in node_ids if (next_svc, n) in X]
            
            if not curr_nodes or not next_nodes:
                continue
            
            # 均匀路由概率
            prob = 1.0 / len(next_nodes)
            
            for curr_n in curr_nodes:
                for next_n in next_nodes:
                    P[(curr_svc, curr_n, next_svc, next_n)] = prob
        
        return P
