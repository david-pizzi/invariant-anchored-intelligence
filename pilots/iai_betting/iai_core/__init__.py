"""
IAI Core - Full Invariant-Anchored Intelligence Implementation
===============================================================
Implements the complete IAI pattern:
- Challenger: Proposes alternative strategies
- Evaluator: Tests hypotheses empirically
- Authority: Reviews and accepts/rejects based on invariant
"""

from .hypotheses import (
    BettingHypothesis,
    BASELINE_HOME_UNDERDOGS,
    EXPANSION_HOME_MODERATE,
    HOME_EXTREME_UNDERDOGS,
    AWAY_VALUE_BET,
    DRAW_VALUE_BET,
    ALL_HYPOTHESES
)
from .evaluator import BettingEvaluator
from .authority import IAIAuthority
from .challenger import HypothesisChallenger
from .orchestrator import IAIOrchestrator

__all__ = [
    'BettingHypothesis',
    'BettingEvaluator',
    'IAIAuthority',
    'HypothesisChallenger',
    'IAIOrchestrator',
    'ALL_HYPOTHESES',
]
