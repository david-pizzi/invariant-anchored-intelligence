"""
Betting Hypotheses - Alternative Strategies for Testing
=======================================================
Each hypothesis represents a different betting approach to test.
"""

from dataclasses import dataclass
from typing import List, Literal


@dataclass
class BettingHypothesis:
    """A testable betting hypothesis."""
    
    id: str
    name: str
    description: str
    
    # Strategy parameters
    selection: Literal["H", "D", "A"]  # Home, Draw, Away
    odds_min: float
    odds_max: float
    stake_pct: float  # % of bankroll
    
    # Expected performance (from prior analysis)
    expected_edge: float  # Expected edge %
    expected_win_rate: float  # Expected win rate %
    
    # Lifecycle status
    status: Literal["PROPOSED", "EVALUATING", "ACCEPTED", "REJECTED", "DEPLOYED"] = "PROPOSED"
    
    # Evidence from evaluation
    evaluation_result: dict = None
    authority_decision: dict = None
    
    def qualifies(self, home_team: str, away_team: str, home_odds: float, 
                  draw_odds: float, away_odds: float) -> tuple[bool, float]:
        """Check if a match qualifies for this hypothesis and return odds."""
        if self.selection == "H":
            odds = home_odds
        elif self.selection == "D":
            odds = draw_odds
        else:  # "A"
            odds = away_odds
        
        qualifies = self.odds_min <= odds <= self.odds_max
        return qualifies, odds


# ============================================================================
# HYPOTHESIS DEFINITIONS
# ============================================================================

BASELINE_HOME_UNDERDOGS = BettingHypothesis(
    id="H1",
    name="Baseline: Home Underdogs",
    description="Original strategy - Home win @ 4.0-6.0 odds",
    selection="H",
    odds_min=4.0,
    odds_max=6.0,
    stake_pct=3.0,
    expected_edge=5.18,  # Validated from historical data
    expected_win_rate=24.0,
    status="DEPLOYED"  # Currently active
)

EXPANSION_HOME_MODERATE = BettingHypothesis(
    id="H2",
    name="Expansion: Home Moderate",
    description="Test slightly lower odds - Home win @ 3.0-4.0 odds",
    selection="H",
    odds_min=3.0,
    odds_max=4.0,
    stake_pct=3.0,
    expected_edge=-0.24,  # From prior research - likely to FAIL
    expected_win_rate=28.0,
    status="PROPOSED"
)

HOME_EXTREME_UNDERDOGS = BettingHypothesis(
    id="H3",
    name="Home Extreme Underdogs",
    description="Test higher odds - Home win @ 6.0-10.0 odds",
    selection="H",
    odds_min=6.0,
    odds_max=10.0,
    stake_pct=2.0,  # Lower stake due to higher risk
    expected_edge=2.5,  # Uncertain - needs testing
    expected_win_rate=15.0,
    status="PROPOSED"
)

AWAY_VALUE_BET = BettingHypothesis(
    id="H4",
    name="Away Value Bet",
    description="Test away teams at value odds - Away win @ 3.0-4.0 odds",
    selection="A",
    odds_min=3.0,
    odds_max=4.0,
    stake_pct=3.0,
    expected_edge=-0.67,  # From prior research - likely to FAIL
    expected_win_rate=30.0,
    status="PROPOSED"
)

DRAW_VALUE_BET = BettingHypothesis(
    id="H5",
    name="Draw Value Bet",
    description="Test draws at premium odds - Draw @ 3.5+ odds",
    selection="D",
    odds_min=3.5,
    odds_max=5.0,
    stake_pct=2.5,
    expected_edge=-1.2,  # From prior research - likely to FAIL
    expected_win_rate=25.0,
    status="PROPOSED"
)

HOME_FAVORITES = BettingHypothesis(
    id="H6",
    name="Home Favorites",
    description="Test home favorites - Home win @ 1.5-2.5 odds",
    selection="H",
    odds_min=1.5,
    odds_max=2.5,
    stake_pct=5.0,  # Higher stake, lower risk
    expected_edge=-2.5,  # Bookmaker juice - likely to FAIL
    expected_win_rate=55.0,
    status="PROPOSED"
)

AWAY_EXTREME_UNDERDOGS = BettingHypothesis(
    id="H7",
    name="Away Extreme Underdogs",
    description="Test away extreme underdogs - Away win @ 6.0-10.0 odds",
    selection="A",
    odds_min=6.0,
    odds_max=10.0,
    stake_pct=2.0,
    expected_edge=1.0,  # Uncertain
    expected_win_rate=12.0,
    status="PROPOSED"
)

HOME_SLIGHT_UNDERDOGS = BettingHypothesis(
    id="H8",
    name="Home Slight Underdogs",
    description="Test borderline cases - Home win @ 2.5-3.0 odds",
    selection="H",
    odds_min=2.5,
    odds_max=3.0,
    stake_pct=4.0,
    expected_edge=-1.0,  # Likely negative
    expected_win_rate=38.0,
    status="PROPOSED"
)


# All hypotheses for testing
ALL_HYPOTHESES = [
    BASELINE_HOME_UNDERDOGS,
    EXPANSION_HOME_MODERATE,
    HOME_EXTREME_UNDERDOGS,
    AWAY_VALUE_BET,
    DRAW_VALUE_BET,
    HOME_FAVORITES,
    AWAY_EXTREME_UNDERDOGS,
    HOME_SLIGHT_UNDERDOGS,
]
