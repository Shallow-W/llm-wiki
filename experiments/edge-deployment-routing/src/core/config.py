"""
配置系统：YAML配置加载和管理

使用Hydra风格的分层配置，支持YAML覆盖。
"""

import yaml
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class SimulationConfig:
    """仿真参数配置"""
    warmup_period: int = 300        # 预热期(秒)
    run_length: int = 3600          # 运行长度(秒)
    num_replications: int = 30      # 重复次数
    seed: int = 42                  # 随机种子


@dataclass
class OutputConfig:
    """输出配置"""
    results_dir: str = "./results"
    log_dir: str = "./logs"
    log_level: str = "INFO"
    save_intermediate: bool = True
    plot_format: str = "png"


@dataclass
class ExperimentConfig:
    """
    实验配置
    
    使用Hydra风格的分层配置。
    """
    # 实验标识
    experiment_id: str = "default"
    name: str = "Default Experiment"
    description: str = ""
    
    # 网络规模
    scale: str = "medium"  # 'small' | 'medium' | 'large'
    
    # 配置引用
    network_config: str = "base/network.yaml"
    services_config: str = "base/services.yaml"
    chains_config: str = "base/chains.yaml"
    
    # 算法列表
    algorithms: List[str] = field(default_factory=lambda: ["random"])
    
    # 仿真参数
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    
    # 输出配置
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # 扩展参数
    extra: Dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """
    配置加载器
    
    支持从YAML文件加载配置，支持配置继承和覆盖。
    """
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Any] = {}
    
    def load(self, config_path: str) -> ExperimentConfig:
        """
        加载实验配置
        
        Args:
            config_path: 配置文件路径（相对于config_dir）
        
        Returns:
            ExperimentConfig: 实验配置对象
        """
        full_path = self.config_dir / config_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 处理defaults继承
        if 'defaults' in data:
            data = self._merge_defaults(data, full_path.parent)
        
        return self._dict_to_config(data)
    
    def load_network(self, config_path: str) -> Dict[str, Any]:
        """加载网络配置"""
        full_path = self.config_dir / config_path
        with open(full_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _merge_defaults(self, data: Dict, base_path: Path) -> Dict:
        """合并默认配置"""
        defaults = data.pop('defaults', [])
        merged = {}
        
        for default in defaults:
            if default == '_self_':
                continue
            
            default_path = base_path / f"{default}.yaml"
            if default_path.exists():
                with open(default_path, 'r', encoding='utf-8') as f:
                    default_data = yaml.safe_load(f)
                merged.update(default_data)
        
        # 当前配置覆盖默认配置
        merged.update(data)
        return merged
    
    def _dict_to_config(self, data: Dict) -> ExperimentConfig:
        """将字典转换为配置对象"""
        # 提取嵌套配置
        sim_data = data.pop('simulation', {})
        out_data = data.pop('output', {})
        
        sim_config = SimulationConfig(**sim_data)
        out_config = OutputConfig(**out_data)
        
        return ExperimentConfig(
            simulation=sim_config,
            output=out_config,
            **data
        )
    
    def save(self, config: ExperimentConfig, path: str):
        """
        保存配置到文件
        
        Args:
            config: 配置对象
            path: 保存路径
        """
        full_path = self.config_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._config_to_dict(config)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    
    def _config_to_dict(self, config: ExperimentConfig) -> Dict:
        """将配置对象转换为字典"""
        return {
            'experiment_id': config.experiment_id,
            'name': config.name,
            'description': config.description,
            'scale': config.scale,
            'network_config': config.network_config,
            'services_config': config.services_config,
            'chains_config': config.chains_config,
            'algorithms': config.algorithms,
            'simulation': {
                'warmup_period': config.simulation.warmup_period,
                'run_length': config.simulation.run_length,
                'num_replications': config.simulation.num_replications,
                'seed': config.simulation.seed,
            },
            'output': {
                'results_dir': config.output.results_dir,
                'log_dir': config.output.log_dir,
                'log_level': config.output.log_level,
                'save_intermediate': config.output.save_intermediate,
                'plot_format': config.output.plot_format,
            },
            'extra': config.extra,
        }


def load_experiment_config(config_path: str, config_dir: str = "configs") -> ExperimentConfig:
    """
    便捷函数：加载实验配置
    
    Args:
        config_path: 配置文件路径
        config_dir: 配置目录
    
    Returns:
        ExperimentConfig: 实验配置
    """
    loader = ConfigLoader(config_dir)
    return loader.load(config_path)
