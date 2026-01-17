"""IAI Betting Pilot - UK Football Betting Optimization.

This pilot tests IAI on sports betting with focus on:
- Bet sizing optimization (not prediction)
- Bankroll management
- Market selection

Domain-specific components extend the iai_core base classes.
"""

from .data import FootballDataLoader, Match, BettingOdds
from .strategies import (
    BaseStrategy,
    FlatBettingStrategy,
    KellyStrategy,
    FractionalKellyStrategy,
    IAIStrategy,
)
from .evaluator import BettingEvaluator
from .challenger import BettingChallenger
from .orchestrator import BettingOrchestrator
from .simulator import BettingSimulator

__all__ = [
    # Data
    "FootballDataLoader",
    "Match",
    "BettingOdds",
    # Strategies
    "BaseStrategy",
    "FlatBettingStrategy",
    "KellyStrategy",
    "FractionalKellyStrategy",
    "IAIStrategy",
    # IAI Components
    "BettingEvaluator",
    "BettingChallenger",
    "BettingOrchestrator",
    "BettingSimulator",
]
