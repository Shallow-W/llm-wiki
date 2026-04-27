# 工作开发流规范

## 一、Git 开发管理规范

### 1.1 分支策略

```
main (保护分支，永远可运行)
  └── feature/xxx (功能分支)
  └── fix/xxx (修复分支)
  └── refactor/xxx (重构分支)
  └── docs/xxx (文档分支)
```

**分支命名规范**:
- `feature/ams-core` — 新功能
- `fix/erlang-c-overflow` — Bug修复
- `refactor/experiment-runner` — 代码重构
- `docs/api-reference` — 文档更新

### 1.2 开发流程

```bash
# 1. 更新主分支
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/xxx

# 3. 开发（遵循代码规范）
# ...

# 4. 提交前检查
git status
git diff

# 5. 提交（遵循中文Commit规范）
git add <files>
git commit -m "feat(ams): 实现自适应模型选择核心逻辑

- 添加贪心变体选择算法
- 实现资源硬约束过滤
- 优化实例数量和路由策略

关联: #15"

# 6. 推送
git push -u origin feature/xxx

# 7. 创建 PR（Code Review）
# 8. Review 通过后合并到 main
# 9. 删除功能分支
```

### 1.3 中文 Commit 规范

**格式**:
```
<类型>(<模块>): <简短描述>

<详细描述>

<关联信息>
```

**类型**:
| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(ams): 实现自适应模型选择` |
| `fix` | Bug修复 | `fix(erlang-c): 修复大c时数值溢出` |
| `docs` | 文档更新 | `docs(readme): 更新架构图` |
| `style` | 代码格式 | `style(core): 统一缩进为4空格` |
| `refactor` | 重构 | `refactor(engine): 优化流量方程求解器` |
| `test` | 测试相关 | `test(ams): 添加单元测试` |
| `chore` | 构建/工具 | `chore(deps): 添加Hydra依赖` |
| `perf` | 性能优化 | `perf(delay): 优化关键路径计算` |

**模块**:
| 模块名 | 说明 |
|--------|------|
| `core` | 核心引擎层 |
| `models` | 数据模型层 |
| `algorithm` | 算法层 |
| `experiment` | 实验框架层 |
| `stats` | 验证统计层 |
| `config` | 配置层 |
| `docs` | 文档 |

**示例**:
```bash
# 好的提交
git commit -m "feat(algorithm): 实现AMS贪心变体选择

- 根据节点负载动态选择light/medium/heavy变体
- 添加资源约束硬过滤，确保不超出CPU/GPU/内存
- 优化目标：最小化端到端延迟

关联: #15
评审: #23"

# 不好的提交
git commit -m "update"  # ❌ 无类型、无模块、无描述
git commit -m "fix bug" # ❌ 无模块、描述不清
```

### 1.4 PR 规范

**PR 标题**: `[类型] 简要描述`
- `[Feature] 实现AMS自适应模型选择`
- `[Fix] 修复Erlang-C大c时数值溢出`

**PR 描述模板**:
```markdown
## 变更内容
- 实现了 xxx 功能
- 修复了 yyy 问题
- 优化了 zzz 性能

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试验证

## 相关 Issue
关联: #15
阻塞: #23
```

### 1.5 Code Review 检查项

- [ ] 代码逻辑是否正确？
- [ ] 是否符合项目编码规范？
- [ ] 是否有潜在的性能问题？
- [ ] 错误处理是否完善？
- [ ] 测试是否充分？
- [ ] 文档是否更新？

---

## 二、文档撰写规范

### 2.1 文档类型

| 文档 | 路径 | 说明 | 更新时机 |
|------|------|------|---------|
| 架构简介 | `docs/ARCHITECTURE.md` | 整体架构、数据流、接口 | 架构变更时 |
| 工作流规范 | `docs/WORKFLOW.md` | Git规范、Commit规范、Review流程 | 流程变更时 |
| 开发指引 | `docs/GUIDE.md` | 开发指引、文件索引、FAQ | 持续更新 |
| 数据结构 | `docs/DATA_STRUCTURES.md` | DTO定义、接口规范、序列化 | 数据模型变更时 |
| 实验设计 | `docs/plans/iterations/*.md` | 实验框架设计文档 | 设计迭代时 |
| API文档 | 代码docstring | 函数/类/模块文档 | 代码变更时 |

### 2.2 文档撰写原则

1. **代码即文档**: 核心逻辑必须有docstring
2. **变更即更新**: 代码变更时同步更新相关文档
3. **中文为主**: 项目文档使用中文，代码注释使用英文
4. **示例驱动**: 复杂概念必须附示例

### 2.3 Docstring 规范

```python
def solve_traffic_equations(X, P, chains, requests, max_iter=1000, tol=1e-8):
    """
    求解流量方程，计算每个服务-节点对的到达率。
    
    使用Gauss-Seidel迭代法求解线性系统：
        λ_{m,n} = Σ_f x_{m,n}·λ_f + Σ_{m',n'} P_{m',n'→m,n}·λ_{m',n'}
    
    Args:
        X: 部署矩阵，{(service_id, node_id): variant_id}
        P: 路由概率矩阵，{(s1,n1,s2,n2): prob}
        chains: 调用链列表 [Chain]
        requests: 请求流 {chain_id: Request}
        max_iter: 最大迭代次数，默认1000
        tol: 收敛阈值，默认1e-8
    
    Returns:
        (λ, converged, iterations): 
            λ - 到达率矩阵 {(service_id, node_id): rate}
            converged - 是否收敛
            iterations - 实际迭代次数
    
    Raises:
        RuntimeError: 迭代发散时抛出
    
    Example:
        >>> λ, ok, iters = solve_traffic_equations(X, P, chains, reqs)
        >>> assert ok, f"未收敛，迭代{iters}次"
    """
```

---

## 三、数据结构文档规范

### 3.1 DTO 定义规范

所有DTO使用 `@dataclass` 定义，必须包含:
- 类型注解
- 默认值（如适用）
- `to_dict()` / `from_dict()` 序列化方法

```python
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class NodeDTO:
    """节点数据传输对象"""
    node_id: str
    cpu_cores: int
    gpu_cards: int
    memory_gb: int
    speed_factor: float = 1.0
    cost_per_hour: float = 0.0
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NodeDTO':
        """从字典反序列化"""
        return cls(**data)
```

### 3.2 接口定义规范

抽象接口使用 `ABC` + `abstractmethod`:

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class BasePlacementPolicy(ABC):
    """部署策略抽象基类"""
    
    @abstractmethod
    def select(self, request: 'RequestDTO', nodes: List['NodeDTO'],
               services: List['ServiceDTO']) -> 'PlacementDecision':
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
```

---

## 四、模块开发 Review 流程

### 4.1 Review 触发条件

**必须触发 Review**:
- 核心引擎层任何修改
- AMS算法修改
- 实验框架修改
- 新增Baseline

**可选触发 Review**:
- 文档更新
- 配置文件修改
- 单元测试补充

### 4.2 Review 流程（三轮迭代）

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 开发者完成代码任务                                   │
│  └── 自测通过 → 提交PR                                       │
├─────────────────────────────────────────────────────────────┤
│  Step 2: 启动 Round 1 Review                                 │
│  ├── Reviewer A (技术角度): 代码正确性、性能、边界情况         │
│  └── Reviewer B (业务角度): 需求理解、完整性、可测试性         │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 开发者根据反馈修复                                   │
│  └── 修复后进入 Round 2                                      │
├─────────────────────────────────────────────────────────────┤
│  Step 4: Round 2 Review                                      │
│  ├── Reviewer A: 验证修复是否充分                             │
│  └── Reviewer B: 验证是否有新问题引入                         │
├─────────────────────────────────────────────────────────────┤
│  Step 5: 开发者根据反馈修复                                   │
│  └── 修复后进入 Round 3                                      │
├─────────────────────────────────────────────────────────────┤
│  Step 6: Round 3 Review (最终确认)                            │
│  ├── Reviewer A: 最终技术确认                                 │
│  └── Reviewer B: 最终业务确认                                 │
├─────────────────────────────────────────────────────────────┤
│  Step 7: 三轮都通过 → 合并到main                              │
│  └── 任一不通过 → 继续修复直到通过                            │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Reviewer 分工

**Reviewer A — 技术角度**:
- 代码逻辑正确性
- 性能优化空间
- 边界情况处理
- 错误处理完善性
- 代码风格规范

**Reviewer B — 业务/科研角度**:
- 需求理解准确性
- 实验设计完整性
- 与论文一致性
- 可复现性保障
- 文档充分性

### 4.4 Review 输出格式

```markdown
## Review 报告

### 总体判断
通过 / 不通过

### 问题列表
#### 🔴 高严重（必须修复）
1. xxx
2. xxx

#### 🟡 中严重（建议修复）
1. xxx
2. xxx

#### 🟢 低严重（可选优化）
1. xxx

### 改进建议
1. xxx
2. xxx
```

### 4.5 Review 终止条件

**必须同时满足**:
1. ✅ 完成至少 3 轮 Review
2. ✅ 每轮两个 Reviewer 都给出 "通过"
3. ✅ 第3轮与第2轮相比没有新问题引入

**不满足以上条件不得合并代码！**

---

## 五、开发检查清单

### 5.1 代码提交前检查

- [ ] 代码是否通过所有单元测试？
- [ ] 是否有未使用的导入/变量？
- [ ] 代码风格是否符合项目规范（PEP8）？
- [ ] 是否更新了相关文档？
- [ ] 是否添加了必要的注释和docstring？
- [ ] 是否处理了所有边界情况？
- [ ] 是否有性能隐患？

### 5.2 PR 创建前检查

- [ ] 分支是否基于最新 main？
- [ ] Commit 是否符合规范？
- [ ] 是否包含单元测试？
- [ ] 是否更新了 CHANGELOG？
- [ ] 是否关联了相关 Issue？

### 5.3 合并前检查

- [ ] Code Review 三轮全部通过？
- [ ] CI 检查全部通过？
- [ ] 文档是否同步更新？
- [ ] 是否删除了功能分支？
