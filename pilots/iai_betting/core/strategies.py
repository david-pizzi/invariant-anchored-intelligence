"""Betting strategies for IAI pilot.

Provides baseline strategies and IAI-enhanced strategy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import math
import random

from .data import Match, BettingOdds


@dataclass
class Bet:
    """A single bet."""
    match: Match
    selection: str  # "H", "D", "A"
    odds: float
    stake: float
    
    # Computed after settlement
    won: Optional[bool] = None
    profit: Optional[float] = None
    
    def settle(self):
        """Settle the bet based on match result."""
        self.won = self.match.result == self.selection
        if self.won:
            self.profit = self.stake * (self.odds - 1)
        else:
            self.profit = -self.stake


@dataclass
class BettingState:
    """Current state of the betting system."""
    bankroll: float
    initial_bankroll: float
    bets: List[Bet] = field(default_factory=list)
    
    @property
    def total_profit(self) -> float:
        return sum(b.profit for b in self.bets if b.profit is not None)
    
    @property
    def roi(self) -> float:
        """Return on investment."""
        total_staked = sum(b.stake for b in self.bets)
        if total_staked == 0:
            return 0.0
        return self.total_profit / total_staked
    
    @property
    def win_rate(self) -> float:
        settled = [b for b in self.bets if b.won is not None]
        if not settled:
            return 0.0
        return sum(1 for b in settled if b.won) / len(settled)
    
    @property
    def max_drawdown(self) -> float:
        """Maximum peak-to-trough drawdown."""
        if not self.bets:
            return 0.0
        
        cumulative = self.initial_bankroll
        peak = cumulative
        max_dd = 0.0
        
        for bet in self.bets:
            if bet.profit is not None:
                cumulative += bet.profit
                peak = max(peak, cumulative)
                dd = (peak - cumulative) / peak if peak > 0 else 0
                max_dd = max(max_dd, dd)
        
        return max_dd


class BaseStrategy(ABC):
    """
    Abstract base class for betting strategies.
    
    Strategies decide:
    1. Which matches to bet on (selection)
    2. What outcome to bet on (H/D/A)
    3. How much to stake (sizing)
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """
        Decide whether and how to bet on a match.
        
        Args:
            match: The match to consider
            state: Current betting state
            
        Returns:
            Bet if placing one, None if passing
        """
        pass
    
    def estimate_edge(
        self,
        match: Match,
        selection: str,
    ) -> float:
        """
        Estimate edge for a selection.
        
        Uses the trained HistoricalEdgeModel if available,
        otherwise falls back to fair odds comparison.
        
        Returns:
            Estimated edge (positive = value bet)
        """
        # Try to use trained edge model
        model = get_edge_model()
        if model.trained:
            return model.estimate_edge(match, selection)
        
        # Fallback: fair odds comparison
        fair = match.odds.fair_odds()
        
        if selection == "H":
            fair_prob = 1 / fair.home_odds
            offered_prob = 1 / match.odds.home_odds
        elif selection == "D":
            fair_prob = 1 / fair.draw_odds
            offered_prob = 1 / match.odds.draw_odds
        else:
            fair_prob = 1 / fair.away_odds
            offered_prob = 1 / match.odds.away_odds
        
        # Edge = true probability - implied probability
        return fair_prob - offered_prob
    
    def get_odds_for_selection(self, match: Match, selection: str) -> float:
        """Get odds for a selection."""
        if selection == "H":
            return match.odds.home_odds
        elif selection == "D":
            return match.odds.draw_odds
        else:
            return match.odds.away_odds


class HistoricalEdgeModel:
    """
    Edge model based on historical statistics.
    
    Compares odds-implied probability to historical base rates,
    with adjustments for odds ranges (favorites vs underdogs behave differently).
    """
    
    def __init__(self):
        # Historical Premier League base rates (will be updated from training data)
        self.base_rates = {
            "H": 0.46,  # Home win ~46%
            "D": 0.26,  # Draw ~26%
            "A": 0.28,  # Away win ~28%
        }
        
        # Odds-range calibration: how often does each odds range actually win?
        # Format: (min_odds, max_odds) -> actual_win_rate
        self.odds_calibration = {
            "H": {},  # Will be populated from training data
            "D": {},
            "A": {},
        }
        
        # Track training stats
        self.trained = False
    
    def train(self, matches: List[Match]):
        """
        Train edge model on historical matches.
        
        Calculates:
        1. Overall base rates for H/D/A
        2. Odds-range calibration (what's the actual win rate for 2.0-2.5 odds, etc.)
        """
        if not matches:
            return
        
        # Calculate base rates
        results = {"H": 0, "D": 0, "A": 0}
        for m in matches:
            results[m.result] += 1
        
        total = len(matches)
        self.base_rates = {k: v / total for k, v in results.items()}
        
        # Odds-range calibration
        # Group matches by odds ranges and calculate actual win rates
        odds_ranges = [(1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0), 
                       (3.0, 4.0), (4.0, 6.0), (6.0, 10.0), (10.0, 50.0)]
        
        for selection in ["H", "D", "A"]:
            self.odds_calibration[selection] = {}
            
            for low, high in odds_ranges:
                # Find matches where this selection had odds in this range
                range_matches = []
                for m in matches:
                    odds = self._get_odds(m, selection)
                    if low <= odds < high:
                        range_matches.append(m)
                
                if len(range_matches) >= 10:  # Need enough samples
                    wins = sum(1 for m in range_matches if m.result == selection)
                    actual_rate = wins / len(range_matches)
                    implied_rate = sum(1 / self._get_odds(m, selection) for m in range_matches) / len(range_matches)
                    
                    self.odds_calibration[selection][(low, high)] = {
                        "actual": actual_rate,
                        "implied": implied_rate,
                        "edge": actual_rate - implied_rate,
                        "count": len(range_matches),
                    }
        
        self.trained = True
        self._print_calibration()
    
    def _print_calibration(self):
        """Print calibration summary."""
        print("\n📊 Edge Model Calibration:")
        print(f"   Base rates: H={self.base_rates['H']:.1%} D={self.base_rates['D']:.1%} A={self.base_rates['A']:.1%}")
        
        print("\n   Odds-range value (actual vs implied):")
        for selection in ["H", "D", "A"]:
            for (low, high), stats in self.odds_calibration[selection].items():
                edge_pct = stats["edge"] * 100
                marker = "✓" if edge_pct > 0 else "✗"
                print(f"   {selection} @ {low:.1f}-{high:.1f}: {stats['actual']:.1%} vs {stats['implied']:.1%} "
                      f"(edge: {edge_pct:+.1f}%) {marker} [n={stats['count']}]")
    
    def _get_odds(self, match: Match, selection: str) -> float:
        """Get odds for selection."""
        if selection == "H":
            return match.odds.home_odds
        elif selection == "D":
            return match.odds.draw_odds
        else:
            return match.odds.away_odds
    
    def estimate_edge(self, match: Match, selection: str) -> float:
        """
        Estimate edge based on historical calibration.
        
        Returns edge = estimated_true_prob - implied_prob
        """
        odds = self._get_odds(match, selection)
        implied_prob = 1 / odds
        
        # Find the calibration for this odds range
        for (low, high), stats in self.odds_calibration[selection].items():
            if low <= odds < high:
                # Use historical actual rate vs implied
                return stats["edge"]
        
        # No calibration data - use base rate vs implied
        return self.base_rates[selection] - implied_prob
    
    def get_estimated_prob(self, match: Match, selection: str) -> float:
        """Get estimated true probability for a selection."""
        odds = self._get_odds(match, selection)
        
        # Find calibration
        for (low, high), stats in self.odds_calibration[selection].items():
            if low <= odds < high:
                return stats["actual"]
        
        return self.base_rates[selection]


# Global edge model instance (trained once, shared by strategies)
_edge_model: Optional[HistoricalEdgeModel] = None


def get_edge_model() -> HistoricalEdgeModel:
    """Get or create the global edge model."""
    global _edge_model
    if _edge_model is None:
        _edge_model = HistoricalEdgeModel()
    return _edge_model


def train_edge_model(matches: List[Match]):
    """Train the global edge model on historical data."""
    model = get_edge_model()
    model.train(matches)


class FlatBettingStrategy(BaseStrategy):
    """
    Flat betting: Fixed stake on all selections with positive edge.
    
    Simplest baseline strategy.
    """
    
    def __init__(
        self,
        stake_fraction: float = 0.01,  # 1% of bankroll
        min_edge: float = 0.0,  # Minimum edge to bet
    ):
        super().__init__(name="FlatBetting")
        self.stake_fraction = stake_fraction
        self.min_edge = min_edge
    
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """Bet flat amount on best value selection."""
        
        # Find selection with best edge
        best_selection = None
        best_edge = self.min_edge
        
        for selection in ["H", "D", "A"]:
            edge = self.estimate_edge(match, selection)
            if edge > best_edge:
                best_edge = edge
                best_selection = selection
        
        if best_selection is None:
            return None  # No value
        
        stake = state.bankroll * self.stake_fraction
        odds = self.get_odds_for_selection(match, best_selection)
        
        return Bet(
            match=match,
            selection=best_selection,
            odds=odds,
            stake=stake,
        )


class KellyStrategy(BaseStrategy):
    """
    Kelly Criterion betting strategy.
    
    Optimal bet sizing for maximizing log-wealth growth.
    stake = edge / (odds - 1)
    """
    
    def __init__(
        self,
        min_edge: float = 0.02,  # 2% minimum edge
        max_stake_fraction: float = 0.25,  # Cap at 25% of bankroll
    ):
        super().__init__(name="Kelly")
        self.min_edge = min_edge
        self.max_stake_fraction = max_stake_fraction
    
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """Apply Kelly criterion for bet sizing."""
        
        # Find selection with best edge
        best_selection = None
        best_edge = self.min_edge
        best_odds = 0
        
        for selection in ["H", "D", "A"]:
            edge = self.estimate_edge(match, selection)
            if edge > best_edge:
                best_edge = edge
                best_selection = selection
                best_odds = self.get_odds_for_selection(match, selection)
        
        if best_selection is None:
            return None
        
        # Kelly formula: f* = edge / (odds - 1)
        # Where edge = p - 1/odds, so f* = (p * odds - 1) / (odds - 1)
        kelly_fraction = best_edge / (best_odds - 1)
        
        # Cap at maximum
        kelly_fraction = min(kelly_fraction, self.max_stake_fraction)
        
        # Don't bet negative Kelly
        if kelly_fraction <= 0:
            return None
        
        stake = state.bankroll * kelly_fraction
        
        return Bet(
            match=match,
            selection=best_selection,
            odds=best_odds,
            stake=stake,
        )


class FractionalKellyStrategy(BaseStrategy):
    """
    Fractional Kelly strategy.
    
    Uses a fraction of full Kelly to reduce variance.
    Common choices: 0.25 (quarter-Kelly), 0.5 (half-Kelly)
    """
    
    def __init__(
        self,
        kelly_fraction: float = 0.25,  # Quarter-Kelly
        min_edge: float = 0.02,
        max_stake_fraction: float = 0.10,  # 10% max
    ):
        super().__init__(name=f"Kelly-{kelly_fraction:.0%}")
        self.kelly_fraction = kelly_fraction
        self.min_edge = min_edge
        self.max_stake_fraction = max_stake_fraction
    
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """Apply fractional Kelly criterion."""
        
        # Find best selection
        best_selection = None
        best_edge = self.min_edge
        best_odds = 0
        
        for selection in ["H", "D", "A"]:
            edge = self.estimate_edge(match, selection)
            if edge > best_edge:
                best_edge = edge
                best_selection = selection
                best_odds = self.get_odds_for_selection(match, selection)
        
        if best_selection is None:
            return None
        
        # Fractional Kelly
        full_kelly = best_edge / (best_odds - 1)
        fractional = full_kelly * self.kelly_fraction
        
        # Cap and validate
        fractional = min(fractional, self.max_stake_fraction)
        if fractional <= 0:
            return None
        
        stake = state.bankroll * fractional
        
        return Bet(
            match=match,
            selection=best_selection,
            odds=best_odds,
            stake=stake,
        )


class IAIStrategy(BaseStrategy):
    """
    IAI-enhanced betting strategy.
    
    Allows meta-parameters to be adapted by IAI:
    - Kelly fraction
    - Minimum edge threshold
    - Maximum stake
    - Selection criteria
    
    The IAI orchestrator will adjust these based on performance.
    """
    
    def __init__(
        self,
        params: Optional[Dict[str, float]] = None,
    ):
        super().__init__(name="IAI")
        
        # Default parameters - can be updated by IAI
        self.params = {
            "kelly_fraction": 0.25,
            "min_edge": 0.02,
            "max_stake_fraction": 0.10,
            "min_odds": 1.20,
            "max_odds": 5.00,
            "confidence_weight": 1.0,  # How much to weight edge confidence
        }
        
        if params:
            self.params.update(params)
        
        # Track for meta-learning
        self.recent_bets: List[Bet] = []
        self.param_history: List[Dict[str, float]] = [self.params.copy()]
    
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """Make betting decision with current parameters."""
        
        # Find best selection
        best_selection = None
        best_edge = self.params["min_edge"]
        best_odds = 0
        
        for selection in ["H", "D", "A"]:
            odds = self.get_odds_for_selection(match, selection)
            
            # Apply odds filter
            if odds < self.params["min_odds"] or odds > self.params["max_odds"]:
                continue
            
            edge = self.estimate_edge(match, selection)
            
            # Weight by confidence
            weighted_edge = edge * self.params["confidence_weight"]
            
            if weighted_edge > best_edge:
                best_edge = weighted_edge
                best_selection = selection
                best_odds = odds
        
        if best_selection is None:
            return None
        
        # Compute stake with fractional Kelly
        full_kelly = best_edge / (best_odds - 1) if best_odds > 1 else 0
        fractional = full_kelly * self.params["kelly_fraction"]
        
        # Apply limits
        fractional = max(0, min(fractional, self.params["max_stake_fraction"]))
        
        if fractional <= 0:
            return None
        
        stake = state.bankroll * fractional
        
        bet = Bet(
            match=match,
            selection=best_selection,
            odds=best_odds,
            stake=stake,
        )
        
        self.recent_bets.append(bet)
        return bet
    
    def update_params(self, new_params: Dict[str, float]):
        """Update strategy parameters (called by IAI)."""
        old_params = self.params.copy()
        self.params.update(new_params)
        self.param_history.append(self.params.copy())
        
        print(f"IAI Strategy params updated:")
        for key, new_val in new_params.items():
            old_val = old_params.get(key, "N/A")
            print(f"  {key}: {old_val} → {new_val}")
    
    def get_recent_performance(self, n: int = 50) -> Dict[str, float]:
        """Get performance metrics for recent bets."""
        recent = [b for b in self.recent_bets[-n:] if b.profit is not None]
        
        if not recent:
            return {}
        
        return {
            "n_bets": len(recent),
            "win_rate": sum(1 for b in recent if b.won) / len(recent),
            "avg_profit": sum(b.profit for b in recent) / len(recent),
            "total_profit": sum(b.profit for b in recent),
            "avg_odds": sum(b.odds for b in recent) / len(recent),
            "avg_stake": sum(b.stake for b in recent) / len(recent),
        }

class SelectiveEdgeStrategy(BaseStrategy):
    """
    Selective strategy that only bets on historically profitable ranges.
    
    Based on edge model calibration, only bets when:
    1. The selection/odds combination has shown positive historical edge
    2. The edge exceeds a minimum threshold
    
    This is the "be smart" strategy - quality over quantity.
    """
    
    def __init__(
        self,
        stake_fraction: float = 0.03,  # 3% per bet
        min_edge: float = 0.02,  # Only bet if 2%+ edge
        min_sample_size: int = 50,  # Need enough historical data
    ):
        super().__init__(name="SelectiveEdge")
        self.stake_fraction = stake_fraction
        self.min_edge = min_edge
        self.min_sample_size = min_sample_size
    
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """Only bet on selections with proven positive edge."""
        
        model = get_edge_model()
        if not model.trained:
            return None
        
        best_selection = None
        best_edge = self.min_edge
        best_odds = 0
        
        for selection in ["H", "D", "A"]:
            odds = self.get_odds_for_selection(match, selection)
            
            # Check if this odds range has enough data AND positive edge
            for (low, high), stats in model.odds_calibration[selection].items():
                if low <= odds < high:
                    # Require minimum sample size
                    if stats["count"] < self.min_sample_size:
                        continue
                    
                    # Only bet if historical edge is positive
                    if stats["edge"] > best_edge:
                        best_edge = stats["edge"]
                        best_selection = selection
                        best_odds = odds
                    break
        
        if best_selection is None:
            return None
        
        stake = state.bankroll * self.stake_fraction
        
        return Bet(
            match=match,
            selection=best_selection,
            odds=best_odds,
            stake=stake,
        )


class UnderdogValueStrategy(BaseStrategy):
    """
    Strategy specifically targeting home underdogs.
    
    Historical data shows home teams at 4.0-6.0 odds consistently
    outperform their implied probability (+8% edge on 6 seasons).
    
    This exploits the "home underdog bias" - bookies may undervalue
    home teams that are expected to lose.
    """
    
    def __init__(
        self,
        stake_fraction: float = 0.05,  # 5% per bet (fewer bets, higher stakes)
        min_odds: float = 4.0,
        max_odds: float = 6.0,
    ):
        super().__init__(name="HomeUnderdog")
        self.stake_fraction = stake_fraction
        self.min_odds = min_odds
        self.max_odds = max_odds
    
    def decide(
        self,
        match: Match,
        state: BettingState,
    ) -> Optional[Bet]:
        """Bet on home underdogs in the sweet spot."""
        
        home_odds = match.odds.home_odds
        
        # Only bet on home underdogs in the profitable range
        if self.min_odds <= home_odds < self.max_odds:
            stake = state.bankroll * self.stake_fraction
            
            return Bet(
                match=match,
                selection="H",
                odds=home_odds,
                stake=stake,
            )
        
        return None