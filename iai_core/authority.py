"""Authority component for IAI.

The Authority reviews Challenger proposals and decides whether to accept,
reject, or modify changes to evaluation invariants.

This module provides:
- BaseAuthority: Abstract interface for all Authority implementations
- FoundryLocalAuthority: LLM-based Authority using Foundry Local
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import re

from .types import (
    Proposal,
    AuthorityDecision,
    Invariants,
    Verdict,
)


def convert_numpy_types(obj: Any) -> Any:
    """Convert NumPy types to JSON-serializable Python types."""
    try:
        import numpy as np
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


class BaseAuthority(ABC):
    """
    Abstract base class for IAI Authority.
    
    The Authority is the external decision-maker that reviews proposals
    from the Challenger and decides whether to accept invariant changes.
    
    Key responsibilities:
    - Review Challenger proposals with full context
    - Make ACCEPT/REJECT/MODIFY decisions
    - Provide rationale for auditability
    - Maintain decision history
    """
    
    def __init__(self, strictness: str = "balanced"):
        """
        Initialize Authority.
        
        Args:
            strictness: Decision-making style
                - "strict": High evidence bar, reject by default
                - "balanced": Accept improvements with good evidence
                - "permissive": Exploratory, lower evidence bar
        """
        self.strictness = strictness
        self.decision_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    def review_proposal(
        self,
        proposal: Proposal,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        current_invariants: Invariants,
        generation: int,
        evolution_history: Optional[List[Dict[str, Any]]] = None,
    ) -> AuthorityDecision:
        """
        Review a Challenger proposal.
        
        Args:
            proposal: Output from Challenger.analyse()
            current_metrics: Current system performance metrics
            baseline_metrics: Baseline performance for comparison
            current_invariants: Current invariant configuration
            generation: Current generation number
            evolution_history: List of past generation summaries
            
        Returns:
            AuthorityDecision with verdict, rationale, and confidence
        """
        pass
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Return full decision history for audit."""
        return self.decision_history


class FoundryLocalAuthority(BaseAuthority):
    """
    LLM-based Authority using Microsoft Foundry Local.
    
    Reviews Challenger proposals using a local LLM that runs on-device.
    No cloud dependencies, no API keys required.
    """
    
    def __init__(
        self,
        model_alias: str = "phi-3.5-mini",
        strictness: str = "balanced",
        domain_context: str = "",
    ):
        """
        Initialize Foundry Local Authority.
        
        Args:
            model_alias: Foundry Local model alias
            strictness: Decision-making style
            domain_context: Domain-specific context for prompts
        """
        super().__init__(strictness)
        
        print(f"\n{'='*60}")
        print(f"Initializing Foundry Local Authority")
        print(f"{'='*60}")
        print(f"Model: {model_alias}")
        print(f"Strictness: {strictness}")
        
        # Lazy import to avoid dependency if not using this Authority
        import openai
        from foundry_local import FoundryLocalManager
        
        self.manager = FoundryLocalManager(model_alias)
        self.client = openai.OpenAI(
            base_url=self.manager.endpoint,
            api_key=self.manager.api_key,
        )
        self.model_id = self.manager.get_model_info(model_alias).id
        self.domain_context = domain_context
        
        print(f"✓ Authority ready")
        print(f"  Endpoint: {self.manager.endpoint}")
        print(f"  Model ID: {self.model_id}")
        print(f"{'='*60}\n")
    
    def review_proposal(
        self,
        proposal: Proposal,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        current_invariants: Invariants,
        generation: int,
        evolution_history: Optional[List[Dict[str, Any]]] = None,
    ) -> AuthorityDecision:
        """Review proposal using local LLM."""
        
        prompt = self._construct_prompt(
            proposal,
            current_metrics,
            baseline_metrics,
            current_invariants,
            generation,
            evolution_history or [],
        )
        
        print(f"\n{'─'*60}")
        print(f"Authority Review - Generation {generation}")
        print(f"{'─'*60}")
        
        response = self._call_llm(prompt)
        decision = self._parse_decision(response)
        
        # Log for auditability
        self.decision_history.append({
            "generation": generation,
            "prompt": prompt,
            "llm_response": response,
            "decision": decision.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_id,
        })
        
        return decision
    
    def _construct_prompt(
        self,
        proposal: Proposal,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        current_invariants: Invariants,
        generation: int,
        evolution_history: List[Dict[str, Any]],
    ) -> str:
        """Construct prompt for LLM review."""
        
        strictness_guidance = {
            "strict": (
                "You are CONSERVATIVE. Reject proposals unless evidence is overwhelming. "
                "Default to REJECT. Only accept if metrics show >20% improvement."
            ),
            "balanced": (
                "You are BALANCED. Accept proposals with solid evidence of improvement. "
                "Consider both potential gains and risks."
            ),
            "permissive": (
                "You are EXPLORATORY. Accept proposals that show promise, even with "
                "moderate evidence. Favor learning over stability."
            ),
        }
        
        proposal_dict = convert_numpy_types(proposal.to_dict())
        current_metrics = convert_numpy_types(current_metrics)
        baseline_metrics = convert_numpy_types(baseline_metrics)
        
        prompt = f"""You are an IAI Authority reviewing a proposal to modify system invariants.

{self.domain_context}

{strictness_guidance.get(self.strictness, strictness_guidance['balanced'])}

## Current State
- Generation: {generation}
- Current Invariants: {json.dumps(current_invariants.to_dict(), indent=2)}
- Current Metrics: {json.dumps(current_metrics, indent=2)}
- Baseline Metrics: {json.dumps(baseline_metrics, indent=2)}

## Challenger Proposal
{json.dumps(proposal_dict, indent=2)}

## Evolution History (last 5 generations)
{json.dumps(evolution_history[-5:], indent=2) if evolution_history else "No prior history"}

## Your Task
Decide: ACCEPT, REJECT, or MODIFY this proposal.

Respond in this exact JSON format:
{{
    "verdict": "ACCEPT" | "REJECT" | "MODIFY",
    "rationale": "Brief explanation of your decision",
    "confidence": 0.0-1.0,
    "concerns": ["list", "of", "concerns"],
    "modified_proposal": null or {{ modified proposal if MODIFY }}
}}
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call local LLM and return response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM call failed: {e}")
            return '{"verdict": "REJECT", "rationale": "LLM call failed", "confidence": 0.0, "concerns": ["LLM error"]}'
    
    def _parse_decision(self, response: str) -> AuthorityDecision:
        """Parse LLM response into AuthorityDecision."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            verdict = Verdict(data.get("verdict", "REJECT"))
            
            return AuthorityDecision(
                verdict=verdict,
                rationale=data.get("rationale", ""),
                confidence=float(data.get("confidence", 0.5)),
                concerns=data.get("concerns", []),
                modified_proposal=data.get("modified_proposal"),
                model_used=self.model_id,
            )
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return AuthorityDecision(
                verdict=Verdict.REJECT,
                rationale=f"Failed to parse response: {e}",
                confidence=0.0,
                concerns=["Parse error"],
                model_used=self.model_id,
            )
