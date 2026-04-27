# Experiment Framework v1: Heterogeneous Edge Network with Dynamic Model Selection

## Core Innovation

**Problem**: In heterogeneous edge networks, different nodes have different resources (CPU/GPU/memory). Traditional approaches use fixed model variants for all nodes, leading to suboptimal performance.

**Our Solution**: Dynamically search and select the most suitable model variant for each node based on current load, node capabilities, and end-to-end latency requirements.

**Key Difference from Baselines**:
- Baselines: Use fixed model variant (e.g., always "medium") across all nodes
- Our Algorithm: Adaptively selects from {light, medium, heavy} per node based on load

---

## 1. System Model

### 1.1 Network Topology (Heterogeneous)

```
┌─────────────────────────────────────────────────────────────┐
│                    Heterogeneous Edge Network                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐│
│   │  Edge 1     │←────→│  Edge 2     │←────→│  Edge 3     ││
│   │  [High-End] │ 5ms  │  [Mid]      │ 5ms  │  [Low]      ││
│   │  CPU:16     │      │  CPU:8      │      │  CPU:4      ││
│   │  GPU:4      │      │  GPU:2      │      │  GPU:0      ││
│   │  Mem:64GB   │      │  Mem:32GB   │      │  Mem:16GB   ││
│   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘│
│          │                    │                    │       │
│          └────────────────────┼────────────────────┘       │
│                               │                            │
│                          ┌────┴────┐                       │
│                          │ Cloud   │                       │
│                          │ [Ultra] │                       │
│                          │ CPU:64  │                       │
│                          │ GPU:8   │                       │
│                          └─────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Node Categories**:
| Type | CPU Cores | GPU Cards | Memory | Example |
|------|-----------|-----------|--------|---------|
| Low-end | 4 | 0 | 16GB | Raspberry Pi cluster |
| Mid-range | 8 | 2 | 32GB | Edge server |
| High-end | 16 | 4 | 64GB | Edge data center |
| Cloud | 64 | 8 | 256GB | Central cloud |

### 1.2 Service Model with Multiple Variants

Each microservice has **K model variants** with different accuracy-latency trade-offs:

| Variant | Accuracy | Processing Rate (req/s) | GPU Memory | GPU Required |
|---------|----------|------------------------|------------|--------------|
| light (k=1) | 85% | 50 | 500MB | 0.5 |
| medium (k=2) | 90% | 25 | 2000MB | 1.0 |
| heavy (k=3) | 95% | 10 | 8000MB | 2.0 |

**Key Insight**: 
- High-load → light variant (faster, less queuing)
- Low-load → heavy variant (better accuracy)
- Heterogeneous nodes → different optimal variants

### 1.3 Request Model

- **Arrival Process**: Poisson process with rate λ_f for flow f
- **Service Chain**: DAG of microservices (e.g., A→B→C→D)
- **SLA Constraint**: Maximum end-to-end delay T_f^max

---

## 2. Analytical Simulation Framework (NOT Discrete Event Simulation)

### 2.1 Core Principle

Instead of simulating individual requests over time, we **directly compute steady-state performance metrics** using queuing theory formulas.

```
Input: Network topology, service variants, arrival rates, deployment decisions
↓
Open Jackson Queuing Network Analysis
↓
Direct Calculation (NO event-by-event simulation)
↓
Output: Average delay, queue lengths, utilization, success rate
```

### 2.2 Mathematical Model

#### Step 1: Flow Merging (Burke's Theorem)

For each service m at node v, compute total arrival rate:

```
λ^m_v = Σ_f x^m_v · λ_f                          (external arrivals)
      + Σ_r Σ_i Σ_v' P(r)_mi,v'→m,v · λ^mi_v'    (routed arrivals)
```

Where:
- x^m_v = 1 if service m is deployed at node v
- P(r)_mi,v'→m,v = routing probability from service i at v' to service m at v

#### Step 2: Service Intensity (Stability Check)

```
ρ^m_v,k = λ^m_v / (N^m_v · μ_m,k)
```

Where:
- N^m_v = number of container instances
- μ_m,k = processing rate of variant k
- **Must have**: ρ^m_v,k < 1 for stability

#### Step 3: M/M/c Queueing Analysis (Erlang-C)

```
Average queue length:    L^m_v,k = C(N^m_v, ρ^m_v,k) · ρ^m_v,k / (1 - ρ^m_v,k)
Average waiting time:    W^m_v,k = L^m_v,k / λ^m_v
Average service time:    S^m_v,k = 1 / μ_m,k
Average response time:   R^m_v,k = W^m_v,k + S^m_v,k
```

Where C(N, ρ) is the Erlang-C formula.

#### Step 4: End-to-End Delay

```
E[T_f] = Σ_(m,v)∈path R^m_v,k + Σ_(v_i,v_j)∈path D_vi,v_j
```

Where D_vi,v_j = propagation delay + data_size / bandwidth

#### Step 5: SLA Satisfaction

```
η_f = 1 if E[T_f] ≤ T_f^max, else 0
Overall success rate: η = Σ_f η_f · λ_f / Σ_f λ_f
```

### 2.3 Why Analytical (Not DES)

| Aspect | Analytical (Our Approach) | Discrete Event Simulation |
|--------|--------------------------|---------------------------|
| **Speed** | Fast (seconds) | Slow (minutes to hours) |
| **Accuracy** | Exact for M/M/c | Approximate (variance) |
| **Scalability** | Excellent | Limited |
| **Dynamic Load** | Requires iterative update | Natural fit |
| **Suitable for** | Parameter sweep, optimization | Complex non-Markovian systems |

**Trade-off**: We assume Poisson arrivals and exponential service times (standard in literature).

---

## 3. Algorithm Design

### 3.1 Baseline Algorithms (Fixed Model)

| Baseline | Description | Model Selection |
|----------|-------------|-----------------|
| **Fixed-Light** | Always use light variant everywhere | Fixed: k=1 |
| **Fixed-Medium** | Always use medium variant everywhere | Fixed: k=2 |
| **Fixed-Heavy** | Always use heavy variant everywhere | Fixed: k=3 |
| **Greedy-Local** | Deploy at nearest node, fixed model | Fixed: k=2 |
| **Uniform** | Uniform deployment, fixed model | Fixed: k=2 |

### 3.2 Our Algorithm: Adaptive Model Selection (AMS)

**Core Idea**: For each node and each service, dynamically select the variant that minimizes end-to-end delay while meeting accuracy requirements.

```python
def AMS_Algorithm(network, services, requests, accuracy_threshold):
    """
    Adaptive Model Selection Algorithm
    
    Input:
        network: Heterogeneous edge nodes
        services: Microservices with K variants each
        requests: Request flows with arrival rates
        accuracy_threshold: Minimum required accuracy
    
    Output:
        deployment: Which variant at which node
        routing: Probability matrix P(r)
    """
    
    # Phase 1: Variant Selection per Node
    for node in network.edge_nodes:
        for service in services:
            best_variant = None
            best_delay = infinity
            
            for variant in service.variants:
                # Check accuracy constraint
                if variant.accuracy < accuracy_threshold:
                    continue
                
                # Check resource feasibility
                if not node.can_accommodate(variant):
                    continue
                
                # Compute expected delay with this variant
                expected_delay = compute_delay(node, service, variant, requests)
                
                if expected_delay < best_delay:
                    best_delay = expected_delay
                    best_variant = variant
            
            deployment[node][service] = best_variant
    
    # Phase 2: Deployment Optimization (GMDA-style)
    # Greedy deployment based on resource demands
    deployment = optimize_deployment(deployment, network)
    
    # Phase 3: Routing Optimization (RMPR-style)
    # Probability routing to minimize end-to-end delay
    routing = optimize_routing(deployment, network, requests)
    
    return deployment, routing
```

**Key Innovation**: 
- Baselines: One model for all nodes
- AMS: Different model per node based on local load and resources

### 3.3 Oracle Upper Bound

```python
def Oracle(network, services, requests):
    """
    Theoretical upper bound: exhaustive search over all combinations
    """
    best_solution = None
    best_delay = infinity
    
    for deployment in all_possible_deployments():
        for routing in all_possible_routings():
            delay = compute_end_to_end_delay(deployment, routing)
            if delay < best_delay:
                best_delay = delay
                best_solution = (deployment, routing)
    
    return best_solution
```

**Note**: Oracle is computationally expensive, only used for small-scale validation.

---

## 4. Experiment Design

### 4.1 Experiment 1: Static Load Comparison (Medium Scale)

**Setup**:
- Network: 5 edge nodes (1 low, 2 mid, 2 high) + 1 cloud
- Services: 3 call chains, 4 microservices each
- Load: Medium (λ = 10-30 req/s)

**Comparison**:
| Algorithm | Model Selection | Deployment | Routing |
|-----------|----------------|------------|---------|
| Fixed-Light | Fixed k=1 | GMDA | Shortest-Path |
| Fixed-Medium | Fixed k=2 | GMDA | Shortest-Path |
| Fixed-Heavy | Fixed k=3 | GMDA | Shortest-Path |
| AMS (Ours) | Adaptive | GMDA | RMPR |
| Oracle | Exhaustive | Exhaustive | Exhaustive |

**Metrics**:
- Average end-to-end delay
- P99 delay
- SLA satisfaction rate
- Deployment cost
- Resource utilization

**Expected Result**: AMS ≈ Oracle > Fixed-Medium > Fixed-Light > Fixed-Heavy

### 4.2 Experiment 2: Heterogeneity Impact

**Setup**: Vary heterogeneity degree

| Scenario | Node Configuration |
|----------|-------------------|
| Homogeneous | All nodes: 8 CPU, 2 GPU |
| Mild Heterogeneous | Mix of 4-8-16 CPU |
| High Heterogeneous | Mix of 2-4-8-16-32 CPU |

**Goal**: Show AMS benefits increase with heterogeneity

### 4.3 Experiment 3: Scalability (Small/Medium/Large)

| Scale | Edge Nodes | Services | Chains | Arrival Rate |
|-------|-----------|----------|--------|--------------|
| Small | 3 | 3 | 2 | 5-15 req/s |
| Medium | 5-10 | 4-6 | 3-5 | 10-50 req/s |
| Large | 20-50 | 10+ | 10+ | 50-200 req/s |

**Goal**: Show AMS scales well, computation time acceptable

### 4.4 Experiment 4: Dynamic Load (Optional)

**Load Patterns**:
- Gradual: λ(t) = λ₀ + α·t
- Burst: λ(t) = λ_base + λ_burst·I(t∈[t₁,t₂])
- Periodic: λ(t) = λ_base + A·sin(ωt)

**Adaptation**: AMS re-selects variants when load changes significantly

**Comparison**: AMS (adaptive) vs Fixed-Medium (static)

---

## 5. Implementation Framework

```
experiment/
├── 📄 main.py                          # Entry point
├── ⚙️ config.py                        # Configuration
│
├── 📂 core/                            # Core Engine (Analytical)
│   ├── __init__.py
│   ├── 🌐 jackson_network.py           # Open Jackson Network
│   ├── 📊 erlang_c.py                  # Erlang-C formula
│   ├── 🧮 delay_calculator.py          # End-to-end delay
│   └── ✅ stability.py                # Stability check
│
├── 📂 models/                          # System Models
│   ├── __init__.py
│   ├── 🖥️ node.py                      # Heterogeneous node
│   ├── ⚙️ service.py                   # Service with variants
│   ├── 🔗 chain.py                     # Call chain
│   └── 📦 variant.py                   # Model variant
│
├── 📂 algorithms/                      # Algorithms
│   ├── __init__.py
│   ├── ⭐ ams.py                       # Our AMS algorithm
│   ├── 📚 fixed_light.py              # Baseline: fixed light
│   ├── 📚 fixed_medium.py             # Baseline: fixed medium
│   ├── 📚 fixed_heavy.py              # Baseline: fixed heavy
│   ├── 📚 greedy_local.py             # Baseline: greedy
│   └── 📚 oracle.py                   # Oracle upper bound
│
├── 📂 experiments/                     # Experiments
│   ├── __init__.py
│   ├── 🔍 exp1_static_comparison.py    # Exp 1: Static load
│   ├── 📊 exp2_heterogeneity.py        # Exp 2: Heterogeneity
│   ├── 📈 exp3_scalability.py          # Exp 3: Small/Medium/Large
│   └── 🔄 exp4_dynamic.py              # Exp 4: Dynamic load
│
├── 📂 metrics/                         # Metrics
│   ├── __init__.py
│   └── 📊 evaluator.py                 # Performance metrics
│
├── 📂 visualization/                   # Visualization
│   ├── __init__.py
│   └── 📈 plots.py                     # Result plots
│
└── 📂 results/                         # Results
    ├── 📁 raw/                         # Raw data
    └── 📁 figures/                     # Figures
```

---

## 6. Key Formulas Summary

| Formula | Description | Usage |
|---------|-------------|-------|
| `λ^m_v = Σ λ_ext + Σ P·λ_up` | Flow merging | Compute arrival rates |
| `ρ = λ / (N·μ)` | Service intensity | Stability check |
| `C(N,ρ) = [Σ (Nρ)^k/k! + (Nρ)^N/(N!(1-ρ))]^-1` | Erlang-C | Queue length |
| `L = C·ρ / (1-ρ)` | Avg queue length | Delay calculation |
| `W = L / λ` | Avg waiting time | Delay calculation |
| `R = W + 1/μ` | Avg response time | End-to-end delay |
| `E[T] = Σ R + Σ D` | End-to-end delay | SLA check |

---

## 7. Definition of Done

- [ ] Core engine: Open Jackson network with Erlang-C
- [ ] Node model: Heterogeneous resources (CPU/GPU/Mem)
- [ ] Service model: Multiple variants per service
- [ ] AMS algorithm implementation
- [ ] 5 Baseline algorithms implementation
- [ ] Oracle upper bound (small scale)
- [ ] Experiment 1: Static comparison (medium scale)
- [ ] Experiment 2: Heterogeneity impact
- [ ] Experiment 3: Scalability (small/medium/large)
- [ ] Experiment 4: Dynamic load (optional)
- [ ] Metrics: delay, cost, success rate, utilization
- [ ] Visualization: charts and tables
- [ ] README with reproduction instructions
