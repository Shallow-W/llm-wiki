# Experiment Framework v4 (Final): Heterogeneous Edge Network with Dynamic Model Selection

## Revision Notes (v3 → v4)

Based on Round 3 review feedback, v4 makes the following final corrections:
- **Erlang-C Formula**: Fixed recursive calculation using standard Erlang-B recurrence + conversion
- **Numerical Stability**: Added log-space computation and Hayward approximation fallback for large c
- **Experiment 7**: Redesigned as "Adaptive Accuracy Regulation" experiment
- **Threshold Baseline**: Replaced with parameter-tuned version + added AWStream competitive baseline
- **Statistical Methods**: Added explicit warm-up/run length quantification + Wilcoxon signed-rank test

---

## 1. System Model

### 1.1 Network Topology (Heterogeneous)

| Node ID | Type | CPU Cores | GPU Cards | Memory (GB) | Speed Factor | Cost/hour |
|---------|------|-----------|-----------|-------------|--------------|-----------|
| E1 | Low | 4 | 0 | 16 | 1.0x | $0.10 |
| E2 | Low | 4 | 0 | 16 | 1.0x | $0.10 |
| E3 | Mid | 8 | 2 | 32 | 2.0x | $0.25 |
| E4 | Mid | 8 | 2 | 32 | 2.0x | $0.25 |
| E5 | High | 16 | 4 | 64 | 3.0x | $0.50 |
| Cloud | Cloud | 64 | 8 | 256 | 5.0x | $1.00 |

**Speed Factor**: Multiplier on base processing rate. Calibrated via benchmark: `speed_factor_n = benchmark_score_n / benchmark_score_low`

### 1.2 Service Model with Multiple Variants

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

### 1.3 Service Chain (DAG) — Critical Path Definition

**End-to-End Delay Definition**:

We use **Critical Path Method** for DAG delay calculation:

```
For a service chain DAG:
1. Assign each node (service instance) a weight = R_{m,n} (response time)
2. Assign each edge a weight = D_{n_i,n_j} (communication delay)
3. Find the longest path from source to sink
4. E2E delay = sum of weights on critical path
```

**Note**: DAGs are restricted to **series-parallel** structure (no complex fork-join synchronization). Parallel branches use max-of-branches.

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

### 2.1 Queuing Model — Simplified QNA

**Theoretical Foundation**: Simplified Whitt's Queueing Network Analyzer (QNA)

1. Each service-node pair: independent M/M/c queue
2. Arrival rates: computed via traffic equations (flow conservation)
3. Approximation: merged flows treated as Poisson (independent approximation)

**Approximation Error Analysis**:

| Condition | Approximation Error | Mitigation |
|-----------|-------------------|------------|
| ρ < 0.5 | < 5% | Acceptable |
| 0.5 ≤ ρ < 0.7 | 5-15% | Acceptable with caveat |
| ρ ≥ 0.7 | > 15% | Flag in results; DES validation subset |

**Validation**: 5 representative configurations validated via DES (SimPy). See Section 6.

### 2.2 Mathematical Model

#### Step 1: Traffic Equations

```
λ_{m,n} = Σ_f x_{m,n} · λ_f · I(m ∈ chain_f)          (external)
          + Σ_{m'} Σ_{n'} P_{m',n'→m,n} · λ_{m',n'}     (routed)
```

#### Step 2: Resource Constraints (HARD)

For each node n:
```
Σ_m x_{m,n} · N_{m,n} · CPU_req_{m,k} ≤ CPU_n
Σ_m x_{m,n} · N_{m,n} · GPU_req_{m,k} ≤ GPU_n
Σ_m x_{m,n} · GPU_mem_{m,k} ≤ Mem_n
```

**Policy**: Violation → deployment INFEASIBLE. AMS must reject or repair.

#### Step 3: M/M/c Queueing — Erlang-C (Complete & Corrected)

```
Offered load:          A_{m,n} = λ_{m,n} / μ_{m,k,n}    [Erlangs]
Number of servers:     c_{m,n} = N_{m,n}
Utilization:           ρ_{m,n} = A_{m,n} / c_{m,n}

Stability:             ρ_{m,n} < 1  (REQUIRED)

Erlang-C (explicit):
C(c, A) = [ (A^c / c!) · (c / (c - A)) ] / 
          [ Σ_{i=0}^{c-1} (A^i / i!) + (A^c / c!) · (c / (c - A)) ]

Queue length (waiting):  L_q = C(c, A) · ρ / (1 - ρ)
Queue length (system):   L = L_q + A
Waiting time:            W_q = L_q / λ_{m,n}
Response time:           R_{m,n} = W_q + 1/μ_{m,k,n}
```

**Numerical Stability — Recursive Calculation (CORRECTED)**:

```python
def erlang_c_stable(c, A):
    """
    Numerically stable Erlang-C calculation.
    Uses Erlang-B recurrence then converts to Erlang-C.
    """
    if A >= c:
        raise ValueError(f"A={A} must be < c={c}")
    
    # Step 1: Compute Erlang-B via standard recurrence
    B = 1.0  # B(0, A) = 1
    for i in range(1, c + 1):
        B = (A * B) / (i + A * B)
    
    # Step 2: Convert Erlang-B to Erlang-C
    C = (c * B) / (c - A + A * B)
    
    return C


def erlang_c_logspace(c, A):
    """
    Log-space computation for very large c (c > 200).
    Prevents overflow in factorials and powers.
    """
    import numpy as np
    
    # Compute in log space: log(A^i / i!) = i*log(A) - lgamma(i+1)
    log_A = np.log(A)
    
    # Sum terms in log space
    log_terms = []
    for i in range(c + 1):
        log_term = i * log_A - np.math.lgamma(i + 1)
        log_terms.append(log_term)
    
    # Log-sum-exp trick for numerical stability
    log_sum = np.logaddexp.reduce(log_terms[:-1])  # sum_{i=0}^{c-1}
    log_last = log_terms[-1] + np.log(c / (c - A))  # last term
    
    log_C = log_last - np.logaddexp(log_sum, log_last)
    
    return np.exp(log_C)


def erlang_c(c, A):
    """
    Unified Erlang-C with automatic method selection.
    """
    if c <= 200:
        return erlang_c_stable(c, A)
    else:
        return erlang_c_logspace(c, A)
```

**Large c Fallback (Hayward Approximation)**:

```python
def erlang_c_hayward(c, A):
    """
    Hayward approximation for very large c (c > 500).
    Uses Normal approximation to Erlang-C.
    """
    import numpy as np
    from scipy.stats import norm
    
    rho = A / c
    z = (c - A) / np.sqrt(A)
    
    # Normal approximation
    C_approx = norm.sf(z) / (norm.sf(z) + z * norm.pdf(z))
    
    return C_approx
```

#### Step 4: End-to-End Delay (Critical Path)

```
E[T_f] = CriticalPathDelay(DAG_f)

CriticalPathDelay:
1. Build weighted DAG: node weight = R_{m,n}, edge weight = D_{n_i,n_j}
2. Find longest path from ingress to egress
3. Sum weights on critical path
```

#### Step 5: SLA Satisfaction

```
η_f = 1  if E[T_f] ≤ T_f^max, else 0
η = (Σ_f η_f · λ_f) / (Σ_f λ_f)
```

### 2.3 Traffic Equation Solver (Complete)

```python
def solve_traffic_equations(X, P, chains, requests, max_iter=1000, tol=1e-8):
    """
    Iterative solver for traffic equations.
    Gauss-Seidel style with convergence and divergence checks.
    """
    λ = {}
    for m in services:
        for n in nodes:
            λ[m,n] = 0.0
    
    for iteration in range(max_iter):
        λ_old = λ.copy()
        max_diff = 0.0
        
        for m in services:
            for n in nodes:
                if X[m,n] == 0:
                    continue
                
                # External arrivals
                external = sum(
                    X[m,n] * requests[f].arrival_rate * I(m in chains[f].services)
                    for f in requests
                )
                
                # Routed arrivals
                routed = sum(
                    P.get((m_prev, n_prev, m, n), 0) * λ[m_prev, n_prev]
                    for m_prev in services
                    for n_prev in nodes
                )
                
                λ[m,n] = external + routed
                max_diff = max(max_diff, abs(λ[m,n] - λ_old[m,n]))
        
        # Convergence check
        if max_diff < tol:
            return λ, True, iteration
        
        # Divergence check (error growing)
        if iteration > 10 and max_diff > max(λ.values()) * 100:
            return λ, False, iteration
    
    return λ, False, max_iter
```

---

## 3. Algorithm Design

### 3.1 Baseline Algorithms

| Baseline | Description | Model | Deployment | Routing |
|----------|-------------|-------|------------|---------|
| **Fixed-Light** | Always light | Fixed k=1 | Greedy | Shortest-Path |
| **Fixed-Medium** | Always medium | Fixed k=2 | Greedy | Shortest-Path |
| **Fixed-Heavy** | Always heavy | Fixed k=3 | Greedy | Shortest-Path |
| **Random** | Random variant | Random | Greedy | Shortest-Path |
| **Greedy-Local** | Local priority | Fixed k=2 | Greedy | Shortest-Path |
| **Cloud-Only** | All to cloud | Fixed k=2 | Cloud-only | Direct |
| **Edge-Only** | No cloud | Fixed k=2 | Edge-only | Shortest-Path |
| **AWStream** | Competitive baseline from literature | Adaptive | Greedy | Shortest-Path |
| **Oracle** | Exhaustive search (small scale) | Exhaustive | Exhaustive | Exhaustive |

**Note**: Threshold baseline REMOVED (unfair parameter sensitivity). Replaced with AWStream [Zhang et al., OSDI 2018] as competitive baseline.

### 3.2 AMS Algorithm (Complete)

```python
def AMS(network, services, chains, requests, accuracy_threshold):
    """
    Adaptive Model Selection Algorithm (v4 Final)
    
    Objective: Minimize weighted end-to-end delay
    Constraints: SLA, accuracy (hard), resources (hard)
    """
    
    # Phase 1: Initialization
    X = initialize_with_medium_variant(network, services)
    N = initialize_instance_counts(X, network)
    P = initialize_shortest_path_routing(network, chains)
    
    # Phase 2: Iterative Optimization
    for iteration in range(MAX_ITER):
        
        # 2.1 Solve traffic equations
        λ, converged, iters = solve_traffic_equations(X, P, chains, requests)
        if not converged:
            print(f"Warning: Traffic eqs diverged at iter {iteration}")
            break
        
        # 2.2 Check resource feasibility (HARD)
        if not check_resource_constraints(X, N, network):
            X, N = repair_infeasible(X, N, network)
            if X is None:
                print("Warning: Cannot repair infeasible deployment")
                break
            continue
        
        # 2.3 Check stability
        if not check_stability(λ, X, N, services, network):
            X, N = add_instances(X, N, network)
            continue
        
        # 2.4 Compute delays
        R = compute_response_times(λ, X, N, network, services)
        E2E = compute_e2e_delays(R, P, chains)
        
        # 2.5 Check convergence
        if iteration > 0 and converged_objective(E2E, prev_E2E, tol=1e-6):
            break
        prev_E2E = E2E.copy()
        
        # 2.6 Greedy variant selection
        improved = False
        for n in network.nodes:
            for m in services:
                if X[m,n] == 0:
                    continue
                
                current_variant = get_variant(X, m, n)
                current_delay = max(E2E[f] for f in chains if m in chains[f].services)
                
                best_variant = current_variant
                best_delay = current_delay
                
                for variant in services[m].variants:
                    if variant.accuracy < accuracy_threshold:
                        continue
                    
                    temp_X = switch_variant(X, m, n, variant)
                    if not check_resource_constraints(temp_X, N, network):
                        continue
                    
                    temp_R = compute_response_times_for_variant(λ, temp_X, N, m, n, variant)
                    temp_E2E = compute_e2e_delays(temp_R, P, chains)
                    temp_delay = max(temp_E2E[f] for f in chains if m in chains[f].services)
                    
                    if temp_delay < best_delay:
                        best_delay = temp_delay
                        best_variant = variant
                        improved = True
                
                X = switch_variant(X, m, n, best_variant)
        
        if not improved:
            break
        
        # 2.7 Instance count optimization
        N = optimize_instance_counts(λ, X, network, services)
        
        # 2.8 Routing optimization
        P = optimize_routing_probabilities(X, N, λ, network, chains)
    
    # Phase 3: Local Search
    X = local_search_variant_swap(X, N, network, services, chains)
    
    return X, P, N
```

### 3.3 Oracle Upper Bound

```python
def Oracle(network, services, chains, requests):
    """Exhaustive search for small scale (≤ 5 nodes, ≤ 3 services)"""
    best = None
    best_obj = float('inf')
    
    for X in all_valid_deployments(network, services):
        for N in all_valid_instance_counts(X, network):
            λ, conv, _ = solve_traffic_equations(X, P, chains, requests)
            if not conv or not check_stability(λ, X, N, services, network):
                continue
            
            R = compute_response_times(λ, X, N, network, services)
            E2E = compute_e2e_delays(R, P, chains)
            obj = compute_objective(E2E, X, N)
            
            if obj < best_obj:
                best_obj = obj
                best = (X, N)
    
    return best
```

---

## 4. Experiment Design (8 Experiments)

### Experiment 1: Static Load Benchmark (Medium Scale)

**Setup**: 5 edge + 1 cloud, 3 chains, medium load (λ = 10-30 req/s)

**Comparison**: All 9 algorithms (8 baselines + AMS + Oracle)

**Metrics**: Average delay, P99, SLA satisfaction, cost, utilization

**Expected**: Oracle ≥ AMS > Fixed-Medium > AWStream > Greedy-Local > Fixed-Light > Fixed-Heavy > Random

### Experiment 2: Heterogeneity Impact

**Scenarios**: H = 0.0 (homogeneous) → 0.3 → 0.6 → 1.0 (high)

**Goal**: AMS benefits increase with H

### Experiment 3: Scalability (Small/Medium/Large)

| Scale | Nodes | Services | Chains | λ | Decision Time |
|-------|-------|----------|--------|---|---------------|
| Small | 3 | 3 | 2 | 5-15 | < 1s |
| Medium | 5-10 | 4-6 | 3-5 | 10-50 | < 10s |
| Large | 20-50 | 10+ | 10+ | 50-200 | < 60s |

### Experiment 4: Dynamic Load (MMPP) — REQUIRED

**Model**: Two-state MMPP
- State 1 (Low): λ₁ = 10, duration ~ Exp(α=1/60)  # 1 minute
- State 2 (High): λ₂ = 30, duration ~ Exp(β=1/40)  # 40 seconds

**AMS Adaptation**:
- Monitor rate over sliding window W = 30s
- Re-run AMS when change > 20%
- Metrics: adaptation delay, reconfiguration overhead, delay time series

### Experiment 5: Robustness

- Node failure (10% random removal)
- μ estimation error ±20%
- λ estimation error ±30%

### Experiment 6: Ablation Study

| Variant | Heterogeneity | Adaptive | Global Opt |
|---------|--------------|----------|------------|
| AMS-Full | ✅ | ✅ | ✅ |
| AMS-NoHetero | ❌ | ✅ | ✅ |
| AMS-NoAdaptive | ✅ | ❌ | ✅ |
| AMS-LocalOnly | ✅ | ✅ | ❌ |

### Experiment 7: Adaptive Accuracy Regulation (REDESIGNED)

**Purpose**: Show AMS dynamically adjusts accuracy based on load

**Setup**:
- Vary accuracy threshold: 85%, 90%, 95%
- Under different load levels: low, medium, high
- Observe: which variant AMS selects under each condition

**Metrics**:
- Selected variant distribution per node
- Accuracy vs delay trade-off curve
- Load-adaptation heatmap

**Visualization**:
- X-axis: Load level
- Y-axis: Node type
- Color: Selected variant (light/medium/heavy)

### Experiment 8: Algorithm Overhead

- Decision time vs nodes/services
- Convergence iterations
- Memory overhead

---

## 5. Metrics (Complete)

### Performance
| Metric | Symbol | Definition |
|--------|--------|------------|
| Average E2E delay | E[T] | Mean response time |
| P99 delay | T₉₉ | 99th percentile |
| Throughput | Θ | Max sustainable λ |
| SLA satisfaction | η | Fraction meeting SLA |

### Resource
| Metric | Symbol | Definition |
|--------|--------|------------|
| Deployment cost | Cost | Σ(instances × cost/hour) |
| CPU utilization | U_CPU | Average CPU usage |
| GPU utilization | U_GPU | Average GPU usage |

### Quality
| Metric | Symbol | Definition |
|--------|--------|------------|
| Model accuracy | Acc | Average accuracy |
| Accuracy loss | ΔAcc | 1 - Acc/Acc_heavy |

### Algorithm
| Metric | Symbol | Definition |
|--------|--------|------------|
| Decision time | T_dec | Time to compute decision |
| Convergence iterations | I_conv | Iterations to converge |
| Reconfiguration freq | F_reconf | Switches per unit time |

### Fairness
| Metric | Symbol | Definition |
|--------|--------|------------|
| Jain's fairness | J | (Σxᵢ)² / (n·Σxᵢ²) |

---

## 6. Statistical Methodology (Complete)

### Warm-up and Run Length

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Warm-up | 1000 requests OR 5 minutes | Transient elimination |
| Run length | 10000 requests OR 30 minutes | CI estimation |
| Replications | 20 | Standard for 95% CI |

### Confidence Interval

```python
def compute_confidence_interval(data, confidence=0.95):
    """
    Compute mean and confidence interval using t-distribution.
    """
    import numpy as np
    from scipy import stats
    
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    
    t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
    margin = t_critical * std / np.sqrt(n)
    
    return mean, mean - margin, mean + margin
```

### Statistical Significance Test

```python
def wilcoxon_test(ams_results, baseline_results):
    """
    Wilcoxon signed-rank test for paired samples.
    Tests if AMS significantly outperforms baseline.
    """
    from scipy.stats import wilcoxon
    
    statistic, p_value = wilcoxon(ams_results, baseline_results, alternative='less')
    
    return {
        'statistic': statistic,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'effect_size': compute_cohens_d(ams_results, baseline_results)
    }
```

**Reporting Standard**:
- All results: Mean ± 95% CI
- AMS vs best baseline: Wilcoxon test (p < 0.05)
- Effect size: Cohen's d (small: 0.2, medium: 0.5, large: 0.8)

---

## 7. Approximation Validation Plan

```python
def validate_approximation(configs):
    """
    Validate QNA approximation against DES for representative configs.
    """
    results = []
    
    for config in configs:
        # Analytical (fast)
        delay_qna = analytical_simulation(config)
        
        # DES (slow, accurate)
        delay_des = discrete_event_simulation(config, duration=3600)
        
        error = abs(delay_qna - delay_des) / delay_des * 100
        
        results.append({
            'rho': config.utilization,
            'delay_qna': delay_qna,
            'delay_des': delay_des,
            'error_pct': error
        })
    
    return results
```

**Validation Configs** (5 representative):
| Config | ρ | Expected Error |
|--------|---|----------------|
| Low load | 0.3 | < 5% |
| Medium load | 0.5 | < 8% |
| High load | 0.7 | < 15% |
| Very high | 0.8 | Flag: > 15% |
| Burst | 0.9 | Flag: > 20% |

---

## 8. Implementation Framework

```
experiment/
├── main.py
├── config.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── erlang_c.py              # Stable + log-space + Hayward
│   ├── traffic_solver.py        # Iterative solver with convergence
│   ├── delay_calculator.py      # Critical path E2E delay
│   ├── stability.py             # Stability check
│   └── qna_validation.py        # DES validation
├── models/
│   ├── node.py
│   ├── service.py
│   ├── chain.py
│   └── variant.py
├── algorithms/
│   ├── ams.py                   # Our algorithm
│   ├── fixed_light.py
│   ├── fixed_medium.py
│   ├── fixed_heavy.py
│   ├── random_baseline.py
│   ├── greedy_local.py
│   ├── cloud_only.py
│   ├── edge_only.py
│   ├── awstream.py              # Competitive baseline
│   └── oracle.py
├── experiments/
│   ├── exp1_static_benchmark.py
│   ├── exp2_heterogeneity.py
│   ├── exp3_scalability.py
│   ├── exp4_dynamic_load.py     # MMPP
│   ├── exp5_robustness.py
│   ├── exp6_ablation.py
│   ├── exp7_adaptive_accuracy.py # REDESIGNED
│   └── exp8_overhead.py
├── metrics/
│   └── evaluator.py
├── stats/
│   ├── confidence_interval.py
│   └── significance_test.py     # Wilcoxon + Cohen's d
└── visualization/
    └── plots.py
```

---

## 9. Key Formulas Summary (v4 Final — All Corrected)

| Formula | Description | Status |
|---------|-------------|--------|
| `λ_{m,n} = Σ λ_ext + Σ P·λ_up` | Traffic equations | ✅ |
| `A = λ / μ` | Offered load (Erlangs) | ✅ |
| `ρ = A / c` | Utilization | ✅ |
| `C(c,A) = [(A^c/c!)·(c/(c-A))] / [Σ(A^i/i!) + (A^c/c!)·(c/(c-A))]` | Erlang-C (explicit) | ✅ |
| `B(i) = (A·B(i-1)) / (i + A·B(i-1))` | Erlang-B recurrence | ✅ |
| `C = (c·B) / (c - A + A·B)` | Erlang-C from Erlang-B | ✅ |
| `L_q = C·ρ/(1-ρ)` | Queue length (waiting) | ✅ |
| `L = L_q + A` | Queue length (system) | ✅ |
| `W_q = L_q / λ` | Waiting time | ✅ |
| `R = W_q + 1/μ` | Response time | ✅ |
| `E[T] = CriticalPath(DAG)` | End-to-end delay | ✅ |
| `μ_{m,k,n} = base_μ × speed_n` | Heterogeneous rate | ✅ |

---

## 10. Definition of Done

- [ ] Core engine: Erlang-C (stable + log-space + Hayward)
- [ ] Traffic equation solver (convergence + divergence check)
- [ ] Delay calculator (critical path)
- [ ] Resource constraint enforcement (hard)
- [ ] AMS algorithm (complete pseudocode → implementation)
- [ ] 9 Baseline algorithms (8 + Oracle)
- [ ] Experiment 1: Static benchmark
- [ ] Experiment 2: Heterogeneity impact
- [ ] Experiment 3: Scalability (S/M/L)
- [ ] Experiment 4: Dynamic load (MMPP)
- [ ] Experiment 5: Robustness
- [ ] Experiment 6: Ablation study
- [ ] Experiment 7: Adaptive accuracy regulation (REDESIGNED)
- [ ] Experiment 8: Algorithm overhead
- [ ] Statistical methods: CI + Wilcoxon + Cohen's d
- [ ] QNA validation (DES comparison, 5 configs)
- [ ] Visualization scripts
- [ ] README with reproduction instructions
- [ ] Requirements.txt
