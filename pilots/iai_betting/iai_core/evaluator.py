"""
Evaluator - Tests Hypotheses Empirically
========================================
Tests each hypothesis against historical data and computes:
- Edge with 95% confidence interval
- Statistical significance
- Stability across seasons
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Any
from dataclasses import dataclass

from .hypotheses import BettingHypothesis


@dataclass
class EvaluationResult:
    """Result of hypothesis evaluation."""
    hypothesis_id: str
    hypothesis_name: str
    
    # Performance metrics
    total_bets: int
    wins: int
    losses: int
    win_rate: float
    
    # Financial metrics
    total_staked: float
    total_return: float
    profit: float
    roi: float
    edge: float  # Actual edge %
    
    # Statistical significance
    edge_ci_lower: float  # 95% CI lower bound
    edge_ci_upper: float  # 95% CI upper bound
    p_value: float
    is_significant: bool  # p < 0.05
    
    # Stability analysis
    season_edges: List[float]
    edge_std: float  # Standard deviation across seasons
    is_stable: bool  # Low variance across seasons
    
    # Overall assessment
    passes_invariant: bool  # Edge > 2.0% with 95% confidence
    recommendation: str  # ACCEPT, REJECT, NEEDS_MORE_DATA


class BettingEvaluator:
    """Evaluates betting hypotheses against historical data."""
    
    def __init__(self, invariant_edge: float = 2.0, confidence_level: float = 0.95):
        """
        Args:
            invariant_edge: Minimum edge required (%)
            confidence_level: Confidence level for statistical tests
        """
        self.invariant_edge = invariant_edge
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
    
    def evaluate(self, hypothesis: BettingHypothesis, matches_df: pd.DataFrame,
                 initial_bankroll: float = 1000) -> EvaluationResult:
        """
        Evaluate a hypothesis against historical match data.
        
        Args:
            hypothesis: Hypothesis to test
            matches_df: DataFrame with columns: Date, HomeTeam, AwayTeam, 
                       FTR (Full Time Result), B365H, B365D, B365A (odds)
            initial_bankroll: Starting bankroll for simulation
        
        Returns:
            EvaluationResult with all metrics
        """
        # Filter qualifying matches
        qualifying = self._filter_qualifying_matches(hypothesis, matches_df)
        
        if len(qualifying) < 20:
            return self._insufficient_data_result(hypothesis, len(qualifying))
        
        # Simulate bets
        bankroll = initial_bankroll
        bets = []
        
        for _, match in qualifying.iterrows():
            # Determine odds based on selection
            if hypothesis.selection == "H":
                odds = match['B365H']
                won = match['FTR'] == 'H'
            elif hypothesis.selection == "D":
                odds = match['B365D']
                won = match['FTR'] == 'D'
            else:  # "A"
                odds = match['B365A']
                won = match['FTR'] == 'A'
            
            # Calculate stake
            stake = bankroll * (hypothesis.stake_pct / 100)
            
            # Record bet
            profit = stake * (odds - 1) if won else -stake
            bets.append({
                'date': match['Date'],
                'season': match.get('Season', 'unknown'),
                'stake': stake,
                'odds': odds,
                'won': won,
                'profit': profit
            })
            
            bankroll += profit
        
        # Convert to DataFrame for analysis
        bets_df = pd.DataFrame(bets)
        
        # Calculate metrics
        total_bets = len(bets_df)
        wins = bets_df['won'].sum()
        losses = total_bets - wins
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        
        total_staked = bets_df['stake'].sum()
        total_return = bets_df[bets_df['won']]['stake'].sum() * bets_df[bets_df['won']]['odds'].mean() if wins > 0 else 0
        profit = bets_df['profit'].sum()
        roi = (profit / total_staked * 100) if total_staked > 0 else 0
        
        # Calculate edge
        avg_odds = bets_df['odds'].mean()
        implied_prob = 1 / avg_odds * 100
        actual_win_rate = win_rate
        edge = actual_win_rate - implied_prob
        
        # Statistical significance (t-test)
        returns = bets_df['profit'] / bets_df['stake']
        t_stat, p_value = stats.ttest_1samp(returns, 0)
        is_significant = p_value < self.alpha
        
        # 95% Confidence interval for edge
        returns_pct = returns * 100
        ci_margin = stats.t.ppf(1 - self.alpha/2, len(returns) - 1) * returns_pct.std() / np.sqrt(len(returns))
        edge_ci_lower = edge - ci_margin
        edge_ci_upper = edge + ci_margin
        
        # Stability analysis (by season)
        season_edges = []
        if 'season' in bets_df.columns:
            for season in bets_df['season'].unique():
                season_bets = bets_df[bets_df['season'] == season]
                if len(season_bets) >= 5:
                    season_win_rate = (season_bets['won'].sum() / len(season_bets) * 100)
                    season_avg_odds = season_bets['odds'].mean()
                    season_implied = 1 / season_avg_odds * 100
                    season_edge = season_win_rate - season_implied
                    season_edges.append(season_edge)
        
        edge_std = np.std(season_edges) if season_edges else 0
        is_stable = edge_std < 3.0  # Stable if std < 3%
        
        # Overall assessment
        passes_invariant = edge_ci_lower > self.invariant_edge and is_significant
        
        if total_bets < 30:
            recommendation = "NEEDS_MORE_DATA"
        elif passes_invariant and is_stable:
            recommendation = "ACCEPT"
        else:
            recommendation = "REJECT"
        
        return EvaluationResult(
            hypothesis_id=hypothesis.id,
            hypothesis_name=hypothesis.name,
            total_bets=total_bets,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_staked=total_staked,
            total_return=total_return,
            profit=profit,
            roi=roi,
            edge=edge,
            edge_ci_lower=edge_ci_lower,
            edge_ci_upper=edge_ci_upper,
            p_value=p_value,
            is_significant=is_significant,
            season_edges=season_edges,
            edge_std=edge_std,
            is_stable=is_stable,
            passes_invariant=passes_invariant,
            recommendation=recommendation
        )
    
    def _filter_qualifying_matches(self, hypothesis: BettingHypothesis, 
                                   matches_df: pd.DataFrame) -> pd.DataFrame:
        """Filter matches that qualify for the hypothesis."""
        if hypothesis.selection == "H":
            odds_col = 'B365H'
        elif hypothesis.selection == "D":
            odds_col = 'B365D'
        else:
            odds_col = 'B365A'
        
        mask = (
            (matches_df[odds_col] >= hypothesis.odds_min) &
            (matches_df[odds_col] <= hypothesis.odds_max) &
            (matches_df['FTR'].notna())
        )
        
        return matches_df[mask].copy()
    
    def _insufficient_data_result(self, hypothesis: BettingHypothesis, 
                                  bet_count: int) -> EvaluationResult:
        """Return result for insufficient data case."""
        return EvaluationResult(
            hypothesis_id=hypothesis.id,
            hypothesis_name=hypothesis.name,
            total_bets=bet_count,
            wins=0,
            losses=0,
            win_rate=0.0,
            total_staked=0.0,
            total_return=0.0,
            profit=0.0,
            roi=0.0,
            edge=0.0,
            edge_ci_lower=0.0,
            edge_ci_upper=0.0,
            p_value=1.0,
            is_significant=False,
            season_edges=[],
            edge_std=0.0,
            is_stable=False,
            passes_invariant=False,
            recommendation="NEEDS_MORE_DATA"
        )
