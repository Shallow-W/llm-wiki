# Experiment Framework v3: Heterogeneous Edge Network with Dynamic Model Selection

## Revision Notes (v2 → v3)

Based on Round 2 review feedback, v3 makes the following critical corrections:
- **Queuing Model Theory**: Explicitly state we use simplified Whitt's QNA, acknowledge approximation error
- **Erlang-C Formula**: Explicit full formula with A in Erlangs
- **End-to-End Delay**: Explicitly define critical path method
- **Resource Constraints**: Explicitly define as hard constraints with infeasible handling
- **Traffic Equation Solver**: Complete iterative solver pseudocode with convergence check
- **Numerical Stability**: Specify recursive Erlang-C calculation
- **Dynamic Load**: Explicitly use MMPP (Markov Modulated Poisson Process)
- **Statistical Details**: Add warm-up period, run length, CI calculation

---

## 1. System Model

### 1.1 Network Topology (Heterogeneous)

Same as v2 (see v2 document for full table).

Key: Each node has speed_factor that scales base processing rate.

### 1.2 Service Model with Multiple Variants

Same as v2.

### 1.3 Service Chain (DAG) — Critical Path Definition

**End-to-End Delay Definition (CRITICAL — v3 Clarification)**:

We use **Critical Path Method** for DAG delay calculation:

```
For a service chain DAG:
1. Assign each node (service instance) a weight = R_{m,n} (response time)
2. Assign each edge a weight = D_{n_i,n_j} (communication delay)
3. Find the longest path from source to sink
4. E2E delay = sum of weights on critical path
```

**Example**:
```
Chain with parallel branches:
    A(10ms)
   /        \
  B(20ms)   C(15ms)
   \        /
    D(10ms)

Critical path: A → B → D = 10 + 20 + 10 = 40ms
(Not A → C → D = 10 + 15 + 10 = 35ms)
```

---

## 2. Analytical Simulation Framework

### 2.1 Queuing Model — Simplified QNA (Queueing Network Analyzer)

**Theoretical Foundation**:

We use a **simplified version of Whitt's Queueing Network Analyzer (QNA)**:

1. **Each service-node pair is modeled as independent M/M/c queue**
2. **Arrival rates computed via traffic equations** (flow conservation)
3. **Approximation**: We treat merged flows as Poisson (independent approximation)

**Approximation Error Analysis**:

| Condition | Approximation Error | Mitigation |
|-----------|-------------------|------------|
| ρ < 0.5 | < 5% | Acceptable |
| 0.5 ≤ ρ < 0.7 | 5-15% | Acceptable with caveat |
| ρ ≥ 0.7 | > 15% | Flag in results; consider DES validation |

**Validation**: For critical results, we validate a subset using discrete event simulation (SimPy) to confirm approximation accuracy.

### 2.2 Mathematical Model (v3 Corrected and Clarified)

#### Step 1: Traffic Equations

For each service m at node n:

```
λ_{m,n} = Σ_f x_{m,n} · λ_f · I(m ∈ chain_f)          (external arrivals)
          + Σ_{m'} Σ_{n'} P_{m',n'→m,n} · λ_{m',n'}     (routed arrivals)
```

**Note**: This is a linear system solved iteratively.

#### Step 2: Resource Constraints (HARD CONSTRAINTS)

For each node n:
```
Σ_m x_{m,n} · N_{m,n} · CPU_req_{m,k} ≤ CPU_n          (CPU)
Σ_m x_{m,n} · N_{m,n} · GPU_req_{m,k} ≤ GPU_n          (GPU)
Σ_m x_{m,n} · GPU_mem_{m,k} ≤ Mem_n                    (Memory)
```

**Hard Constraint Policy**: If constraints violated, deployment is **INFEASIBLE**. AMS algorithm must reject or repair.

#### Step 3: M/M/c Queueing Analysis — Erlang-C (Complete Formula)

For each deployed service m at node n with variant k:

```
Offered load:          A_{m,n} = λ_{m,n} / μ_{m,k,n}    [Unit: Erlangs]
Number of servers:     c_{m,n} = N_{m,n}
Utilization:           ρ_{m,n} = A_{m,n} / c_{m,n}

Stability check:       ρ_{m,n} < 1  (REQUIRED)

Erlang-C formula (COMPLETE):

C(c, A) = [ (A^c / c!) · (c / (c - A)) ] / 
          [ Σ_{i=0}^{c-1} (A^i / i!) + (A^c / c!) · (c / (c - A)) ]

Where:
- A = offered load in Erlangs
- c = number of parallel servers
- Requires: A < c (i.e., ρ < 1)

Average queue length (waiting):  
L_q = C(c, A) · ρ / (1 - ρ) = C(c, A) · A / (c - A)

Average queue length (system):
L = L_q + A

Average waiting time:
W_q = L_q / λ_{m,n}

Average response time:
R_{m,n} = W_q + 1/μ_{m,k,n}
```

**Numerical Stability — Recursive Calculation**:

For large c (c > 100), use recursive form to avoid overflow:

```python
def erlang_c_recursive(c, A):
    """
    Numerically stable Erlang-C calculation
    Using recursion: C(c,A) from C(c-1,A)
    """
    # Base case
    C = A  # C(1, A) = A
    
    for i in range(2, c + 1):
        C = (A * C) / (i - A + A * C)
    
    return C
```

#### Step 4: End-to-End Delay (Critical Path)

```
E[T_f] = CriticalPathDelay(DAG_f)

Where CriticalPathDelay:
1. Build weighted DAG: node weight = R_{m,n}, edge weight = D_{n_i,n_j}
2. Find longest path from ingress to egress
3. Sum weights on critical path
```

#### Step 5: SLA Satisfaction

```
η_f = 1  if E[T_f] ≤ T_f^max, else 0
η = (Σ_f η_f · λ_f) / (Σ_f λ_f)
```

### 2.3 Traffic Equation Solver (Complete Pseudocode)

```python
def solve_traffic_equations(X, P, chains, requests, max_iter=1000, tol=1e-6):
    """
    Iterative solver for traffic equations
    
    Input:
        X: Deployment matrix
        P: Routing probability matrix
        chains: Service call chains
        requests: Request flows
    
    Output:
        λ: Arrival rates λ[m,n]
        converged: Boolean
    """
    # Initialize
    λ = {}
    for m in services:
        for n in nodes:
            λ[m,n] = 0.0
    
    # Iterative solution (Gauss-Seidel style)
    for iteration in range(max_iter):
        λ_old = λ.copy()
        
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
                    P[m_prev, n_prev, m, n] * λ[m_prev, n_prev]
                    for m_prev in services
                    for n_prev in nodes
                    if P.get((m_prev, n_prev, m, n), 0) > 0
                )
                
                λ[m,n] = external + routed
        
        # Check convergence
        max_diff = max(abs(λ[m,n] - λ_old[m,n]) for m in services for n in nodes)
        if max_diff < tol:
            return λ, True
    
    # Not converged
    return λ, False
```

---

## 3. Algorithm Design

### 3.1 AMS Algorithm (v3 Complete)

```python
def AMS(network, services, chains, requests, accuracy_threshold):
    """
    Adaptive Model Selection Algorithm (Complete v3)
    
    Objective: Minimize weighted end-to-end delay
    Constraints: SLA, accuracy, resource (hard)
    """
    
    # Phase 1: Initialization
    X = initialize_with_medium_variant(network, services)
    N = initialize_instance_counts(X, network)
    
    # Phase 2: Iterative Optimization
    for iteration in range(MAX_ITER):
        
        # 2.1 Solve traffic equations
        λ, converged = solve_traffic_equations(X, P, chains, requests)
        if not converged:
            print("Warning: Traffic equations did not converge")
            break
        
        # 2.2 Check resource feasibility (HARD CONSTRAINTS)
        if not check_resource_constraints(X, N, network):
            X, N = repair_infeasible(X, N, network)
            continue
        
        # 2.3 Check stability
        if not check_stability(λ, X, N, services, network):
            X, N = add_instances(X, N, network)
            continue
        
        # 2.4 Compute delays
        R = compute_response_times(λ, X, N, network, services)
        E2E = compute_e2e_delays(R, P, chains)
        
        # 2.5 Check convergence
        if converged(E2E, prev_E2E):
            break
        
        # 2.6 Greedy variant selection
        improved = False
        for n in network.nodes:
            for m in services:
                if X[m,n] == 0:
                    continue
                
                current_variant = get_variant(X, m, n)
                current_delay = E2E[chains_containing(m)]
                
                best_variant = current_variant
                best_delay = current_delay
                
                for variant in services[m].variants:
                    # Accuracy constraint
                    if variant.accuracy < accuracy_threshold:
                        continue
                    
                    # Resource feasibility (check before evaluating)
                    temp_X = switch_variant(X, m, n, variant)
                    if not check_resource_constraints(temp_X, N, network):
                        continue
                    
                    # Evaluate delay
                    temp_R = compute_response_times_for_variant(λ, temp_X, N, m, n, variant)
                    temp_E2E = compute_e2e_delays(temp_R, P, chains)
                    
                    if temp_E2E < best_delay:
                        best_delay = temp_E2E
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


def repair_infeasible(X, N, network):
    """
    Repair infeasible deployment by:
    1. Reducing instance counts
    2. Switching to lighter variants
    3. Removing low-priority services
    """
    # Try reducing instances first
    for n in network.nodes:
        while not check_node_resources(X, N, n):
            # Find service with most resource usage
            m_max = argmax(services, lambda m: resource_usage(X, N, m, n))
            if N[m_max, n] > 1:
                N[m_max, n] -= 1
            else:
                # Switch to lighter variant
                lighter = get_lighter_variant(X, m_max, n)
                if lighter:
                    X = switch_variant(X, m_max, n, lighter)
                else:
                    # Remove service
                    X[m_max, n] = 0
    
    return X, N
```

---

## 4. Experiment Design (8 Experiments)

Same 8 experiments as v2, with the following enhancements:

### Experiment 4: Dynamic Load (MMPP Model)

**Dynamic Load Model**: Markov Modulated Poisson Process (MMPP)

```
Two-state MMPP:
- State 1 (Low): λ_1 = 10 req/s, duration ~ Exp(α)
- State 2 (High): λ_2 = 30 req/s, duration ~ Exp(β)

Transition matrix:
    [ -α    α  ]
Q = [  β   -β  ]

Where α = 1/300 (mean low duration = 300s)
      β = 1/200 (mean high duration = 200s)
```

**AMS Adaptation**:
- Monitor arrival rate over sliding window (W = 50s)
- Re-run AMS when rate change > 20%
- Measure: adaptation delay, reconfiguration overhead

### Statistical Methodology

**For each experiment configuration**:
1. **Warm-up period**: Discard first 1000 samples (transient)
2. **Run length**: 10000 samples after warm-up
3. **Replications**: 10 independent runs with different seeds
4. **Reporting**: Mean ± 95% confidence interval

```
95% CI = mean ± t_{0.025, n-1} · (s / √n)

Where:
- t_{0.025, 9} = 2.262 (for 10 replications)
- s = sample standard deviation
- n = 10
```

---

## 5. Metrics (Same as v2)

---

## 6. Reproducibility (Enhanced)

### Warm-up and Run Length

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Warm-up samples | 1000 | Discard transient state |
| Run length | 10000 | Sufficient for CI estimation |
| Replications | 10 | Standard for 95% CI |

### Confidence Interval Calculation

```python
def compute_confidence_interval(data, confidence=0.95):
    """
    Compute mean and confidence interval
    
    Input: data = [x1, x2, ..., xn] from n replications
    Output: (mean, lower_bound, upper_bound)
    """
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    
    # t-distribution critical value
    t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
    
    margin = t_critical * std / np.sqrt(n)
    
    return mean, mean - margin, mean + margin
```

---

## 7. Implementation Framework

Same as v2, with additions:
- `core/qna_approximation.py`: QNA approximation validation
- `core/erlang_c_recursive.py`: Numerically stable Erlang-C
- `core/traffic_solver.py`: Iterative traffic equation solver
- `experiments/validation_des.py`: DES validation for subset

---

## 8. Key Formulas Summary (v3 Final)

| Formula | Description | Status |
|---------|-------------|--------|
| `λ_{m,n} = Σ λ_ext + Σ P·λ_up` | Traffic equations | ✅ |
| `A = λ / μ` | Offered load (Erlangs) | ✅ |
| `ρ = A / c` | Utilization | ✅ |
| `C(c,A) = [(A^c/c!)·(c/(c-A))] / [Σ(A^i/i!) + (A^c/c!)·(c/(c-A))]` | Erlang-C (complete) | ✅ |
| `L_q = C(c,A)·ρ/(1-ρ)` | Queue length (waiting) | ✅ |
| `L = L_q + A` | Queue length (system) | ✅ |
| `W_q = L_q / λ` | Waiting time | ✅ |
| `R = W_q + 1/μ` | Response time | ✅ |
| `E[T] = CriticalPath(DAG)` | End-to-end delay | ✅ |
| `μ_{m,k,n} = base_μ × speed_n` | Heterogeneous service rate | ✅ |

---

## 9. Approximation Validation Plan

To address Reviewer A's concern about approximation error:

**Subset Validation**:
1. Select 5 representative configurations (varying ρ from 0.3 to 0.8)
2. Run both analytical (QNA) and DES (SimPy) for each
3. Compare: delay difference < 10%?
4. Report validation results in appendix

```python
def validate_approximation(config):
    """
    Compare QNA approximation with DES ground truth
    """
    # Analytical (fast)
    delay_qna = analytical_simulation(config)
    
    # DES (slow, but accurate)
    delay_des = discrete_event_simulation(config, duration=3600)
    
    error = abs(delay_qna - delay_des) / delay_des * 100
    
    return error  # Should be < 10% for ρ < 0.7
```

---

## 10. Definition of Done

Same as v2, plus:
- [ ] QNA approximation validation (DES comparison)
- [ ] Erlang-C recursive implementation (numerically stable)
- [ ] Traffic equation solver with convergence check
- [ ] Resource constraint hard enforcement
- [ ] MMPP dynamic load model
- [ ] Statistical methodology (warm-up, CI)
- [ ] Critical path delay calculation
