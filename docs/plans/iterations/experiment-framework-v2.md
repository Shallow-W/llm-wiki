# Experiment Framework v2: Heterogeneous Edge Network with Dynamic Model Selection

## Revision Notes

Based on Round 1 review feedback, v2 makes the following critical corrections:
- **Queuing Model**: Replaced Open Jackson with independent M/M/c per service + traffic equations
- **Formula Corrections**: Fixed Erlang-C, queue length, and response time formulas
- **Heterogeneity**: Introduced μ_{m,n} — service rate depends on both model variant AND node
- **Resource Constraints**: Added CPU/GPU/Memory capacity constraints
- **AMS Algorithm**: Added complete pseudocode with objective function
- **Dynamic Experiments**: Changed from "optional" to "required"
- **Baselines**: Added Random, Threshold-Based, Cloud-Only
- **Metrics**: Added accuracy loss, algorithm overhead, fairness
- **Reproducibility**: Added complete parameter tables, DAG examples, random seeds

---

## 1. System Model

### 1.1 Network Topology (Heterogeneous)

```
┌─────────────────────────────────────────────────────────────┐
│              Heterogeneous Edge-Cloud Network                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐│
│   │  Edge 1     │←────→│  Edge 2     │←────→│  Edge 3     ││
│   │  [High-End] │ 5ms  │  [Mid]      │ 5ms  │  [Low]      ││
│   │  CPU:16     │      │  CPU:8      │      │  CPU:4      ││
│   │  GPU:4      │      │  GPU:2      │      │  GPU:0      ││
│   │  Mem:64GB   │      │  Mem:32GB   │      │  Mem:16GB   ││
│   │  Speed:3.0x │      │  Speed:2.0x │      │  Speed:1.0x ││
│   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘│
│          │                    │                    │       │
│          └────────────────────┼────────────────────┘       │
│                               │                            │
│                          ┌────┴────┐                       │
│                          │ Cloud   │                       │
│                          │ [Ultra] │                       │
│                          │ CPU:64  │                       │
│                          │ GPU:8   │                       │
│                          │ Speed:5x│                       │
│                          └─────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Node Configuration Table**:

| Node ID | Type | CPU Cores | GPU Cards | Memory (GB) | Speed Factor | Cost/hour |
|---------|------|-----------|-----------|-------------|--------------|-----------|
| E1 | Low | 4 | 0 | 16 | 1.0x | $0.10 |
| E2 | Low | 4 | 0 | 16 | 1.0x | $0.10 |
| E3 | Mid | 8 | 2 | 32 | 2.0x | $0.25 |
| E4 | Mid | 8 | 2 | 32 | 2.0x | $0.25 |
| E5 | High | 16 | 4 | 64 | 3.0x | $0.50 |
| Cloud | Cloud | 64 | 8 | 256 | 5.0x | $1.00 |

**Speed Factor**: Multiplier on base processing rate (models run faster on better hardware)

### 1.2 Service Model with Multiple Variants

Each microservice has **K=3** model variants:

| Variant | Accuracy | Base μ (req/s) | GPU Mem (MB) | GPU Req | CPU Req |
|---------|----------|----------------|--------------|---------|---------|
| light (k=1) | 85% | 50 | 512 | 0.5 | 1 |
| medium (k=2) | 90% | 25 | 2048 | 1.0 | 2 |
| heavy (k=3) | 95% | 10 | 8192 | 2.0 | 4 |

**Effective Service Rate** (heterogeneity-aware):
```
μ_{m,k,n} = base_μ_{m,k} × speed_factor_n
```

Example: medium model on High node: μ = 25 × 3.0 = 75 req/s

**Resource Requirements**:
- Each deployed instance consumes: GPU_req GPU cards, CPU_req CPU cores, GPU_mem GPU memory
- Multiple instances of same model can share GPU memory (read-only weights)

### 1.3 Service Chain (DAG)

**Example DAGs**:

```
Chain 1 (Image Recognition):
  User → [A: preprocess] → [B: feature_extract] → [C: ai_inference] → [D: postprocess] → Return
  
Chain 2 (Quality Check):
  User → [A: preprocess] → [B: feature_extract] → [E: quality_check] → [D: postprocess] → Return
  (Shares A, B, D with Chain 1)
  
Chain 3 (Light Inference):
  User → [A: preprocess] → [C: ai_inference] → Return
```

**DAG Properties**:
- Linear chain: Sequential execution
- Parallel branches: Fork-join (max of branch delays)
- Service reuse: Multiple chains can use same service instance

### 1.4 Request Model

- **Arrival Process**: Poisson process with rate λ_f for flow f
- **Request Size**: Exponentially distributed, mean = 100 KB
- **SLA Constraint**: Maximum end-to-end delay T_f^max

| Chain | Services | SLA (ms) | Base λ (req/s) |
|-------|----------|----------|----------------|
| 1 | A→B→C→D | 150 | 10 |
| 2 | A→B→E→D | 200 | 5 |
| 3 | A→C | 100 | 15 |

---

## 2. Analytical Simulation Framework

### 2.1 Core Principle

**Direct computation of steady-state metrics using queuing theory formulas** (NO event-by-event simulation).

```
Input: Network, services, variants, arrival rates, deployment decisions
↓
Traffic Equations (solve for λ at each node)
↓
Resource Constraint Check (feasibility)
↓
M/M/c Analysis per Service-Node Pair (Erlang-C)
↓
End-to-End Delay Calculation (DAG traversal)
↓
Output: Delay, cost, success rate, utilization
```

### 2.2 Mathematical Model (Corrected)

#### Step 1: Traffic Equations

For each service m at node n, compute total arrival rate:

```
λ_{m,n} = Σ_f x_{m,n} · λ_f · I(m ∈ chain_f)          (external arrivals)
          + Σ_{m'} Σ_{n'} P_{m',n'→m,n} · λ_{m',n'}     (routed arrivals)
```

Where:
- x_{m,n} ∈ {0,1}: whether service m is deployed at node n
- P_{m',n'→m,n}: routing probability from service m' at n' to service m at n
- I(m ∈ chain_f): indicator if service m is in chain f

**For deterministic routing (DAG)**: P ∈ {0,1}

**Note**: We do NOT assume Poisson output (Burke's theorem doesn't apply to deterministic routing). Instead, we use the **approximation** that merged flows can be treated as independent Poisson processes. This is a common approximation in the literature.

#### Step 2: Resource Constraints

For each node n:
```
Σ_m x_{m,n} · N_{m,n} · CPU_req_{m,k} ≤ CPU_n          (CPU constraint)
Σ_m x_{m,n} · N_{m,n} · GPU_req_{m,k} ≤ GPU_n          (GPU constraint)
Σ_m x_{m,n} · GPU_mem_{m,k} ≤ Mem_n                    (Memory constraint)
```

Where N_{m,n} = number of container instances of service m at node n.

#### Step 3: M/M/c Queueing Analysis (Erlang-C)

For each deployed service m at node n with variant k:

```
Offered load:          A_{m,n} = λ_{m,n} / μ_{m,k,n}
Number of servers:     c_{m,n} = N_{m,n} × (CPU_n / CPU_req_{m,k})  [simplified]
Utilization:           ρ_{m,n} = A_{m,n} / c_{m,n}

Stability check:       ρ_{m,n} < 1  (must hold)

Erlang-C formula:      C(c, A) = [ (A^c / c!) × (1/(1-ρ)) ] / 
                                   [ Σ_{i=0}^{c-1} (A^i / i!) + (A^c / c!) × (1/(1-ρ)) ]

Average queue length (waiting):  L_q = C(c, A) × ρ / (1 - ρ)
Average queue length (system):   L = L_q + A

Average waiting time:            W_q = L_q / λ_{m,n}
Average response time:           R_{m,n} = W_q + 1/μ_{m,k,n}
```

**Correction from v1**: 
- v1 had `L = C·ρ/(1-ρ)` which is WRONG (missing `+ A`)
- v2 uses `L = L_q + A` where `L_q = C(c,A)·ρ/(1-ρ)`

#### Step 4: End-to-End Delay

For linear chain:
```
E[T_f] = Σ_{(m,n) ∈ path_f} R_{m,n} + Σ_{(n_i, n_j) ∈ path_f} D_{n_i, n_j}
```

For parallel branches (fork-join):
```
E[T_f] = Σ_{sequential} R_{m,n} + max_{branches} (Σ_{branch} R_{m,n}) + Σ D_{n_i, n_j}
```

Where D_{n_i, n_j} = propagation_delay + data_size / bandwidth

#### Step 5: SLA Satisfaction

```
η_f = 1  if E[T_f] ≤ T_f^max
      0  otherwise

Overall success rate: η = (Σ_f η_f × λ_f) / (Σ_f λ_f)
```

### 2.3 Why Analytical (Not DES)

| Aspect | Analytical (Our Approach) | Discrete Event Simulation |
|--------|--------------------------|---------------------------|
| **Speed** | Fast (seconds) | Slow (minutes to hours) |
| **Accuracy** | Exact for M/M/c assumptions | Approximate (variance) |
| **Scalability** | Excellent | Limited |
| **Suitable for** | Parameter sweep, optimization | Complex non-Markovian systems |

**Assumptions** (must be stated in paper):
1. Poisson arrivals (standard benchmark)
2. Exponential service times (approximation for AI inference)
3. Steady-state analysis (for static loads)
4. Independent flows approximation (for merged streams)

---

## 3. Algorithm Design

### 3.1 Baseline Algorithms (Fixed Model)

| Baseline | Description | Model Selection | Deployment | Routing |
|----------|-------------|----------------|------------|---------|
| **Fixed-Light** | Always light variant everywhere | Fixed: k=1 | Greedy | Shortest-Path |
| **Fixed-Medium** | Always medium variant everywhere | Fixed: k=2 | Greedy | Shortest-Path |
| **Fixed-Heavy** | Always heavy variant everywhere | Fixed: k=3 | Greedy | Shortest-Path |
| **Random** | Random variant per node | Random | Greedy | Shortest-Path |
| **Threshold** | Switch based on queue length | Threshold | Greedy | Shortest-Path |
| **Greedy-Local** | Local processing priority | Fixed: k=2 | Greedy | Shortest-Path |
| **Cloud-Only** | All requests to cloud | Fixed: k=2 | Cloud-only | Direct |
| **Edge-Only** | No cloud usage | Fixed: k=2 | Edge-only | Shortest-Path |

### 3.2 Our Algorithm: AMS (Adaptive Model Selection)

**Complete Pseudocode**:

```python
def AMS(network, services, chains, requests, accuracy_threshold):
    """
    Adaptive Model Selection Algorithm
    
    Input:
        network: Heterogeneous edge nodes with resources
        services: Microservices with K variants each
        chains: Service call chains (DAGs)
        requests: Request flows with arrival rates λ_f
        accuracy_threshold: Minimum required accuracy per chain
    
    Output:
        X: Deployment matrix X[m,n,k] ∈ {0,1}
        P: Routing probability matrix P[m',n'→m,n]
        N: Instance count matrix N[m,n]
    """
    
    # ============================================================
    # Phase 1: Initialization
    # ============================================================
    # Start with medium variant for all services at all feasible nodes
    X = initialize_with_medium_variant(network, services)
    
    # ============================================================
    # Phase 2: Iterative Greedy Optimization
    # ============================================================
    for iteration in range(MAX_ITER):
        
        # 2.1 Solve traffic equations for current deployment
        λ = solve_traffic_equations(X, P, chains, requests)
        
        # 2.2 Check resource feasibility
        if not check_resource_constraints(X, N, network):
            # Reduce instances or switch to lighter variants
            X, N = reduce_resource_usage(X, N, network)
            continue
        
        # 2.3 Compute delays for current deployment
        R = compute_response_times(λ, X, N, network, services)
        E2E_delays = compute_e2e_delays(R, P, chains)
        
        # 2.4 Check convergence
        if converged(E2E_delays, prev_E2E_delays):
            break
        
        # 2.5 Greedy variant selection
        for node in network.nodes:
            for service in services:
                current_variant = get_variant(X, service, node)
                current_delay = E2E_delays[service, node]
                
                best_variant = current_variant
                best_delay = current_delay
                
                for variant in service.variants:
                    # Check accuracy constraint
                    if variant.accuracy < accuracy_threshold:
                        continue
                    
                    # Check resource feasibility
                    if not node.can_accommodate(variant, service):
                        continue
                    
                    # Temporarily switch to this variant
                    X_temp = switch_variant(X, service, node, variant)
                    
                    # Recompute delay
                    λ_temp = solve_traffic_equations(X_temp, P, chains, requests)
                    R_temp = compute_response_times(λ_temp, X_temp, N, network, services)
                    E2E_temp = compute_e2e_delays(R_temp, P, chains)
                    
                    if E2E_temp < best_delay:
                        best_delay = E2E_temp
                        best_variant = variant
                
                # Apply best variant
                X = switch_variant(X, service, node, best_variant)
        
        # 2.6 Instance count adjustment
        N = optimize_instance_counts(λ, X, network, services)
        
        # 2.7 Routing optimization (RMPR-style)
        P = optimize_routing_probabilities(X, N, λ, network, chains)
    
    # ============================================================
    # Phase 3: Fine-tuning
    # ============================================================
    # Local search: try swapping variants between adjacent nodes
    X = local_search_variant_swap(X, N, network, services, chains)
    
    return X, P, N


def solve_traffic_equations(X, P, chains, requests):
    """
    Solve for arrival rate λ_{m,n} at each service-node pair
    
    For deterministic routing (DAG), P ∈ {0,1}
    λ_{m,n} = Σ_f X[m,n] × λ_f × I(m ∈ chain_f) 
              + Σ_{m'} Σ_{n'} P[m',n'→m,n] × λ_{m',n'}
    
    This is a linear system that can be solved iteratively.
    """
    λ = initialize_arrival_rates(requests)
    
    for _ in range(MAX_ITER_TRAFFIC):
        λ_new = {}
        for m in services:
            for n in nodes:
                λ_new[m,n] = compute_arrival_rate(m, n, λ, X, P, chains, requests)
        
        if converged(λ_new, λ):
            break
        λ = λ_new
    
    return λ


def compute_response_times(λ, X, N, network, services):
    """
    Compute response time R_{m,n} for each deployed service-node pair
    using M/M/c analysis (Erlang-C)
    """
    R = {}
    for m in services:
        for n in network.nodes:
            if X[m,n] == 0:
                continue
            
            variant = get_variant(X, m, n)
            mu = variant.base_mu × n.speed_factor
            c = N[m,n]  # number of parallel servers
            A = λ[m,n] / mu
            rho = A / c
            
            if rho >= 1:
                R[m,n] = float('inf')  # Unstable
            else:
                C_erlang = erlang_c(c, A)
                L_q = C_erlang × rho / (1 - rho)
                W_q = L_q / λ[m,n]
                R[m,n] = W_q + 1/mu
    
    return R
```

**Objective Function**:
```
minimize:    Σ_f w_f × E[T_f]        (weighted end-to-end delay)
subject to:
    η_f ≥ η_min                         (SLA satisfaction)
    accuracy_f ≥ accuracy_threshold     (accuracy constraint)
    Σ_m X[m,n] × N[m,n] × CPU_req ≤ CPU_n   (CPU capacity)
    Σ_m X[m,n] × N[m,n] × GPU_req ≤ GPU_n   (GPU capacity)
    Σ_m X[m,n] × GPU_mem ≤ Mem_n            (Memory capacity)
    X[m,n] ∈ {0,1}                        (binary deployment)
    N[m,n] ∈ {1, 2, ..., N_max}           (instance count)
```

### 3.3 Oracle Upper Bound

```python
def Oracle(network, services, chains, requests):
    """
    Theoretical upper bound: exhaustive search over all valid deployments
    
    For small scale only (≤ 5 nodes, ≤ 3 services)
    """
    best_solution = None
    best_objective = infinity
    
    for X in all_valid_deployments(network, services):
        for N in all_valid_instance_counts(X, network):
            λ = solve_traffic_equations(X, P, chains, requests)
            if not stable(λ, X, N):
                continue
            
            R = compute_response_times(λ, X, N, network, services)
            E2E = compute_e2e_delays(R, chains)
            objective = compute_objective(E2E, X, N)
            
            if objective < best_objective:
                best_objective = objective
                best_solution = (X, N)
    
    return best_solution
```

---

## 4. Experiment Design (8 Experiments)

### Experiment 1: Static Load Benchmark (Medium Scale)

**Setup**:
- Network: 5 edge + 1 cloud (medium scale)
- Services: 3 chains, 5 microservices
- Load: Medium (λ = 10-30 req/s)

**Comparison**:
| Algorithm | Model Selection | Deployment | Routing |
|-----------|----------------|------------|---------|
| Fixed-Light | Fixed k=1 | Greedy | Shortest-Path |
| Fixed-Medium | Fixed k=2 | Greedy | Shortest-Path |
| Fixed-Heavy | Fixed k=3 | Greedy | Shortest-Path |
| Random | Random | Greedy | Shortest-Path |
| Threshold | Queue-based | Greedy | Shortest-Path |
| AMS (Ours) | Adaptive | Greedy | Optimized |
| Oracle | Exhaustive | Exhaustive | Exhaustive |

**Metrics**: Average delay, P99 delay, SLA satisfaction rate, deployment cost, resource utilization

**Expected Result**: Oracle ≥ AMS > Fixed-Medium > Threshold > Random > Fixed-Light > Fixed-Heavy

### Experiment 2: Heterogeneity Impact

**Setup**: Vary heterogeneity degree H = σ_resources / μ_resources

| Scenario | H | Node Configuration |
|----------|---|-------------------|
| Homogeneous | 0.0 | All: 8 CPU, 2 GPU |
| Mild | 0.3 | Mix: 4-8-16 CPU |
| Moderate | 0.6 | Mix: 2-4-8-16 CPU |
| High | 1.0 | Mix: 2-4-8-16-32 CPU |

**Goal**: Show AMS benefits increase with H

### Experiment 3: Scalability (Small/Medium/Large)

| Scale | Edge Nodes | Services | Chains | Arrival Rate | Computation Time |
|-------|-----------|----------|--------|--------------|-----------------|
| Small | 3 | 3 | 2 | 5-15 req/s | < 1s |
| Medium | 5-10 | 4-6 | 3-5 | 10-50 req/s | < 10s |
| Large | 20-50 | 10+ | 10+ | 50-200 req/s | < 60s |

**Goal**: Show AMS scales well, computation time acceptable

### Experiment 4: Dynamic Load (REQUIRED — Core Contribution)

**Load Patterns**:

| Pattern | Formula | Duration |
|---------|---------|----------|
| Gradual | λ(t) = λ₀ + α·t | 1000 slots |
| Burst | λ(t) = λ_base + λ_burst·I(t∈[400,600]) | 1000 slots |
| Periodic | λ(t) = λ_base + A·sin(2πt/T) | 1000 slots |

**Adaptation**: AMS re-selects variants every T_adapt slots

**Comparison**: AMS (adaptive) vs Fixed-Medium (static) vs Threshold

**Metrics**: Delay time series, adaptation speed, reconfiguration overhead

### Experiment 5: Robustness

**Scenarios**:
- Node failure: Randomly remove 10% of nodes
- Parameter error: μ estimation error ±20%
- Load estimation error: λ estimation error ±30%

**Goal**: Show AMS is robust to real-world uncertainties

### Experiment 6: Ablation Study

| Variant | Heterogeneity | Adaptive | Global Opt | Description |
|---------|--------------|----------|------------|-------------|
| AMS-Full | ✅ | ✅ | ✅ | Complete algorithm |
| AMS-NoHetero | ❌ | ✅ | ✅ | Ignore node differences |
| AMS-NoAdaptive | ✅ | ❌ | ✅ | Fixed medium variant |
| AMS-LocalOnly | ✅ | ✅ | ❌ | Greedy local optimization |

**Goal**: Attribute performance gains to each component

### Experiment 7: Delay-Accuracy Trade-off

**Setup**: Plot Pareto frontier of all variant combinations

**Metrics**:
- X-axis: Average delay
- Y-axis: Average accuracy
- Points: AMS solutions under different accuracy thresholds

**Goal**: Show AMS achieves near-optimal delay-accuracy trade-off

### Experiment 8: Algorithm Overhead

**Metrics**:
- Decision time vs number of nodes
- Decision time vs number of services
- Communication overhead (if distributed)
- Memory overhead

**Goal**: Prove overhead is negligible compared to delay gains

---

## 5. Metrics (Complete List)

### Performance Metrics
| Metric | Symbol | Definition |
|--------|--------|------------|
| Average end-to-end delay | E[T] | Mean response time across all requests |
| P99 delay | T_p99 | 99th percentile delay |
| Throughput | Θ | Maximum sustainable arrival rate |
| SLA satisfaction rate | η | Fraction of requests meeting SLA |
| SLA violation rate | 1-η | Fraction of requests violating SLA |

### Resource Metrics
| Metric | Symbol | Definition |
|--------|--------|------------|
| Deployment cost | Cost | Σ (instances × cost_per_hour) |
| CPU utilization | U_CPU | Average CPU usage percentage |
| GPU utilization | U_GPU | Average GPU usage percentage |
| Memory utilization | U_Mem | Average memory usage percentage |

### Quality Metrics
| Metric | Symbol | Definition |
|--------|--------|------------|
| Model accuracy | Acc | Average accuracy of selected variants |
| Accuracy loss | ΔAcc | 1 - Acc_selected / Acc_heavy |

### Algorithm Metrics
| Metric | Symbol | Definition |
|--------|--------|------------|
| Decision time | T_dec | Time to compute deployment decision |
| Convergence iterations | I_conv | Number of iterations to converge |
| Reconfiguration frequency | F_reconf | Number of model switches per unit time |

### Fairness Metrics
| Metric | Symbol | Definition |
|--------|--------|------------|
| Jain's fairness index | J | (Σx_i)² / (n·Σx_i²) for per-chain delays |

---

## 6. Reproducibility Checklist

### Parameters (Complete Table)

| Parameter | Symbol | Default | Range | Unit |
|-----------|--------|---------|-------|------|
| Edge nodes | N_edge | 5 | 3-50 | count |
| Cloud nodes | N_cloud | 1 | 1-2 | count |
| Microservices | M | 5 | 3-15 | count |
| Model variants | K | 3 | 2-5 | count |
| Call chains | F | 3 | 2-10 | count |
| Base arrival rate | λ | 10 | 5-200 | req/s |
| SLA deadline | T_max | 150 | 50-500 | ms |
| Speed factor (Low) | s_low | 1.0 | 0.5-2.0 | multiplier |
| Speed factor (Mid) | s_mid | 2.0 | 1.0-3.0 | multiplier |
| Speed factor (High) | s_high | 3.0 | 2.0-5.0 | multiplier |
| Speed factor (Cloud) | s_cloud | 5.0 | 3.0-10.0 | multiplier |
| Max iterations | MAX_ITER | 100 | 50-500 | count |
| Convergence threshold | ε | 1e-6 | 1e-8 - 1e-4 | - |

### DAG Examples

**Chain 1 (Linear)**:
```
A → B → C → D
```

**Chain 2 (With Branch)**:
```
A → B → C → D
      ↘ E ↗
```

**Chain 3 (Parallel)**:
```
    → B →
A →       → D
    → C →
```

### Random Seeds

| Experiment | Seed | Purpose |
|------------|------|---------|
| 1 | 42 | Main benchmark |
| 2 | 123 | Sensitivity check |
| 3 | 456 | Sensitivity check |
| 4 | 789 | Sensitivity check |
| 5 | 101112 | Sensitivity check |

**Reporting**: Mean ± 95% confidence interval across 5 seeds

### Hardware Environment

| Component | Specification |
|-----------|--------------|
| CPU | Intel Xeon E5-2680 v4 @ 2.4GHz |
| Memory | 64 GB DDR4 |
| GPU | NVIDIA Tesla V100 (optional) |
| OS | Ubuntu 20.04 LTS |
| Python | 3.9+ |

---

## 7. Implementation Framework

```
experiment/
├── 📄 main.py                          # Entry point
├── ⚙️ config.py                        # Configuration
├── 📋 requirements.txt                 # Dependencies
│
├── 📂 core/                            # Core Engine (Analytical)
│   ├── __init__.py
│   ├── 🧮 erlang_c.py                  # Erlang-C formula (numerically stable)
│   ├── 🌐 traffic_equations.py         # Traffic equation solver
│   ├── 📊 delay_calculator.py          # End-to-end delay computation
│   ├── ✅ stability.py                # Stability check
│   └── 🔍 feasibility.py              # Resource feasibility check
│
├── 📂 models/                          # System Models
│   ├── __init__.py
│   ├── 🖥️ node.py                      # Heterogeneous node
│   ├── ⚙️ service.py                   # Microservice with variants
│   ├── 🔗 chain.py                     # Call chain (DAG)
│   └── 📦 variant.py                   # Model variant
│
├── 📂 algorithms/                      # Algorithms
│   ├── __init__.py
│   ├── ⭐ ams.py                       # Our AMS algorithm
│   ├── 📚 fixed_light.py              # Baseline: fixed light
│   ├── 📚 fixed_medium.py             # Baseline: fixed medium
│   ├── 📚 fixed_heavy.py              # Baseline: fixed heavy
│   ├── 📚 random_baseline.py          # Baseline: random
│   ├── 📚 threshold.py                # Baseline: threshold-based
│   ├── 📚 greedy_local.py             # Baseline: greedy local
│   ├── 📚 cloud_only.py               # Baseline: cloud-only
│   ├── 📚 edge_only.py                # Baseline: edge-only
│   └── 📚 oracle.py                   # Oracle upper bound
│
├── 📂 experiments/                     # Experiments
│   ├── __init__.py
│   ├── 🔍 exp1_static_benchmark.py     # Exp 1: Static benchmark
│   ├── 📊 exp2_heterogeneity.py        # Exp 2: Heterogeneity impact
│   ├── 📈 exp3_scalability.py          # Exp 3: Small/Medium/Large
│   ├── 🔄 exp4_dynamic_load.py         # Exp 4: Dynamic load (REQUIRED)
│   ├── 🛡️ exp5_robustness.py          # Exp 5: Robustness
│   ├── 🔬 exp6_ablation.py             # Exp 6: Ablation study
│   ├── ⚖️ exp7_delay_accuracy.py       # Exp 7: Delay-accuracy trade-off
│   └── ⏱️ exp8_overhead.py            # Exp 8: Algorithm overhead
│
├── 📂 metrics/                         # Metrics
│   ├── __init__.py
│   └── 📊 evaluator.py                 # Comprehensive metrics
│
├── 📂 visualization/                   # Visualization
│   ├── __init__.py
│   └── 📈 plots.py                     # Result plots
│
└── 📂 results/                         # Results
    ├── 📁 raw/                         # Raw data (CSV)
    └── 📁 figures/                     # Figures (PNG/PDF)
```

---

## 8. Key Formulas Summary (Corrected)

| Formula | Description | Status |
|---------|-------------|--------|
| `λ_{m,n} = Σ λ_ext + Σ P·λ_up` | Traffic equations | ✅ Correct |
| `A = λ / μ` | Offered load | ✅ Correct |
| `ρ = A / c` | Utilization | ✅ Correct |
| `C(c,A) = [(A^c/c!)·(1/(1-ρ))] / [Σ(A^k/k!) + (A^c/c!)·(1/(1-ρ))]` | Erlang-C | ✅ Correct |
| `L_q = C(c,A) · ρ / (1-ρ)` | Queue length (waiting) | ✅ Correct |
| `L = L_q + A` | Queue length (system) | ✅ **Fixed from v1** |
| `W_q = L_q / λ` | Waiting time | ✅ Correct |
| `R = W_q + 1/μ` | Response time | ✅ Correct |
| `E[T] = Σ R + Σ D` | End-to-end delay | ✅ Correct |
| `μ_{m,k,n} = base_μ_{m,k} × speed_n` | Heterogeneous service rate | ✅ **New in v2** |

---

## 9. Definition of Done

- [ ] Core engine: Traffic equations + Erlang-C (numerically stable)
- [ ] Node model: Heterogeneous resources with speed factors
- [ ] Service model: Multiple variants with resource requirements
- [ ] AMS algorithm: Complete pseudocode implemented
- [ ] 8 Baseline algorithms implemented
- [ ] Oracle upper bound (small scale)
- [ ] Experiment 1: Static benchmark (medium scale)
- [ ] Experiment 2: Heterogeneity impact
- [ ] Experiment 3: Scalability (small/medium/large)
- [ ] Experiment 4: Dynamic load (REQUIRED)
- [ ] Experiment 5: Robustness
- [ ] Experiment 6: Ablation study
- [ ] Experiment 7: Delay-accuracy trade-off
- [ ] Experiment 8: Algorithm overhead
- [ ] All metrics implemented
- [ ] Visualization scripts
- [ ] README with reproduction instructions
- [ ] Requirements.txt
- [ ] Example configuration files
