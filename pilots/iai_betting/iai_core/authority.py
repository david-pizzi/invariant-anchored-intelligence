"""
IAI Authority - Reviews and Approves/Rejects Hypotheses
=======================================================
The Authority NEVER makes decisions unilaterally.
It reviews evidence from the Evaluator and applies the invariant.
"""

from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .hypotheses import BettingHypothesis
from .evaluator import EvaluationResult


@dataclass
class AuthorityDecision:
    """A decision made by the Authority."""
    timestamp: str
    hypothesis_id: str
    hypothesis_name: str
    
    # Decision
    decision: str  # ACCEPT, REJECT, DEFER
    reasoning: List[str]
    
    # Evidence considered
    edge: float
    edge_ci_lower: float
    edge_ci_upper: float
    is_significant: bool
    is_stable: bool
    total_bets: int
    
    # Invariant check
    passes_invariant: bool
    invariant_threshold: float


class IAIAuthority:
    """
    The IAI Authority reviews hypothesis evaluations and makes decisions.
    
    Core principles:
    - Never acts unilaterally
    - Always requires evidence from Evaluator
    - Applies invariant consistently
    - Provides clear reasoning for all decisions
    """
    
    def __init__(self, invariant_edge: float = 2.0, min_bets: int = 30):
        """
        Args:
            invariant_edge: Minimum edge required (%)
            min_bets: Minimum number of bets required for decision
        """
        self.invariant_edge = invariant_edge
        self.min_bets = min_bets
        self.decisions: List[AuthorityDecision] = []
    
    def review(self, hypothesis: BettingHypothesis, 
               evaluation: EvaluationResult) -> AuthorityDecision:
        """
        Review an evaluated hypothesis and make a decision.
        
        Args:
            hypothesis: The hypothesis being reviewed
            evaluation: Results from Evaluator
        
        Returns:
            AuthorityDecision with reasoning
        """
        timestamp = datetime.utcnow().isoformat()
        reasoning = []
        
        # Check 1: Sufficient data
        if evaluation.total_bets < self.min_bets:
            decision = "DEFER"
            reasoning.append(f"Insufficient data: {evaluation.total_bets} bets < {self.min_bets} required")
            reasoning.append("Decision: Continue collecting data")
        else:
            # Check 2: Invariant - Edge > threshold with 95% confidence
            if not evaluation.passes_invariant:
                decision = "REJECT"
                reasoning.append(f"FAILS INVARIANT: Edge CI [{evaluation.edge_ci_lower:.2f}%, {evaluation.edge_ci_upper:.2f}%]")
                reasoning.append(f"Required: Lower bound > {self.invariant_edge}% with 95% confidence")
                
                if evaluation.edge < 0:
                    reasoning.append(f"Strategy has NEGATIVE edge ({evaluation.edge:.2f}%)")
                elif evaluation.edge < self.invariant_edge:
                    reasoning.append(f"Edge ({evaluation.edge:.2f}%) below threshold ({self.invariant_edge}%)")
                else:
                    reasoning.append("Confidence interval too wide - insufficient evidence")
            
            # Check 3: Statistical significance
            elif not evaluation.is_significant:
                decision = "REJECT"
                reasoning.append(f"NOT statistically significant (p={evaluation.p_value:.4f})")
                reasoning.append("Cannot distinguish from random chance")
            
            # Check 4: Stability across seasons
            elif not evaluation.is_stable:
                decision = "REJECT"
                reasoning.append(f"UNSTABLE across seasons (std={evaluation.edge_std:.2f}%)")
                reasoning.append("Performance varies too much - unreliable")
            
            # All checks passed
            else:
                decision = "ACCEPT"
                reasoning.append(f"✓ PASSES INVARIANT: Edge = {evaluation.edge:.2f}% (CI: [{evaluation.edge_ci_lower:.2f}%, {evaluation.edge_ci_upper:.2f}%])")
                reasoning.append(f"✓ Statistically significant (p={evaluation.p_value:.4f})")
                reasoning.append(f"✓ Stable across seasons (std={evaluation.edge_std:.2f}%)")
                reasoning.append(f"✓ Win rate: {evaluation.win_rate:.1f}% on {evaluation.total_bets} bets")
                reasoning.append(f"Decision: APPROVE for deployment")
        
        # Create decision record
        decision_record = AuthorityDecision(
            timestamp=timestamp,
            hypothesis_id=hypothesis.id,
            hypothesis_name=hypothesis.name,
            decision=decision,
            reasoning=reasoning,
            edge=evaluation.edge,
            edge_ci_lower=evaluation.edge_ci_lower,
            edge_ci_upper=evaluation.edge_ci_upper,
            is_significant=evaluation.is_significant,
            is_stable=evaluation.is_stable,
            total_bets=evaluation.total_bets,
            passes_invariant=evaluation.passes_invariant,
            invariant_threshold=self.invariant_edge
        )
        
        # Record decision
        self.decisions.append(decision_record)
        
        # Update hypothesis with decision
        hypothesis.authority_decision = asdict(decision_record)
        if decision == "ACCEPT":
            hypothesis.status = "ACCEPTED"
        elif decision == "REJECT":
            hypothesis.status = "REJECTED"
        else:
            hypothesis.status = "EVALUATING"
        
        return decision_record
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a summary report of all decisions."""
        if not self.decisions:
            return {
                "total_decisions": 0,
                "accepted": 0,
                "rejected": 0,
                "deferred": 0,
                "decisions": []
            }
        
        accepted = sum(1 for d in self.decisions if d.decision == "ACCEPT")
        rejected = sum(1 for d in self.decisions if d.decision == "REJECT")
        deferred = sum(1 for d in self.decisions if d.decision == "DEFER")
        
        return {
            "total_decisions": len(self.decisions),
            "accepted": accepted,
            "rejected": rejected,
            "deferred": deferred,
            "acceptance_rate": f"{(accepted / len(self.decisions) * 100):.1f}%" if self.decisions else "0%",
            "decisions": [asdict(d) for d in self.decisions]
        }
