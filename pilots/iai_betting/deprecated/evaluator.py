"""Betting evaluator for IAI.

External evaluator that computes performance metrics
and enforces invariant constraints.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from iai_core.evaluator import BaseEvaluator, EvaluationResult, InvariantViolation
from .data import Match
from .strategies import BaseStrategy, Bet, BettingState


@dataclass
class BettingMetrics:
    """Comprehensive betting performance metrics."""
    # Core metrics
    total_profit: float
    roi: float  # Return on investment
    win_rate: float
    
    # Risk metrics
    max_drawdown: float
    sharpe_ratio: float
    
    # Volume metrics
    n_bets: int
    total_staked: float
    avg_stake: float
    avg_odds: float
    
    # Additional
    profitable_streaks: int
    losing_streaks: int
    longest_losing_streak: int
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "total_profit": self.total_profit,
            "roi": self.roi,
            "win_rate": self.win_rate,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "n_bets": self.n_bets,
            "total_staked": self.total_staked,
            "avg_stake": self.avg_stake,
            "avg_odds": self.avg_odds,
            "longest_losing_streak": self.longest_losing_streak,
        }


class BettingEvaluator(BaseEvaluator):
    """
    Evaluator for betting strategies.
    
    External authority that:
    - Computes profit/loss from settled bets
    - Calculates performance metrics
    - Enforces bankroll and risk constraints
    - Detects invariant violations
    """
    
    def __init__(
        self,
        initial_bankroll: float = 1000.0,
        constraints: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize betting evaluator.
        
        Args:
            initial_bankroll: Starting bankroll
            constraints: Invariant constraints
        """
        default_constraints = {
            "max_stake_fraction": 0.25,  # Max 25% on single bet
            "min_bankroll_fraction": 0.1,  # Stop if bankroll < 10% of initial
            "max_drawdown": 0.5,  # Stop if 50% drawdown
            "min_bets_per_evaluation": 10,  # Need at least 10 bets
        }
        
        constraints = {**default_constraints, **(constraints or {})}
        super().__init__(constraints)
        
        self.initial_bankroll = initial_bankroll
    
    def evaluate(
        self,
        strategy: BaseStrategy,
        matches: List[Match],
        **kwargs,
    ) -> EvaluationResult:
        """
        Evaluate a strategy on historical matches.
        
        Args:
            strategy: Betting strategy to evaluate
            matches: List of matches to bet on
            
        Returns:
            EvaluationResult with metrics and any violations
        """
        # Initialize betting state
        state = BettingState(
            bankroll=self.initial_bankroll,
            initial_bankroll=self.initial_bankroll,
        )
        
        # Process each match
        for match in matches:
            # Check for ruin
            if state.bankroll < self.initial_bankroll * self.constraints["min_bankroll_fraction"]:
                self.log_violation(
                    violation_type="bankroll_ruin",
                    description=f"Bankroll {state.bankroll:.2f} below minimum threshold",
                    severity="critical",
                )
                break
            
            # Get strategy decision
            bet = strategy.decide(match, state)
            
            if bet:
                # Check stake constraint
                stake_fraction = bet.stake / state.bankroll
                if stake_fraction > self.constraints["max_stake_fraction"]:
                    self.log_violation(
                        violation_type="stake_violation",
                        description=f"Stake {stake_fraction:.1%} exceeds max {self.constraints['max_stake_fraction']:.1%}",
                        severity="warning",
                        context={"bet": bet, "match": match},
                    )
                    # Reduce stake to maximum allowed
                    bet.stake = state.bankroll * self.constraints["max_stake_fraction"]
                
                # Settle bet
                bet.settle()
                state.bets.append(bet)
                state.bankroll += bet.profit
                
                # Check drawdown
                if state.max_drawdown > self.constraints["max_drawdown"]:
                    self.log_violation(
                        violation_type="drawdown_violation",
                        description=f"Max drawdown {state.max_drawdown:.1%} exceeds limit",
                        severity="critical",
                    )
        
        # Compute metrics
        metrics = self._compute_metrics(state)
        
        # Check minimum bets constraint
        if metrics.n_bets < self.constraints["min_bets_per_evaluation"]:
            self.log_violation(
                violation_type="insufficient_bets",
                description=f"Only {metrics.n_bets} bets, need {self.constraints['min_bets_per_evaluation']}",
                severity="warning",
            )
        
        # Create summary
        summary = self._create_summary(metrics, state)
        
        return EvaluationResult(
            metrics=metrics.to_dict(),
            summary=summary,
            violations=self.violations.copy(),
            raw_data=state,
        )
    
    def _compute_metrics(self, state: BettingState) -> BettingMetrics:
        """Compute comprehensive betting metrics."""
        bets = [b for b in state.bets if b.profit is not None]
        
        if not bets:
            return BettingMetrics(
                total_profit=0, roi=0, win_rate=0,
                max_drawdown=0, sharpe_ratio=0,
                n_bets=0, total_staked=0, avg_stake=0, avg_odds=0,
                profitable_streaks=0, losing_streaks=0, longest_losing_streak=0,
            )
        
        # Core metrics
        total_profit = sum(b.profit for b in bets)
        total_staked = sum(b.stake for b in bets)
        roi = total_profit / total_staked if total_staked > 0 else 0
        wins = sum(1 for b in bets if b.won)
        win_rate = wins / len(bets)
        
        # Sharpe ratio (annualized, assuming ~1000 bets/year)
        profits = [b.profit for b in bets]
        avg_profit = sum(profits) / len(profits)
        if len(profits) > 1:
            import math
            variance = sum((p - avg_profit) ** 2 for p in profits) / (len(profits) - 1)
            std_profit = math.sqrt(variance)
            sharpe_ratio = (avg_profit / std_profit) * math.sqrt(1000) if std_profit > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Streak analysis
        streaks = self._analyze_streaks(bets)
        
        return BettingMetrics(
            total_profit=total_profit,
            roi=roi,
            win_rate=win_rate,
            max_drawdown=state.max_drawdown,
            sharpe_ratio=sharpe_ratio,
            n_bets=len(bets),
            total_staked=total_staked,
            avg_stake=total_staked / len(bets),
            avg_odds=sum(b.odds for b in bets) / len(bets),
            profitable_streaks=streaks["profitable_streaks"],
            losing_streaks=streaks["losing_streaks"],
            longest_losing_streak=streaks["longest_losing_streak"],
        )
    
    def _analyze_streaks(self, bets: List[Bet]) -> Dict[str, int]:
        """Analyze winning and losing streaks."""
        if not bets:
            return {"profitable_streaks": 0, "losing_streaks": 0, "longest_losing_streak": 0}
        
        profitable_streaks = 0
        losing_streaks = 0
        current_losing = 0
        longest_losing = 0
        
        in_profit_streak = False
        in_loss_streak = False
        
        for bet in bets:
            if bet.won:
                if in_loss_streak:
                    losing_streaks += 1
                    longest_losing = max(longest_losing, current_losing)
                    current_losing = 0
                    in_loss_streak = False
                if not in_profit_streak:
                    in_profit_streak = True
            else:
                if in_profit_streak:
                    profitable_streaks += 1
                    in_profit_streak = False
                if not in_loss_streak:
                    in_loss_streak = True
                current_losing += 1
        
        # Close final streaks
        if in_profit_streak:
            profitable_streaks += 1
        if in_loss_streak:
            losing_streaks += 1
            longest_losing = max(longest_losing, current_losing)
        
        return {
            "profitable_streaks": profitable_streaks,
            "losing_streaks": losing_streaks,
            "longest_losing_streak": longest_losing,
        }
    
    def _create_summary(
        self,
        metrics: BettingMetrics,
        state: BettingState,
    ) -> Dict[str, Any]:
        """Create evaluation summary."""
        return {
            "strategy": "evaluated",
            "initial_bankroll": self.initial_bankroll,
            "final_bankroll": state.bankroll,
            "total_profit": metrics.total_profit,
            "roi_pct": metrics.roi * 100,
            "win_rate_pct": metrics.win_rate * 100,
            "max_drawdown_pct": metrics.max_drawdown * 100,
            "sharpe_ratio": metrics.sharpe_ratio,
            "n_bets": metrics.n_bets,
            "violations": len(self.violations),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _check_violations(
        self,
        raw_data: Any,
        metrics: Dict[str, float],
    ) -> List[InvariantViolation]:
        """Return accumulated violations."""
        return self.violations
