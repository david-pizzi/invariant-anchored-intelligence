"""
Challenger - Proposes Alternative Strategies
============================================
The Challenger's job is to continuously propose alternatives
and generate evidence about their potential performance.
"""

from typing import List
from .hypotheses import BettingHypothesis, ALL_HYPOTHESES


class HypothesisChallenger:
    """
    Proposes alternative betting strategies for evaluation.
    
    The Challenger does NOT make decisions - it only proposes.
    The Evaluator tests, and the Authority decides.
    """
    
    def __init__(self, hypotheses: List[BettingHypothesis] = None):
        """
        Args:
            hypotheses: List of hypotheses to manage. Defaults to ALL_HYPOTHESES.
        """
        self.hypotheses = hypotheses or ALL_HYPOTHESES.copy()
    
    def get_proposed_hypotheses(self) -> List[BettingHypothesis]:
        """Get all hypotheses with status PROPOSED."""
        return [h for h in self.hypotheses if h.status == "PROPOSED"]
    
    def get_evaluating_hypotheses(self) -> List[BettingHypothesis]:
        """Get all hypotheses currently being evaluated."""
        return [h for h in self.hypotheses if h.status == "EVALUATING"]
    
    def get_accepted_hypotheses(self) -> List[BettingHypothesis]:
        """Get all hypotheses that passed Authority review."""
        return [h for h in self.hypotheses if h.status == "ACCEPTED"]
    
    def get_rejected_hypotheses(self) -> List[BettingHypothesis]:
        """Get all hypotheses that failed Authority review."""
        return [h for h in self.hypotheses if h.status == "REJECTED"]
    
    def get_deployed_hypotheses(self) -> List[BettingHypothesis]:
        """Get all hypotheses currently deployed in production."""
        return [h for h in self.hypotheses if h.status == "DEPLOYED"]
    
    def propose_next_for_evaluation(self) -> BettingHypothesis:
        """
        Propose the next hypothesis for evaluation.
        
        Strategy: Prioritize hypotheses with highest expected edge
        that haven't been evaluated yet.
        
        Returns:
            Next hypothesis to evaluate, or None if all evaluated
        """
        proposed = self.get_proposed_hypotheses()
        
        if not proposed:
            return None
        
        # Sort by expected edge (highest first)
        proposed.sort(key=lambda h: h.expected_edge, reverse=True)
        
        # Return highest expected edge
        next_hyp = proposed[0]
        next_hyp.status = "EVALUATING"
        
        return next_hyp
    
    def generate_challenge_report(self) -> dict:
        """Generate a report on current hypothesis status."""
        return {
            "total_hypotheses": len(self.hypotheses),
            "proposed": len(self.get_proposed_hypotheses()),
            "evaluating": len(self.get_evaluating_hypotheses()),
            "accepted": len(self.get_accepted_hypotheses()),
            "rejected": len(self.get_rejected_hypotheses()),
            "deployed": len(self.get_deployed_hypotheses()),
            "hypotheses": [
                {
                    "id": h.id,
                    "name": h.name,
                    "status": h.status,
                    "expected_edge": h.expected_edge,
                    "selection": h.selection,
                    "odds_range": f"{h.odds_min}-{h.odds_max}"
                }
                for h in self.hypotheses
            ]
        }
