# Pilot Definition Template (Invariant-Anchored Intelligence)

Use this template to define, bound, and evaluate candidate pilot domains for invariant-anchored recursive optimisation.

---

## 1. Domain Overview

- Domain name:
- Brief description of the task:
- Why this domain is difficult for humans or static systems:
- Why incremental (non-recursive) optimisation typically plateaus:

---

## 2. System Boundary

- What is inside the system boundary:
- What is explicitly outside the system boundary:
- What the system is *not permitted* to modify:
- External systems or authorities the system must treat as immutable:

---

## 3. State and Signals

- Observable state variables available to the system:
- Signals explicitly *not* available to the system:
- Leading indicators of instability, drift, or failure:
- Data availability and update frequency:

---

## 4. Action Space

- Actions the system may propose:
- Actions the system may execute (if any):
- Discrete vs continuous action space:
- Reversibility of actions:
- Rate limits, budgets, or safeguards on actions:

---

## 5. Invariants

- Primary invariant (authoritative success signal):
- Authority responsible for computing the invariant:
- Secondary or guardrail invariants (if any):
- How invariant compliance is measured and enforced:
- What constitutes an invariant violation:

---

## 6. Learning and Adaptation Scope

- What the system is allowed to adapt or optimise:
- What the system is explicitly forbidden from adapting:
- Frequency and magnitude limits on adaptation:
- How recursive updates are logged and audited:

---

## 7. Baselines and Comparators

- Baseline A: traditional or existing approach:
- Baseline B: static (non-recursive) AI or heuristic system:
- Baseline C: invariant-anchored recursive system:
- What differs between baselines:
- What is held constant across all baselines:

---

## 8. Evaluation Metrics

- Primary success metrics (externally computed):
- Secondary or cost metrics:
- Stability and robustness metrics:
- Failure modes to explicitly monitor:

---

## 9. Test Harness and Validation Method

- Offline replay or simulation availability:
- Simulator assumptions and limitations:
- Shadow-mode feasibility:
- Randomisation and repeatability strategy:

---

## 10. Risks and Mitigations

- Known or anticipated risks:
- Signals that indicate emerging risk:
- Mitigation strategies:
- Rollback or shutdown conditions:

---

## 11. Expected Outcomes

- What success would look like:
- What partial success would demonstrate:
- What failure would teach us:
