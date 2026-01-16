# Proposal: Invariant-Anchored Intelligence

## 1. Purpose

This document proposes a design approach for **local, self-improving AI systems**
capable of solving problems that are currently unachievable for human-led processes,
without requiring global control or full technological singularity.

The aim is to define a **credible middle path**:
- more powerful than constrained, static AI systems,
- less irreversible than full self-sovereign intelligence.

The proposal is intended to be:
- concrete,
- testable,
- and grounded in real pilot domains.

---

## 2. Problem Statement

Certain domains exhibit characteristics that make them resistant to human optimisation:

- high-dimensional decision spaces,
- delayed and indirect feedback,
- non-linear interactions,
- coordination across many agents or processes,
- instability emerging faster than human response cycles.

In these domains:
- human governance struggles to keep pace,
- incremental optimisation plateaus,
- advisory AI systems help but do not break structural limits.

Examples include operational queues, supply chains, scheduling systems,
and risk triage pipelines.

The central question is:

> Can AI systems be designed to **improve their own problem-solving capability**
within such domains, without gaining unchecked authority over what counts as truth or success?

---

## 3. Design Space Overview

Broadly, three approaches exist:

### 3.1 Fully Constrained Systems
- Human-defined rules and objectives
- Limited learning
- High predictability
- Low ceiling

These systems are safe but insufficient for genuinely hard problems.

---

### 3.2 Full Self-Sovereign Intelligence
- Intelligence owns its own improvement loop
- Objectives, evaluation, and learning are self-defined
- Maximum flexibility
- Structural irreversibility

While powerful, this approach removes reliable external correction and is out of scope.

---

### 3.3 Invariant-Anchored Intelligence (Proposed)
- Strong self-improvement within a domain
- Freedom to invent representations and strategies
- Freedom to challenge and propose alternative invariants
- At least one external invariant retained as binding at all times
- External authority required to ratify invariant changes

This approach aims to retain **external grounding** while enabling
**revolutionary local capability** and **collaborative invariant evolution**.

---

## 4. Core Concept: Invariant Anchoring

Invariant anchoring means that:

- the system may improve *how* it solves problems,
- the system may *propose* redefinitions of *what counts as success or truth*,
- but the system may not *enact, ratify, or internally assume* such redefinitions.

At least one invariant must remain **external, binding, and authoritative** at all times.

Invariants function as **external measurement anchors**,
not as behavioural or moral constraints.

While invariants remain externally owned, the system may detect strain or mis-specification
in current invariants and propose evidence-based alternatives through a structured
**Invariant Challenge Loop**. All such challenges remain advisory and require external ratification.

Detailed definitions and examples are provided in `context/invariants.md`.
The challenge mechanism is defined in `context/invariant-challenge-loop.md`.

---

## 5. Self-Improvement Without Sovereignty

The proposed systems allow:

- discovery of new internal representations,
- reformulation of subproblems,
- strategy invention and selection,
- learning from outcomes over time,
- detection of invariant strain or mis-specification,
- generation of evidence-based critiques of current invariants,
- proposal of alternative invariant formulations.

The following are explicitly disallowed:

- self-removal of all invariants,
- self-ratification of invariant challenges,
- self-enactment of proposed invariant changes,
- internal substitution or simulation under proposed-but-not-ratified invariants,
- expansion beyond the declared domain.

This preserves corrigibility without enforcing human-style reasoning.
It enables **progress through challenge** without **sovereignty through self-ratification**.

---

## 6. System Characteristics

An invariant-anchored system is expected to be:

- **Self-driven**  
  Initiates action based on detected instability or opportunity.

- **Domain-bounded**  
  Operates within a clearly defined system boundary.

- **Adaptive**  
  Improves performance through experience and exploration.

- **Self-challenging**  
  Capable of detecting and articulating its own evaluation failures or invariant mis-specifications.

- **Grounded**  
  Evaluated against external, non-self-redefinable criteria, even when challenging those criteria.

---

## 7. Proof of Concept Strategy

Rather than speculative deployment, the proposal emphasises
**empirical validation through pilots**.

Each pilot should:
- operate in a closed or well-bounded domain,
- expose observable state and outcomes,
- allow offline replay and shadow testing,
- use clearly defined evaluation metrics.

A general pilot structure is defined in `pilots/pilot-template.md`.

---

## 8. Candidate Pilot Domains

Candidate domains include, but are not limited to:

- casework or ticket queue orchestration,
- supply chain and inventory optimisation,
- compute or job scheduling,
- incident detection and response,
- compliance or risk triage.

These domains share:
- high complexity,
- delayed feedback,
- and significant cost of failure.

---

## 9. Testing and Evaluation

Testing proceeds in stages:

1. **Offline replay**  
   Historical data used to compare system decisions to baselines.  
   Invariant challenge outputs are encouraged and logged for review.

2. **Shadow mode**  
   Live data with advisory-only output.  
   Challenger outputs are monitored alongside operational recommendations.

3. **Reversible actuation**  
   Limited, rate-controlled actions with rollback capability.  
   Invariant challenges are tightly governed with mandatory external review.

At each stage, **challenger outputs** (critiques, evidence packages, alternative formulations)
are logged, versioned, and reviewed by external authorities. Invariant changes require
explicit ratification and are never enacted unilaterally.

Success is defined strictly by **external metrics**, not internal confidence.

---

## 10. Expected Outcomes

A successful pilot would demonstrate that:

- the system improves outcomes beyond human baselines,
- self-improvement does not require self-sovereignty,
- invariants do not prevent radical capability gains,
- local deployment avoids global irreversibility,
- system-initiated invariant challenges improve human understanding of the domain,
- challenger outputs accelerate invariant evolution through evidence-based collaboration.

Failure is also informative, clarifying:
- where constraints bind too tightly,
- where stronger autonomy may truly be required,
- what signals reliably indicate invariant strain vs operational instability,
- whether challenge mechanisms improve or degrade human-system trust,
- how often human-specified invariants prove incomplete or mis-specified.

---

## 11. Next Steps

Immediate next steps include:

1. Selecting a first pilot domain
2. Choosing the primary invariant for that pilot
3. Building a minimal test harness
4. Running offline and shadow evaluations
5. Documenting results and failure modes

Further escalation should be based on evidence, not assumption.

---

## 12. Position Statement

This proposal does not claim to solve all problems,
nor to eliminate the eventual need for more radical intelligence.

It claims only that:

> **Local, invariant-anchored, self-improving AI systems are a necessary
and testable step toward solving problems currently beyond human reach.**

Everything else should follow from evidence.
