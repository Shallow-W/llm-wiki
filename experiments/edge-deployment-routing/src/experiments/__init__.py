"""
实验框架模块

包含实验运行器、指标收集器和结果分析器。
"""

from .runner import ExperimentRunner
from .metrics import DefaultMetricCollector

__all__ = ['ExperimentRunner', 'DefaultMetricCollector']
