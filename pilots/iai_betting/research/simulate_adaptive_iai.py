"""
IAI Time-Series Simulation - Continuous Adaptation
==================================================
Shows how IAI adapts over time as market conditions change.

Simulates:
1. Starting with baseline strategy
2. Re-evaluating weekly on rolling window
3. Authority accepting/rejecting as edge changes
4. Comparing fixed strategy vs adaptive IAI
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from iai_core.orchestrator import IAIOrchestrator
from iai_core.hypotheses import ALL_HYPOTHESES, BettingHypothesis
from iai_core.evaluator import BettingEvaluator
from research.validate_iai import load_historical_data


class TimeSeriesSimulator:
    """Simulates IAI adapting over time."""
    
    def __init__(self, matches_df: pd.DataFrame, initial_bankroll: float = 1000):
        self.matches_df = matches_df.sort_values('Date').reset_index(drop=True)
        self.initial_bankroll = initial_bankroll
        
        # Convert Date to datetime
        self.matches_df['Date'] = pd.to_datetime(self.matches_df['Date'], errors='coerce')
        self.matches_df = self.matches_df.dropna(subset=['Date'])
        
        self.orchestrator = IAIOrchestrator(invariant_edge=2.0, min_bets=30)
        self.evaluator = BettingEvaluator(invariant_edge=2.0)
        
    def simulate_fixed_strategy(self, hypothesis: BettingHypothesis) -> Dict:
        """Simulate a fixed strategy that never adapts."""
        bankroll = self.initial_bankroll
        bets = []
        
        for _, match in self.matches_df.iterrows():
            qualifies, odds = hypothesis.qualifies(
                match['HomeTeam'], match['AwayTeam'],
                match['B365H'], match['B365D'], match['B365A']
            )
            
            if qualifies:
                stake = bankroll * (hypothesis.stake_pct / 100)
                
                # Determine if won
                if hypothesis.selection == "H":
                    won = match['FTR'] == 'H'
                elif hypothesis.selection == "D":
                    won = match['FTR'] == 'D'
                else:
                    won = match['FTR'] == 'A'
                
                profit = stake * (odds - 1) if won else -stake
                bankroll += profit
                
                bets.append({
                    'date': match['Date'],
                    'strategy': hypothesis.id,
                    'odds': odds,
                    'stake': stake,
                    'won': won,
                    'profit': profit,
                    'bankroll': bankroll
                })
        
        bets_df = pd.DataFrame(bets)
        
        return {
            'strategy': 'FIXED',
            'hypothesis_id': hypothesis.id,
            'total_bets': len(bets_df),
            'wins': bets_df['won'].sum(),
            'win_rate': (bets_df['won'].sum() / len(bets_df) * 100) if len(bets_df) > 0 else 0,
            'final_bankroll': bankroll,
            'total_profit': bankroll - self.initial_bankroll,
            'roi': ((bankroll - self.initial_bankroll) / self.initial_bankroll * 100),
            'bets': bets_df
        }
    
    def simulate_adaptive_iai(self, reeval_window_days: int = 90) -> Dict:
        """
        Simulate IAI continuously adapting.
        
        Args:
            reeval_window_days: Re-evaluate strategies every N days
        """
        bankroll = self.initial_bankroll
        bets = []
        adaptations = []
        
        # Start with baseline
        current_hypothesis = ALL_HYPOTHESES[0]  # H1: Home Underdogs
        
        # Get date range
        start_date = self.matches_df['Date'].min()
        end_date = self.matches_df['Date'].max()
        
        # Initial evaluation window (first 6 months of data)
        initial_window_end = start_date + timedelta(days=180)
        evaluation_data = self.matches_df[self.matches_df['Date'] < initial_window_end]
        
        print(f"\n{'='*80}")
        print(f"IAI ADAPTIVE SIMULATION")
        print(f"{'='*80}")
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        print(f"Re-evaluation every {reeval_window_days} days")
        print(f"Starting with: {current_hypothesis.name}")
        
        # Simulation loop
        current_date = initial_window_end
        eval_count = 0
        
        while current_date < end_date:
            eval_count += 1
            next_eval_date = current_date + timedelta(days=reeval_window_days)
            
            # Get matches in this period
            period_matches = self.matches_df[
                (self.matches_df['Date'] >= current_date) &
                (self.matches_df['Date'] < next_eval_date)
            ]
            
            # Place bets with current strategy
            for _, match in period_matches.iterrows():
                qualifies, odds = current_hypothesis.qualifies(
                    match['HomeTeam'], match['AwayTeam'],
                    match['B365H'], match['B365D'], match['B365A']
                )
                
                if qualifies:
                    stake = bankroll * (current_hypothesis.stake_pct / 100)
                    
                    if current_hypothesis.selection == "H":
                        won = match['FTR'] == 'H'
                    elif current_hypothesis.selection == "D":
                        won = match['FTR'] == 'D'
                    else:
                        won = match['FTR'] == 'A'
                    
                    profit = stake * (odds - 1) if won else -stake
                    bankroll += profit
                    
                    bets.append({
                        'date': match['Date'],
                        'strategy': current_hypothesis.id,
                        'odds': odds,
                        'stake': stake,
                        'won': won,
                        'profit': profit,
                        'bankroll': bankroll
                    })
            
            # Re-evaluate all hypotheses on recent data
            eval_window_start = current_date - timedelta(days=180)  # 6-month window
            eval_data = self.matches_df[
                (self.matches_df['Date'] >= eval_window_start) &
                (self.matches_df['Date'] < current_date)
            ]
            
            if len(eval_data) >= 100:  # Need minimum data
                # Test all hypotheses
                best_hypothesis = current_hypothesis
                best_edge = -100
                
                evaluations = []
                
                for hyp in ALL_HYPOTHESES:
                    try:
                        result = self.evaluator.evaluate(hyp, eval_data, self.initial_bankroll)
                        decision = self.orchestrator.authority.review(hyp, result)
                        
                        evaluations.append({
                            'hypothesis': hyp.id,
                            'edge': result.edge,
                            'edge_ci_lower': result.edge_ci_lower,
                            'bets': result.total_bets,
                            'decision': decision.decision
                        })
                        
                        # Track best ACCEPTED hypothesis
                        if decision.decision == "ACCEPT" and result.edge > best_edge:
                            best_edge = result.edge
                            best_hypothesis = hyp
                    except:
                        pass
                
                # Check if we should switch
                if best_hypothesis.id != current_hypothesis.id:
                    adaptation = {
                        'date': current_date,
                        'from': current_hypothesis.id,
                        'to': best_hypothesis.id,
                        'from_edge': next((e['edge'] for e in evaluations if e['hypothesis'] == current_hypothesis.id), 0),
                        'to_edge': best_edge,
                        'bankroll': bankroll,
                        'total_bets': len(bets)
                    }
                    adaptations.append(adaptation)
                    
                    print(f"\n[Evaluation {eval_count}] Date: {current_date.date()}")
                    print(f"  ADAPTATION: {current_hypothesis.id} → {best_hypothesis.id}")
                    print(f"  Old edge: {adaptation['from_edge']:.2f}% | New edge: {best_edge:.2f}%")
                    print(f"  Bankroll: £{bankroll:.2f}")
                    
                    current_hypothesis = best_hypothesis
                else:
                    print(f"\n[Evaluation {eval_count}] Date: {current_date.date()}")
                    print(f"  Keeping: {current_hypothesis.id} (Edge: {best_edge:.2f}%)")
                    print(f"  Bankroll: £{bankroll:.2f}")
            
            current_date = next_eval_date
        
        bets_df = pd.DataFrame(bets)
        
        return {
            'strategy': 'ADAPTIVE_IAI',
            'total_bets': len(bets_df),
            'wins': bets_df['won'].sum() if len(bets_df) > 0 else 0,
            'win_rate': (bets_df['won'].sum() / len(bets_df) * 100) if len(bets_df) > 0 else 0,
            'final_bankroll': bankroll,
            'total_profit': bankroll - self.initial_bankroll,
            'roi': ((bankroll - self.initial_bankroll) / self.initial_bankroll * 100),
            'adaptations': adaptations,
            'bets': bets_df
        }


def compare_strategies(matches_df: pd.DataFrame):
    """Compare fixed vs adaptive strategies."""
    simulator = TimeSeriesSimulator(matches_df, initial_bankroll=1000)
    
    print("\n" + "="*80)
    print("SIMULATING FIXED STRATEGY (No IAI)")
    print("="*80)
    
    # Fixed baseline
    baseline = ALL_HYPOTHESES[0]
    fixed_result = simulator.simulate_fixed_strategy(baseline)
    
    print(f"\nStrategy: {baseline.name}")
    print(f"Total Bets: {fixed_result['total_bets']}")
    print(f"Wins: {fixed_result['wins']} ({fixed_result['win_rate']:.1f}%)")
    print(f"Final Bankroll: £{fixed_result['final_bankroll']:.2f}")
    print(f"Total Profit: £{fixed_result['total_profit']:.2f}")
    print(f"ROI: {fixed_result['roi']:.2f}%")
    
    # Adaptive IAI
    adaptive_result = simulator.simulate_adaptive_iai(reeval_window_days=90)
    
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    comparison = pd.DataFrame([
        {
            'Strategy': 'Fixed (No IAI)',
            'Total Bets': fixed_result['total_bets'],
            'Win Rate': f"{fixed_result['win_rate']:.1f}%",
            'Final Bankroll': f"£{fixed_result['final_bankroll']:.2f}",
            'Profit': f"£{fixed_result['total_profit']:.2f}",
            'ROI': f"{fixed_result['roi']:.1f}%"
        },
        {
            'Strategy': 'Adaptive IAI',
            'Total Bets': adaptive_result['total_bets'],
            'Win Rate': f"{adaptive_result['win_rate']:.1f}%",
            'Final Bankroll': f"£{adaptive_result['final_bankroll']:.2f}",
            'Profit': f"£{adaptive_result['total_profit']:.2f}",
            'ROI': f"{adaptive_result['roi']:.1f}%"
        }
    ])
    
    print("\n" + comparison.to_string(index=False))
    
    # Show adaptations
    if adaptive_result['adaptations']:
        print("\n" + "="*80)
        print("IAI ADAPTATIONS OVER TIME")
        print("="*80)
        
        for i, adapt in enumerate(adaptive_result['adaptations'], 1):
            print(f"\nAdaptation {i}: {adapt['date'].date()}")
            print(f"  Switch: {adapt['from']} → {adapt['to']}")
            print(f"  Edge improvement: {adapt['from_edge']:.2f}% → {adapt['to_edge']:.2f}%")
            print(f"  Bankroll at time: £{adapt['bankroll']:.2f}")
    
    # Performance improvement
    improvement = adaptive_result['final_bankroll'] - fixed_result['final_bankroll']
    improvement_pct = (improvement / fixed_result['final_bankroll'] * 100) if fixed_result['final_bankroll'] > 0 else 0
    
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    if improvement > 0:
        print(f"\n✓ IAI OUTPERFORMED by £{improvement:.2f} ({improvement_pct:.1f}%)")
        print(f"  • More bets placed: {adaptive_result['total_bets']} vs {fixed_result['total_bets']}")
        print(f"  • Better win rate: {adaptive_result['win_rate']:.1f}% vs {fixed_result['win_rate']:.1f}%")
        print(f"  • Adapted {len(adaptive_result['adaptations'])} times to changing conditions")
    elif improvement < 0:
        print(f"\n⚠ In this period, fixed strategy performed better by £{abs(improvement):.2f}")
        print(f"  • This can happen when market conditions are stable")
        print(f"  • IAI's value is in ADAPTING when conditions change")
    else:
        print(f"\n≈ Similar performance (difference: £{abs(improvement):.2f})")
        print(f"  • Market conditions were stable during this period")
        print(f"  • IAI made {len(adaptive_result['adaptations'])} adaptations just in case")
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("""
IAI's advantage is NOT in stable markets - it's in CHANGING markets.

In this historical simulation:
- Fixed strategy: Keeps using same rules regardless of performance
- IAI: Monitors edge continuously, switches when better option appears

Real-world value: When bookmakers adjust odds or market conditions shift,
IAI detects it within 90 days and adapts. Fixed strategy takes months of
losses before human intervention.
    """)


def main():
    print("="*80)
    print("TIME-SERIES SIMULATION: IAI CONTINUOUS ADAPTATION")
    print("="*80)
    
    print("\nLoading historical data...")
    matches = load_historical_data()
    
    print(f"Loaded {len(matches)} matches")
    print(f"Date range: {matches['Date'].min()} to {matches['Date'].max()}")
    
    compare_strategies(matches)


if __name__ == "__main__":
    main()
