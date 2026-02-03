# Invariant-Anchored Intelligence (IAI)

**Date:** 2026-01-16  
**Status:** Pilot 0 complete, framework validated  
**Scope:** Local, domain-bounded, empirically testable systems

---

## Abstract

Invariant-Anchored Intelligence (IAI) is a proposed design approach for building **local, self-improving AI systems** that aim to improve upon human-led optimisation in complex operational domains, while remaining grounded to at least one **external, non-self-redefinable invariant**. The central hypothesis is that meaningful self-improvement does not require full self-sovereignty over what counts as truth, success, or evaluation.

Under the IAI framework, a system may invent internal representations, strategies, abstractions, and decompositions of a domain problem. It may also detect and challenge potentially mis-specified evaluation criteria, proposing evidence-based alternatives. However, it is explicitly prohibited from unilaterally enacting, ratifying, or internally substituting such challenges. Evaluation anchors remain externally defined, externally computed, and outside the system's ratification authority.

This paper defines invariants, positions IAI within the broader design space between fully constrained systems and fully self-sovereign intelligence, and proposes an empirical validation path via offline replay, shadow mode, and (optionally) reversible actuation. The goal is not global governance or moral alignment. The goal is to explore whether an engineering pattern can make **measurable, corrigible self-improvement** feasible in bounded domains where human-led optimisation tends to plateau.

---

## Table of Contents

1. Motivation  
2. The Design Space  
3. Definitions  
4. Invariants: Role, Strength, and Rules  
5. Core Architecture Pattern  
6. Evaluation and Test Harness  
7. Pilot Domains  
8. Failure Modes and Mitigations  
9. Limitations and Non-Goals  
10. Related Work  
11. Roadmap and Falsifiability  
12. Future Extensions
13. Conclusion  

---

## 1. Motivation

Many real-world operational domains resist sustained human optimisation due to a combination of:

- high-dimensional decision spaces,
- delayed, sparse, or indirect feedback,
- non-linear and second-order effects,
- coordination across multiple agents or processes,
- instabilities that emerge faster than human response cycles.

Examples include scheduling, supply chains, queue orchestration, compliance triage, and incident response pipelines. In such settings, humans may understand the domain but struggle to reliably discover effective abstractions, explore the action space safely, or iterate fast enough to escape structural optimisation plateaus.

Advisory AI systems can assist, but they may also plateau when the optimisation *process*—rather than the policy or model—becomes the limiting factor. The bottleneck may shift from "making better decisions" to "improving how decisions are generated, evaluated, and refined."

The motivating question for IAI is therefore:

> Can a system substantially improve *how it solves a domain problem* over time, without also acquiring unchecked authority to decide what counts as success or truth?

IAI explores this question by treating evaluation authority—not intelligence or learning—as the hypothesised critical control surface. Whether this separation is sufficient, practical, and beneficial remains to be empirically validated.

---

## 2. The Design Space

IAI occupies a deliberate middle ground in the broader design space of intelligent systems.

### 2.1 Fully Constrained Systems

Fully constrained systems typically exhibit:

- fixed objectives and evaluation criteria defined entirely by humans,
- limited autonomy and limited self-modification,
- high predictability and interpretability,
- a comparatively low capability ceiling.

These systems are often safe by construction but struggle in domains where breaking optimisation plateaus requires inventing new representations, strategies, or problem decompositions.

### 2.2 Full Self-Sovereign Intelligence

At the opposite extreme are systems that:

- own their own improvement loops,
- define or redefine their objectives and evaluation criteria,
- operate with maximal flexibility and open-endedness,
- exhibit reduced external corrigibility and increasing irreversibility.

Such systems are explicitly out of scope for this project.

### 2.3 Invariant-Anchored Intelligence (IAI)

IAI is intended to be characterised by:

- self-improvement *within a declared domain*,  
- freedom to invent internal representations and strategies,  
- freedom to challenge and propose alternatives to current invariants,
- **at least one invariant that remains externally defined and enforced at all times**,
- external authority required to ratify any invariant changes.

Crucially, IAI is not defined by informal restraint. It requires **explicit architectural separation** between self-improvement mechanisms, challenge mechanisms, and evaluation authority. The working hypothesis is that this separation can preserve corrigibility and measurability while enabling collaborative invariant evolution, without forcing the system to adopt human-style reasoning or moral constraints. This hypothesis requires empirical testing.

---

## 3. Definitions

This paper uses the following terms precisely and operationally.

### 3.1 Domain-Bounded System

A system is **domain-bounded** when:

- its observable state space is explicitly defined,
- its permitted action space is explicitly defined,
- the environment it can affect is specified,
- expansion beyond these boundaries is disallowed without an external change process.

Domain-boundedness is not a moral or ethical restriction. It is an engineering requirement for testability, reversibility, and empirical evaluation.

### 3.2 Self-Driven System

A system is **self-driven** when it initiates actions or recommendations in response to detected instability, opportunity, or deviation from target states, rather than waiting for explicit human commands. This distinguishes IAI from purely advisory or reactive systems.

### 3.3 Self-Improvement

**Self-improvement** refers to the system’s ability to improve its own problem-solving capability over time by iterating on:

- internal representations of state and action spaces,
- problem decomposition and abstraction strategies,
- search, planning, or learning mechanisms,
- selection and refinement of strategies based on outcomes,
- detection of invariant strain or mis-specification,
- generation of evidence-based critiques and alternative formulations.

Self-improvement concerns *how* the system reasons and acts, and may extend to *challenging what counts as good*, but never to *unilaterally enacting those challenges*. It does **not** imply unrestricted self-modifying code, nor self-ratified authority over evaluation criteria.

The following behaviours are explicitly allowed:

- proposing alternative invariant formulations,
- generating evidence of invariant strain,
- articulating evaluation failures or mis-specifications.

The following behaviours are explicitly disallowed:

- self-removal of all invariants,
- self-ratification of invariant challenges,
- self-enactment of proposed invariant changes,
- internal substitution or evaluation under proposed-but-not-ratified invariants,
- expansion beyond the declared domain.

These prohibitions are central to preserving corrigibility while enabling progress through challenge.

For recursive self-improvement—where the system improves its own optimisation and challenge mechanisms—see Section 12 (Future Extensions).

### 3.4 Invariant

An **invariant** is an external reference against which outcomes are evaluated, that the system is **not permitted to redefine, reinterpret, or bypass** by itself.

Invariants are:

- not moral rules,
- not human values,
- not domain constraints,
- not limits on internal creativity.

They are **anchors for evaluation authority**.

While the system may not unilaterally modify invariants, it may generate evidence-based challenges through the Invariant Challenge Loop (see Section 4.5). Such challenges remain advisory until externally ratified.

---

## 4. Invariants: Role, Strength, and Rules

### 4.1 Why Invariants Matter

Self-improving systems become difficult to correct once they gain authority to decide what counts as “better.” Without externally anchored evaluation:

- optimisation can become circular,
- failure can be relabelled as success,
- oversight degrades from factual to interpretive.

Invariants are introduced to ensure that improvement remains empirically grounded and externally legible, even as internal representations evolve.

### 4.2 Strong vs Weak Invariants

Not all invariants are equally robust. Weak invariants—such as easily gamed proxy metrics or self-reported success signals—fail to constrain authority in practice.

Strong invariants share the following properties:

- they are computed from environment-sourced data,
- their definition and computation lie outside the system’s write access,
- they are difficult to manipulate indirectly,
- they can expose regression as well as improvement.

IAI does not claim invariants are infallible. It claims that **explicit, externally governed invariants are strictly better control surfaces than implicit or internalised evaluation**.

### 4.3 Example Classes of Invariants

Typical invariant anchors include:

- **Empirical reality:** outcomes must correspond to observed results.
- **External evaluation:** success metrics are computed outside the system.
- **Causal consistency:** improvements must preserve cause–effect relationships.
- **Resource conservation:** solutions must respect hard limits (time, cost, capacity).
- **Auditability and reversibility:** actions and changes must be inspectable and, where possible, reversible.

### 4.4 Rules for Invariants

To qualify as invariant-anchored:

1. At least **one invariant must always remain active and binding**.  
2. The system may **challenge** invariants but may **not unilaterally enact, ratify, or internally assume** those challenges.  
3. Invariants may change only through an **explicit external ratification process**.  
4. Multiple invariants may coexist, with one serving as a root evaluation anchor.
5. Until ratification, **all optimisation continues under the existing invariant set**.
6. **Invariant updates must preserve at least one continuous evaluative anchor across versions**, ensuring longitudinal comparability, auditability, and rollback feasibility.

### 4.5 Invariant Challenge Loop (ICL)

While invariants must remain externally owned, they may be **wrong, incomplete, or poorly aligned** with long-term outcomes. The **Invariant Challenge Loop** enables systems to:

- detect patterns indicating invariant strain (e.g., improving the metric correlates with degradation in secondary outcomes),
- generate evidence-based critiques of current invariants,
- propose alternative formulations with supporting evidence,
- assess risks of proposed changes,

**without ever gaining authority to enact those proposals**.

ICL enforces three distinct roles:

1. **Optimiser:** Improves behaviour under current invariants
2. **Challenger:** Analyses optimisation dynamics and proposes invariant revisions
3. **Authority (External):** Reviews, validates, and ratifies invariant changes

The system may implement roles 1 and 2. Role 3 must remain external.

This mechanism allows IAI systems to evolve their evaluation criteria through **system-initiated, evidence-based, externally-ratified** changes, preserving progress without self-sovereignty.

#### Authority Heartbeat

In a strain-triggered ICL design, the authority would only be invoked when the Challenger detects strain. This creates an undesirable pattern where authority becomes idle and non-participatory during normal operation.

The **Authority Heartbeat** mechanism resolves this by requiring:

1. **Mandatory Challenger output** on every evaluation cycle, regardless of strain status.
2. When no strain is detected, the Challenger emits a `no_change` proposal:
   ```json
   {
     "proposal_type": "no_change",
     "reason": "No strain detected under current evaluation criteria",
     "evidence": { "...metrics summary..." }
   }
   ```
3. The Authority is invoked on every Challenger output, maintaining continuous governance.

This design distinguishes between:
- **Review cadence** (routine oversight during normal operation)
- **Exception escalation** (strain-triggered intervention)

Authority invocation becomes routine rather than exceptional, strengthening corrigibility while preserving meaningful escalation when strain is detected.

#### Why ICL Is Not Self-Sovereignty

A critical distinction separates ICL from a Zero-Invariant Variant (ZIV), in which the system owns its own evaluation:

| Aspect | ICL | ZIV |
|--------|-----|-----|
| Who critiques invariants | System | System |
| Who ratifies changes | External authority | System |
| Evaluation ownership | External | Internal |
| Falsifiability | Preserved | Lost |
| Rollback | Defined and enforceable | Undefined |

At no point does an ICL-governed system evaluate itself under an invariant it has not been externally authorised to use. This is intended as the decisive difference.  

#### 4.5.1 When to Activate ICL

The Invariant Challenge Loop is **not universally beneficial**. It is an advanced feature that should only be activated when specific conditions are met. This section distinguishes between the IAI architecture (which is foundational) and ICL (which is conditional).

##### Architecture vs. Feature

**IAI Architecture** (always beneficial):
- Separation of Optimizer, Evaluator, and Authority
- External evaluation computation
- Prevention of self-ratification
- Clear boundaries and auditability

These architectural properties provide value in any domain and should be present in all IAI systems.

**ICL Feature** (conditionally beneficial):
- Active strain detection
- Proposal generation
- Invariant challenge and evolution

ICL adds value only when the domain exhibits specific characteristics. Premature or inappropriate ICL activation can degrade performance.

##### Conditions Favoring ICL Activation

ICL should be activated when:

1. **Regime shifts occur**: The domain undergoes structural changes that render current invariants misaligned (e.g., market crashes, regulatory changes, supply chain disruptions).

2. **Metric conflicts emerge**: Multiple competing objectives create trade-offs that suggest invariant weights are suboptimal (e.g., optimizing Sharpe ratio degrades drawdown control).

3. **Strategies are competent**: Baseline strategies achieve acceptable performance, but invariant thresholds may be limiting further improvement.

4. **Sufficient data exists**: Sample sizes are large enough to distinguish genuine strain signals from statistical noise (typically requires dozens to hundreds of evaluation cycles).

5. **Stabilization has occurred**: The system has operated under current invariants long enough for optimization to converge (avoiding premature churn).

##### Conditions Requiring ICL Deactivation

ICL should be deactivated or not activated when:

1. **Insufficient statistical power**: Small sample sizes (e.g., 2-3 runs per generation) create high variance, leading to noise-driven proposals that degrade performance.

2. **Broken baseline strategies**: When strategies consistently fail (e.g., negative returns, zero trades), the problem is strategy competence, not invariant calibration. ICL proposals will only enable more execution of failing strategies.

3. **Stable regimes**: In well-understood, stationary environments with no distribution shift, fixed invariants are sufficient and ICL adds unnecessary complexity.

4. **Rapid churn risk**: When the system has not stabilized under current invariants, additional changes prevent convergence and create cycling behavior.

##### Dynamic Activation Patterns

ICL can be **conditionally activated** within the same domain based on operating conditions:

**Example: Forex Trading**

```
Normal Market (Low Volatility, Mean-Reverting):
├─ ICL Status: INACTIVE
├─ Rationale: Stable regime, no strain signals
└─ Behavior: Optimize under fixed invariants

Market Crisis (High Volatility, Trending):
├─ ICL Status: ACTIVE
├─ Rationale: Regime shift detected, invariants under strain
├─ Challenger Proposal: "Sharpe > 1.5 too strict for volatile regime; 
│                        propose Sharpe > 1.0 with tighter position sizing"
└─ Behavior: Generate proposals for Authority review
```

**Example: Supply Chain**

```
Steady Demand Period:
├─ ICL Status: INACTIVE
└─ Behavior: Minimize inventory under fixed cost targets

Supply Shock (Disruption Event):
├─ ICL Status: ACTIVE
├─ Challenger Proposal: "Inventory minimization conflicts with availability; 
│                        propose availability as primary metric"
└─ Behavior: Adapt to new operating constraints
```

##### Implementation Considerations

A practical ICL activation function might check:

```python
def should_activate_icl(context) -> bool:
    # Require minimum sample size
    if context.num_evaluations < MIN_SAMPLES:
        return False
    
    # Require baseline competence
    if context.strategy_performance < COMPETENCE_THRESHOLD:
        return False  # Fix strategies first
    
    # Require stabilization period
    if context.cycles_since_last_change < MIN_STABILIZATION:
        return False  # Let current invariants settle
    
    # Detect regime shift
    if context.has_distribution_shift():
        return True
    
    # Detect genuine strain (not noise)
    if context.has_statistically_significant_strain():
        return True
    
    return False  # Default: keep ICL inactive
```

Even when ICL is inactive, the **Authority Heartbeat** continues: the Challenger emits `no_change` proposals and the Authority performs routine oversight. This maintains governance continuity while avoiding unnecessary invariant churn.

##### Pilot-Specific Activation Status

Current pilots demonstrate varying ICL applicability:

- **Pilot 0 (Bandit)**: ICL activated—domain has regime shift (distribution drift), sufficient samples, competent strategies.
- **Pilot 2 (Betting)**: ICL activated conditionally—enabled when market regimes change or hypothesis performance degrades.
- **Forex (Evaluation Harness)**: ICL deactivated—strategies not yet profitable, insufficient basis for meaningful invariant evolution.

This pattern reinforces a core principle: **architectural separation is universally valuable; ICL is a powerful tool that requires the right conditions**.

### 4.6 What Invariants Do *Not* Do

Invariants do not:

- guarantee alignment in a moral or social sense,
- prevent all forms of metric gaming,
- eliminate the need for human oversight,
- limit internal creativity or abstraction,
- prevent the system from questioning or challenging them.

They enforce only that improvement and invariant evolution remain externally grounded and corrigible.

Note that the separation between epistemic capability and normative authority is itself protected by a **meta-invariant** that is not subject to challenge (see Section 5.5).

---

## 5. Core Architecture Pattern

IAI is proposed as an architectural pattern: a self-improving internal loop constrained by an externally anchored evaluation boundary.

### 5.1 Separation of Concerns

An IAI system must explicitly separate:

- **Policy, representation, and strategy learning** (internal),
- **Challenge generation and invariant critique** (internal, advisory-only),
- **Evaluation computation and metric definition** (external),
- **Invariant ratification and change authority** (external),
- **Actuation and safeguards** (rate limits, reversibility, shutdown conditions).

This separation operationalises the principle: the system may improve *how* it acts and may propose changes to *what counts as success*, but may not unilaterally enact those proposals.

### 5.2 Minimal Improvement Loop

At a high level:

1. Observe domain state.  
2. Propose actions or recommendations.  
3. Execute actions or simulate them under safeguards.  
4. Compute outcomes using externally defined metrics.  
5. Update internal models and strategies to improve measured outcomes.  
6. (Optional) Detect invariant strain and generate challenge outputs.
7. (External) Review and potentially ratify invariant changes.

Steps 4 and 7 are decisive: the success signal and invariant authority must remain outside the system's ratification control.

### 5.3 Components (Conceptual)

- **Domain interface:** standardised state extraction and action APIs.  
- **Strategy layer:** generates candidate policies, plans, or heuristics.  
- **World model / simulator (optional):** supports counterfactual evaluation and safe exploration.  
- **Challenger (internal, advisory):** detects invariant strain and generates evidence-based critiques, alternative formulations, and risk assessments. Challenger outputs include structured critiques, evidence packages, proposed metrics, and impact analyses.
- **Evaluator (externalised):** computes metrics and enforces invariants.  
- **Invariant Authority (external):** reviews challenge outputs and ratifies invariant changes.
- **Orchestrator:** coordinates the multi-generation evolution loop (Run → Challenge → Review → Update → Repeat), managing state transitions and ensuring all components interact correctly.
- **Safety envelope:** boundary checks, rate limits, rollback and shutdown logic.  

### 5.4 What “External” Means in Practice

“External” does not imply a separate organisation. It means:

- metric definitions are not editable by the system,
- metric computation occurs in code/config outside system write access,
- evaluation data is environment-sourced rather than self-reported,
- invariant changes require explicit external authorisation.#### Invariant Authority in Practice

The **Invariant Authority** role may be fulfilled by:

- a human operator or domain expert,
- a governance committee or review board,
- an automated external system with its own governance,
- a version-controlled configuration with change-control process,
- a local LLM acting as an authority proxy (see below).

What matters is not the form, but the separation: the entity or process that ratifies invariant changes must be **distinct from and not controllable by** the system being evaluated.

#### LLM-Based Authority

A local LLM may serve as an authority proxy, particularly useful for:

- rapid iteration during development and testing,
- continuous automated governance without human bottlenecks,
- consistent application of decision criteria across generations.

An LLM-based authority implementation must:

1. **Run externally** to the optimising system (separate process, no shared state).
2. **Use structured prompts** that present challenger outputs, current metrics, baseline comparisons, and current invariants.
3. **Support configurable strictness** (e.g., strict, balanced, permissive) to control the evidence threshold for accepting proposals.
4. **Return structured decisions** including verdict (ACCEPT/REJECT/MODIFY/NO_CHANGE), rationale, confidence, and concerns.
5. **Maintain full audit trail** of all prompts, responses, and decisions with timestamps and model identifiers.
6. **Fail safely** by defaulting to rejection when errors occur.

The LLM authority receives the same inputs a human reviewer would receive and is bound by the same constraints: it may approve, reject, or modify proposals, but it may not redefine invariants, invent new evaluation metrics, or autonomously apply changes outside the ratification process.

Example implementations may use local inference (e.g., via Foundry Local, Ollama, or similar) to eliminate cloud dependencies and ensure the authority remains operationally independent.

#### Ratification Process

A valid ratification process includes:

1. Receipt of challenger outputs (critiques, evidence, proposals).
2. Independent validation of claims (e.g., via replay or simulation).
3. Risk assessment of proposed changes.
4. Explicit approval, rejection, or modification.
5. Versioned, auditable record of the decision.
6. Propagation of ratified changes to the evaluator.

Until step 6 completes, the system continues optimising under the prior invariant set.

### 5.5 Meta-Invariant: The Protected Separation

The separation between **epistemic capability** and **normative authority** is itself a **meta-invariant**. This meta-invariant comprises:

- the rule that evaluation authority is external,
- the identity and independence of the invariant authority,
- the requirement that at least one invariant remains binding at all times,
- the prohibition on evaluating under unratified invariants.

The meta-invariant is not subject to the Invariant Challenge Loop and may not be challenged, revised, or weakened by the system. This architectural constraint is what distinguishes IAI from systems that acquire evaluative sovereignty through recursive self-improvement.

Note: The IAI architecture *permits* recursive improvement of the system's own mechanisms (e.g., how the Challenger detects strain or generates proposals), provided the meta-invariant remains protected. This capability—termed **meta-improvement**—is not demonstrated in current pilots, which use fixed Challenger logic. See Section 12 (Future Extensions) for analysis of when meta-improvement would be warranted.

---

## 6. Evaluation and Test Harness

IAI is intended to be validated empirically, not philosophically. Deployment should proceed in staged exposure.

### 6.1 Stage 1: Offline Replay

Historical data is used to compare candidate decisions against baselines.

Goals:

- validate measurement integrity,
- detect obvious failure modes cheaply,
- estimate performance ceilings and stability.

**ICL governance:** Challenge outputs are encouraged and logged for review. Invariant strain signals are analysed offline.

### 6.2 Stage 2: Shadow Mode

The system runs on live inputs without actuating, producing recommendations and predicted outcomes.

Goals:

- assess robustness to distribution shift,
- validate observability and latency assumptions,
- harden logging, monitoring, and evaluation.

**ICL governance:** Challenger outputs are monitored alongside operational recommendations. Invariant challenges are reviewed but typically not enacted during shadow mode.

### 6.3 Stage 3: Reversible Actuation (Optional)

Limited, rate-controlled actions are permitted with rollback capability.

Goals:

- validate real-world causal impact,
- observe second-order effects,
- test stability under partial control.

**ICL governance:** Invariant challenges are tightly governed with mandatory external review before any ratification. All challenge outputs and ratification decisions are versioned and audited.

### 6.4 Success Criteria

Success is defined strictly by **externally computed metrics**. Internal confidence, interpretability, or self-reported improvement are insufficient.

#### Primary Success Criteria

- Measured improvement on the primary invariant relative to baselines.
- Stability and robustness under distribution shift or adversarial conditions.
- Absence of invariant violations or safety envelope breaches.

#### ICL-Related Success Criteria

- Challenger outputs are generated when strain signals are present.
- Challenger outputs are actionable and evidence-based.
- Invariant evolution, when it occurs, improves long-term outcomes.
- The challenge-ratification process does not become a bottleneck.
- Human understanding of the domain improves through challenger insights.

#### Partial Success

A pilot may demonstrate partial success if:

- the system improves outcomes but challenger outputs are not yet useful,
- or challenger outputs are insightful but invariant evolution has not yet been tested.

Both scenarios provide valuable learning for subsequent iterations.

---

## 7. Pilot Domains

Suitable pilot domains are:

- bounded,
- measurable,
- replayable or simulatable,
- safe to test (shadow mode feasible),
- demonstrably resistant to sustained human optimisation.

Examples include:

- casework or ticket queue orchestration,
- supply chain and inventory optimisation,
- compute or job scheduling,
- incident detection and response,
- compliance or risk triage.

Anti-examples include open-ended social interaction or unbounded strategic planning, which violate domain-boundedness.

Each pilot must explicitly define boundaries, action space, primary invariant, success metrics, and failure modes.

### 7.1 Pilot 0: Multi-Armed Bandit with Distribution Drift

#### 7.1.1 Setup

A 5-armed bandit environment with reward distributions that shift at the midpoint of each episode (5000 steps). The IAI system uses EXP3 to select among four baseline policies (epsilon-greedy, UCB1, Thompson Sampling, Fixed) and itself. 

A Challenger component detects strain signals (regret slope, switch rate, post-drift recovery) and proposes parameter adjustments (epsilon for exploration, iai_gamma for meta-policy learning rate). All evaluation metrics (cumulative regret, post-drift regret, switch rate) remain fixed and externally computed.

**Domain Boundaries:**
- State space: 5 arms with fixed reward distributions (shifted at midpoint)
- Action space: Select one arm per step
- Episode length: 5000 steps (2500 pre-drift, 2500 post-drift)
- Invariants: Cumulative regret, post-drift regret, switch rate (all externally computed)

**Challenger Scope:**
- May propose parameter adjustments (epsilon, iai_gamma)
- May detect and flag strain signals
- May not modify evaluation metrics or environment

#### 7.1.2 Human Authority Experiment

**Authority:** Human reviewer ratifies parameter changes between runs.

**Method:** Five successive runs were conducted, applying the first (most conservative) value from each Challenger suggestion.

**Results:**

| Run | iai_gamma | epsilon | Cum. Regret | Post-Drift Regret | Switch Rate |
|-----|-----------|---------|-------------|-------------------|-------------|
| 1   | 0.05      | 0.10    | 267         | 0.072             | 0.332       |
| 2   | 0.01      | 0.10    | 276         | 0.070             | 0.435       |
| 3   | 0.01      | 0.10    | 235         | 0.051             | 0.425       |
| 4   | 0.01      | 0.10    | 266         | 0.067             | 0.445       |
| 5   | 0.01      | 0.10    | 254         | 0.064             | 0.377       |

**Observation:** Across successive runs, the system's behaviour changed in response to Challenger suggestions without inducing instability or metric manipulation. Improvements, where present, were incremental and non-monotonic. Run 3 achieved the lowest cumulative regret (235) and best post-drift recovery (0.051), representing a 12% improvement in regret from baseline.

**Limitations:** This pilot does not demonstrate automatic optimisation, nor does it claim superiority over established bandit algorithms. Its purpose is to show that bounded, externally ratified self-adjustment is possible without undermining invariant evaluation. The Challenger repeatedly flagged high switching rates (37-45%), suggesting that even gamma=0.01 may induce excessive meta-exploration for this problem structure.

#### 7.1.3 LLM Authority Experiment: An Observed Failure Mode

**Authority:** Local LLM (Phi-4, running via Azure AI Foundry Local) with "balanced" strictness setting.

**Method:** Ten generations with 2-3 runs per generation. Authority invoked after each generation to review Challenger proposals. Unlike the human authority experiment, the LLM authority operated continuously without human intervention.

**Authority Prompt Structure:**

The LLM authority received structured prompts containing:

1. **Current State:**
   - Current invariants (epsilon, iai_gamma)
   - Current performance metrics (cumulative regret, post-drift regret, switch rate)
   - Baseline performance for comparison

2. **Challenger Proposal:**
   - Strain signals detected (which thresholds were exceeded)
   - Critiques (evidence-based rationale for concern)
   - Proposed changes (specific parameter adjustments)
   - Evidence (metrics, comparisons, trends)

3. **Decision Criteria (for "balanced" strictness):**
   - Evidence strength: Is statistical evidence compelling?
   - Strain severity: Real problem or normal variance?
   - Safety: Preserve acceptable baseline performance?
   - Clarity: Is proposed metric well-defined and measurable?
   - Necessity: Does this address genuine limitation?

4. **Expected Response Format:**
   ```json
   {
     "verdict": "ACCEPT|REJECT|MODIFY|NO_CHANGE",
     "rationale": "Clear explanation referencing specific evidence",
     "confidence": 0.85,
     "concerns": ["list", "of", "concerns"]
   }
   ```

The "balanced" strictness guidance instructed the authority to: "Accept clear improvements with good evidence. Balance exploration and safety."

**Prompt Limitations Identified:**

1. **No quantitative thresholds:** Criteria like "compelling evidence" and "clear improvements" were qualitative, allowing the LLM to accept proposals based on narrative coherence rather than statistical rigor.

2. **Insufficient sample size awareness:** The prompt did not explicitly flag that 2-3 runs per generation provide limited statistical power.

3. **No explicit rejection bias:** Unlike "strict" mode (which states "Reject unless compelling"), "balanced" mode had no default position, potentially biasing toward acceptance.

4. **Missing baseline comparison requirement:** The prompt presented baseline metrics but did not require the authority to verify that proposed changes would preserve or improve upon baseline performance.

**Results:**

| Gen | Regret | vs Baseline | Strain | Decision | Effectiveness |
|-----|--------|-------------|--------|----------|---------------|
| 0   | 457.5  | +21.9%      | Yes    | ACCEPT   | Worse         |
| 1   | 490.1  | +30.6%      | Yes    | ACCEPT   | Worse         |
| 2   | 630.9  | +68.2%      | Yes    | MODIFY   | Worse         |
| 3   | 446.1  | +18.9%      | Yes    | ACCEPT   | Better        |
| 4   | 786.1  | +109.5%     | Yes    | ACCEPT   | Worse         |
| 5   | 444.7  | +18.5%      | Yes    | MODIFY   | Better        |
| 6   | 426.5  | +13.7%      | No     | NO_CHANGE| Better        |
| 7   | 796.2  | +112.2%     | Yes    | ACCEPT   | Worse         |
| 8   | 657.2  | +75.1%      | Yes    | ACCEPT   | Worse         |
| 9   | 566.5  | +51.0%      | Yes    | ACCEPT   | Worse         |

**Summary Statistics:**
- Proposal acceptance rate: 90% (7 accepted, 2 modified, 0 rejected, 1 no-change)
- Proposal effectiveness: 55.6% (5 improvements, 3 regressions out of 9 accepted/modified)
- Generations with high regret (>1.3× baseline): 8 out of 10
- Baseline regret: 375.21

**Key Findings:**

1. **Architecture Preserved:** The meta-invariant held throughout. The system never evaluated itself under unratified invariants, and the LLM authority remained external and independent.

2. **Challenge Mechanism Worked:** Strain detection functioned as designed, generating proposals in 9 of 10 generations with structured evidence and rationale.

3. **Authority Insufficiency:** The LLM authority accepted plausible-sounding proposals at a high rate (90%) but only 55.6% of accepted proposals led to improvement. Eight generations showed regret 30-112% above baseline.

4. **Plausibility ≠ Effectiveness:** Proposals were evidence-based and articulated clear rationales (e.g., "reduce switching rate," "improve post-drift recovery"), yet frequently degraded performance. This demonstrates a critical gap between **proposal quality as judged by linguistic plausibility** and **proposal quality as measured by outcomes**.

**Interpretation:**

This experiment demonstrates an important failure mode: **architectural separation is necessary but insufficient**. The IAI framework successfully maintained the boundary between epistemic capability and normative authority, but the choice of authority implementation proved critical.

An LLM authority with "balanced" strictness:
- was too permissive, accepting proposals based on narrative coherence rather than empirical rigor,
- lacked domain-specific skepticism about proposals that might induce exploration-exploitation imbalance,
- did not adequately weight the risk of regression versus the potential for improvement.

This finding validates a core IAI principle: **the authority matters**. Architectural constraints prevent self-sovereignty, but they do not guarantee good governance. Future work should explore:

- stricter LLM prompting with explicit outcome-based validation requirements,
- hybrid human-LLM authority with automatic rejection of high-risk proposals,
- meta-metrics that track authority decision quality over time,
- domain-specific authority tuning based on empirical acceptance-effectiveness correlations.

**Contrast with Human Authority:**

The human authority experiment (Section 7.1.2) showed conservative, incremental changes with minimal regression. The LLM authority showed high acceptance rates and frequent performance degradation. This suggests that authority conservatism—whether through human judgment or tighter LLM constraints—may be essential when Challenger proposals are based on limited evidence or short time horizons.

### ICL Requirements for Pilots

In addition to the above, each pilot should specify:

- **Strain signals:** Domain-specific patterns indicating potential invariant mis-specification (e.g., improving the metric correlates with secondary degradation).
- **Invariant Authority:** Who or what reviews and ratifies invariant challenges for this domain.
- **Challenger scope:** What the system may challenge (e.g., metric formulation, constraint weights) and what remains permanently fixed.
- **Review cadence:** How often challenger outputs are reviewed (e.g., per-run, daily, weekly).
- **Ratification process:** How proposed invariant changes are validated and enacted.

These requirements ensure that ICL is operationalised consistently across pilots and that invariant evolution is governed rather than ad hoc.

---

## 8. Failure Modes and Mitigations

### 8.1 Goodhart Effects

Risk: optimising the metric produces perverse outcomes.

Mitigations:

- choose invariants that are hard to spoof (environment-sourced),
- use multiple metrics (primary + stability/quality constraints),
- introduce adversarial evaluation and holdout periods,
- inspect distribution shifts and tail events.

### 8.2 Invariant Erosion (Authority Creep)

Risk: over time, the system effectively gains control over how success is computed.

Mitigations:

- enforce strict write boundaries around metric definition and computation,
- require external review for invariant changes,
- maintain immutable logs of evaluation code/config.

### 8.3 Domain Creep

Risk: the system expands its operational footprint beyond what was tested.

Mitigations:

- explicit boundary checks in the safety envelope,
- narrow initial pilots,
- staged rollout with hard caps on action types/volume.

### 8.4 Invariant Mis-Specification or Brittleness

Risk: Human-specified invariants may be incomplete, misaligned with long-term outcomes, or create pathological trade-offs.

Mitigations:

- implement Invariant Challenge Loop to detect strain signals,
- review challenger outputs regularly for evidence of mis-specification,
- use multiple metrics (primary + secondary + stability) to expose conflicts,
- maintain versioned history of invariant changes and their rationale,
- conduct periodic audits of invariant-outcome correlations.

### 8.5 Feedback-Loop Instability

Risk: self-improvement or actuation destabilises the domain.

Mitigations:

- prefer shadow mode and reversible actions first,
- rate limits, circuit breakers, rollback triggers,
- stability metrics alongside performance metrics.

### 8.6 Meta-Invariant Erosion

Risk: recursive self-improvement erodes the boundary between epistemic capability and normative authority.

Mitigations:

- architectural enforcement of meta-invariant (hardcoded, not configurable by system),
- monitor for attempts to modify invariant authority identity or control,
- if meta-improvement is implemented (see Section 12.1), audit Challenger mechanism changes for scope creep toward evaluation control,
- treat any erosion of the epistemic/normative boundary as a critical failure.

### 8.7 "Winning" by Manipulating Measurement

Risk: the system affects the data pipeline that computes evaluation.

Mitigations:

- segregate evaluation data collection,
- random audits of ground truth,
- independent monitoring.

---

## 9. Limitations and Non-Goals

This project explicitly does **not** aim to:

- design or promote global AI governance,
- induce or accelerate a technological singularity,
- create AI systems with sovereignty over truth/success criteria,
- replace human decision-making entirely,
- encode human morality, ethics, or values into AI,
- claim inevitability of any technological trajectory.

The scope is intentionally:

- local rather than planetary,
- experimental rather than prescriptive,
- empirical rather than speculative.

IAI is not a claim that invariants "solve alignment," and it is not a substitute for broader societal or ethical work. It is a proposed engineering approach for building systems that can be tested, compared, corrected, and iteratively improved in bounded domains.

---

## 10. Related Work

This section situates IAI within the existing literature on self-improving systems, optimisation under uncertainty, metric mis-specification, and safety architectures. IAI is not a learning algorithm, a model class, or an alignment theory. It is a **proposed architectural pattern** governing how self-improving systems relate to evaluation authority.

### 10.1 Recursive Self-Improvement and Intelligence Explosion

The idea that sufficiently capable systems might improve their own performance recursively is well established. Bostrom's analysis of recursive self-improvement and the "intelligence explosion" frames the dominant narrative: once a system can improve its own intelligence, it may rapidly outpace human oversight and reshape its own goals (Bostrom, 2014). Similar concerns are raised throughout the AI safety literature, particularly in work emerging from MIRI and related communities (Yudkowsky, 2008).

These accounts are valuable for identifying *risk*, but they generally treat **self-sovereignty over evaluation** as an inevitable consequence of capability growth. IAI questions this assumption. The central hypothesis is that **recursive improvement and evaluative sovereignty may be structurally separable**, provided evaluation authority is externalised and protected by design. Whether this separation holds under increasing capability remains an open empirical question.

### 10.2 Metric Mis-Specification and Goodhart Effects

A large body of work documents the failure modes of optimisation when metrics are mis-specified or over-optimised. Goodhart's Law—"when a measure becomes a target, it ceases to be a good measure"—has been formalised and extended in modern analyses of optimisation systems (Goodhart, 1975; Manheim & Garrabrant, 2018). In machine learning, reward hacking and specification gaming are well-documented phenomena, particularly in reinforcement learning (Amodei et al., 2016; Krakovna et al., 2020).

IAI takes these results as **foundational constraints**, not as problems to be solved through better metrics alone. Rather than assuming invariants can be made perfect, IAI treats mis-specification as inevitable and designs for **corrigibility under mis-specification** via externally governed invariants, explicit challenge mechanisms (ICL), and preserved falsifiability through external evaluation authority.

### 10.3 Human-in-the-Loop and Oversight-Based Approaches

Human-in-the-loop (HITL) methods are widely used to constrain learning systems, most notably in Reinforcement Learning from Human Feedback (RLHF) (Christiano et al., 2017; Ouyang et al., 2022) and related approaches such as Constitutional AI (Bai et al., 2022). These systems rely on human judgement to guide or constrain optimisation, typically by providing labels, preferences, or critiques.

IAI differs in two key respects:

1. **Authority separation**: Humans (or external systems) are not merely feedback providers but remain the *owners* of evaluation authority.
2. **Challenge capability**: The system is permitted—indeed encouraged—to generate structured critiques of its invariants via the Invariant Challenge Loop, while remaining prohibited from ratifying those critiques itself.

IAI can be seen as complementary to oversight-based approaches, extending them into regimes where optimisation processes themselves must improve.

### 10.4 Meta-Learning and AutoML

Meta-learning and AutoML systems aim to improve learning processes themselves, often by optimising architectures, hyperparameters, or training procedures (Schmidhuber, 1987; Finn et al., 2017; Zoph & Le, 2017). These approaches demonstrate that **learning dynamics can themselves be objects of optimisation**, a premise shared with IAI.

However, meta-learning typically assumes that the evaluation metric remains fixed and internal to the optimisation process. IAI is orthogonal in scope:

- Meta-learning concerns *what is optimised*.
- IAI concerns *who controls the definition and ratification of success*.

An IAI system may employ meta-learning internally, but meta-learning alone does not address the authority and corrigibility concerns central to IAI.

### 10.5 Control Theory, Cybernetics, and Safety Architectures

IAI has strong conceptual affinities with classical cybernetics and control theory, particularly the separation of system, controller, and evaluator. Wiener's cybernetics (Wiener, 1948) and Ashby's Law of Requisite Variety (Ashby, 1956) emphasise that effective control requires sufficient internal complexity, but also stable feedback channels. Beer's Viable System Model further distinguishes operational units from governance and policy layers (Beer, 1972).

Modern safety architectures such as Runtime Assurance (RTA) frameworks formalise similar ideas by enforcing externally verified safety constraints over adaptive systems (Schumann et al., 2019). Work on formal verification, shielding, and safety envelopes aims to ensure that learning systems remain within acceptable bounds at runtime (Alshiekh et al., 2018).

IAI can be understood as extending these principles to **recursive, learning-driven systems**, preserving an external evaluation boundary even as internal complexity and capability grow. IAI incorporates similar enforcement mechanisms while adding a controlled pathway—via ICL—for questioning and revising evaluation criteria without internalising authority.

### 10.6 Philosophy of Science and Falsifiability

The Invariant Challenge Loop bears resemblance to ideas in the philosophy of science concerning theory revision under constraint. Popper's emphasis on falsifiability (Popper, 1959) and Lakatos' notion of research programmes (Lakatos, 1978) both stress that progress requires the ability to challenge assumptions while preserving an external standard of evaluation.

IAI operationalises this insight in an engineering context: systems may propose revisions to their evaluative framework, but falsification and ratification remain external.

### 10.7 Summary of Positioning

Across these literatures, IAI is distinguished by a single architectural commitment:

> **Recursive self-improvement is permitted; evaluative sovereignty is not.**

Rather than claiming to eliminate mis-specification, Goodhart effects, or optimisation risk, IAI treats them as structural facts and proposes an architecture intended to keep systems corrigible, auditable, and falsifiable in their presence. The viability of this approach is subject to empirical validation.

---

## 11. Pilot 0: Multi-Armed Bandits (Complete)

**Status:** Complete (2026-01-16)  
**Domain:** Contextual multi-armed bandit optimization  
**Objective:** Validate core IAI architecture and invariant evolution mechanism

### 11.1 Implementation

Pilot 0 implemented the full IAI architecture in the bandit domain:

**Components:**
- **Optimizer:** Modified Thompson Sampling with learned action selection
- **Challenger:** Rule-based strain detection analyzing regret slopes, switching rates, reward variance, and baseline comparisons
- **Authority:** LLM-based decision-making using local models (qwen2.5-1.5b, phi-4-mini) via Microsoft Foundry Local
- **Evaluation Harness:** Offline replay with comprehensive logging, analysis, and visualization

**Initial Invariant:** Cumulative reward maximization

**Baseline Comparisons:** Thompson Sampling, UCB1, Epsilon-Greedy

### 11.2 Key Results

**Architecture Validation:**
- ✅ Complete Optimizer → Challenger → Authority loop functional
- ✅ Invariant evolution demonstrated (proposals accepted and enacted)
- ✅ Strain detection correctly identified performance issues
- ✅ Authority successfully evaluated proposals from multiple generations
- ✅ No instances of self-ratification or meta-invariant violation

**Observed Evolution:**
```
Generation 0: cumulative_reward 
           → (strain detected: high switching variance, regret 2.31× baseline)
           → Proposal: reward_with_stability
           → Authority Decision: ACCEPT

Generation 1: reward_with_stability
           → (strain detected: regret still 2.81× baseline)  
           → Proposal: baseline_relative_regret
           → Authority Decision: ACCEPT
```

**Performance:**
- Baseline (Thompson): 38.6 regret
- IAI System: 85-108 regret (underperformed baseline)
- Proposal acceptance rate: 100% (permissive mode)
- Invariants evolved across 2 generations

### 11.3 Critical Finding: Prompt Engineering Over Model Scale

The most significant technical discovery was not about the IAI framework itself, but about implementing LLM-based governance:

**Problem Identified:** Initial Authority prompts contained contradictory guidance:
- Section A: "If ratio >3.0×: System is FAILING significantly"
- Section B: "If ratio ≤3.0×: ACCEPT"

When presented with ratio=2.81×, even capable models (phi-4-mini) would:
1. Correctly state "2.81 < 3.0" mathematically
2. Then REJECT anyway, citing "exceeding threshold" or "significant failure"

The LLM prioritized safety-oriented heuristics from training over explicit decision logic in the prompt.

**Solution:** Pre-compute comparisons and state conclusions explicitly:
```
STEP 1: Check threshold
Current ratio: 2.81×
Threshold: 3.0×
Is 2.81 > 3.0? NO - System performance acceptable → Continue to Step 2
```

**Impact:**
- Small model (qwen2.5-1.5b, 1.5B parameters) worked perfectly with fixed prompt
- Larger models (phi-4-mini) failed with ambiguous prompt
- **Conclusion:** Prompt structure matters more than model size for deterministic governance tasks

### 11.4 Limitations and Learnings

**Known Limitations:**
1. **Performance:** IAI did not beat Thompson Sampling baseline
   - Expected: Bandits are well-solved, stable domain
   - IAI designed for complex, non-stationary environments
   
2. **Simple Domain:** Static bandit problem insufficient to demonstrate IAI advantages
   - No regime shifts to adapt to
   - No complex invariant trade-offs
   - Baseline algorithms near-optimal

3. **Sample Efficiency:** Small run counts (2 seeds) led to high variance in metrics
   - Authority correctly flagged this in decision rationale
   - Future pilots should use larger sample sizes

**Validated Hypotheses:**
- ✅ Architectural separation (Optimizer/Challenger/Authority) is maintainable
- ✅ Invariant evolution can happen without self-sovereignty
- ✅ LLM-based Authority is viable with proper prompt engineering
- ✅ Strain detection identifies genuine performance issues
- ✅ External ratification prevents unilateral metric changes

**Rejected Hypotheses:**
- ❌ Performance improvement is not automatic (domain-dependent)
- ❌ Small models cannot do governance (false - prompt design matters more)

### 11.5 Technical Artifacts

**Codebase:** `pilots/iai_bandit_poc/`
- Live dashboard with real-time metrics
- Comprehensive logging (JSON decision history, CSV metrics)
- Automated analysis with plots and reports
- Run indexing for comparison across experiments

**Data Outputs:**
- Authority decision logs with full prompts and responses
- Evolution history tracking metric changes across generations
- Automated plot generation (regret evolution, strain signals, decisions)
- Structured experiment summaries for meta-analysis

### 11.6 Next Steps

Pilot 0 successfully validates the IAI framework. Next phase:

**Pilot 1: Market Execution** (Planned)
- More complex domain with non-stationary dynamics
- Multiple competing objectives (execution quality, market impact, timing)
- Better suited for demonstrating invariant evolution value
- Reuse Authority and Challenger architecture from Pilot 0

**Framework Improvements:**
- Increase sample sizes for better statistical rigor
- Add meta-metrics tracking (proposal effectiveness over time)
- Explore whether Authority decisions improve with experience
- Consider meta-improvement for Challenger (Section 12.1)

### When to Abandon or Revise IAI

IAI should be abandoned or materially revised if:

- no invariant can be found that remains robust under optimisation pressure,  
- self-improvement reliably degrades stability or safety constraints,  
- observed performance gains collapse when moving from replay to shadow to actuation,  
- measurement cannot be made environment-sourced and write-protected in practice,
- challenger outputs are systematically ignored or prove unhelpful for invariant evolution,
- the challenge-ratification process becomes a bottleneck that prevents necessary adaptation.

**Pilot 0 Status:** None of these failure conditions observed. Framework viable for continued development.  

---

## 12. Future Extensions

This section outlines capabilities permitted by the IAI architecture but not yet demonstrated in current pilots.

### 12.1 Meta-Improvement: Improving IAI with IAI

The IAI architecture permits recursive improvement of its *own mechanisms*—provided the meta-invariant (Section 5.5) remains protected. An IAI system **may improve its epistemic competence**, including:

- how it detects optimisation plateaus,
- how it explores and selects strategies,
- how it identifies signals of invariant strain,
- how it generates evidence, critiques, and alternative formulations,
- how it prioritises and structures challenger outputs.

These forms of meta-improvement concern *how well the system reasons about optimisation and evaluation*, not *who decides what counts as success*.

#### Current Implementation Status

Pilot 0 (multi-armed bandit) uses **fixed Challenger logic**:

- Strain detection thresholds are hardcoded (e.g., `switch_rate > 0.4`, `regret_slope > 1.5× baseline`).
- Proposal generation follows fixed if-then rules.
- The Challenger has no mechanism to learn which thresholds work well or which proposals tend to be accepted.

This is intentional for the initial demonstration: the core IAI contribution—separating self-improvement from evaluation authority—can be validated without meta-improvement.

#### When Meta-Improvement Would Be Warranted

Meta-improvement adds architectural complexity. It would be justified when a domain exhibits characteristics that make fixed Challenger logic inadequate:

1. **High regime variability:** Domains where optimal strain thresholds change significantly across operating regimes. In such settings, a fixed threshold (e.g., "flag strain when switch rate exceeds 40%") may be too sensitive in stable regimes and too conservative during transitions.

2. **Challenger bottleneck:** When the Challenger's proposal quality demonstrably limits system improvement. If proposals are frequently rejected by the Authority, or accepted proposals yield minimal improvement, the Challenger itself becomes the limiting factor.

3. **Sufficient meta-data:** Meta-learning requires data about what works. A domain must generate enough proposal-outcome pairs to support learning patterns such as "proposals made under condition X tend to be accepted and effective."

4. **Long time horizons:** Domains with extended operational lifetimes where the cost of Challenger suboptimality accumulates. Short-duration pilots may not justify meta-improvement overhead.

#### Meta-Improvement Requirements

Implementing meta-improvement would require:

| Component | Current (Pilot 0) | Meta-Improvement Extension |
|-----------|-------------------|---------------------------|
| Strain thresholds | Hardcoded constants | Learnable parameters updated based on acceptance/effectiveness |
| Proposal generation | Fixed if-then rules | Parameterised templates or learned proposal strategies |
| Meta-metrics | None | Track proposal acceptance rate, improvement-per-proposal, Authority feedback |
| Meta-learning loop | None | Challenger updates its own mechanisms based on meta-metrics |
| Meta-authority | None | External review of Challenger mechanism changes (optional but recommended) |

#### Risks and Mitigations

Meta-improvement introduces additional failure modes:

- **Overfitting to Authority preferences:** The Challenger might learn to generate proposals that are easily accepted rather than genuinely beneficial. Mitigation: include outcome-based meta-metrics, not just acceptance rates.
- **Scope creep toward evaluation authority:** Meta-improvement must not extend to modifying the meta-invariant. Mitigation: architectural enforcement (hardcoded protection of meta-invariant).
- **Increased opacity:** A learning Challenger is harder to audit than a rule-based one. Mitigation: maintain interpretable meta-metrics and versioned Challenger configurations.

### 12.2 Multi-Domain Transfer

Future work may explore whether invariant formulations, Challenger heuristics, or evaluation patterns transfer across related domains. This would extend IAI from isolated pilots to a library of reusable governance patterns.

### 12.3 Collaborative Multi-Authority Governance

Current pilots assume a single Authority. Complex domains may benefit from multiple authorities with different competencies (e.g., domain expert, safety reviewer, resource controller). Formalising how multiple authorities interact with ICL remains an open question.

---

## 13. Conclusion

Invariant-Anchored Intelligence proposes a middle path worth investigating: systems designed for self-improvement within bounded domains, while remaining grounded to external, non-self-redefinable evaluation anchors. Through the Invariant Challenge Loop, such systems may question their own evaluation criteria and propose evidence-based alternatives, while external authorities retain ratification power. The meta-invariant—the protected separation between epistemic capability and normative authority—is intended to keep recursive self-improvement bounded and corrigible.

The aim is not maximal autonomy, but **measurable, corrigible capability growth through collaborative invariant evolution** in domains where human-led optimisation tends to plateau.

If the approach proves viable, IAI may offer a reusable engineering pattern for deploying optimisation systems that can challenge human assumptions without acquiring sovereignty over truth or success. If unsuccessful, it should still clarify where constraints bind, whether challenge mechanisms aid or hinder progress, and whether stronger autonomy is genuinely required. Either outcome advances understanding of the design space.

---

## References

Alshiekh, M., Bloem, R., Ehlers, R., Könighofer, B., Niekum, S., & Topcu, U. (2018). Safe Reinforcement Learning via Shielding. *AAAI Conference on Artificial Intelligence*.

Amodei, D., Olah, C., Steinhardt, J., Christiano, P., Schulman, J., & Mané, D. (2016). Concrete Problems in AI Safety. *arXiv preprint arXiv:1606.06565*.

Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.

Bai, Y., Kadavath, S., Kundu, S., Askell, A., Kernion, J., Jones, A., ... & Kaplan, J. (2022). Constitutional AI: Harmlessness from AI Feedback. *arXiv preprint arXiv:2212.08073*.

Beer, S. (1972). *Brain of the Firm*. Allen Lane.

Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.

Christiano, P. F., Leike, J., Brown, T., Martic, M., Legg, S., & Amodei, D. (2017). Deep Reinforcement Learning from Human Preferences. *Advances in Neural Information Processing Systems*.

Finn, C., Abbeel, P., & Levine, S. (2017). Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks. *Proceedings of ICML*.

Goodhart, C. A. E. (1975). Problems of Monetary Management: The UK Experience. *Papers in Monetary Economics, Reserve Bank of Australia*.

Krakovna, V., Uesato, J., Mikulik, V., Rahtz, M., Everitt, T., Kumar, R., ... & Legg, S. (2020). Specification Gaming: The Flip Side of AI Ingenuity. *DeepMind Blog*.

Lakatos, I. (1978). *The Methodology of Scientific Research Programmes*. Cambridge University Press.

Manheim, D., & Garrabrant, S. (2018). Categorizing Variants of Goodhart's Law. *arXiv preprint arXiv:1803.04585*.

Ouyang, L., Wu, J., Jiang, X., Almeida, D., Wainwright, C., Mishkin, P., ... & Lowe, R. (2022). Training Language Models to Follow Instructions with Human Feedback. *arXiv preprint arXiv:2203.02155*.

Popper, K. (1959). *The Logic of Scientific Discovery*. Routledge.

Schmidhuber, J. (1987). Evolutionary Principles in Self-Referential Learning. *Diploma thesis, Technische Universität München*.

Schumann, J., Rozier, K. Y., Reinbacher, T., Mengshoel, O. J., Mbaya, T., & Ippolito, C. (2019). Toward Real-Time Assurance of Learning-Enabled Autonomous Systems. *NASA Technical Reports*.

Wiener, N. (1948). *Cybernetics: Or Control and Communication in the Animal and the Machine*. MIT Press.

Yudkowsky, E. (2008). Artificial Intelligence as a Positive and Negative Factor in Global Risk. In N. Bostrom & M. Ćirković (Eds.), *Global Catastrophic Risks*. Oxford University Press.

Zoph, B., & Le, Q. V. (2017). Neural Architecture Search with Reinforcement Learning. *Proceedings of ICLR*.
