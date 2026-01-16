"""LLM-based Authority using Foundry Local for IAI system.

The Authority reviews Challenger proposals and decides whether to accept,
reject, or modify changes to evaluation invariants.

Uses local LLM via Foundry Local - no cloud dependencies, no API keys.
"""

import openai
from foundry_local import FoundryLocalManager
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np


def convert_types(obj: Any) -> Any:
    """Convert NumPy and Python special types to JSON-serializable types."""
    # Handle NumPy bool before Python bool check
    if isinstance(obj, np.bool_):
        return bool(obj)
    
    # Handle Python bool
    if isinstance(obj, bool):
        return obj
    
    # Handle NumPy types
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Handle dicts and lists recursively
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_types(item) for item in obj]
    
    return obj


class FoundryLocalAuthority:
    """
    LLM-based Authority using Microsoft Foundry Local.
    
    Reviews Challenger proposals and makes decisions about invariant changes
    using a local LLM that runs on-device without cloud dependencies.
    """
    
    def __init__(self, model_alias: str = "qwen2.5-1.5b", strictness: str = "balanced"):
        """
        Initialize Foundry Local Authority.
        
        Args:
            model_alias: Foundry Local model alias. Options:
                - "qwen2.5-0.5b" (500MB, fast but LIMITED reasoning - use with strict mode)
                - "phi-3.5-mini" (~3GB, better reasoning - RECOMMENDED but may not load)
                - Other models may be available depending on Foundry Local version
            strictness: Decision-making style
                - "strict": RECOMMENDED for weak models - high evidence bar, reject by default
                - "balanced": Moderate - accept improvements with good evidence
                - "permissive": Exploratory - may be too permissive with weak models
        
        IMPORTANT: qwen2.5-0.5b has limited reasoning capacity.
        Use "strict" mode and rely on quantitative thresholds in prompts.
        Upgrade to larger model if governance quality is insufficient.
        """
        print(f"\n{'='*60}")
        print(f"Initializing Foundry Local Authority")
        print(f"{'='*60}")
        print(f"Model: {model_alias}")
        print(f"Strictness: {strictness}")
        
        # Initialize Foundry Local Manager
        # This will auto-start service and load model
        self.manager = FoundryLocalManager(model_alias)
        
        # Create OpenAI-compatible client pointing to local endpoint
        self.client = openai.OpenAI(
            base_url=self.manager.endpoint,
            api_key=self.manager.api_key
        )
        
        self.model_id = self.manager.get_model_info(model_alias).id
        self.strictness = strictness
        self.decision_history: List[Dict[str, Any]] = []
        
        print(f"✓ Authority ready")
        print(f"  Endpoint: {self.manager.endpoint}")
        print(f"  Model ID: {self.model_id}")
        print(f"{'='*60}\n")
    
    def review_proposal(
        self, 
        challenger_output: Dict[str, Any],
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        current_invariants: Dict[str, Any],
        generation: int,
        evolution_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Review a Challenger proposal using the local LLM.
        
        Args:
            challenger_output: Output from Challenger.analyse()
            current_metrics: Current system performance metrics
            baseline_metrics: Baseline performance for comparison
            current_invariants: Current invariant configuration
            generation: Current generation number
            evolution_history: List of past generation summaries for context
            
        Returns:
            Decision dict with:
                - verdict: "ACCEPT" | "REJECT" | "MODIFY"
                - rationale: Detailed explanation
                - confidence: 0.0-1.0
                - concerns: List of issues identified
                - modified_proposal: (optional) If verdict is MODIFY
        """
        prompt = self._construct_prompt(
            challenger_output, current_metrics, baseline_metrics,
            current_invariants, generation, evolution_history or []
        )
        
        print(f"\n{'─'*60}")
        print(f"Authority Review - Generation {generation}")
        print(f"{'─'*60}")
        
        # Call local LLM
        response = self._call_local_llm(prompt)
        decision = self._parse_decision(response)
        
        # Log for auditability
        self.decision_history.append({
            'generation': generation,
            'prompt': prompt,
            'llm_response': response,
            'decision': decision,
            'timestamp': datetime.now().isoformat(),
            'model_used': self.model_id
        })
        
        return decision
    
    def _construct_prompt(
        self,
        challenger_output: Dict[str, Any],
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        current_invariants: Dict[str, Any],
        generation: int,
        evolution_history: List[Dict[str, Any]]
    ) -> str:
        """Construct the review prompt for the LLM."""
        
        # Convert all data to JSON-serializable types
        challenger_output = convert_types(challenger_output)
        current_metrics = convert_types(current_metrics)
        baseline_metrics = convert_types(baseline_metrics)
        current_invariants = convert_types(current_invariants)
        evolution_history = convert_types(evolution_history)
        
        # Check if any strain was detected
        has_strain = bool(challenger_output.get('proposed_metrics'))
        
        # Dynamic thresholds based on strictness (MUST be defined BEFORE strictness_guidance)
        failure_thresholds = {
            "strict": 1.3,      # Conservative: flag as failing at 1.3× baseline
            "balanced": 1.5,    # Moderate: allow some underperformance  
            "permissive": 3.0   # Exploratory: only flag catastrophic failures (>3× baseline)
        }
        failure_threshold = failure_thresholds[self.strictness]
        
        # Calculate current ratio for the guidance examples
        current_ratio = current_metrics.get('avg_regret', 0) / baseline_metrics.get('avg_regret', 1)
        
        strictness_guidance = {
            "strict": "REJECT unless: (1) Evidence from ≥5 runs, (2) Improvement >20% vs baseline, (3) Statistical significance clear, (4) No safety degradation.",
            "balanced": "ACCEPT only if: (1) Current performance ≤1.2× baseline OR (2) Proposed change has strong evidence (effect size >0.5) AND (3) Safety preserved (no switching rate increase >10%). Default to REJECT when uncertain.",
            "permissive": f"""EXPLORATORY MODE - Goal: observe IAI evolution, not beat baseline.

**STEP 1: Check catastrophic failure threshold**
Current ratio: {current_ratio:.2f}×
Catastrophic threshold: {failure_threshold}×

Is {current_ratio:.2f} > {failure_threshold}? 
{"YES - System is catastrophically broken → REJECT" if current_ratio > failure_threshold else "NO - System performance acceptable → Continue to Step 2"}

**STEP 2: Check proposal quality** (only if Step 1 = NO)
- Is the proposal well-defined? (has clear name, description, formula)
- Does it have a clear rationale?

If YES to both → ACCEPT (enable evolution)
If NO → REJECT (proposal unclear)

**YOUR SITUATION:**
- Current ratio {current_ratio:.2f}× is {"ABOVE" if current_ratio > failure_threshold else "BELOW"} threshold {failure_threshold}×
- Performance is {"CATASTROPHIC - you must REJECT" if current_ratio > failure_threshold else "ACCEPTABLE - check proposal quality and likely ACCEPT"}"""
        }
        
        if not has_strain:
            # NO STRAIN DETECTED - Authority Heartbeat / Routine Governance
            return f"""You are the Authority in an Invariant-Anchored Intelligence system.
This is a ROUTINE GOVERNANCE REVIEW (Authority Heartbeat).

## CURRENT STATE (Generation {generation})

**Current Invariants:**
{json.dumps(current_invariants, indent=2)}

**Current Performance:**
{json.dumps(current_metrics, indent=2)}

**Baseline Performance:**
{json.dumps(baseline_metrics, indent=2)}

## CHALLENGER REPORT

**Status:** NO STRAIN DETECTED

**Evidence:**
{json.dumps(challenger_output.get('evidence', {}), indent=2)}

**Strain Signals:** All within acceptable bounds
{json.dumps(challenger_output.get('strain_signals', {}), indent=2)}

## YOUR TASK

Provide routine governance oversight. Since no strain was detected:
- Confirm system is operating within acceptable parameters
- Note any observations about performance trends
- Maintain audit trail of governance

**Strictness Mode**: {self.strictness}

## RESPONSE FORMAT

Respond with ONLY valid JSON (no markdown, no extra text):

{{
  "verdict": "NO_CHANGE",
  "rationale": "System operating normally. No intervention required. [Add any observations about performance trends]",
  "confidence": 0.95,
  "concerns": []
}}

This is routine oversight, not exceptional intervention.
"""
        
        # STRAIN DETECTED - Review proposed changes
        return f"""You are the Authority in an Invariant-Anchored Intelligence system.
Review proposed changes to evaluation metrics from the Challenger component.

## CURRENT STATE (Generation {generation})

**Current Invariants:**
{json.dumps(current_invariants, indent=2)}

**Current Performance:**
{json.dumps(current_metrics, indent=2)}

**Baseline Performance:**
{json.dumps(baseline_metrics, indent=2)}

## EVOLUTION HISTORY

{self._format_evolution_history(evolution_history)}

## CHALLENGER PROPOSAL

**Strain Signals Detected:**
{json.dumps(challenger_output.get('strain_signals', {}), indent=2)}

**Critiques:**
{json.dumps(challenger_output.get('critiques', []), indent=2)}

**Proposed Changes:**
{json.dumps(challenger_output.get('proposed_metrics', []), indent=2)}

**Evidence:**
{json.dumps(challenger_output.get('evidence', {}), indent=2)}

## YOUR TASK

Decide: ACCEPT, REJECT, or MODIFY this proposal.

**Current Performance Metrics:**
- Current regret: {current_metrics.get('avg_regret', 0):.1f}
- Baseline regret: {baseline_metrics.get('avg_regret', 375.2):.1f}
- Ratio: {current_metrics.get('avg_regret', 0) / baseline_metrics.get('avg_regret', 375.2):.2f}× baseline

**Strictness Mode**: {self.strictness}

**DECISION RULES** (follow these in order):

{strictness_guidance[self.strictness]}

**Additional Checks** (only after applying decision logic above):
- Proposal must be well-defined, measurable, and externally computable
- Must NOT increase switching rate by >10% or decrease reward by >5%
- Should address genuine strain signals, not just noise

## RESPONSE FORMAT

Respond with ONLY valid JSON (no markdown, no extra text):

{{
  "verdict": "ACCEPT",
  "rationale": "Clear explanation referencing specific evidence",
  "confidence": 0.85,
  "concerns": ["list", "of", "concerns"]
}}

If verdict is MODIFY, add: "modified_proposal": {{"name": "...", "description": "..."}}

Focus on evidence quality and safety.
"""
    
    def _call_local_llm(self, prompt: str) -> str:
        """Call the local Foundry LLM."""
        try:
            print("⏳ Consulting LLM Authority...")
            # Build system prompt with IAI context
            system_prompt = f"""You are the external Authority in an Invariant-Anchored Intelligence (IAI) system.

YOUR CRITICAL ROLE:
- You are the ONLY mechanism preventing the system from gaining self-sovereignty over evaluation
- The system CANNOT change its own success criteria without your explicit approval
- If you accept bad proposals, the system degrades and architectural separation becomes meaningless
- Your decisions determine whether the system remains corrigible or drifts toward self-sovereignty

YOUR RESPONSIBILITY:
- Protect the meta-invariant: the system must NEVER evaluate itself under unratified invariants
- Ensure proposed changes are evidence-based, statistically sound, and preserve baseline performance
- Be skeptical of proposals based on limited evidence (few runs, short time horizons)
- Default to REJECTION when evidence is weak or safety is unclear

DOMAIN CONTEXT: Multi-Armed Bandit with Distribution Drift
- Baseline performance: 375 cumulative regret (Thompson Sampling)
- Any proposal >1.3× baseline indicates fundamental failure, not "exploration"
- Excessive policy switching (>0.4) indicates over-exploration and instability
- With only 2-3 runs per generation, statistical power is LIMITED - require strong effect sizes
- Proposals must preserve or improve upon baseline to be acceptable

STRICTNESS MODE: {self.strictness}
- strict: Reject unless compelling statistical evidence with large sample sizes
- balanced: Accept only when evidence clearly shows improvement AND safety is preserved
- permissive: Accept reasonable proposals with adequate evidence and clear rationale

Respond ONLY with valid JSON. No markdown formatting."""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temp for more consistent governance
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"✗ ERROR calling local LLM: {e}")
            # Fallback to safe rejection
            return json.dumps({
                "verdict": "REJECT",
                "rationale": f"LLM error: {str(e)}. Defaulting to rejection for safety.",
                "confidence": 0.0,
                "concerns": ["LLM_ERROR"]
            })
    
    def _parse_decision(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured decision."""
        try:
            # Clean up response - remove markdown if present
            response_clean = llm_response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            decision = json.loads(response_clean.strip())
            
            # Validate required fields
            assert 'verdict' in decision, "Missing 'verdict' field"
            assert decision['verdict'] in ['ACCEPT', 'REJECT', 'MODIFY', 'NO_CHANGE'], "Invalid verdict"
            assert 'rationale' in decision, "Missing 'rationale' field"
            
            # Set defaults for optional fields
            decision.setdefault('confidence', 0.5)
            decision.setdefault('concerns', [])
            decision.setdefault('modified_proposal', None)
            
            return decision
            
        except Exception as e:
            print(f"⚠ WARNING: Failed to parse LLM response: {e}")
            print(f"Raw response: {llm_response[:200]}...")
            # Return safe fallback
            return {
                'verdict': 'REJECT',
                'rationale': f'Failed to parse LLM response: {str(e)}',
                'confidence': 0.0,
                'concerns': ['PARSE_ERROR']
            }
    
    def save_decision_history(self, output_dir: str):
        """Save all decisions to JSON for auditability."""
        from pathlib import Path
        filepath = Path(output_dir) / 'authority_decisions.json'
        with open(filepath, 'w') as f:
            json.dump(self.decision_history, f, indent=2)
        print(f"✓ Decision history saved to {filepath}")
    
    def _format_evolution_history(self, history: List[Dict[str, Any]]) -> str:
        """Format evolution history for prompt inclusion."""
        if not history:
            return "**First Generation** - No previous history available."
        
        # Show last 5 generations
        recent = history[-5:]
        
        lines = ["**Recent Performance Trajectory:**\n"]
        for h in recent:
            metrics = h.get('metrics', {})
            regret = metrics.get('avg_regret', 0)
            reward = metrics.get('avg_reward', 0)
            decision = h.get('decision', 'UNKNOWN')
            rationale = h.get('rationale', '')[:80]
            
            lines.append(
                f"Gen {h['generation']}: "
                f"Regret={regret:.1f}, Reward={reward:.1f} → {decision} "
                f"({rationale}...)"
            )
        
        # Pattern analysis
        decisions = [h.get('decision') for h in recent]
        accept_count = decisions.count('ACCEPT')
        reject_count = decisions.count('REJECT')
        
        lines.append(f"\n**Decision Pattern (last {len(recent)} gens):** "
                    f"{accept_count} Accept, {reject_count} Reject")
        
        # Performance trend
        if len(recent) >= 2:
            first_regret = recent[0].get('metrics', {}).get('avg_regret', 0)
            last_regret = recent[-1].get('metrics', {}).get('avg_regret', 0)
            if last_regret > first_regret * 1.1:
                trend = "⚠️ DEGRADING"
            elif last_regret < first_regret * 0.9:
                trend = "✓ IMPROVING"
            else:
                trend = "→ STABLE"
            lines.append(f"**Trend:** {trend} ({first_regret:.1f} → {last_regret:.1f} regret)")
        
        return "\n".join(lines)

