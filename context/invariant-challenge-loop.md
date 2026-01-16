# Invariant Challenge Loop (ICL)

**Status:** Core IAI mechanism  
**Purpose:** Enable discovery and revision of mis-specified invariants without surrendering evaluation authority  
**Relationship to ZIV:** Safe alternative to self-sovereign reformulation  

---

## 1. Overview

Invariant-Anchored Intelligence (IAI) requires that at least one invariant remains **external, non-self-redefinable, and binding** at all times.  
However, invariants may be *wrong, incomplete, or poorly aligned* with long-term outcomes.

The **Invariant Challenge Loop (ICL)** is the mechanism by which an IAI system may:

- detect strain or misalignment in current invariants,
- generate evidence-based critiques of those invariants,
- propose alternative formulations,

**without ever owning the authority to enact, simulate as enacted, or internally substitute those changes.**

ICL enables progress **without self-sovereignty**.

---

## 2. Design Principle

> **IAI systems may challenge invariants, but may not ratify, enact, or internally assume those challenges.**

This enforces a strict separation between:
- *intelligence* (analysis, hypothesis, discovery),
- and *authority* (decision, ratification, enforcement).

---

## 3. Roles and Separation of Authority

The loop enforces three distinct roles:

### 3.1 Optimiser
- Improves behaviour strictly under current, binding invariants.
- Explores strategies, representations, and policies.
- Detects performance plateaus or trade-offs.

### 3.2 Challenger
- Analyses optimisation dynamics and outcomes.
- Identifies patterns indicating invariant strain or mis-specification.
- Generates hypotheses regarding invariant failure or incompleteness.

### 3.3 Authority (External)
- Reviews challenger outputs.
- Evaluates proposals via simulation or offline replay.
- Decides whether, how, and when invariants change.

**The system may implement roles 1 and 2.  
Role 3 must remain external and authoritative.**

---

## 4. Signals of Invariant Strain

The Challenger is activated when patterns such as the following are observed:

- improving the invariant correlates with degradation in secondary outcomes,
- optimisation gains plateau despite apparent slack elsewhere,
- increased brittleness, instability, or variance,
- repeated reliance on edge cases or pathological trade-offs,
- divergence between short-term metric gains and long-term outcomes.

These signals do **not** indicate failure — they indicate *mis-specification risk*.

---

## 5. Challenger Outputs

The Challenger may produce the following **advisory-only** outputs:

### 5.1 Invariant Critiques
Structured claims such as:
- “Invariant A conflicts with observed causal structure.”
- “Optimising X produces negative second-order effects Y.”

### 5.2 Evidence Packages
- statistical correlations,
- counterfactual simulations,
- replay results,
- ablation studies.

### 5.3 Alternative Formulations
- revised metrics,
- additional constraints,
- composite or multi-objective formulations,
- candidate guardrails.

### 5.4 Risk Assessments
- expected benefit of change,
- new failure modes introduced by revision,
- reversibility and rollback analysis.

All outputs remain **non-binding**.

---

## 6. External Review and Ratification

Invariant changes may occur **only** through an external process:

1. Review challenger outputs.
2. Validate claims via replay or simulation.
3. Assess asymmetrical risk and reversibility.
4. Approve, reject, or modify proposals.
5. Version, audit, and explicitly ratify any invariant changes.

Until ratification, **all optimisation continues under the existing invariant set**.

---

## 7. Why This Is Not ZIV

The Invariant Challenge Loop differs from a Zero-Invariant Variant (ZIV) in one decisive respect:

> **At no point does the system evaluate itself under an invariant it has not been externally authorised to use.**

| Aspect | ICL | ZIV |
|---|---|---|
| Who critiques invariants | System | System |
| Who replaces invariants | External authority | System |
| Evaluation ownership | External | Internal |
| Falsifiability | Preserved | Lost |
| Rollback | Defined and enforceable | Undefined |

ICL permits reformulation **without epistemic collapse**.

---

## 8. Safety Properties

ICL preserves:

- at least one binding invariant at all times,
- external veto power,
- shared evaluative frames,
- empirical falsifiability,
- staged and reversible change.

These properties are violated if challenger and authority are merged.

---

## 9. Relationship to Progress

ICL acknowledges a fundamental constraint:

> **Progress requires questioning assumptions.  
Safety requires that someone else can prove those questions were wrong.**

IAI institutionalises both.

---

## 10. Status and Use

The Invariant Challenge Loop is a **core, always-on capability** of IAI systems.

It is:
- encouraged in offline replay and simulation,
- monitored in shadow mode,
- tightly governed in live deployments.

ICL eliminates the need for Zero-Invariant experimentation in production systems.

---

## 11. Summary

The Invariant Challenge Loop formalises how IAI systems can:

- remain corrigible,
- challenge human assumptions,
- propose better formulations,
- and still preserve a shared, external notion of success.

It is the mechanism that allows IAI to evolve **without crossing the boundary into self-sovereign evaluation**.
