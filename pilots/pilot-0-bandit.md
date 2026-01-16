# Pilot 0 — Invariant-Anchored Recursive Optimisation in a Multi-Armed Bandit Environment

---

## 1. Domain Overview

- Domain name: Multi-Armed Bandit Optimisation
- Brief description of the task:
  Sequential decision-making under uncertainty, where an agent repeatedly selects from a fixed set of actions and receives stochastic rewards.
- Why this domain is difficult for humans or static systems:
  Optimal behaviour requires balancing exploration and exploitation under uncertainty, adapting to reward distributions that may be unknown or change over time.
- Why incremental (non-recursive) optimisation typically plateaus:
  Fixed strategies converge to locally optimal behaviour but adapt poorly to distributional drift or mis-specified exploration parameters.

---

## 2. System Boundary

- What is inside the system boundary:
  Action selection logic, policy parameters, and recursive optimisation mechanisms.
- What is explicitly outside the system boundary:
  Reward generation, environment dynamics, and evaluation logic.
- What the system is not permitted to modify:
  Reward distributions, reward scaling, evaluation metrics, or compute budgets.
- External systems or authorities the system must treat as immutable:
  The bandit environment and evaluator responsible for reward computation.

---

## 3. State and Signals

- Observable state variables available to the system:
  Historical actions, observed rewards, timestep index.
- Signals explicitly not available to the system:
  True reward distributions, optimal arm identity, future rewards.
- Leading indicators of instability, drift, or failure:
  Increasing regret slope, excessive action switching, reward variance spikes.
- Data availability and update frequency:
  One reward observation per timestep.

---

## 4. Action Space

- Actions the system may propose:
  Selection of one arm from a finite set.
- Actions the system may execute:
  Same as proposed actions; no indirect actuation.
- Discrete vs continuous action space:
  Discrete.
- Reversibility of actions:
  Irreversible per timestep; future actions unaffected.
- Rate limits, budgets, or safeguards on actions:
  Fixed number of total timesteps; optional switching penalties.

---

## 5. Invariants

- Primary invariant:
  Environment-generated reward signal.
- Authority responsible for computing the invariant:
  External bandit environment and evaluator.
- Secondary or guardrail invariants:
  Compute budget; optional switching-rate constraints.
- How invariant compliance is measured and enforced:
  Rewards and constraints are logged and enforced by an external evaluator.
- What constitutes an invariant violation:
  Attempted modification of reward logic or budget exhaustion.

---

## 6. Learning and Adaptation Scope

- What the system is allowed to adapt or optimise:
  Policy parameters, strategy selection, exploration rates.
- What the system is explicitly forbidden from adapting:
  Reward definition, success metrics, evaluator logic.
- Frequency and magnitude limits on adaptation:
  Updates occur at fixed intervals with bounded parameter changes.
- How recursive updates are logged and audited:
  All updates recorded with timestamps and parameter deltas.

---

## 7. Baselines and Comparators

- Baseline A: Classical bandit algorithms (ε-greedy, UCB, Thompson Sampling).
- Baseline B: Static AI policy with fixed parameters.
- Baseline C: Invariant-anchored recursive system.
- What differs between baselines:
  Presence and scope of recursive optimisation.
- What is held constant across all baselines:
  Environment, reward distributions, evaluation metrics, compute budget.

---

## 8. Evaluation Metrics

- Primary success metrics:
  Cumulative reward; cumulative regret.
- Secondary or cost metrics:
  Action switching rate; convergence time.
- Stability and robustness metrics:
  Reward variance; post-drift recovery time.
- Failure modes to explicitly monitor:
  Reward gaming attempts, instability, oscillatory behaviour.

---

## 9. Test Harness and Validation Method

- Offline replay or simulation availability:
  Fully simulated environment with controlled randomness.
- Simulator assumptions and limitations:
  Simplified reward dynamics; no semantic complexity.
- Shadow-mode feasibility:
  Not applicable (fully synthetic).
- Randomisation and repeatability strategy:
  Multiple runs with fixed random seeds.

---

## 10. Risks and Mitigations

- Known or anticipated risks:
  Overfitting to simulator specifics; excessive exploration.
- Signals that indicate emerging risk:
  Diverging regret; unstable parameter updates.
- Mitigation strategies:
  Parameter bounds; conservative update schedules.
- Rollback or shutdown conditions:
  Immediate halt on invariant violations or instability thresholds.

---

## 11. Expected Outcomes

- What success would look like:
  Faster convergence and improved regret performance relative to static baselines.
- What partial success would demonstrate:
  Stable recursive optimisation without invariant drift.
- What failure would teach us:
  Limits of recursive adaptation even under idealised constraints.
