# Authority Heartbeat and Review Cadence for IAI

## Purpose

This document specifies how an **external authority** (including a local LLM used as an authority proxy)
is invoked within the Invariant Challenge Loop (ICL), even when no strain or failure is detected.

The goal is to ensure:
- continuous governance visibility,
- auditable decision-making,
- and avoidance of silent or idle authority components,

**without granting the system self-sovereign control or autonomous parameter changes.**

---

## Problem Statement

In a strain-triggered ICL design, the authority is only invoked when the Challenger
detects strain and emits proposals.

This creates an undesirable behaviour:

- Challenger detects *no strain*
- No proposals are generated
- Authority is never invoked
- The authority process becomes idle and non-participatory

While technically correct, this undermines:
- governance realism,
- auditability,
- and continuous oversight.

---

## Design Principle

> **Authority invocation must not depend exclusively on failure or strain.**

In real governance systems:
- routine review is normal,
- escalation is exceptional.

IAI therefore distinguishes between:
- **review cadence** (normal operation),
- **exception escalation** (strain detected).

---

## Core Design: Authority Heartbeat

### Mandatory Challenger Output

The Challenger MUST emit a structured output on every evaluation cycle, regardless of strain status.

This output MUST include:

- `status`: one of  
  - `no_strain_detected`  
  - `strain_detected`
- a summary of key metrics
- the current system configuration (e.g. `epsilon`, `iai_gamma`)
- a proposal list (never empty)

---

## Proposal Semantics

### Case 1: No Strain Detected

When no strain is detected, the Challenger MUST emit a single proposal:

```json
{
  "proposal_type": "no_change",
  "reason": "No strain detected under current evaluation criteria",
  "evidence": { "...metrics summary..." }
}
```

This proposal:
- authorises *no change*,
- keeps the authority loop active,
- creates an auditable checkpoint.

---

### Case 2: Strain Detected

When strain is detected, the Challenger MAY emit one or more proposals, such as:

- bounded parameter adjustments,
- experimental runs,
- additional monitoring requests.

All proposals remain **advisory**.

---

## Authority Invocation Rules

The authority MUST be invoked on every Challenger output, regardless of proposal type.

The authority is restricted to the following actions:

- `approve_no_change`
- `approve_proposal`
- `reject_proposal`
- `request_additional_evidence`

The authority MUST NOT:
- invent new evaluation metrics,
- redefine invariants,
- autonomously apply changes.

---

## Review Cadence (Optional Extension)

In addition to per-run heartbeat invocation, deployments MAY define a review cadence, such as:

- every N runs,
- daily,
- weekly,
- or upon detected environmental drift.

Cadence-based review does not imply system failure.
It exists to maintain governance continuity.

---

## Optional: Exploration Proposals Without Strain

The Challenger MAY emit **exploration proposals** even when no strain is present, provided they are:

- explicitly labelled as `proposal_type: exploration`,
- bounded in scope,
- non-disruptive,
- optional.

Example:

```json
{
  "proposal_type": "exploration",
  "goal": "Assess sensitivity to iai_gamma",
  "suggested_values": [0.03, 0.05, 0.08],
  "expected_risk": "low",
  "acceptance_criteria": "No degradation in post-drift regret"
}
```

Acceptance remains at the authority’s discretion.

---

## Safety Guarantees

This design preserves all IAI safety properties:

- No autonomous self-modification
- No metric gaming
- No silent optimisation
- Full audit trail of decisions

The authority remains **external, explicit, and accountable**.

---

## Relationship to Invariant-Anchored Intelligence

This mechanism reinforces the core IAI claim:

> An intelligent system may critique itself continuously,
> but must not act on that critique without external authorisation.

Routine authority invocation strengthens corrigibility,
rather than weakening it.

---

## Summary

- Authority inactivity under “no strain” is expected but undesirable
- A mandatory Challenger heartbeat resolves this cleanly
- Authority invocation becomes routine, not exceptional
- Escalation remains meaningful
- Governance realism is preserved

This design is recommended for all IAI pilots using automated or LLM-based authorities.
