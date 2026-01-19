"""
IAI Orchestrator - Runs the Complete Challenge Loop
===================================================
Coordinates Challenger, Evaluator, and Authority to implement
the full Invariant-Anchored Intelligence pattern.
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from .hypotheses import BettingHypothesis
from .challenger import HypothesisChallenger
from .evaluator import BettingEvaluator, EvaluationResult
from .authority import IAIAuthority, AuthorityDecision


class IAIOrchestrator:
    """
    Orchestrates the complete IAI loop:
    1. Challenger proposes alternatives
    2. Evaluator tests them empirically
    3. Authority reviews and accepts/rejects
    4. Repeat
    """
    
    def __init__(self, invariant_edge: float = 2.0, min_bets: int = 30):
        """
        Args:
            invariant_edge: Minimum edge required (%)
            min_bets: Minimum bets required for Authority decision
        """
        self.challenger = HypothesisChallenger()
        self.evaluator = BettingEvaluator(invariant_edge=invariant_edge)
        self.authority = IAIAuthority(invariant_edge=invariant_edge, min_bets=min_bets)
        
        self.evaluation_results: List[EvaluationResult] = []
        self.authority_decisions: List[AuthorityDecision] = []
    
    def run_evaluation_cycle(self, matches_df: pd.DataFrame, 
                            initial_bankroll: float = 1000) -> Dict[str, Any]:
        """
        Run one complete evaluation cycle:
        - Evaluate all proposed hypotheses
        - Authority reviews results
        - Update hypothesis statuses
        
        Args:
            matches_df: Historical match data for testing
            initial_bankroll: Starting bankroll for simulations
        
        Returns:
            Summary of cycle results
        """
        cycle_start = datetime.utcnow().isoformat()
        
        # Get all hypotheses that need evaluation
        to_evaluate = self.challenger.get_proposed_hypotheses()
        
        results = []
        decisions = []
        
        for hypothesis in to_evaluate:
            # Challenger proposes
            hypothesis.status = "EVALUATING"
            
            # Evaluator tests
            evaluation = self.evaluator.evaluate(hypothesis, matches_df, initial_bankroll)
            self.evaluation_results.append(evaluation)
            hypothesis.evaluation_result = evaluation.__dict__
            
            # Authority reviews
            decision = self.authority.review(hypothesis, evaluation)
            self.authority_decisions.append(decision)
            
            results.append({
                "hypothesis": hypothesis.name,
                "edge": evaluation.edge,
                "ci": f"[{evaluation.edge_ci_lower:.2f}%, {evaluation.edge_ci_upper:.2f}%]",
                "bets": evaluation.total_bets,
                "decision": decision.decision
            })
            
            decisions.append(decision)
        
        return {
            "cycle_timestamp": cycle_start,
            "hypotheses_evaluated": len(to_evaluate),
            "results": results,
            "decisions": decisions,
            "summary": {
                "accepted": sum(1 for d in decisions if d.decision == "ACCEPT"),
                "rejected": sum(1 for d in decisions if d.decision == "REJECT"),
                "deferred": sum(1 for d in decisions if d.decision == "DEFER")
            }
        }
    
    def get_deployment_ready_hypotheses(self) -> List[BettingHypothesis]:
        """Get hypotheses that Authority has accepted for deployment."""
        return self.challenger.get_accepted_hypotheses()
    
    def generate_full_report(self) -> Dict[str, Any]:
        """Generate comprehensive report of IAI system state."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "challenger": self.challenger.generate_challenge_report(),
            "authority": self.authority.generate_report(),
            "evaluations_completed": len(self.evaluation_results),
            "decisions_made": len(self.authority_decisions),
            "deployment_ready": len(self.get_deployment_ready_hypotheses())
        }
