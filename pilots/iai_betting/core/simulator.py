"""Betting simulator for IAI.

Runs betting simulations on historical data.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .data import Match, FootballDataLoader
from .strategies import BaseStrategy, BettingState, Bet
from .evaluator import BettingEvaluator, EvaluationResult


@dataclass
class SimulationConfig:
    """Configuration for betting simulation."""
    initial_bankroll: float = 1000.0
    
    # Data selection
    leagues: List[str] = None
    seasons: List[str] = None
    
    # Train/test split
    train_fraction: float = 0.7  # Use 70% for training
    
    # Constraints
    max_stake_fraction: float = 0.25
    min_bankroll_fraction: float = 0.1
    max_drawdown: float = 0.5
    
    def __post_init__(self):
        if self.leagues is None:
            self.leagues = ["E0"]  # Premier League
        if self.seasons is None:
            self.seasons = ["2122", "2223", "2324"]


class BettingSimulator:
    """
    Simulator for testing betting strategies on historical data.
    
    Provides:
    - Historical backtesting
    - Train/test splits
    - Multiple strategy comparison
    - IAI evolution loop integration
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize simulator.
        
        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.data_loader = FootballDataLoader()
        self.matches: List[Match] = []
        self.train_matches: List[Match] = []
        self.test_matches: List[Match] = []
    
    def load_data(self) -> Tuple[List[Match], List[Match]]:
        """
        Load and split data into train/test sets.
        
        Returns:
            Tuple of (train_matches, test_matches)
        """
        # Load all matches
        all_matches = []
        for league in self.config.leagues:
            matches = self.data_loader.load_multiple_seasons(
                league, self.config.seasons
            )
            all_matches.extend(matches)
        
        # Sort by date
        all_matches.sort(key=lambda m: m.date)
        self.matches = all_matches
        
        # Split
        split_idx = int(len(all_matches) * self.config.train_fraction)
        self.train_matches = all_matches[:split_idx]
        self.test_matches = all_matches[split_idx:]
        
        print(f"\nData loaded:")
        print(f"  Total matches: {len(all_matches)}")
        print(f"  Train: {len(self.train_matches)} ({self.config.train_fraction:.0%})")
        print(f"  Test: {len(self.test_matches)} ({1-self.config.train_fraction:.0%})")
        
        if all_matches:
            print(f"  Date range: {all_matches[0].date.date()} to {all_matches[-1].date.date()}")
        
        return self.train_matches, self.test_matches
    
    def run_strategy(
        self,
        strategy: BaseStrategy,
        matches: Optional[List[Match]] = None,
        initial_bankroll: Optional[float] = None,
    ) -> EvaluationResult:
        """
        Run a strategy on matches and return evaluation.
        
        Args:
            strategy: Betting strategy to run
            matches: Matches to bet on (default: test set)
            initial_bankroll: Starting bankroll (default: from config)
            
        Returns:
            EvaluationResult with full metrics
        """
        matches = matches or self.test_matches
        initial_bankroll = initial_bankroll or self.config.initial_bankroll
        
        if not matches:
            raise ValueError("No matches loaded. Call load_data() first.")
        
        # Create evaluator
        evaluator = BettingEvaluator(
            initial_bankroll=initial_bankroll,
            constraints={
                "max_stake_fraction": self.config.max_stake_fraction,
                "min_bankroll_fraction": self.config.min_bankroll_fraction,
                "max_drawdown": self.config.max_drawdown,
            }
        )
        
        # Run evaluation
        result = evaluator.evaluate(strategy, matches)
        
        return result
    
    def compare_strategies(
        self,
        strategies: List[BaseStrategy],
        matches: Optional[List[Match]] = None,
    ) -> Dict[str, EvaluationResult]:
        """
        Compare multiple strategies on the same data.
        
        Args:
            strategies: List of strategies to compare
            matches: Matches to use (default: test set)
            
        Returns:
            Dict mapping strategy names to results
        """
        matches = matches or self.test_matches
        results = {}
        
        print(f"\n{'='*60}")
        print("Comparing Strategies")
        print(f"{'='*60}")
        print(f"Matches: {len(matches)}")
        print(f"Initial bankroll: £{self.config.initial_bankroll:.2f}")
        print()
        
        for strategy in strategies:
            result = self.run_strategy(strategy, matches)
            results[strategy.name] = result
            
            summary = result.summary
            print(f"  {strategy.name}:")
            print(f"    Profit: £{summary['total_profit']:.2f}")
            print(f"    ROI: {summary['roi_pct']:.2f}%")
            print(f"    Win rate: {summary['win_rate_pct']:.1f}%")
            print(f"    Max drawdown: {summary['max_drawdown_pct']:.1f}%")
            print(f"    Bets: {summary['n_bets']}")
            print()
        
        # Find best
        best = max(results.items(), key=lambda x: x[1].metrics.get("total_profit", 0))
        print(f"🏆 Best strategy: {best[0]} (£{best[1].metrics['total_profit']:.2f} profit)")
        
        return results
    
    def run_baseline_comparison(self) -> Dict[str, Any]:
        """
        Run standard baseline strategies for comparison.
        
        Returns:
            Baseline results for IAI orchestrator
        """
        from .strategies import (
            FlatBettingStrategy,
            KellyStrategy,
            FractionalKellyStrategy,
        )
        
        strategies = [
            FlatBettingStrategy(stake_fraction=0.01, min_edge=0.0),
            FlatBettingStrategy(stake_fraction=0.02, min_edge=0.02),
            KellyStrategy(min_edge=0.02),
            FractionalKellyStrategy(kelly_fraction=0.5, min_edge=0.02),
            FractionalKellyStrategy(kelly_fraction=0.25, min_edge=0.02),
        ]
        
        results = self.compare_strategies(strategies)
        
        # Format for IAI
        best_result = max(results.values(), key=lambda r: r.metrics.get("roi", 0))
        best_strategy = [k for k, v in results.items() if v == best_result][0]
        
        return {
            "systems": [
                {
                    "name": name,
                    "performance": result.metrics.get("roi", 0),
                    "metrics": result.metrics,
                }
                for name, result in results.items()
            ],
            "summary": {
                "best_system": best_strategy,
                "best_performance": best_result.metrics.get("roi", 0),
                "best_profit": best_result.metrics.get("total_profit", 0),
            },
        }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data."""
        if not self.matches:
            return {"error": "No data loaded"}
        
        return self.data_loader.summary(self.matches)
