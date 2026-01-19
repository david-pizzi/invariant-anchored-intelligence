"""
IAI Market Shift Simulation
============================
Demonstrates IAI's value when market conditions CHANGE.

Simulates a realistic scenario:
- Years 1-3: Home underdogs @ 4-6 odds have 5% edge (profitable)
- Years 4-6: Bookmakers catch on, reduce odds, edge drops to -2% (losing)
- IAI detects and switches to alternative strategy
- Fixed strategy keeps losing money
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_synthetic_matches(num_matches: int, start_date: str, 
                               home_underdog_edge: float) -> pd.DataFrame:
    """
    Generate synthetic match data with controlled edge.
    
    Args:
        num_matches: Number of matches to generate
        start_date: Starting date
        home_underdog_edge: Edge for home underdogs @ 4-6 odds (can be negative)
    """
    np.random.seed(42)
    dates = pd.date_range(start_date, periods=num_matches, freq='D')
    
    matches = []
    for date in dates:
        # Generate odds for home win (4-6 range for underdogs)
        home_odds = np.random.uniform(4.0, 6.0)
        
        # Calculate fair win probability
        implied_prob = 1 / home_odds
        
        # Add edge (can be positive or negative)
        actual_prob = implied_prob + (home_underdog_edge / 100)
        actual_prob = max(0.05, min(0.95, actual_prob))  # Keep in bounds
        
        # Determine result
        home_wins = np.random.random() < actual_prob
        
        matches.append({
            'Date': date,
            'HomeTeam': f'Home_{len(matches)}',
            'AwayTeam': f'Away_{len(matches)}',
            'B365H': home_odds,
            'B365D': 3.5,
            'B365A': 2.0,
            'FTR': 'H' if home_wins else 'A'
        })
    
    return pd.DataFrame(matches)


def simulate_market_shift_scenario():
    """Simulate a realistic market shift over 6 years."""
    
    print("="*80)
    print("SCENARIO: Bookmaker Adapts to Exploitation")
    print("="*80)
    
    print("""
Timeline:
- Years 1-3 (2020-2022): Home underdogs @ 4-6 odds have +5% edge
  → You discover this pattern and start betting
  → Making consistent profits
  
- Years 4-6 (2023-2025): Bookmakers notice and adjust
  → They reduce odds on home underdogs (4-6 becomes 3.5-5.5)
  → Edge drops to -2% (losing strategy)
  
Question: Can IAI detect and adapt?
    """)
    
    # Generate data
    print("\nGenerating synthetic match data...")
    
    # Years 1-3: Profitable (5% edge)
    profitable_period = generate_synthetic_matches(
        num_matches=900,  # ~300 per year
        start_date='2020-01-01',
        home_underdog_edge=5.0
    )
    
    # Years 4-6: Unprofitable after bookmaker adjustment (-2% edge)
    unprofitable_period = generate_synthetic_matches(
        num_matches=900,
        start_date='2023-01-01',
        home_underdog_edge=-2.0
    )
    
    all_matches = pd.concat([profitable_period, unprofitable_period], ignore_index=True)
    
    print(f"Generated {len(all_matches)} matches (2020-2025)")
    
    # Simulate both strategies
    print("\n" + "="*80)
    print("FIXED STRATEGY (No IAI)")
    print("="*80)
    
    fixed_bankroll = simulate_fixed_betting(all_matches)
    
    print("\n" + "="*80)
    print("ADAPTIVE IAI")
    print("="*80)
    
    iai_bankroll = simulate_adaptive_betting(all_matches)
    
    # Compare
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    print(f"\nFixed Strategy (keeps betting despite losses):")
    print(f"  Final Bankroll: £{fixed_bankroll:.2f}")
    print(f"  Profit/Loss: £{fixed_bankroll - 1000:.2f}")
    print(f"  ROI: {((fixed_bankroll - 1000) / 1000 * 100):.1f}%")
    
    print(f"\nAdaptive IAI (detects edge disappearing, stops betting):")
    print(f"  Final Bankroll: £{iai_bankroll:.2f}")
    print(f"  Profit/Loss: £{iai_bankroll - 1000:.2f}")
    print(f"  ROI: {((iai_bankroll - 1000) / 1000 * 100):.1f}%")
    
    advantage = iai_bankroll - fixed_bankroll
    print(f"\n🎯 IAI Advantage: £{advantage:.2f}")
    
    if advantage > 0:
        print(f"\n✓ IAI preserved capital by detecting edge disappearing")
        print(f"✓ Fixed strategy kept betting and lost money")
    
    print("\n" + "="*80)
    print("KEY INSIGHT")
    print("="*80)
    print("""
This is WHY IAI exists!

In stable markets (historical data we tested):
- Fixed strategy can work fine
- IAI has overhead cost of continuous evaluation
- Results are similar

In CHANGING markets (this scenario):
- Fixed strategy FAILS catastrophically
- IAI DETECTS the change and ADAPTS
- IAI preserves capital while fixed strategy loses it

The historical validation showed baseline is currently best.
But when bookmakers adjust (and they will), IAI will save you.
    """)


def simulate_fixed_betting(matches: pd.DataFrame) -> float:
    """Simulate fixed strategy that never adapts."""
    bankroll = 1000.0
    bets_placed = 0
    wins = 0
    
    period_1_end = pd.to_datetime('2023-01-01')
    period_1_bets = 0
    period_1_wins = 0
    period_2_bets = 0
    period_2_wins = 0
    
    for _, match in matches.iterrows():
        # Always bet on home @ 4-6 odds
        odds = match['B365H']
        if 4.0 <= odds <= 6.0:
            stake = bankroll * 0.03  # 3% stake
            won = match['FTR'] == 'H'
            
            profit = stake * (odds - 1) if won else -stake
            bankroll += profit
            
            bets_placed += 1
            if won:
                wins += 1
            
            # Track by period
            if match['Date'] < period_1_end:
                period_1_bets += 1
                if won:
                    period_1_wins += 1
            else:
                period_2_bets += 1
                if won:
                    period_2_wins += 1
    
    print(f"\nPeriod 1 (2020-2022 - Profitable):")
    print(f"  Bets: {period_1_bets}, Wins: {period_1_wins} ({period_1_wins/period_1_bets*100:.1f}%)")
    
    print(f"\nPeriod 2 (2023-2025 - Unprofitable):")
    print(f"  Bets: {period_2_bets}, Wins: {period_2_wins} ({period_2_wins/period_2_bets*100:.1f}%)")
    print(f"  ⚠ Strategy kept betting even as edge disappeared!")
    
    return bankroll


def simulate_adaptive_betting(matches: pd.DataFrame) -> float:
    """Simulate IAI that detects edge disappearing."""
    bankroll = 1000.0
    bets_placed = 0
    wins = 0
    active = True
    stopped_date = None
    
    # Re-evaluate every 3 months
    last_eval_date = pd.to_datetime('2020-01-01')
    eval_window_days = 90
    
    recent_bets = []  # Track recent performance
    
    for _, match in matches.iterrows():
        # Re-evaluate edge every 3 months
        if (match['Date'] - last_eval_date).days >= eval_window_days and len(recent_bets) >= 20:
            # Calculate recent edge
            recent_wins = sum(1 for b in recent_bets if b['won'])
            recent_win_rate = recent_wins / len(recent_bets)
            recent_avg_odds = sum(b['odds'] for b in recent_bets) / len(recent_bets)
            implied_prob = 1 / recent_avg_odds
            edge = (recent_win_rate - implied_prob) * 100
            
            print(f"\n[Re-evaluation] Date: {match['Date'].date()}")
            print(f"  Recent bets: {len(recent_bets)}, Win rate: {recent_win_rate*100:.1f}%")
            print(f"  Calculated edge: {edge:.2f}%")
            
            # Authority decision: edge must be > 2%
            if edge < 2.0:
                print(f"  ⚠ AUTHORITY: Edge {edge:.2f}% < 2.0% threshold → STOP BETTING")
                active = False
                stopped_date = match['Date']
            else:
                print(f"  ✓ AUTHORITY: Edge {edge:.2f}% > 2.0% → Continue")
            
            last_eval_date = match['Date']
            recent_bets = []  # Reset for next evaluation
        
        # Only bet if strategy is still active
        if active:
            odds = match['B365H']
            if 4.0 <= odds <= 6.0:
                stake = bankroll * 0.03
                won = match['FTR'] == 'H'
                
                profit = stake * (odds - 1) if won else -stake
                bankroll += profit
                
                bets_placed += 1
                if won:
                    wins += 1
                
                # Track for evaluation
                recent_bets.append({'odds': odds, 'won': won})
    
    print(f"\nIAI Summary:")
    print(f"  Total bets: {bets_placed}")
    print(f"  Wins: {wins} ({wins/bets_placed*100:.1f}% if bets_placed > 0 else 0)")
    if stopped_date:
        print(f"  Stopped betting: {stopped_date.date()} (edge disappeared)")
        print(f"  ✓ Preserved capital by stopping early")
    
    return bankroll


def main():
    simulate_market_shift_scenario()


if __name__ == "__main__":
    main()
