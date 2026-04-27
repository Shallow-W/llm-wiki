# 开发指引文件

## 一、项目文件索引

### 1.1 设计文档

| 文件 | 路径 | 说明 |
|------|------|------|
| **架构简介** | `docs/ARCHITECTURE.md` | 整体架构、数据流、核心接口 |
| **工作流规范** | `docs/WORKFLOW.md` | Git规范、Commit规范、Review流程 |
| **开发指引** | `docs/GUIDE.md` | 本文件：文件索引、开发指引、FAQ |
| **数据结构** | `docs/DATA_STRUCTURES.md` | DTO定义、接口规范、序列化 |
| **实验框架v4** | `docs/plans/iterations/experiment-framework-v4-final.md` | 完整实验设计文档 |
| **实验框架v3** | `docs/plans/iterations/experiment-framework-v3.md` | 历史版本 |
| **实验框架v2** | `docs/plans/iterations/experiment-framework-v2.md` | 历史版本 |
| **实验框架v1** | `docs/plans/iterations/experiment-framework-v1.md` | 历史版本 |

### 1.2 核心公式与参数

| 内容 | 路径 | 说明 |
|------|------|------|
| **关键公式速查** | `docs/plans/iterations/experiment-framework-v4-final.md` 第9节 | Erlang-C、流量方程、延迟计算 |
| **参数配置表** | `docs/plans/iterations/experiment-framework-v4-final.md` 第6节 | 20+参数完整表格 |
| **节点配置** | `docs/plans/iterations/experiment-framework-v4-final.md` 第1.1节 | 异构节点详细配置 |
| **服务变体** | `docs/plans/iterations/experiment-framework-v4-final.md` 第1.2节 | light/medium/heavy参数 |

### 1.3 代码目录结构（规划）

```
edge-deployment-routing/
├── docs/                           # 文档目录
│   ├── ARCHITECTURE.md             # 架构简介
│   ├── WORKFLOW.md                 # 工作流规范
│   ├── GUIDE.md                    # 开发指引（本文件）
│   ├── DATA_STRUCTURES.md          # 数据结构文档
│   └── plans/                      # 设计文档
│       └── iterations/             # 迭代版本
│           ├── experiment-framework-v4-final.md
│           ├── experiment-framework-v3.md
│           ├── experiment-framework-v2.md
│           └── experiment-framework-v1.md
│
├── src/                            # 源代码
│   ├── __init__.py
│   ├── core/                       # 核心引擎层
│   │   ├── __init__.py
│   │   ├── erlang_c.py             # Erlang-C计算
│   │   ├── traffic_solver.py       # 流量方程求解器
│   │   ├── delay_calculator.py     # 端到端延迟计算
│   │   └── qna_validation.py       # QNA验证(DES对比)
│   │
│   ├── models/                     # 数据模型层
│   │   ├── __init__.py
│   │   ├── node.py                 # 节点模型
│   │   ├── service.py              # 服务模型
│   │   ├── chain.py                # 调用链模型
│   │   ├── request.py              # 请求模型
│   │   └── registry.py             # 服务注册表
│   │
│   ├── algorithms/                 # 算法策略层
│   │   ├── __init__.py
│   │   ├── base.py                 # BasePlacementPolicy抽象类
│   │   ├── ams.py                  # AMS算法
│   │   └── baselines/              # Baseline算法
│   │       ├── fixed_light.py
│   │       ├── fixed_medium.py
│   │       ├── fixed_heavy.py
│   │       ├── random_baseline.py
│   │       ├── greedy_local.py
│   │       ├── cloud_only.py
│   │       ├── edge_only.py
│   │       └── awstream.py
│   │
│   ├── experiments/                # 实验编排层
│   │   ├── __init__.py
│   │   ├── runner.py               # ExperimentRunner
│   │   └── configs/                # 实验配置YAML
│   │       ├── exp1_static.yaml
│   │       ├── exp2_heterogeneity.yaml
│   │       ├── exp3_scalability.yaml
│   │       ├── exp4_dynamic.yaml
│   │       ├── exp5_robustness.yaml
│   │       ├── exp6_ablation.yaml
│   │       ├── exp7_accuracy.yaml
│   │       └── exp8_overhead.yaml
│   │
│   └── stats/                      # 验证统计层
│       ├── __init__.py
│       ├── confidence_interval.py  # 置信区间
│       ├── significance_test.py    # 显著性检验
│       └── plots.py                # 绘图脚本
│
├── tests/                          # 测试目录
│   ├── __init__.py
│   ├── fixtures.py                 # 测试fixtures
│   ├── test_erlang_c.py            # Erlang-C测试
│   ├── test_traffic_solver.py      # 流量方程测试
│   ├── test_delay_calculator.py    # 延迟计算测试
│   └── test_ams.py                 # AMS算法测试
│
├── configs/                        # 全局配置
│   ├── base.yaml                   # 基础配置
│   ├── small_scale.yaml            # 小规模覆盖
│   ├── medium_scale.yaml           # 中规模覆盖
│   └── large_scale.yaml            # 大规模覆盖
│
├── main.py                         # 入口程序
├── pyproject.toml                  # 项目依赖
├── requirements.txt                # 依赖列表
└── README.md                       # 项目说明
```

---

## 二、快速开始

### 2.1 环境搭建

```bash
# 1. 克隆仓库
git clone <repo-url>
cd edge-deployment-routing

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "from src.core.erlang_c import erlang_c; print('OK')"
```

### 2.2 运行单个实验

```bash
# 运行实验1（静态基准）
python main.py experiment=exp1_static

# 运行实验3（可扩展性，大规模）
python main.py experiment=exp3_scalability scale=large

# 运行所有实验
python main.py --run-all
```

### 2.3 运行单元测试

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_erlang_c.py -v

# 生成覆盖率报告
pytest --cov=src tests/
```

---

## 三、开发指引

### 3.1 新增模块开发流程

```
1. 阅读相关设计文档
   └── docs/plans/iterations/experiment-framework-v4-final.md

2. 定义数据接口（DTO）
   └── 更新 docs/DATA_STRUCTURES.md

3. 实现核心逻辑
   └── 遵循 WORKFLOW.md 中的代码规范

4. 编写单元测试
   └── tests/test_xxx.py

5. 自测通过
   └── pytest tests/test_xxx.py -v

6. 提交代码
   └── git commit -m "feat(module): 描述"

7. 触发Review（三轮）
   └── 创建PR → Reviewer A + Reviewer B → 修复 → 合并

8. 更新文档
   └── ARCHITECTURE.md / GUIDE.md / DATA_STRUCTURES.md
```

### 3.2 核心引擎层开发要点

**Erlang-C模块** (`src/core/erlang_c.py`):
- 必须支持三种计算方式：稳定递推、log-space、Hayward近似
- 自动根据c的大小选择最优方法
- 单元测试覆盖c∈[1, 500], ρ∈[0.1, 0.95]

**流量方程求解器** (`src/core/traffic_solver.py`):
- Gauss-Seidel迭代，支持收敛检测
- 稳定性检查（ρ < 1）
- 发散时返回警告而非崩溃

**延迟计算器** (`src/core/delay_calculator.py`):
- 关键路径法计算端到端延迟
- 支持串行链和并行分支（max-of-branches）

### 3.3 算法层开发要点

**AMS算法** (`src/algorithms/ams.py`):
- 继承BasePlacementPolicy
- 贪心变体选择 + 资源硬过滤
- 优化目标：最小化加权端到端延迟

**Baseline算法** (`src/algorithms/baselines/*.py`):
- 统一继承BasePlacementPolicy
- 每个baseline独立文件
- 必须实现get_name()方法

### 3.4 实验层开发要点

**ExperimentRunner** (`src/experiments/runner.py`):
- 加载YAML配置
- 遍历所有算法组合
- 收集结果并输出CSV/JSON

**实验配置YAML** (`src/experiments/configs/*.yaml`):
- 继承base.yaml
- 覆盖特定参数
- 明确实验变量和固定参数

---

## 四、FAQ

### Q1: 如何添加新的Baseline算法？

```python
# 1. 创建文件 src/algorithms/baselines/my_baseline.py
from src.algorithms.base import BasePlacementPolicy

class MyBaseline(BasePlacementPolicy):
    def select(self, request, nodes, services):
        # 实现选择逻辑
        return PlacementDecision(...)
    
    def get_name(self):
        return "MyBaseline"

# 2. 在 ExperimentRunner 中注册
# 3. 编写单元测试 tests/test_baselines.py
# 4. 更新文档 ARCHITECTURE.md
```

### Q2: 如何添加新的实验场景？

```yaml
# 1. 创建配置文件 src/experiments/configs/exp9_my_exp.yaml
defaults:
  - base

experiment:
  name: "my_experiment"
  description: "描述"
  
# 2. 在 runner.py 中注册
# 3. 更新文档和README
```

### Q3: 如何调试AMS算法？

```python
# 启用日志记录
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用toy example
from tests.fixtures import TINY_NETWORK
from src.algorithms.ams import AMS

ams = AMS()
result = ams.select(request, TINY_NETWORK.nodes, TINY_NETWORK.services)
print(result)
```

### Q4: 解析仿真结果与预期不符？

1. 检查参数配置是否正确
2. 验证Erlang-C计算（与标准表对比）
3. 检查流量方程是否收敛
4. 使用DES验证（SimPy）对比
5. 查看日志中的决策上下文

### Q5: 如何生成投稿级图表？

```python
from src.stats.plots import plot_latency_comparison, plot_heatmap

# 实验完成后自动生成
plot_latency_comparison(results, output="figures/fig3_latency.pdf")
plot_heatmap(utilization, output="figures/fig4_heatmap.pdf")
```

---

## 五、关键联系人

| 角色 | 职责 |
|------|------|
| 项目负责人 | 整体架构设计、关键决策 |
| 核心引擎负责人 | Erlang-C、流量方程、延迟计算 |
| 算法负责人 | AMS、Baseline、Oracle |
| 实验负责人 | ExperimentRunner、配置、执行 |
| 验证负责人 | QNA验证、统计检验、绘图 |

---

## 六、外部资源

| 资源 | 链接 | 说明 |
|------|------|------|
| Whitt's QNA | 论文引用 | 排队网络分析器 |
| Erlang-C标准表 | 在线计算器 | 验证数值正确性 |
| SimPy文档 | https://simpy.readthedocs.io | DES验证 |
| Hydra文档 | https://hydra.cc | 配置管理 |

---

## 七、更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-27 | v1.0 | 初始版本，基于v4实验框架 |
